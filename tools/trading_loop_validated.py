#!/usr/bin/env python3
"""
VALIDATED 15-MINUTE TRADING LOOP
Integrates market data validation into the trading pipeline

Flow:
1. Pull Twitter signals (bookmarks)
2. Validate with real-time market data
3. Pass only HIGH-CONFIDENCE signals to Grok
4. Generate trade recommendations
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
import requests

# Import our new validation layer
from signal_validator import SignalValidator
from market_data_feeds import MarketDataFeeds

# Configuration
GROK_API_KEY = None  # Loaded from api_keys.json
CYCLE_MINUTES = 15

# Dynamic path detection
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / 'BRAIN' / 'INTEL' / 'trades'
BOOKMARKS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks.json'
FULL_CONTEXT_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'twitter_bookmarks_full_context.json'
SIGNAL_LOG = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/INTEL/signal_history.json'
VALIDATED_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'validated_trades.json'

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

    for bookmark in bookmarks[-100:]:  # Last 100 bookmarks
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

    return signals[:50]  # Max 50 signals per cycle


def analyze_with_grok(validated_signals):
    """Send VALIDATED signals to Grok for trading analysis"""
    if not GROK_API_KEY:
        print("WARNING: No Grok API key found, using Claude for analysis")
        return analyze_with_claude(validated_signals)

    # Format validated signals with market data
    signal_text = "\n\n---\n\n".join([
        f"""SIGNAL {i+1} [VALIDATED - Confidence: {s['confidence']}/100]
Token: {s.get('best_token', 'Unknown')}
Market Data:
  - Price: ${s.get('market_data', {}).get('price_data', {}).get('price', 0):,.2f}
  - 24h Change: {s.get('market_data', {}).get('momentum', {}).get('change_24h', 0):.1f}%
  - Volume: ${s.get('market_data', {}).get('price_data', {}).get('volume_24h', 0):,.0f}
  - Trend: {s.get('market_data', {}).get('momentum', {}).get('trend', 'unknown')}

Validation Reasoning:
{s.get('reasoning', 'N/A')}

Original Signal:
{s.get('original_signal', {}).get('text', '')}"""
        for i, s in enumerate(validated_signals)
    ])

    prompt = f"""You are a quantitative trading analyst with VALIDATED MARKET DATA.

These signals have been cross-referenced with real-time price/volume data and passed validation.

Analyze and provide:

1. **IMMEDIATE OPPORTUNITIES** (next 15 minutes):
   - Which validated signals are actionable NOW?
   - Specific entry points and position sizes
   - Risk/reward for each

2. **MARKET CONFIRMATION**:
   - Does price action support these signals?
   - Are volume patterns confirming the narrative?
   - Any divergences between social signal and market reality?

3. **EXECUTION PRIORITY**:
   - Rank signals from strongest to weakest
   - Which should be executed first?
   - Which need more confirmation?

4. **RECOMMENDED TRADES**:
   - EXECUTE NOW: List specific trades with parameters
   - WAIT: Signals that need 1 more cycle
   - PASS: Validated but not strong enough

VALIDATED SIGNALS:
{signal_text}

Be specific. These signals have market confirmation. Give me executable trades."""

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
                    {'role': 'system', 'content': 'You are Grok 4.1 Fast with reasoning, analyzing PRE-VALIDATED trading signals with confirmed market data. Be aggressive on high-confidence setups.'},
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
            return analyze_with_claude(validated_signals)

    except Exception as e:
        print(f"Grok API error: {e}")
        return analyze_with_claude(validated_signals)


def analyze_with_claude(validated_signals):
    """Fallback: Use Claude for analysis"""
    import anthropic

    client = anthropic.Anthropic()

    signal_text = "\n\n---\n\n".join([
        f"SIGNAL {i+1} [Confidence: {s['confidence']}/100]\n{s.get('reasoning', '')}\n{s.get('original_signal', {}).get('text', '')}"
        for i, s in enumerate(validated_signals)
    ])

    response = client.messages.create(
        model="claude-opus-4-5-20251101",
        max_tokens=2000,
        messages=[{
            'role': 'user',
            'content': f"""Analyze these VALIDATED trading signals with market confirmation:

{signal_text}

Provide:
1. IMMEDIATE OPPORTUNITIES
2. MARKET CONFIRMATION
3. EXECUTION PRIORITY
4. RECOMMENDED TRADES (EXECUTE/WAIT/PASS)

Be specific and actionable."""
        }]
    )

    return response.content[0].text


def save_cycle_results(cycle_num, raw_signals, validated_signals, analysis):
    """Save results for this trading cycle"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')

    result = {
        'cycle': cycle_num,
        'timestamp': datetime.now().isoformat(),
        'raw_signal_count': len(raw_signals),
        'validated_signal_count': len(validated_signals),
        'validation_pass_rate': f"{len(validated_signals)/max(len(raw_signals), 1)*100:.1f}%",
        'validated_signals': validated_signals,
        'analysis': analysis
    }

    # Save individual cycle
    cycle_file = f"{OUTPUT_DIR}/validated_cycle_{timestamp}.json"
    with open(cycle_file, 'w') as f:
        json.dump(result, f, indent=2)

    # Append to validated trades log
    history = []
    if os.path.exists(VALIDATED_LOG):
        with open(VALIDATED_LOG) as f:
            history = json.load(f)

    history.append(result)
    history = history[-100:]  # Keep last 100 cycles

    with open(VALIDATED_LOG, 'w') as f:
        json.dump(history, f, indent=2)

    return cycle_file


def run_validated_trading_loop():
    """Main validated trading loop - runs every 15 minutes"""
    print("="*60)
    print("SØWL VALIDATED TRADING LOOP - 15 MINUTE CYCLES")
    print("With Real-Time Market Data Validation")
    print("="*60)

    load_api_keys()
    validator = SignalValidator()
    cycle = 0

    while True:
        cycle += 1
        cycle_start = datetime.now()

        print(f"\n{'='*60}")
        print(f"CYCLE {cycle} - {cycle_start.strftime('%H:%M:%S')}")
        print("="*60)

        # Step 1: Gather raw signals
        print("\n[1/4] Gathering signals from bookmarks...")
        raw_signals = get_latest_signals()
        print(f"      Found {len(raw_signals)} trading-relevant signals")

        if not raw_signals:
            print("      No signals found, waiting for next cycle...")
        else:
            # Step 2: VALIDATE with market data
            print("\n[2/4] Validating with real-time market data...")
            validated_signals = validator.batch_validate(raw_signals)
            print(f"      ✅ {len(validated_signals)} signals passed validation")
            print(f"      ❌ {len(raw_signals) - len(validated_signals)} signals rejected")

            if validated_signals:
                # Show top validated signals
                print("\n      Top validated signals:")
                for i, sig in enumerate(validated_signals[:3], 1):
                    print(f"        {i}. {sig['best_token']} - Confidence: {sig['confidence']}/100")

                # Step 3: Analyze with Grok
                print("\n[3/4] Analyzing validated signals with Grok 4.20...")
                analysis = analyze_with_grok(validated_signals)

                # Step 4: Save and display
                print("\n[4/4] Saving results...")
                cycle_file = save_cycle_results(cycle, raw_signals, validated_signals, analysis)

                print("\n" + "="*60)
                print("GROK ANALYSIS:")
                print("="*60)
                print(analysis)
                print("\n" + "="*60)
                print(f"Saved to: {cycle_file}")
            else:
                print("\n      No signals passed validation. Waiting for next cycle...")

        # Calculate sleep time
        elapsed = (datetime.now() - cycle_start).seconds
        sleep_time = max(0, CYCLE_MINUTES * 60 - elapsed)

        print(f"\nNext cycle in {sleep_time//60}m {sleep_time%60}s...")
        print("(Press Ctrl+C to stop)")

        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n\nValidated trading loop stopped.")
            break


def run_single_cycle():
    """Run a single analysis cycle (for testing)"""
    print("Running single validated analysis cycle...")
    load_api_keys()
    validator = SignalValidator()

    raw_signals = get_latest_signals()
    print(f"Found {len(raw_signals)} raw signals")

    if raw_signals:
        validated_signals = validator.batch_validate(raw_signals)
        print(f"✅ {len(validated_signals)} signals passed validation\n")

        if validated_signals:
            print("Top 5 validated signals:")
            for i, sig in enumerate(validated_signals[:5], 1):
                print(f"\n{i}. {sig['best_token']} - Confidence: {sig['confidence']}/100")
                print(f"   Recommendation: {sig['recommendation']}")
                print(f"   Reasoning: {sig['reasoning'][:100]}...")

            print("\nAnalyzing with Grok...")
            analysis = analyze_with_grok(validated_signals)
            print("\n" + "="*60)
            print("GROK ANALYSIS:")
            print("="*60)
            print(analysis)

            save_cycle_results(1, raw_signals, validated_signals, analysis)
        else:
            print("No signals passed validation")
    else:
        print("No signals found")


if __name__ == '__main__':
    import sys

    if '--single' in sys.argv:
        run_single_cycle()
    else:
        run_validated_trading_loop()
