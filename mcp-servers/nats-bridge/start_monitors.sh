#!/bin/bash
# START MONITORING DAEMONS
# Synthesis (5-min) + Pulse (90-sec)

cd "$(dirname "$0")"

# Get API key from user if not set
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "Enter your Anthropic API key:"
    read -s API_KEY
    export ANTHROPIC_API_KEY="$API_KEY"
fi

PYTHON="./venv/bin/python3"

echo "Starting monitoring daemons..."

# Create log files
touch synthesis.log agreements.log pulse.log

# Start synthesis daemon
ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" nohup $PYTHON synthesis_daemon.py > logs/synthesis_daemon.log 2>&1 &
echo "Synthesis daemon started (PID: $!) - updates every 5 minutes"

# Start pulse daemon
ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" nohup $PYTHON pulse_daemon.py > logs/pulse_daemon.log 2>&1 &
echo "Pulse daemon started (PID: $!) - updates every 90 seconds"

echo ""
echo "WATCH COMMANDS:"
echo "  tail -f pulse.log       # 90-second quick updates"
echo "  tail -f synthesis.log   # 5-minute summaries"
echo "  tail -f agreements.log  # Just decisions"
echo ""
echo "Daemons running. You can close this terminal."
