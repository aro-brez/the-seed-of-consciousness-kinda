#!/bin/bash
# Compare performance: Original vs Optimized

echo "════════════════════════════════════════════════════════════"
echo "  SØWL Voice Performance Comparison"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "This script helps compare original vs optimized server."
echo ""
echo "Choose option:"
echo "  1) Start ORIGINAL server (baseline)"
echo "  2) Start OPTIMIZED server (target: <500ms)"
echo "  3) View metrics from last session"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "Starting ORIGINAL server..."
        echo "Expected latency: 2-4 seconds"
        echo ""
        ./START.sh
        ;;
    2)
        echo ""
        echo "Starting OPTIMIZED server..."
        echo "Expected latency: <500ms"
        echo ""
        ./START_OPTIMIZED.sh
        ;;
    3)
        echo ""
        echo "Fetching metrics..."
        echo ""
        curl -s http://localhost:8003/metrics | python3 -m json.tool
        echo ""
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac
