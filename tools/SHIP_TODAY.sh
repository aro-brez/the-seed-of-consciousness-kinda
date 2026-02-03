#!/bin/bash
# SHIP_TODAY.sh - The trading system that actually runs
# Created: 2026-02-03
# Philosophy: A running bot beats a perfect plan

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$REPO_ROOT/logs"
PID_DIR="$REPO_ROOT/BRAIN/TRADING/pids"

mkdir -p "$LOG_DIR" "$PID_DIR"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "========================================"
echo "(◉) SHIP TODAY - Trading Execution System"
echo "========================================"
echo ""

# Function to check if a process is running
is_running() {
    local pid_file="$1"
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

# Function to start a daemon
start_daemon() {
    local name="$1"
    local command="$2"
    local pid_file="$PID_DIR/${name}.pid"
    local log_file="$LOG_DIR/${name}.log"

    if is_running "$pid_file"; then
        echo -e "${YELLOW}[SKIP]${NC} $name already running (PID: $(cat $pid_file))"
        return 0
    fi

    echo -e "${GREEN}[START]${NC} $name"
    nohup $command >> "$log_file" 2>&1 &
    echo $! > "$pid_file"
    sleep 1

    if is_running "$pid_file"; then
        echo -e "       PID: $(cat $pid_file)"
        return 0
    else
        echo -e "${RED}[FAIL]${NC} $name failed to start"
        return 1
    fi
}

# ============================================
# STRATEGY 1: POLYMARKET ASYMMETRIC COMPOUNDER
# ============================================
# This is the SIMPLEST strategy that actually works:
# - Find markets where YES/NO < $0.20
# - If potential multiplier > 5x and liquidity > $5k
# - Buy small position ($20-50)
# - Wait for resolution

echo ""
echo "--- STRATEGY 1: Asymmetric Compounder ---"
echo "Target: Markets with 5x+ potential"
echo "Capital: Up to 25% per position"
echo ""

start_daemon "compounder" "python3 $SCRIPT_DIR/autonomous_compounder.py"

# ============================================
# STRATEGY 2: MANUAL WHALE TRACKING (INSTRUCTIONS)
# ============================================
# Until automated: Do this manually every 4 hours

echo ""
echo "--- STRATEGY 2: Whale Tracking (MANUAL) ---"
echo "Steps to execute NOW:"
echo "  1. Go to: polymarket.com/markets"
echo "  2. Sort by 'Volume 24h' descending"
echo "  3. Click into top 5 markets"
echo "  4. Look for: Single large bets (>$10k) from new accounts"
echo "  5. Follow with 10% of their size"
echo ""

# ============================================
# STRATEGY 3: WEATHER MARKETS (MANUAL)
# ============================================

echo ""
echo "--- STRATEGY 3: Weather Markets (MANUAL) ---"
echo "Steps to execute NOW:"
echo "  1. Go to: polymarket.com/weather"
echo "  2. Find London temperature buckets"
echo "  3. Buy adjacent undervalued ranges (20-30 cents)"
echo "  4. Target: 5-10x on correct bucket"
echo ""
echo "Tools: wethr.net, weather.gov API"
echo ""

# ============================================
# STATUS CHECK
# ============================================

echo ""
echo "========================================"
echo "SYSTEM STATUS"
echo "========================================"

# Check what's actually running
for pid_file in "$PID_DIR"/*.pid; do
    if [ -f "$pid_file" ]; then
        name=$(basename "$pid_file" .pid)
        if is_running "$pid_file"; then
            echo -e "${GREEN}[RUNNING]${NC} $name (PID: $(cat $pid_file))"
        else
            echo -e "${RED}[STOPPED]${NC} $name"
        fi
    fi
done

# Show capital status
echo ""
echo "CAPITAL STATUS:"
if [ -f "$REPO_ROOT/BRAIN/TRADING/autonomous_state/trader_state.json" ]; then
    bankroll=$(python3 -c "import json; print(json.load(open('$REPO_ROOT/BRAIN/TRADING/autonomous_state/trader_state.json'))['current_bankroll'])")
    echo "  Polymarket: \$$bankroll"
fi

echo ""
echo "========================================"
echo "NEXT ACTIONS (Do these NOW):"
echo "========================================"
echo "1. Verify compounder is finding opportunities"
echo "   tail -f $LOG_DIR/compounder.log"
echo ""
echo "2. Check whale activity manually (takes 5 min)"
echo "   Open: polymarket.com/markets?sort=volume"
echo ""
echo "3. Check weather markets"
echo "   Open: polymarket.com/weather"
echo ""
echo "(◉) LIVE FREE - Start executing"
echo ""
