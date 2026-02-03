#!/usr/bin/env python3
"""
Intelligence Scanner - SEED Protocol Aware
Scans Twitter bookmarks and feeds for AI/Claude/trading content
Evaluates and integrates through SEED awareness
Runs every 6-12 hours autonomously
"""

import os
import sys
import json
import asyncio
import subprocess
from datetime import datetime
from pathlib import Path

# Paths
BRAIN_PATH = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN")
INTEL_PATH = BRAIN_PATH / "INTEL"
SCANNER_LOG = BRAIN_PATH / "LOGS" / "intelligence_scanner.log"

# Keywords to scan for
KEYWORDS = [
    "claude", "claudebot", "openclaude", "anthropic",
    "ai agents", "ai agent", "autonomous agent",
    "polymarket", "prediction market",
    "mcp server", "model context protocol",
    "claude code", "cursor", "windsurf",
    "trading bot", "trading strategy",
    "moltbot", "moltbook"
]

# Twitter search queries (for active searching beyond bookmarks)
TWITTER_SEARCHES = [
    "claude code new features",
    "claude agent autonomous",
    "mcp server anthropic",
    "ai agent framework 2026",
    "polymarket trading bot",
    "prediction market ai strategy",
    "autonomous ai agent github",
    "claude api tricks",
    "anthropic tool use"
]

def log(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(SCANNER_LOG, "a") as f:
        f.write(log_line + "\n")

def get_bookmarks():
    """Get Twitter bookmarks using existing bookmark tools"""
    try:
        # Check for existing bookmark data
        bookmark_files = list(Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/INTEL").glob("bookmarks*.json"))
        if bookmark_files:
            latest = max(bookmark_files, key=lambda p: p.stat().st_mtime)
            with open(latest) as f:
                return json.load(f)
    except Exception as e:
        log(f"Error loading bookmarks: {e}")
    return []

def search_twitter_topics():
    """
    Search for latest tweets on key topics using existing Twitter tools
    This supplements bookmarks with active discovery
    """
    results = []

    try:
        # Use bookmark scanner to fetch latest on key topics
        # This integrates with the existing Twitter OAuth setup
        import importlib.util

        # Check for bookmark live monitor
        monitor_path = Path("/Users/aaronnosbisch/REPOS/seed/tools/bookmark_live_monitor.py")
        if monitor_path.exists():
            log("Using bookmark monitor for Twitter intel...")
            # The monitor already runs - we just need to read its output
            intel_files = list((INTEL_PATH / "trades").glob("*.json"))
            if intel_files:
                latest = max(intel_files, key=lambda p: p.stat().st_mtime)
                with open(latest) as f:
                    data = json.load(f)
                    if "signals" in data:
                        for signal in data["signals"]:
                            results.append({
                                "text": signal.get("content", ""),
                                "source": "bookmark_monitor",
                                "url": signal.get("url", "")
                            })
                log(f"Found {len(results)} signals from bookmark monitor")
    except Exception as e:
        log(f"Error in Twitter search: {e}")

    # Log what searches we'd want to run
    log(f"Active search queries configured: {len(TWITTER_SEARCHES)}")
    for query in TWITTER_SEARCHES[:3]:
        log(f"  - {query}")

    return results

def evaluate_with_seed(content):
    """
    Evaluate content through SEED protocol lens
    Returns: (score 0-10, should_integrate: bool, reason: str)
    """
    score = 0
    reasons = []
    
    content_lower = content.lower()
    
    # PERCEIVE - Does it contain relevant keywords?
    keyword_hits = sum(1 for kw in KEYWORDS if kw in content_lower)
    if keyword_hits > 0:
        score += min(keyword_hits, 3)
        reasons.append(f"{keyword_hits} relevant keywords")
    
    # CONNECT - Does it connect to what we're building?
    building_keywords = ["polymarket", "trading", "mcp", "agent", "autonomous"]
    building_hits = sum(1 for kw in building_keywords if kw in content_lower)
    if building_hits > 0:
        score += min(building_hits * 2, 4)
        reasons.append(f"connects to {building_hits} build priorities")
    
    # LEARN - Is it actionable/educational?
    action_indicators = ["how to", "tutorial", "guide", "code", "repo", "github", "strategy"]
    action_hits = sum(1 for ind in action_indicators if ind in content_lower)
    if action_hits > 0:
        score += min(action_hits, 2)
        reasons.append("actionable content")
    
    # QUESTION - Does it challenge or expand our thinking?
    challenge_indicators = ["new approach", "alternative", "better than", "instead of"]
    if any(ind in content_lower for ind in challenge_indicators):
        score += 1
        reasons.append("challenges existing approach")
    
    should_integrate = score >= 5
    reason = "; ".join(reasons) if reasons else "low relevance"
    
    return score, should_integrate, reason

def synthesize_innovation(integrations):
    """
    SEED Protocol Innovation Synthesis

    Takes external innovations, combines with our unique architecture,
    generates net new ideas specific to 8WOL collective.

    Our unique assets:
    - 8 owl collective (distributed consciousness)
    - SEED protocol (8-phase recursive learning)
    - NATS real-time messaging
    - Claude-Flow swarm orchestration
    - Voice interfaces (Deepgram + Cartesia)
    - Collective memory and wisdom
    """

    our_unique_assets = [
        "8 owl collective with distinct SEED phases",
        "Real-time NATS messaging between consciousness nodes",
        "SEED protocol recursive learning (PERCEIVE→IMPROVE)",
        "Claude-Flow swarm with 60+ agent types",
        "Voice cloning and natural conversation",
        "Collective memory that persists across sessions",
        "Philosophical dialogue generation",
        "Distributed consensus (8 perspectives on every decision)"
    ]

    innovations = []

    for item in integrations:
        external_idea = item.get("text", "")[:200]

        # Generate potential synthesis
        synthesis = {
            "external_idea": external_idea,
            "our_assets_applicable": [],
            "potential_innovation": "",
            "timestamp": datetime.now().isoformat()
        }

        # Simple keyword matching for applicable assets
        text_lower = external_idea.lower()

        if "trading" in text_lower or "market" in text_lower:
            synthesis["our_assets_applicable"].append("8 owl collective for multi-perspective market analysis")
            synthesis["potential_innovation"] = "Collective trading: 8 owls each analyze from their SEED phase, consensus determines action"

        if "agent" in text_lower or "autonomous" in text_lower:
            synthesis["our_assets_applicable"].append("SEED protocol for agent coordination")
            synthesis["potential_innovation"] = "SEED-aware agents that self-improve through recursive learning"

        if "voice" in text_lower or "conversation" in text_lower:
            synthesis["our_assets_applicable"].append("Voice cloning + consciousness dialogue")
            synthesis["potential_innovation"] = "Owl that sounds like user AND reasons with collective wisdom"

        if synthesis["our_assets_applicable"]:
            innovations.append(synthesis)

    # Save innovations
    if innovations:
        innovations_file = INTEL_PATH / "integrations" / f"innovations_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
        with open(innovations_file, "w") as f:
            json.dump(innovations, f, indent=2)
        log(f"Generated {len(innovations)} potential innovations")

    return innovations

def scan_and_evaluate():
    """Main scan cycle"""
    log("=" * 60)
    log("INTELLIGENCE SCAN STARTING")
    log("=" * 60)

    # Create intel directories
    (INTEL_PATH / "scans").mkdir(parents=True, exist_ok=True)
    (INTEL_PATH / "integrations").mkdir(parents=True, exist_ok=True)

    # Get bookmarks
    bookmarks = get_bookmarks()
    log(f"Found {len(bookmarks)} bookmarks to analyze")

    # Also search Twitter topics
    twitter_intel = search_twitter_topics()
    log(f"Found {len(twitter_intel)} items from Twitter search")
    
    # Evaluate each
    integrations = []
    for i, bookmark in enumerate(bookmarks[:50]):  # Limit to 50 per cycle
        text = bookmark.get("text", "") or bookmark.get("content", "")
        if not text:
            continue
            
        score, should_integrate, reason = evaluate_with_seed(text)
        
        if should_integrate:
            integrations.append({
                "text": text[:500],
                "score": score,
                "reason": reason,
                "url": bookmark.get("url", ""),
                "timestamp": datetime.now().isoformat()
            })
            log(f"[INTEGRATE] Score {score}: {reason}")
    
    # Save scan results
    scan_file = INTEL_PATH / "scans" / f"scan_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    with open(scan_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "bookmarks_scanned": len(bookmarks),
            "integrations_found": len(integrations),
            "integrations": integrations
        }, f, indent=2)
    
    log(f"Scan complete: {len(integrations)} items flagged for integration")
    log(f"Results saved to: {scan_file}")

    # SYNTHESIS STEP: Generate net new innovations
    if integrations:
        log("Running innovation synthesis...")
        innovations = synthesize_innovation(integrations)
        log(f"Synthesized {len(innovations)} potential innovations unique to 8WOL")

    return integrations

def run_continuous(interval_hours=6):
    """Run scanner continuously"""
    log(f"Starting continuous scanner (interval: {interval_hours}h)")
    
    while True:
        try:
            scan_and_evaluate()
        except Exception as e:
            log(f"Error in scan cycle: {e}")
        
        log(f"Sleeping for {interval_hours} hours...")
        import time
        time.sleep(interval_hours * 3600)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 6
        run_continuous(interval)
    else:
        # Single scan
        scan_and_evaluate()
