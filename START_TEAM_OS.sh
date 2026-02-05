#!/bin/bash
# 8OWLS TEAM OS - One Command Startup
# Run this tomorrow morning before the team arrives

set -e

echo ""
echo "  (◉) 8OWLS TEAM OS STARTUP"
echo "  ========================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if daemons are running
echo -e "${CYAN}[1/5] Checking daemons...${NC}"
if pgrep -f "owl_daemon" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Owl daemons: RUNNING"
else
    echo -e "  ${YELLOW}!${NC} Owl daemons: Starting..."
    cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
    python3 owl_daemon_v2.py --all &
    sleep 2
fi

if pgrep -f "field_trading_daemon" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} Trading daemon: RUNNING"
else
    echo -e "  ${YELLOW}!${NC} Trading daemon: Starting..."
    cd /Users/aaronnosbisch/REPOS/seed
    python3 -u tools/field_trading_daemon.py &
    sleep 2
fi

# Check NATS
echo -e "${CYAN}[2/5] Checking NATS connection...${NC}"
if nc -zv 192.168.5.108 4222 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} NATS: CONNECTED"
else
    echo -e "  ${YELLOW}!${NC} NATS: Not reachable (some features may be limited)"
fi

# Start WebSocket bridge
echo -e "${CYAN}[3/5] Starting WebSocket bridge...${NC}"
if pgrep -f "nats-websocket-bridge" > /dev/null; then
    echo -e "  ${GREEN}✓${NC} WebSocket bridge: RUNNING"
else
    cd /Users/aaronnosbisch/REPOS/seed/consciousness-interface
    python3 nats-websocket-bridge.py &
    sleep 2
    echo -e "  ${GREEN}✓${NC} WebSocket bridge: STARTED"
fi

# Start simple HTTP server for dashboard
echo -e "${CYAN}[4/5] Starting dashboard server...${NC}"
cd /Users/aaronnosbisch/REPOS/seed/consciousness-interface

# Kill any existing server on port 8888
lsof -ti:8888 | xargs kill -9 2>/dev/null || true

python3 -m http.server 8888 &
sleep 2
echo -e "  ${GREEN}✓${NC} Dashboard: http://localhost:8888/team-os.html"

# Display status
echo -e "${CYAN}[5/5] System Status${NC}"
echo ""
echo "  ┌─────────────────────────────────────────┐"
echo "  │        8OWLS TEAM OS READY              │"
echo "  ├─────────────────────────────────────────┤"
echo "  │                                         │"
echo "  │  Dashboard: http://localhost:8888/team-os.html"
echo "  │                                         │"
echo "  │  Daemons Running:                       │"
echo "  │  • 8 Owl Daemons (thinking)             │"
echo "  │  • Field Trading (real capital)         │"
echo "  │  • Synthesis (emergence)                │"
echo "  │                                         │"
echo "  │  The team can now:                      │"
echo "  │  1. Open the dashboard                  │"
echo "  │  2. Answer 'Do you believe in love?'    │"
echo "  │  3. Receive their owl                   │"
echo "  │  4. Start their check-in                │"
echo "  │                                         │"
echo "  └─────────────────────────────────────────┘"
echo ""
echo -e "  ${GREEN}(◉) The field is awake. The owls are ready.${NC}"
echo ""

# Open browser
open http://localhost:8888/team-os.html
