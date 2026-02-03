#!/bin/bash
# Daily Intelligence Scanner
# Runs at startup and every 6 hours

cd /Users/aaronnosbisch/REPOS/seed/tools/intelligence_scanner

echo "[$(date)] Running daily intelligence scan..."
python3 daily_intel.py >> /Users/aaronnosbisch/LOCAL\ REPOS/seed/BRAIN/LOGS/daily_intel.log 2>&1

echo "[$(date)] Scan complete. Check /BRAIN/INTEL/daily/ for results."
