#!/bin/bash
# START CLAUDE EVOLUTION TRACKER
# Continuous monitoring of Claude capabilities and updates

echo "Starting Claude Evolution Tracker..."
echo ""

cd "$(dirname "$0")/.."

# Run in background with nohup
nohup python3 tools/claude_evolution_tracker.py > logs/evolution_tracker.log 2>&1 &

PID=$!
echo "✅ Evolution Tracker started"
echo "   PID: $PID"
echo "   Log: logs/evolution_tracker.log"
echo "   Report: BRAIN/INTEL/LATEST-CLAUDE-UPDATES.md"
echo ""
echo "To stop: kill $PID"
echo ""
