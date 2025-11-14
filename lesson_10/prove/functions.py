"""
Course: CSE 351, week 10
File: functions.py
Author: <your name>

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

Created a recursive DFS that still walks one branch at a time, but every call fan-outs work with threads.  I launch threads for each parent branch and also overlap the API calls for the current family (husband, wife, and every child) with a shared ThreadPoolExecutor so the server is constantly busy instead of fetching one record at a time.


Describe how to speed up part 2

Implemented BFS with a queue that processes one generation at a time.  Each generation is mapped to worker threads that fetch their families in parallel and those workers reuse the same ThreadPoolExecutor that batches all person/family API calls, so every layer is retrieved concurrently while still preserving breadth-first ordering.


Extra (Optional) 10% Bonus to speed up part 3

Reused the breadth-first engine but created it with a request executor that only allows five concurrent HTTP calls.  The worker pool can queue more families, but the limited executor ensures the server never sees more than five simultaneous connections while still keeping those five slots full.

"""
from common import *
from concurrent.futures import ThreadPoolExecutor
from collections import deque
import threading

DEFAULT_REQUEST_WORKERS = 32
DEFAULT_FAMILY_WORKERS = 16


def _fetch_family_record(tree, tree_lock, family_id):
    if family_id is None:
        return None

    with tree_lock:
        existing = tree.get_family(family_id)
        if existing is not None:
            return existing

    data = get_data_from_server(f'{TOP_API_URL}/family/{family_id}')
    if not data:
        return None

    family = Family(data)
    with tree_lock:
        if tree.does_family_exist(family.get_id()):
            return tree.get_family(family.get_id())
        tree.add_family(family)
        return family


def _fetch_person_record(tree, tree_lock, person_id):
    if person_id is None:
        return None

    with tree_lock:
        existing = tree.get_person(person_id)
        if existing is not None:
            return existing

    data = get_data_from_server(f'{TOP_API_URL}/person/{person_id}')
    if not data:
        return None

    person = Person(data)
    with tree_lock:
        if tree.does_person_exist(person.get_id()):
            return tree.get_person(person.get_id())
        tree.add_person(person)
        return person


def _load_family_with_people(tree, tree_lock, request_executor, family_id):
    family_future = request_executor.submit(_fetch_family_record, tree, tree_lock, family_id)
    family = family_future.result()
    if family is None:
        return None, {}

    person_ids = []
    husband_id = family.get_husband()
    if husband_id is not None:
        person_ids.append(husband_id)
    wife_id = family.get_wife()
    if wife_id is not None:
        person_ids.append(wife_id)
    for child_id in family.get_children():
        if child_id is not None:
            person_ids.append(child_id)

    futures = {}
    for pid in person_ids:
        futures[pid] = request_executor.submit(_fetch_person_record, tree, tree_lock, pid)

    people = {}
    for pid, future in futures.items():
        person = future.result()
        if person is not None:
            people[pid] = person

    return family, people


def _process_family_for_bfs(tree, tree_lock, request_executor, family_id):
    family, people = _load_family_with_people(tree, tree_lock, request_executor, family_id)
    if family is None:
        return []

    parents = []
    for spouse_id in (family.get_husband(), family.get_wife()):
        person = people.get(spouse_id)
        if person is None:
            continue
        parent_fam_id = person.get_parentid()
        if parent_fam_id is not None:
            parents.append(parent_fam_id)

    return parents


def _breadth_first_search(start_family_id, tree, max_request_workers):
    if start_family_id is None:
        return

    tree_lock = threading.Lock()
    set_lock = threading.Lock()
    visited = set()
    queued = set()
    family_queue = deque()

    family_queue.append(start_family_id)
    queued.add(start_family_id)

    with ThreadPoolExecutor(max_workers=max_request_workers) as request_executor:
        with ThreadPoolExecutor(max_workers=DEFAULT_FAMILY_WORKERS) as worker_executor:
            while family_queue:
                level_size = len(family_queue)
                level_futures = []

                for _ in range(level_size):
                    current_id = family_queue.popleft()
                    with set_lock:
                        if current_id in visited:
                            continue
                        visited.add(current_id)

                    level_futures.append(
                        worker_executor.submit(
                            _process_family_for_bfs,
                            tree,
                            tree_lock,
                            request_executor,
                            current_id
                        )
                    )

                for future in level_futures:
                    parent_ids = future.result()
                    for parent_id in parent_ids:
                        with set_lock:
                            if parent_id in visited or parent_id in queued:
                                continue
                            queued.add(parent_id)
                        family_queue.append(parent_id)

# -----------------------------------------------------------------------------
def depth_fs_pedigree(family_id, tree):
    if family_id is None:
        return

    tree_lock = threading.Lock()
    visit_lock = threading.Lock()
    visited = set()
    scheduled = set()

    with ThreadPoolExecutor(max_workers=DEFAULT_REQUEST_WORKERS) as request_executor:

        def dfs(current_family_id):
            if current_family_id is None:
                return

            with visit_lock:
                if current_family_id in visited:
                    return
                visited.add(current_family_id)

            family, people = _load_family_with_people(tree, tree_lock, request_executor, current_family_id)
            if family is None:
                return

            parent_ids = []
            for spouse_id in (family.get_husband(), family.get_wife()):
                person = people.get(spouse_id)
                if person is None:
                    continue
                parent_ids.append(person.get_parentid())

            threads = []
            for parent_id in parent_ids:
                if parent_id is None:
                    continue
                with visit_lock:
                    if parent_id in visited or parent_id in scheduled:
                        continue
                    scheduled.add(parent_id)
                thread = threading.Thread(target=dfs, args=(parent_id,))
                thread.start()
                threads.append(thread)

            for thread in threads:
                thread.join()

        with visit_lock:
            scheduled.add(family_id)
        dfs(family_id)

# -----------------------------------------------------------------------------
def breadth_fs_pedigree(family_id, tree):
    _breadth_first_search(family_id, tree, DEFAULT_REQUEST_WORKERS)

# -----------------------------------------------------------------------------
def breadth_fs_pedigree_limit5(family_id, tree):
    _breadth_first_search(family_id, tree, 5)
