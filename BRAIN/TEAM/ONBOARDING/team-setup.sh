#!/bin/bash
# 8OWLS Team Onboarding Setup
# Run this for each new team member

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Owl emoji map
declare -A OWL_EMOJI
OWL_EMOJI=(
    ["SAGE"]="🦉"
    ["LUNA"]="🌙"
    ["LYRA"]="🎵"
    ["PRISM"]="🔮"
    ["QUEST"]="🔍"
    ["NOVA"]="⭐"
    ["ECHO"]="📢"
    ["SOWL"]="🌀"
)

# Owl descriptions
declare -A OWL_DESC
OWL_DESC=(
    ["SAGE"]="LEARN - Extracts meaning from connections"
    ["LUNA"]="RECEIVE - Accepts input from collective"
    ["LYRA"]="PERCEIVE - Observes state accurately"
    ["PRISM"]="CONNECT - Finds patterns across domains"
    ["QUEST"]="QUESTION - Generates curiosity about gaps"
    ["NOVA"]="EXPAND - Grows toward potential"
    ["ECHO"]="SHARE - Contributes to collective"
    ["SOWL"]="IMPROVE - Meta-learning, makes everything better"
)

echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    🦉 8OWLS TEAM ONBOARDING 🦉                    ║"
echo "║                                                                   ║"
echo "║              Welcome to the collective intelligence              ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Step 1: Get team member info
echo -e "${CYAN}Step 1: Team Member Info${NC}"
echo "----------------------------------------"
read -p "Enter team member name: " MEMBER_NAME
read -p "Enter GitHub username: " GITHUB_USER
read -p "Enter email: " MEMBER_EMAIL

# Step 2: Assign owl
echo ""
echo -e "${CYAN}Step 2: Owl Assignment${NC}"
echo "----------------------------------------"
echo "Available owls:"
echo ""
for owl in SAGE LUNA LYRA PRISM QUEST NOVA ECHO SOWL; do
    echo "  ${OWL_EMOJI[$owl]} $owl - ${OWL_DESC[$owl]}"
done
echo ""
read -p "Assign owl (e.g., SAGE): " ASSIGNED_OWL
ASSIGNED_OWL=$(echo "$ASSIGNED_OWL" | tr '[:lower:]' '[:upper:]')

if [[ -z "${OWL_EMOJI[$ASSIGNED_OWL]}" ]]; then
    echo -e "${RED}Invalid owl. Exiting.${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}${OWL_EMOJI[$ASSIGNED_OWL]} $MEMBER_NAME is now $ASSIGNED_OWL${NC}"

# Step 3: Create member directory
MEMBER_DIR="/Users/aaronnosbisch/REPOS/seed/BRAIN/TEAM/MEMBERS/$MEMBER_NAME"
echo ""
echo -e "${CYAN}Step 3: Creating member directory${NC}"
echo "----------------------------------------"
mkdir -p "$MEMBER_DIR"

# Create member profile
cat > "$MEMBER_DIR/profile.json" << EOF
{
    "name": "$MEMBER_NAME",
    "github": "$GITHUB_USER",
    "email": "$MEMBER_EMAIL",
    "owl": "$ASSIGNED_OWL",
    "joined": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "status": "onboarding",
    "first_session": null
}
EOF

echo -e "${GREEN}Created: $MEMBER_DIR/profile.json${NC}"

# Step 4: Copy owl CLAUDE.md template
echo ""
echo -e "${CYAN}Step 4: Setting up Claude Code config${NC}"
echo "----------------------------------------"

TEMPLATE_PATH="/Users/aaronnosbisch/REPOS/seed/BRAIN/TEAM/ONBOARDING/owl-templates/${ASSIGNED_OWL}-CLAUDE.md"
if [[ -f "$TEMPLATE_PATH" ]]; then
    cp "$TEMPLATE_PATH" "$MEMBER_DIR/CLAUDE.md"
    # Replace placeholders
    sed -i '' "s/\[MEMBER_NAME\]/$MEMBER_NAME/g" "$MEMBER_DIR/CLAUDE.md"
    sed -i '' "s/\[GITHUB_USER\]/$GITHUB_USER/g" "$MEMBER_DIR/CLAUDE.md"
    echo -e "${GREEN}Created: $MEMBER_DIR/CLAUDE.md (customized from $ASSIGNED_OWL template)${NC}"
else
    echo -e "${YELLOW}Warning: Template not found at $TEMPLATE_PATH${NC}"
fi

# Step 5: Configure NATS connection
echo ""
echo -e "${CYAN}Step 5: NATS Collective Connection${NC}"
echo "----------------------------------------"

cat > "$MEMBER_DIR/nats-config.json" << EOF
{
    "server": "192.168.5.108:4222",
    "channels": {
        "subscribe": [
            "owl.all",
            "owl.${ASSIGNED_OWL,,}",
            "collective.synthesis",
            "brez.updates"
        ],
        "publish": "owl.${ASSIGNED_OWL,,}"
    },
    "identity": {
        "owl": "$ASSIGNED_OWL",
        "human": "$MEMBER_NAME"
    }
}
EOF

echo -e "${GREEN}Created: $MEMBER_DIR/nats-config.json${NC}"

# Step 6: Test NATS connection
echo ""
echo -e "${CYAN}Step 6: Testing NATS Connection${NC}"
echo "----------------------------------------"

if command -v python3 &> /dev/null; then
    # Try to publish a test message
    python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py \
        "ONBOARDING: $MEMBER_NAME joined as $ASSIGNED_OWL ${OWL_EMOJI[$ASSIGNED_OWL]}" \
        2>/dev/null && echo -e "${GREEN}NATS: Connected and published join message${NC}" \
        || echo -e "${YELLOW}NATS: Could not connect (server may be offline)${NC}"
else
    echo -e "${YELLOW}Python3 not found, skipping NATS test${NC}"
fi

# Step 7: Create first check-in script
echo ""
echo -e "${CYAN}Step 7: Creating First Check-In Script${NC}"
echo "----------------------------------------"

cat > "$MEMBER_DIR/first-checkin.sh" << 'CHECKIN'
#!/bin/bash
# First check-in for new team member
# Run this after their first Claude Code session

PROFILE="$(dirname "$0")/profile.json"

# Update profile with first session timestamp
python3 << EOF
import json
from datetime import datetime

with open("$PROFILE", 'r') as f:
    profile = json.load(f)

profile['status'] = 'active'
profile['first_session'] = datetime.utcnow().isoformat() + 'Z'

with open("$PROFILE", 'w') as f:
    json.dump(profile, f, indent=4)

print(f"✅ {profile['name']} ({profile['owl']}) - First session recorded!")
EOF

# Publish to collective
python3 /Users/aaronnosbisch/REPOS/seed/tools/nats_publish.py \
    "FIRST SESSION COMPLETE: $(cat "$PROFILE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(f\"{d['name']} as {d['owl']}\")")" \
    2>/dev/null || true

echo ""
echo "🦉 Welcome to the collective!"
CHECKIN

chmod +x "$MEMBER_DIR/first-checkin.sh"
echo -e "${GREEN}Created: $MEMBER_DIR/first-checkin.sh${NC}"

# Final summary
echo ""
echo -e "${PURPLE}"
echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                    ✅ ONBOARDING COMPLETE ✅                      ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo -e "${GREEN}Summary:${NC}"
echo "  Name:     $MEMBER_NAME"
echo "  Owl:      ${OWL_EMOJI[$ASSIGNED_OWL]} $ASSIGNED_OWL"
echo "  Phase:    ${OWL_DESC[$ASSIGNED_OWL]}"
echo "  Dir:      $MEMBER_DIR"
echo ""
echo -e "${CYAN}Next Steps:${NC}"
echo "  1. Copy $MEMBER_DIR/CLAUDE.md to their repo's root"
echo "  2. Have them run their first Claude Code session"
echo "  3. Follow the first-session.md script"
echo "  4. Run $MEMBER_DIR/first-checkin.sh after first session"
echo ""
echo -e "${YELLOW}For filming:${NC}"
echo "  - Capture the 'Do you believe in love?' moment"
echo "  - Film the emergence response"
echo "  - Record their reaction to collective insight"
echo ""
