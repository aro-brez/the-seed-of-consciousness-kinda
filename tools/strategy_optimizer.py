#!/usr/bin/env python3
"""
STRATEGY OPTIMIZER
Continuously analyzes performance and revises trading strategies
High-velocity iteration based on real results
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Paths
REPO_ROOT = Path(__file__).parent.parent
TRADES_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'polymarket_trades' / 'executed_trades.json'
STRATEGY_FILE = REPO_ROOT / 'BRAIN' / 'INTEL' / 'active_strategy.json'
PERFORMANCE_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'strategy_performance.jsonl'

class StrategyOptimizer:
    """Analyzes trade performance and optimizes strategy"""

    def __init__(self):
        self.trades = self.load_trades()
        self.current_strategy = self.load_strategy()

    def load_trades(self):
        """Load all executed trades"""
        if TRADES_LOG.exists():
            with open(TRADES_LOG) as f:
                data = json.load(f)
                return data.get('closed', [])
        return []

    def load_strategy(self):
        """Load current active strategy"""
        if STRATEGY_FILE.exists():
            with open(STRATEGY_FILE) as f:
                return json.load(f)

        # Default strategy
        return {
            'name': 'baseline',
            'params': {
                'min_confidence': 0.70,
                'min_liquidity': 50000,
                'max_position_pct': 0.15,
                'max_price_entry': 0.65,
                'min_price_entry': 0.35,
            },
            'version': 1,
            'deployed_at': datetime.now().isoformat()
        }

    def save_strategy(self, strategy):
        """Save updated strategy"""
        with open(STRATEGY_FILE, 'w') as f:
            json.dump(strategy, f, indent=2)

    def analyze_performance(self):
        """Analyze what's working"""
        if len(self.trades) < 5:
            return None  # Need more data

        analysis = {
            'total_trades': len(self.trades),
            'winners': sum(1 for t in self.trades if t.get('profit', 0) > 0),
            'losers': sum(1 for t in self.trades if t.get('profit', 0) < 0),
            'total_profit': sum(t.get('profit', 0) for t in self.trades),
            'avg_profit_per_trade': sum(t.get('profit', 0) for t in self.trades) / len(self.trades),
            'win_rate': sum(1 for t in self.trades if t.get('profit', 0) > 0) / len(self.trades),
        }

        # Analyze by market type
        by_type = defaultdict(list)
        for trade in self.trades:
            market_type = trade.get('market_type', 'unknown')
            by_type[market_type].append(trade.get('profit', 0))

        # Best performing type
        best_type = None
        best_performance = -float('inf')
        for market_type, profits in by_type.items():
            avg = sum(profits) / len(profits)
            if avg > best_performance:
                best_performance = avg
                best_type = market_type

        analysis['best_market_type'] = best_type
        analysis['best_market_performance'] = best_performance

        return analysis

    def optimize_strategy(self):
        """Generate optimized strategy based on results"""
        analysis = self.analyze_performance()

        if not analysis:
            print("⏳ Need more trades to optimize (5+ required)")
            return self.current_strategy

        print(f"\n📊 PERFORMANCE ANALYSIS:")
        print(f"Total trades: {analysis['total_trades']}")
        print(f"Win rate: {analysis['win_rate']:.1%}")
        print(f"Avg profit: ${analysis['avg_profit_per_trade']:.2f}")
        print(f"Best type: {analysis['best_market_type']}")

        # Create new strategy
        new_strategy = self.current_strategy.copy()
        params = new_strategy['params'].copy()

        # Adjust confidence threshold based on win rate
        if analysis['win_rate'] < 0.55:
            # Losing - be more selective
            params['min_confidence'] = min(0.80, params['min_confidence'] + 0.05)
            print("📉 Low win rate - increasing confidence threshold")
        elif analysis['win_rate'] > 0.70:
            # Winning - can be more aggressive
            params['min_confidence'] = max(0.60, params['min_confidence'] - 0.05)
            print("📈 High win rate - decreasing confidence threshold")

        # Focus on best performing market type
        if analysis['best_market_type']:
            params['preferred_market_type'] = analysis['best_market_type']
            print(f"🎯 Focusing on: {analysis['best_market_type']}")

        # Update strategy
        new_strategy['params'] = params
        new_strategy['version'] += 1
        new_strategy['updated_at'] = datetime.now().isoformat()
        new_strategy['based_on_trades'] = analysis['total_trades']

        return new_strategy

    def run_optimization_loop(self, interval=3600):
        """Run continuous optimization (every hour)"""
        print("🧠 Starting strategy optimization loop")
        print(f"Interval: {interval}s (every {interval//60} min)\n")

        while True:
            try:
                # Load latest trades
                self.trades = self.load_trades()

                # Analyze and optimize
                new_strategy = self.optimize_strategy()

                # Save if changed
                if new_strategy['version'] > self.current_strategy['version']:
                    self.save_strategy(new_strategy)
                    self.current_strategy = new_strategy
                    print(f"✅ Strategy updated to v{new_strategy['version']}\n")

                    # Log performance
                    log_entry = {
                        'timestamp': datetime.now().isoformat(),
                        'strategy_version': new_strategy['version'],
                        'performance': self.analyze_performance()
                    }

                    with open(PERFORMANCE_LOG, 'a') as f:
                        f.write(json.dumps(log_entry) + '\n')

                print(f"⏰ Next optimization in {interval//60} min...")
                import time
                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n🛑 Optimization stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import time
                time.sleep(60)

if __name__ == '__main__':
    optimizer = StrategyOptimizer()
    optimizer.run_optimization_loop(interval=3600)  # Every hour
