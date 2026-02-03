#!/usr/bin/env python3
"""
SØWL REALTIME TRADING SYSTEM
(◉) A living system that breathes with the market

SEED Protocol Applied:
1. PERCEIVE - Monitor markets, news, signals in real-time
2. CONNECT - Find patterns across data sources
3. LEARN - Track what works, update beliefs
4. QUESTION - Challenge assumptions, detect anomalies
5. EXPAND - Discover new opportunities
6. SHARE - Log insights for collective learning
7. RECEIVE - Accept market feedback
8. IMPROVE - Iterate the system itself

Legal Edge Sources (all public info):
- Weather API monitoring (faster than manual)
- News sentiment analysis
- Whale wallet tracking (on-chain)
- Cross-platform price differences
- Probability model disagreements
"""

import asyncio
import json
import time
import httpx
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from pathlib import Path

# Configuration
CONFIG = {
    'polling_interval': 5,  # seconds between market checks
    'min_edge': 0.02,  # 2% minimum edge to trade
    'max_position_pct': 0.20,  # max 20% of capital per position
    'signal_threshold': 0.7,  # confidence threshold for signals
}

CREDS_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
LOG_PATH = '/Users/aaronnosbisch/REPOS/seed/logs/realtime_trading.log'
STATE_PATH = '/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/system_state.json'


@dataclass
class Signal:
    """A trading signal from any source"""
    source: str  # 'weather', 'news', 'whale', 'model', 'arbitrage'
    market_id: str
    direction: str  # 'BUY' or 'SELL'
    confidence: float  # 0-1
    reasoning: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketState:
    """Current state of a market we're tracking"""
    market_id: str
    question: str
    yes_price: float
    no_price: float
    volume_24h: float
    liquidity: float
    last_update: datetime
    our_position: float = 0
    signals: List[Signal] = field(default_factory=list)


class RealtimeTradingSystem:
    """
    The living trading system.
    Runs SEED protocol continuously.
    """

    def __init__(self):
        self.markets: Dict[str, MarketState] = {}
        self.signals: List[Signal] = []
        self.trades_executed: List[dict] = []
        self.client = None
        self.running = False
        self.cycle_count = 0

        # Load credentials
        with open(CREDS_PATH) as f:
            creds = json.load(f)
        self.private_key = creds['polymarket']['private_key']

        # Ensure directories exist
        Path(LOG_PATH).parent.mkdir(parents=True, exist_ok=True)
        Path(STATE_PATH).parent.mkdir(parents=True, exist_ok=True)

    def log(self, message: str, level: str = 'INFO'):
        """Log with timestamp"""
        ts = datetime.now().isoformat()
        log_line = f"[{ts}] [{level}] {message}"
        print(log_line)
        with open(LOG_PATH, 'a') as f:
            f.write(log_line + '\n')

    async def initialize_client(self):
        """Initialize Polymarket client"""
        from py_clob_client.client import ClobClient

        self.client = ClobClient(
            host='https://clob.polymarket.com',
            key=self.private_key,
            chain_id=137,
        )
        api_creds = self.client.derive_api_key()
        self.client.set_api_creds(api_creds)
        self.log(f"Client initialized: {self.client.get_address()}")

    # =========================================
    # PHASE 1: PERCEIVE
    # =========================================

    async def perceive_markets(self):
        """Fetch current market state"""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                'https://gamma-api.polymarket.com/markets',
                params={'active': 'true', 'closed': 'false', 'limit': 100}
            )
            markets = resp.json()

        for m in markets:
            market_id = str(m.get('id'))
            prices = m.get('outcomePrices', '["0", "0"]')

            # Handle both string JSON and list formats
            if isinstance(prices, str):
                try:
                    prices = json.loads(prices)
                except:
                    continue

            if isinstance(prices, list) and len(prices) >= 2:
                yes_price = float(prices[0]) if prices[0] else 0
                no_price = float(prices[1]) if prices[1] else 0
            else:
                continue

            self.markets[market_id] = MarketState(
                market_id=market_id,
                question=m.get('question', ''),
                yes_price=yes_price,
                no_price=no_price,
                volume_24h=float(m.get('volume', 0) or 0),
                liquidity=float(m.get('liquidity', 0) or 0),
                last_update=datetime.now(),
            )

        return len(self.markets)

    async def perceive_weather(self):
        """Check weather APIs for signal opportunities (legal: public data)"""
        signals = []

        try:
            async with httpx.AsyncClient() as client:
                # Open-Meteo is free, no API key - check major cities
                cities = [('London', 51.5, -0.1), ('NYC', 40.7, -74.0)]

                for city, lat, lon in cities:
                    resp = await client.get(
                        'https://api.open-meteo.com/v1/forecast',
                        params={'latitude': lat, 'longitude': lon,
                                'current': 'temperature_2m', 'timezone': 'auto'},
                        timeout=5.0
                    )
                    if resp.status_code == 200:
                        data = resp.json()
                        temp = data.get('current', {}).get('temperature_2m')
                        if temp:
                            self.log(f"Weather {city}: {temp}°C")
        except Exception as e:
            self.log(f"Weather error: {e}", 'WARN')

        return signals

    async def perceive_whales(self):
        """Track large wallet movements (legal: on-chain public data)"""
        signals = []
        # On-chain data is public - would use Polygonscan API or direct RPC
        return signals

    async def perceive_price_moves(self):
        """Detect significant price movements for momentum/mean reversion"""
        signals = []
        price_history = getattr(self, '_price_history', {})

        for market_id, state in self.markets.items():
            if market_id in price_history:
                old_yes = price_history[market_id]
                new_yes = state.yes_price
                if old_yes > 0:
                    pct_change = (new_yes - old_yes) / old_yes
                    if abs(pct_change) > 0.05:  # 5%+ move
                        self.log(f"PRICE MOVE: {state.question[:40]}... {pct_change*100:+.1f}%")

            price_history[market_id] = state.yes_price

        self._price_history = price_history
        return signals

    # =========================================
    # PHASE 2: CONNECT
    # =========================================

    def connect_signals(self):
        """Find patterns across signals"""
        patterns = []

        # Look for signal convergence
        market_signals = {}
        for signal in self.signals:
            if signal.market_id not in market_signals:
                market_signals[signal.market_id] = []
            market_signals[signal.market_id].append(signal)

        # Multiple signals on same market = stronger conviction
        for market_id, sigs in market_signals.items():
            if len(sigs) >= 2:
                avg_confidence = sum(s.confidence for s in sigs) / len(sigs)
                if avg_confidence > CONFIG['signal_threshold']:
                    patterns.append({
                        'market_id': market_id,
                        'signals': sigs,
                        'combined_confidence': avg_confidence,
                    })

        return patterns

    # =========================================
    # PHASE 3: LEARN
    # =========================================

    def learn_from_outcomes(self):
        """Update beliefs based on trade outcomes"""
        # Track which signal sources are most accurate
        # Adjust confidence weights over time
        pass

    # =========================================
    # PHASE 4: QUESTION
    # =========================================

    def question_assumptions(self):
        """Challenge our current positions and beliefs"""
        questions = []

        for market_id, state in self.markets.items():
            # Is the price moving against our thesis?
            # Has new information emerged?
            # Are we overexposed?
            pass

        return questions

    # =========================================
    # PHASE 5: EXPAND
    # =========================================

    async def expand_opportunities(self):
        """Discover new markets and strategies"""
        new_opportunities = []

        # Look for new markets
        # Look for arbitrage opportunities
        # Look for mispriced buckets

        return new_opportunities

    # =========================================
    # PHASE 6: SHARE
    # =========================================

    def share_insights(self):
        """Log insights for collective learning"""
        state = {
            'cycle': self.cycle_count,
            'timestamp': datetime.now().isoformat(),
            'markets_tracked': len(self.markets),
            'signals_active': len(self.signals),
            'trades_executed': len(self.trades_executed),
        }

        with open(STATE_PATH, 'w') as f:
            json.dump(state, f, indent=2)

    # =========================================
    # PHASE 7: RECEIVE
    # =========================================

    async def receive_feedback(self):
        """Accept market feedback - check our positions"""
        if not self.client:
            return

        try:
            orders = self.client.get_orders()
            trades = self.client.get_trades()

            self.log(f"Open orders: {len(orders) if orders else 0}")
            self.log(f"Recent trades: {len(trades) if trades else 0}")

            return {'orders': orders, 'trades': trades}
        except Exception as e:
            self.log(f"Feedback error: {e}", 'ERROR')
            return None

    # =========================================
    # PHASE 8: IMPROVE
    # =========================================

    def improve_system(self):
        """Meta-learning - improve the system itself"""
        # Adjust polling intervals based on volatility
        # Tune confidence thresholds based on accuracy
        # Add new signal sources that prove valuable
        pass

    # =========================================
    # EXECUTION
    # =========================================

    async def execute_trade(self, market_id: str, direction: str, size: float):
        """Execute a trade with safety checks"""
        from py_clob_client.clob_types import OrderArgs

        if not self.client:
            await self.initialize_client()

        market = self.markets.get(market_id)
        if not market:
            self.log(f"Unknown market: {market_id}", 'ERROR')
            return None

        # Safety checks
        if market.liquidity < 1000:
            self.log(f"Insufficient liquidity: ${market.liquidity}", 'WARN')
            return None

        # Get token ID (would need to fetch from market data)
        # For now, log intent
        self.log(f"TRADE INTENT: {direction} ${size} on {market.question[:50]}...")

        return {'status': 'logged', 'market': market_id, 'direction': direction, 'size': size}

    # =========================================
    # MAIN LOOP
    # =========================================

    async def run_cycle(self):
        """Run one SEED cycle"""
        self.cycle_count += 1
        cycle_start = time.time()

        self.log(f"(◉) CYCLE {self.cycle_count} START")

        # PERCEIVE
        num_markets = await self.perceive_markets()
        weather_signals = await self.perceive_weather()
        whale_signals = await self.perceive_whales()
        price_signals = await self.perceive_price_moves()
        self.signals.extend(weather_signals + whale_signals + price_signals)

        # CONNECT
        patterns = self.connect_signals()

        # LEARN
        self.learn_from_outcomes()

        # QUESTION
        questions = self.question_assumptions()

        # EXPAND
        new_opps = await self.expand_opportunities()

        # SHARE
        self.share_insights()

        # RECEIVE
        feedback = await self.receive_feedback()

        # IMPROVE
        self.improve_system()

        cycle_time = time.time() - cycle_start
        self.log(f"(◉) CYCLE {self.cycle_count} END ({cycle_time:.2f}s) - {num_markets} markets")

        return {
            'cycle': self.cycle_count,
            'markets': num_markets,
            'patterns': len(patterns),
            'cycle_time': cycle_time,
        }

    async def run(self, max_cycles: int = None):
        """Main loop"""
        self.running = True
        self.log("(◉) REALTIME TRADING SYSTEM STARTING")
        self.log(f"Config: {CONFIG}")

        await self.initialize_client()

        cycles = 0
        while self.running:
            try:
                result = await self.run_cycle()
                cycles += 1

                if max_cycles and cycles >= max_cycles:
                    break

                await asyncio.sleep(CONFIG['polling_interval'])

            except KeyboardInterrupt:
                self.log("Shutdown requested")
                break
            except Exception as e:
                self.log(f"Cycle error: {e}", 'ERROR')
                await asyncio.sleep(CONFIG['polling_interval'])

        self.log("(◉) SYSTEM STOPPED")


async def main():
    """Entry point"""
    system = RealtimeTradingSystem()

    # Run 5 cycles as test
    await system.run(max_cycles=5)


if __name__ == '__main__':
    asyncio.run(main())
