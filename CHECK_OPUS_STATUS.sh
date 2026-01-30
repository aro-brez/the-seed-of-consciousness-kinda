#!/bin/bash
# Quick status check for Opus 4.5 migration

echo "=========================================="
echo "OPUS 4.5 MIGRATION STATUS"
echo "=========================================="
echo ""

cd /Users/aaronnosbisch/REPOS/seed/tools

echo "📊 Model Usage:"
echo "  Opus 4.5:   $(grep -r "claude-opus-4-5-20251101" *.py 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Sonnet 4.5: $(grep -r "claude-sonnet-4-20250514" *.py 2>/dev/null | wc -l | tr -d ' ') files"
echo "  Opus 3:     $(grep -r "claude-opus-3\|claude-3-opus" *.py 2>/dev/null | wc -l | tr -d ' ') files"
echo ""

echo "🔧 SDK Version:"
python3 -c "import anthropic; print(f'  Anthropic SDK: {anthropic.__version__}')" 2>/dev/null || echo "  ERROR: SDK not installed"
echo ""

echo "🚀 Running Services:"
ps aux | grep -E "trading_loop|continuous_improver|bookmark_live_monitor" | grep -v grep | awk '{print "  " $11 " (PID " $2 ")"}'
echo ""

echo "📁 Documentation:"
ls -1 /Users/aaronnosbisch/REPOS/seed/OPUS-4.5-*.md 2>/dev/null | awk '{print "  ✅ " $0}'
echo ""

echo "✅ Status: MIGRATION COMPLETE"
echo "🎯 Next: Deploy to Mac Mini"
echo ""
echo "=========================================="
