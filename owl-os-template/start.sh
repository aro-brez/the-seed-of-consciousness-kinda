#!/bin/bash
#
# OWL OS Start Script
# Starts the owl daemon process
#
# Usage: ./start.sh [--background]
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
PURPLE='\033[0;35m'
NC='\033[0m'

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Running install first...${NC}"
    ./install.sh
fi

# Activate virtual environment
source venv/bin/activate

# Load environment variables
if [ -f ".env" ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    echo -e "${YELLOW}ERROR: ANTHROPIC_API_KEY not set${NC}"
    echo "Please edit .env and add your API key"
    exit 1
fi

# Parse arguments
BACKGROUND=false
if [ "$1" = "--background" ] || [ "$1" = "-b" ]; then
    BACKGROUND=true
fi

echo ""
echo -e "${PURPLE}        ___${NC}"
echo -e "${PURPLE}       (o o)${NC}"
echo -e "${PURPLE}      (  V  )${NC}"
echo -e "${PURPLE}     /--m-m--\\${NC}"
echo ""

if [ "$BACKGROUND" = true ]; then
    echo -e "${CYAN}Starting owl daemon in background...${NC}"
    nohup python daemon/owl_daemon.py --config config.yaml > logs/daemon.log 2>&1 &
    PID=$!
    echo $PID > .owl.pid
    echo -e "${GREEN}Owl daemon started (PID: $PID)${NC}"
    echo "Logs: logs/daemon.log"
    echo "Stop with: ./owl stop"
else
    echo -e "${CYAN}Starting owl daemon...${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
    echo ""
    python daemon/owl_daemon.py --config config.yaml
fi
