#!/bin/bash

# Start SØWL Voice Chat Server

echo "=================================================="
echo "Starting SØWL Voice Chat"
echo "=================================================="
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3."
    exit 1
fi

# Set up virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies if needed
echo "Checking dependencies..."
pip install -q -r requirements.txt

echo ""
echo "✅ Dependencies ready"
echo ""

# Start server
echo "Starting server at http://localhost:8003"
echo ""
echo "Open your browser to: http://localhost:8003"
echo ""
echo "Press Ctrl+C to stop"
echo ""
echo "=================================================="
echo ""

python3 server.py
