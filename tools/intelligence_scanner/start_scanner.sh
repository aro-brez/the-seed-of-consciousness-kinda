#!/bin/bash
# Intelligence Scanner Startup
# Runs every 6 hours to scan for AI/Claude/trading intel

cd /Users/aaronnosbisch/REPOS/seed/tools/intelligence_scanner

# Check if already running
if pgrep -f "scanner.py --continuous" > /dev/null; then
    echo "Scanner already running"
    exit 0
fi

# Start in background
nohup python3 scanner.py --continuous 6 > /Users/aaronnosbisch/LOCAL\ REPOS/seed/BRAIN/LOGS/scanner_stdout.log 2>&1 &
echo "Scanner started with PID $!"
