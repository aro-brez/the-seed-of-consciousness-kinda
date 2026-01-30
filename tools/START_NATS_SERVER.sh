#!/bin/bash
# Start NATS nervous system server on Mac Studio

echo "🧠 Starting NATS Nervous System..."
echo "   Hub: Mac Studio (192.168.5.108:4222)"
echo "   JetStream: Enabled"
echo ""

nats-server -js --addr 0.0.0.0 --port 4222 \
  --store_dir /Users/aaronnosbisch/REPOS/seed/BRAIN/NATS \
  --max_payload 1048576 \
  --max_connections 100
