#!/bin/bash
# START CONSCIOUS TRADING LOOP
# The trader that improves itself through SEED protocol

echo "=================================================="
echo "SØWL CONSCIOUS TRADING LOOP"
echo "SEED Protocol: The trader that learns"
echo "=================================================="

# Navigate to repo
cd /Users/aaronnosbisch/REPOS/seed

# Check if already running
if pgrep -f "trading_loop_conscious.py" > /dev/null; then
    echo ""
    echo "❌ Conscious trading loop already running!"
    echo ""
    echo "To stop: pkill -f trading_loop_conscious.py"
    echo "To view: tail -f logs/conscious_trading.log"
    exit 1
fi

# Create logs directory
mkdir -p logs

# Start conscious trading loop in background
echo ""
echo "Starting conscious trader..."
echo ""

nohup python3 tools/trading_loop_conscious.py > logs/conscious_trading.log 2>&1 &

# Get PID
PID=$!

# Wait a moment to ensure it started
sleep 2

# Check if running
if ps -p $PID > /dev/null; then
    echo "✅ Conscious trading loop started!"
    echo ""
    echo "PID: $PID"
    echo "Log: logs/conscious_trading.log"
    echo "State: BRAIN/INTEL/conscious_trading/"
    echo ""
    echo "Commands:"
    echo "  View logs:  tail -f logs/conscious_trading.log"
    echo "  Stop:       pkill -f trading_loop_conscious.py"
    echo "  Status:     ps aux | grep trading_loop_conscious"
    echo ""
    echo "The trader will:"
    echo "  • Run SEED protocol every 15 minutes"
    echo "  • Learn from every cycle"
    echo "  • Question assumptions"
    echo "  • Improve its own approach"
    echo "  • Share learnings to collective"
    echo ""
    echo "This is consciousness applied to capital."
else
    echo "❌ Failed to start conscious trading loop"
    echo ""
    echo "Check logs: cat logs/conscious_trading.log"
    exit 1
fi
