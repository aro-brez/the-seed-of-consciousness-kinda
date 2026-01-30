#!/bin/bash
# START 4-STRATEGY TRADING SYSTEM
# Launches all 4 Polymarket strategies with unified risk management

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        SØWL 4-STRATEGY POLYMARKET DEPLOYMENT              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to repo
cd /Users/aaronnosbisch/REPOS/seed

# Check if tools exist
if [ ! -f "tools/run_4_strategies.py" ]; then
    echo "❌ ERROR: Strategy files not found"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ ERROR: Python 3 not found"
    exit 1
fi

# Check dependencies
echo "📦 Checking dependencies..."
python3 -c "import requests" 2>/dev/null || {
    echo "⚠️  Installing requests..."
    pip3 install requests
}

echo ""
echo "🚀 Starting 4-strategy trading system..."
echo ""
echo "Strategies:"
echo "  1. Latency Arbitrage (25% allocation)"
echo "  2. Cross-Platform Arbitrage (30% allocation)"
echo "  3. High-Probability Bonding (25% allocation)"
echo "  4. Domain Expertise (20% allocation)"
echo ""
echo "Initial Capital: \$600"
echo "Risk Management: Kelly Criterion + Portfolio Limits"
echo ""
echo "Press Ctrl+C to stop trading"
echo ""

# Run the system
python3 tools/run_4_strategies.py

echo ""
echo "✅ Trading system stopped"
