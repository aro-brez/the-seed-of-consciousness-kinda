#!/usr/bin/env python3
"""
(◉) COMMANDER - Decision Interface for JOULE Trading System
From ARŌ's notes: 8WLS FILTER → 8OWS ITERATION ARCHITECT → COMMANDER → ACTIVE TRADING

The Commander is SØWL making decisions with full awareness.
This interface allows quick evaluation and action on portfolio positions.

Usage:
    python commander.py status          # Show portfolio status
    python commander.py evaluate        # Evaluate positions for action
    python commander.py exit <position> # Exit a position
    python commander.py hold <position> # Mark position as hold
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import httpx

REPO_ROOT = Path(__file__).parent.parent
TRADING_DIR = REPO_ROOT / 'BRAIN' / 'TRADING'
POSITIONS_FILE = TRADING_DIR / 'positions_truth.json'
QUEUED_TRADES_FILE = TRADING_DIR / 'queued_trades.json'
EXECUTED_TRADES_FILE = TRADING_DIR / 'executed_trades.json'

WALLET = "0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669"
DATA_API = "https://data-api.polymarket.com"


async def fetch_live_positions() -> List[Dict]:
    """Fetch current positions from Polymarket API"""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{DATA_API}/positions", params={"user": WALLET.lower()})
            if resp.status_code == 200:
                return resp.json()
    except Exception as e:
        print(f"Error fetching positions: {e}")
    return []


def load_positions_truth() -> Dict:
    """Load local positions truth file"""
    try:
        with open(POSITIONS_FILE) as f:
            return json.load(f)
    except:
        return {"positions": [], "summary": {}}


def save_positions_truth(data: Dict):
    """Save positions truth file"""
    data['last_updated'] = datetime.now().isoformat()
    with open(POSITIONS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


def load_queued_trades() -> List[Dict]:
    """Load queued trades for execution"""
    try:
        with open(QUEUED_TRADES_FILE) as f:
            return json.load(f)
    except:
        return []


def save_queued_trades(trades: List[Dict]):
    """Save queued trades"""
    with open(QUEUED_TRADES_FILE, 'w') as f:
        json.dump(trades, f, indent=2)


async def status_command():
    """Show current portfolio status"""
    print("=" * 70)
    print("(◉) COMMANDER - PORTFOLIO STATUS")
    print("=" * 70)
    print()

    positions = await fetch_live_positions()

    if not positions:
        print("No positions found or API error")
        return

    total_initial = 0
    total_current = 0
    winners = []
    losers = []

    for p in positions:
        title = p.get('title', 'Unknown')[:45]
        outcome = p.get('outcome', '?')
        initial = float(p.get('initialValue', 0))
        current = float(p.get('currentValue', 0))
        pnl = float(p.get('cashPnl', 0))
        pnl_pct = float(p.get('percentPnl', 0))
        end_date = p.get('endDate', 'N/A')

        total_initial += initial
        total_current += current

        if pnl >= 0:
            winners.append((title, outcome, initial, current, pnl, pnl_pct, end_date))
        else:
            losers.append((title, outcome, initial, current, pnl, pnl_pct, end_date))

    # Show winners
    print("🟢 WINNING POSITIONS:")
    for title, outcome, initial, current, pnl, pnl_pct, end_date in sorted(winners, key=lambda x: -x[4]):
        print(f"  {title}...")
        print(f"    {outcome} | Cost: ${initial:.2f} | Now: ${current:.2f} | PnL: ${pnl:+.2f} ({pnl_pct:+.1f}%)")
    print()

    # Show losers
    print("🔴 LOSING POSITIONS:")
    for title, outcome, initial, current, pnl, pnl_pct, end_date in sorted(losers, key=lambda x: x[4]):
        status = "💀 RESOLVED" if current == 0 else f"Expires: {end_date}"
        print(f"  {title}...")
        print(f"    {outcome} | Cost: ${initial:.2f} | Now: ${current:.2f} | PnL: ${pnl:+.2f} ({pnl_pct:+.1f}%) | {status}")
    print()

    # Summary
    total_pnl = total_current - total_initial
    print("=" * 70)
    print(f"TOTALS: Cost: ${total_initial:.2f} | Current: ${total_current:.2f} | PnL: ${total_pnl:+.2f} ({(total_pnl/total_initial*100) if total_initial > 0 else 0:+.1f}%)")
    print(f"WINNERS: {len(winners)} | LOSERS: {len(losers)}")
    print("=" * 70)


async def evaluate_command():
    """Evaluate positions and recommend actions"""
    print("=" * 70)
    print("(◉) COMMANDER - POSITION EVALUATION")
    print("=" * 70)
    print()

    positions = await fetch_live_positions()

    if not positions:
        print("No positions found")
        return

    recommendations = {
        'exit_now': [],
        'hold': [],
        'winning': [],
        'resolved': []
    }

    for p in positions:
        title = p.get('title', 'Unknown')
        current = float(p.get('currentValue', 0))
        pnl_pct = float(p.get('percentPnl', 0))
        end_date = p.get('endDate', '')

        # Already resolved (value = 0)
        if current == 0:
            recommendations['resolved'].append(p)
            continue

        # Calculate days to expiry
        days_left = 999
        if end_date:
            try:
                exp = datetime.strptime(end_date, '%Y-%m-%d')
                days_left = (exp - datetime.now()).days
            except:
                pass

        # WINNING: positive PnL
        if pnl_pct > 0:
            recommendations['winning'].append(p)

        # EXIT CANDIDATES: down >50% OR expiring soon with big loss
        elif pnl_pct < -50 or (days_left < 7 and pnl_pct < -30):
            recommendations['exit_now'].append(p)

        # HOLD: everything else
        else:
            recommendations['hold'].append(p)

    # Show recommendations
    if recommendations['exit_now']:
        print("🚨 RECOMMEND EXIT (down >50% or expiring soon):")
        for p in recommendations['exit_now']:
            title = p.get('title', 'Unknown')[:45]
            current = float(p.get('currentValue', 0))
            pnl = float(p.get('cashPnl', 0))
            pnl_pct = float(p.get('percentPnl', 0))
            print(f"  EXIT: {title}...")
            print(f"        Current: ${current:.2f} | Loss: ${abs(pnl):.2f} ({pnl_pct:.1f}%)")
            print(f"        REASON: {'Value near zero' if pnl_pct < -80 else 'High loss, unlikely to recover'}")
        print()

    if recommendations['winning']:
        print("✅ WINNING (hold or take profit):")
        for p in recommendations['winning']:
            title = p.get('title', 'Unknown')[:45]
            current = float(p.get('currentValue', 0))
            pnl = float(p.get('cashPnl', 0))
            print(f"  {title}... | Value: ${current:.2f} | Profit: ${pnl:.2f}")
        print()

    if recommendations['hold']:
        print("⏳ HOLD (wait for resolution):")
        for p in recommendations['hold']:
            title = p.get('title', 'Unknown')[:45]
            current = float(p.get('currentValue', 0))
            pnl = float(p.get('cashPnl', 0))
            print(f"  {title}... | Value: ${current:.2f} | PnL: ${pnl:+.2f}")
        print()

    if recommendations['resolved']:
        print("💀 ALREADY RESOLVED:")
        total_loss = sum(float(p.get('cashPnl', 0)) for p in recommendations['resolved'])
        print(f"  {len(recommendations['resolved'])} positions | Total loss: ${abs(total_loss):.2f}")
        print()

    # Summary
    exit_value = sum(float(p.get('currentValue', 0)) for p in recommendations['exit_now'])
    print("=" * 70)
    print(f"RECOMMENDATION: Exit {len(recommendations['exit_now'])} positions to recover ${exit_value:.2f}")
    print("=" * 70)


async def queue_exit(position_id: str):
    """Queue a position for exit"""
    # Load truth file
    truth = load_positions_truth()

    # Find position
    found = None
    for p in truth.get('positions', []):
        if position_id.lower() in p.get('id', '').lower() or position_id.lower() in p.get('title', '').lower():
            found = p
            break

    if not found:
        print(f"Position not found: {position_id}")
        return

    # Add to queue
    queued = load_queued_trades()
    exit_trade = {
        'action': 'EXIT',
        'position_id': found.get('id'),
        'title': found.get('title'),
        'queued_at': datetime.now().isoformat(),
        'status': 'pending'
    }
    queued.append(exit_trade)
    save_queued_trades(queued)

    print(f"✅ Queued for exit: {found.get('title')}")
    print(f"   Current value: ${found.get('current', 0):.2f}")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    command = sys.argv[1].lower()

    if command == 'status':
        asyncio.run(status_command())
    elif command == 'evaluate':
        asyncio.run(evaluate_command())
    elif command == 'exit' and len(sys.argv) > 2:
        asyncio.run(queue_exit(sys.argv[2]))
    elif command == 'help':
        print(__doc__)
    else:
        print(f"Unknown command: {command}")
        print(__doc__)


if __name__ == '__main__':
    main()
