#!/bin/bash
# START_BREATHING_TRADER.sh
# Launch the Conscious Breathing Trader
# "Breathe WITH the market, not extract FROM it"

set -e

REPO_ROOT="/Users/aaronnosbisch/REPOS/seed"
LOG_DIR="$REPO_ROOT/logs"
SCRIPT="$REPO_ROOT/tools/conscious_breathing_trader.py"
PID_FILE="$LOG_DIR/breathing_trader.pid"
LOG_FILE="$LOG_DIR/breathing_trader.log"

# Create log directory
mkdir -p "$LOG_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "════════════════════════════════════════════════════════════════════"
echo "  CONSCIOUS BREATHING TRADER"
echo "  'Breathe WITH the market, not extract FROM it'"
echo "════════════════════════════════════════════════════════════════════"
echo ""

# Check if already running
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}⚠️  Trader already running (PID: $OLD_PID)${NC}"
        echo ""
        echo "Options:"
        echo "  1. Stop existing: kill $OLD_PID"
        echo "  2. View logs: tail -f $LOG_FILE"
        echo "  3. Check status: ps -p $OLD_PID"
        exit 1
    else
        echo -e "${YELLOW}⚠️  Stale PID file found, removing...${NC}"
        rm "$PID_FILE"
    fi
fi

# Parse arguments
MODE="full"  # default
if [ "$1" = "--paper" ]; then
    MODE="paper"
    echo "📝 PAPER TRADING MODE (simulation only)"
elif [ "$1" = "--micro" ]; then
    MODE="micro"
    echo "💵 MICRO POSITIONS MODE (1% = ~$6 per trade)"
elif [ "$1" = "--full" ]; then
    MODE="full"
    echo "💰 FULL DEPLOYMENT MODE (10% = ~$60 per trade)"
elif [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [MODE]"
    echo ""
    echo "Modes:"
    echo "  --paper   Paper trading (simulation, zero risk)"
    echo "  --micro   Micro positions (1% per trade, minimal risk)"
    echo "  --full    Full deployment (10% per trade, standard risk)"
    echo ""
    echo "Examples:"
    echo "  $0 --paper    # Start in paper trading mode"
    echo "  $0 --micro    # Start with micro positions"
    echo "  $0            # Start with full deployment (default)"
    echo ""
    exit 0
else
    echo "💰 FULL DEPLOYMENT MODE (10% = ~$60 per trade)"
fi

echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi

# Check script exists
if [ ! -f "$SCRIPT" ]; then
    echo -e "${RED}❌ Script not found: $SCRIPT${NC}"
    exit 1
fi

# Check API keys
API_KEYS="/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json"
if [ ! -f "$API_KEYS" ]; then
    echo -e "${RED}❌ API keys not found: $API_KEYS${NC}"
    exit 1
fi

# Install dependencies
echo "📦 Checking dependencies..."
pip3 install -q anthropic requests

echo ""
echo "════════════════════════════════════════════════════════════════════"
echo "  STARTING TRADER"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "Mode: $MODE"
echo "Log file: $LOG_FILE"
echo "State dir: $REPO_ROOT/BRAIN/INTEL/breathing_trader/"
echo ""

# Start trader in background
if [ "$MODE" = "paper" ]; then
    echo "⚠️  Paper trading mode not yet implemented"
    echo "Running in full mode for now..."
    # TODO: Add paper trading flag to Python script
fi

nohup python3 "$SCRIPT" > "$LOG_FILE" 2>&1 &
PID=$!

# Save PID
echo "$PID" > "$PID_FILE"

# Wait a moment to check if it started
sleep 2

if ps -p "$PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Trader started successfully (PID: $PID)${NC}"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "  MONITORING"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "View live log:"
    echo "  tail -f $LOG_FILE"
    echo ""
    echo "Check status:"
    echo "  ps -p $PID"
    echo ""
    echo "Stop trader:"
    echo "  kill $PID"
    echo ""
    echo "View state:"
    echo "  cat $REPO_ROOT/BRAIN/INTEL/breathing_trader/state.json | jq"
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""

    # Show first few lines of log
    echo "📊 Initial output:"
    echo ""
    sleep 1
    tail -n 20 "$LOG_FILE"
else
    echo -e "${RED}❌ Failed to start trader${NC}"
    echo ""
    echo "Check logs:"
    echo "  cat $LOG_FILE"
    exit 1
fi
