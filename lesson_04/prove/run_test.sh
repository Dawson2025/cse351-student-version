#!/bin/bash
# Test runner for Lesson 04 optimizations

cd "/home/dawson/code/Parallelism and Concurrency/real/cse351-student-version/lesson_04/prove"

# Kill any existing servers
pkill -9 -f "server.py" 2>/dev/null || true
sleep 2

# Start fresh server
echo "Starting server..."
python3 server.py > /tmp/server_test.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
sleep 3

# Run assignment
echo "Running assignment..."
START_TIME=$(date +%s)
python3 assignment04.py > /tmp/assignment_test.log 2>&1
RESULT=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Kill server
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

# Report results
echo "================================================"
echo "Test completed in $DURATION seconds"
echo "Assignment exit code: $RESULT"
echo "================================================"
echo ""
echo "Server summary:"
tail -10 /tmp/server_test.log | grep -E "(Total|Calls|time|threads)"
echo ""
echo "Assignment log:"
cat logs/assignment.log | tail -5
echo ""
echo "Full output saved to:"
echo "  Server: /tmp/server_test.log"
echo "  Assignment: /tmp/assignment_test.log"

