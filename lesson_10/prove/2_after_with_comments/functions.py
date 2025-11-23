"""
Fully documented version of Assignment 10: Family Search implementations.
Each line includes an explanatory comment for instructional clarity.

Course: CSE 351, week 10
File: functions.py
Author: Dawson Packer

Instructions:

Depth First Search
https://www.youtube.com/watch?v=9RHO6jU--GU

Breadth First Search
https://www.youtube.com/watch?v=86g8jAQug04


Requesting a family from the server:
family_id = 6128784944
data = get_data_from_server('{TOP_API_URL}/family/{family_id}')

Example JSON returned from the server
{
    'id': 6128784944,
    'husband_id': 2367673859,        # use with the Person API
    'wife_id': 2373686152,           # use with the Person API
    'children': [2380738417, 2185423094, 2192483455]    # use with the Person API
}

Requesting an individual from the server:
person_id = 2373686152
data = get_data_from_server('{TOP_API_URL}/person/{person_id}')

Example JSON returned from the server
{
    'id': 2373686152,
    'name': 'Stella',
    'birth': '9-3-1846',
    'parent_id': 5428641880,   # use with the Family API
    'family_id': 6128784944    # use with the Family API
}


--------------------------------------------------------------------------------------
You will lose 10% if you don't detail your part 1 and part 2 code below

Describe how to speed up part 1

Part 1 uses a recursive depth-first search with threading to speed up family tree retrieval.
The key optimizations are:
1. Concurrent person data retrieval: For each family, we retrieve husband, wife, and all
   children concurrently using threads, rather than sequentially. Since each request takes
   0.25 seconds, this saves significant time when a family has multiple members.
2. Concurrent recursive calls: When recursing to get parents, we spawn two threads - one
   for the husband's parents and one for the wife's parents. This allows both branches of
   the tree to be explored simultaneously.
3. Thread synchronization: We use locks to ensure thread-safe access to the tree data
   structure when adding families and people.
The recursive nature of DFS combined with threading allows us to explore multiple branches
of the family tree concurrently.


Describe how to speed up part 2

Part 2 uses a breadth-first search with threading to retrieve the family tree level by level.
The key optimizations are:
1. Level-based concurrency: Process all families at the same generation level concurrently
   using threads. This is more efficient than DFS for wide trees since all families at a
   level can be fetched simultaneously.
2. Concurrent person retrieval: Like Part 1, we fetch all people in a family (husband, wife,
   children) concurrently using threads.
3. Queue-based approach: Use a queue to track which families to process next, allowing us to
   systematically process the tree level by level without recursion.
4. Thread joining: Wait for all threads at a level to complete before moving to the next
   level, ensuring data consistency.
BFS is often more efficient than DFS for this problem because it maximizes concurrency across
the tree width rather than depth.


Extra (Optional) 10% Bonus to speed up part 3

Part 3 uses the same BFS algorithm as Part 2, but limits concurrent threads to 5 using a
Semaphore.
The implementation:
1. Semaphore with limit 5: Before creating each thread, we acquire a semaphore permit. This
   ensures no more than 5 threads run concurrently.
2. Release on completion: Each thread releases its semaphore permit when done, allowing
   waiting threads to proceed.
3. Maintains BFS structure: The level-by-level processing remains the same, but thread
   creation is throttled by the semaphore.
This approach balances concurrency with resource constraints, preventing server overload while
still achieving good performance.

"""
from common import *  # Import common classes (Person, Family, Tree, get_data_from_server)
import queue  # Import queue for potential use in BFS
import threading  # Import threading for concurrent execution

# -----------------------------------------------------------------------------
def depth_fs_pedigree(family_id, tree):
    """
    Part 1: Depth-First Search with threading to retrieve family tree.
    Recursively explores the tree, going deep into each branch before backtracking.
    """

    lock = threading.Lock()  # Create lock for thread-safe access to shared tree data

    def process_family(fam_id):
        """
        Recursively process a family and all its ancestors.
        This inner function is called recursively to explore the tree depth-first.
        """
        if fam_id is None:  # Base case: if no family ID provided
            return  # Exit early, nothing to process

        # Check if family already exists in tree (avoid duplicate processing)
        with lock:  # Acquire lock before checking shared tree data
            if tree.does_family_exist(fam_id):  # If family already in tree
                return  # Skip this family, it's already been processed

        # Get family data from server (HTTP request, takes ~0.25 seconds)
        family_data = get_data_from_server(f'{TOP_API_URL}/family/{fam_id}')
        if family_data is None:  # If server returned no data (error or missing family)
            return  # Exit early, can't process this family

        family_obj = Family(family_data)  # Create Family object from server JSON data

        # Add family to tree (thread-safe with lock)
        with lock:  # Acquire lock before modifying shared tree
            if not tree.does_family_exist(fam_id):  # Double-check it wasn't added by another thread
                tree.add_family(family_obj)  # Add the family to our tree

        # Get all person IDs we need to fetch from this family
        person_ids = []  # Initialize empty list for person IDs
        if family_obj.get_husband() is not None:  # If family has a husband
            person_ids.append(family_obj.get_husband())  # Add husband ID to list
        if family_obj.get_wife() is not None:  # If family has a wife
            person_ids.append(family_obj.get_wife())  # Add wife ID to list
        person_ids.extend(family_obj.get_children())  # Add all children IDs to list

        # Fetch all people concurrently (KEY OPTIMIZATION #1)
        person_threads = []  # List to track all person-fetching threads
        people_data = {}  # Dictionary to store person data from all threads

        def fetch_person(person_id):
            """
            Fetch a single person's data from the server.
            Runs concurrently with other person fetches.
            """
            person_data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')  # Get person from API
            if person_data is not None:  # If server returned valid data
                with lock:  # Acquire lock before writing to shared dictionary
                    people_data[person_id] = person_data  # Store person data by ID

        for person_id in person_ids:  # For each person we need to fetch
            thread = threading.Thread(target=fetch_person, args=(person_id,))  # Create thread for this person
            thread.start()  # Start thread to fetch person data concurrently
            person_threads.append(thread)  # Track thread for later joining

        # Wait for all person fetches to complete
        for thread in person_threads:  # For each person-fetching thread
            thread.join()  # Wait for this thread to complete before continuing

        # Add all people to tree and collect parent family IDs for recursion
        parent_ids = []  # List to track unique parent family IDs
        for person_id, person_data in people_data.items():  # For each person we fetched
            person_obj = Person(person_data)  # Create Person object from JSON data
            with lock:  # Acquire lock before modifying shared tree
                if not tree.does_person_exist(person_id):  # If person not already in tree
                    tree.add_person(person_obj)  # Add person to tree

            # Collect parent family IDs for recursion (to go up the tree)
            parent_fam_id = person_obj.get_parentid()  # Get this person's parent family ID
            if parent_fam_id is not None and parent_fam_id not in parent_ids:  # If has parents and not already tracked
                parent_ids.append(parent_fam_id)  # Add to list of families to process next

        # Recursively process parent families concurrently (KEY OPTIMIZATION #2)
        parent_threads = []  # List to track recursive threads
        for parent_id in parent_ids:  # For each parent family to process
            thread = threading.Thread(target=process_family, args=(parent_id,))  # Create thread for recursive call
            thread.start()  # Start thread to explore this branch concurrently
            parent_threads.append(thread)  # Track thread for joining

        # Wait for all recursive calls to complete
        for thread in parent_threads:  # For each recursive thread
            thread.join()  # Wait for this branch to complete before returning

    # Start the recursive process with the initial family
    process_family(family_id)  # Begin depth-first search from starting family

# -----------------------------------------------------------------------------
def breadth_fs_pedigree(family_id, tree):
    """
    Part 2: Breadth-First Search with threading to retrieve family tree.
    Processes the tree level by level, fetching all families at each generation
    before moving to the next generation.
    """

    lock = threading.Lock()  # Create lock for thread-safe access to shared data
    current_level = [family_id]  # Start with the initial family ID in first level

    while current_level:  # Continue while there are families to process at this level
        next_level = []  # Initialize list for family IDs at the next generation
        level_threads = []  # List to track threads processing families at this level

        def process_family(fam_id):
            """
            Process a single family: fetch it, add to tree, fetch all people,
            and collect parent IDs for the next level.
            """
            if fam_id is None:  # If no family ID provided
                return  # Exit early

            # Check if family already exists (avoid duplicate work)
            with lock:  # Acquire lock for thread-safe read
                if tree.does_family_exist(fam_id):  # If already processed
                    return  # Skip this family

            # Get family data from server
            family_data = get_data_from_server(f'{TOP_API_URL}/family/{fam_id}')  # Fetch family via HTTP
            if family_data is None:  # If server returned nothing
                return  # Can't process, exit

            family_obj = Family(family_data)  # Create Family object from JSON

            # Add family to tree (thread-safe)
            with lock:  # Acquire lock before modifying tree
                if not tree.does_family_exist(fam_id):  # Double-check not added by another thread
                    tree.add_family(family_obj)  # Add family to tree

            # Get all person IDs in this family
            person_ids = []  # Initialize person ID list
            if family_obj.get_husband() is not None:  # If has husband
                person_ids.append(family_obj.get_husband())  # Add husband ID
            if family_obj.get_wife() is not None:  # If has wife
                person_ids.append(family_obj.get_wife())  # Add wife ID
            person_ids.extend(family_obj.get_children())  # Add all children IDs

            # Fetch all people concurrently (reduces wait time significantly)
            person_threads = []  # Track person-fetching threads
            people_data = {}  # Store fetched person data

            def fetch_person(person_id):
                """Fetch one person's data concurrently."""
                person_data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')  # Fetch person
                if person_data is not None:  # If got valid data
                    with lock:  # Thread-safe write to shared dict
                        people_data[person_id] = person_data  # Store person data

            for person_id in person_ids:  # For each person to fetch
                thread = threading.Thread(target=fetch_person, args=(person_id,))  # Create thread
                thread.start()  # Start fetching concurrently
                person_threads.append(thread)  # Track for joining

            # Wait for all person fetches to finish
            for thread in person_threads:  # For each person thread
                thread.join()  # Wait for completion

            # Add all people to tree and collect parent family IDs for next level
            for person_id, person_data in people_data.items():  # For each fetched person
                person_obj = Person(person_data)  # Create Person object
                with lock:  # Thread-safe tree modification
                    if not tree.does_person_exist(person_id):  # If not already in tree
                        tree.add_person(person_obj)  # Add to tree

                # Add parent family to next level for BFS continuation
                parent_fam_id = person_obj.get_parentid()  # Get parent family ID
                if parent_fam_id is not None:  # If person has parents
                    with lock:  # Thread-safe access to next_level list
                        if parent_fam_id not in next_level and not tree.does_family_exist(parent_fam_id):  # If not already queued or processed
                            next_level.append(parent_fam_id)  # Queue for next generation

        # Process all families in current level concurrently (KEY OPTIMIZATION - concurrent execution)
        for fam_id in current_level:  # For each family at this generation level
            thread = threading.Thread(target=process_family, args=(fam_id,))  # Create thread for this family
            thread.start()  # Start processing concurrently with other families at this level
            level_threads.append(thread)  # Track for joining

        # Wait for all families in current level to be processed before moving to next level
        for thread in level_threads:  # For each family thread at this level
            thread.join()  # Wait for completion (ensures level is complete before advancing)

        # Move to next level (next generation up the tree)
        current_level = next_level  # Set current level to the collected parent families

# -----------------------------------------------------------------------------
def breadth_fs_pedigree_limit5(family_id, tree):
    """
    Part 3 (BONUS): Breadth-First Search with 5-thread concurrency limit.
    Same as Part 2 but uses a Semaphore to ensure no more than 5 concurrent
    server API calls at any time.
    """

    lock = threading.Lock()  # Lock for thread-safe tree access
    semaphore = threading.Semaphore(5)  # Semaphore to limit concurrent API calls to 5
    current_level = [family_id]  # Start with initial family at first level

    def get_data_limited(url):
        """
        Wrapper around get_data_from_server that enforces the 5-concurrent-call limit.
        The semaphore blocks if 5 calls are already active.
        """
        with semaphore:  # Acquire semaphore permit (blocks if 5 already active)
            return get_data_from_server(url)  # Make API call (permit automatically released on exit)

    while current_level:  # While there are families to process at this level
        next_level = []  # Families for next generation
        level_threads = []  # Threads processing this level

        def process_family(fam_id):
            """Process a single family with semaphore-limited API calls."""
            if fam_id is None:  # No family to process
                return  # Exit early

            # Check if family already exists
            with lock:  # Thread-safe check
                if tree.does_family_exist(fam_id):  # Already processed
                    return  # Skip

            # Get family data (limited by semaphore to 5 concurrent calls)
            family_data = get_data_limited(f'{TOP_API_URL}/family/{fam_id}')  # Semaphore-limited fetch
            if family_data is None:  # If no data returned
                return  # Can't process

            family_obj = Family(family_data)  # Create Family object

            # Add family to tree (thread-safe)
            with lock:  # Lock for tree modification
                if not tree.does_family_exist(fam_id):  # Double-check not added
                    tree.add_family(family_obj)  # Add to tree

            # Get all person IDs to fetch
            person_ids = []  # Person ID list
            if family_obj.get_husband() is not None:  # Has husband
                person_ids.append(family_obj.get_husband())  # Add husband
            if family_obj.get_wife() is not None:  # Has wife
                person_ids.append(family_obj.get_wife())  # Add wife
            person_ids.extend(family_obj.get_children())  # Add children

            # Fetch all people concurrently (each fetch limited by semaphore)
            person_threads = []  # Track person threads
            people_data = {}  # Store person data

            def fetch_person(person_id):
                """Fetch person with semaphore limit."""
                person_data = get_data_limited(f'{TOP_API_URL}/person/{person_id}')  # Semaphore-limited fetch
                if person_data is not None:  # Got data
                    with lock:  # Thread-safe write
                        people_data[person_id] = person_data  # Store data

            for person_id in person_ids:  # For each person
                thread = threading.Thread(target=fetch_person, args=(person_id,))  # Create thread
                thread.start()  # Start (may block on semaphore if 5 already active)
                person_threads.append(thread)  # Track

            # Wait for all person fetches to complete
            for thread in person_threads:  # For each person thread
                thread.join()  # Wait for completion

            # Add all people to tree and collect parent family IDs
            for person_id, person_data in people_data.items():  # For each person
                person_obj = Person(person_data)  # Create Person object
                with lock:  # Thread-safe add
                    if not tree.does_person_exist(person_id):  # Not already in tree
                        tree.add_person(person_obj)  # Add person

                # Add parent family to next level
                parent_fam_id = person_obj.get_parentid()  # Get parent family
                if parent_fam_id is not None:  # Has parents
                    with lock:  # Thread-safe next_level access
                        if parent_fam_id not in next_level and not tree.does_family_exist(parent_fam_id):  # Not queued or processed
                            next_level.append(parent_fam_id)  # Queue for next level

        # Process all families in current level concurrently (API calls limited by semaphore)
        for fam_id in current_level:  # For each family at this level
            thread = threading.Thread(target=process_family, args=(fam_id,))  # Create thread
            thread.start()  # Start (actual API calls limited by semaphore inside)
            level_threads.append(thread)  # Track thread

        # Wait for all families in current level to be processed
        for thread in level_threads:  # For each level thread
            thread.join()  # Wait for completion

        # Move to next level
        current_level = next_level  # Advance to next generation
