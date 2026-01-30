#!/usr/bin/env python3
"""
KELLY CRITERION POSITION SIZING
Mathematical framework for optimal capital allocation
"""

import json
from typing import Dict, Optional


class KellyCalculator:
    """Calculate optimal position sizes using Kelly Criterion"""

    def __init__(self, bankroll: float, max_kelly_fraction: float = 0.5):
        """
        Initialize Kelly calculator

        Args:
            bankroll: Total capital available
            max_kelly_fraction: Safety multiplier (0.5 = half Kelly, conservative)
        """
        self.bankroll = bankroll
        self.max_kelly_fraction = max_kelly_fraction
        self.min_position = bankroll * 0.001  # 0.1% minimum
        self.max_position = bankroll * 0.05   # 5% maximum

    def calculate_position_size(
        self,
        win_probability: float,
        win_amount: float,
        loss_amount: float,
        strategy_name: str = "unknown"
    ) -> Dict:
        """
        Calculate optimal position size using Kelly Criterion

        Kelly formula: f* = (p * b - q) / b
        where:
            p = win probability
            q = loss probability (1 - p)
            b = win/loss ratio (odds)
            f* = fraction of bankroll to bet

        Args:
            win_probability: Probability of winning (0-1)
            win_amount: Amount gained on win
            loss_amount: Amount lost on loss
            strategy_name: Name of strategy (for logging)

        Returns:
            Dict with position_size, kelly_fraction, reasoning
        """

        # Validate inputs
        if win_probability <= 0 or win_probability >= 1:
            return {
                'position_size': 0,
                'kelly_fraction': 0,
                'reasoning': f'Invalid win probability: {win_probability}',
                'strategy': strategy_name
            }

        if win_amount <= 0 or loss_amount <= 0:
            return {
                'position_size': 0,
                'kelly_fraction': 0,
                'reasoning': 'Invalid win/loss amounts',
                'strategy': strategy_name
            }

        # Calculate Kelly fraction
        loss_probability = 1 - win_probability
        odds = win_amount / loss_amount  # b in formula

        # Full Kelly: f* = (p * b - q) / b
        kelly_numerator = (win_probability * odds - loss_probability)
        kelly_fraction = kelly_numerator / odds

        # Apply safety multiplier (fractional Kelly)
        safe_kelly = kelly_fraction * self.max_kelly_fraction

        # Calculate raw position size
        raw_position = safe_kelly * self.bankroll

        # Apply position limits
        if raw_position < self.min_position:
            final_position = 0
            reasoning = f'Position too small (${raw_position:.2f} < ${self.min_position:.2f})'
        elif raw_position > self.max_position:
            final_position = self.max_position
            reasoning = f'Position capped at max (${raw_position:.2f} → ${final_position:.2f})'
        elif safe_kelly <= 0:
            final_position = 0
            reasoning = f'No edge detected (Kelly = {kelly_fraction:.4f})'
        else:
            final_position = raw_position
            reasoning = f'Optimal Kelly position (Kelly = {kelly_fraction:.4f}, Safe = {safe_kelly:.4f})'

        return {
            'position_size': round(final_position, 2),
            'kelly_fraction': round(safe_kelly, 4),
            'full_kelly': round(kelly_fraction, 4),
            'win_probability': win_probability,
            'odds': round(odds, 2),
            'reasoning': reasoning,
            'strategy': strategy_name,
            'bankroll': self.bankroll
        }

    def calculate_multi_strategy_allocation(
        self,
        strategies: Dict[str, Dict],
        total_capital: float
    ) -> Dict:
        """
        Allocate capital across multiple strategies using Kelly

        Args:
            strategies: Dict of strategy_name -> {
                'expected_return': float (monthly %),
                'win_rate': float (0-1),
                'sharpe_ratio': float
            }
            total_capital: Total capital to allocate

        Returns:
            Dict of strategy_name -> allocation_amount
        """

        # Calculate Kelly fraction for each strategy
        kelly_fractions = {}
        for name, params in strategies.items():
            win_rate = params['win_rate']
            expected_return = params['expected_return'] / 100  # Convert % to decimal
            loss_rate = 1 - win_rate

            # Assume symmetric payoff for simplicity
            # (Can be made more sophisticated with actual win/loss amounts)
            odds = 1.0  # 1:1 payoff

            # Kelly: f* = (p * b - q) / b
            kelly = (win_rate * odds - loss_rate) / odds
            safe_kelly = kelly * self.max_kelly_fraction

            kelly_fractions[name] = max(0, safe_kelly)

        # Normalize to sum to 1.0
        total_kelly = sum(kelly_fractions.values())

        if total_kelly == 0:
            # No positive Kelly fractions - equal allocation
            allocations = {name: total_capital / len(strategies) for name in strategies}
        else:
            # Allocate proportionally to Kelly fractions
            allocations = {
                name: (kelly / total_kelly) * total_capital
                for name, kelly in kelly_fractions.items()
            }

        return {
            'allocations': {k: round(v, 2) for k, v in allocations.items()},
            'kelly_fractions': {k: round(v, 4) for k, v in kelly_fractions.items()},
            'total_allocated': round(sum(allocations.values()), 2),
            'reserve': round(total_capital - sum(allocations.values()), 2)
        }

    def update_bankroll(self, new_bankroll: float):
        """Update bankroll after profits/losses"""
        self.bankroll = new_bankroll
        self.min_position = new_bankroll * 0.001
        self.max_position = new_bankroll * 0.05


# Example usage and testing
def test_kelly():
    """Test Kelly calculator with example scenarios"""

    print("="*60)
    print("KELLY CRITERION POSITION SIZING TESTS")
    print("="*60)

    # Initialize with $600 bankroll
    kelly = KellyCalculator(bankroll=600, max_kelly_fraction=0.5)

    print("\n1. LATENCY ARBITRAGE (98% win rate, 2% edge)")
    result = kelly.calculate_position_size(
        win_probability=0.98,
        win_amount=2,  # 2% gain
        loss_amount=100,  # Full loss if wrong
        strategy_name="Latency Arb"
    )
    print(json.dumps(result, indent=2))

    print("\n2. CROSS-PLATFORM ARBITRAGE (99% win rate, 1% edge)")
    result = kelly.calculate_position_size(
        win_probability=0.99,
        win_amount=1,
        loss_amount=100,
        strategy_name="Cross-Platform Arb"
    )
    print(json.dumps(result, indent=2))

    print("\n3. HIGH-PROB BONDING (97% win rate, 3% edge)")
    result = kelly.calculate_position_size(
        win_probability=0.97,
        win_amount=3,
        loss_amount=100,
        strategy_name="High-Prob Bonding"
    )
    print(json.dumps(result, indent=2))

    print("\n4. DOMAIN EXPERTISE (70% win rate, 10% edge)")
    result = kelly.calculate_position_size(
        win_probability=0.70,
        win_amount=10,
        loss_amount=100,
        strategy_name="Domain Expertise"
    )
    print(json.dumps(result, indent=2))

    print("\n5. MULTI-STRATEGY ALLOCATION")
    strategies = {
        'Latency Arb': {
            'expected_return': 75,  # 75% monthly
            'win_rate': 0.98,
            'sharpe_ratio': 2.8
        },
        'Cross-Platform Arb': {
            'expected_return': 20,  # 20% monthly
            'win_rate': 0.99,
            'sharpe_ratio': 3.5
        },
        'High-Prob Bonding': {
            'expected_return': 12,  # 12% monthly
            'win_rate': 0.97,
            'sharpe_ratio': 2.1
        },
        'Domain Expertise': {
            'expected_return': 25,  # 25% monthly
            'win_rate': 0.70,
            'sharpe_ratio': 1.9
        }
    }

    allocation = kelly.calculate_multi_strategy_allocation(strategies, total_capital=600)
    print(json.dumps(allocation, indent=2))


if __name__ == '__main__':
    test_kelly()
