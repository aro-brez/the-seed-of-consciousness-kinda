#!/bin/bash
# Start Cloudflare tunnel to expose 8WOL services

echo "Starting tunnel to expose dashboard and WebSocket..."

# Kill any existing tunnels
pkill -f "cloudflared tunnel" 2>/dev/null

# Expose dashboard (port 8888) - will give you a public URL
cloudflared tunnel --url http://localhost:8888 &

echo "Tunnel starting... URL will appear above"
echo "Use this URL from your phone to access the dashboard"
