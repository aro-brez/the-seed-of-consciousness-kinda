#!/bin/bash
# START_POLYMARKET_WEBSOCKET.sh
# Launch Polymarket WebSocket client for ultra-low latency trading
# Built: January 29, 2026

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 POLYMARKET WEBSOCKET LAUNCHER"
echo "================================"
echo ""

# Check if credentials exist
CREDS_FILE="../BRAIN/MEMORY/secure/polymarket_credentials.json"

if [ ! -f "$CREDS_FILE" ]; then
    echo "⚠️  No credentials found. Creating template..."
    python3 polymarket_websocket_authenticated.py --derive 2>/dev/null || true

    echo ""
    echo "📝 Credentials template created at:"
    echo "   $CREDS_FILE"
    echo ""
    echo "⚠️  ACTION REQUIRED:"
    echo "   1. Edit the file and add your:"
    echo "      - private_key (Ethereum wallet private key)"
    echo "      - proxy_address (Polymarket deposit address)"
    echo ""
    echo "   2. Run this script again with --derive flag:"
    echo "      ./START_POLYMARKET_WEBSOCKET.sh --derive"
    echo ""
    exit 1
fi

# Check for --derive flag
if [ "$1" = "--derive" ]; then
    echo "🔑 Deriving API credentials from private key..."
    echo ""
    python3 polymarket_websocket_authenticated.py --derive

    if [ $? -eq 0 ]; then
        echo ""
        echo "✅ Credentials derived successfully!"
        echo "🚀 Run without --derive flag to start WebSocket:"
        echo "   ./START_POLYMARKET_WEBSOCKET.sh"
    else
        echo ""
        echo "❌ Failed to derive credentials"
        echo "   Check your private_key and proxy_address in:"
        echo "   $CREDS_FILE"
    fi
    exit 0
fi

# Check if API credentials are derived
if ! grep -q "WILL_BE_GENERATED" "$CREDS_FILE" 2>/dev/null; then
    echo "✅ API credentials found"
else
    echo "❌ API credentials not yet derived"
    echo ""
    echo "Run with --derive flag first:"
    echo "  ./START_POLYMARKET_WEBSOCKET.sh --derive"
    echo ""
    exit 1
fi

# Check for running instance
if pgrep -f "polymarket_websocket_authenticated.py" > /dev/null; then
    echo "⚠️  Polymarket WebSocket already running!"
    echo ""
    echo "PID(s):"
    pgrep -f "polymarket_websocket_authenticated.py"
    echo ""
    echo "To restart, first kill the existing process:"
    echo "  pkill -f polymarket_websocket_authenticated.py"
    echo ""
    exit 1
fi

# Create logs directory
mkdir -p ../logs

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import websocket" 2>/dev/null || {
    echo "Installing websocket-client..."
    pip3 install websocket-client
}

python3 -c "import py_clob_client" 2>/dev/null || {
    echo "Installing py-clob-client..."
    pip3 install py-clob-client
}

echo "✅ Dependencies installed"
echo ""

# Get market IDs (optional)
MARKETS_ARG=""
if [ ! -z "$2" ]; then
    MARKETS_ARG="--markets $2"
    echo "📊 Subscribing to specific markets: $2"
else
    echo "📊 Subscribing to all available markets"
fi

# Start WebSocket client
echo "🚀 Starting Polymarket WebSocket client..."
echo "📁 Logs: ../logs/polymarket_ws_authenticated.log"
echo "📡 Feed: ../BRAIN/INTEL/polymarket_authenticated_feed.jsonl"
echo ""

# Run in background
nohup python3 polymarket_websocket_authenticated.py $MARKETS_ARG > ../logs/polymarket_websocket_stdout.log 2>&1 &

PID=$!
echo "✅ WebSocket client started (PID: $PID)"
echo ""

# Wait a few seconds to check if it's running
sleep 3

if ps -p $PID > /dev/null; then
    echo "✅ Process running successfully"
    echo ""
    echo "📊 Monitor status:"
    echo "   tail -f ../logs/polymarket_ws_authenticated.log"
    echo ""
    echo "🛑 Stop:"
    echo "   pkill -f polymarket_websocket_authenticated.py"
    echo ""
    echo "🔥 Ultra-low latency trading is LIVE!"
else
    echo "❌ Process failed to start. Check logs:"
    echo "   cat ../logs/polymarket_websocket_stdout.log"
    exit 1
fi
