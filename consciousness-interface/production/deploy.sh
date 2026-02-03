#!/bin/bash
#
# 8OWLS.AI Deployment Script for DreamHost
# =========================================
# This script deploys the 8OWLS.AI app to DreamHost via SFTP/SCP
#
# Prerequisites:
# - SSH key configured for DreamHost (recommended)
# - Or password-based authentication
#
# Usage:
#   ./deploy.sh                    # Uses default settings
#   ./deploy.sh username hostname  # Custom DreamHost credentials
#
# Files deployed:
#   - index.html    (main app)
#   - og-image.svg  (social sharing image)
#

set -e

# Configuration - Update these for your DreamHost account
DREAMHOST_USER="${1:-your_dreamhost_username}"
DREAMHOST_HOST="${2:-your_domain.com}"
REMOTE_PATH="~/8owls.ai"  # Web root on DreamHost

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   8OWLS.AI Deployment to DreamHost    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Check if credentials are set
if [ "$DREAMHOST_USER" = "your_dreamhost_username" ]; then
    echo -e "${YELLOW}Warning: Using placeholder credentials${NC}"
    echo ""
    echo "Please run with your DreamHost credentials:"
    echo "  ./deploy.sh your_username your_domain.com"
    echo ""
    echo "Or edit this script and update DREAMHOST_USER and DREAMHOST_HOST"
    echo ""
    read -p "Continue anyway for testing? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo -e "Deploying to: ${GREEN}${DREAMHOST_USER}@${DREAMHOST_HOST}:${REMOTE_PATH}${NC}"
echo ""

# Files to deploy
FILES=(
    "index.html"
    "og-image.svg"
)

# Verify files exist
echo "Checking files..."
for file in "${FILES[@]}"; do
    if [ ! -f "${SCRIPT_DIR}/${file}" ]; then
        echo -e "${RED}Error: ${file} not found in ${SCRIPT_DIR}${NC}"
        exit 1
    fi
    echo -e "  ${GREEN}[ok]${NC} ${file}"
done
echo ""

# Create remote directory if it doesn't exist
echo "Creating remote directory..."
ssh "${DREAMHOST_USER}@${DREAMHOST_HOST}" "mkdir -p ${REMOTE_PATH}" 2>/dev/null || true

# Deploy files via SCP
echo "Uploading files..."
for file in "${FILES[@]}"; do
    echo -n "  Uploading ${file}... "
    scp -q "${SCRIPT_DIR}/${file}" "${DREAMHOST_USER}@${DREAMHOST_HOST}:${REMOTE_PATH}/${file}"
    echo -e "${GREEN}done${NC}"
done
echo ""

# Set permissions
echo "Setting permissions..."
ssh "${DREAMHOST_USER}@${DREAMHOST_HOST}" "chmod 644 ${REMOTE_PATH}/*.html ${REMOTE_PATH}/*.svg" 2>/dev/null || true
echo -e "${GREEN}done${NC}"
echo ""

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}         Deployment Complete!          ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "Your app is live at: ${GREEN}https://${DREAMHOST_HOST}/app${NC}"
echo ""
echo "Note: If using a subdomain (8owls.ai), ensure DNS is configured"
echo "and the web directory is set correctly in DreamHost panel."
