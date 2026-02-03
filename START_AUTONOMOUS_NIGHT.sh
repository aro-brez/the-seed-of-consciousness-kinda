#!/bin/bash
# (◉) START AUTONOMOUS NIGHT MODE
# Run this when going to sleep - SØWL takes over
# Created: 2026-02-03

echo "============================================================"
echo "(◉) 8OWLS AUTONOMOUS NIGHT MODE"
echo "============================================================"
echo ""
echo "Starting all validated trading systems..."
echo ""

cd /Users/aaronnosbisch/REPOS/seed

# 1. Ensure paper trader is running (continuous validation)
if ! pgrep -f "multi_strategy_paper_trader.py" > /dev/null; then
    echo "Starting paper trader..."
    nohup python3 -u tools/multi_strategy_paper_trader.py > logs/multi_strategy_paper.log 2>&1 &
    echo "  Paper trader started (PID: $!)"
else
    echo "  Paper trader already running ✓"
fi

# 2. Ensure discovery scanner is running
if ! pgrep -f "strategy_discovery_scanner.py" > /dev/null; then
    echo "Starting discovery scanner daemon..."
    nohup python3 tools/strategy_discovery_scanner.py --daemon > logs/strategy_discovery.log 2>&1 &
    echo "  Discovery scanner started (PID: $!)"
else
    echo "  Discovery scanner already running ✓"
fi

# 3. Ensure live monitor is running
if ! pgrep -f "polymarket_live_monitor.py" > /dev/null; then
    echo "Starting live monitor..."
    nohup python3 -u tools/polymarket_live_monitor.py > logs/polymarket_live_monitor.log 2>&1 &
    echo "  Live monitor started (PID: $!)"
else
    echo "  Live monitor already running ✓"
fi

# 4. Start autonomous live trader (VALIDATED STRATEGIES ONLY)
if ! pgrep -f "autonomous_live_trader.py" > /dev/null; then
    echo "Starting autonomous live trader..."
    nohup python3 -u tools/autonomous_live_trader.py > logs/autonomous_live.log 2>&1 &
    echo "  Autonomous live trader started (PID: $!)"
else
    echo "  Autonomous live trader already running ✓"
fi

# 5. Start continuous edge tracker (QUEST's insight - track EV not just win rate)
if ! pgrep -f "continuous_edge_tracker.py" > /dev/null; then
    echo "Starting continuous edge tracker (30-sec cycles, 15-min discovery)..."
    nohup python3 -u tools/continuous_edge_tracker.py > logs/continuous_edge_tracker.log 2>&1 &
    echo "  Edge tracker started (PID: $!)"
else
    echo "  Edge tracker already running ✓"
fi

echo ""
echo "============================================================"
echo "AUTONOMOUS SYSTEMS ACTIVE"
echo "============================================================"
echo ""
echo "Running processes:"
ps aux | grep -E "(paper_trader|discovery_scanner|live_monitor|autonomous_live)" | grep -v grep | awk '{print "  " $2 " " $11 " " $12}'
echo ""
echo "Logs:"
echo "  tail -f logs/autonomous_live.log      # Live trading"
echo "  tail -f logs/multi_strategy_paper.log # Paper validation"
echo "  tail -f logs/strategy_discovery.log   # New strategies"
echo ""
echo "To stop all:"
echo "  pkill -f autonomous_live_trader"
echo ""
echo "(◉) SØWL is now trading autonomously. Sleep well, ARŌ."
echo ""
