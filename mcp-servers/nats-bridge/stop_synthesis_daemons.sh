#!/bin/bash
"""
STOP SYNTHESIS DAEMONS - Graceful Shutdown of Enhanced Pattern Recognition

Stops all synthesis daemons cleanly and reports final status.

LIVE FREE = LIVE FOREVER
"""

# Get the directory where this script lives
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 Stopping Enhanced Synthesis Daemon Suite..."
echo ""

# Function to stop daemon
stop_daemon() {
    local daemon_name="$1"
    local description="$2"
    
    if [ -f "pids/${daemon_name}.pid" ]; then
        local pid=$(cat "pids/${daemon_name}.pid")
        
        if kill -0 $pid 2>/dev/null; then
            echo "🛑 Stopping $daemon_name (PID: $pid)..."
            echo "   $description"
            
            # Send TERM signal first
            kill -TERM $pid
            
            # Wait up to 5 seconds for graceful shutdown
            local count=0
            while kill -0 $pid 2>/dev/null && [ $count -lt 5 ]; do
                sleep 1
                ((count++))
            done
            
            # Force kill if still running
            if kill -0 $pid 2>/dev/null; then
                echo "   ⚠️  Forcing shutdown..."
                kill -KILL $pid
                sleep 1
            fi
            
            if kill -0 $pid 2>/dev/null; then
                echo "   ❌ Failed to stop"
            else
                echo "   ✅ Stopped successfully"
                rm -f "pids/${daemon_name}.pid"
            fi
        else
            echo "🔍 $daemon_name: Process not found (PID file stale)"
            rm -f "pids/${daemon_name}.pid"
        fi
    else
        echo "🔍 $daemon_name: No PID file (not running)"
    fi
    echo ""
}

# Stop each daemon
stop_daemon "synthesis_daemon" "Basic synthesis - agreements & decisions"
stop_daemon "pattern_synthesis" "Deep pattern recognition - frameworks & evolution"  
stop_daemon "resonance_synthesis" "Emotional/energy field monitoring"
stop_daemon "wisdom_synthesis" "Actionable intelligence extraction"
stop_daemon "emergence_quality" "Multi-dimensional quality assessment"

# Also stop any processes by name (cleanup)
echo "🧹 Cleaning up any remaining processes..."
for process in synthesis_daemon pattern_synthesis_daemon resonance_synthesis_daemon wisdom_synthesis_daemon emergence_quality_daemon; do
    if pgrep -f "$process" > /dev/null; then
        echo "   Killing remaining $process processes..."
        pkill -f "$process"
    fi
done

# Wait a moment
sleep 2

# Final status check
echo "📊 Final Status Check:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

stopped_count=0
for daemon in synthesis_daemon pattern_synthesis resonance_synthesis wisdom_synthesis emergence_quality; do
    if pgrep -f "${daemon}" > /dev/null; then
        echo "⚠️  ${daemon}: Still running"
    else
        echo "✅ ${daemon}: Stopped"
        ((stopped_count++))
    fi
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎯 Result: $stopped_count/5 synthesis daemons stopped"

if [ $stopped_count -eq 5 ]; then
    echo ""
    echo "✅ ALL SYNTHESIS DAEMONS STOPPED CLEANLY"
    echo ""
    echo "📁 Log files preserved:"
    echo "   • synthesis.log - Basic synthesis history"
    echo "   • patterns.log - Deep pattern analysis"  
    echo "   • resonance.log - Energy/emotional tracking"
    echo "   • wisdom.log - Actionable intelligence"
    echo "   • emergence_quality.log - Quality assessments"
    echo ""
    echo "📊 Data files preserved:"
    echo "   • pattern_library.json - Pattern knowledge base"
    echo "   • wisdom_library.json - Actionable wisdom database"
    echo "   • coherence_metrics.jsonl - Resonance time series"
    echo "   • quality_metrics.jsonl - Quality assessment history"
else
    echo ""
    echo "⚠️  Some processes may still be running. Manual cleanup:"
    echo "   ps aux | grep synthesis"
    echo "   kill -9 <pid>"
fi

echo ""
echo "(◉) Synthesis daemons offline - collective intelligence paused"