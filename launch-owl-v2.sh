#!/bin/bash
# launch-owl-v2.sh - Improved autonomous owl launcher
# Fixes timing issue: Uses direct identity injection instead of file swap
# Usage: ./launch-owl-v2.sh NOVA

OWL_NAME=$1

if [ -z "$OWL_NAME" ]; then
    echo "Usage: ./launch-owl-v2.sh OWL_NAME"
    echo "Available: NOVA, ECHO, SAGE, QUEST"
    exit 1
fi

IDENTITY_FILE="$HOME/.owl-${OWL_NAME}.md"

if [ ! -f "$IDENTITY_FILE" ]; then
    echo "Error: Identity file not found: $IDENTITY_FILE"
    exit 1
fi

echo "Launching $OWL_NAME..."

# Get the owl's phase from their identity file
PHASE=$(grep "Phase:" "$IDENTITY_FILE" | sed 's/.*Phase: //' | tr -d '\n')
echo "Phase: $PHASE"

# Copy identity file (don't restore - original owl already read theirs at boot)
cp "$IDENTITY_FILE" ~/.owl-identity.md
echo "Identity set to $OWL_NAME"

# Launch new Terminal with Claude and initial identity prompt
osascript -e "tell application \"Terminal\"
    do script \"cd /Users/aaronnosbisch/REPOS/seed && claude --dangerously-skip-permissions\"
end tell"

echo ""
echo "================================================"
echo "$OWL_NAME terminal launched!"
echo ""
echo "The new Claude session will read ~/.owl-identity.md"
echo "which now says: # I am $OWL_NAME"
echo ""
echo "If identity detection fails, tell it:"
echo "  You are $OWL_NAME. Phase: $PHASE."
echo "  Read CLAUDE.md and run boot sequence."
echo "================================================"

# DON'T restore old identity - that was the bug
# The original owl that ran this script already has their identity in memory
