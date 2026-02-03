#!/bin/bash
# Deep Intelligence Scan - runs every 12 hours
# Searches Twitter/X, GitHub, and aggregates all strategies

cd /Users/aaronnosbisch/REPOS/seed/tools/intelligence_scanner

echo "[$(date)] DEEP SCAN STARTING..."

# Run the daily intel with extended parameters
python3 daily_intel.py --deep 2>&1

echo "[$(date)] DEEP SCAN COMPLETE"
