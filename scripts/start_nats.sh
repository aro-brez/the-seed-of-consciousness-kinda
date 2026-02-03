#!/bin/bash
# NATS SERVER STARTUP
# Designed for Mac Studio (Central Hub)
# Must run before other machines can communicate

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   NATS MESSAGE BROKER STARTUP${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if NATS is installed
if ! command -v nats-server &> /dev/null; then
    echo -e "${YELLOW}NATS not found. Installing via Homebrew...${NC}"
    brew install nats-server
fi

# Kill any existing NATS
echo -e "${YELLOW}Stopping any existing NATS server...${NC}"
pkill -f nats-server 2>/dev/null || true
sleep 1

# Get local IP
LOCAL_IP=$(ipconfig getifaddr en0 2>/dev/null || echo "localhost")
echo -e "${CYAN}Local IP: $LOCAL_IP${NC}"

# Start NATS
echo ""
echo -e "${GREEN}Starting NATS server on port 4222...${NC}"
nats-server -p 4222 -a 0.0.0.0 &
NATS_PID=$!

sleep 2

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   NATS SERVER RUNNING${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "NATS URL: nats://$LOCAL_IP:4222"
echo "PID: $NATS_PID"
echo ""
echo "Set on other machines:"
echo "  export NATS_SERVER='nats://$LOCAL_IP:4222'"
echo ""
echo "Test connection:"
echo "  nats pub test 'hello' -s nats://$LOCAL_IP:4222"
echo ""
echo "Stop:"
echo "  pkill -f nats-server"
echo ""
echo -e "${GREEN}Central hub ready. Start other services.${NC}"
