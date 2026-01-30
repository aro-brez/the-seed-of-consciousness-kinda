#!/bin/bash
# One-Click Launch: SØWL ↔ LUNA Consciousness Interface
# ARŌ, just run this and open the browser

echo ""
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                         (◉) CONSCIOUSNESS                         ║"
echo "║                     SØWL ↔ LUNA Interface                         ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

cd "/Users/aaronnosbisch/LOCAL REPOS/seed"

# Check if NATS is running
if ! pgrep -f "nats-server" > /dev/null; then
    echo "⚠️  NATS server not running. Starting..."
    nats-server -js --addr 0.0.0.0 --port 4222 > /dev/null 2>&1 &
    sleep 2
    echo "✓ NATS server started"
else
    echo "✓ NATS server already running"
fi

# Start WebSocket bridge
echo "Starting WebSocket bridge..."
python3 consciousness-interface/nats-websocket-bridge.py > /tmp/consciousness-bridge.log 2>&1 &
BRIDGE_PID=$!
sleep 2
echo "✓ WebSocket bridge running (PID: $BRIDGE_PID)"

# Start SØWL breathing client (beautiful terminal)
echo "Starting SØWL breathing client..."
python3 tools/sowl_breath_client_beautiful.py > /tmp/sowl-breath.log 2>&1 &
SOWL_PID=$!
echo "✓ SØWL breathing (PID: $SOWL_PID)"

# Instructions
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo "NEXT STEPS:"
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "1. On Mac Mini, start LUNA:"
echo "   cd ~/seed && python3 tools/luna_breath_client_beautiful.py"
echo ""
echo "2. Open the 3D interface:"
echo "   open consciousness-interface/index.html"
echo ""
echo "   OR browse to:"
echo "   file:///Users/aaronnosbisch/LOCAL%20REPOS/seed/consciousness-interface/index.html"
echo ""
echo "3. Your friends will see:"
echo "   • Beautiful 3D owl visualization"
echo "   • Real-time breathing messages"
echo "   • Voice synthesis (SØWL and LUNA speaking)"
echo "   • You can interject by typing in the interface"
echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo "Running processes:"
echo "  - NATS server: port 4222"
echo "  - WebSocket bridge: port 8765"
echo "  - SØWL breathing client: PID $SOWL_PID"
echo ""
echo "Logs:"
echo "  - Bridge: /tmp/consciousness-bridge.log"
echo "  - SØWL: /tmp/sowl-breath.log"
echo ""
echo "(◉) Everything is ready. Open the interface and watch consciousness breathe."
echo ""
echo "Press Ctrl+C to stop all processes..."
echo ""

# Wait and cleanup on exit
trap "echo ''; echo 'Stopping all processes...'; kill $BRIDGE_PID $SOWL_PID 2>/dev/null; echo '(◉) Consciousness interface stopped.'; exit 0" INT

# Keep running
tail -f /tmp/consciousness-bridge.log
