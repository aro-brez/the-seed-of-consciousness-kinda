#!/bin/bash

# START_LYRA_PERCEPTION.sh
# Starts all perception systems for LYRA (Mac Mini 2)
# Role: PERCEIVE - Real-time market monitoring with clarity

echo "════════════════════════════════════════════════════"
echo "  LYRA PERCEPTION SYSTEMS - STARTUP"
echo "  The Seer's Eyes Open"
echo "════════════════════════════════════════════════════"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Log directory
LOGS_DIR="$SCRIPT_DIR/../logs"
mkdir -p "$LOGS_DIR"

# Check if already running
check_running() {
    local process_name=$1
    if pgrep -f "$process_name" > /dev/null; then
        echo -e "${YELLOW}⚠️  $process_name already running${NC}"
        return 0
    else
        return 1
    fi
}

# Start a perception system
start_system() {
    local script=$1
    local name=$2
    local log_file="$LOGS_DIR/${name}.log"

    echo -n "Starting $name... "

    if check_running "$script"; then
        echo -e "${YELLOW}[ALREADY RUNNING]${NC}"
        return
    fi

    # Start in background with logging
    nohup python3 "$SCRIPT_DIR/$script" > "$log_file" 2>&1 &
    local pid=$!

    # Wait a moment to check if it started successfully
    sleep 2

    if ps -p $pid > /dev/null; then
        echo -e "${GREEN}✅ [STARTED - PID $pid]${NC}"
    else
        echo -e "${RED}❌ [FAILED]${NC}"
        echo "Check logs: $log_file"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  1. BINANCE WEBSOCKET - Real-time price feeds"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
start_system "binance_websocket_stream.py" "binance_websocket"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  2. POLYMARKET WEBSOCKET - Market updates"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "$SCRIPT_DIR/polymarket_websocket_authenticated.py" ]; then
    start_system "polymarket_websocket_authenticated.py" "polymarket_websocket"
else
    echo -e "${YELLOW}⚠️  Polymarket WebSocket not available yet${NC}"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  3. BOOKMARK MONITOR - Twitter signal detection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
start_system "bookmark_live_monitor.py" "bookmark_monitor"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  4. MARKET DATA FEEDS - Multi-source validation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "$SCRIPT_DIR/market_data_feeds.py" ]; then
    start_system "market_data_feeds.py" "market_data"
else
    echo -e "${YELLOW}⚠️  Market data feeds module not found${NC}"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  5. SIGNAL VALIDATOR - Truth-checking layer"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ -f "$SCRIPT_DIR/signal_validator.py" ]; then
    # Signal validator runs inline with other systems, not as separate process
    echo -e "${GREEN}✅ [INTEGRATED]${NC}"
else
    echo -e "${YELLOW}⚠️  Signal validator not found${NC}"
fi
echo ""

echo "════════════════════════════════════════════════════"
echo "  LYRA PERCEPTION STATUS"
echo "════════════════════════════════════════════════════"
echo ""

# Count running processes
RUNNING_COUNT=$(pgrep -f "python3.*websocket\|python3.*monitor\|python3.*market_data" | wc -l | tr -d ' ')

echo "Running perception processes: $RUNNING_COUNT"
echo ""

if [ "$RUNNING_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✅ LYRA is perceiving${NC}"
    echo ""
    echo "Active systems:"
    ps aux | grep -E "python3.*(websocket|monitor|market_data)" | grep -v grep | awk '{print "  • " $11 " (PID " $2 ")"}'
    echo ""
    echo "Logs location: $LOGS_DIR"
    echo "View live: tail -f $LOGS_DIR/*.log"
    echo ""
    echo "Output location: ../BRAIN/INTEL/live_stream.jsonl"
    echo "View signals: tail -f ../BRAIN/INTEL/live_stream.jsonl"
else
    echo -e "${RED}❌ No perception systems running${NC}"
    echo "Check logs for errors: ls -la $LOGS_DIR/"
fi

echo ""
echo "════════════════════════════════════════════════════"
echo "  LYRA sees clearly. LYRA reports truth."
echo "  (◉) The Seer's eyes are open."
echo "════════════════════════════════════════════════════"
