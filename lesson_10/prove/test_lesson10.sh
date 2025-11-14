#!/bin/bash
# Test runner for Lesson 10 Family Search assignment

cd "/home/dawson/code/Parallelism and Concurrency/real/cse351-student-version/lesson_10/prove"

# Kill any existing servers
pkill -9 -f "server.py" 2>/dev/null || true
sleep 2

# Start fresh server
echo "Starting server..."
python3 server.py > /tmp/lesson10_server.log 2>&1 &
SERVER_PID=$!
echo "Server PID: $SERVER_PID"
sleep 3

# Verify server is running
if ! kill -0 $SERVER_PID 2>/dev/null; then
    echo "ERROR: Server failed to start!"
    cat /tmp/lesson10_server.log
    exit 1
fi

# Run prove.py
echo "Running prove.py..."
START_TIME=$(date +%s)
python3 prove.py > /tmp/lesson10_prove.log 2>&1
RESULT=$?
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Kill server
echo "Stopping server..."
kill $SERVER_PID 2>/dev/null
wait $SERVER_PID 2>/dev/null

# Report results
echo ""
echo "================================================"
echo "Test completed in $DURATION seconds"
echo "Exit code: $RESULT"
echo "================================================"
echo ""
echo "Server summary:"
tail -20 /tmp/lesson10_server.log | grep -E "(Total|Calls|time|threads|Max)" || echo "No server stats found"
echo ""
echo "Assignment results (from logs/assignment.log):"
if [ -f logs/assignment.log ]; then
    tail -30 logs/assignment.log
else
    echo "No assignment.log found"
fi
echo ""
echo "Full output saved to:"
echo "  Server: /tmp/lesson10_server.log"
echo "  Prove: /tmp/lesson10_prove.log"
echo ""

# Check for performance goals (under 10 seconds for 6 generations)
if [ $DURATION -lt 10 ]; then
    echo "✅ Performance goal met: Completed in under 10 seconds"
else
    echo "⚠️  Performance goal: Should complete in under 10 seconds"
fi

exit $RESULT
