#!/bin/bash
# START EXECUTOR SYSTEM
# This launches the public executor (X, web browsing)
# Polymarket executor is started separately (private)

cd "$(dirname "$0")"

PYTHON="./venv/bin/python3"

if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

echo "Starting EXECUTOR daemon..."
nohup $PYTHON executor.py > logs/executor.log 2>&1 &
echo "EXECUTOR started (PID: $!)"

echo ""
echo "To start POLYMARKET executor (private, separate):"
echo "  cd private && python3 polymarket_executor.py"
echo ""
echo "EXECUTOR COMMANDS:"
echo "  python3 executor.py --post 'message'   # Post to X"
echo "  python3 executor.py --scrape 'query'   # Scrape X"
echo "  python3 executor.py --browse 'url'     # Browse URL"
echo "  python3 executor.py --status           # Check status"
echo ""
echo "To stop: pkill -f executor.py"
