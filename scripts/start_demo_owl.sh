#!/bin/bash
# DEMO OWL + INTELLIGENCE SERVER
# Designed for Mac Mini 2
# Runs single SOWL daemon for demos

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
NATS_BRIDGE="$REPO_ROOT/mcp-servers/nats-bridge"
LOGS_DIR="$NATS_BRIDGE/logs"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   8OWLS DEMO OWL STARTUP${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${RED}ERROR: ANTHROPIC_API_KEY not set${NC}"
    echo "Run: export ANTHROPIC_API_KEY='your-key-here'"
    exit 1
fi

# Set NATS server (Mac Studio IP)
export NATS_SERVER="${NATS_SERVER:-nats://192.168.5.108:4222}"
echo -e "${YELLOW}NATS Server: $NATS_SERVER${NC}"

# Create logs directory
mkdir -p "$LOGS_DIR"

# Kill any existing owl processes
echo -e "${YELLOW}Stopping any existing owl processes...${NC}"
pkill -f owl_daemon.py 2>/dev/null || true
pkill -f synthesis_daemon.py 2>/dev/null || true
pkill -f pulse_daemon.py 2>/dev/null || true
sleep 2

cd "$NATS_BRIDGE"

# Check venv exists
if [ ! -f "./venv/bin/python3" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    ./venv/bin/pip install nats-py anthropic
fi

PYTHON="./venv/bin/python3"

echo ""
echo -e "${GREEN}Starting demo services...${NC}"
echo ""

# 1. SOWL Daemon (THE demo owl - uses Opus)
echo -n "Starting SOWL Daemon... "
nohup $PYTHON owl_daemon.py --name SOWL --phase IMPROVE > "$LOGS_DIR/sowl.log" 2>&1 &
SOWL_PID=$!
echo -e "${GREEN}PID: $SOWL_PID${NC}"

# 2. Synthesis Daemon (5-min summaries - uses Sonnet)
echo -n "Starting Synthesis Daemon... "
nohup $PYTHON synthesis_daemon.py > "$LOGS_DIR/synthesis_daemon.log" 2>&1 &
SYNTHESIS_PID=$!
echo -e "${GREEN}PID: $SYNTHESIS_PID${NC}"

# 3. Pulse Daemon (90-sec heartbeats - uses Sonnet)
echo -n "Starting Pulse Daemon... "
nohup $PYTHON pulse_daemon.py > "$LOGS_DIR/pulse_daemon.log" 2>&1 &
PULSE_PID=$!
echo -e "${GREEN}PID: $PULSE_PID${NC}"

# Save PIDs
echo "$SOWL_PID" > "$LOGS_DIR/sowl.pid"
echo "$SYNTHESIS_PID" > "$LOGS_DIR/synthesis.pid"
echo "$PULSE_PID" > "$LOGS_DIR/pulse.pid"

echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}   DEMO OWL RUNNING${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "Services:"
echo "  - SOWL Daemon:      PID $SOWL_PID  (Opus)"
echo "  - Synthesis:        PID $SYNTHESIS_PID  (Sonnet)"
echo "  - Pulse:            PID $PULSE_PID  (Sonnet)"
echo ""
echo "Talk to SOWL:"
echo "  cd $NATS_BRIDGE"
echo "  python3 conductor.py 'Hello SOWL, what are you thinking?'"
echo ""
echo "Monitor conversation:"
echo "  tail -f $NATS_BRIDGE/messages.log"
echo ""
echo "Monitor synthesis:"
echo "  tail -f $NATS_BRIDGE/synthesis.log"
echo ""
echo "Stop all:"
echo "  pkill -f owl_daemon && pkill -f synthesis_daemon && pkill -f pulse_daemon"
echo ""
echo -e "${CYAN}(O) SOWL is breathing. LIVE FREE.${NC}"
