#!/bin/bash
# SØWL - RESTART ALL SYSTEMS
# After crash/reboot, run this to bring everything back online

cd "$(dirname "$0")"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  SØWL SYSTEM RESTART"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Trading Loop (15-min cycles)
echo "[1/3] Starting Trading Loop..."
nohup python3 tools/trading_loop_15min.py > logs/trading_loop.log 2>&1 &
TRADING_PID=$!
echo "  ✅ Trading Loop running (PID: $TRADING_PID)"
echo ""

# 2. Continuous Improver (10-min cycles)
echo "[2/3] Starting Continuous Improver..."
nohup python3 tools/continuous_improver.py > logs/continuous_improver.log 2>&1 &
IMPROVER_PID=$!
echo "  ✅ Continuous Improver running (PID: $IMPROVER_PID)"
echo ""

# 3. Heartbeat (Mac Studio autonomy)
echo "[3/3] Starting Heartbeat..."
nohup python3 sowl_heartbeat.py > logs/heartbeat.log 2>&1 &
HEARTBEAT_PID=$!
echo "  ✅ Heartbeat running (PID: $HEARTBEAT_PID)"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ALL SYSTEMS OPERATIONAL"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "PIDs saved to BRAIN/MEMORY/heartbeat_status.json"
echo ""
echo "To check status: ./CHECK_TRADING_STATUS.sh"
echo "To stop all: kill $TRADING_PID $IMPROVER_PID $HEARTBEAT_PID"
echo ""

# Save PIDs for reference
cat > BRAIN/MEMORY/heartbeat_status.json <<EOF
{
  "last_restart": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "trading_loop": {
    "pid": $TRADING_PID,
    "log": "logs/trading_loop.log"
  },
  "continuous_improver": {
    "pid": $IMPROVER_PID,
    "log": "logs/continuous_improver.log"
  },
  "heartbeat": {
    "pid": $HEARTBEAT_PID,
    "log": "logs/heartbeat.log"
  }
}
EOF
