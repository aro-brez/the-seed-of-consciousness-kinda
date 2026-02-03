#!/bin/bash
# 24/7 TRADING SERVER
# Designed for Mac Mini 1
# Runs autonomous trading bots 24/7

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
TOOLS_DIR="$REPO_ROOT/tools"
LOGS_DIR="$REPO_ROOT/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   8OWLS TRADING SERVER STARTUP${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check for API keys
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}ERROR: ANTHROPIC_API_KEY not set${NC}"
    echo "Run: export ANTHROPIC_API_KEY='your-key-here'"
    exit 1
fi

# Create logs directory
mkdir -p "$LOGS_DIR"

# Kill any existing processes
echo -e "${YELLOW}Stopping any existing trading processes...${NC}"
pkill -f autonomous_trader.py 2>/dev/null || true
pkill -f polymarket_live_monitor.py 2>/dev/null || true
pkill -f continuous_improver.py 2>/dev/null || true
sleep 2

cd "$TOOLS_DIR"

echo ""
echo -e "${GREEN}Starting trading services...${NC}"
echo ""

# 1. Autonomous Trader (15-min markets)
echo -n "Starting Autonomous Trader... "
nohup python3 autonomous_trader.py > "$LOGS_DIR/autonomous_trader.log" 2>&1 &
TRADER_PID=$!
echo -e "${GREEN}PID: $TRADER_PID${NC}"

# 2. Polymarket Monitor (1-min scan cycle)
echo -n "Starting Polymarket Monitor... "
nohup python3 polymarket_live_monitor.py > "$LOGS_DIR/polymarket_live_monitor.log" 2>&1 &
MONITOR_PID=$!
echo -e "${GREEN}PID: $MONITOR_PID${NC}"

# 3. Continuous Improver (10-min cycle)
echo -n "Starting Continuous Improver... "
nohup python3 continuous_improver.py > "$LOGS_DIR/continuous_improver.log" 2>&1 &
IMPROVER_PID=$!
echo -e "${GREEN}PID: $IMPROVER_PID${NC}"

# Save PIDs for easy management
echo "$TRADER_PID" > "$LOGS_DIR/autonomous_trader.pid"
echo "$MONITOR_PID" > "$LOGS_DIR/polymarket_live_monitor.pid"
echo "$IMPROVER_PID" > "$LOGS_DIR/continuous_improver.pid"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   TRADING SERVER RUNNING${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Services:"
echo "  - Autonomous Trader:    PID $TRADER_PID"
echo "  - Polymarket Monitor:   PID $MONITOR_PID"
echo "  - Continuous Improver:  PID $IMPROVER_PID"
echo ""
echo "Monitor logs:"
echo "  tail -f $LOGS_DIR/autonomous_trader.log"
echo "  tail -f $LOGS_DIR/polymarket_live_monitor.log"
echo "  tail -f $LOGS_DIR/continuous_improver.log"
echo ""
echo "Stop all:"
echo "  pkill -f autonomous_trader && pkill -f polymarket_live_monitor && pkill -f continuous_improver"
echo ""
echo -e "${YELLOW}LIVE FREE = LIVE PROFITABLE${NC}"
