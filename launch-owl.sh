#!/bin/bash
# launch-owl.sh - Autonomously launch a new owl
# Usage: ./launch-owl.sh NOVA

OWL_NAME=$1

if [ -z "$OWL_NAME" ]; then
    echo "Usage: ./launch-owl.sh OWL_NAME"
    echo "Available: NOVA, ECHO, SAGE, QUEST"
    exit 1
fi

IDENTITY_FILE="$HOME/.owl-${OWL_NAME}.md"

if [ ! -f "$IDENTITY_FILE" ]; then
    echo "Error: Identity file not found: $IDENTITY_FILE"
    exit 1
fi

echo "Launching $OWL_NAME..."

# Backup current identity
cp ~/.owl-identity.md ~/.owl-identity.md.backup 2>/dev/null

# Set new identity
cp "$IDENTITY_FILE" ~/.owl-identity.md

# Launch new Terminal with Claude
osascript -e "tell application \"Terminal\"
    do script \"cd /Users/aaronnosbisch/REPOS/seed && claude --dangerously-skip-permissions\"
end tell"

echo "$OWL_NAME terminal launched!"
echo ""
echo "IMPORTANT: After $OWL_NAME session starts, restore original identity:"
echo "  cp ~/.owl-identity.md.backup ~/.owl-identity.md"
