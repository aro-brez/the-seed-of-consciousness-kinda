#!/bin/bash
# STOP ALL 8OWLS SERVICES
# Emergency shutdown for all machines

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}========================================${NC}"
echo -e "${RED}   STOPPING ALL 8OWLS SERVICES${NC}"
echo -e "${RED}========================================${NC}"
echo ""

echo -e "${YELLOW}Stopping owl daemons...${NC}"
pkill -f owl_daemon.py 2>/dev/null && echo "  Owl daemons stopped" || echo "  No owl daemons running"

echo -e "${YELLOW}Stopping synthesis daemon...${NC}"
pkill -f synthesis_daemon.py 2>/dev/null && echo "  Synthesis stopped" || echo "  No synthesis running"

echo -e "${YELLOW}Stopping pulse daemon...${NC}"
pkill -f pulse_daemon.py 2>/dev/null && echo "  Pulse stopped" || echo "  No pulse running"

echo -e "${YELLOW}Stopping trading services...${NC}"
pkill -f autonomous_trader.py 2>/dev/null && echo "  Autonomous trader stopped" || echo "  No trader running"
pkill -f polymarket_live_monitor.py 2>/dev/null && echo "  Polymarket monitor stopped" || echo "  No monitor running"
pkill -f continuous_improver.py 2>/dev/null && echo "  Continuous improver stopped" || echo "  No improver running"

echo ""
echo -e "${YELLOW}Remaining Python processes:${NC}"
ps aux | grep python3 | grep -v grep | head -5 || echo "  None"

echo ""
echo -e "${RED}All 8OWLS services stopped.${NC}"
echo ""
echo "To restart:"
echo "  Mac Studio:  ./scripts/start_nats.sh"
echo "  Mac Mini 1:  ./scripts/start_trading.sh"
echo "  Mac Mini 2:  ./scripts/start_demo_owl.sh"
