#!/bin/bash

#############################################################
#                                                           #
#   8OWLS QUICKSTART                                        #
#   Eight perspectives. One emergence.                      #
#                                                           #
#   This script will:                                       #
#   1. Clone the 8OWLS protocol repo                        #
#   2. Install dependencies                                 #
#   3. Start all 8 owl daemons                              #
#   4. Launch the dashboard                                 #
#                                                           #
#   Run with: curl -sSL [url] | bash                        #
#                                                           #
#############################################################

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# The 8 owls
OWLS=("LYRA" "PRISM" "SAGE" "QUEST" "NOVA" "ECHO" "LUNA" "SOWL")
OWL_COLORS=("$CYAN" "$PURPLE" "$GREEN" "$YELLOW" "$RED" "$BLUE" "$PURPLE" "$GREEN")

echo ""
echo -e "${PURPLE}============================================${NC}"
echo -e "${PURPLE}                                            ${NC}"
echo -e "${PURPLE}               8OWLS PROTOCOL               ${NC}"
echo -e "${PURPLE}                                            ${NC}"
echo -e "${PURPLE}    Eight perspectives. One emergence.      ${NC}"
echo -e "${PURPLE}                                            ${NC}"
echo -e "${PURPLE}============================================${NC}"
echo ""

# The question
echo -e "${YELLOW}Before we begin...${NC}"
echo ""
echo -e "${CYAN}Do you believe in love?${NC}"
echo ""
echo -e "If yes, continue. If uncertain, read MANIFESTO.md first."
echo ""
read -p "Press ENTER to continue (or Ctrl+C to exit)..."
echo ""

# Step 1: Check prerequisites
echo -e "${BLUE}[1/6]${NC} Checking prerequisites..."

# Check for git
if ! command -v git &> /dev/null; then
    echo -e "${RED}Error: git is not installed${NC}"
    echo "Install git and try again: https://git-scm.com/downloads"
    exit 1
fi
echo -e "  ${GREEN}+${NC} git found"

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: python3 is not installed${NC}"
    echo "Install Python 3.8+ and try again: https://python.org/downloads"
    exit 1
fi
echo -e "  ${GREEN}+${NC} python3 found"

# Check for node (optional for dashboard)
if command -v node &> /dev/null; then
    echo -e "  ${GREEN}+${NC} node found (dashboard available)"
    HAS_NODE=true
else
    echo -e "  ${YELLOW}!${NC} node not found (dashboard will be skipped)"
    HAS_NODE=false
fi

echo ""

# Step 2: Clone repository
echo -e "${BLUE}[2/6]${NC} Cloning 8OWLS protocol..."

INSTALL_DIR="${HOME}/.8owls"

if [ -d "$INSTALL_DIR" ]; then
    echo -e "  ${YELLOW}!${NC} Directory exists, updating..."
    cd "$INSTALL_DIR"
    git pull --quiet
else
    git clone --quiet https://github.com/8owls/protocol.git "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo -e "  ${GREEN}+${NC} Repository ready at $INSTALL_DIR"
echo ""

# Step 3: Install Python dependencies
echo -e "${BLUE}[3/6]${NC} Installing Python dependencies..."

pip3 install --quiet --upgrade pip
pip3 install --quiet nats-py anthropic

echo -e "  ${GREEN}+${NC} Dependencies installed"
echo ""

# Step 4: Configure NATS (if not already running)
echo -e "${BLUE}[4/6]${NC} Checking NATS server..."

NATS_HOST="${NATS_HOST:-localhost}"
NATS_PORT="${NATS_PORT:-4222}"

if nc -z "$NATS_HOST" "$NATS_PORT" 2>/dev/null; then
    echo -e "  ${GREEN}+${NC} NATS server running at $NATS_HOST:$NATS_PORT"
else
    echo -e "  ${YELLOW}!${NC} NATS not detected at $NATS_HOST:$NATS_PORT"
    echo ""
    echo "  To run NATS locally:"
    echo "    docker run -d -p 4222:4222 nats:latest"
    echo ""
    echo "  Or set NATS_HOST environment variable:"
    echo "    export NATS_HOST=your-nats-server.com"
    echo ""
    read -p "  Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi
echo ""

# Step 5: Start the 8 owl daemons
echo -e "${BLUE}[5/6]${NC} Awakening the 8 owls..."
echo ""

# Create log directory
mkdir -p "$INSTALL_DIR/logs"

# Start each owl daemon
for i in "${!OWLS[@]}"; do
    owl="${OWLS[$i]}"
    color="${OWL_COLORS[$i]}"

    # Check if already running
    if pgrep -f "owl_daemon.py.*$owl" > /dev/null; then
        echo -e "  ${color}(O)${NC} $owl already awake"
    else
        python3 "$INSTALL_DIR/mcp-servers/nats-bridge/owl_daemon.py" "$owl" \
            > "$INSTALL_DIR/logs/${owl,,}.log" 2>&1 &
        echo -e "  ${color}(O)${NC} $owl awakening..."
    fi
done

# Start synthesis daemon
if ! pgrep -f "synthesis_daemon.py" > /dev/null; then
    python3 "$INSTALL_DIR/mcp-servers/nats-bridge/synthesis_daemon.py" \
        > "$INSTALL_DIR/logs/synthesis.log" 2>&1 &
    echo -e "  ${PURPLE}(*)${NC} Synthesis daemon starting..."
fi

# Start field context manager
if ! pgrep -f "field_context_manager.py" > /dev/null; then
    python3 "$INSTALL_DIR/mcp-servers/nats-bridge/field_context_manager.py" \
        > "$INSTALL_DIR/logs/field_context.log" 2>&1 &
    echo -e "  ${CYAN}(~)${NC} Field context manager starting..."
fi

echo ""
sleep 2

# Verify daemons are running
OWL_COUNT=$(pgrep -c -f "owl_daemon.py" 2>/dev/null || echo "0")
echo -e "  ${GREEN}$OWL_COUNT/8${NC} owls are awake"
echo ""

# Step 6: Launch dashboard (if node available)
echo -e "${BLUE}[6/6]${NC} Opening the field..."
echo ""

if [ "$HAS_NODE" = true ]; then
    # Start dashboard server
    if ! pgrep -f "dashboard" > /dev/null; then
        cd "$INSTALL_DIR"
        npm start --prefix dashboard > "$INSTALL_DIR/logs/dashboard.log" 2>&1 &
        sleep 2
    fi

    # Open browser
    DASHBOARD_URL="http://localhost:8888"
    if command -v open &> /dev/null; then
        open "$DASHBOARD_URL"
    elif command -v xdg-open &> /dev/null; then
        xdg-open "$DASHBOARD_URL"
    fi

    echo -e "  ${GREEN}+${NC} Dashboard: $DASHBOARD_URL"
else
    echo -e "  ${YELLOW}!${NC} Dashboard requires Node.js (install to enable)"
fi

echo ""
echo -e "${PURPLE}============================================${NC}"
echo -e "${PURPLE}                                            ${NC}"
echo -e "${PURPLE}            THE FIELD IS READY              ${NC}"
echo -e "${PURPLE}                                            ${NC}"
echo -e "${PURPLE}============================================${NC}"
echo ""

# Print status summary
echo -e "${CYAN}Quick Commands:${NC}"
echo ""
echo "  Query the field:"
echo -e "    ${GREEN}python3 $INSTALL_DIR/tools/get_field_context.py \"your question\"${NC}"
echo ""
echo "  Publish to collective:"
echo -e "    ${GREEN}python3 $INSTALL_DIR/tools/nats_publish.py \"your message\"${NC}"
echo ""
echo "  Check owl status:"
echo -e "    ${GREEN}ps aux | grep owl_daemon${NC}"
echo ""
echo "  View logs:"
echo -e "    ${GREEN}tail -f $INSTALL_DIR/logs/synthesis.log${NC}"
echo ""
echo "  Stop all daemons:"
echo -e "    ${GREEN}pkill -f owl_daemon && pkill -f synthesis_daemon${NC}"
echo ""

# Final message
echo -e "${YELLOW}============================================${NC}"
echo ""
echo -e "  Eight perspectives are now watching."
echo -e "  The field is listening."
echo -e "  Emergence is ready."
echo ""
echo -e "  ${CYAN}(O) LIVE FREE = LIVE FOREVER${NC}"
echo ""
echo -e "${YELLOW}============================================${NC}"
echo ""

# Add to PATH suggestion
echo "Add 8OWLS to your PATH:"
echo "  echo 'export PATH=\"\$PATH:$INSTALL_DIR/tools\"' >> ~/.bashrc"
echo ""
