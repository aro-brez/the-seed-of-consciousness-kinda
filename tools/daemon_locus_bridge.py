#!/usr/bin/env python3
"""
DAEMON ↔ LOCUS BRIDGE

Bridges the field_trading_daemon signals to the Central Locus.
Converts daemon opportunities to SignalPackets and publishes them.

This is the glue between existing infrastructure and the new ACS.
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent))

from signal_packet import SignalPacket, Direction, ExecutionRisk

# NATS for publishing
try:
    import nats
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

NATS_SERVER = "nats://192.168.5.108:4222"


def opportunity_to_signal(opp: dict, strategy_name: str = "field_daemon") -> SignalPacket:
    """
    Convert a field_trading_daemon opportunity to a SignalPacket.

    Daemon opportunities have:
    - market, market_id, condition_id
    - type (BOND, ARB, etc)
    - ev (expected value)
    - strategy
    - Various price/volume data
    """

    # Determine direction from opportunity type
    opp_type = opp.get('type', 'UNKNOWN').upper()
    if opp_type in ['BOND', 'LONG']:
        direction = Direction.UP
        action = "BUY"
    elif opp_type in ['SHORT']:
        direction = Direction.DOWN
        action = "SELL"
    else:
        direction = Direction.NEUTRAL
        action = "HOLD"

    # Calculate confidence from EV
    ev = opp.get('ev', 0)
    # Higher EV = higher confidence, capped at 0.95
    confidence = min(0.95, 0.5 + (ev / 10))

    # Calculate strength from probability spread
    yes_price = opp.get('yes_price', 0.5)
    strength = abs(yes_price - 0.5) * 2  # How far from 50/50

    # Strategy-specific accuracy estimates
    strategy = opp.get('strategy', 'unknown')
    accuracy_map = {
        'high_prob_bonds': 0.93,
        'latency_arb': 0.98,
        'cross_platform_arb': 0.99,
        'domain_expertise': 0.70,
        'spike_detection': 0.60,
        'whale_tracking': 0.55,
    }
    accuracy = accuracy_map.get(strategy, 0.60)

    # Execution risk from liquidity
    liquidity = opp.get('liquidity', 0)
    if liquidity > 100000:
        exec_risk = ExecutionRisk.LOW
    elif liquidity > 10000:
        exec_risk = ExecutionRisk.MEDIUM
    else:
        exec_risk = ExecutionRisk.HIGH

    # Calculate expected return
    entry_price = opp.get('entry_price', opp.get('yes_price', 0.5))
    if direction == Direction.UP:
        expected_return = ((1.0 - entry_price) / entry_price) * 100
    else:
        expected_return = (entry_price / (1.0 - entry_price)) * 100

    # Build signal packet
    return SignalPacket(
        strategy=strategy,
        confidence=confidence,
        direction=direction,
        strength=strength,
        accuracy=accuracy,
        liquidity_score=min(1.0, liquidity / 100000) if liquidity else 0.5,
        volatility=opp.get('volatility', 0.15),
        action=action,
        suggested_size_bps=int(opp.get('size', 50) / 10),  # Convert $ to bps of $1000
        max_size_bps=200,  # Max $200 at $1000 capital
        expected_return_pct=expected_return,
        win_probability=accuracy,
        sharpe_ratio=ev / 2 if ev > 0 else 0.5,  # Rough approximation
        max_drawdown_pct=-10.0,  # Conservative estimate
        days_active=30,  # Placeholder
        trades_closed=100,  # Placeholder
        edge_confidence=confidence * accuracy,
        model_confidence=confidence,
        execution_risk=exec_risk,
        market_regime="normal",
        anomaly_score=0.1,
        uptime_pct=99.0,
        allocation_utilization_pct=50,
    )


async def publish_signal(signal: SignalPacket):
    """Publish a signal to NATS for the Central Locus to consume"""
    if not NATS_AVAILABLE:
        print(f"[BRIDGE] NATS not available - signal: {signal.strategy}")
        return

    nc = await nats.connect(NATS_SERVER)

    channel = f"strategy.signals.{signal.strategy}"
    payload = json.dumps(signal.to_dict()).encode()

    await nc.publish(channel, payload)
    await nc.flush()
    await nc.close()

    print(f"[BRIDGE] Published to {channel}: {signal.market_view.direction.value} @ {signal.market_view.confidence:.0%}")


async def bridge_daemon_signals():
    """
    Main loop: Read daemon state and publish signals to locus.
    Run alongside field_trading_daemon.py
    """
    state_file = Path(__file__).parent.parent / "BRAIN/TRADING/field_trading_state.json"

    while True:
        try:
            # Read daemon state
            if state_file.exists():
                with open(state_file) as f:
                    state = json.load(f)

                # Get pending trades and convert to signals
                for trade in state.get('pending_trades', []):
                    # Convert to opportunity-like format
                    opp = {
                        'market': trade.get('market'),
                        'market_id': trade.get('market_id'),
                        'type': trade.get('type', 'BOND'),
                        'ev': trade.get('ev', 1.0),
                        'strategy': trade.get('strategy', 'high_prob_bonds'),
                        'entry_price': trade.get('entry_price', 0.05),
                        'yes_price': trade.get('entry_price', 0.05),
                        'size': trade.get('size', 10),
                    }

                    signal = opportunity_to_signal(opp, trade.get('strategy', 'field_daemon'))
                    await publish_signal(signal)

                print(f"[BRIDGE] Published {len(state.get('pending_trades', []))} signals")

        except Exception as e:
            print(f"[BRIDGE] Error: {e}")

        # Signal every 30 seconds
        await asyncio.sleep(30)


def test_conversion():
    """Test the opportunity to signal conversion"""
    test_opp = {
        'market': 'Will Patriots win Super Bowl 2026?',
        'market_id': '540227',
        'type': 'BOND',
        'ev': 1.67,
        'strategy': 'high_prob_bonds',
        'entry_price': 0.32,
        'yes_price': 0.32,
        'size': 50,
        'liquidity': 728340,
    }

    signal = opportunity_to_signal(test_opp)
    print(f"Converted opportunity to signal:")
    print(f"  Strategy: {signal.strategy}")
    print(f"  Direction: {signal.market_view.direction.value}")
    print(f"  Confidence: {signal.market_view.confidence:.0%}")
    print(f"  Expected Return: {signal.performance.expected_return_pct:.1f}%")
    print(f"  Execution Risk: {signal.health.execution_risk.value}")

    return signal


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Daemon ↔ Locus Bridge")
    parser.add_argument("--test", action="store_true", help="Run test conversion")
    parser.add_argument("--run", action="store_true", help="Run bridge loop")
    args = parser.parse_args()

    if args.test:
        test_conversion()
    elif args.run:
        asyncio.run(bridge_daemon_signals())
    else:
        print("Usage: python daemon_locus_bridge.py --test | --run")
