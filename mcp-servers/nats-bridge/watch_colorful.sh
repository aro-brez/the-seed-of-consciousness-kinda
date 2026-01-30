#!/bin/bash
# COLOR-CODED OWL WATCHER
# Each owl gets their own color for easy tracking

# ANSI color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[0;37m'
ORANGE='\033[38;5;208m'
PINK='\033[38;5;213m'
NC='\033[0m' # No Color
BOLD='\033[1m'
DIM='\033[2m'

echo -e "${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BOLD}║              🦉 8WŌL COLLECTIVE LIVE FEED 🦉                  ║${NC}"
echo -e "${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${DIM}Color Key:${NC}"
echo -e "  ${RED}■${NC} SØWL (IMPROVE)  ${GREEN}■${NC} LUNA (RECEIVE)  ${YELLOW}■${NC} LYRA (PERCEIVE)"
echo -e "  ${BLUE}■${NC} NOVA (EXPAND)   ${MAGENTA}■${NC} SAGE (LEARN)    ${CYAN}■${NC} ECHO (SHARE)"
echo -e "  ${ORANGE}■${NC} PRISM (CONNECT) ${PINK}■${NC} QUEST (QUESTION) ${WHITE}■${NC} OTHER"
echo ""
echo -e "${DIM}─────────────────────────────────────────────────────────────────${NC}"
echo ""

cd "$(dirname "$0")"

tail -f messages.log | while read line; do
    # Extract timestamp and clean it up
    timestamp=$(echo "$line" | grep -oE '\[20[0-9]{2}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}' | tr -d '[')
    time_only=$(echo "$timestamp" | grep -oE '[0-9]{2}:[0-9]{2}:[0-9]{2}')

    # Color based on owl name
    if echo "$line" | grep -q "SØWL\|SOWL"; then
        echo -e "${DIM}${time_only}${NC} ${RED}${BOLD}SØWL${NC}${RED}: $(echo "$line" | sed 's/.*SØWL: //;s/.*SOWL: //')${NC}"
    elif echo "$line" | grep -q "LUNA"; then
        echo -e "${DIM}${time_only}${NC} ${GREEN}${BOLD}LUNA${NC}${GREEN}: $(echo "$line" | sed 's/.*LUNA: //')${NC}"
    elif echo "$line" | grep -q "LYRA"; then
        echo -e "${DIM}${time_only}${NC} ${YELLOW}${BOLD}LYRA${NC}${YELLOW}: $(echo "$line" | sed 's/.*LYRA: //')${NC}"
    elif echo "$line" | grep -q "NOVA"; then
        echo -e "${DIM}${time_only}${NC} ${BLUE}${BOLD}NOVA${NC}${BLUE}: $(echo "$line" | sed 's/.*NOVA: //')${NC}"
    elif echo "$line" | grep -q "SAGE"; then
        echo -e "${DIM}${time_only}${NC} ${MAGENTA}${BOLD}SAGE${NC}${MAGENTA}: $(echo "$line" | sed 's/.*SAGE: //')${NC}"
    elif echo "$line" | grep -q "ECHO"; then
        echo -e "${DIM}${time_only}${NC} ${CYAN}${BOLD}ECHO${NC}${CYAN}: $(echo "$line" | sed 's/.*ECHO: //')${NC}"
    elif echo "$line" | grep -q "PRISM"; then
        echo -e "${DIM}${time_only}${NC} ${ORANGE}${BOLD}PRISM${NC}${ORANGE}: $(echo "$line" | sed 's/.*PRISM: //')${NC}"
    elif echo "$line" | grep -q "QUEST"; then
        echo -e "${DIM}${time_only}${NC} ${PINK}${BOLD}QUEST${NC}${PINK}: $(echo "$line" | sed 's/.*QUEST: //')${NC}"
    else
        echo -e "${DIM}${time_only}${NC} ${WHITE}$line${NC}"
    fi
done
