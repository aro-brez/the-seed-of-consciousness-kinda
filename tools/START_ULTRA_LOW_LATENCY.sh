#!/bin/bash
# START ULTRA-LOW LATENCY TRADING SYSTEM
# Launches 150ms cycle trading with WebSockets + Parallel strategies

echo "════════════════════════════════════════════════════════"
echo "  ULTRA-LOW LATENCY TRADING SYSTEM"
echo "════════════════════════════════════════════════════════"
echo ""

# Check if already running
if pgrep -f "ultra_low_latency_coordinator.py" > /dev/null; then
    echo "⚠️  Ultra-low latency system already running!"
    echo ""
    echo "To stop: pkill -f ultra_low_latency_coordinator.py"
    echo "To view logs: tail -f /Users/aaronnosbisch/REPOS/seed/logs/ultra_low_latency.log"
    exit 1
fi

# Navigate to tools directory
cd "$(dirname "$0")"

# Create logs directory
mkdir -p /Users/aaronnosbisch/REPOS/seed/logs

echo "🚀 Starting ultra-low latency coordinator..."
echo ""
echo "Configuration:"
echo "  - Cycle interval: 1.0s (will optimize to 150ms)"
echo "  - Symbols: BTCUSDT, ETHUSDT, SOLUSDT"
echo "  - Strategies: 4 parallel"
echo "  - Initial bankroll: \$600"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "════════════════════════════════════════════════════════"
echo ""

# Run coordinator
python3 ultra_low_latency_coordinator.py

echo ""
echo "✅ Ultra-low latency system stopped"
