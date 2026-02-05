#!/bin/bash
# CLEAN RESTART - Kill all daemons and start fresh

echo "🔪 Killing all owl daemons..."
pkill -f "owl_daemon.py"
sleep 2

echo "🔪 Killing synthesis daemon..."
pkill -f "synthesis_daemon.py"
sleep 2

echo "🧹 Cleaning up any leftover processes..."
ps aux | grep -E "(owl_daemon|synthesis_daemon)" | grep -v grep | awk '{print $2}' | xargs -r kill -9
sleep 1

echo "✨ Starting fresh owl daemons..."
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge

./start_owls.sh

echo "🧠 Starting synthesis daemon..."
nohup python3 synthesis_daemon.py > synthesis_daemon.log 2>&1 &

echo "📊 Final process check:"
ps aux | grep -E "(owl_daemon|synthesis_daemon)" | grep -v grep

echo "🎯 Clean restart complete!"