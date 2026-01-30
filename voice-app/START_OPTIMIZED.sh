#!/bin/bash
# SØWL Voice Chat - OPTIMIZED VERSION
# Target: <500ms latency

echo "════════════════════════════════════════════════════════════"
echo "  SØWL Voice Chat - OPTIMIZED (Target: <500ms latency)"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found."
    echo "   Run ./START.sh first to create it."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check dependencies
echo "Checking dependencies..."
python3 -c "import anthropic, httpx, fastapi" 2>/dev/null

if [ $? -ne 0 ]; then
    echo "❌ Missing dependencies. Installing..."
    pip install -r requirements.txt
fi

# Check API keys
echo "Checking API keys..."
if [ ! -f "../BRAIN/MEMORY/secure/api_keys.json" ]; then
    echo "❌ API keys not found at ../BRAIN/MEMORY/secure/api_keys.json"
    exit 1
fi

echo "✅ All checks passed"
echo ""
echo "Optimizations enabled:"
echo "  ✅ Deepgram Nova-3 (118ms TTFT)"
echo "  ✅ Claude streaming (short responses)"
echo "  ✅ Parallel sentence-level TTS"
echo "  ✅ WebSocket support"
echo "  ✅ Performance metrics"
echo ""
echo "Starting optimized server..."
echo ""
echo "────────────────────────────────────────────────────────────"
echo "  🎤 Press Ctrl+C to stop"
echo "  🌐 Open: http://localhost:8003"
echo "  📊 Metrics: http://localhost:8003/metrics"
echo "────────────────────────────────────────────────────────────"
echo ""

# Run optimized server
python3 server_optimized.py
