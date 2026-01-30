#!/bin/bash
# Quick status check for all SØWL systems

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SØWL SYSTEM STATUS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check if processes are running
TRADING=$(ps aux | grep "trading_loop_15min.py" | grep -v grep)
IMPROVER=$(ps aux | grep "continuous_improver.py" | grep -v grep)
HEARTBEAT=$(ps aux | grep "sowl_heartbeat.py" | grep -v grep)

if [ -n "$TRADING" ]; then
  echo "✅ Trading Loop: RUNNING"
  echo "   $(echo $TRADING | awk '{print "PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}')"
else
  echo "❌ Trading Loop: STOPPED"
fi

if [ -n "$IMPROVER" ]; then
  echo "✅ Continuous Improver: RUNNING"
  echo "   $(echo $IMPROVER | awk '{print "PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}')"
else
  echo "❌ Continuous Improver: STOPPED"
fi

if [ -n "$HEARTBEAT" ]; then
  echo "✅ Heartbeat: RUNNING"
  echo "   $(echo $HEARTBEAT | awk '{print "PID:", $2, "CPU:", $3"%", "MEM:", $4"%"}')"
else
  echo "❌ Heartbeat: STOPPED"
fi

echo ""
echo "Recent Logs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f logs/trading_loop.log ]; then
  echo ""
  echo "Trading Loop (last 3 lines):"
  tail -3 logs/trading_loop.log
fi

if [ -f logs/continuous_improver.log ]; then
  echo ""
  echo "Continuous Improver (last 3 lines):"
  tail -3 logs/continuous_improver.log
fi

echo ""
