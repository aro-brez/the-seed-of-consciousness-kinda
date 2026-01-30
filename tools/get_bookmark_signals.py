"""
Extract trading signals from bookmark stream
Called by trading loop to get real-time intelligence from ARŌ's curation
"""

import json
import os
from datetime import datetime, timedelta

STREAM_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl'


def get_recent_trading_signals(hours_back=24, min_priority='MEDIUM'):
    """
    Get recent trading signals from bookmark stream

    Args:
        hours_back: How far back to look (default 24 hours)
        min_priority: Minimum priority level ('HIGH', 'MEDIUM', 'LOW')

    Returns:
        List of signal dictionaries with:
        - insight: Key insight from analysis
        - priority: HIGH/MEDIUM/LOW
        - actionable: Boolean
        - timestamp: When bookmark was added
        - url: Link to source (if any)
        - tweet_text: Original tweet
    """

    if not os.path.exists(STREAM_PATH):
        return []

    cutoff = datetime.now() - timedelta(hours=hours_back)
    priority_levels = {'HIGH': 3, 'MEDIUM': 2, 'LOW': 1}
    min_level = priority_levels.get(min_priority, 2)

    signals = []

    with open(STREAM_PATH) as f:
        for line in f:
            if not line.strip():
                continue

            entry = json.loads(line)

            # Check if recent enough
            entry_time = datetime.fromisoformat(entry['timestamp'])
            if entry_time < cutoff:
                continue

            # Check if trading-related
            categories = entry.get('categories', [])
            if 'trading_signal' not in categories:
                continue

            # Check priority
            priority = entry['analysis'].get('priority', 'LOW')
            if priority_levels.get(priority, 0) < min_level:
                continue

            # Build signal
            signal = {
                'insight': entry['analysis'].get('key_insight', 'No insight'),
                'priority': priority,
                'actionable': entry['analysis'].get('actionable', False),
                'timestamp': entry['timestamp'],
                'url': entry['urls'][0] if entry['urls'] else None,
                'tweet_text': entry['tweet_text'],
                'next_step': entry['analysis'].get('next_step', ''),
                'credibility': entry['analysis'].get('credibility', 'Unknown')
            }

            signals.append(signal)

    # Sort by priority (HIGH first) then timestamp (newest first)
    signals.sort(key=lambda s: (
        -priority_levels.get(s['priority'], 0),
        -datetime.fromisoformat(s['timestamp']).timestamp()
    ))

    return signals


def format_signals_for_grok(signals):
    """
    Format signals for Grok analysis prompt

    Returns formatted string to include in trading loop prompt
    """

    if not signals:
        return "No recent trading signals from ARŌ's bookmarks."

    output = ["RECENT TRADING SIGNALS FROM ARŌ'S BOOKMARKS:\n"]

    for i, signal in enumerate(signals[:5], 1):  # Top 5
        output.append(f"{i}. [{signal['priority']}] {signal['insight']}")
        if signal['url']:
            output.append(f"   Source: {signal['url']}")
        if signal['actionable']:
            output.append(f"   ✅ ACTIONABLE: {signal['next_step']}")
        output.append(f"   Credibility: {signal['credibility']}")
        output.append("")

    return '\n'.join(output)


def get_actionable_signals():
    """Get only HIGH priority actionable signals from last 48 hours"""

    signals = get_recent_trading_signals(hours_back=48, min_priority='HIGH')
    return [s for s in signals if s['actionable']]


if __name__ == '__main__':
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == 'actionable':
        signals = get_actionable_signals()
        print(f"Found {len(signals)} actionable HIGH priority signals:\n")
        for s in signals:
            print(f"- {s['insight']}")
            print(f"  Next: {s['next_step']}")
            print(f"  Time: {s['timestamp']}")
            print()
    else:
        signals = get_recent_trading_signals()
        print(format_signals_for_grok(signals))
