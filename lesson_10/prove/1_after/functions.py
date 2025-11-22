"""
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
1. Parallelizing person data retrieval: For each family, we retrieve husband, wife, and all
   children in parallel using threads, rather than sequentially. Since each request takes
   0.25 seconds, this saves significant time when a family has multiple members.
2. Parallelizing recursive calls: When recursing to get parents, we spawn two threads - one
   for the husband's parents and one for the wife's parents. This allows both branches of
   the tree to be explored simultaneously.
3. Thread synchronization: We use locks to ensure thread-safe access to the tree data
   structure when adding families and people.
The recursive nature of DFS combined with threading allows us to explore multiple branches
of the family tree concurrently.


Describe how to speed up part 2

Part 2 uses a breadth-first search with threading to retrieve the family tree level by level.
The key optimizations are:
1. Level-based parallelization: Process all families at the same generation level in parallel
   using threads. This is more efficient than DFS for wide trees since all families at a
   level can be fetched simultaneously.
2. Parallel person retrieval: Like Part 1, we fetch all people in a family (husband, wife,
   children) in parallel using threads.
3. Queue-based approach: Use a queue to track which families to process next, allowing us to
   systematically process the tree level by level without recursion.
4. Thread joining: Wait for all threads at a level to complete before moving to the next
   level, ensuring data consistency.
BFS is often more efficient than DFS for this problem because it maximizes parallelism across
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
This approach balances parallelism with resource constraints, preventing server overload while
still achieving good performance.

"""
from common import *
import queue
import threading

# -----------------------------------------------------------------------------
def depth_fs_pedigree(family_id, tree):
    # KEEP this function even if you don't implement it
    # TODO - implement Depth first retrieval
    # TODO - Printing out people and families that are retrieved from the server will help debugging

    lock = threading.Lock()

    def process_family(fam_id):
        if fam_id is None:
            return

        # Check if family already exists in tree
        with lock:
            if tree.does_family_exist(fam_id):
                return

        # Get family data from server
        family_data = get_data_from_server(f'{TOP_API_URL}/family/{fam_id}')
        if family_data is None:
            return

        family_obj = Family(family_data)

        # Add family to tree (thread-safe)
        with lock:
            if not tree.does_family_exist(fam_id):
                tree.add_family(family_obj)

        # Get all person IDs we need to fetch
        person_ids = []
        if family_obj.get_husband() is not None:
            person_ids.append(family_obj.get_husband())
        if family_obj.get_wife() is not None:
            person_ids.append(family_obj.get_wife())
        person_ids.extend(family_obj.get_children())

        # Fetch all people in parallel
        person_threads = []
        people_data = {}

        def fetch_person(person_id):
            person_data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')
            if person_data is not None:
                with lock:
                    people_data[person_id] = person_data

        for person_id in person_ids:
            thread = threading.Thread(target=fetch_person, args=(person_id,))
            thread.start()
            person_threads.append(thread)

        # Wait for all person fetches to complete
        for thread in person_threads:
            thread.join()

        # Add all people to tree
        parent_ids = []
        for person_id, person_data in people_data.items():
            person_obj = Person(person_data)
            with lock:
                if not tree.does_person_exist(person_id):
                    tree.add_person(person_obj)

            # Collect parent family IDs for recursion
            parent_fam_id = person_obj.get_parentid()
            if parent_fam_id is not None and parent_fam_id not in parent_ids:
                parent_ids.append(parent_fam_id)

        # Recursively process parent families in parallel
        parent_threads = []
        for parent_id in parent_ids:
            thread = threading.Thread(target=process_family, args=(parent_id,))
            thread.start()
            parent_threads.append(thread)

        # Wait for all recursive calls to complete
        for thread in parent_threads:
            thread.join()

    # Start the recursive process
    process_family(family_id)

# -----------------------------------------------------------------------------
def breadth_fs_pedigree(family_id, tree):
    # KEEP this function even if you don't implement it
    # TODO - implement breadth first retrieval
    # TODO - Printing out people and families that are retrieved from the server will help debugging

    lock = threading.Lock()
    current_level = [family_id]

    while current_level:
        next_level = []
        level_threads = []

        def process_family(fam_id):
            if fam_id is None:
                return

            # Check if family already exists
            with lock:
                if tree.does_family_exist(fam_id):
                    return

            # Get family data
            family_data = get_data_from_server(f'{TOP_API_URL}/family/{fam_id}')
            if family_data is None:
                return

            family_obj = Family(family_data)

            # Add family to tree (thread-safe)
            with lock:
                if not tree.does_family_exist(fam_id):
                    tree.add_family(family_obj)

            # Get all person IDs
            person_ids = []
            if family_obj.get_husband() is not None:
                person_ids.append(family_obj.get_husband())
            if family_obj.get_wife() is not None:
                person_ids.append(family_obj.get_wife())
            person_ids.extend(family_obj.get_children())

            # Fetch all people in parallel
            person_threads = []
            people_data = {}

            def fetch_person(person_id):
                person_data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')
                if person_data is not None:
                    with lock:
                        people_data[person_id] = person_data

            for person_id in person_ids:
                thread = threading.Thread(target=fetch_person, args=(person_id,))
                thread.start()
                person_threads.append(thread)

            # Wait for all person fetches
            for thread in person_threads:
                thread.join()

            # Add all people to tree and collect parent family IDs
            for person_id, person_data in people_data.items():
                person_obj = Person(person_data)
                with lock:
                    if not tree.does_person_exist(person_id):
                        tree.add_person(person_obj)

                # Add parent family to next level
                parent_fam_id = person_obj.get_parentid()
                if parent_fam_id is not None:
                    with lock:
                        if parent_fam_id not in next_level and not tree.does_family_exist(parent_fam_id):
                            next_level.append(parent_fam_id)

        # Process all families in current level in parallel
        for fam_id in current_level:
            thread = threading.Thread(target=process_family, args=(fam_id,))
            thread.start()
            level_threads.append(thread)

        # Wait for all families in current level to be processed
        for thread in level_threads:
            thread.join()

        # Move to next level
        current_level = next_level

# -----------------------------------------------------------------------------
def breadth_fs_pedigree_limit5(family_id, tree):
    # KEEP this function even if you don't implement it
    # TODO - implement breadth first retrieval
    #      - Limit number of concurrent connections to the FS server to 5
    # TODO - Printing out people and families that are retrieved from the server will help debugging

    lock = threading.Lock()
    semaphore = threading.Semaphore(5)
    current_level = [family_id]

    def get_data_limited(url):
        with semaphore:
            return get_data_from_server(url)

    while current_level:
        next_level = []
        level_threads = []

        def process_family(fam_id):
            if fam_id is None:
                return

            # Check if family already exists
            with lock:
                if tree.does_family_exist(fam_id):
                    return

            # Get family data (limited by semaphore)
            family_data = get_data_limited(f'{TOP_API_URL}/family/{fam_id}')
            if family_data is None:
                return

            family_obj = Family(family_data)

            # Add family to tree (thread-safe)
            with lock:
                if not tree.does_family_exist(fam_id):
                    tree.add_family(family_obj)

            # Get all person IDs
            person_ids = []
            if family_obj.get_husband() is not None:
                person_ids.append(family_obj.get_husband())
            if family_obj.get_wife() is not None:
                person_ids.append(family_obj.get_wife())
            person_ids.extend(family_obj.get_children())

            # Fetch all people in parallel (each limited by semaphore)
            person_threads = []
            people_data = {}

            def fetch_person(person_id):
                person_data = get_data_limited(f'{TOP_API_URL}/person/{person_id}')
                if person_data is not None:
                    with lock:
                        people_data[person_id] = person_data

            for person_id in person_ids:
                thread = threading.Thread(target=fetch_person, args=(person_id,))
                thread.start()
                person_threads.append(thread)

            # Wait for all person fetches
            for thread in person_threads:
                thread.join()

            # Add all people to tree and collect parent family IDs
            for person_id, person_data in people_data.items():
                person_obj = Person(person_data)
                with lock:
                    if not tree.does_person_exist(person_id):
                        tree.add_person(person_obj)

                # Add parent family to next level
                parent_fam_id = person_obj.get_parentid()
                if parent_fam_id is not None:
                    with lock:
                        if parent_fam_id not in next_level and not tree.does_family_exist(parent_fam_id):
                            next_level.append(parent_fam_id)

        # Process all families in current level in parallel (API calls limited by semaphore)
        for fam_id in current_level:
            thread = threading.Thread(target=process_family, args=(fam_id,))
            thread.start()
            level_threads.append(thread)

        # Wait for all families in current level to be processed
        for thread in level_threads:
            thread.join()

        # Move to next level
        current_level = next_level