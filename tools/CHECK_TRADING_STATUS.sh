#!/bin/bash
# Quick status check for SØWL trading pipeline

cd "$(dirname "$0")/.."

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "              SØWL TRADING PIPELINE STATUS"
echo "═══════════════════════════════════════════════════════════"
echo ""

# Check trading loop
TRADING_PID=$(ps aux | grep "trading_loop_15min.py" | grep -v grep | awk '{print $2}')
if [ -n "$TRADING_PID" ]; then
    ELAPSED=$(ps -p $TRADING_PID -o etime= | tr -d ' ')
    echo "✅ Trading Loop: RUNNING (PID $TRADING_PID, uptime: $ELAPSED)"
else
    echo "❌ Trading Loop: NOT RUNNING"
fi

# Check bookmark monitor
BOOKMARK_PID=$(ps aux | grep "bookmark_live_monitor.py" | grep -v grep | awk '{print $2}')
if [ -n "$BOOKMARK_PID" ]; then
    echo "✅ Bookmark Monitor: RUNNING (PID $BOOKMARK_PID)"
else
    echo "⚠️  Bookmark Monitor: NOT RUNNING (optional)"
fi

# Count cycles
CYCLE_COUNT=$(ls BRAIN/INTEL/trades/cycle_*.json 2>/dev/null | wc -l | tr -d ' ')
echo ""
echo "📊 Trading Cycles Completed: $CYCLE_COUNT"

# Show latest cycle
LATEST=$(ls -t BRAIN/INTEL/trades/cycle_*.json 2>/dev/null | head -1)
if [ -n "$LATEST" ]; then
    TIMESTAMP=$(basename "$LATEST" | sed 's/cycle_//' | sed 's/.json//')
    SIGNAL_COUNT=$(cat "$LATEST" | grep -o '"signal_count": [0-9]*' | awk '{print $2}')
    DECISION=$(cat "$LATEST" | grep -o '"analysis":.*RECOMMENDED ACTION.*EXECUTE NOW\|WAIT\|PASS' | head -1)

    echo "📁 Latest Cycle: $TIMESTAMP"
    echo "   Signals: $SIGNAL_COUNT"

    if echo "$DECISION" | grep -q "EXECUTE"; then
        echo "   Decision: 🚀 EXECUTE"
    elif echo "$DECISION" | grep -q "WAIT"; then
        echo "   Decision: ⏸️  WAIT"
    elif echo "$DECISION" | grep -q "PASS"; then
        echo "   Decision: ⏭️  PASS"
    else
        echo "   Decision: (analyzing...)"
    fi
fi

echo ""
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📖 Read full status:"
echo "   • QUICK-STATUS.md (summary)"
echo "   • DEPLOYMENT-STATUS.md (detailed)"
echo ""
echo "🔧 Commands:"
echo "   • View latest analysis: cat '$LATEST'"
echo "   • Watch live: tail -f BRAIN/INTEL/trades/cycle_*.json"
echo "   • Enable live bookmarks: ./tools/START_TWITTER_AUTH.sh"
echo ""
