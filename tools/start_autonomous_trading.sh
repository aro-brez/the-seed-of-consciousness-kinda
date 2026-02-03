#!/bin/bash
#
# AUTONOMOUS TRADING DAEMON LAUNCHER
# ==================================
# Start and manage the autonomous trading system
#
# Usage:
#   ./start_autonomous_trading.sh              # Start with default $1000
#   ./start_autonomous_trading.sh --capital 5000   # Start with $5000
#   ./start_autonomous_trading.sh --simulate   # Simulation mode (no real trades)
#   ./start_autonomous_trading.sh --stop       # Stop the daemon
#   ./start_autonomous_trading.sh --status     # Check daemon status
#   ./start_autonomous_trading.sh --logs       # Tail logs
#
# The daemon runs 24/7, trades autonomously, and logs everything.
# Fund your wallet, start the daemon, never touch it again.
#

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$REPO_ROOT/logs"
STATE_DIR="$REPO_ROOT/BRAIN/TRADING/autonomous_state"
PID_FILE="$STATE_DIR/daemon.pid"
LOG_FILE="$LOG_DIR/autonomous_trader.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create directories
mkdir -p "$LOG_DIR"
mkdir -p "$STATE_DIR"

# Functions
print_banner() {
    echo ""
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${BLUE}           AUTONOMOUS TRADING DAEMON                            ${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${YELLOW}  Zero human intervention required                              ${NC}"
    echo -e "${YELLOW}  Fund wallet -> Start daemon -> Collect profits               ${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0  # Running
    fi
    return 1  # Not running
}

start_daemon() {
    local capital="${1:-1000}"
    local simulate="${2:-}"

    if is_running; then
        echo -e "${YELLOW}Daemon is already running (PID: $(get_pid))${NC}"
        echo "Use --stop to stop it first, or --status to check status"
        return 1
    fi

    echo -e "${GREEN}Starting autonomous trading daemon...${NC}"
    echo "  Capital: \$${capital}"
    echo "  Mode: ${simulate:-live}"
    echo "  Log: $LOG_FILE"
    echo ""

    # Build command
    local cmd="python3 $SCRIPT_DIR/autonomous_trader.py --capital $capital"
    if [ -n "$simulate" ]; then
        cmd="$cmd --simulate"
    fi

    # Start in background
    nohup $cmd >> "$LOG_FILE" 2>&1 &
    local pid=$!

    # Save PID
    echo $pid > "$PID_FILE"

    # Wait a moment and check if started
    sleep 2

    if is_running; then
        echo -e "${GREEN}Daemon started successfully!${NC}"
        echo "  PID: $pid"
        echo ""
        echo "Commands:"
        echo "  ./start_autonomous_trading.sh --status  # Check status"
        echo "  ./start_autonomous_trading.sh --logs    # View logs"
        echo "  ./start_autonomous_trading.sh --stop    # Stop daemon"
    else
        echo -e "${RED}Failed to start daemon. Check logs:${NC}"
        tail -20 "$LOG_FILE"
        return 1
    fi
}

stop_daemon() {
    if ! is_running; then
        echo -e "${YELLOW}Daemon is not running${NC}"
        rm -f "$PID_FILE"
        return 0
    fi

    local pid=$(get_pid)
    echo -e "${YELLOW}Stopping daemon (PID: $pid)...${NC}"

    # Send SIGTERM for graceful shutdown
    kill -TERM "$pid" 2>/dev/null

    # Wait for shutdown
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
        echo -n "."
    done
    echo ""

    if is_running; then
        echo -e "${RED}Graceful shutdown failed, forcing...${NC}"
        kill -9 "$pid" 2>/dev/null
        sleep 1
    fi

    rm -f "$PID_FILE"
    echo -e "${GREEN}Daemon stopped${NC}"
}

show_status() {
    print_banner

    if is_running; then
        echo -e "Status: ${GREEN}RUNNING${NC} (PID: $(get_pid))"
    else
        echo -e "Status: ${RED}STOPPED${NC}"
    fi
    echo ""

    # Show state if available
    local state_file="$STATE_DIR/trader_state.json"
    if [ -f "$state_file" ]; then
        echo "Current State:"
        echo "=============="
        python3 -c "
import json
with open('$state_file') as f:
    state = json.load(f)
    print(f\"  Bankroll:      \${state.get('current_bankroll', 0):,.2f}\")
    print(f\"  Peak:          \${state.get('peak_bankroll', 0):,.2f}\")
    print(f\"  PnL Today:     \${state.get('pnl_today', 0):+,.2f}\")
    print(f\"  Trades Today:  {state.get('trades_today', 0)}\")
    print(f\"  Total Trades:  {state.get('total_trades', 0)}\")
    print(f\"  Active Pos:    {len(state.get('active_positions', []))}\")
    print(f\"  Last Update:   {state.get('last_updated', 'N/A')}\")
"
        echo ""
    fi

    # Show learning state
    local learning_file="$STATE_DIR/learning_state.json"
    if [ -f "$learning_file" ]; then
        echo "Learning State:"
        echo "==============="
        python3 -c "
import json
with open('$learning_file') as f:
    state = json.load(f)
    print(f\"  Momentum Threshold:   {state.get('momentum_threshold', 0.3):.3f}\")
    print(f\"  Position Multiplier:  {state.get('position_multiplier', 1.0):.2f}\")
    print(f\"  Win Rate:             {state.get('win_rate', 0):.1%}\")
    print(f\"  Avg Return:           {state.get('avg_return', 0):.1f}%\")
"
        echo ""
    fi

    # Show recent log entries
    if [ -f "$LOG_FILE" ]; then
        echo "Recent Activity (last 10 lines):"
        echo "================================="
        tail -10 "$LOG_FILE"
    fi
}

show_logs() {
    if [ ! -f "$LOG_FILE" ]; then
        echo "No log file found at $LOG_FILE"
        return 1
    fi

    echo -e "${BLUE}Tailing logs (Ctrl+C to stop)...${NC}"
    echo ""
    tail -f "$LOG_FILE"
}

show_performance() {
    local perf_file="$STATE_DIR/performance.jsonl"

    if [ ! -f "$perf_file" ]; then
        echo "No performance data found"
        return 1
    fi

    echo "Performance History:"
    echo "===================="
    echo ""

    python3 << 'EOF'
import json
from pathlib import Path

perf_file = Path("$STATE_DIR/performance.jsonl".replace("$STATE_DIR", "$STATE_DIR"))
perf_file = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/autonomous_state/performance.jsonl")

if perf_file.exists():
    entries = []
    with open(perf_file) as f:
        for line in f:
            try:
                entries.append(json.loads(line))
            except:
                pass

    if entries:
        # Show last 20 entries
        for entry in entries[-20:]:
            ts = entry.get('timestamp', '')[:19]
            br = entry.get('bankroll', 0)
            pnl = entry.get('pnl_today', 0)
            wr = entry.get('win_rate', 0)
            print(f"  {ts} | Bankroll: ${br:,.2f} | PnL: ${pnl:+,.2f} | Win Rate: {wr:.1%}")
    else:
        print("  No entries found")
else:
    print("  Performance file not found")
EOF
}

# Parse arguments
case "${1:-}" in
    --stop)
        stop_daemon
        ;;
    --status)
        show_status
        ;;
    --logs)
        show_logs
        ;;
    --performance)
        show_performance
        ;;
    --help|-h)
        print_banner
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --capital <amount>  Starting capital (default: \$1000)"
        echo "  --simulate          Run in simulation mode (no real trades)"
        echo "  --full-sim <cycles> Run full simulation with N synthetic trades"
        echo "  --stop              Stop the daemon"
        echo "  --status            Show daemon status"
        echo "  --logs              Tail the log file"
        echo "  --performance       Show performance history"
        echo "  --help              Show this help"
        echo ""
        echo "Examples:"
        echo "  $0                      # Start with \$1000"
        echo "  $0 --capital 5000       # Start with \$5000"
        echo "  $0 --simulate           # Simulation mode (uses real markets)"
        echo "  $0 --full-sim 100       # Test with 100 synthetic trades"
        echo ""
        ;;
    --full-sim)
        # Full simulation mode
        print_banner
        cycles="${2:-100}"
        capital="${4:-1000}"
        echo -e "${GREEN}Running full simulation with $cycles cycles...${NC}"
        python3 "$SCRIPT_DIR/autonomous_trader.py" --full-sim "$cycles" --capital "$capital"
        ;;
    *)
        # Start daemon
        print_banner

        capital="1000"
        simulate=""

        # Parse remaining args
        while [[ $# -gt 0 ]]; do
            case "$1" in
                --capital)
                    capital="$2"
                    shift 2
                    ;;
                --simulate)
                    simulate="simulate"
                    shift
                    ;;
                *)
                    shift
                    ;;
            esac
        done

        start_daemon "$capital" "$simulate"
        ;;
esac
