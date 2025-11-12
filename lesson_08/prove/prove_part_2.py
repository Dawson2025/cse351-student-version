"""
Course: CSE 351 
Assignment: 08 Prove Part 2
File:   prove_part_2.py
Author: <Add name here>

Purpose: Part 2 of assignment 8, finding the path to the end of a maze using recursion.

Instructions:
- Do not create classes for this assignment, just functions.
- Do not use any other Python modules other than the ones included.
- You MUST use recursive threading to find the end of the maze.
- Each thread MUST have a different color than the previous thread:
    - Use get_color() to get the color for each thread; you will eventually have duplicated colors.
    - Keep using the same color for each branch that a thread is exploring.
    - When you hit an intersection spin off new threads for each option and give them their own colors.

This code is not interested in tracking the path to the end position. Once you have completed this
program however, describe how you could alter the program to display the found path to the exit
position:

What would be your strategy?

While exploring, keep a dictionary that maps each visited cell to the parent cell that discovered it. When a thread reaches the exit, use that dictionary to walk backwards from the exit to the start and draw the path.

Why would it work?

Every cell is discovered exactly once in this search, so the parent dictionary forms a tree rooted at the start. Following parent pointers from the exit inevitably leads back to the start, giving the path in reverse order without needing to revisit cells.

"""

import math
import threading 
from screen import Screen
from maze import Maze
import sys
import cv2

# Include cse 351 files
from cse351 import *

SCREEN_SIZE = 700
COLOR = (0, 0, 255)
COLORS = (
    (0,0,255),
    (0,255,0),
    (255,0,0),
    (255,255,0),
    (0,255,255),
    (255,0,255),
    (128,0,0),
    (128,128,0),
    (0,128,0),
    (128,0,128),
    (0,128,128),
    (0,0,128),
    (72,61,139),
    (143,143,188),
    (226,138,43),
    (128,114,250)
)
SLOW_SPEED = 100
FAST_SPEED = 0  # 0 = instant, no delay

# Globals
current_color_index = 0
thread_count = 0
stop = False
speed = FAST_SPEED  # Start with fast speed for automated testing

visited_positions = set()
visited_lock = threading.Lock()
thread_lock = threading.Lock()


def _register_thread():
    global thread_count
    with thread_lock:
        thread_count += 1


def _claim_position(position):
    with visited_lock:
        if position in visited_positions:
            return False
        visited_positions.add(position)
        return True

def get_color():
    """ Returns a different color when called """
    global current_color_index
    if current_color_index >= len(COLORS):
        current_color_index = 0
    color = COLORS[current_color_index]
    current_color_index += 1
    return color


# TODO: Add any function(s) you need, if any, here.


def _explore_branch(maze, row, col, color, already_claimed=False):
    global stop

    if stop:
        return

    if not already_claimed:
        if not _claim_position((row, col)):
            return

    maze.move(row, col, color)

    if maze.at_end(row, col):
        stop = True
        return

    # Get all possible moves and claim them
    moves = maze.get_possible_moves(row, col)
    unclaimed_moves = []
    for next_row, next_col in moves:
        if stop:
            return
        if _claim_position((next_row, next_col)):
            unclaimed_moves.append((next_row, next_col))
    
    # Create and start threads for all paths except the first one
    # This ensures threads explore in parallel
    child_threads = []
    for idx, (next_row, next_col) in enumerate(unclaimed_moves):
        if idx == 0:
            # Current thread will explore this path - save it for last
            continue
        else:
            # Create new thread for this path
            branch_color = get_color()
            thread = threading.Thread(
                target=_explore_branch,
                args=(maze, next_row, next_col, branch_color, True),
            )
            _register_thread()
            child_threads.append(thread)
            thread.start()
    
    # Now explore the first path with the current thread
    if unclaimed_moves and not stop:
        next_row, next_col = unclaimed_moves[0]
        _explore_branch(maze, next_row, next_col, color, already_claimed=True)
    
    # Wait for all child threads to complete
    for thread in child_threads:
        thread.join()


def solve_find_end(maze):
    """ Finds the end position using threads. Nothing is returned. """
    # When one of the threads finds the end position, stop all of them.
    global stop, visited_positions, current_color_index, thread_count
    stop = False
    visited_positions = set()
    current_color_index = 0
    thread_count = 0

    start_row, start_col = maze.get_start_pos()
    initial_color = get_color()

    def root_runner():
        _explore_branch(maze, start_row, start_col, initial_color)

    root_thread = threading.Thread(target=root_runner)
    _register_thread()
    root_thread.start()
    root_thread.join()




def find_end(log, filename, delay):
    """ Do not change this function """

    global thread_count
    global speed

    # create a Screen Object that will contain all of the drawing commands
    screen = Screen(SCREEN_SIZE, SCREEN_SIZE)
    screen.background((255, 255, 0))

    maze = Maze(screen, SCREEN_SIZE, SCREEN_SIZE, filename, delay=delay)

    solve_find_end(maze)

    log.write(f'Number of drawing commands = {screen.get_command_count()}')
    log.write(f'Number of threads created  = {thread_count}')

    done = False
    while not done:
        if screen.play_commands(speed): 
            key = cv2.waitKey(1)
            if key == ord('1'):
                speed = SLOW_SPEED
            elif key == ord('2'):
                speed = FAST_SPEED
            elif key == ord('q'):
                exit()
            elif key != ord('p'):
                done = True
        else:
            done = True


def find_ends(log):
    """ Do not change this function """

    files = (
        ('very-small.bmp', True),
        ('very-small-loops.bmp', True),
        ('small.bmp', True),
        ('small-loops.bmp', True),
        ('small-odd.bmp', True),
        ('small-open.bmp', False),
        ('large.bmp', False),
        ('large-loops.bmp', False),
        ('large-squares.bmp', False),
        ('large-open.bmp', False)
    )

    log.write('*' * 40)
    log.write('Part 2')
    for filename, delay in files:
        filename = f'./mazes/{filename}'
        log.write()
        log.write(f'File: {filename}')
        find_end(log, filename, delay)
    log.write('*' * 40)


def main():
    """ Do not change this function """
    sys.setrecursionlimit(5000)
    log = Log(show_terminal=True)
    find_ends(log)


if __name__ == "__main__":
    main()
