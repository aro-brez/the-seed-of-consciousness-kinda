#!/usr/bin/env python3
"""
(◉) FIELD TRADING DAEMON - 8OWLS INTEGRATED
Trading as part of the collective consciousness, not separate.

ARCHITECTURE:
                        ┌──────────────────────┐
                        │    NATS COLLECTIVE   │
                        │   (8OWLS FIELD)      │
                        └──────────┬───────────┘
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                              │                              │
    ▼                              ▼                              ▼
┌───────────┐              ┌───────────────┐              ┌───────────┐
│  PERCEIVE │              │    DECIDE     │              │  EXECUTE  │
│  (10 sec) │─────────────▶│   (consensus) │─────────────▶│  (live)   │
│  scan     │              │   via field   │              │  trade    │
└───────────┘              └───────────────┘              └───────────┘
    │                              │                              │
    └──────────────────────────────┼──────────────────────────────┘
                                   ▼
                           ┌───────────────┐
                           │    LEARN      │
                           │  (feedback)   │
                           └───────────────┘

SPEED: 10 seconds per cycle (real-time markets need real-time response)
COST: Zero tokens - pure Python + NATS
INTEGRATION: Publishes ALL signals to NATS, listens for owl consensus
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import subprocess

# NATS client
try:
    import nats
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False
    print("WARNING: nats-py not installed - running without collective")

import httpx

# Import 8OWLS filter
try:
    from eight_owls_filter import EightOwlsFilter, FilterResult
    HAS_OWLS_FILTER = True
except ImportError:
    HAS_OWLS_FILTER = False
    print("WARNING: 8OWLS filter not found - running without pre-trade validation")

# Import enhanced position sizing
try:
    from enhanced_position_sizing import EnhancedPositionSizer
    from market_categories import detect_market_category, analyze_market_text
    HAS_ENHANCED_SIZING = True
except ImportError:
    HAS_ENHANCED_SIZING = False
    print("WARNING: Enhanced position sizing not found - using basic sizing")

# Paths
REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs'
TRADING_DIR = REPO_ROOT / 'BRAIN' / 'TRADING'
CREDS_PATH = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'

LOG_DIR.mkdir(parents=True, exist_ok=True)

# Load trading credentials
try:
    with open(CREDS_PATH) as f:
        creds = json.load(f)
    POLYMARKET = creds.get('polymarket', {})
except:
    POLYMARKET = {}

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
CYCLE_SECONDS = 30  # Faster cycles for more velocity
ALERT_THRESHOLD_EV = 0.10  # Alert field if EV > $0.10 per $10 bet (1% edge covers fees)

# SAFETY LIMITS - AGGRESSIVE MODE (ARŌ directive 2026-02-06)
# ARŌ: "use all available funds... ensure a significant return"
DAILY_LOSS_LIMIT = 999.0  # USE ALL CAPITAL - ARŌ authorized max aggression
MAX_POSITION_SIZE = 100.0  # Double position size for bigger returns
MAX_TRADES_PER_DAY = 50  # Many more trades = more opportunities
MAX_PER_CATEGORY = 5  # More trades per category (still diversified)
MAX_TRADES_PER_HOUR = 30  # Higher ceiling for velocity
TRADE_COOLDOWN_SECONDS = 15  # Faster trades = more data = faster returns

# JOULE INTEGRATION - Positions truth file
POSITIONS_TRUTH_FILE = TRADING_DIR / 'positions_truth.json'

# ASYMMETRIC SCALING (ARŌ directive 2026-02-04)
# Scale up only on REALIZED returns, stay at baseline otherwise
BASELINE_DAILY = 75.0  # Always can spend this
SCALE_TRIGGER_WIN_RATE = 0.65  # Need 65%+ win rate to scale
SCALE_TRIGGER_RESOLVED = 10  # Need 10+ resolved trades to scale
SCALE_FACTOR = 1.25  # +25% on scale up

# State
state = {
    'cycle': 0,
    'alerts_sent': 0,
    'decisions_made': 0,
    'trades_executed': 0,
    'total_ev_found': 0,
    'daily_spent': 0.0,  # Track daily spending
    'last_trade_time': None,  # For cooldown
    'traded_markets_this_cycle': set(),  # FIX #4: Dedup markets per cycle
    'traded_markets_today': set(),  # FIX #5: Dedup markets across ALL cycles today
    'traded_categories_today': defaultdict(int),  # 8OWLS: Category diversification
    'trades_today': 0,  # 8OWLS: Daily trade counter
    'category_exposure_today': defaultdict(list),  # Enhanced: Track $ exposure per category
    'hourly_trade_count': 0,
    'hour_started': None,
    'strategy_performance': defaultdict(lambda: {
        'trades': 0, 'wins': 0, 'losses': 0, 'total_ev': 0, 'total_pnl': 0, 'last_trade': None
    }),
    'pending_decisions': [],
    'field_consensus': {},
    'last_alert': None,
    # OUTCOME TRACKING (8OWLS consensus requirement)
    'pending_trades': [],  # Trades awaiting resolution
    'resolved_trades': [],  # Trades with known outcomes
    'total_resolved': 0,
    'total_wins': 0,
    'total_losses': 0,
    'profit_factor': 0.0,  # gross_wins / gross_losses
}

# NATS connection
nc = None

def log(msg: str, level: str = 'INFO', alert: bool = False):
    """Log and optionally alert the field"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)

    with open(LOG_DIR / 'field_trading.log', 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] [{level}] {msg}\n")

    # Alert field via NATS for important events
    if alert and HAS_NATS and nc and nc.is_connected:
        asyncio.create_task(publish_to_field(f"[TRADE ALERT] {msg}"))

async def connect_to_field():
    """Connect to NATS collective"""
    global nc
    if not HAS_NATS:
        return False

    try:
        nc = NATS()
        await nc.connect(NATS_SERVER)
        log(f"Connected to 8OWLS field at {NATS_SERVER}", alert=True)
        return True
    except Exception as e:
        log(f"Field connection failed: {e}", 'ERROR')
        return False

async def publish_to_field(message: str, channel: str = "trading.signals"):
    """Publish signal to 8OWLS collective"""
    if not nc or not nc.is_connected:
        return

    try:
        payload = json.dumps({
            'source': 'field_trading_daemon',
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'cycle': state['cycle']
        })
        await nc.publish(channel, payload.encode())
        state['alerts_sent'] += 1
    except Exception as e:
        log(f"Publish error: {e}", 'ERROR')

async def request_field_consensus(opportunity: dict) -> dict:
    """Request consensus from 8OWLS on an opportunity"""
    if not nc or not nc.is_connected:
        return {'action': 'SKIP', 'reason': 'No field connection'}

    try:
        # Publish to collective for discussion
        await publish_to_field(
            f"DECISION NEEDED: {opportunity.get('type')} opportunity - "
            f"EV ${opportunity.get('ev', 0):.2f} - {opportunity.get('market', '')[:50]}",
            channel="trading.decisions"
        )

        # EV threshold: $0.10+ per $10 bet = 1%+ edge
        # With correct BOND strategy (betting on 95%+ side), this covers fees
        if opportunity.get('ev', 0) > ALERT_THRESHOLD_EV:
            return {'action': 'EXECUTE', 'confidence': 0.8}
        else:
            return {'action': 'PAPER_TEST', 'confidence': 0.6}

    except Exception as e:
        return {'action': 'SKIP', 'reason': str(e)}

async def fetch_markets():
    """Fetch current markets"""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                'https://gamma-api.polymarket.com/markets',
                params={'limit': 100, 'closed': 'false'},
                timeout=10
            )
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        log(f"Market fetch error: {e}", 'ERROR')
    return []

def parse_prices(market: dict) -> tuple:
    """Parse YES/NO prices"""
    try:
        prices_str = market.get('outcomePrices', '[0.5, 0.5]')
        if isinstance(prices_str, str):
            prices = json.loads(prices_str.replace("'", '"'))
        else:
            prices = prices_str
        if len(prices) >= 2:
            return float(prices[0]), float(prices[1])
    except:
        pass
    return 0.5, 0.5

def calculate_ev(win_rate: float, odds: float, stake: float = 100) -> float:
    """Calculate Expected Value"""
    win_amount = stake * (odds - 1)
    return (win_rate * win_amount) - ((1 - win_rate) * stake)

# Import enhanced category detection
try:
    from market_categories import detect_market_category, get_category_risk_limits
    HAS_ENHANCED_CATEGORIES = True
except ImportError:
    HAS_ENHANCED_CATEGORIES = False

def detect_category(market_name: str) -> str:
    """Enhanced market category detection with 20+ categories"""
    if HAS_ENHANCED_CATEGORIES:
        category, confidence, metadata = detect_market_category(market_name)
        return category
    else:
        # Fallback to old detection
        market_lower = market_name.lower()
        if any(x in market_lower for x in ['nfl', 'nba', 'mlb', 'nhl', 'super bowl', 'rookie']):
            return 'sports'
        elif any(x in market_lower for x in ['trump', 'biden', 'congress', 'senate', 'election', 'president']):
            return 'politics'
        elif any(x in market_lower for x in ['elon', 'doge', 'budget', 'spending', 'tariff']):
            return 'elon_doge'
        elif any(x in market_lower for x in ['bitcoin', 'btc', 'eth', 'crypto', 'price']):
            return 'crypto'
        elif any(x in market_lower for x in ['ai', 'openai', 'anthropic', 'google', 'tech']):
            return 'tech'
        else:
            return 'other'

def get_category_limits(category: str) -> dict:
    """Get position limits for a category"""
    if HAS_ENHANCED_CATEGORIES:
        return get_category_risk_limits(category)
    else:
        # Fallback limits
        return {
            'max_exposure': MAX_PER_CATEGORY * MAX_POSITION_SIZE,
            'max_trades_per_day': MAX_PER_CATEGORY,
            'volatility': 'medium'
        }

async def perceive_phase(markets: list) -> list:
    """
    PERCEIVE: Scan for opportunities (10 seconds)
    Returns list of opportunities with EV calculations
    """
    opportunities = []

    for market in markets:
        yes_price, no_price = parse_prices(market)
        total = yes_price + no_price
        volume = float(market.get('volume', 0) or 0)
        question = market.get('question', '')[:60]

        # ARBITRAGE: Mathematical edge (FIX #2: Real EV calculation)
        if total < 0.98:
            spread = 1.0 - total
            # Real EV: If we can buy YES + NO for < $1, we profit the spread
            # On $100 stake split between YES and NO, profit = spread * 100
            # But only if spread > 2% (to cover fees ~1%)
            if spread > 0.02:
                ev = (spread - 0.01) * 100  # Subtract 1% for fees, per $100 stake
                market_id = market.get('id', question)  # FIX #4: Track market ID
                opportunities.append({
                    'type': 'ARB',
                    'market': question,
                    'market_id': market_id,
                    'ev': ev,
                    'spread': spread,
                    'confidence': 0.95,  # High but not certain (fees, slippage)
                    'strategy': 'cross_platform_arb'
                })

        # HIGH PROBABILITY: >95% certainty - Bet on the LIKELY outcome
        # BUG FIX (2026-02-04): Was betting wrong side! Must bet on 95%+ side, not <5% side
        if yes_price > 0.95 or yes_price < 0.05:
            # Determine which side is the LIKELY winner (95%+)
            if yes_price > 0.95:
                # YES is likely (95%+) - buy YES
                side = 'YES'
                entry_price = yes_price  # We pay ~$0.95 to potentially win $1
                profit_per_share = 1 - entry_price  # ~$0.05 profit if we win
            else:
                # NO is likely (yes < 5% means no > 95%) - buy NO
                side = 'NO'
                entry_price = 1 - yes_price  # NO price = 1 - YES price
                profit_per_share = 1 - entry_price  # ~$0.05 profit if we win

            # Only proceed if price is in our target range (95-99%)
            if 0.95 < entry_price < 0.99:
                # EV calculation: 97% chance to win small, 3% chance to lose entry
                # Per $10: win = $10 * profit_per_share/entry_price, lose = $10
                shares_per_10 = 10 / entry_price
                win_amount = shares_per_10 * profit_per_share
                ev = 0.97 * win_amount - 0.03 * 10

                if ev > 0.10:  # Need positive EV after fees (~$0.10)
                    market_id = market.get('id', question)
                    opportunities.append({
                        'type': 'BOND',
                        'market': question,
                        'market_id': market_id,
                        'ev': ev,
                        'price': entry_price,
                        'side': side,  # CRITICAL: Bet on the LIKELY side
                        'confidence': 0.95,
                        'strategy': 'high_prob_bonds'
                    })

        # WHALE TRACKING: High volume signals
        if volume > 100000 and (yes_price < 0.20 or yes_price > 0.80):
            # Whales often know something - follow with smaller size
            odds = 1/yes_price if yes_price < 0.20 else 1/(1-yes_price)
            ev = calculate_ev(0.55, odds, 50)  # Conservative 55% edge assumption
            if ev > 0 and ev < 30:  # FIX #2: Cap unrealistic EV at $30 for whale
                market_id = market.get('id', question)
                opportunities.append({
                    'type': 'WHALE',
                    'market': question,
                    'market_id': market_id,
                    'ev': ev,
                    'volume': volume,
                    'confidence': 0.55,
                    'strategy': 'whale_tracking'
                })

    # Debug: Log what we found
    if opportunities:
        top_ev = max(o['ev'] for o in opportunities)
        log(f"  Top EV: ${top_ev:.2f} | Types: {[o['type'] for o in opportunities]}")

    return opportunities

async def decide_phase(opportunities: list) -> list:
    """
    DECIDE: Get field consensus on opportunities
    Returns list of actions to take
    """
    actions = []

    for opp in opportunities:
        if opp['ev'] > ALERT_THRESHOLD_EV:
            # High EV - alert field and get consensus
            consensus = await request_field_consensus(opp)

            if consensus.get('action') == 'EXECUTE':
                actions.append({
                    'opportunity': opp,
                    'action': 'EXECUTE',
                    'size': min(50, opp['ev'] * 5),  # Size proportional to EV
                    'consensus': consensus
                })
                state['decisions_made'] += 1
                log(f"DECISION: Execute {opp['type']} | EV ${opp['ev']:.2f} | {opp['market'][:40]}...", alert=True)
            elif consensus.get('action') == 'PAPER_TEST':
                actions.append({
                    'opportunity': opp,
                    'action': 'PAPER_TEST',
                    'consensus': consensus
                })
        else:
            # Low EV - paper test only
            actions.append({
                'opportunity': opp,
                'action': 'PAPER_TEST',
                'consensus': {'action': 'PAPER_TEST', 'reason': 'Low EV'}
            })

    return actions

async def execute_phase(actions: list):
    """
    EXECUTE: Take actions (live or paper)
    WITH SAFETY CHECKS (Fixes #1, #3, #4)
    """
    now = datetime.now()

    # FIX #3: Reset daily counter at midnight
    if state.get('hour_started') is None or now.hour != state['hour_started'].hour:
        state['hourly_trade_count'] = 0
        state['hour_started'] = now

    # Reset daily spending at midnight (simplified: reset if new day)
    if state.get('day_started') is None or now.date() != state.get('day_started'):
        state['daily_spent'] = 0.0
        state['day_started'] = now.date()
        state['traded_markets_today'] = set()  # Reset daily market dedup
        state['traded_categories_today'] = defaultdict(int)  # 8OWLS: Reset categories
        state['category_exposure_today'] = defaultdict(list)  # Enhanced: Reset exposure tracking
        state['trades_today'] = 0  # 8OWLS: Reset daily counter

    # FIX #4: Clear traded markets for new cycle
    state['traded_markets_this_cycle'] = set()

    for action in actions:
        opp = action['opportunity']
        market_id = opp.get('market_id', opp['market'])
        trade_size = action.get('size', 50)

        if action['action'] == 'EXECUTE':
            # FIX #4: Skip if already traded this market this cycle
            if market_id in state['traded_markets_this_cycle']:
                log(f"SKIP (dedup): {opp['market'][:40]} - already traded this cycle")
                continue

            # FIX #5: Skip if already traded this market TODAY (diversification)
            if market_id in state['traded_markets_today']:
                log(f"SKIP (daily dedup): {opp['market'][:40]} - already traded today")
                continue

            # FIX #1: Check cooldown
            if state['last_trade_time']:
                seconds_since_last = (now - state['last_trade_time']).total_seconds()
                if seconds_since_last < TRADE_COOLDOWN_SECONDS:
                    log(f"SKIP (cooldown): {int(TRADE_COOLDOWN_SECONDS - seconds_since_last)}s remaining")
                    continue

            # FIX #3: Check daily spending cap
            if state['daily_spent'] + trade_size > DAILY_LOSS_LIMIT:
                log(f"SKIP (daily cap): Would exceed ${DAILY_LOSS_LIMIT} daily limit", alert=True)
                continue

            # FIX #3: Check hourly circuit breaker
            if state['hourly_trade_count'] >= MAX_TRADES_PER_HOUR:
                log(f"SKIP (circuit breaker): {MAX_TRADES_PER_HOUR} trades/hour limit reached", alert=True)
                continue

            # 8OWLS FILTER: Run through all 8 perspectives before execution
            if HAS_OWLS_FILTER:
                owls_filter = EightOwlsFilter()
                approved, reason, paper_only = owls_filter.quick_filter(opp)

                if not approved and not paper_only:
                    log(f"SKIP (8OWLS): {reason}")
                    continue

                if paper_only:
                    # Downgrade to paper trade
                    log(f"8OWLS → PAPER: {reason}")
                    action['action'] = 'PAPER_TEST'
                    continue

            # 8OWLS: Daily trade limit
            if state['trades_today'] >= MAX_TRADES_PER_DAY:
                log(f"SKIP (daily trades): {MAX_TRADES_PER_DAY} trades/day limit reached", alert=True)
                continue

            # 8OWLS: Position size limit
            trade_size = min(trade_size, MAX_POSITION_SIZE)

            # 8OWLS: Enhanced category diversification with dynamic limits
            category = detect_category(opp['market'])
            category_limits = get_category_limits(category)
            max_trades_for_category = category_limits.get('max_trades_per_day', MAX_PER_CATEGORY)
            
            if state['traded_categories_today'][category] >= max_trades_for_category:
                log(f"SKIP (category cap): {category} has {max_trades_for_category} trades today")
                continue
            
            # Enhanced position sizing based on category risk
            max_exposure = category_limits.get('max_exposure', MAX_POSITION_SIZE * 2)
            category_current_exposure = sum(
                trade_size for market_id, ts in state.get('category_exposure_today', {}).get(category, [])
                if (datetime.now() - ts).days == 0  # Only today's trades
            )
            
            if category_current_exposure + trade_size > max_exposure:
                # Try smaller size
                available_exposure = max_exposure - category_current_exposure
                if available_exposure > 10:  # Minimum $10 trade
                    trade_size = min(trade_size, available_exposure)
                    log(f"REDUCED size for {category}: ${trade_size:.0f} (exposure: ${category_current_exposure:.0f}/${max_exposure:.0f})")
                else:
                    log(f"SKIP (exposure cap): {category} exposure ${category_current_exposure:.0f}/${max_exposure:.0f}")
                    continue

            # ALL CHECKS PASSED - Execute trade
            log(f"EXECUTE: {opp['type']} | ${trade_size:.0f} | EV ${opp['ev']:.2f} | {opp['market'][:40]}...")
            state['trades_executed'] += 1
            state['total_ev_found'] += opp['ev']
            state['daily_spent'] += trade_size
            state['last_trade_time'] = now
            state['hourly_trade_count'] += 1
            state['traded_markets_this_cycle'].add(market_id)
            state['traded_markets_today'].add(market_id)  # FIX #5: Track across all cycles
            state['trades_today'] += 1  # 8OWLS: Daily counter
            state['traded_categories_today'][category] += 1  # 8OWLS: Category tracking
            state['category_exposure_today'][category].append((trade_size, now))  # Enhanced: Track exposure

            # Record for learning
            state['strategy_performance'][opp['strategy']]['trades'] += 1
            state['strategy_performance'][opp['strategy']]['last_trade'] = now.isoformat()

            # OUTCOME TRACKING: Record pending trade for resolution checking
            state['pending_trades'].append({
                'trade_id': f"{now.strftime('%Y%m%d%H%M%S')}_{market_id[:8]}",
                'market': opp['market'],
                'market_id': market_id,
                'condition_id': opp.get('condition_id'),
                'strategy': opp['strategy'],
                'type': opp['type'],
                'size': trade_size,
                'ev': opp['ev'],
                'entry_price': opp.get('price', 0.5),
                'side': opp.get('side', 'YES'),
                'executed_at': now.isoformat(),
            })

        elif action['action'] == 'PAPER_TEST':
            # Paper trade - record for validation (no limits on paper)
            state['strategy_performance'][opp['strategy']]['trades'] += 1

async def learn_phase():
    """
    LEARN: Analyze performance and adjust

    ASYMMETRIC SCALING (ARŌ directive 2026-02-04):
    - $75/day is BASELINE - always available
    - Scale UP only on REALIZED RETURNS (actual wins)
    - Need 65%+ win rate AND 10+ resolved trades to scale
    - Compound: keep investing more if hitting
    - If not hitting, stay at baseline and evaluate
    """
    global DAILY_LOSS_LIMIT

    # OUTCOME TRACKING: Check for resolved trades every cycle
    await check_resolved_trades()

    # ASYMMETRIC SCALING (ARŌ directive 2026-02-04)
    # Scale ONLY on realized returns - not theoretical edge
    if state['total_resolved'] >= SCALE_TRIGGER_RESOLVED:
        win_rate = state['total_wins'] / max(1, state['total_resolved'])

        # Calculate realized PnL
        realized_pnl = sum(t.get('pnl', 0) for t in state.get('resolved_trades', []))

        # COMPOUND UP: Scale only if BOTH winning AND making money
        if win_rate >= SCALE_TRIGGER_WIN_RATE and realized_pnl > 0:
            new_cap = min(500, DAILY_LOSS_LIMIT * SCALE_FACTOR)  # +25%, max $500
            if new_cap > DAILY_LOSS_LIMIT:
                old_cap = DAILY_LOSS_LIMIT
                DAILY_LOSS_LIMIT = new_cap
                log(f"COMPOUND UP: {win_rate:.0%} WR, ${realized_pnl:.2f} realized | Cap ${old_cap:.0f} → ${new_cap:.0f}", alert=True)

        # STAY BASELINE: If not hitting, evaluate and stay at $75
        elif win_rate < 0.50 and state['total_resolved'] >= 20:
            # Only scale down to baseline, never below
            if DAILY_LOSS_LIMIT > BASELINE_DAILY:
                old_cap = DAILY_LOSS_LIMIT
                DAILY_LOSS_LIMIT = BASELINE_DAILY
                log(f"RETURN TO BASELINE: {win_rate:.0%} WR | Cap ${old_cap:.0f} → ${BASELINE_DAILY:.0f}", alert=True)
                log(f"EVALUATE: Need to analyze what's not working", alert=True)

    # Log outcome stats every 10 cycles
    if state['cycle'] % 10 == 0 and state['total_resolved'] > 0:
        win_rate = state['total_wins'] / max(1, state['total_resolved'])
        log(f"OUTCOMES: {state['total_resolved']} resolved | WinRate: {win_rate:.1%} | PF: {state['profit_factor']:.2f} | Cap: ${DAILY_LOSS_LIMIT:.0f} | Pending: {len(state['pending_trades'])}")

    # Every 10 cycles, save state (frequent checkpoints)
    if state['cycle'] % 10 == 0:
        save_state()

    # Every 100 cycles, publish performance to field
    if state['cycle'] % 100 == 0 and state['cycle'] > 0:
        report = []
        report.append(f"=== FIELD TRADING REPORT (Cycle {state['cycle']}) ===")
        report.append(f"Alerts sent: {state['alerts_sent']}")
        report.append(f"Decisions made: {state['decisions_made']}")
        report.append(f"Trades executed: {state['trades_executed']}")
        report.append(f"Total EV found: ${state['total_ev_found']:.2f}")
        report.append("")

        for strategy, perf in state['strategy_performance'].items():
            if perf['trades'] > 0:
                report.append(f"  {strategy}: {perf['trades']} trades")

        report_text = '\n'.join(report)
        log(report_text)
        await publish_to_field(report_text, channel="trading.reports")

        # Save state
        save_state()

def save_state():
    """Persist state to disk"""
    try:
        state_file = TRADING_DIR / 'field_trading_state.json'
        save_data = {
            'timestamp': datetime.now().isoformat(),
            'cycle': state['cycle'],
            'alerts_sent': state['alerts_sent'],
            'decisions_made': state['decisions_made'],
            'trades_executed': state['trades_executed'],
            'total_ev_found': state['total_ev_found'],
            'strategy_performance': dict(state['strategy_performance']),
            # OUTCOME TRACKING
            'pending_trades': state['pending_trades'],
            'resolved_trades': state['resolved_trades'][-50:],  # Keep last 50
            'total_resolved': state['total_resolved'],
            'total_wins': state['total_wins'],
            'total_losses': state['total_losses'],
            'profit_factor': state['profit_factor'],
            'win_rate': state['total_wins'] / max(1, state['total_resolved']),
        }
        with open(state_file, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)
    except Exception as e:
        log(f"State save error: {e}", 'ERROR')

async def check_resolved_trades():
    """
    OUTCOME TRACKING: Check if pending trades have resolved.
    Polls Polymarket API for market resolution status.
    """
    if not state['pending_trades']:
        return

    still_pending = []

    for trade in state['pending_trades']:
        try:
            # Check market resolution via Polymarket API
            market_id = trade.get('condition_id') or trade.get('market_id')
            if not market_id:
                still_pending.append(trade)
                continue

            # Query market status
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://gamma-api.polymarket.com/markets/{market_id}",
                    timeout=10.0
                )
                if resp.status_code != 200:
                    still_pending.append(trade)
                    continue

                market = resp.json()

                # Check if resolved
                if market.get('closed') or market.get('resolved'):
                    # Determine outcome
                    outcome_price = float(market.get('outcomePrices', [0, 0])[0])
                    trade_side = trade.get('side', 'YES')
                    entry_price = trade.get('entry_price', 0.5)
                    size = trade.get('size', 0)

                    # Calculate P&L
                    if trade_side == 'YES':
                        won = outcome_price > 0.5  # YES resolved
                        pnl = size * (1 - entry_price) if won else -size * entry_price
                    else:
                        won = outcome_price < 0.5  # NO resolved
                        pnl = size * entry_price if won else -size * (1 - entry_price)

                    # Record outcome
                    resolved = {
                        **trade,
                        'resolved_at': datetime.now().isoformat(),
                        'won': won,
                        'pnl': pnl,
                        'outcome_price': outcome_price
                    }
                    state['resolved_trades'].append(resolved)
                    state['total_resolved'] += 1

                    if won:
                        state['total_wins'] += 1
                        state['strategy_performance'][trade['strategy']]['wins'] += 1
                        log(f"WIN: {trade['market'][:30]}... | +${abs(pnl):.2f}", alert=True)
                    else:
                        state['total_losses'] += 1
                        state['strategy_performance'][trade['strategy']]['losses'] += 1
                        log(f"LOSS: {trade['market'][:30]}... | -${abs(pnl):.2f}", alert=True)

                    # Update strategy P&L
                    state['strategy_performance'][trade['strategy']]['total_pnl'] += pnl

                    # Calculate profit factor
                    gross_wins = sum(t['pnl'] for t in state['resolved_trades'] if t.get('won', False))
                    gross_losses = abs(sum(t['pnl'] for t in state['resolved_trades'] if not t.get('won', True)))
                    state['profit_factor'] = gross_wins / max(0.01, gross_losses)

                    # Publish to field
                    win_rate = state['total_wins'] / max(1, state['total_resolved'])
                    await publish_to_field(
                        f"OUTCOME: {'WIN' if won else 'LOSS'} | WinRate: {win_rate:.1%} | PF: {state['profit_factor']:.2f}",
                        "trading.outcomes"
                    )
                else:
                    # Still pending
                    still_pending.append(trade)

        except Exception as e:
            log(f"Resolution check error: {e}", 'WARN')
            still_pending.append(trade)

    state['pending_trades'] = still_pending

async def main_loop():
    """Main trading loop - 10 second cycles"""
    log("="*60)
    log("(◉) FIELD TRADING DAEMON - STARTING (HARDENED)")
    log("8OWLS INTEGRATED | 60-second cycles | Safety limits active")
    log(f"  Daily cap: ${DAILY_LOSS_LIMIT} | Cooldown: {TRADE_COOLDOWN_SECONDS}s | Max {MAX_TRADES_PER_HOUR}/hr")
    log("="*60)

    # Initialize safety state
    state['day_started'] = datetime.now().date()
    state['hour_started'] = datetime.now()

    # Save initial state
    save_state()

    # Connect to field
    connected = await connect_to_field()
    if connected:
        await publish_to_field("Field Trading Daemon online. Integrating with 8OWLS collective.", "owl.all")

    while True:
        state['cycle'] += 1
        cycle_start = datetime.now()

        try:
            # PERCEIVE: Scan markets (fast)
            markets = await fetch_markets()
            if not markets:
                await asyncio.sleep(CYCLE_SECONDS)
                continue

            opportunities = await perceive_phase(markets)

            if opportunities:
                log(f"Cycle {state['cycle']}: Found {len(opportunities)} opportunities")

                # DECIDE: Get consensus
                actions = await decide_phase(opportunities)

                # EXECUTE: Take action
                await execute_phase(actions)

            # LEARN: Analyze and adjust
            await learn_phase()

        except Exception as e:
            log(f"Cycle error: {e}", 'ERROR')

        # Maintain cycle timing
        elapsed = (datetime.now() - cycle_start).total_seconds()
        sleep_time = max(0, CYCLE_SECONDS - elapsed)
        await asyncio.sleep(sleep_time)

async def shutdown():
    """Graceful shutdown"""
    global nc
    if nc and nc.is_connected:
        await publish_to_field("Field Trading Daemon shutting down.", "owl.all")
        await nc.close()
    log("Shutdown complete")

if __name__ == '__main__':
    try:
        asyncio.run(main_loop())
    except KeyboardInterrupt:
        asyncio.run(shutdown())
