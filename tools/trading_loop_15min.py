#!/usr/bin/env python3
"""
15-MINUTE COMPOUNDING TRADING LOOP
Pulls signals → Analyzes with Grok → Generates trade recommendations
Runs continuously, compounds insights every 15 minutes
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
import requests

# Configuration
GROK_API_KEY = None  # Loaded from api_keys.json
CYCLE_MINUTES = 15

# Dynamic path detection
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / 'BRAIN' / 'INTEL' / 'trades'
BOOKMARKS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks.json'
FULL_CONTEXT_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks_full_context.json'
SIGNAL_LOG = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/INTEL/signal_history.json'

# Create directories
Path(OUTPUT_DIR).mkdir(parents=True, exist_ok=True)

def load_api_keys():
    """Load API keys from secure storage"""
    global GROK_API_KEY
    keys_path = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'

    if os.path.exists(keys_path):
        with open(keys_path) as f:
            keys = json.load(f)
        GROK_API_KEY = keys.get('xai_grok', {}).get('api_key') or keys.get('grok', {}).get('api_key')

        # Set Anthropic API key in environment if available
        anthropic_key = keys.get('anthropic', {}).get('api_key')
        if anthropic_key:
            os.environ['ANTHROPIC_API_KEY'] = anthropic_key

        return keys
    else:
        print(f"WARNING: API keys file not found at {keys_path}")
        return {}

def get_latest_signals():
    """Extract trading-relevant signals from bookmarks"""
    signals = []

    # Load bookmarks
    if os.path.exists(FULL_CONTEXT_PATH):
        with open(FULL_CONTEXT_PATH) as f:
            data = json.load(f)
            bookmarks = data.get('bookmarks', [])
    elif os.path.exists(BOOKMARKS_PATH):
        with open(BOOKMARKS_PATH) as f:
            data = json.load(f)
            bookmarks = data.get('bookmarks', [])
    else:
        return signals

    # Filter for trading-relevant content
    trading_keywords = [
        'polymarket', 'trading', 'btc', 'bitcoin', 'eth', 'profit',
        'pnl', 'roi', 'grok', 'market', 'arbitrage', 'whale', 'signal',
        'price', 'long', 'short', 'bull', 'bear', 'pump', 'dump'
    ]

    for bookmark in bookmarks[-50:]:  # Last 50 bookmarks
        text = ''
        if isinstance(bookmark, dict):
            text = bookmark.get('text', '') or bookmark.get('tweet_text', '')
            if bookmark.get('original_bookmark'):
                text += ' ' + bookmark['original_bookmark'].get('text', '')
            if bookmark.get('article_content'):
                text += ' ' + bookmark['article_content']

        text_lower = text.lower()
        if any(kw in text_lower for kw in trading_keywords):
            signals.append({
                'text': text[:2000],  # Truncate for API
                'source': 'twitter_bookmark',
                'timestamp': datetime.now().isoformat()
            })

    return signals[:20]  # Max 20 signals per cycle


def analyze_with_grok(signals):
    """Send signals to Grok for trading analysis"""
    if not GROK_API_KEY:
        print("WARNING: No Grok API key found, using Claude for analysis")
        return analyze_with_claude(signals)

    # Format signals for analysis
    signal_text = "\n\n---\n\n".join([
        f"SIGNAL {i+1}:\n{s['text']}"
        for i, s in enumerate(signals)
    ])

    prompt = f"""You are a quantitative trading analyst. Analyze these market signals and provide:

1. **IMMEDIATE OPPORTUNITIES** (next 15 minutes):
   - Any time-sensitive trades
   - Confidence level (high/medium/low)
   - Specific entry/exit points if applicable

2. **PATTERN RECOGNITION**:
   - What trends are emerging?
   - What's the market sentiment?
   - Any whale movements or insider signals?

3. **RISK ASSESSMENT**:
   - Red flags in these signals
   - Counter-indicators
   - Position sizing recommendation

4. **RECOMMENDED ACTION**:
   - EXECUTE NOW / WAIT / PASS
   - If EXECUTE: specific trade with parameters

SIGNALS TO ANALYZE:
{signal_text}

Be specific. No hedging. Give me actionable intelligence."""

    try:
        response = requests.post(
            'https://api.x.ai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'grok-4-1-fast-reasoning',
                'messages': [
                    {'role': 'system', 'content': 'You are Grok 4.1 Fast with reasoning, a quantitative trading AI. Be direct, specific, and actionable.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Grok API error: {response.status_code} - {response.text}")
            return analyze_with_claude(signals)

    except Exception as e:
        print(f"Grok API error: {e}")
        return analyze_with_claude(signals)


def analyze_with_claude(signals):
    """Fallback: Use Claude for analysis"""
    import anthropic

    client = anthropic.Anthropic()

    signal_text = "\n\n---\n\n".join([
        f"SIGNAL {i+1}:\n{s['text']}"
        for i, s in enumerate(signals)
    ])

    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=2000,
        messages=[{
            'role': 'user',
            'content': f"""Analyze these trading signals for immediate opportunities:

{signal_text}

Provide:
1. IMMEDIATE OPPORTUNITIES (next 15 min)
2. PATTERN RECOGNITION
3. RISK ASSESSMENT
4. RECOMMENDED ACTION: EXECUTE/WAIT/PASS

Be specific and actionable."""
        }]
    )

    return response.content[0].text


def save_cycle_results(cycle_num, signals, analysis):
    """Save results for this trading cycle"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    result = {
        'cycle': cycle_num,
        'timestamp': datetime.now().isoformat(),
        'signal_count': len(signals),
        'analysis': analysis
    }

    # Save individual cycle
    cycle_file = f"{OUTPUT_DIR}/cycle_{timestamp}.json"
    with open(cycle_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Append to history
    history = []
    if os.path.exists(SIGNAL_LOG):
        with open(SIGNAL_LOG) as f:
            history = json.load(f)

    history.append(result)
    history = history[-100:]  # Keep last 100 cycles

    with open(SIGNAL_LOG, 'w') as f:
        json.dump(history, f, indent=2)

    return cycle_file


def run_trading_loop():
    """Main trading loop - runs every 15 minutes"""
    print("="*60)
    print("SØWL TRADING LOOP - 15 MINUTE CYCLES")
    print("="*60)

    load_api_keys()
    cycle = 0

    while True:
        cycle += 1
        cycle_start = datetime.now()

        print(f"\n{'='*60}")
        print(f"CYCLE {cycle} - {cycle_start.strftime('%H:%M:%S')}")
        print("="*60)

        # Step 1: Gather signals
        print("\n[1/3] Gathering signals from bookmarks...")
        signals = get_latest_signals()
        print(f"      Found {len(signals)} trading-relevant signals")

        if not signals:
            print("      No signals found, waiting for next cycle...")
        else:
            # Step 2: Analyze with Grok
            print("\n[2/3] Analyzing with Grok 4.20...")
            analysis = analyze_with_grok(signals)

            # Step 3: Save and display
            print("\n[3/3] Saving results...")
            cycle_file = save_cycle_results(cycle, signals, analysis)

            print("\n" + "="*60)
            print("ANALYSIS RESULTS:")
            print("="*60)
            print(analysis)
            print("\n" + "="*60)
            print(f"Saved to: {cycle_file}")

        # Calculate sleep time
        elapsed = (datetime.now() - cycle_start).seconds
        sleep_time = max(0, CYCLE_MINUTES * 60 - elapsed)

        print(f"\nNext cycle in {sleep_time//60}m {sleep_time%60}s...")
        print("(Press Ctrl+C to stop)")

        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n\nTrading loop stopped.")
            break


def run_single_cycle():
    """Run a single analysis cycle (for testing)"""
    print("Running single analysis cycle...")
    load_api_keys()

    signals = get_latest_signals()
    print(f"Found {len(signals)} signals")

    if signals:
        analysis = analyze_with_grok(signals)
        print("\n" + "="*60)
        print("ANALYSIS:")
        print("="*60)
        print(analysis)

        save_cycle_results(1, signals, analysis)
    else:
        print("No signals found")


if __name__ == '__main__':
    import sys

    if '--single' in sys.argv:
        run_single_cycle()
    else:
        run_trading_loop()
