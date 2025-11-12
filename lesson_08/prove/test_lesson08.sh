#!/bin/bash
# Quick test for Lesson 08

cd "/home/dawson/code/Parallelism and Concurrency/real/cse351-student-version/lesson_08/prove"

echo "========================================="
echo "Testing Lesson 08 - Maze Solver"
echo "========================================="
echo ""

# Set display for headless operation (WSL)
export DISPLAY=:0
export QT_QPA_PLATFORM=offscreen

echo "Running Part 2 (Multi-threaded maze exploration)..."
echo "This requires GUI - will run and capture log"
echo ""

# Run Part 2 - it will open windows but we can close them quickly
timeout 180 python3 prove_part_2.py 2>&1 &
PART2_PID=$!

# Wait a bit then check if it's running
sleep 5
if ps -p $PART2_PID > /dev/null; then
    echo "Part 2 is running... waiting for completion or user to close windows"
    wait $PART2_PID
else
    echo "Part 2 exited early"
fi

echo ""
echo "========================================="
echo "Checking latest log file..."
echo "========================================="
LATEST_LOG=$(ls -t logs/*.log | head -1)
if [ -f "$LATEST_LOG" ]; then
    echo "Latest log: $LATEST_LOG"
    echo ""
    cat "$LATEST_LOG"
else
    echo "No log file found"
fi

echo ""
echo "========================================="
echo "Test complete!"
echo "========================================="

