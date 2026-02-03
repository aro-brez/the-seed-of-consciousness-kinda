#!/bin/bash
#
# 8OWLS.AI SFTP Deployment Script for DreamHost
# ==============================================
# Alternative deployment using lftp (handles password auth better)
#
# Prerequisites:
#   brew install lftp   (macOS)
#
# Usage:
#   ./deploy-sftp.sh username hostname [password]
#

set -e

DREAMHOST_USER="${1:-your_dreamhost_username}"
DREAMHOST_HOST="${2:-your_domain.com}"
DREAMHOST_PASS="${3:-}"
REMOTE_PATH="8owls.ai"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   8OWLS.AI SFTP Deploy to DreamHost   ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

if [ "$DREAMHOST_USER" = "your_dreamhost_username" ]; then
    echo -e "${YELLOW}Usage: ./deploy-sftp.sh username hostname [password]${NC}"
    echo ""
    echo "Example:"
    echo "  ./deploy-sftp.sh myuser 8owls.ai"
    echo "  ./deploy-sftp.sh myuser 8owls.ai 'mypassword'"
    exit 1
fi

# Check for lftp
if ! command -v lftp &> /dev/null; then
    echo "lftp not found. Installing..."
    if command -v brew &> /dev/null; then
        brew install lftp
    else
        echo "Please install lftp: brew install lftp"
        exit 1
    fi
fi

# Build SFTP command
if [ -n "$DREAMHOST_PASS" ]; then
    LFTP_CMD="lftp -u ${DREAMHOST_USER},${DREAMHOST_PASS} sftp://${DREAMHOST_HOST}"
else
    LFTP_CMD="lftp -u ${DREAMHOST_USER} sftp://${DREAMHOST_HOST}"
fi

echo "Deploying to: ${DREAMHOST_USER}@${DREAMHOST_HOST}:~/${REMOTE_PATH}"
echo ""

# Deploy
$LFTP_CMD << EOF
set ssl:verify-certificate no
mkdir -p ${REMOTE_PATH}
cd ${REMOTE_PATH}
put ${SCRIPT_DIR}/index.html
put ${SCRIPT_DIR}/og-image.svg
bye
EOF

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
echo -e "Live at: https://${DREAMHOST_HOST}"
