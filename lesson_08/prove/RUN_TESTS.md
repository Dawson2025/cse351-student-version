# Lesson 08 - How to Run Tests

## Prerequisites

Make sure you have the required Python packages:
```bash
pip3 install opencv-python numpy
```

## Running Part 1 (Recursive DFS Path Finding)

```bash
cd "/home/dawson/code/Parallelism and Concurrency/real/cse351-student-version/lesson_08/prove"
python3 prove_part_1.py
```

**What to expect:**
- GUI windows will open showing each maze being solved
- The program will solve 10 mazes sequentially
- For each maze:
  - A window shows the path being explored (red path)
  - Dead ends are marked in grey (backtracking)
  - When solved, the final path is shown
  - **Press any key (except 'p') to move to next maze**
  - Press 'q' to quit entirely
  - Press '1' for slow speed, '2' for fast speed

**Expected runtime:** ~2-3 minutes total (with FAST_SPEED)

**Output:** Log file created in `logs/` folder with:
- Drawing commands count for each maze
- Path length for each maze

---

## Running Part 2 (Multi-threaded Maze Exploration)

```bash
cd "/home/dawson/code/Parallelism and Concurrency/real/cse351-student-version/lesson_08/prove"
python3 prove_part_2.py
```

**What to expect:**
- GUI windows will open showing each maze being explored
- Multiple colored threads explore different paths simultaneously
- When one thread finds the exit, all threads stop
- For each maze:
  - Watch the colored threads explore in parallel
  - **Press any key (except 'p') to move to next maze**
  - Press 'q' to quit entirely
  - Press '1' for slow speed, '2' for fast speed

**Expected runtime:** ~2-3 minutes total (with FAST_SPEED=0)

**Output:** Log file created in `logs/` folder with:
- Number of drawing commands for each maze
- **Number of threads created** for each maze (this is the key metric!)

---

## Expected Results

### Part 1 - Expected Drawing Commands & Path Lengths:
```
File: ./mazes/very-small.bmp
Drawing commands to solve = 88
Found path has length     = 11

File: ./mazes/very-small-loops.bmp
Drawing commands to solve = 352
Found path has length     = 55

File: ./mazes/small.bmp
Drawing commands to solve = 1360
Found path has length     = 79

File: ./mazes/small-loops.bmp
Drawing commands to solve = 1600
Found path has length     = 159

File: ./mazes/small-odd.bmp
Drawing commands to solve = 2536
Found path has length     = 79

File: ./mazes/small-open.bmp
Drawing commands to solve = 2496
Found path has length     = 319

File: ./mazes/large.bmp
Drawing commands to solve = 41984
Found path has length     = 1299

File: ./mazes/large-loops.bmp
Drawing commands to solve = 46064
Found path has length     = 803
```

### Part 2 - Expected Thread Counts:
```
File: ./mazes/very-small.bmp
Number of drawing commands = 84
Number of threads created  = 3        ✅

File: ./mazes/very-small-loops.bmp
Number of drawing commands = 322
Number of threads created  = 7        ✅

File: ./mazes/small.bmp
Number of drawing commands = 1740
Number of threads created  = 21       ✅

File: ./mazes/small-loops.bmp
Number of drawing commands = 2052
Number of threads created  = 33       ✅

File: ./mazes/small-odd.bmp
Number of drawing commands = 2174
Number of threads created  = 153      ✅

File: ./mazes/small-open.bmp
Number of drawing commands = 3010
Number of threads created  = 351      ✅

File: ./mazes/large.bmp
Number of drawing commands = 30936
Number of threads created  = 356      ✅

File: ./mazes/large-loops.bmp
Number of drawing commands = 29580
Number of threads created  = 464      ✅
```

---

## Checking Results

After running, check the latest log file:

```bash
# View the most recent log
cat logs/$(ls -t logs/*.log | head -1)

# Or list all logs
ls -lth logs/
```

---

## Troubleshooting

### "No display" error (WSL):
If you get display errors, you may need X11 forwarding:
```bash
# On Windows, install Xming or VcXsrv
# Then in WSL:
export DISPLAY=:0
python3 prove_part_1.py
```

### Windows close too quickly:
- The program runs with FAST_SPEED=0 by default (instant)
- You can press '1' during display to slow it down
- Or edit the code to change `speed = SLOW_SPEED` temporarily

### Want to see it run slowly:
Edit the files and change:
- `prove_part_1.py` line 29: `speed = SLOW_SPEED`
- `prove_part_2.py` line 69: `speed = SLOW_SPEED`

---

## Quick Test (Just First Maze)

If you want to test quickly without running all 10 mazes, you can temporarily modify the files list in `find_paths()` or `find_ends()` to only include the first maze:

```python
files = (
    'very-small.bmp',  # Just test this one
)
```

---

## Success Criteria

✅ **Part 1:** All 10 mazes solved, path lengths match expected values  
✅ **Part 2:** Multiple threads created (3, 7, 21, 33, 153, 351, 356, 464, etc.)  
✅ **Both:** Complete in ~2-3 minutes total  
✅ **Both:** Log files created with correct output

Good luck! 🎯

