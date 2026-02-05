#!/usr/bin/env python3
"""
ENHANCED POSITION SIZING FOR JOULE TRADING BOT
Sophisticated Kelly-based position sizing with volatility adjustment
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from kelly_criterion import KellyCalculator


class EnhancedPositionSizer:
    """Advanced position sizing with Kelly Criterion and risk adjustments"""
    
    def __init__(self, initial_bankroll: float = 500.0):
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.kelly_calculator = KellyCalculator(
            bankroll=initial_bankroll,
            max_kelly_fraction=0.25  # Quarter Kelly for safety
        )
        
        # Volatility adjustments by strategy type
        self.strategy_volatility = {
            'high_prob_bonds': 0.8,    # Low vol - 95%+ win rate
            'arbitrage': 0.9,          # Very low vol - near guaranteed
            'cross_platform_arb': 0.9, 
            'whale_tracking': 0.6,     # Higher vol - following whales
            'sentiment_momentum': 0.5,  # High vol - sentiment driven
            'domain_expertise': 0.7,   # Med vol - subject matter edge
            'default': 0.7
        }
        
        # Category risk multipliers
        self.category_risk = {
            'crypto': 1.2,      # Higher volatility
            'sports': 0.8,      # More predictable
            'politics': 1.0,    # Baseline
            'tech': 1.1,        # Tech volatility
            'elon_doge': 1.5,   # Meme volatility
            'other': 1.0
        }
        
        # Performance tracking for dynamic adjustment
        self.strategy_performance = {}
        self.recent_trades = []
        
    def calculate_optimal_size(self, 
                             opportunity: Dict,
                             current_exposure: float = 0,
                             category: str = 'other') -> Dict:
        """
        Calculate optimal position size using enhanced Kelly with volatility adjustment
        
        Args:
            opportunity: Dict with type, ev, confidence, strategy, price, side
            current_exposure: Current $ exposure in this category
            category: Market category for risk adjustment
            
        Returns:
            Dict with position_size, reasoning, risk_metrics
        """
        
        # Extract opportunity parameters
        strategy_type = opportunity.get('strategy', 'default')
        expected_value = opportunity.get('ev', 0)
        confidence = opportunity.get('confidence', 0.5)
        market_price = opportunity.get('price', 0.5)
        
        # Convert confidence to win probability with strategy adjustment
        base_win_prob = confidence
        
        # Strategy-specific adjustments
        if strategy_type == 'high_prob_bonds':
            # High confidence in 95%+ markets
            win_prob = max(0.95, confidence)
        elif strategy_type in ['arbitrage', 'cross_platform_arb']:
            # Near-certain arbitrage
            win_prob = max(0.98, confidence)
        elif strategy_type == 'whale_tracking':
            # Conservative whale following
            win_prob = min(0.60, confidence + 0.05)
        else:
            win_prob = confidence
            
        # Calculate expected return based on market structure
        if strategy_type == 'high_prob_bonds':
            # Betting on 95%+ side, small edge but high probability
            if market_price > 0.95:  # Betting YES on 95%+ market
                potential_return = (1 - market_price) / market_price * 100  # % return
                loss_amount = 100  # Full stake if wrong
            else:  # Betting NO on <5% market  
                potential_return = market_price / (1 - market_price) * 100
                loss_amount = 100
        elif strategy_type in ['arbitrage', 'cross_platform_arb']:
            # Spread capture - guaranteed return
            potential_return = expected_value  # Direct EV
            loss_amount = 1  # Minimal loss risk
        else:
            # General case - use EV as return estimate
            potential_return = expected_value if expected_value > 0 else 5
            loss_amount = 100
            
        # Kelly calculation
        kelly_result = self.kelly_calculator.calculate_position_size(
            win_probability=win_prob,
            win_amount=potential_return,
            loss_amount=loss_amount,
            strategy_name=strategy_type
        )
        
        base_size = kelly_result['position_size']
        
        # Apply volatility adjustment
        vol_multiplier = self.strategy_volatility.get(strategy_type, 0.7)
        volatility_adjusted = base_size * vol_multiplier
        
        # Apply category risk adjustment
        risk_multiplier = self.category_risk.get(category, 1.0)
        risk_adjusted = volatility_adjusted * risk_multiplier
        
        # Performance-based dynamic adjustment
        perf_multiplier = self._get_performance_multiplier(strategy_type)
        performance_adjusted = risk_adjusted * perf_multiplier
        
        # Final safety caps
        max_single_position = self.current_bankroll * 0.10  # 10% max
        min_position = 5.0  # $5 minimum
        
        final_size = max(min_position, 
                        min(performance_adjusted, max_single_position))
        
        # Reasoning
        reasoning = self._generate_sizing_reasoning(
            kelly_result, vol_multiplier, risk_multiplier, 
            perf_multiplier, final_size, base_size
        )
        
        return {
            'position_size': round(final_size, 2),
            'kelly_optimal': round(base_size, 2),
            'volatility_multiplier': vol_multiplier,
            'risk_multiplier': risk_multiplier,
            'performance_multiplier': perf_multiplier,
            'win_probability': round(win_prob, 3),
            'expected_return': round(potential_return, 2),
            'reasoning': reasoning,
            'confidence_level': 'HIGH' if win_prob > 0.8 else 'MEDIUM' if win_prob > 0.6 else 'LOW',
            'risk_metrics': {
                'max_loss': round(final_size, 2),
                'expected_profit': round(final_size * potential_return / 100 * win_prob, 2),
                'risk_reward_ratio': round(potential_return / 100, 2)
            }
        }
    
    def _get_performance_multiplier(self, strategy_type: str) -> float:
        """Calculate performance-based sizing adjustment"""
        if strategy_type not in self.strategy_performance:
            return 1.0  # Neutral for new strategies
            
        perf = self.strategy_performance[strategy_type]
        win_rate = perf.get('win_rate', 0.5)
        total_trades = perf.get('total_trades', 0)
        
        # Need minimum sample size
        if total_trades < 5:
            return 1.0
            
        # Scale up on strong performance
        if win_rate > 0.70:
            return min(1.5, 1.0 + (win_rate - 0.70) * 2)  # Up to 1.5x
        elif win_rate < 0.40:
            return max(0.5, win_rate / 0.40)  # Scale down to 0.5x
        else:
            return 1.0  # Neutral
            
    def _generate_sizing_reasoning(self, kelly_result: Dict, vol_mult: float, 
                                 risk_mult: float, perf_mult: float, 
                                 final_size: float, base_size: float) -> str:
        """Generate human-readable reasoning"""
        parts = []
        parts.append(f"Kelly: ${base_size:.0f}")
        
        if vol_mult != 1.0:
            parts.append(f"Vol adj: {vol_mult:.1f}x")
        if risk_mult != 1.0:
            parts.append(f"Risk adj: {risk_mult:.1f}x")
        if perf_mult != 1.0:
            parts.append(f"Perf adj: {perf_mult:.1f}x")
            
        if final_size != base_size * vol_mult * risk_mult * perf_mult:
            parts.append("Safety capped")
            
        return " | ".join(parts)
    
    def update_performance(self, strategy_type: str, trade_result: Dict):
        """Update strategy performance tracking"""
        if strategy_type not in self.strategy_performance:
            self.strategy_performance[strategy_type] = {
                'total_trades': 0,
                'wins': 0,
                'total_pnl': 0,
                'win_rate': 0
            }
            
        perf = self.strategy_performance[strategy_type]
        perf['total_trades'] += 1
        
        if trade_result.get('won', False):
            perf['wins'] += 1
            
        perf['total_pnl'] += trade_result.get('pnl', 0)
        perf['win_rate'] = perf['wins'] / perf['total_trades']
        
        # Track recent trades for dynamic adjustment
        self.recent_trades.append({
            'strategy': strategy_type,
            'result': trade_result,
            'timestamp': datetime.now()
        })
        
        # Keep only last 50 trades
        if len(self.recent_trades) > 50:
            self.recent_trades = self.recent_trades[-50:]
            
    def update_bankroll(self, new_bankroll: float):
        """Update bankroll after P&L"""
        self.current_bankroll = new_bankroll
        self.kelly_calculator.update_bankroll(new_bankroll)
        
    def get_portfolio_allocation(self, opportunities: List[Dict]) -> Dict:
        """Allocate capital across multiple opportunities"""
        if not opportunities:
            return {'allocations': {}, 'total_allocated': 0, 'reasoning': 'No opportunities'}
            
        # Calculate individual position sizes
        allocations = {}
        total_requested = 0
        
        for i, opp in enumerate(opportunities):
            key = f"{opp.get('type', 'unknown')}_{i}"
            sizing = self.calculate_optimal_size(opp)
            allocations[key] = {
                'opportunity': opp,
                'position_size': sizing['position_size'],
                'reasoning': sizing['reasoning']
            }
            total_requested += sizing['position_size']
            
        # If total exceeds reasonable portfolio allocation, scale down
        max_total_allocation = self.current_bankroll * 0.20  # 20% max total exposure
        
        if total_requested > max_total_allocation:
            scale_factor = max_total_allocation / total_requested
            
            for key in allocations:
                allocations[key]['position_size'] *= scale_factor
                allocations[key]['reasoning'] += f" | Scaled {scale_factor:.2f}x (portfolio limit)"
                
            total_allocated = max_total_allocation
            reasoning = f"Scaled down due to portfolio limit (${total_requested:.0f} → ${total_allocated:.0f})"
        else:
            total_allocated = total_requested
            reasoning = f"Full allocation within limits"
            
        return {
            'allocations': allocations,
            'total_allocated': round(total_allocated, 2),
            'portfolio_utilization': f"{total_allocated / self.current_bankroll:.1%}",
            'reasoning': reasoning
        }
    
    def get_sizing_summary(self) -> Dict:
        """Get summary of current sizing parameters"""
        return {
            'bankroll': self.current_bankroll,
            'max_single_position': self.current_bankroll * 0.10,
            'max_portfolio_exposure': self.current_bankroll * 0.20,
            'strategy_performance': {
                k: {
                    'trades': v['total_trades'],
                    'win_rate': f"{v['win_rate']:.1%}",
                    'pnl': round(v['total_pnl'], 2)
                }
                for k, v in self.strategy_performance.items()
            },
            'recent_trade_count': len(self.recent_trades),
            'kelly_settings': {
                'max_kelly_fraction': self.kelly_calculator.max_kelly_fraction,
                'min_position': self.kelly_calculator.min_position,
                'max_position': self.kelly_calculator.max_position
            }
        }


# Testing function
def test_enhanced_sizing():
    """Test the enhanced position sizer"""
    print("="*60)
    print("ENHANCED POSITION SIZING TESTS")
    print("="*60)
    
    sizer = EnhancedPositionSizer(initial_bankroll=500)
    
    print("\n1. HIGH-PROBABILITY BOND (97% confidence)")
    bond_opp = {
        'type': 'BOND',
        'strategy': 'high_prob_bonds',
        'ev': 0.15,
        'confidence': 0.97,
        'price': 0.955,
        'side': 'YES'
    }
    
    result = sizer.calculate_optimal_size(bond_opp, category='politics')
    print(json.dumps(result, indent=2))
    
    print("\n2. ARBITRAGE OPPORTUNITY (99% confidence)")
    arb_opp = {
        'type': 'ARB',
        'strategy': 'cross_platform_arb',
        'ev': 2.5,
        'confidence': 0.99,
        'spread': 0.025
    }
    
    result = sizer.calculate_optimal_size(arb_opp, category='crypto')
    print(json.dumps(result, indent=2))
    
    print("\n3. WHALE TRACKING (60% confidence)")
    whale_opp = {
        'type': 'WHALE',
        'strategy': 'whale_tracking', 
        'ev': 8.0,
        'confidence': 0.60,
        'volume': 150000
    }
    
    result = sizer.calculate_optimal_size(whale_opp, category='elon_doge')
    print(json.dumps(result, indent=2))
    
    print("\n4. PORTFOLIO ALLOCATION (Multiple opportunities)")
    opportunities = [bond_opp, arb_opp, whale_opp]
    portfolio = sizer.get_portfolio_allocation(opportunities)
    print(json.dumps(portfolio, indent=2))
    
    print("\n5. SIZING SUMMARY")
    summary = sizer.get_sizing_summary()
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    test_enhanced_sizing()