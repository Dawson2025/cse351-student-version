"""
Fully documented version of the merge sort implementations used in CSE 351.
Each line includes an explanatory comment for instructional clarity.
"""

import time  # Use high-resolution timer for benchmarking
import random  # Generate the random input data to be sorted
import threading  # Create threads for the threaded merge sort variant
import multiprocessing as mp  # Create processes/queues for the process variant

from cse351 import *  # Course-provided helpers (kept as-is per starter instructions)


# Prevent creating excessive threads or processes on tiny partitions.
THREAD_THRESHOLD = 50_000  # Spawn threads only when a slice is at least this large
PROCESS_THRESHOLD = 100_000  # Spawn processes only when a slice is at least this large


def merge_sort(arr):
    """Baseline recursive merge sort (unchanged from starter)."""

    if len(arr) > 1:  # Recurse only if there are at least two elements to sort
        mid = len(arr) // 2  # Find the midpoint of the slice
        L = arr[:mid]  # Take left half of the list
        R = arr[mid:]  # Take right half of the list

        merge_sort(L)  # Recurse to sort the left half
        merge_sort(R)  # Recurse to sort the right half

        i = j = k = 0  # Track positions for left, right, and merged array

        while i < len(L) and j < len(R):  # Merge while both halves have elements
            if L[i] < R[j]:  # Pull from left when smaller
                arr[k] = L[i]  # Write left value into merged array
                i += 1  # Move left index
            else:  # Otherwise pull from right
                arr[k] = R[j]  # Write right value into merged array
                j += 1  # Move right index
            k += 1  # Move merged array index

        while i < len(L):  # Copy any remaining elements from the left half
            arr[k] = L[i]
            i += 1
            k += 1

        while j < len(R):  # Copy any remaining elements from the right half
            arr[k] = R[j]
            j += 1
            k += 1


def _merge_arrays(arr, left, right):
    """Merge two sorted lists into ``arr`` in-place."""

    i = j = k = 0  # Track indices for left, right, and destination array

    while i < len(left) and j < len(right):  # Merge until one side is exhausted
        if left[i] < right[j]:  # Take from left when smaller
            arr[k] = left[i]
            i += 1
        else:  # Otherwise take from right
            arr[k] = right[j]
            j += 1
        k += 1  # Advance destination slot

    while i < len(left):  # Copy any remaining from the left half
        arr[k] = left[i]
        i += 1
        k += 1

    while j < len(right):  # Copy any remaining from the right half
        arr[k] = right[j]
        j += 1
        k += 1


def is_sorted(arr):
    """Return True if the array is non-decreasing."""
    return all(arr[i] <= arr[i + 1] for i in range(len(arr) - 1))  # Check pairs in order


def merge_normal(arr):
    """Sequential merge sort wrapper for timing harness."""
    merge_sort(arr)  # Use the baseline implementation


def merge_sort_thread(arr):
    """Threaded merge sort that recurses in parallel above a size threshold."""

    if len(arr) <= 1:  # Return when the slice is already sorted
        return

    mid = len(arr) // 2  # Find midpoint for splitting
    left = arr[:mid]  # Split out left partition
    right = arr[mid:]  # Split out right partition

    if len(arr) >= THREAD_THRESHOLD:  # Spawn threads only for large partitions
        left_thread = threading.Thread(target=merge_sort_thread, args=(left,))  # Launch worker for left
        right_thread = threading.Thread(target=merge_sort_thread, args=(right,))  # Launch worker for right
        left_thread.start()  # Begin left sort in parallel
        right_thread.start()  # Begin right sort in parallel
        left_thread.join()  # Wait for left worker to finish
        right_thread.join()  # Wait for right worker to finish
    else:  # For small slices, stay in the current thread to reduce overhead
        merge_sort(left)
        merge_sort(right)

    _merge_arrays(arr, left, right)  # Merge the sorted halves back into arr


def merge_sort_process(arr):
    """Process-based merge sort that forks when partitions are large enough."""

    if len(arr) <= 1:  # Return when the slice is already sorted
        return

    mid = len(arr) // 2  # Find midpoint for splitting
    left = arr[:mid]  # Split out left partition
    right = arr[mid:]  # Split out right partition

    if len(arr) >= PROCESS_THRESHOLD:  # Fork only for large slices to offset overhead
        left_queue = mp.Queue()  # Create queue to collect sorted left data from child
        right_queue = mp.Queue()  # Create queue to collect sorted right data from child

        left_proc = mp.Process(target=_merge_sort_process_worker, args=(left, left_queue))  # Launch left child
        right_proc = mp.Process(target=_merge_sort_process_worker, args=(right, right_queue))  # Launch right child

        left_proc.start()  # Start left process
        right_proc.start()  # Start right process

        left = left_queue.get()  # Pull sorted left list
        right = right_queue.get()  # Pull sorted right list

        left_proc.join()  # Wait for left process to exit
        right_proc.join()  # Wait for right process to exit
    else:  # For small slices, stay in the current process
        merge_sort(left)
        merge_sort(right)

    _merge_arrays(arr, left, right)  # Merge sorted halves into the destination slice


def _merge_sort_process_worker(sub_arr, queue):
    """Child-process worker: sort its partition and return via queue."""
    merge_sort_process(sub_arr)  # Sort recursively (may spawn more children)
    queue.put(sub_arr)  # Send sorted result back to parent


def main():
    """Benchmark the three merge sort variants on a 1,000,000-element list."""

    merges = [  # List of (function, description) for the benchmarking loop
        (merge_sort, ' Normal Merge Sort '),
        (merge_sort_thread, ' Threaded Merge Sort '),
        (merge_sort_process, ' Processes Merge Sort ')
    ]

    for merge_function, desc in merges:  # Run each variant in sequence
        arr = [random.randint(1, 10_000_000) for _ in range(1_000_000)]  # Build fresh random data

        print(f'\n{desc:-^70}')  # Print header centered with dashes
        print(f'Before: {str(arr[:5])[1:-1]} ... {str(arr[-5:])[1:-1]}')  # Show sample before
        start_time = time.perf_counter()  # Start timer

        merge_function(arr)  # Execute the chosen merge strategy

        end_time = time.perf_counter()  # Stop timer
        print(f'Sorted: {str(arr[:5])[1:-1]} ... {str(arr[-5:])[1:-1]}')  # Show sample after

        print('Array is sorted' if is_sorted(arr) else 'Array is NOT sorted')  # Verify correctness
        print(f'Time to sort = {end_time - start_time:.14f}')  # Report duration


if __name__ == '__main__':  # Standard Python entry-point guard
    main()  # Run the benchmark when executed as a script
