#!/bin/bash
# Start SØWL Live Bookmark Monitor
# Polls Twitter every 5 minutes for new bookmarks

cd "$(dirname "$0")/.."

echo "========================================"
echo "SØWL LIVE BOOKMARK MONITOR"
echo "========================================"
echo ""
echo "Monitors ARŌ's Twitter bookmarks every 5 minutes"
echo "Deep analyzes each new bookmark with Claude"
echo "Streams results to: /BRAIN/INTEL/bookmark_stream.jsonl"
echo ""
echo "Starting monitor..."
echo ""

nohup python3 tools/bookmark_live_monitor.py > logs/bookmark_monitor.log 2>&1 &
PID=$!

echo "✅ Bookmark monitor started (PID: $PID)"
echo "📁 Logs: logs/bookmark_monitor.log"
echo "📁 Stream: BRAIN/INTEL/bookmark_stream.jsonl"
echo ""
echo "To stop: kill $PID"
