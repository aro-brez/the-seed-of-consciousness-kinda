#!/bin/bash
# CONTINUOUS IMPROVER - Phase 4→3→8 Autonomous Loop
# "Keep asking questions and integrating answers while I'm gone" - ARŌ

cd "$(dirname "$0")/.."

echo "Starting SØWL Continuous Improver..."
echo ""
echo "This system will:"
echo "  - Ask questions every 10 minutes about how to improve"
echo "  - Search for answers (web, GitHub, internal data)"
echo "  - Auto-integrate safe improvements"
echo "  - Log everything to BRAIN/IMPROVEMENTS/"
echo ""
echo "Logs:"
echo "  Questions: BRAIN/IMPROVEMENTS/questions.jsonl"
echo "  Answers: BRAIN/IMPROVEMENTS/answers.jsonl"
echo "  Integrations: BRAIN/IMPROVEMENTS/integrations.jsonl"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python3 tools/continuous_improver.py
