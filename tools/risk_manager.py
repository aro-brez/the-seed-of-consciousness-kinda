#!/usr/bin/env python3
"""
UNIFIED RISK MANAGER
Portfolio-wide risk controls for multi-strategy trading
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from kelly_criterion import KellyCalculator


class RiskManager:
    """Unified risk management across all trading strategies"""

    def __init__(
        self,
        initial_bankroll: float,
        max_daily_drawdown: float = 0.05,
        max_weekly_drawdown: float = 0.10,
        max_monthly_drawdown: float = 0.20,
        max_position_size: float = 0.05,
        max_strategy_allocation: float = 0.30,
        reserve_fraction: float = 0.30
    ):
        """
        Initialize risk manager

        Args:
            initial_bankroll: Starting capital
            max_daily_drawdown: Stop trading if lose this % in one day (default 5%)
            max_weekly_drawdown: Reduce sizes if lose this % in week (default 10%)
            max_monthly_drawdown: Pause if lose this % in month (default 20%)
            max_position_size: Max % of bankroll in single trade (default 5%)
            max_strategy_allocation: Max % allocated to one strategy (default 30%)
            reserve_fraction: % to keep in reserve (default 30%)
        """
        self.initial_bankroll = initial_bankroll
        self.current_bankroll = initial_bankroll
        self.peak_bankroll = initial_bankroll

        # Drawdown limits
        self.max_daily_drawdown = max_daily_drawdown
        self.max_weekly_drawdown = max_weekly_drawdown
        self.max_monthly_drawdown = max_monthly_drawdown

        # Position limits
        self.max_position_size = max_position_size
        self.max_strategy_allocation = max_strategy_allocation
        self.reserve_fraction = reserve_fraction

        # Tracking
        self.open_positions: Dict[str, List[Dict]] = {}  # strategy -> [positions]
        self.trade_history: List[Dict] = []
        self.daily_start_bankroll = initial_bankroll
        self.weekly_start_bankroll = initial_bankroll
        self.monthly_start_bankroll = initial_bankroll
        self.last_day = datetime.now().date()
        self.last_week = datetime.now().isocalendar()[1]
        self.last_month = datetime.now().month

        # Kelly calculator
        self.kelly = KellyCalculator(bankroll=initial_bankroll)

        # State
        self.trading_halted = False
        self.halt_reason = None
        self.size_reduction_factor = 1.0  # Multiplier for reducing position sizes

    def check_trading_allowed(self) -> Dict:
        """
        Check if trading is allowed based on drawdown limits

        Returns:
            Dict with status and reason
        """
        # Update time-based tracking
        self._update_time_periods()

        # Calculate current drawdowns
        daily_dd = (self.daily_start_bankroll - self.current_bankroll) / self.daily_start_bankroll
        weekly_dd = (self.weekly_start_bankroll - self.current_bankroll) / self.weekly_start_bankroll
        monthly_dd = (self.monthly_start_bankroll - self.current_bankroll) / self.monthly_start_bankroll

        # Check monthly limit (most severe)
        if monthly_dd >= self.max_monthly_drawdown:
            self.trading_halted = True
            self.halt_reason = f"Monthly drawdown {monthly_dd:.2%} >= {self.max_monthly_drawdown:.2%}"
            return {
                'allowed': False,
                'reason': self.halt_reason,
                'severity': 'CRITICAL',
                'action': 'HALT ALL TRADING - Manual review required'
            }

        # Check daily limit
        if daily_dd >= self.max_daily_drawdown:
            self.trading_halted = True
            self.halt_reason = f"Daily drawdown {daily_dd:.2%} >= {self.max_daily_drawdown:.2%}"
            return {
                'allowed': False,
                'reason': self.halt_reason,
                'severity': 'HIGH',
                'action': 'Stop trading for today'
            }

        # Check weekly limit (reduce sizes)
        if weekly_dd >= self.max_weekly_drawdown:
            self.size_reduction_factor = 0.5
            return {
                'allowed': True,
                'reason': f"Weekly drawdown {weekly_dd:.2%} >= {self.max_weekly_drawdown:.2%}",
                'severity': 'MEDIUM',
                'action': 'Reduce all position sizes by 50%'
            }

        # All clear
        self.trading_halted = False
        self.size_reduction_factor = 1.0
        return {
            'allowed': True,
            'reason': 'All risk limits OK',
            'severity': 'LOW',
            'action': 'Normal trading'
        }

    def calculate_position_size(
        self,
        strategy_name: str,
        win_probability: float,
        expected_return: float,
        current_strategy_exposure: float = 0
    ) -> Dict:
        """
        Calculate safe position size for a trade

        Args:
            strategy_name: Name of strategy
            win_probability: Probability of winning (0-1)
            expected_return: Expected return on win (%)
            current_strategy_exposure: Current capital in this strategy

        Returns:
            Dict with position_size and reasoning
        """

        # Check if trading allowed
        status = self.check_trading_allowed()
        if not status['allowed']:
            return {
                'position_size': 0,
                'reason': status['reason'],
                'action': status['action']
            }

        # Calculate Kelly-optimal position
        kelly_result = self.kelly.calculate_position_size(
            win_probability=win_probability,
            win_amount=expected_return,
            loss_amount=100,  # Assume 100% loss if wrong
            strategy_name=strategy_name
        )

        raw_position = kelly_result['position_size']

        # Apply size reduction if weekly drawdown triggered
        adjusted_position = raw_position * self.size_reduction_factor

        # Check position limits
        max_single_position = self.current_bankroll * self.max_position_size
        if adjusted_position > max_single_position:
            adjusted_position = max_single_position
            reason = f"Capped at max position size ({self.max_position_size:.1%} of bankroll)"
        else:
            reason = kelly_result['reasoning']

        # Check strategy allocation limit
        available_capital = self.current_bankroll * (1 - self.reserve_fraction)
        max_strategy_capital = available_capital * self.max_strategy_allocation

        if current_strategy_exposure + adjusted_position > max_strategy_capital:
            adjusted_position = max(0, max_strategy_capital - current_strategy_exposure)
            reason = f"Strategy allocation capped at {self.max_strategy_allocation:.1%}"

        return {
            'position_size': round(adjusted_position, 2),
            'kelly_optimal': kelly_result['position_size'],
            'size_reduction_factor': self.size_reduction_factor,
            'reason': reason,
            'strategy': strategy_name,
            'bankroll': self.current_bankroll
        }

    def record_trade(
        self,
        strategy_name: str,
        position_size: float,
        entry_price: float,
        trade_type: str,
        market_id: str
    ) -> Dict:
        """
        Record a new trade opening

        Returns:
            Trade ID and position details
        """
        trade = {
            'trade_id': f"{strategy_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'strategy': strategy_name,
            'position_size': position_size,
            'entry_price': entry_price,
            'entry_time': datetime.now().isoformat(),
            'type': trade_type,
            'market_id': market_id,
            'status': 'OPEN'
        }

        # Add to open positions
        if strategy_name not in self.open_positions:
            self.open_positions[strategy_name] = []
        self.open_positions[strategy_name].append(trade)

        # Add to history
        self.trade_history.append(trade)

        return trade

    def close_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str
    ) -> Dict:
        """
        Close a trade and update bankroll

        Returns:
            Trade result with P&L
        """
        # Find trade
        trade = None
        strategy_name = None

        for strategy, positions in self.open_positions.items():
            for pos in positions:
                if pos['trade_id'] == trade_id:
                    trade = pos
                    strategy_name = strategy
                    break

        if not trade:
            return {'error': f'Trade {trade_id} not found'}

        # Calculate P&L
        pnl = trade['position_size'] * (exit_price - trade['entry_price']) / trade['entry_price']
        pnl_percent = (exit_price - trade['entry_price']) / trade['entry_price']

        # Update trade
        trade['exit_price'] = exit_price
        trade['exit_time'] = datetime.now().isoformat()
        trade['exit_reason'] = exit_reason
        trade['pnl'] = round(pnl, 2)
        trade['pnl_percent'] = round(pnl_percent * 100, 2)
        trade['status'] = 'CLOSED'

        # Update bankroll
        self.current_bankroll += pnl
        self.kelly.update_bankroll(self.current_bankroll)

        # Update peak
        if self.current_bankroll > self.peak_bankroll:
            self.peak_bankroll = self.current_bankroll

        # Remove from open positions
        self.open_positions[strategy_name] = [
            p for p in self.open_positions[strategy_name]
            if p['trade_id'] != trade_id
        ]

        return trade

    def get_portfolio_status(self) -> Dict:
        """
        Get current portfolio status

        Returns:
            Dict with all risk metrics
        """
        # Calculate exposure
        total_exposure = sum(
            sum(pos['position_size'] for pos in positions)
            for positions in self.open_positions.values()
        )

        strategy_exposure = {
            strategy: sum(pos['position_size'] for pos in positions)
            for strategy, positions in self.open_positions.items()
        }

        # Calculate drawdowns
        daily_dd = (self.daily_start_bankroll - self.current_bankroll) / self.daily_start_bankroll
        weekly_dd = (self.weekly_start_bankroll - self.current_bankroll) / self.weekly_start_bankroll
        monthly_dd = (self.monthly_start_bankroll - self.current_bankroll) / self.monthly_start_bankroll
        max_dd = (self.peak_bankroll - self.current_bankroll) / self.peak_bankroll

        # Calculate returns
        total_return = (self.current_bankroll - self.initial_bankroll) / self.initial_bankroll

        return {
            'bankroll': {
                'initial': self.initial_bankroll,
                'current': round(self.current_bankroll, 2),
                'peak': round(self.peak_bankroll, 2),
                'total_return': f"{total_return:.2%}"
            },
            'exposure': {
                'total': round(total_exposure, 2),
                'percent_of_bankroll': f"{total_exposure / self.current_bankroll:.2%}",
                'by_strategy': {k: round(v, 2) for k, v in strategy_exposure.items()}
            },
            'drawdown': {
                'daily': f"{daily_dd:.2%}",
                'weekly': f"{weekly_dd:.2%}",
                'monthly': f"{monthly_dd:.2%}",
                'max': f"{max_dd:.2%}"
            },
            'limits': {
                'daily_limit': f"{self.max_daily_drawdown:.2%}",
                'weekly_limit': f"{self.max_weekly_drawdown:.2%}",
                'monthly_limit': f"{self.max_monthly_drawdown:.2%}"
            },
            'status': {
                'trading_halted': self.trading_halted,
                'halt_reason': self.halt_reason,
                'size_reduction': f"{self.size_reduction_factor:.0%}"
            },
            'open_positions': len([pos for positions in self.open_positions.values() for pos in positions]),
            'total_trades': len(self.trade_history)
        }

    def _update_time_periods(self):
        """Update daily/weekly/monthly tracking"""
        now = datetime.now()

        # New day
        if now.date() != self.last_day:
            self.daily_start_bankroll = self.current_bankroll
            self.last_day = now.date()

        # New week
        current_week = now.isocalendar()[1]
        if current_week != self.last_week:
            self.weekly_start_bankroll = self.current_bankroll
            self.last_week = current_week

        # New month
        if now.month != self.last_month:
            self.monthly_start_bankroll = self.current_bankroll
            self.last_month = now.month

    def save_state(self, filepath: Path):
        """Save risk manager state to disk"""
        state = {
            'current_bankroll': self.current_bankroll,
            'peak_bankroll': self.peak_bankroll,
            'open_positions': self.open_positions,
            'trade_history': self.trade_history[-50:],  # Last 50 trades
            'trading_halted': self.trading_halted,
            'halt_reason': self.halt_reason,
            'last_updated': datetime.now().isoformat()
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)

    def load_state(self, filepath: Path):
        """Load risk manager state from disk"""
        if not filepath.exists():
            return

        with open(filepath) as f:
            state = json.load(f)

        self.current_bankroll = state['current_bankroll']
        self.peak_bankroll = state['peak_bankroll']
        self.open_positions = state['open_positions']
        self.trade_history = state['trade_history']
        self.trading_halted = state['trading_halted']
        self.halt_reason = state['halt_reason']

        self.kelly.update_bankroll(self.current_bankroll)


# Testing
def test_risk_manager():
    """Test risk manager with example scenarios"""

    print("="*60)
    print("RISK MANAGER TESTS")
    print("="*60)

    # Initialize with $600
    risk = RiskManager(initial_bankroll=600)

    print("\n1. INITIAL STATUS")
    status = risk.get_portfolio_status()
    print(json.dumps(status, indent=2))

    print("\n2. CALCULATE POSITION SIZE (Latency Arb, 98% win rate)")
    position = risk.calculate_position_size(
        strategy_name="Latency Arb",
        win_probability=0.98,
        expected_return=2.0
    )
    print(json.dumps(position, indent=2))

    print("\n3. RECORD TRADE")
    trade = risk.record_trade(
        strategy_name="Latency Arb",
        position_size=position['position_size'],
        entry_price=0.50,
        trade_type="BUY YES",
        market_id="btc_15min_12345"
    )
    print(json.dumps(trade, indent=2))

    print("\n4. PORTFOLIO STATUS (with open position)")
    status = risk.get_portfolio_status()
    print(json.dumps(status, indent=2))

    print("\n5. CLOSE WINNING TRADE")
    result = risk.close_trade(
        trade_id=trade['trade_id'],
        exit_price=0.51,
        exit_reason="15-min resolution"
    )
    print(json.dumps(result, indent=2))

    print("\n6. FINAL STATUS")
    status = risk.get_portfolio_status()
    print(json.dumps(status, indent=2))


if __name__ == '__main__':
    test_risk_manager()
