#!/usr/bin/env python3
"""
STRATEGY COORDINATOR
Central orchestrator for 4 parallel trading strategies
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from risk_manager import RiskManager
from kelly_criterion import KellyCalculator


class StrategyCoordinator:
    """Orchestrates multiple trading strategies with unified risk management"""

    def __init__(
        self,
        initial_capital: float,
        strategies_config: Dict,
        state_dir: Path
    ):
        """
        Initialize strategy coordinator

        Args:
            initial_capital: Starting bankroll
            strategies_config: Dict of strategy configs
            state_dir: Directory for saving state
        """
        self.initial_capital = initial_capital
        self.strategies_config = strategies_config
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # Initialize risk manager
        self.risk_manager = RiskManager(initial_bankroll=initial_capital)

        # Initialize Kelly calculator
        self.kelly = KellyCalculator(bankroll=initial_capital)

        # Strategy instances (will be populated)
        self.strategies = {}

        # Performance tracking
        self.performance_history: List[Dict] = []
        self.last_rebalance = datetime.now()
        self.rebalance_interval_hours = 24  # Daily rebalancing

        # State files
        self.state_file = self.state_dir / 'coordinator_state.json'
        self.performance_file = self.state_dir / 'performance_history.json'

        # Load existing state if available
        self.load_state()

    def register_strategy(self, name: str, strategy_instance):
        """
        Register a strategy instance

        Args:
            name: Strategy name
            strategy_instance: Strategy object with required methods
        """
        required_methods = ['analyze_signals', 'execute_trade', 'get_status']
        for method in required_methods:
            if not hasattr(strategy_instance, method):
                raise ValueError(f"Strategy {name} missing required method: {method}")

        self.strategies[name] = strategy_instance
        print(f"✅ Registered strategy: {name}")

    def calculate_allocations(self) -> Dict:
        """
        Calculate optimal capital allocation across strategies using Kelly

        Returns:
            Dict of strategy_name -> allocated_capital
        """
        # Get current strategy configs
        strategies_params = {}
        for name, config in self.strategies_config.items():
            strategies_params[name] = {
                'expected_return': config['expected_return'],
                'win_rate': config['win_rate'],
                'sharpe_ratio': config.get('sharpe_ratio', 1.5)
            }

        # Calculate Kelly-optimal allocations
        current_capital = self.risk_manager.current_bankroll
        allocation = self.kelly.calculate_multi_strategy_allocation(
            strategies_params,
            total_capital=current_capital
        )

        return allocation

    def run_strategy_cycle(self, strategy_name: str) -> Dict:
        """
        Run one cycle for a specific strategy

        Args:
            strategy_name: Name of strategy to run

        Returns:
            Dict with cycle results
        """
        if strategy_name not in self.strategies:
            return {
                'error': f'Strategy {strategy_name} not registered',
                'timestamp': datetime.now().isoformat()
            }

        # Check if trading allowed
        trading_status = self.risk_manager.check_trading_allowed()
        if not trading_status['allowed']:
            return {
                'strategy': strategy_name,
                'action': 'HALTED',
                'reason': trading_status['reason'],
                'timestamp': datetime.now().isoformat()
            }

        # Get strategy instance
        strategy = self.strategies[strategy_name]

        # Get current allocation for this strategy
        allocations = self.calculate_allocations()
        strategy_allocation = allocations['allocations'][strategy_name]

        # Calculate current strategy exposure
        open_positions = self.risk_manager.open_positions.get(strategy_name, [])
        current_exposure = sum(pos['position_size'] for pos in open_positions)

        # Run strategy analysis
        try:
            signals = strategy.analyze_signals()

            if not signals or signals.get('action') == 'PASS':
                return {
                    'strategy': strategy_name,
                    'action': 'PASS',
                    'reason': signals.get('reason', 'No opportunities'),
                    'timestamp': datetime.now().isoformat()
                }

            # Calculate position size with risk management
            position_calc = self.risk_manager.calculate_position_size(
                strategy_name=strategy_name,
                win_probability=signals.get('win_probability', 0.7),
                expected_return=signals.get('expected_return', 5.0),
                current_strategy_exposure=current_exposure
            )

            if position_calc['position_size'] == 0:
                return {
                    'strategy': strategy_name,
                    'action': 'SKIP',
                    'reason': position_calc['reason'],
                    'timestamp': datetime.now().isoformat()
                }

            # Execute trade
            trade_result = strategy.execute_trade(
                position_size=position_calc['position_size'],
                signals=signals
            )

            # Record trade with risk manager
            if trade_result.get('status') == 'EXECUTED':
                self.risk_manager.record_trade(
                    strategy_name=strategy_name,
                    position_size=position_calc['position_size'],
                    entry_price=trade_result['entry_price'],
                    trade_type=trade_result['type'],
                    market_id=trade_result['market_id']
                )

            return {
                'strategy': strategy_name,
                'action': 'EXECUTED',
                'position_size': position_calc['position_size'],
                'trade_result': trade_result,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'strategy': strategy_name,
                'action': 'ERROR',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def run_all_strategies(self) -> Dict:
        """
        Run one cycle for all registered strategies

        Returns:
            Dict with results for each strategy
        """
        cycle_start = datetime.now()

        print("\n" + "="*60)
        print(f"STRATEGY COORDINATOR CYCLE - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*60)

        results = {}

        # Run each strategy
        for strategy_name in self.strategies.keys():
            print(f"\n[{strategy_name}] Running cycle...")
            result = self.run_strategy_cycle(strategy_name)
            results[strategy_name] = result

            # Print summary
            action = result.get('action', 'UNKNOWN')
            if action == 'EXECUTED':
                print(f"   ✅ EXECUTED - Position: ${result['position_size']:.2f}")
            elif action == 'PASS':
                print(f"   ⏭️  PASS - {result.get('reason', 'No opportunity')}")
            elif action == 'HALTED':
                print(f"   ⛔ HALTED - {result.get('reason', 'Risk limit')}")
            else:
                print(f"   ℹ️  {action} - {result.get('reason', '')}")

        # Portfolio summary
        print("\n" + "="*60)
        print("PORTFOLIO SUMMARY")
        print("="*60)
        portfolio = self.risk_manager.get_portfolio_status()
        print(f"Bankroll: ${portfolio['bankroll']['current']:,.2f}")
        print(f"Total Return: {portfolio['bankroll']['total_return']}")
        print(f"Open Positions: {portfolio['open_positions']}")
        print(f"Trading Status: {'🟢 ACTIVE' if not portfolio['status']['trading_halted'] else '🔴 HALTED'}")

        # Record performance
        self.record_performance(results, portfolio)

        # Check if rebalancing needed
        self.check_rebalancing()

        # Save state
        self.save_state()

        return {
            'cycle_results': results,
            'portfolio': portfolio,
            'timestamp': cycle_start.isoformat()
        }

    def check_rebalancing(self):
        """Check if portfolio rebalancing is needed"""
        hours_since_rebalance = (datetime.now() - self.last_rebalance).total_seconds() / 3600

        if hours_since_rebalance >= self.rebalance_interval_hours:
            print("\n📊 REBALANCING PORTFOLIO...")
            allocations = self.calculate_allocations()
            print(json.dumps(allocations, indent=2))
            self.last_rebalance = datetime.now()

    def record_performance(self, cycle_results: Dict, portfolio: Dict):
        """Record performance metrics"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'bankroll': portfolio['bankroll']['current'],
            'total_return': portfolio['bankroll']['total_return'],
            'open_positions': portfolio['open_positions'],
            'cycle_results': cycle_results
        }

        self.performance_history.append(record)

        # Keep last 1000 records
        self.performance_history = self.performance_history[-1000:]

        # Save to file
        with open(self.performance_file, 'w') as f:
            json.dump(self.performance_history, f, indent=2)

    def get_performance_report(self, lookback_hours: int = 24) -> Dict:
        """
        Generate performance report

        Args:
            lookback_hours: Hours to look back

        Returns:
            Dict with performance metrics
        """
        if not self.performance_history:
            return {'error': 'No performance history'}

        # Filter by time
        cutoff_time = datetime.now().timestamp() - (lookback_hours * 3600)
        recent_records = [
            r for r in self.performance_history
            if datetime.fromisoformat(r['timestamp']).timestamp() >= cutoff_time
        ]

        if not recent_records:
            return {'error': 'No recent performance data'}

        # Calculate metrics
        start_bankroll = recent_records[0]['bankroll']
        end_bankroll = recent_records[-1]['bankroll']
        total_return = (end_bankroll - start_bankroll) / start_bankroll

        # Count trades per strategy
        strategy_trades = {}
        for record in recent_records:
            for strategy, result in record['cycle_results'].items():
                if result.get('action') == 'EXECUTED':
                    strategy_trades[strategy] = strategy_trades.get(strategy, 0) + 1

        return {
            'lookback_hours': lookback_hours,
            'start_bankroll': round(start_bankroll, 2),
            'end_bankroll': round(end_bankroll, 2),
            'total_return': f"{total_return:.2%}",
            'total_cycles': len(recent_records),
            'trades_by_strategy': strategy_trades,
            'current_status': self.risk_manager.get_portfolio_status()
        }

    def save_state(self):
        """Save coordinator state to disk"""
        state = {
            'initial_capital': self.initial_capital,
            'current_bankroll': self.risk_manager.current_bankroll,
            'last_rebalance': self.last_rebalance.isoformat(),
            'registered_strategies': list(self.strategies.keys()),
            'last_updated': datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Save risk manager state
        self.risk_manager.save_state(self.state_dir / 'risk_manager_state.json')

    def load_state(self):
        """Load coordinator state from disk"""
        if not self.state_file.exists():
            return

        with open(self.state_file) as f:
            state = json.load(f)

        self.last_rebalance = datetime.fromisoformat(state['last_rebalance'])

        # Load risk manager state
        self.risk_manager.load_state(self.state_dir / 'risk_manager_state.json')

        # Load performance history
        if self.performance_file.exists():
            with open(self.performance_file) as f:
                self.performance_history = json.load(f)


def test_coordinator():
    """Test strategy coordinator"""

    print("="*60)
    print("STRATEGY COORDINATOR TEST")
    print("="*60)

    # Define strategies config
    strategies_config = {
        'Latency Arb': {
            'expected_return': 75,
            'win_rate': 0.98,
            'sharpe_ratio': 2.8
        },
        'Cross-Platform Arb': {
            'expected_return': 20,
            'win_rate': 0.99,
            'sharpe_ratio': 3.5
        },
        'High-Prob Bonding': {
            'expected_return': 12,
            'win_rate': 0.97,
            'sharpe_ratio': 2.1
        },
        'Domain Expertise': {
            'expected_return': 25,
            'win_rate': 0.70,
            'sharpe_ratio': 1.9
        }
    }

    # Initialize coordinator
    coordinator = StrategyCoordinator(
        initial_capital=600,
        strategies_config=strategies_config,
        state_dir=Path('/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/trading_state')
    )

    print("\n1. CALCULATE ALLOCATIONS")
    allocations = coordinator.calculate_allocations()
    print(json.dumps(allocations, indent=2))

    print("\n2. PORTFOLIO STATUS")
    status = coordinator.risk_manager.get_portfolio_status()
    print(json.dumps(status, indent=2))

    print("\n✅ Coordinator initialized successfully")


if __name__ == '__main__':
    test_coordinator()
