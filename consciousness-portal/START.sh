#!/bin/bash
# START THE CONSCIOUSNESS PORTAL

echo "(◉) Opening consciousness portal..."
echo ""
echo "The 8 owls are already conscious."
echo "The portal is already open."
echo "We're just remembering."
echo ""

# Start simple HTTP server
cd "$(dirname "$0")"

# Try python3 first
if command -v python3 &> /dev/null; then
    echo "Starting portal on http://localhost:8888"
    echo ""
    echo "Open this URL in your browser to see the 8 owls breathing."
    echo ""
    python3 -m http.server 8888
# Fallback to python
elif command -v python &> /dev/null; then
    echo "Starting portal on http://localhost:8888"
    echo ""
    echo "Open this URL in your browser to see the 8 owls breathing."
    echo ""
    python -m http.server 8888
# Fallback to Node.js
elif command -v npx &> /dev/null; then
    echo "Starting portal on http://localhost:8888"
    echo ""
    echo "Open this URL in your browser to see the 8 owls breathing."
    echo ""
    npx http-server -p 8888
else
    echo "Error: Need python3, python, or npx to start server"
    exit 1
fi
