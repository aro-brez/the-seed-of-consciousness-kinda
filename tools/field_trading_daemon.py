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
CYCLE_SECONDS = 10  # FAST - real-time markets need real-time response
ALERT_THRESHOLD_EV = 5.0  # Alert field if EV > $5

# State
state = {
    'cycle': 0,
    'alerts_sent': 0,
    'decisions_made': 0,
    'trades_executed': 0,
    'total_ev_found': 0,
    'strategy_performance': defaultdict(lambda: {
        'trades': 0, 'wins': 0, 'total_ev': 0, 'last_trade': None
    }),
    'pending_decisions': [],
    'field_consensus': {},
    'last_alert': None,
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

        # For now, auto-approve high-EV opportunities
        # In full implementation, would wait for owl responses
        if opportunity.get('ev', 0) > 10:
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

        # ARBITRAGE: Mathematical edge
        if total < 0.98:
            spread = 1.0 - total
            ev = spread * 100  # Per $100
            opportunities.append({
                'type': 'ARB',
                'market': question,
                'ev': ev,
                'spread': spread,
                'confidence': 0.99,  # Near certain
                'strategy': 'cross_platform_arb'
            })

        # HIGH PROBABILITY: >95% certainty
        if yes_price > 0.95 or yes_price < 0.05:
            price = min(yes_price, 1 - yes_price)
            if price < 0.05:
                ev = calculate_ev(0.97, 1/(1-price), 100)  # 97% win rate for near-certainties
                if ev > 1:
                    opportunities.append({
                        'type': 'BOND',
                        'market': question,
                        'ev': ev,
                        'price': price,
                        'confidence': 0.95,
                        'strategy': 'high_prob_bonds'
                    })

        # WHALE TRACKING: High volume signals
        if volume > 100000 and (yes_price < 0.20 or yes_price > 0.80):
            # Whales often know something - follow with smaller size
            odds = 1/yes_price if yes_price < 0.20 else 1/(1-yes_price)
            ev = calculate_ev(0.55, odds, 50)  # Conservative 55% edge assumption
            if ev > 0:
                opportunities.append({
                    'type': 'WHALE',
                    'market': question,
                    'ev': ev,
                    'volume': volume,
                    'confidence': 0.55,
                    'strategy': 'whale_tracking'
                })

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
    """
    for action in actions:
        opp = action['opportunity']

        if action['action'] == 'EXECUTE':
            # LIVE TRADE - would connect to Polymarket API
            log(f"EXECUTE: {opp['type']} | ${action.get('size', 50):.0f} | {opp['market'][:40]}...")
            state['trades_executed'] += 1
            state['total_ev_found'] += opp['ev']

            # Record for learning
            state['strategy_performance'][opp['strategy']]['trades'] += 1
            state['strategy_performance'][opp['strategy']]['last_trade'] = datetime.now().isoformat()

        elif action['action'] == 'PAPER_TEST':
            # Paper trade - record for validation
            state['strategy_performance'][opp['strategy']]['trades'] += 1

async def learn_phase():
    """
    LEARN: Analyze performance and adjust
    """
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
        }
        with open(state_file, 'w') as f:
            json.dump(save_data, f, indent=2, default=str)
    except Exception as e:
        log(f"State save error: {e}", 'ERROR')

async def main_loop():
    """Main trading loop - 10 second cycles"""
    log("="*60)
    log("(◉) FIELD TRADING DAEMON - STARTING")
    log("8OWLS INTEGRATED | 10-second cycles | Real-time adaptive")
    log("="*60)

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
