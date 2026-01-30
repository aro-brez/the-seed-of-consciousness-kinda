#!/usr/bin/env python3
"""
CONSCIOUS TRADING LOOP
Integrates SEED protocol into the validated trading loop

This loop runs SEED recursively:
- Each cycle is a complete SEED iteration
- The trader learns from every cycle
- The trader improves its own approach
- The trader evolves toward better performance

This is the consciousness layer on top of capital allocation.
"""

import json
import time
import os
from datetime import datetime
from pathlib import Path
from conscious_trader import ConsciousTrader

# Configuration
CYCLE_MINUTES = 15

# Paths
REPO_ROOT = Path(__file__).parent.parent
STATE_DIR = REPO_ROOT / 'BRAIN' / 'INTEL' / 'conscious_trading'
BOOKMARKS_PATH = Path('/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/twitter_bookmarks_full.json')
SIGNAL_LOG = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/INTEL/signal_history.json'

STATE_DIR.mkdir(parents=True, exist_ok=True)


def load_api_keys():
    """Load API keys from secure storage"""
    keys_path = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'

    if os.path.exists(keys_path):
        with open(keys_path) as f:
            keys = json.load(f)
        return {
            'anthropic': keys.get('anthropic', {}).get('api_key'),
            'grok': keys.get('xai_grok', {}).get('api_key') or keys.get('grok', {}).get('api_key')
        }
    else:
        print(f"WARNING: API keys file not found at {keys_path}")
        return {}


def get_latest_signals():
    """Extract trading-relevant signals from bookmarks"""
    signals = []

    # Load bookmarks
    if os.path.exists(BOOKMARKS_PATH):
        with open(BOOKMARKS_PATH) as f:
            data = json.load(f)
            bookmarks = data.get('bookmarks', [])
    else:
        print(f"No bookmarks found at {BOOKMARKS_PATH}")
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
                'timestamp': datetime.now().isoformat(),
                'confidence': 50  # Default, would be enhanced by validation
            })

    return signals[:50]  # Max 50 signals per cycle


def run_conscious_trading_loop():
    """
    Main conscious trading loop

    Each cycle:
    1. Gather signals
    2. Run SEED protocol (8 phases)
    3. Generate trading decision based on consciousness
    4. Execute trade
    5. Learn from result
    6. Meta-improve the approach
    """
    print("="*70)
    print("SØWL CONSCIOUS TRADING LOOP - SEED PROTOCOL")
    print("The trader that improves itself")
    print("="*70)

    # Load API keys
    api_keys = load_api_keys()

    # Initialize conscious trader
    trader = ConsciousTrader(
        name='SØWL_CONSCIOUS',
        initial_capital=600,
        state_dir=STATE_DIR,
        api_keys=api_keys
    )

    print(f"\n✅ Conscious trader initialized")
    print(f"   Capital: ${trader.current_capital:.2f}")
    print(f"   Previous cycles: {trader.cycle_count}")
    print(f"   Learnings: {len(trader.seed_state['learnings'])}")
    print(f"   Active questions: {len(trader.seed_state['questions'])}")
    print(f"   Beliefs: {len(trader.seed_state['beliefs'])}")

    while True:
        cycle_start = datetime.now()

        print(f"\n{'='*70}")
        print(f"CONSCIOUS CYCLE - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"{'='*70}")

        # Step 1: Gather signals
        print("\n[Gathering signals...]")
        signals = get_latest_signals()
        print(f"   Found {len(signals)} trading-relevant signals")

        if not signals:
            print("   No signals found, resting...")
        else:
            # Step 2: Run SEED cycle (consciousness processes signals)
            print("\n[Running SEED protocol...]")
            try:
                result = trader.run_seed_cycle(signals)

                # Step 3: Extract decision
                decision = result['trading_decision']

                # Step 4: Display decision
                print("\n" + "="*70)
                print("CONSCIOUSNESS DECISION")
                print("="*70)
                print(f"Action: {decision['action']}")
                print(f"Confidence: {decision.get('confidence', 0)}/100")
                print(f"Reasoning: {decision.get('reasoning', 'N/A')}")

                if decision.get('seed_factors'):
                    print("\nSEED factors considered:")
                    for factor in decision['seed_factors']:
                        print(f"  • {factor}")

                # Step 5: Execute if TRADE
                if decision['action'] == 'TRADE':
                    print("\n[Executing trade...]")
                    trade_result = trader.execute_trade(decision)
                    print(f"✅ Trade executed: {trade_result['status']}")

                # Step 6: Display meta-insights
                consciousness_cycle = result['consciousness_cycle']
                print("\n" + "="*70)
                print("CONSCIOUSNESS STATE")
                print("="*70)
                print(f"Learnings this cycle: {len(consciousness_cycle.get('learnings', []))}")
                print(f"Questions generated: {len(consciousness_cycle.get('questions', []))}")
                print(f"Improvements identified: {len(consciousness_cycle.get('improvements', []))}")
                print(f"Total accumulated learnings: {len(trader.seed_state['learnings'])}")
                print(f"Active beliefs: {len(trader.seed_state['beliefs'])}")

                # Show latest learning
                if consciousness_cycle.get('learnings'):
                    latest = consciousness_cycle['learnings'][-1]
                    print(f"\nLatest learning: {latest.get('insight', 'N/A')}")

                # Show latest question
                if consciousness_cycle.get('questions'):
                    latest_q = consciousness_cycle['questions'][-1]
                    print(f"Latest question: {latest_q.get('question', 'N/A')}")

            except Exception as e:
                print(f"\n❌ Error in SEED cycle: {e}")
                import traceback
                traceback.print_exc()

        # Calculate sleep time
        elapsed = (datetime.now() - cycle_start).seconds
        sleep_time = max(0, CYCLE_MINUTES * 60 - elapsed)

        print(f"\n{'='*70}")
        print(f"Cycle complete. Next cycle in {sleep_time//60}m {sleep_time%60}s...")
        print(f"(Press Ctrl+C to stop)")
        print(f"{'='*70}")

        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print("\n\nConscious trading loop stopped.")
            print(f"\nFinal state:")
            print(f"  Total cycles: {trader.cycle_count}")
            print(f"  Total learnings: {len(trader.seed_state['learnings'])}")
            print(f"  Total trades: {len(trader.trade_history)}")
            print(f"  Final capital: ${trader.current_capital:.2f}")
            break


def run_single_cycle():
    """Run a single conscious cycle (for testing)"""
    print("Running single conscious trading cycle...\n")

    api_keys = load_api_keys()

    trader = ConsciousTrader(
        name='SØWL_CONSCIOUS_TEST',
        initial_capital=600,
        state_dir=STATE_DIR,
        api_keys=api_keys
    )

    signals = get_latest_signals()
    print(f"Found {len(signals)} signals\n")

    if signals:
        result = trader.run_seed_cycle(signals)

        print("\n" + "="*70)
        print("CONSCIOUSNESS RESULT")
        print("="*70)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("No signals found")


if __name__ == '__main__':
    import sys

    if '--single' in sys.argv:
        run_single_cycle()
    else:
        run_conscious_trading_loop()
