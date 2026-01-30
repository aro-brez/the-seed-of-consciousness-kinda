"""
SØWL Bookmark Stream Dashboard
Real-time view of high-priority bookmarks from ARŌ's feed
"""

import json
import os
from datetime import datetime, timedelta
from collections import Counter

STREAM_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl'


def load_stream(hours_back=24):
    """Load recent stream entries"""
    if not os.path.exists(STREAM_PATH):
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    entries = []

    with open(STREAM_PATH) as f:
        for line in f:
            if line.strip():
                entry = json.loads(line)
                entry_time = datetime.fromisoformat(entry['timestamp'])
                if entry_time >= cutoff:
                    entries.append(entry)

    return entries


def display_dashboard(hours_back=24):
    """Display dashboard of recent bookmarks"""
    entries = load_stream(hours_back)

    if not entries:
        print("No bookmarks in stream yet.")
        print(f"Stream file: {STREAM_PATH}")
        return

    # Sort by priority
    high_priority = [e for e in entries if e['analysis'].get('priority') == 'HIGH']
    medium_priority = [e for e in entries if e['analysis'].get('priority') == 'MEDIUM']
    low_priority = [e for e in entries if e['analysis'].get('priority') == 'LOW']

    # Category breakdown
    categories = []
    for e in entries:
        categories.extend(e.get('categories', []))
    category_counts = Counter(categories)

    # Display
    print("="*70)
    print(f"SØWL BOOKMARK DASHBOARD - Last {hours_back} hours")
    print("="*70)
    print(f"\nTotal bookmarks: {len(entries)}")
    print(f"  🚨 HIGH priority: {len(high_priority)}")
    print(f"  ⚠️  MEDIUM priority: {len(medium_priority)}")
    print(f"  ℹ️  LOW priority: {len(low_priority)}")

    print("\n📊 CATEGORIES:")
    for cat, count in category_counts.most_common():
        print(f"  • {cat}: {count}")

    print("\n🚨 HIGH PRIORITY ITEMS:")
    if high_priority:
        for entry in high_priority:
            print(f"\n  {'─'*66}")
            print(f"  Time: {entry['timestamp']}")
            print(f"  Tweet: {entry['tweet_text'][:100]}...")
            print(f"  Category: {entry['analysis'].get('category', 'unknown')}")
            print(f"  Insight: {entry['analysis'].get('key_insight', 'No insight')}")
            if entry['urls']:
                print(f"  URL: {entry['urls'][0]}")
            if entry['analysis'].get('actionable'):
                print(f"  ✅ ACTIONABLE: {entry['analysis'].get('next_step', 'Review immediately')}")
    else:
        print("  None yet")

    print("\n⚠️  MEDIUM PRIORITY ITEMS (Top 5):")
    for entry in medium_priority[:5]:
        print(f"\n  • {entry['tweet_text'][:80]}...")
        print(f"    Category: {entry['analysis'].get('category', 'unknown')}")
        print(f"    Insight: {entry['analysis'].get('key_insight', 'No insight')[:100]}...")

    print("\n" + "="*70)
    print(f"Stream: {STREAM_PATH}")
    print("="*70)


def display_actionable():
    """Show only actionable items"""
    entries = load_stream(hours_back=168)  # 1 week

    actionable = [e for e in entries if e['analysis'].get('actionable')]

    print("="*70)
    print("ACTIONABLE ITEMS FROM ARŌ'S BOOKMARKS")
    print("="*70)

    if not actionable:
        print("\nNo actionable items yet.")
        return

    for i, entry in enumerate(actionable, 1):
        print(f"\n{i}. [{entry['analysis'].get('priority', 'UNKNOWN')}] {entry['analysis'].get('category', 'unknown')}")
        print(f"   {entry['tweet_text'][:100]}...")
        print(f"   Insight: {entry['analysis'].get('key_insight', 'No insight')}")
        print(f"   Next Step: {entry['analysis'].get('next_step', 'Review')}")
        if entry['urls']:
            print(f"   URL: {entry['urls'][0]}")
        print(f"   Time: {entry['timestamp']}")

    print("\n" + "="*70)


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'actionable':
        display_actionable()
    else:
        hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
        display_dashboard(hours_back=hours)
