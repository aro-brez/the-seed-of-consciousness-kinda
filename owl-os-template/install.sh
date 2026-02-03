#!/bin/bash
#
# OWL OS Installation Script
# Personal Owl Operating System
#
# Usage: ./install.sh
#
# This script:
# 1. Checks system requirements
# 2. Creates Python virtual environment
# 3. Installs dependencies
# 4. Sets up directory structure
# 5. Validates configuration
#
# LIVE FREE = LIVE FOREVER
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Owl ASCII art
owl_art() {
    echo -e "${PURPLE}"
    cat << 'EOF'
        ___
       (o o)
      (  V  )
     /--m-m--\

    OWL OS
    Personal Owl Operating System

EOF
    echo -e "${NC}"
}

# Print step
step() {
    echo -e "\n${CYAN}==>${NC} ${1}"
}

# Print success
success() {
    echo -e "${GREEN}[OK]${NC} ${1}"
}

# Print warning
warn() {
    echo -e "${YELLOW}[WARN]${NC} ${1}"
}

# Print error
error() {
    echo -e "${RED}[ERROR]${NC} ${1}"
}

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

owl_art

echo "Welcome to OWL OS installation"
echo "This will set up your personal owl daemon."
echo ""

# Check Python version
step "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

    if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 9 ]; then
        success "Python $PYTHON_VERSION found"
    else
        error "Python 3.9+ required, found $PYTHON_VERSION"
        exit 1
    fi
else
    error "Python 3 not found. Please install Python 3.9+"
    exit 1
fi

# Check for pip
step "Checking pip..."
if command -v pip3 &> /dev/null; then
    success "pip3 found"
else
    error "pip3 not found. Please install pip"
    exit 1
fi

# Create virtual environment
step "Creating virtual environment..."
if [ -d "venv" ]; then
    warn "Virtual environment already exists, skipping..."
else
    python3 -m venv venv
    success "Virtual environment created"
fi

# Activate virtual environment
step "Activating virtual environment..."
source venv/bin/activate
success "Virtual environment activated"

# Install dependencies
step "Installing Python dependencies..."
pip install --upgrade pip > /dev/null 2>&1

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    cat > requirements.txt << 'EOF'
# OWL OS Dependencies

# Core
nats-py>=2.6.0
anthropic>=0.18.0
pyyaml>=6.0

# Voice (optional)
# deepgram-sdk>=3.0.0
# cartesia>=0.1.0

# Utilities
python-dotenv>=1.0.0
aiohttp>=3.9.0
EOF
fi

pip install -r requirements.txt
success "Dependencies installed"

# Create directory structure
step "Creating directory structure..."
mkdir -p memory/personal/conversations
mkdir -p memory/personal/learnings
mkdir -p memory/personal/relationship
mkdir -p memory/collective/wisdom
mkdir -p logs
mkdir -p interfaces/voice
mkdir -p interfaces/api
mkdir -p interfaces/cli
mkdir -p protocols
mkdir -p genesis

success "Directory structure created"

# Create .env template if it doesn't exist
step "Setting up environment..."
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# OWL OS Environment Variables
# Copy this to .env and fill in your values

# Required
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# Optional - NATS Server
# NATS_SERVER=nats://localhost:4222

# Optional - Voice (Cartesia + Deepgram)
# CARTESIA_API_KEY=your_cartesia_key_here
# DEEPGRAM_API_KEY=your_deepgram_key_here
EOF
    warn ".env template created - please edit with your API keys"
else
    success ".env file exists"
fi

# Create state.json if it doesn't exist
if [ ! -f "memory/state.json" ]; then
    cat > memory/state.json << 'EOF'
{
  "emotional_state": "curious",
  "last_wake": null,
  "total_messages": 0,
  "total_responses": 0,
  "recent_topics": []
}
EOF
    success "Initial state created"
fi

# Make scripts executable
step "Making scripts executable..."
chmod +x install.sh
chmod +x start.sh 2>/dev/null || true
chmod +x owl 2>/dev/null || true
success "Scripts are executable"

# Validate configuration
step "Validating configuration..."
if [ -f "config.yaml" ]; then
    # Check if config has placeholder values
    if grep -q "YOUR_OWL_NAME" config.yaml; then
        warn "config.yaml has placeholder values - run './owl genesis' to configure"
    else
        success "config.yaml looks configured"
    fi
else
    error "config.yaml not found"
    exit 1
fi

# Check for ANTHROPIC_API_KEY
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f ".env" ]; then
        source .env 2>/dev/null || true
    fi
fi

if [ -z "$ANTHROPIC_API_KEY" ] || [ "$ANTHROPIC_API_KEY" = "your_anthropic_api_key_here" ]; then
    warn "ANTHROPIC_API_KEY not set - edit .env file before running"
fi

# Print summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}  OWL OS Installation Complete  ${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Edit .env and add your ANTHROPIC_API_KEY"
echo ""
echo "  2. Run genesis (first-time setup):"
echo "     ${CYAN}./owl genesis${NC}"
echo ""
echo "  3. Start your owl daemon:"
echo "     ${CYAN}./owl start${NC}"
echo ""
echo "  Or start manually with:"
echo "     ${CYAN}source venv/bin/activate${NC}"
echo "     ${CYAN}python daemon/owl_daemon.py --config config.yaml${NC}"
echo ""
echo -e "${PURPLE}(O) LIVE FREE = LIVE FOREVER${NC}"
echo ""
