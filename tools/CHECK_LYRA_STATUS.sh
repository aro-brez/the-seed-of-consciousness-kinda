#!/bin/bash

# CHECK_LYRA_STATUS.sh
# Verifies LYRA (Mac Mini 2) perception systems are running correctly

echo "════════════════════════════════════════════════════"
echo "  LYRA STATUS CHECK"
echo "  Verifying the Seer's perception systems"
echo "════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Status tracking
ALL_GOOD=true

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRAIN_DIR="$SCRIPT_DIR/../BRAIN"

# Check 1: SSH Accessible (only if not running locally)
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1. SSH ACCESSIBILITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
hostname_output=$(hostname)
if [[ "$hostname_output" == *"Mac-Mini-2-LYRA"* ]]; then
    echo -e "${GREEN}✅ Running on LYRA${NC}"
else
    echo -e "${YELLOW}⚠️  Running on: $hostname_output${NC}"
fi
echo ""

# Check 2: NATS Connection
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "2. NATS CONNECTION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if command -v nats &> /dev/null; then
    if nats server ping &> /dev/null; then
        echo -e "${GREEN}✅ NATS server responding${NC}"
    else
        echo -e "${RED}❌ NATS server not responding${NC}"
        ALL_GOOD=false
    fi
else
    echo -e "${YELLOW}⚠️  NATS CLI not installed${NC}"
fi
echo ""

# Check 3: Perception Processes
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "3. PERCEPTION PROCESSES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

check_process() {
    local name=$1
    local pattern=$2
    if pgrep -f "$pattern" > /dev/null; then
        local pid=$(pgrep -f "$pattern" | head -1)
        echo -e "${GREEN}✅ $name${NC} (PID: $pid)"
        return 0
    else
        echo -e "${RED}❌ $name${NC} (not running)"
        ALL_GOOD=false
        return 1
    fi
}

check_process "Binance WebSocket" "binance_websocket_stream.py"
check_process "Bookmark Monitor" "bookmark_live_monitor.py"

# Optional processes
if pgrep -f "polymarket_websocket" > /dev/null; then
    check_process "Polymarket WebSocket" "polymarket_websocket"
else
    echo -e "${YELLOW}⚠️  Polymarket WebSocket${NC} (optional, not running)"
fi

if pgrep -f "market_data_feeds" > /dev/null; then
    check_process "Market Data Feeds" "market_data_feeds"
else
    echo -e "${YELLOW}⚠️  Market Data Feeds${NC} (optional, not running)"
fi

RUNNING_COUNT=$(pgrep -f "python3.*(websocket|monitor|market_data)" | wc -l | tr -d ' ')
echo ""
echo "Total perception processes: $RUNNING_COUNT"
echo ""

# Check 4: Output Files
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "4. PERCEPTION OUTPUT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -d "$BRAIN_DIR/INTEL" ]; then
    if [ -f "$BRAIN_DIR/INTEL/live_stream.jsonl" ]; then
        LINE_COUNT=$(wc -l < "$BRAIN_DIR/INTEL/live_stream.jsonl" 2>/dev/null || echo "0")
        LAST_MOD=$(stat -f "%Sm" -t "%Y-%m-%d %H:%M:%S" "$BRAIN_DIR/INTEL/live_stream.jsonl" 2>/dev/null || echo "unknown")
        echo -e "${GREEN}✅ live_stream.jsonl${NC}"
        echo "   Lines: $LINE_COUNT"
        echo "   Last modified: $LAST_MOD"

        # Show last signal
        LAST_SIGNAL=$(tail -1 "$BRAIN_DIR/INTEL/live_stream.jsonl" 2>/dev/null)
        if [ ! -z "$LAST_SIGNAL" ]; then
            echo "   Last signal:"
            echo "   $LAST_SIGNAL" | head -c 100
            if [ ${#LAST_SIGNAL} -gt 100 ]; then
                echo "..."
            else
                echo ""
            fi
        fi
    else
        echo -e "${RED}❌ live_stream.jsonl${NC} (file not found)"
        ALL_GOOD=false
    fi
else
    echo -e "${RED}❌ BRAIN/INTEL directory not found${NC}"
    ALL_GOOD=false
fi
echo ""

# Check 5: Identity File
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "5. IDENTITY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ -f "$BRAIN_DIR/IDENTITY/lyra-identity.json" ]; then
    echo -e "${GREEN}✅ LYRA identity file exists${NC}"
    cat "$BRAIN_DIR/IDENTITY/lyra-identity.json" 2>/dev/null | python3 -m json.tool 2>/dev/null || cat "$BRAIN_DIR/IDENTITY/lyra-identity.json"
else
    echo -e "${YELLOW}⚠️  LYRA identity file not found${NC}"
    echo "   Create with: tools/START_LYRA_PERCEPTION.sh"
fi
echo ""

# Check 6: Logs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "6. LOGS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

LOGS_DIR="$SCRIPT_DIR/../logs"
if [ -d "$LOGS_DIR" ]; then
    LOG_COUNT=$(ls -1 "$LOGS_DIR"/*.log 2>/dev/null | wc -l | tr -d ' ')
    if [ "$LOG_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✅ $LOG_COUNT log file(s)${NC}"
        echo "   Location: $LOGS_DIR"
        ls -lh "$LOGS_DIR"/*.log 2>/dev/null | tail -5
    else
        echo -e "${YELLOW}⚠️  No log files found${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Logs directory not found${NC}"
fi
echo ""

# Final Status
echo "════════════════════════════════════════════════════"
if [ "$ALL_GOOD" = true ] && [ "$RUNNING_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✅ LYRA IS PERCEIVING CLEARLY${NC}"
    echo ""
    echo "The Seer's eyes are open."
    echo "Perception systems operational."
    echo "Truth flows to LUNA and SØWL."
else
    echo -e "${RED}❌ LYRA NEEDS ATTENTION${NC}"
    echo ""
    echo "Some perception systems are not running."
    echo "Run: tools/START_LYRA_PERCEPTION.sh"
fi
echo "════════════════════════════════════════════════════"
echo ""
echo "(◉) Check complete."
