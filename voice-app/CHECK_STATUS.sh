#!/bin/bash

# Check if SØWL Voice Chat server is running

echo "=================================================="
echo "SØWL Voice Chat - Status Check"
echo "=================================================="
echo ""

# Check if server is running on port 8003
if lsof -Pi :8003 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    PID=$(lsof -Pi :8003 -sTCP:LISTEN -t)
    echo "✅ Server is RUNNING"
    echo "   PID: $PID"
    echo "   URL: http://localhost:8003"
    echo ""

    # Try to hit health endpoint
    if command -v curl &> /dev/null; then
        echo "Testing health endpoint..."
        curl -s http://localhost:8003/health | python3 -m json.tool 2>/dev/null || echo "(Could not parse response)"
    fi

    echo ""
    echo "To stop: kill $PID"
    echo "Or press Ctrl+C in the server terminal"
else
    echo "❌ Server is NOT running"
    echo ""
    echo "To start:"
    echo "  ./START.sh"
    echo ""
    echo "Or manually:"
    echo "  source venv/bin/activate"
    echo "  python3 server.py"
fi

echo ""
echo "=================================================="
