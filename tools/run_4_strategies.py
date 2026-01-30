#!/usr/bin/env python3
"""
4-STRATEGY DEPLOYMENT LAUNCHER
Run all 4 trading strategies simultaneously with unified risk management
"""

import json
import os
import time
from datetime import datetime
from pathlib import Path

# Import strategy modules
from strategy_coordinator import StrategyCoordinator
from strategy_latency_arb import LatencyArbStrategy
from strategy_cross_platform_arb import CrossPlatformArbStrategy
from strategy_high_prob_bonding import HighProbBondingStrategy
from strategy_domain_expertise import DomainExpertiseStrategy


def load_api_keys():
    """Load API keys from secure storage"""
    keys_path = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'

    if os.path.exists(keys_path):
        with open(keys_path) as f:
            return json.load(f)
    else:
        print(f"⚠️  WARNING: API keys not found at {keys_path}")
        return {}


def initialize_strategies(api_keys: dict, base_dir: Path) -> dict:
    """
    Initialize all 4 strategy instances

    Args:
        api_keys: Dict with API keys
        base_dir: Base directory for logs

    Returns:
        Dict of strategy_name -> strategy_instance
    """
    print("\n🔧 INITIALIZING STRATEGIES...")

    strategies = {}

    # Strategy 1: Latency Arbitrage
    print("   [1/4] Latency Arbitrage...")
    strategies['Latency Arb'] = LatencyArbStrategy(
        api_keys=api_keys,
        log_dir=base_dir / 'latency_arb'
    )

    # Strategy 2: Cross-Platform Arbitrage
    print("   [2/4] Cross-Platform Arbitrage...")
    strategies['Cross-Platform Arb'] = CrossPlatformArbStrategy(
        api_keys=api_keys,
        log_dir=base_dir / 'cross_platform_arb'
    )

    # Strategy 3: High-Probability Bonding
    print("   [3/4] High-Probability Bonding...")
    strategies['High-Prob Bonding'] = HighProbBondingStrategy(
        api_keys=api_keys,
        log_dir=base_dir / 'high_prob_bonding'
    )

    # Strategy 4: Domain Expertise
    print("   [4/4] Domain Expertise...")
    strategies['Domain Expertise'] = DomainExpertiseStrategy(
        api_keys=api_keys,
        log_dir=base_dir / 'domain_expertise'
    )

    print("   ✅ All strategies initialized")

    return strategies


def main():
    """Main execution loop"""

    print("="*70)
    print(" " * 15 + "4-STRATEGY POLYMARKET DEPLOYMENT")
    print("="*70)

    # Configuration
    INITIAL_CAPITAL = 600
    CYCLE_INTERVAL_SECONDS = 300  # 5 minutes between cycles

    BASE_DIR = Path('/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL')
    STATE_DIR = BASE_DIR / 'trading_state'

    # Load API keys
    print("\n🔑 Loading API keys...")
    api_keys = load_api_keys()

    # Define strategies configuration
    strategies_config = {
        'Latency Arb': {
            'expected_return': 75,  # 75% monthly
            'win_rate': 0.98,
            'sharpe_ratio': 2.8,
            'allocation_target': 0.25  # 25% of capital
        },
        'Cross-Platform Arb': {
            'expected_return': 20,  # 20% monthly
            'win_rate': 0.99,
            'sharpe_ratio': 3.5,
            'allocation_target': 0.30  # 30% of capital
        },
        'High-Prob Bonding': {
            'expected_return': 12,  # 12% monthly
            'win_rate': 0.97,
            'sharpe_ratio': 2.1,
            'allocation_target': 0.25  # 25% of capital
        },
        'Domain Expertise': {
            'expected_return': 25,  # 25% monthly
            'win_rate': 0.70,
            'sharpe_ratio': 1.9,
            'allocation_target': 0.20  # 20% of capital
        }
    }

    # Initialize coordinator
    print("\n🎯 Initializing Strategy Coordinator...")
    coordinator = StrategyCoordinator(
        initial_capital=INITIAL_CAPITAL,
        strategies_config=strategies_config,
        state_dir=STATE_DIR
    )

    # Initialize strategy instances
    strategies = initialize_strategies(api_keys, BASE_DIR)

    # Register strategies with coordinator
    print("\n📝 Registering strategies...")
    for name, strategy in strategies.items():
        coordinator.register_strategy(name, strategy)

    # Initial portfolio status
    print("\n" + "="*70)
    print("INITIAL PORTFOLIO STATUS")
    print("="*70)
    allocations = coordinator.calculate_allocations()
    print(json.dumps(allocations, indent=2))

    portfolio = coordinator.risk_manager.get_portfolio_status()
    print("\nBankroll: ${:,.2f}".format(portfolio['bankroll']['current']))
    print("Total Return: {}".format(portfolio['bankroll']['total_return']))
    print("Trading Status: {}".format('🟢 ACTIVE' if not portfolio['status']['trading_halted'] else '🔴 HALTED'))

    print("\n" + "="*70)
    print("STARTING TRADING LOOP")
    print("="*70)
    print(f"Cycle Interval: {CYCLE_INTERVAL_SECONDS} seconds ({CYCLE_INTERVAL_SECONDS/60:.0f} minutes)")
    print("Press Ctrl+C to stop")
    print("="*70)

    cycle = 0

    try:
        while True:
            cycle += 1
            cycle_start = datetime.now()

            print(f"\n{'='*70}")
            print(f"CYCLE {cycle} - {cycle_start.strftime('%Y-%m-%d %H:%M:%S')}")
            print("="*70)

            # Run all strategies
            result = coordinator.run_all_strategies()

            # Calculate sleep time
            elapsed = (datetime.now() - cycle_start).total_seconds()
            sleep_time = max(0, CYCLE_INTERVAL_SECONDS - elapsed)

            print(f"\n⏱️  Next cycle in {sleep_time//60:.0f}m {sleep_time%60:.0f}s...")
            print("   (Press Ctrl+C to stop)")

            time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("TRADING STOPPED BY USER")
        print("="*70)

        # Final report
        print("\n📊 FINAL PERFORMANCE REPORT")
        report = coordinator.get_performance_report(lookback_hours=24)
        print(json.dumps(report, indent=2))

        # Save final state
        coordinator.save_state()
        print("\n✅ State saved to disk")

        print("\n👋 Goodbye!")


if __name__ == '__main__':
    main()
