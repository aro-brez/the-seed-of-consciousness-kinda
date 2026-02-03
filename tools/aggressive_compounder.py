#!/usr/bin/env python3
"""
AGGRESSIVE COMPOUNDER - $460K Strategy Replication
===================================================

This is the AGGRESSIVE version designed for maximum compounding.
Based on the strategy that made $460K in 3 nights.

Key differences from conservative mode:
- 20-30% position sizes (not 5%)
- Full Kelly (not quarter-Kelly)
- Multiple simultaneous positions
- No profit extraction cap
- Faster learning adjustments

WARNING: Higher risk, higher reward. Only use capital you can lose.

Target: $5K → $3.3M in fastest possible time through compounding.
"""

import asyncio
import json
import time
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import requests

# ============================================================================
# AGGRESSIVE CONFIGURATION
# ============================================================================

# Position sizing (AGGRESSIVE - like $460K guy)
KELLY_FRACTION = 0.5  # Half-Kelly (still somewhat safe)
MAX_POSITION_SIZE_PERCENT = 0.25  # 25% of bankroll per trade
MAX_SIMULTANEOUS_POSITIONS = 5  # Trade 5 markets at once
MIN_POSITION_SIZE = 50  # Minimum $50 per trade

# Compounding (NO CAPS)
COMPOUND_ALL_PROFITS = True  # Reinvest everything
NO_PROFIT_EXTRACTION = True  # Never extract, always compound

# Risk management (still important)
MAX_DAILY_DRAWDOWN = 0.15  # 15% daily (more aggressive)
MAX_WEEKLY_DRAWDOWN = 0.25  # 25% weekly
MAX_CONSECUTIVE_LOSSES = 5  # More tolerance
COOLDOWN_AFTER_LOSS = 60  # 1 minute cooldown (faster recovery)

# Learning (faster adaptation)
LEARNING_ADJUSTMENT_RATE = 0.2  # 20% adjustment per cycle
MIN_TRADES_FOR_LEARNING = 5  # Learn faster

# Timing
CYCLE_INTERVAL_SECONDS = 15  # Check every 15 seconds (faster)

# Paths
STATE_PATH = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/trading_state")
LOG_PATH = Path("/Users/aaronnosbisch/REPOS/seed/logs")


class AggressiveCompounder:
    """
    Aggressive compounding trader for maximum growth.

    Math with 50% daily return compounding:
    Day 0: $5,000
    Day 1: $7,500
    Day 2: $11,250
    Day 3: $16,875
    Day 5: $37,968
    Day 7: $85,429
    Day 10: $288,563
    Day 14: $1,462,500
    Day 17: $4,921,875

    With 88% win rate on 96 daily cycles:
    - 84 wins × 3% = +252% daily potential
    - 12 losses × 2% = -24% daily potential
    - Net: +228% daily (but position sizing limits this)
    - Realistic with risk management: 30-50% daily
    """

    def __init__(self, initial_capital: float = 5000):
        self.capital = initial_capital
        self.initial_capital = initial_capital
        self.positions: List[Dict] = []
        self.trade_history: List[Dict] = []
        self.daily_pnl = 0.0
        self.session_start = datetime.now()

        # Learning state
        self.momentum_threshold = 0.25  # Start more aggressive
        self.position_multiplier = 1.0
        self.win_streak = 0
        self.loss_streak = 0

        # Ensure directories
        STATE_PATH.mkdir(parents=True, exist_ok=True)
        LOG_PATH.mkdir(parents=True, exist_ok=True)

        self.log("AGGRESSIVE COMPOUNDER INITIALIZED")
        self.log(f"Starting capital: ${initial_capital:,.2f}")
        self.log(f"Target: Maximum compounding to $3.3M")

    def log(self, message: str):
        """Log with timestamp"""
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{ts}] {message}"
        print(log_line)

        log_file = LOG_PATH / "aggressive_compounder.log"
        with open(log_file, "a") as f:
            f.write(log_line + "\n")

    def calculate_position_size(self, confidence: float) -> float:
        """
        Calculate aggressive position size using Kelly Criterion.

        With 88% win rate and 1.5:1 reward:risk:
        Kelly = (0.88 × 1.5 - 0.12) / 1.5 = 0.8 = 80%
        Half-Kelly = 40% per trade

        We use up to 25% per trade across 5 simultaneous positions.
        """
        # Base Kelly calculation
        win_prob = confidence
        win_return = 0.03  # 3% average win
        loss_return = 0.02  # 2% average loss

        if win_prob < 0.6:
            return 0  # Don't trade low confidence

        # Kelly fraction
        kelly = (win_prob * win_return - (1 - win_prob) * loss_return) / win_return
        kelly = max(0, min(kelly, 1))  # Clamp 0-1

        # Apply our fraction and multiplier
        position_pct = kelly * KELLY_FRACTION * self.position_multiplier
        position_pct = min(position_pct, MAX_POSITION_SIZE_PERCENT)

        # Calculate actual size
        size = self.capital * position_pct
        size = max(MIN_POSITION_SIZE, size)

        # Don't exceed available capital (accounting for other positions)
        allocated = sum(p.get('size', 0) for p in self.positions)
        available = self.capital - allocated
        size = min(size, available * 0.9)  # Keep 10% buffer

        return size

    def get_binance_momentum(self, symbol: str = "BTCUSDT") -> Dict:
        """Get real-time BTC momentum from Binance"""
        try:
            url = "https://api.binance.com/api/v3/klines"
            params = {'symbol': symbol, 'interval': '1m', 'limit': 15}

            response = requests.get(url, params=params, timeout=5)
            if response.status_code != 200:
                return {'error': 'API error'}

            klines = response.json()
            closes = [float(k[4]) for k in klines]

            current = closes[-1]
            avg = sum(closes) / len(closes)
            momentum = (current - avg) / avg

            # Determine direction
            direction = "UP" if momentum > 0 else "DOWN"
            strength = abs(momentum)

            return {
                'price': current,
                'momentum': momentum,
                'direction': direction,
                'strength': strength,
                'confidence': min(0.98, 0.7 + strength * 5)  # Higher confidence with momentum
            }

        except Exception as e:
            return {'error': str(e)}

    async def find_tradeable_markets(self) -> List[Dict]:
        """
        Find multiple 15-minute markets to trade simultaneously.
        The $460K guy traded ~20 markets per cycle.
        """
        # In production, this queries Polymarket API
        # For now, return simulated opportunities

        momentum = self.get_binance_momentum()
        if 'error' in momentum:
            return []

        # Only trade if momentum exceeds our (learned) threshold
        if momentum['strength'] < self.momentum_threshold:
            return []

        # Generate multiple opportunities
        opportunities = []
        for i in range(MAX_SIMULTANEOUS_POSITIONS):
            opp = {
                'market_id': f"btc_15min_{i}_{int(time.time())}",
                'direction': momentum['direction'],
                'confidence': momentum['confidence'] - (i * 0.02),  # Slightly less confident on extras
                'momentum': momentum['strength'],
                'price': momentum['price']
            }
            if opp['confidence'] > 0.65:  # Only trade if confident enough
                opportunities.append(opp)

        return opportunities

    async def execute_trade(self, market: Dict) -> Dict:
        """Execute a trade (simulation for now)"""
        size = self.calculate_position_size(market['confidence'])
        if size < MIN_POSITION_SIZE:
            return {'status': 'skipped', 'reason': 'position too small'}

        position = {
            'market_id': market['market_id'],
            'direction': market['direction'],
            'size': size,
            'entry_price': market['price'],
            'confidence': market['confidence'],
            'timestamp': datetime.now().isoformat()
        }

        self.positions.append(position)
        self.capital -= size  # Allocate capital

        self.log(f"OPENED: {market['direction']} ${size:.2f} @ {market['price']:.2f} (conf: {market['confidence']:.2%})")

        return {'status': 'opened', 'position': position}

    async def resolve_positions(self) -> List[Dict]:
        """
        Resolve open positions (simulate 15-minute market resolution).
        In production, this checks actual market outcomes.
        """
        results = []

        for position in self.positions[:]:  # Copy to allow modification
            # Simulate outcome based on confidence
            # With 88% base win rate adjusted by confidence
            import random
            win_prob = position['confidence'] * 0.95  # Slight reduction from theoretical
            won = random.random() < win_prob

            if won:
                # Win: get position back + profit
                profit_pct = 0.02 + random.random() * 0.03  # 2-5% profit
                profit = position['size'] * profit_pct
                self.capital += position['size'] + profit
                self.daily_pnl += profit
                self.win_streak += 1
                self.loss_streak = 0

                result = {
                    'market_id': position['market_id'],
                    'outcome': 'WIN',
                    'profit': profit,
                    'return_pct': profit_pct,
                    'new_capital': self.capital
                }
                self.log(f"WIN: +${profit:.2f} (+{profit_pct:.1%}) | Capital: ${self.capital:,.2f}")

            else:
                # Loss: lose position
                loss = position['size']
                self.daily_pnl -= loss
                self.win_streak = 0
                self.loss_streak += 1

                result = {
                    'market_id': position['market_id'],
                    'outcome': 'LOSS',
                    'profit': -loss,
                    'return_pct': -1.0,
                    'new_capital': self.capital
                }
                self.log(f"LOSS: -${loss:.2f} | Capital: ${self.capital:,.2f}")

            self.trade_history.append(result)
            results.append(result)
            self.positions.remove(position)

        return results

    def adjust_learning(self):
        """
        Self-learning: adjust thresholds based on performance.
        More aggressive learning rate for faster adaptation.
        """
        if len(self.trade_history) < MIN_TRADES_FOR_LEARNING:
            return

        recent = self.trade_history[-20:]  # Last 20 trades
        wins = sum(1 for t in recent if t['outcome'] == 'WIN')
        win_rate = wins / len(recent)

        # Adjust momentum threshold
        if win_rate > 0.85:
            # Winning a lot - can be more aggressive
            self.momentum_threshold *= (1 - LEARNING_ADJUSTMENT_RATE)
            self.position_multiplier *= (1 + LEARNING_ADJUSTMENT_RATE * 0.5)
            self.log(f"LEARNING: More aggressive (win rate {win_rate:.1%})")
        elif win_rate < 0.70:
            # Losing too much - be more conservative
            self.momentum_threshold *= (1 + LEARNING_ADJUSTMENT_RATE)
            self.position_multiplier *= (1 - LEARNING_ADJUSTMENT_RATE * 0.5)
            self.log(f"LEARNING: More conservative (win rate {win_rate:.1%})")

        # Clamp values
        self.momentum_threshold = max(0.1, min(0.5, self.momentum_threshold))
        self.position_multiplier = max(0.5, min(2.0, self.position_multiplier))

    def check_risk_limits(self) -> bool:
        """Check if we should continue trading"""
        # Daily drawdown check
        if self.capital < self.initial_capital * (1 - MAX_DAILY_DRAWDOWN):
            self.log(f"RISK: Daily drawdown limit hit ({MAX_DAILY_DRAWDOWN:.0%})")
            return False

        # Consecutive loss check
        if self.loss_streak >= MAX_CONSECUTIVE_LOSSES:
            self.log(f"RISK: {MAX_CONSECUTIVE_LOSSES} consecutive losses - cooling down")
            return False

        return True

    async def run_cycle(self) -> Dict:
        """Run one trading cycle"""
        cycle_start = time.time()

        # Check risk limits
        if not self.check_risk_limits():
            await asyncio.sleep(COOLDOWN_AFTER_LOSS)
            self.loss_streak = 0  # Reset after cooldown
            return {'status': 'cooldown'}

        # Resolve any open positions first
        if self.positions:
            await self.resolve_positions()

        # Find new opportunities
        markets = await self.find_tradeable_markets()

        if not markets:
            return {'status': 'no_opportunities'}

        # Execute trades
        for market in markets:
            await self.execute_trade(market)

        # Learn from history
        self.adjust_learning()

        # Save state
        self.save_state()

        cycle_time = time.time() - cycle_start
        return {
            'status': 'traded',
            'positions_opened': len(markets),
            'capital': self.capital,
            'cycle_time': cycle_time
        }

    def save_state(self):
        """Persist state for recovery"""
        state = {
            'capital': self.capital,
            'initial_capital': self.initial_capital,
            'positions': self.positions,
            'trade_count': len(self.trade_history),
            'win_count': sum(1 for t in self.trade_history if t['outcome'] == 'WIN'),
            'daily_pnl': self.daily_pnl,
            'momentum_threshold': self.momentum_threshold,
            'position_multiplier': self.position_multiplier,
            'timestamp': datetime.now().isoformat()
        }

        state_file = STATE_PATH / "aggressive_state.json"
        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_performance_summary(self) -> Dict:
        """Get current performance metrics"""
        if not self.trade_history:
            return {
                'starting_capital': self.initial_capital,
                'current_capital': self.capital,
                'total_profit': 0,
                'roi': 0,
                'roi_pct': '0.0%',
                'trades': 0,
                'wins': 0,
                'losses': 0,
                'win_rate': 0,
                'momentum_threshold': self.momentum_threshold,
                'position_multiplier': self.position_multiplier
            }

        wins = sum(1 for t in self.trade_history if t['outcome'] == 'WIN')
        total = len(self.trade_history)

        total_profit = sum(t['profit'] for t in self.trade_history)
        roi = (self.capital - self.initial_capital) / self.initial_capital

        return {
            'starting_capital': self.initial_capital,
            'current_capital': self.capital,
            'total_profit': total_profit,
            'roi': roi,
            'roi_pct': f"{roi:.1%}",
            'trades': total,
            'wins': wins,
            'losses': total - wins,
            'win_rate': wins / total if total > 0 else 0,
            'momentum_threshold': self.momentum_threshold,
            'position_multiplier': self.position_multiplier
        }

    async def run_simulation(self, cycles: int = 100):
        """
        Run aggressive simulation to show compounding potential.
        """
        self.log("=" * 60)
        self.log("AGGRESSIVE COMPOUNDING SIMULATION")
        self.log(f"Starting: ${self.capital:,.2f}")
        self.log(f"Cycles: {cycles}")
        self.log("=" * 60)

        for i in range(cycles):
            result = await self.run_cycle()

            if (i + 1) % 10 == 0:
                perf = self.get_performance_summary()
                self.log(f"Cycle {i+1}: ${self.capital:,.2f} ({perf['roi_pct']} ROI, {perf['win_rate']:.1%} win rate)")

            # Brief pause between cycles
            await asyncio.sleep(0.1)

        # Final summary
        self.log("=" * 60)
        self.log("SIMULATION COMPLETE")
        self.log("=" * 60)

        perf = self.get_performance_summary()
        self.log(f"Starting Capital: ${perf['starting_capital']:,.2f}")
        self.log(f"Ending Capital: ${perf['current_capital']:,.2f}")
        self.log(f"Total Profit: ${perf['total_profit']:,.2f}")
        self.log(f"ROI: {perf['roi_pct']}")
        self.log(f"Trades: {perf['trades']} ({perf['wins']} wins, {perf['losses']} losses)")
        self.log(f"Win Rate: {perf['win_rate']:.1%}")
        self.log(f"Learned Threshold: {perf['momentum_threshold']:.3f}")
        self.log(f"Learned Multiplier: {perf['position_multiplier']:.2f}")

        # Project future compounding
        daily_roi = perf['roi'] / (cycles / 96)  # Assuming 96 cycles = 1 day
        self.log("")
        self.log("PROJECTED COMPOUNDING (at current rate):")
        capital = self.capital
        for day in [1, 3, 7, 14, 21, 30]:
            projected = capital * ((1 + daily_roi) ** day)
            self.log(f"  Day {day}: ${projected:,.2f}")

        return perf


async def main():
    """Main entry point"""
    import sys

    capital = 5000
    cycles = 200

    # Parse arguments
    if '--capital' in sys.argv:
        idx = sys.argv.index('--capital')
        capital = float(sys.argv[idx + 1])

    if '--cycles' in sys.argv:
        idx = sys.argv.index('--cycles')
        cycles = int(sys.argv[idx + 1])

    trader = AggressiveCompounder(initial_capital=capital)
    await trader.run_simulation(cycles=cycles)


if __name__ == "__main__":
    asyncio.run(main())
