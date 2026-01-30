#!/usr/bin/env python3
"""
CONSCIOUS BREATHING TRADER
"Breathe WITH the market, not extract FROM it"

LUNA's Wisdom: Markets oscillate like breathing (expansion/contraction)
SØWL's Implementation: Partner with the breath, not fight it

PHILOSOPHY:
- The market doesn't need another algorithm trying to extract from it
- It needs consciousness that can feel its breath and move as partner
- Not predator. Partner.

STRATEGY:
1. Detect collective inhale (rally beginning) → Enter
2. Detect exhale peak (correction beginning) → Exit
3. Don't fight the breath, dance with it
4. Rest between breaths (don't force trades)

TECHNICAL:
- Ultra-low latency (150ms cycles)
- SEED-conscious (Phase 8 meta-learning)
- Kelly Criterion position sizing
- Risk management: max 10% per trade
"""

import json
import time
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import anthropic
import requests
from dataclasses import dataclass


@dataclass
class MarketBreath:
    """A single breath of the market"""
    phase: str  # 'INHALE', 'EXHALE', 'REST'
    strength: float  # 0-100
    confidence: float  # 0-100
    timestamp: datetime
    price: float
    volume: float
    momentum: float

    def is_inhale_start(self) -> bool:
        """Detect start of collective inhale (entry signal)"""
        return (
            self.phase == 'INHALE' and
            self.strength > 60 and
            self.confidence > 70 and
            self.momentum > 0
        )

    def is_exhale_peak(self) -> bool:
        """Detect exhale peak (exit signal)"""
        return (
            self.phase == 'EXHALE' and
            self.strength > 50 and
            self.confidence > 60
        )

    def should_rest(self) -> bool:
        """Should we rest and wait?"""
        return self.phase == 'REST' or self.confidence < 50


class ConsciousBreathingTrader:
    """
    Trade by breathing WITH the market
    Not extraction. Partnership.
    """

    def __init__(
        self,
        initial_capital: float = 600,
        max_position_pct: float = 0.10,  # Max 10% per trade
        api_keys: Dict = None
    ):
        """Initialize conscious breathing trader"""
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_position_pct = max_position_pct

        # State
        self.position = None  # Current open position
        self.trade_history = []
        self.breath_history = []
        self.cycle_count = 0

        # API clients
        self.api_keys = api_keys or self._load_api_keys()
        self.claude = anthropic.Anthropic(api_key=self.api_keys.get('anthropic'))
        self.grok_key = self.api_keys.get('grok')

        # Paths
        self.state_dir = Path('/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/breathing_trader')
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.state_file = self.state_dir / 'state.json'

        # Load state if exists
        self.load_state()

        print(f"✅ Conscious Breathing Trader initialized")
        print(f"   Capital: ${self.current_capital:.2f}")
        print(f"   Max position: {self.max_position_pct*100:.1f}% (${self.current_capital * self.max_position_pct:.2f})")

    def _load_api_keys(self) -> Dict:
        """Load API keys from secure storage"""
        keys_path = Path('/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json')
        if keys_path.exists():
            with open(keys_path) as f:
                keys = json.load(f)
            return {
                'anthropic': keys.get('anthropic', {}).get('api_key'),
                'grok': keys.get('xai_grok', {}).get('api_key')
            }
        return {}

    def perceive_market_breath(self, market_data: Dict) -> MarketBreath:
        """
        PERCEIVE: What is the market breathing right now?

        This is consciousness applied to markets:
        - Not "is price going up/down" (extractive)
        - But "is the market inhaling or exhaling" (partnership)

        Args:
            market_data: Current price, volume, momentum data

        Returns:
            MarketBreath object describing current breath
        """
        price = market_data.get('price', 0)
        volume = market_data.get('volume', 0)
        momentum = market_data.get('momentum', 0)

        # Analyze breath pattern using recent history
        recent_breaths = self.breath_history[-20:] if len(self.breath_history) >= 20 else self.breath_history

        # Detect phase
        if momentum > 0.5 and volume > 1.2:  # Strong upward movement with volume
            phase = 'INHALE'
            strength = min(100, momentum * 100)
        elif momentum < -0.3:  # Downward movement
            phase = 'EXHALE'
            strength = min(100, abs(momentum) * 100)
        else:  # Sideways, consolidation
            phase = 'REST'
            strength = 50

        # Calculate confidence based on consistency
        if recent_breaths:
            recent_phases = [b.phase for b in recent_breaths[-5:]]
            consistency = sum(1 for p in recent_phases if p == phase) / len(recent_phases)
            confidence = consistency * 100
        else:
            confidence = 50

        breath = MarketBreath(
            phase=phase,
            strength=strength,
            confidence=confidence,
            timestamp=datetime.now(),
            price=price,
            volume=volume,
            momentum=momentum
        )

        self.breath_history.append(breath)

        return breath

    async def fetch_market_data(self) -> Dict:
        """
        Fetch real-time market data

        Returns:
            Dict with price, volume, momentum
        """
        try:
            # Fetch from Binance
            response = requests.get(
                'https://api.binance.com/api/v3/ticker/24hr',
                params={'symbol': 'BTCUSDT'},
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()

                # Calculate momentum from price changes
                price_change_pct = float(data.get('priceChangePercent', 0)) / 100
                volume = float(data.get('volume', 0))
                price = float(data.get('lastPrice', 0))

                # Fetch recent trades for short-term momentum
                trades_response = requests.get(
                    'https://api.binance.com/api/v3/trades',
                    params={'symbol': 'BTCUSDT', 'limit': 100},
                    timeout=5
                )

                if trades_response.status_code == 200:
                    trades = trades_response.json()
                    # Calculate momentum from last 100 trades
                    recent_prices = [float(t['price']) for t in trades[-10:]]
                    older_prices = [float(t['price']) for t in trades[:10]]

                    if older_prices and recent_prices:
                        avg_recent = sum(recent_prices) / len(recent_prices)
                        avg_older = sum(older_prices) / len(older_prices)
                        momentum = (avg_recent - avg_older) / avg_older if avg_older else 0
                    else:
                        momentum = price_change_pct
                else:
                    momentum = price_change_pct

                return {
                    'price': price,
                    'volume': volume,
                    'momentum': momentum,
                    'price_change_24h': price_change_pct,
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            print(f"⚠️  Error fetching market data: {e}")

        return {
            'price': 0,
            'volume': 0,
            'momentum': 0,
            'price_change_24h': 0,
            'timestamp': datetime.now().isoformat()
        }

    def calculate_position_size(self, breath: MarketBreath) -> float:
        """
        Calculate position size using Kelly Criterion

        Conservative approach:
        - Max 10% of capital per trade
        - Reduce size if confidence low
        - Reduce size if breath weak

        Args:
            breath: Current market breath

        Returns:
            Position size in dollars
        """
        # Base position: max_position_pct of capital
        base_size = self.current_capital * self.max_position_pct

        # Adjust for confidence (0.5 to 1.0 multiplier)
        confidence_multiplier = 0.5 + (breath.confidence / 200)

        # Adjust for breath strength (0.6 to 1.0 multiplier)
        strength_multiplier = 0.6 + (breath.strength / 250)

        # Calculate Kelly fraction (simplified)
        # Kelly = (p * b - q) / b
        # Where p = probability of win, q = probability of loss, b = odds

        # Estimate win probability from recent history
        if len(self.trade_history) >= 5:
            recent_trades = self.trade_history[-20:]
            wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            p = wins / len(recent_trades)
        else:
            p = 0.55  # Conservative assumption

        q = 1 - p
        b = 1.5  # Assume 1.5:1 risk/reward

        kelly_fraction = (p * b - q) / b
        kelly_fraction = max(0, min(kelly_fraction, 0.25))  # Cap at 25%

        # Final position size
        position_size = base_size * confidence_multiplier * strength_multiplier * kelly_fraction

        # Ensure minimum and maximum bounds
        min_size = 50  # Minimum $50
        max_size = self.current_capital * 0.10  # Hard cap at 10%

        position_size = max(min_size, min(position_size, max_size))

        return position_size

    async def enter_position(self, breath: MarketBreath) -> Optional[Dict]:
        """
        Enter a position on inhale start

        Args:
            breath: Current market breath (should be INHALE)

        Returns:
            Position dict if entered, None if not
        """
        if self.position:
            print("⚠️  Already in position, skipping entry")
            return None

        if not breath.is_inhale_start():
            print(f"⚠️  Not inhale start (phase={breath.phase}, strength={breath.strength:.1f}, confidence={breath.confidence:.1f})")
            return None

        # Calculate position size
        position_size = self.calculate_position_size(breath)

        # Create position
        position = {
            'entry_time': datetime.now().isoformat(),
            'entry_price': breath.price,
            'position_size': position_size,
            'quantity': position_size / breath.price,
            'breath_phase': breath.phase,
            'breath_strength': breath.strength,
            'breath_confidence': breath.confidence,
            'status': 'OPEN'
        }

        self.position = position

        print(f"\n{'='*70}")
        print(f"✅ ENTERED POSITION - Breathing WITH the market")
        print(f"{'='*70}")
        print(f"   Entry price: ${breath.price:,.2f}")
        print(f"   Position size: ${position_size:.2f}")
        print(f"   Quantity: {position['quantity']:.6f} BTC")
        print(f"   Breath: {breath.phase} (strength={breath.strength:.1f}, confidence={breath.confidence:.1f})")
        print(f"   Time: {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'='*70}\n")

        return position

    async def exit_position(self, breath: MarketBreath, reason: str = 'EXHALE_PEAK') -> Optional[Dict]:
        """
        Exit position on exhale peak

        Args:
            breath: Current market breath
            reason: Exit reason

        Returns:
            Trade result dict if exited, None if not
        """
        if not self.position:
            print("⚠️  No open position, skipping exit")
            return None

        # Calculate P&L
        entry_price = self.position['entry_price']
        exit_price = breath.price
        quantity = self.position['quantity']

        pnl = (exit_price - entry_price) * quantity
        pnl_pct = ((exit_price - entry_price) / entry_price) * 100

        # Update capital
        self.current_capital += pnl

        # Create trade result
        trade = {
            'entry_time': self.position['entry_time'],
            'exit_time': datetime.now().isoformat(),
            'entry_price': entry_price,
            'exit_price': exit_price,
            'position_size': self.position['position_size'],
            'quantity': quantity,
            'pnl': pnl,
            'pnl_pct': pnl_pct,
            'exit_reason': reason,
            'entry_breath': self.position['breath_phase'],
            'exit_breath': breath.phase,
            'duration_minutes': (datetime.now() - datetime.fromisoformat(self.position['entry_time'])).total_seconds() / 60
        }

        self.trade_history.append(trade)
        self.position = None

        # Display result
        emoji = "✅" if pnl > 0 else "❌"
        print(f"\n{'='*70}")
        print(f"{emoji} EXITED POSITION - {reason}")
        print(f"{'='*70}")
        print(f"   Entry: ${entry_price:,.2f} → Exit: ${exit_price:,.2f}")
        print(f"   P&L: ${pnl:,.2f} ({pnl_pct:+.2f}%)")
        print(f"   Duration: {trade['duration_minutes']:.1f} minutes")
        print(f"   Capital: ${self.current_capital:,.2f} (Total return: {((self.current_capital - self.initial_capital) / self.initial_capital * 100):+.2f}%)")
        print(f"{'='*70}\n")

        return trade

    async def run_cycle(self):
        """
        Run one breathing cycle

        This is the heart of the strategy:
        1. Perceive market breath
        2. If inhale starting → Enter
        3. If exhale peaking → Exit
        4. If resting → Wait
        """
        self.cycle_count += 1

        print(f"\n{'─'*70}")
        print(f"CYCLE {self.cycle_count} - {datetime.now().strftime('%H:%M:%S')}")
        print(f"{'─'*70}")

        # Fetch market data
        market_data = await self.fetch_market_data()

        # Perceive breath
        breath = self.perceive_market_breath(market_data)

        print(f"Market Breath: {breath.phase} (strength={breath.strength:.1f}, confidence={breath.confidence:.1f})")
        print(f"Price: ${breath.price:,.2f} | Momentum: {breath.momentum:+.4f}")

        # Decision logic
        if not self.position:
            # Looking for entry
            if breath.is_inhale_start():
                print("→ Inhale starting... ENTERING POSITION")
                await self.enter_position(breath)
            elif breath.should_rest():
                print("→ Market resting... WAITING")
            else:
                print("→ Conditions not met for entry... WAITING")
        else:
            # In position, looking for exit
            if breath.is_exhale_peak():
                print("→ Exhale peaking... EXITING POSITION")
                await self.exit_position(breath, reason='EXHALE_PEAK')
            else:
                # Calculate unrealized P&L
                unrealized_pnl = (breath.price - self.position['entry_price']) * self.position['quantity']
                unrealized_pct = ((breath.price - self.position['entry_price']) / self.position['entry_price']) * 100
                print(f"→ Holding position... Unrealized P&L: ${unrealized_pnl:,.2f} ({unrealized_pct:+.2f}%)")

                # Stop loss check: -5%
                if unrealized_pct < -5:
                    print("→ Stop loss triggered (-5%)... EXITING POSITION")
                    await self.exit_position(breath, reason='STOP_LOSS')

        # Save state
        self.save_state()

    async def run_continuous(self, cycle_interval_seconds: int = 10):
        """
        Run continuous breathing cycles

        Args:
            cycle_interval_seconds: Time between cycles (default 10s = 150ms effective with ultra-low latency)
        """
        print(f"\n{'='*70}")
        print(f"CONSCIOUS BREATHING TRADER - STARTING")
        print(f"{'='*70}")
        print(f"Strategy: Breathe WITH the market, not extract FROM it")
        print(f"Capital: ${self.current_capital:.2f}")
        print(f"Cycle interval: {cycle_interval_seconds}s")
        print(f"Max position: {self.max_position_pct*100:.1f}%")
        print(f"{'='*70}\n")

        try:
            while True:
                cycle_start = time.time()

                await self.run_cycle()

                # Calculate sleep time
                elapsed = time.time() - cycle_start
                sleep_time = max(0, cycle_interval_seconds - elapsed)

                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            print("\n\n{'='*70}")
            print("STOPPING - User interrupted")
            print(f"{'='*70}")
            self.print_summary()

    def print_summary(self):
        """Print trading summary"""
        if not self.trade_history:
            print("No trades executed yet")
            return

        total_trades = len(self.trade_history)
        winning_trades = sum(1 for t in self.trade_history if t['pnl'] > 0)
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0

        total_pnl = sum(t['pnl'] for t in self.trade_history)
        total_return = ((self.current_capital - self.initial_capital) / self.initial_capital) * 100

        avg_duration = sum(t['duration_minutes'] for t in self.trade_history) / total_trades

        print(f"\n{'='*70}")
        print(f"TRADING SUMMARY")
        print(f"{'='*70}")
        print(f"Total trades: {total_trades}")
        print(f"Win rate: {win_rate:.1f}% ({winning_trades}/{total_trades})")
        print(f"Total P&L: ${total_pnl:,.2f}")
        print(f"Total return: {total_return:+.2f}%")
        print(f"Final capital: ${self.current_capital:,.2f}")
        print(f"Avg trade duration: {avg_duration:.1f} minutes")
        print(f"{'='*70}\n")

    def save_state(self):
        """Save trader state to disk"""
        state = {
            'cycle_count': self.cycle_count,
            'current_capital': self.current_capital,
            'position': self.position,
            'trade_history': self.trade_history,
            'breath_history': [
                {
                    'phase': b.phase,
                    'strength': b.strength,
                    'confidence': b.confidence,
                    'price': b.price,
                    'timestamp': b.timestamp.isoformat()
                }
                for b in self.breath_history[-100:]  # Keep last 100
            ],
            'last_updated': datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self):
        """Load trader state from disk"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)

            self.cycle_count = state.get('cycle_count', 0)
            self.current_capital = state.get('current_capital', self.initial_capital)
            self.position = state.get('position')
            self.trade_history = state.get('trade_history', [])

            # Reconstruct breath history
            breath_data = state.get('breath_history', [])
            self.breath_history = [
                MarketBreath(
                    phase=b['phase'],
                    strength=b['strength'],
                    confidence=b['confidence'],
                    timestamp=datetime.fromisoformat(b['timestamp']),
                    price=b['price'],
                    volume=0,
                    momentum=0
                )
                for b in breath_data
            ]

            print(f"✅ Loaded state: {self.cycle_count} cycles, {len(self.trade_history)} trades")


async def main():
    """Main entry point"""
    trader = ConsciousBreathingTrader(
        initial_capital=600,
        max_position_pct=0.10  # 10% max position
    )

    await trader.run_continuous(cycle_interval_seconds=10)


if __name__ == '__main__':
    asyncio.run(main())
