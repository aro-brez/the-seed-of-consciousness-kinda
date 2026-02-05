#!/usr/bin/env python3
"""
MINIMUM VIABLE RISK SYSTEM (MVRS)

After a -47% drawdown, this is the NON-NEGOTIABLE system.
Every trade MUST pass these gates before execution.

The 8 Rules Encoded:
1. Thesis Quality Gate (confidence >= 0.7, specific, explainable)
2. Position Sizing (Kelly Criterion 1/4 fractional)
3. Loss Stop (max 10% per position, automated)
4. Time Stop (max 14 days hold)
5. Daily Circuit Breaker (stop at 5% daily loss)
6. Trade Journal (entry + exit reason + thesis correctness)
7. Daily Monitoring (health check at market open)
8. Weekly Retrospective (pattern analysis)

Usage:
    mvrs = MinimumViableRiskSystem(bankroll=1318.62)

    # Before entering a trade
    can_enter = mvrs.can_enter_trade(
        thesis="Market will break above $100 on positive earnings",
        confidence=0.75,
        expected_win_pct=0.15
    )

    if can_enter:
        trade = mvrs.enter_trade(...)

    # Morning routine
    mvrs.daily_morning_routine()

    # Friday routine
    mvrs.weekly_retrospective()
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import statistics

REPO_ROOT = Path(__file__).parent.parent
TRADING_DIR = REPO_ROOT / 'BRAIN' / 'TRADING'
TRADING_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Trade:
    """Single trade record"""
    trade_id: str
    entry_time: datetime
    thesis: str
    confidence: float  # 0-1
    position_size: float
    entry_price: float
    entry_value: float
    max_loss_pct: float = 0.10
    max_hold_days: int = 14
    market_id: str = ""

    # Exit info (populated on close)
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None  # "loss_stop", "time_stop", "thesis_stop", "profit_target", "manual"
    thesis_correct: Optional[bool] = None  # Was my thesis right?
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None


class ThesisGate:
    """
    Gate 1: Only enter trades with high-quality theses.
    Rejects low-confidence, vague, or untestable theses.
    """

    def __init__(self, min_confidence: float = 0.70):
        self.min_confidence = min_confidence
        self.rejected_theses = []

    def should_enter(self, thesis: str, confidence: float) -> Tuple[bool, str]:
        """
        Returns: (should_enter, reason)
        """

        # Check 1: Confidence threshold
        if confidence < self.min_confidence:
            reason = f"Confidence {confidence:.0%} below minimum {self.min_confidence:.0%}"
            self.rejected_theses.append({'thesis': thesis, 'reason': reason})
            return False, reason

        # Check 2: Thesis specificity (reject wishy-washy language)
        vague_words = ['probably', 'might', 'maybe', 'could', 'seems', 'appears', 'think', 'believe']
        thesis_lower = thesis.lower()
        if any(word in thesis_lower for word in vague_words):
            reason = f"Thesis too vague (contains uncertainty words): {thesis}"
            self.rejected_theses.append({'thesis': thesis, 'reason': reason})
            return False, reason

        # Check 3: Thesis length (can't explain in ~1 sentence? Don't understand it)
        if len(thesis) > 200:
            reason = f"Thesis too long ({len(thesis)} chars). If you can't explain in 1 sentence, you don't understand it."
            self.rejected_theses.append({'thesis': thesis, 'reason': reason})
            return False, reason

        # Check 4: Thesis contains concrete market signal
        market_words = ['break', 'support', 'resistance', 'trend', 'momentum', 'earnings', 'news', 'flow', 'structure']
        if not any(word in thesis_lower for word in market_words):
            reason = f"Thesis lacks concrete market signal. Be specific about WHAT in the market supports this."
            self.rejected_theses.append({'thesis': thesis, 'reason': reason})
            return False, reason

        # All checks passed
        return True, "Thesis quality APPROVED"

    def get_rejection_summary(self) -> Dict:
        """Summary of rejected theses"""
        return {
            'total_rejected': len(self.rejected_theses),
            'rejections': self.rejected_theses[-10:]  # Last 10
        }


class PositionSizer:
    """
    Gate 2: Scientific position sizing using Kelly Criterion (1/4 fractional).

    Formula: position = (win_rate * win% - loss_rate * loss%) / loss% * kelly_fraction
    Example: (0.55 * 0.15 - 0.45 * 0.10) / 0.10 * 0.25 = 2.25% of bankroll
    """

    def __init__(self, kelly_fraction: float = 0.25, max_position_pct: float = 0.05):
        self.kelly_fraction = kelly_fraction  # 1/4 Kelly = conservative
        self.max_position_pct = max_position_pct  # Cap at 5% per position

    def calculate_position_size(
        self,
        bankroll: float,
        win_rate: float,
        expected_win_pct: float,
        expected_loss_pct: float = 0.10
    ) -> Dict:
        """
        Calculate position size using Kelly Criterion.

        Args:
            bankroll: Current available capital
            win_rate: Probability of win (0-1)
            expected_win_pct: Expected % gain on win
            expected_loss_pct: Expected % loss on loss (typically 10% = stop loss)

        Returns:
            Dict with position_size and reasoning
        """

        # Kelly formula: f = (p*b - q) / b
        # Simplified: f = (win_rate * win% - loss_rate * loss%) / loss%
        loss_rate = 1 - win_rate
        kelly_frac = (win_rate * expected_win_pct - loss_rate * expected_loss_pct) / expected_loss_pct

        # Apply Kelly fraction (use 1/4 Kelly for safety)
        fractional_kelly = kelly_frac * self.kelly_fraction

        # Calculate position size
        position_size = bankroll * fractional_kelly

        # Apply caps
        max_allowed = bankroll * self.max_position_pct
        final_position = min(position_size, max_allowed)

        # Handle negative Kelly (don't trade if math says don't)
        if kelly_frac < 0:
            final_position = 0
            reason = f"Negative expected value: {kelly_frac:.2f}. Don't trade."
        elif fractional_kelly <= 0:
            final_position = 0
            reason = "Fractional Kelly is zero or negative. Wait for better odds."
        elif final_position > max_allowed:
            reason = f"Position capped at max {self.max_position_pct:.0%} of bankroll"
        else:
            reason = f"Kelly optimal {kelly_frac:.2%} -> 1/4 Kelly {fractional_kelly:.2%} -> ${final_position:.2f}"

        return {
            'position_size': max(0, round(final_position, 2)),
            'kelly_optimal': kelly_frac,
            'kelly_fractional': fractional_kelly,
            'max_allowed': max_allowed,
            'reasoning': reason,
            'trade_allowed': final_position > 0
        }


class StopManager:
    """
    Gate 3, 4: Automated stop losses (loss stop + time stop + thesis stop).
    """

    def __init__(self, max_loss_pct: float = 0.10, max_hold_days: int = 14):
        self.max_loss_pct = max_loss_pct
        self.max_hold_days = max_hold_days

    def check_stops(
        self,
        entry_price: float,
        entry_time: datetime,
        current_price: Optional[float] = None,
        thesis_still_valid: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if ANY stop is triggered.

        Returns:
            (should_exit, exit_reason)
        """

        # Stop 1: Loss stop
        if current_price is not None:
            loss_pct = (current_price - entry_price) / entry_price
            if loss_pct <= -self.max_loss_pct:
                return True, f"LOSS_STOP: {loss_pct*100:.1f}% loss (max {-self.max_loss_pct*100:.0f}%)"

        # Stop 2: Time stop
        days_held = (datetime.now() - entry_time).days
        if days_held >= self.max_hold_days:
            return True, f"TIME_STOP: Held {days_held} days (max {self.max_hold_days})"

        # Stop 3: Thesis stop
        if not thesis_still_valid:
            return True, "THESIS_STOP: Thesis invalidated by market"

        # No stops triggered
        return False, None


class DailyCircuitBreaker:
    """
    Gate 5: Daily portfolio-level circuit breaker.
    Stops all trading if daily loss >= 5%.
    """

    def __init__(self, max_daily_loss_pct: float = 0.05, max_weekly_loss_pct: float = 0.10):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_weekly_loss_pct = max_weekly_loss_pct
        self.start_of_day_capital = None
        self.start_of_week_capital = None
        self.last_reset_date = datetime.now().date()
        self.last_reset_week = datetime.now().isocalendar()[1]

    def check_circuit_breaker(self, current_capital: float) -> Tuple[bool, str]:
        """
        Check if trading is allowed based on daily/weekly loss.

        Returns:
            (trading_allowed, message)
        """

        # Initialize on first call
        if self.start_of_day_capital is None:
            self.start_of_day_capital = current_capital
            self.start_of_week_capital = current_capital

        # Reset if new day
        if datetime.now().date() > self.last_reset_date:
            self.start_of_day_capital = current_capital
            self.last_reset_date = datetime.now().date()

        # Reset if new week
        current_week = datetime.now().isocalendar()[1]
        if current_week > self.last_reset_week:
            self.start_of_week_capital = current_capital
            self.last_reset_week = current_week

        # Calculate losses
        daily_loss_pct = (self.start_of_day_capital - current_capital) / self.start_of_day_capital
        weekly_loss_pct = (self.start_of_week_capital - current_capital) / self.start_of_week_capital

        # Check weekly limit first (most severe)
        if weekly_loss_pct >= self.max_weekly_loss_pct:
            return False, f"Weekly loss {weekly_loss_pct*100:.1f}% >= {self.max_weekly_loss_pct*100:.0f}% - ALL TRADING HALTED"

        # Check daily limit
        if daily_loss_pct >= self.max_daily_loss_pct:
            return False, f"Daily loss {daily_loss_pct*100:.1f}% >= {self.max_daily_loss_pct*100:.0f}% - STOP TRADING TODAY"

        # Trading allowed
        return True, f"Trading OK. Daily loss: {daily_loss_pct*100:.1f}%, Weekly loss: {weekly_loss_pct*100:.1f}%"


class TradeJournal:
    """
    Gate 6: Comprehensive trade journal for learning.
    Records entry reason, exit reason, and thesis correctness.
    """

    def __init__(self, journal_file: Path = None):
        if journal_file is None:
            journal_file = TRADING_DIR / 'mvrs_trade_journal.json'
        self.journal_file = journal_file
        self.trades: List[Dict] = self._load_journal()

    def _load_journal(self) -> List[Dict]:
        """Load existing journal from disk"""
        if self.journal_file.exists():
            with open(self.journal_file) as f:
                return json.load(f)
        return []

    def log_entry(self, trade: Trade) -> None:
        """Log trade entry"""
        entry_record = {
            'trade_id': trade.trade_id,
            'entry_time': trade.entry_time.isoformat(),
            'thesis': trade.thesis,
            'confidence': trade.confidence,
            'position_size': trade.position_size,
            'entry_price': trade.entry_price,
            'entry_value': trade.entry_value,
            'market_id': trade.market_id,
        }
        self.trades.append(entry_record)
        self._save_journal()

    def log_exit(self, trade: Trade) -> None:
        """Log trade exit"""
        # Find the entry record
        entry_record = next((t for t in self.trades if t['trade_id'] == trade.trade_id), None)
        if entry_record:
            entry_record['exit_time'] = trade.exit_time.isoformat()
            entry_record['exit_price'] = trade.exit_price
            entry_record['exit_reason'] = trade.exit_reason
            entry_record['thesis_correct'] = trade.thesis_correct
            entry_record['pnl'] = trade.pnl
            entry_record['pnl_pct'] = trade.pnl_pct
            self._save_journal()

    def _save_journal(self) -> None:
        """Save journal to disk"""
        with open(self.journal_file, 'w') as f:
            json.dump(self.trades, f, indent=2, default=str)

    def weekly_analysis(self) -> Dict:
        """Analyze trades from the past week"""
        week_ago = datetime.now() - timedelta(days=7)
        week_trades = [
            t for t in self.trades
            if 'exit_time' in t and datetime.fromisoformat(t['exit_time']) > week_ago
        ]

        if not week_trades:
            return {'total_trades': 0, 'message': 'No completed trades this week'}

        # Calculate metrics
        wins = [t for t in week_trades if t.get('pnl', 0) > 0]
        losses = [t for t in week_trades if t.get('pnl', 0) <= 0]

        win_rate = len(wins) / len(week_trades) if week_trades else 0
        total_pnl = sum(t.get('pnl', 0) for t in week_trades)
        avg_win = statistics.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = statistics.mean([t['pnl'] for t in losses]) if losses else 0

        # By exit reason
        by_reason = {}
        for trade in week_trades:
            reason = trade.get('exit_reason', 'unknown')
            if reason not in by_reason:
                by_reason[reason] = {'count': 0, 'pnl': [], 'correct': []}
            by_reason[reason]['count'] += 1
            by_reason[reason]['pnl'].append(trade.get('pnl', 0))
            by_reason[reason]['correct'].append(trade.get('thesis_correct'))

        # Find the killer
        worst_reason = min(by_reason.items(), key=lambda x: sum(x[1]['pnl'])) if by_reason else None

        return {
            'total_trades': len(week_trades),
            'wins': len(wins),
            'losses': len(losses),
            'win_rate': win_rate,
            'total_pnl': round(total_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'by_exit_reason': {k: {
                'count': v['count'],
                'total_pnl': round(sum(v['pnl']), 2),
                'avg_pnl': round(sum(v['pnl']) / v['count'], 2),
                'thesis_accuracy': round(sum(1 for c in v['correct'] if c) / len(v['correct']), 2) if v['correct'] else 0
            } for k, v in by_reason.items()},
            'top_killer': worst_reason[0] if worst_reason else None,
        }


class PositionMonitor:
    """
    Gate 7: Daily position monitoring.
    Flags unhealthy positions (down >5%, >50% loss, >90% of max loss allowed).
    """

    def __init__(self):
        self.monitored_positions = []

    def add_position(self, trade: Trade) -> None:
        """Track a position"""
        self.monitored_positions.append(trade)

    def remove_position(self, trade_id: str) -> None:
        """Stop tracking a position"""
        self.monitored_positions = [p for p in self.monitored_positions if p.trade_id != trade_id]

    def daily_check(self, current_prices: Dict[str, float]) -> Dict:
        """
        Check all positions at market open.

        Args:
            current_prices: Dict of {trade_id: current_price}

        Returns:
            Dict with health status
        """
        unhealthy = []

        for trade in self.monitored_positions:
            if trade.trade_id not in current_prices:
                continue

            current_price = current_prices[trade.trade_id]
            current_value = trade.position_size * current_price / trade.entry_price
            pnl_pct = (current_price - trade.entry_price) / trade.entry_price

            # Calculate health (0-100)
            if pnl_pct > 0.05:
                health = 100  # Winning
            elif pnl_pct > 0:
                health = 80   # Breakeven zone
            elif pnl_pct > -0.05:
                health = 60   # Small loss
            elif pnl_pct > trade.max_loss_pct * 0.9:
                health = 40   # Close to stop loss
            elif pnl_pct > -0.50:
                health = 20   # Severely underwater
            else:
                health = 0    # Nearly dead

            # Flag unhealthy
            if health < 60:
                unhealthy.append({
                    'trade_id': trade.trade_id,
                    'health': health,
                    'pnl_pct': pnl_pct,
                    'days_held': (datetime.now() - trade.entry_time).days,
                    'thesis': trade.thesis,
                })

        return {
            'total_monitored': len(self.monitored_positions),
            'unhealthy': unhealthy,
            'alert_count': len(unhealthy)
        }


class MinimumViableRiskSystem:
    """
    Orchestrates all risk management gates.
    The master control system that enforces discipline.
    """

    def __init__(self, bankroll: float):
        self.initial_bankroll = bankroll
        self.current_capital = bankroll
        self.peak_capital = bankroll

        # Initialize all gates
        self.thesis_gate = ThesisGate(min_confidence=0.70)
        self.position_sizer = PositionSizer(kelly_fraction=0.25, max_position_pct=0.05)
        self.stop_manager = StopManager(max_loss_pct=0.10, max_hold_days=14)
        self.circuit_breaker = DailyCircuitBreaker(max_daily_loss_pct=0.05, max_weekly_loss_pct=0.10)
        self.journal = TradeJournal()
        self.monitor = PositionMonitor()

        self.open_trades: List[Trade] = []

    def can_enter_trade(
        self,
        thesis: str,
        confidence: float,
        expected_win_pct: float,
        win_rate: float = 0.50
    ) -> Tuple[bool, str]:
        """
        Master gate check: Can we enter this trade?

        Returns:
            (can_enter, reason)
        """

        # Gate 1: Thesis quality
        thesis_ok, thesis_reason = self.thesis_gate.should_enter(thesis, confidence)
        if not thesis_ok:
            return False, f"Thesis gate REJECTED: {thesis_reason}"

        # Gate 2: Circuit breaker
        cb_ok, cb_reason = self.circuit_breaker.check_circuit_breaker(self.current_capital)
        if not cb_ok:
            return False, f"Circuit breaker HALTED: {cb_reason}"

        # Gate 3: Position sizing
        position_info = self.position_sizer.calculate_position_size(
            bankroll=self.current_capital,
            win_rate=win_rate,
            expected_win_pct=expected_win_pct
        )
        if not position_info['trade_allowed']:
            return False, f"Position sizing rejected: {position_info['reasoning']}"

        # All gates passed
        return True, f"Trade approved: {position_info['reasoning']}"

    def enter_trade(
        self,
        thesis: str,
        confidence: float,
        expected_win_pct: float,
        entry_price: float,
        market_id: str,
        win_rate: float = 0.50
    ) -> Optional[Trade]:
        """
        Execute trade entry if all gates pass.
        """

        # Final check
        can_enter, reason = self.can_enter_trade(thesis, confidence, expected_win_pct, win_rate)
        if not can_enter:
            print(f"ENTRY BLOCKED: {reason}")
            return None

        # Calculate position size
        position_info = self.position_sizer.calculate_position_size(
            bankroll=self.current_capital,
            win_rate=win_rate,
            expected_win_pct=expected_win_pct
        )
        position_size = position_info['position_size']

        # Create trade
        trade = Trade(
            trade_id=f"{market_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            entry_time=datetime.now(),
            thesis=thesis,
            confidence=confidence,
            position_size=position_size,
            entry_price=entry_price,
            entry_value=position_size * entry_price,
            market_id=market_id
        )

        # Record
        self.open_trades.append(trade)
        self.journal.log_entry(trade)
        self.monitor.add_position(trade)

        print(f"TRADE ENTERED: {trade.trade_id}")
        print(f"  Thesis: {thesis}")
        print(f"  Position: ${position_size:.2f}")
        print(f"  Entry price: ${entry_price:.2f}")

        return trade

    def exit_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: str,
        thesis_correct: bool
    ) -> Optional[Trade]:
        """
        Exit a trade and record P&L.
        """

        # Find trade
        trade = next((t for t in self.open_trades if t.trade_id == trade_id), None)
        if not trade:
            print(f"ERROR: Trade {trade_id} not found")
            return None

        # Calculate P&L
        pnl_pct = (exit_price - trade.entry_price) / trade.entry_price
        pnl = trade.position_size * pnl_pct

        # Update trade
        trade.exit_time = datetime.now()
        trade.exit_price = exit_price
        trade.exit_reason = exit_reason
        trade.thesis_correct = thesis_correct
        trade.pnl = round(pnl, 2)
        trade.pnl_pct = round(pnl_pct * 100, 2)

        # Update capital
        self.current_capital += pnl
        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

        # Record
        self.journal.log_exit(trade)
        self.monitor.remove_position(trade_id)
        self.open_trades.remove(trade)

        print(f"TRADE EXITED: {trade_id}")
        print(f"  Exit reason: {exit_reason}")
        print(f"  P&L: ${pnl:+.2f} ({pnl_pct*100:+.1f}%)")
        print(f"  Capital now: ${self.current_capital:.2f}")

        return trade

    def daily_morning_routine(self, current_prices: Dict[str, float]) -> None:
        """Run at market open every day"""
        print("\n" + "="*70)
        print("DAILY MORNING ROUTINE")
        print("="*70)

        # Circuit breaker check
        cb_ok, cb_reason = self.circuit_breaker.check_circuit_breaker(self.current_capital)
        print(f"Circuit breaker: {cb_reason}")

        # Position health check
        health_report = self.monitor.daily_check(current_prices)
        print(f"\nPositions monitored: {health_report['total_monitored']}")

        if health_report['alert_count'] > 0:
            print(f"\nUNHEALTHY POSITIONS ({health_report['alert_count']}):")
            for pos in health_report['unhealthy']:
                print(f"  {pos['trade_id']}: {pos['health']}/100 ({pos['pnl_pct']*100:+.1f}%, {pos['days_held']} days)")
                print(f"    Thesis: {pos['thesis']}")

        # Capital status
        dd_pct = (self.peak_capital - self.current_capital) / self.peak_capital
        print(f"\nCapital: ${self.current_capital:.2f} (peak ${self.peak_capital:.2f}, DD {dd_pct*100:.1f}%)")

    def weekly_retrospective(self) -> None:
        """Run Friday at market close"""
        print("\n" + "="*70)
        print("WEEKLY RETROSPECTIVE")
        print("="*70)

        analysis = self.journal.weekly_analysis()

        if analysis['total_trades'] == 0:
            print("No completed trades this week")
            return

        print(f"\nTrade summary:")
        print(f"  Total: {analysis['total_trades']}")
        print(f"  Wins: {analysis['wins']} ({analysis['win_rate']*100:.0f}%)")
        print(f"  Losses: {analysis['losses']}")
        print(f"  P&L: ${analysis['total_pnl']:+.2f}")
        print(f"  Avg win: ${analysis['avg_win']:+.2f}")
        print(f"  Avg loss: ${analysis['avg_loss']:+.2f}")

        print(f"\nBy exit reason:")
        for reason, stats in analysis['by_exit_reason'].items():
            print(f"  {reason}:")
            print(f"    Count: {stats['count']}")
            print(f"    Avg P&L: ${stats['avg_pnl']:+.2f}")
            print(f"    Thesis accuracy: {stats['thesis_accuracy']*100:.0f}%")

        # Find killer
        if analysis['top_killer']:
            killer_stats = analysis['by_exit_reason'][analysis['top_killer']]
            print(f"\nTOP KILLER: {analysis['top_killer']}")
            print(f"  This is costing you ${killer_stats['total_pnl']:+.2f} per week")
            print(f"  ACTION REQUIRED: Investigate why exits via '{analysis['top_killer']}' lose money")

        # Sizing recommendation
        if analysis['win_rate'] < 0.45:
            print(f"\nWARNING: Win rate {analysis['win_rate']*100:.0f}% < 45%")
            print(f"  Recommendation: Reduce position sizes by 50% next week")
        elif analysis['win_rate'] > 0.60:
            print(f"\nGOOD: Win rate {analysis['win_rate']*100:.0f}% > 60%")
            print(f"  Recommendation: Can increase position sizes next week")

    def get_status(self) -> Dict:
        """Current system status"""
        return {
            'capital': {
                'initial': self.initial_bankroll,
                'current': self.current_capital,
                'peak': self.peak_capital,
                'total_return': (self.current_capital - self.initial_bankroll) / self.initial_bankroll
            },
            'positions': {
                'open': len(self.open_trades),
                'total_pnl': sum(t.pnl or 0 for t in self.open_trades)
            },
            'rejected_theses': self.thesis_gate.get_rejection_summary()
        }


# Example usage
if __name__ == '__main__':
    print("MINIMUM VIABLE RISK SYSTEM - Example Usage\n")

    # Initialize with starting capital
    mvrs = MinimumViableRiskSystem(bankroll=1318.62)
    print(f"System initialized with ${mvrs.initial_bankroll:.2f}\n")

    # Attempt to enter a trade (good thesis)
    print("=" * 70)
    print("ATTEMPT 1: High-confidence, specific thesis")
    print("=" * 70)

    can_enter, reason = mvrs.can_enter_trade(
        thesis="Market broke above $100 resistance on strong volume",
        confidence=0.75,
        expected_win_pct=0.15,
        win_rate=0.55
    )
    print(f"Result: {reason}\n")

    if can_enter:
        trade1 = mvrs.enter_trade(
            thesis="Market broke above $100 resistance on strong volume",
            confidence=0.75,
            expected_win_pct=0.15,
            entry_price=100.50,
            market_id="TEST_001",
            win_rate=0.55
        )

    # Attempt to enter a second trade (bad thesis)
    print("\n" + "=" * 70)
    print("ATTEMPT 2: Low-confidence, vague thesis")
    print("=" * 70)

    can_enter, reason = mvrs.can_enter_trade(
        thesis="I think this might go up maybe",
        confidence=0.45,
        expected_win_pct=0.10,
        win_rate=0.50
    )
    print(f"Result: {reason}\n")

    # Check status
    print("\n" + "=" * 70)
    print("SYSTEM STATUS")
    print("=" * 70)
    print(json.dumps(mvrs.get_status(), indent=2, default=str))
