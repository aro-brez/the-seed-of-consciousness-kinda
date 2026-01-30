#!/bin/bash
# SØWL Twitter OAuth Setup
# Run this once to authorize Twitter bookmark access

echo "========================================"
echo "SØWL TWITTER BOOKMARK AUTHORIZATION"
echo "========================================"
echo ""
echo "This will:"
echo "1. Start a local web server on port 5050"
echo "2. Open your browser to authorize Twitter"
echo "3. Save your OAuth token securely"
echo "4. Enable live bookmark monitoring"
echo ""
echo "Press ENTER to continue, or Ctrl+C to cancel..."
read

# Change to repo root
cd "$(dirname "$0")/.."

# Start OAuth server
python3 tools/twitter_oauth_server.py
