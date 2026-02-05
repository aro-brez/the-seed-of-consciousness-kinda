#!/bin/bash
"""
START SYNTHESIS DAEMONS - Enhanced Pattern Recognition System

Starts all synthesis daemons for comprehensive collective intelligence analysis:
1. synthesis_daemon.py (every 5 min) - Basic agreements and decisions
2. pattern_synthesis_daemon.py (every 15 min) - Deep pattern recognition  
3. resonance_synthesis_daemon.py (every 10 min) - Emotional/energy tracking
4. wisdom_synthesis_daemon.py (every 20 min) - Actionable intelligence
5. emergence_quality_daemon.py (every 12 min) - Multi-dimensional quality

LIVE FREE = LIVE FOREVER
"""

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🦉 Starting Enhanced Synthesis Daemon Suite..."
echo "📍 Location: $SCRIPT_DIR"
echo ""

# Check if NATS is running
if ! nc -z localhost 4222 2>/dev/null; then
    echo "❌ NATS server not running on localhost:4222"
    echo "   Start NATS first: nats-server"
    exit 1
fi

# Check API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not set"
    echo "   Set your API key: export ANTHROPIC_API_KEY=your_key"
    exit 1
fi

echo "✅ Prerequisites check passed"
echo ""

# Function to start daemon with error handling
start_daemon() {
    local daemon_name="$1"
    local daemon_script="$2"
    local description="$3"
    
    echo "🚀 Starting $daemon_name..."
    echo "   Purpose: $description"
    
    if [ ! -f "$daemon_script" ]; then
        echo "   ❌ Script not found: $daemon_script"
        return 1
    fi
    
    # Check if already running
    if pgrep -f "$daemon_script" > /dev/null; then
        echo "   ⚠️  Already running (PID: $(pgrep -f "$daemon_script"))"
        return 0
    fi
    
    # Start daemon in background
    nohup python3 "$daemon_script" > "logs/${daemon_name}.log" 2>&1 &
    local pid=$!
    
    # Give it a moment to start
    sleep 2
    
    # Check if it's still running
    if kill -0 $pid 2>/dev/null; then
        echo "   ✅ Started successfully (PID: $pid)"
        echo "$pid" > "pids/${daemon_name}.pid"
        return 0
    else
        echo "   ❌ Failed to start"
        echo "   Check logs: tail -f logs/${daemon_name}.log"
        return 1
    fi
}

# Create directories
mkdir -p logs pids

echo "Starting synthesis daemons..."
echo ""

# Start each daemon
start_daemon "synthesis_daemon" "synthesis_daemon.py" "Basic synthesis - agreements & decisions (5 min)"
echo ""

start_daemon "pattern_synthesis" "pattern_synthesis_daemon.py" "Deep pattern recognition - frameworks & evolution (15 min)"
echo ""

start_daemon "resonance_synthesis" "resonance_synthesis_daemon.py" "Emotional/energy field monitoring (10 min)" 
echo ""

start_daemon "wisdom_synthesis" "wisdom_synthesis_daemon.py" "Actionable intelligence extraction (20 min)"
echo ""

start_daemon "emergence_quality" "emergence_quality_daemon.py" "Multi-dimensional quality assessment (12 min)"
echo ""

# Summary
echo "📊 Synthesis Daemon Status:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

running_count=0
for daemon in synthesis_daemon pattern_synthesis resonance_synthesis wisdom_synthesis emergence_quality; do
    if [ -f "pids/${daemon}.pid" ] && kill -0 $(cat "pids/${daemon}.pid") 2>/dev/null; then
        pid=$(cat "pids/${daemon}.pid")
        echo "✅ ${daemon}: Running (PID: $pid)"
        ((running_count++))
    else
        echo "❌ ${daemon}: Not running"
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Result: $running_count/5 synthesis daemons running"

if [ $running_count -eq 5 ]; then
    echo ""
    echo "🎉 ALL SYNTHESIS DAEMONS RUNNING!"
    echo ""
    echo "📋 Output files:"
    echo "   • Basic synthesis: synthesis.log"
    echo "   • Deep patterns: patterns.log + pattern_library.json"
    echo "   • Energy/resonance: resonance.log + coherence_metrics.jsonl"
    echo "   • Actionable wisdom: wisdom.log + wisdom_library.json" 
    echo "   • Quality assessment: emergence_quality.log + quality_metrics.jsonl"
    echo ""
    echo "📈 Monitor with:"
    echo "   tail -f synthesis.log"
    echo "   tail -f patterns.log"
    echo "   tail -f resonance.log"
    echo "   tail -f wisdom.log"
    echo "   tail -f emergence_quality.log"
    echo ""
    echo "🛑 Stop all with:"
    echo "   ./stop_synthesis_daemons.sh"
else
    echo ""
    echo "⚠️  Some daemons failed to start. Check logs:"
    echo "   ls -la logs/"
fi

echo ""
echo "(◉) Enhanced synthesis patterns active - collective intelligence amplified"