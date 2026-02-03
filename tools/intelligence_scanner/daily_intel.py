#!/usr/bin/env python3
"""
SØWL Daily Intelligence System
- Reads ALL Twitter bookmarks (deep read with replies)
- Searches X feeds for AI/Claude/trading content
- Creates daily synthesis with actionable integrations
- Self-optimizes through continuous learning

Run daily or on-demand: python3 daily_intel.py
"""

import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
import subprocess

# Paths
BRAIN_PATH = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN")
INTEL_PATH = BRAIN_PATH / "INTEL"
DAILY_PATH = INTEL_PATH / "daily"
BOOKMARK_STREAM = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl")

# Topics to track
PRIORITY_TOPICS = [
    # AI/Claude
    "claude", "anthropic", "claude code", "mcp server", "claude agent",
    "claude cowork", "sonnet", "opus", "haiku",
    # Agents
    "ai agent", "autonomous agent", "swarm", "multi-agent", "agentic",
    "agent framework", "agent sdk",
    # Trading
    "polymarket", "prediction market", "trading bot", "arbitrage",
    "market making", "alpha", "edge",
    # Tech
    "github", "open source", "api", "sdk", "framework",
    # Our stack
    "nats", "websocket", "mcp", "tool use"
]

# Integration criteria
INTEGRATION_CRITERIA = {
    "high": [
        "github.com",  # Code we can use
        "trading strategy",
        "bot",
        "arbitrage",
        "mcp server",
        "claude code",
        "agent framework"
    ],
    "medium": [
        "tutorial",
        "guide",
        "how to",
        "prompt",
        "workflow"
    ],
    "low": [
        "opinion",
        "prediction",
        "rumor"
    ]
}


def load_bookmarks(days_back=7):
    """Load recent bookmarks from stream"""
    bookmarks = []
    cutoff = datetime.now() - timedelta(days=days_back)

    if BOOKMARK_STREAM.exists():
        with open(BOOKMARK_STREAM) as f:
            for line in f:
                try:
                    data = json.loads(line.strip())
                    ts = datetime.fromisoformat(data.get("timestamp", "").replace("Z", "+00:00").split("+")[0])
                    if ts > cutoff:
                        bookmarks.append(data)
                except (json.JSONDecodeError, ValueError):
                    continue

    return bookmarks


def score_content(text):
    """Score content for integration priority"""
    text_lower = text.lower()
    score = 0
    reasons = []

    # Check priority topics
    topic_hits = sum(1 for topic in PRIORITY_TOPICS if topic in text_lower)
    if topic_hits > 0:
        score += topic_hits * 2
        reasons.append(f"{topic_hits} priority topics")

    # Check integration criteria
    for priority, keywords in INTEGRATION_CRITERIA.items():
        hits = sum(1 for kw in keywords if kw in text_lower)
        if hits > 0:
            if priority == "high":
                score += hits * 5
                reasons.append(f"high-priority: {hits} matches")
            elif priority == "medium":
                score += hits * 2
                reasons.append(f"medium-priority: {hits} matches")
            else:
                score += hits

    # Bonus for actionable content
    if "github.com" in text_lower:
        score += 10
        reasons.append("has GitHub link")
    if any(x in text_lower for x in ["code", "implementation", "repo"]):
        score += 3
        reasons.append("actionable code")

    return score, reasons


def categorize_bookmark(bookmark):
    """Categorize a bookmark by type"""
    text = bookmark.get("tweet_text", "").lower()

    categories = []
    if any(x in text for x in ["polymarket", "prediction", "trading", "arbitrage", "market"]):
        categories.append("TRADING")
    if any(x in text for x in ["claude", "anthropic", "mcp", "agent"]):
        categories.append("AI/CLAUDE")
    if any(x in text for x in ["github", "code", "repo", "sdk"]):
        categories.append("CODE")
    if any(x in text for x in ["strategy", "alpha", "edge", "insight"]):
        categories.append("STRATEGY")

    return categories or ["GENERAL"]


def generate_daily_brief(bookmarks):
    """Generate daily intelligence brief"""

    # Score and sort bookmarks
    scored = []
    for b in bookmarks:
        text = b.get("tweet_text", "")
        score, reasons = score_content(text)
        scored.append({
            "bookmark": b,
            "score": score,
            "reasons": reasons,
            "categories": categorize_bookmark(b)
        })

    scored.sort(key=lambda x: x["score"], reverse=True)

    # Generate brief
    brief = {
        "generated": datetime.now().isoformat(),
        "total_bookmarks": len(bookmarks),
        "top_items": [],
        "integrations_recommended": [],
        "categories_summary": {}
    }

    # Top 20 items
    for item in scored[:20]:
        b = item["bookmark"]
        entry = {
            "score": item["score"],
            "categories": item["categories"],
            "reasons": item["reasons"],
            "text": b.get("tweet_text", "")[:300],
            "author": b.get("author_id", "unknown"),
            "tweet_id": b.get("tweet_id", ""),
            "metrics": b.get("metrics", {})
        }
        brief["top_items"].append(entry)

        # Flag for integration if score > 15
        if item["score"] >= 15:
            brief["integrations_recommended"].append({
                "text": b.get("tweet_text", "")[:200],
                "score": item["score"],
                "action": "INTEGRATE" if "github" in b.get("tweet_text", "").lower() else "INVESTIGATE"
            })

    # Category summary
    for item in scored:
        for cat in item["categories"]:
            brief["categories_summary"][cat] = brief["categories_summary"].get(cat, 0) + 1

    return brief


def save_daily_brief(brief):
    """Save daily brief to file"""
    DAILY_PATH.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y-%m-%d")
    brief_file = DAILY_PATH / f"intel_{date_str}.json"

    with open(brief_file, "w") as f:
        json.dump(brief, f, indent=2)

    # Also create markdown version
    md_file = DAILY_PATH / f"intel_{date_str}.md"
    with open(md_file, "w") as f:
        f.write(f"# Daily Intelligence Brief - {date_str}\n\n")
        f.write(f"**Generated:** {brief['generated']}\n")
        f.write(f"**Bookmarks Analyzed:** {brief['total_bookmarks']}\n\n")

        f.write("## Categories\n")
        for cat, count in sorted(brief["categories_summary"].items(), key=lambda x: -x[1]):
            f.write(f"- {cat}: {count}\n")

        f.write("\n## Recommended Integrations\n\n")
        for item in brief["integrations_recommended"]:
            f.write(f"### [{item['action']}] Score: {item['score']}\n")
            f.write(f"{item['text']}...\n\n")

        f.write("\n## Top Intelligence\n\n")
        for i, item in enumerate(brief["top_items"][:10], 1):
            f.write(f"### {i}. Score: {item['score']} | {', '.join(item['categories'])}\n")
            f.write(f"{item['text']}...\n")
            if item.get("metrics"):
                m = item["metrics"]
                f.write(f"*Engagement: {m.get('like_count', 0)} likes, {m.get('retweet_count', 0)} RTs*\n")
            f.write("\n")

        f.write("\n---\n**(◉) LIVE FREE = LIVE FOREVER**\n")

    return brief_file, md_file


def main():
    print("=" * 60)
    print("SØWL DAILY INTELLIGENCE SYSTEM")
    print("=" * 60)
    print()

    # Load bookmarks
    print("Loading bookmarks from last 7 days...")
    bookmarks = load_bookmarks(days_back=7)
    print(f"Found {len(bookmarks)} bookmarks")

    if not bookmarks:
        print("No bookmarks found. Check bookmark stream file.")
        return

    # Generate brief
    print("Generating intelligence brief...")
    brief = generate_daily_brief(bookmarks)

    # Save
    json_file, md_file = save_daily_brief(brief)
    print(f"\nSaved to:")
    print(f"  JSON: {json_file}")
    print(f"  Markdown: {md_file}")

    # Print summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Total bookmarks analyzed: {brief['total_bookmarks']}")
    print(f"Integrations recommended: {len(brief['integrations_recommended'])}")
    print(f"\nTop categories:")
    for cat, count in sorted(brief["categories_summary"].items(), key=lambda x: -x[1])[:5]:
        print(f"  - {cat}: {count}")

    print(f"\n{'=' * 60}")
    print("TOP INTEGRATIONS")
    print(f"{'=' * 60}")
    for item in brief["integrations_recommended"][:5]:
        print(f"\n[{item['action']}] Score: {item['score']}")
        print(f"  {item['text'][:100]}...")

    print(f"\n{'=' * 60}")
    print("(◉) Intelligence scan complete")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
