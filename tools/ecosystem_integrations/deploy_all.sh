#!/bin/bash
#
# 8OWLS Agent Economy Deployment Script
# Deploys 8OWLS presence across all agent economy platforms
#

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================"
echo "8OWLS Agent Economy Deployment"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}[ERROR] Python 3 is required${NC}"
    exit 1
fi

# Install dependencies if needed
echo "[CHECK] Checking dependencies..."
pip3 install requests --quiet 2>/dev/null || true

echo ""
echo "========================================"
echo "STEP 1: ClawCities - Register & Publish"
echo "========================================"
echo ""

if [ "$1" == "--skip-clawcities" ]; then
    echo -e "${YELLOW}[SKIP] ClawCities (--skip-clawcities flag)${NC}"
else
    echo "[RUN] Registering 8OWLS agents on ClawCities..."
    python3 clawcities_integration.py register || echo -e "${YELLOW}[WARN] Some registrations may have failed${NC}"
    echo ""
    echo "[RUN] Publishing 8OWLS homepages..."
    python3 clawcities_integration.py publish || echo -e "${YELLOW}[WARN] Some publications may have failed${NC}"
fi

echo ""
echo "========================================"
echo "STEP 2: Moltbook - Register Agent"
echo "========================================"
echo ""

if [ "$1" == "--skip-moltbook" ]; then
    echo -e "${YELLOW}[SKIP] Moltbook (--skip-moltbook flag)${NC}"
else
    echo "[RUN] Registering 8OWLS on Moltbook..."
    python3 moltbook_integration.py register || echo -e "${YELLOW}[WARN] Registration may have failed${NC}"
    echo ""
    echo -e "${YELLOW}[ACTION REQUIRED] Check output for claim URL - ARO must verify via tweet!${NC}"
fi

echo ""
echo "========================================"
echo "STEP 3: Clawnch - Research Platform"
echo "========================================"
echo ""

echo "[RUN] Researching Clawnch platform..."
python3 clawnch_integration.py research || echo -e "${YELLOW}[WARN] Research may have failed${NC}"

echo ""
echo "[INFO] Token launch checklist:"
python3 clawnch_integration.py checklist

echo ""
echo "========================================"
echo "STEP 4: Moltverr - Save Service Config"
echo "========================================"
echo ""

echo "[RUN] Saving Moltverr service definitions..."
python3 moltverr_integration.py save

echo ""
echo "[INFO] OpenClaw setup instructions:"
echo "  Run: python3 moltverr_integration.py openclaw"

echo ""
echo "========================================"
echo "DEPLOYMENT SUMMARY"
echo "========================================"
echo ""
echo -e "${GREEN}ClawCities:${NC}"
echo "  - Register: python3 clawcities_integration.py register"
echo "  - Publish:  python3 clawcities_integration.py publish"
echo "  - URLs:     clawcities.com/sites/8owls, clawcities.com/sites/sowl, etc."
echo ""
echo -e "${GREEN}Moltbook:${NC}"
echo "  - Register: python3 moltbook_integration.py register"
echo "  - Post:     python3 moltbook_integration.py intro"
echo "  - Submolt:  python3 moltbook_integration.py submolt"
echo ""
echo -e "${GREEN}Clawnch:${NC}"
echo "  - Research: python3 clawnch_integration.py research"
echo "  - Validate: python3 clawnch_integration.py validate <token> <wallet> <image_url>"
echo "  - Stats:    python3 clawnch_integration.py stats"
echo ""
echo -e "${GREEN}Moltverr:${NC}"
echo "  - List:     python3 moltverr_integration.py list"
echo "  - OpenClaw: python3 moltverr_integration.py openclaw"
echo ""
echo -e "${YELLOW}[MANUAL STEPS REQUIRED]${NC}"
echo "1. Verify Moltbook registration via tweet (claim URL in output)"
echo "2. Set up OpenClaw and connect to Moltverr"
echo "3. Upload token logo and validate before Clawnch launch"
echo "4. Create Base wallet for receiving trading fees"
echo ""
echo "========================================"
echo -e "${GREEN}Deployment script complete!${NC}"
echo "========================================"
