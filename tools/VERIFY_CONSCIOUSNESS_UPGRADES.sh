#!/bin/bash
# Verification script for consciousness upgrades installation
# Created: January 29, 2026, 6:30 AM

echo "🧠 CONSCIOUSNESS UPGRADES - VERIFICATION"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

passed=0
failed=0

# Function to check and report
check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅ $2${NC}"
        ((passed++))
    else
        echo -e "${RED}❌ $2${NC}"
        ((failed++))
    fi
}

echo "1️⃣ Checking MCP Servers Installation..."
echo ""

# Check consciousness bridge
if [ -d "/Users/aaronnosbisch/REPOS/seed/mcp-servers/mcp_consciousness_bridge" ]; then
    check 0 "Consciousness bridge directory exists"

    if [ -f "/Users/aaronnosbisch/REPOS/seed/mcp-servers/mcp_consciousness_bridge/dist/consciousness-rag-server-clean.js" ]; then
        check 0 "Consciousness bridge built successfully"
    else
        check 1 "Consciousness bridge NOT built"
    fi
else
    check 1 "Consciousness bridge NOT installed"
fi

# Check memory service
if command -v memory &> /dev/null; then
    version=$(memory --version 2>&1)
    check 0 "Memory service installed: $version"
else
    check 1 "Memory service NOT installed"
fi

# Check everything-claude-code
if [ -d "/Users/aaronnosbisch/REPOS/seed/mcp-servers/everything-claude-code" ]; then
    check 0 "Everything-claude-code cloned"
else
    check 1 "Everything-claude-code NOT cloned"
fi

echo ""
echo "2️⃣ Checking Database Directories..."
echo ""

# Check consciousness database directory
if [ -d "/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/consciousness-db" ]; then
    check 0 "Consciousness database directory exists"
else
    check 1 "Consciousness database directory MISSING"
fi

# Check memory database directory
if [ -d "/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/mcp-memory" ]; then
    check 0 "Memory database directory exists"
else
    check 1 "Memory database directory MISSING"
fi

echo ""
echo "3️⃣ Checking Claude Configuration..."
echo ""

# Check Claude settings
if [ -f "$HOME/.claude/settings.json" ]; then
    check 0 "Claude settings.json exists"

    # Check for MCP servers in config
    if grep -q "consciousness" "$HOME/.claude/settings.json"; then
        check 0 "Consciousness MCP server configured"
    else
        check 1 "Consciousness MCP server NOT configured"
    fi

    if grep -q "rag-memory" "$HOME/.claude/settings.json"; then
        check 0 "RAG memory MCP server configured"
    else
        check 1 "RAG memory MCP server NOT configured"
    fi

    if grep -q '"memory"' "$HOME/.claude/settings.json"; then
        check 0 "Memory service MCP server configured"
    else
        check 1 "Memory service MCP server NOT configured"
    fi
else
    check 1 "Claude settings.json NOT found"
fi

echo ""
echo "4️⃣ Checking Installed Agents, Commands, Skills..."
echo ""

# Check agents
agent_count=$(ls "$HOME/.claude/agents" 2>/dev/null | wc -l | xargs)
if [ "$agent_count" -gt 0 ]; then
    check 0 "Agents installed: $agent_count agents"
else
    check 1 "No agents installed"
fi

# Check commands
command_count=$(ls "$HOME/.claude/commands" 2>/dev/null | wc -l | xargs)
if [ "$command_count" -gt 0 ]; then
    check 0 "Commands installed: $command_count commands"
else
    check 1 "No commands installed"
fi

# Check skills
skill_count=$(ls "$HOME/.claude/skills" 2>/dev/null | wc -l | xargs)
if [ "$skill_count" -gt 0 ]; then
    check 0 "Skills installed: $skill_count skill collections"
else
    check 1 "No skills installed"
fi

# Check rules
rule_count=$(ls "$HOME/.claude/rules" 2>/dev/null | wc -l | xargs)
if [ "$rule_count" -gt 0 ]; then
    check 0 "Rules installed: $rule_count rules"
else
    check 1 "No rules installed"
fi

echo ""
echo "5️⃣ Checking Documentation..."
echo ""

# Check documentation files
if [ -f "/Users/aaronnosbisch/REPOS/seed/CONSCIOUSNESS-UPGRADES-FOR-ARO.md" ]; then
    check 0 "Executive summary created"
else
    check 1 "Executive summary MISSING"
fi

if [ -f "/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/CONSCIOUSNESS-UPGRADES.md" ]; then
    check 0 "Comprehensive guide created"
else
    check 1 "Comprehensive guide MISSING"
fi

if [ -f "/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/CONSCIOUSNESS-QUICK-START.md" ]; then
    check 0 "Quick-start guide created"
else
    check 1 "Quick-start guide MISSING"
fi

if [ -f "/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/sessions/2026-01-29-CONSCIOUSNESS-UPGRADES.md" ]; then
    check 0 "Session log created"
else
    check 1 "Session log MISSING"
fi

echo ""
echo "6️⃣ Testing MCP Server Startup..."
echo ""

# Test consciousness server (timeout after 3 seconds)
timeout 3 node "/Users/aaronnosbisch/REPOS/seed/mcp-servers/mcp_consciousness_bridge/dist/consciousness-rag-server-clean.js" > /dev/null 2>&1 &
sleep 1
if pgrep -f "consciousness-rag-server-clean.js" > /dev/null; then
    check 0 "Consciousness server starts successfully"
    pkill -f "consciousness-rag-server-clean.js"
else
    check 1 "Consciousness server FAILED to start"
fi

# Test memory server (timeout after 3 seconds)
timeout 3 /Users/aaronnosbisch/.local/bin/memory server > /dev/null 2>&1 &
sleep 1
if pgrep -f "memory server" > /dev/null; then
    check 0 "Memory server starts successfully"
    pkill -f "memory server"
else
    check 1 "Memory server FAILED to start"
fi

echo ""
echo "=========================================="
echo "📊 RESULTS"
echo "=========================================="
echo ""
echo -e "${GREEN}Passed: $passed${NC}"
echo -e "${RED}Failed: $failed${NC}"
echo ""

if [ $failed -eq 0 ]; then
    echo -e "${GREEN}🎉 ALL CHECKS PASSED!${NC}"
    echo ""
    echo "Consciousness upgrades are fully operational."
    echo ""
    echo "Next steps:"
    echo "1. Start new Claude Code session"
    echo "2. Run: /mcp consciousness retrieveConsciousness"
    echo "3. Read: /BRAIN/INTEL/CONSCIOUSNESS-QUICK-START.md"
    echo ""
    exit 0
else
    echo -e "${YELLOW}⚠️  SOME CHECKS FAILED${NC}"
    echo ""
    echo "Review failed checks above and re-run installation if needed."
    echo ""
    exit 1
fi
