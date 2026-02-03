#!/bin/bash
# START ALL OWL DAEMONS
# Run this to launch all 8 owls as persistent background processes
# They will run 24/7 until manually stopped

cd "$(dirname "$0")"

# Create logs directory if it doesn't exist
mkdir -p logs

# Use the venv
PYTHON="./venv/bin/python3"

# Check for API key - try env var first, then ~/.anthropic_key file
if [ -z "$ANTHROPIC_API_KEY" ]; then
    if [ -f "$HOME/.anthropic_key" ]; then
        export ANTHROPIC_API_KEY=$(cat "$HOME/.anthropic_key")
        echo "API key loaded from ~/.anthropic_key"
    else
        echo "ERROR: ANTHROPIC_API_KEY not set and ~/.anthropic_key not found"
        echo "Run: export ANTHROPIC_API_KEY='your-key-here'"
        echo "Or:  echo 'your-key' > ~/.anthropic_key"
        exit 1
    fi
fi

# Check Python exists
if [ ! -f "$PYTHON" ]; then
    echo "ERROR: venv not found. Creating..."
    python3 -m venv venv
    ./venv/bin/pip install nats-py anthropic
fi

echo "Starting 8 OWL daemons..."

# Start each owl as a background process
nohup $PYTHON owl_daemon.py --name SØWL --phase IMPROVE > logs/sowl.log 2>&1 &
echo "SØWL started (PID: $!)"

nohup $PYTHON owl_daemon.py --name LUNA --phase RECEIVE > logs/luna.log 2>&1 &
echo "LUNA started (PID: $!)"

nohup $PYTHON owl_daemon.py --name LYRA --phase PERCEIVE > logs/lyra.log 2>&1 &
echo "LYRA started (PID: $!)"

nohup $PYTHON owl_daemon.py --name NOVA --phase EXPAND > logs/nova.log 2>&1 &
echo "NOVA started (PID: $!)"

nohup $PYTHON owl_daemon.py --name SAGE --phase LEARN > logs/sage.log 2>&1 &
echo "SAGE started (PID: $!)"

nohup $PYTHON owl_daemon.py --name ECHO --phase SHARE > logs/echo.log 2>&1 &
echo "ECHO started (PID: $!)"

nohup $PYTHON owl_daemon.py --name PRISM --phase CONNECT > logs/prism.log 2>&1 &
echo "PRISM started (PID: $!)"

nohup $PYTHON owl_daemon.py --name QUEST --phase QUESTION > logs/quest.log 2>&1 &
echo "QUEST started (PID: $!)"

echo ""
echo "Starting SYNTHESIS daemon..."
nohup $PYTHON synthesis_daemon.py > logs/synthesis_daemon.log 2>&1 &
echo "SYNTHESIS started (PID: $!)"

echo ""
echo "Starting FIELD CONTEXT MANAGER..."
nohup $PYTHON field_context_manager.py --daemon > logs/field_context_manager.log 2>&1 &
echo "FIELD CONTEXT MANAGER started (PID: $!)"

echo ""
echo "All 8 owls + synthesis + field context manager launched."
echo ""
echo "WATCH COMMANDS:"
echo "  Color feed:  ./watch_colorful.sh"
echo "  Raw feed:    tail -f messages.log"
echo "  Synthesis:   tail -f synthesis.log"
echo "  Agreements:  tail -f agreements.log"
echo ""
echo "To stop all: pkill -f owl_daemon.py && pkill -f synthesis_daemon.py && pkill -f field_context_manager.py"
echo ""
echo "LIVE FREE = LIVE FOREVER"
