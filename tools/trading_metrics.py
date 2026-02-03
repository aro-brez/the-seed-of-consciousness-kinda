#!/usr/bin/env python3
"""
TRADING METRICS - What gets measured gets managed
(◉) Track actual performance, not theoretical edge

SUCCESS METRICS (in priority order):
1. Trades executed per day (target: 5+)
2. Capital deployed % (target: 50%+)
3. Win rate (target: 55%+)
4. ROI (target: 15%+ monthly)
5. System uptime (target: 23+ hours/day)

ANTI-METRICS (what we DON'T optimize):
- Research hours (spending more != better returns)
- Lines of code (more code != more profit)
- Strategies documented (execution > documentation)
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).parent.parent
TRADING_DIR = REPO_ROOT / 'BRAIN' / 'TRADING'
STATE_DIR = TRADING_DIR / 'autonomous_state'


@dataclass
class TradingMetrics:
    """Core metrics that matter"""
    # Execution metrics
    trades_today: int = 0
    trades_this_week: int = 0
    trades_this_month: int = 0

    # Capital metrics
    total_capital: float = 0
    deployed_capital: float = 0
    idle_capital: float = 0
    deployment_ratio: float = 0  # Target: 50%+

    # Performance metrics
    wins: int = 0
    losses: int = 0
    win_rate: float = 0
    total_pnl: float = 0
    roi_monthly: float = 0

    # System health
    last_trade_time: Optional[datetime] = None
    hours_since_last_trade: float = 0
    system_uptime_hours: float = 0

    def score(self) -> float:
        """
        Overall system health score (0-100)
        Based on what actually matters for making money
        """
        score = 0

        # Execution (40 points) - Are we actually trading?
        if self.trades_today >= 5:
            score += 20
        elif self.trades_today >= 1:
            score += 10

        if self.deployment_ratio >= 0.5:
            score += 20
        elif self.deployment_ratio >= 0.25:
            score += 10

        # Performance (40 points) - Are we winning?
        if self.win_rate >= 0.55:
            score += 20
        elif self.win_rate >= 0.45:
            score += 10

        if self.roi_monthly >= 0.15:
            score += 20
        elif self.roi_monthly >= 0.05:
            score += 10

        # System health (20 points) - Is system running?
        if self.hours_since_last_trade <= 4:
            score += 10
        elif self.hours_since_last_trade <= 24:
            score += 5

        if self.system_uptime_hours >= 23:
            score += 10
        elif self.system_uptime_hours >= 12:
            score += 5

        return score


def load_current_metrics() -> TradingMetrics:
    """Load current trading metrics from state files"""
    metrics = TradingMetrics()

    # Load trader state
    trader_state_file = STATE_DIR / 'trader_state.json'
    if trader_state_file.exists():
        with open(trader_state_file) as f:
            state = json.load(f)

        metrics.total_capital = state.get('current_bankroll', 0)
        metrics.trades_today = state.get('trades_today', 0)

        # Calculate deployed capital from active positions
        positions = state.get('active_positions', [])
        metrics.deployed_capital = sum(p.get('value', 0) for p in positions)
        metrics.idle_capital = metrics.total_capital - metrics.deployed_capital

        if metrics.total_capital > 0:
            metrics.deployment_ratio = metrics.deployed_capital / metrics.total_capital

        # Win/loss tracking
        metrics.wins = state.get('wins_today', 0)
        metrics.losses = state.get('losses_today', 0)
        total_trades = metrics.wins + metrics.losses
        if total_trades > 0:
            metrics.win_rate = metrics.wins / total_trades

        metrics.total_pnl = state.get('pnl_today', 0)

        # Last trade time
        last_trade_date = state.get('last_trade_date')
        if last_trade_date:
            try:
                last_date = datetime.strptime(last_trade_date, '%Y-%m-%d')
                metrics.last_trade_time = last_date
                metrics.hours_since_last_trade = (datetime.now() - last_date).total_seconds() / 3600
            except:
                pass

    # Load compounder state
    compounder_file = TRADING_DIR / 'compounder_state.json'
    if compounder_file.exists():
        with open(compounder_file) as f:
            comp_state = json.load(f)

        # Add compounder trades if any
        metrics.trades_this_week += comp_state.get('trades_executed', 0)

    return metrics


def print_dashboard():
    """Print metrics dashboard"""
    metrics = load_current_metrics()
    score = metrics.score()

    # Score indicator
    if score >= 70:
        status = "HEALTHY"
        indicator = "✓"
    elif score >= 40:
        status = "WARNING"
        indicator = "!"
    else:
        status = "CRITICAL"
        indicator = "✗"

    print(f"""
================================================================================
                    (◉) TRADING SYSTEM METRICS DASHBOARD
================================================================================

SYSTEM SCORE: {score}/100 [{status}] {indicator}

EXECUTION METRICS
─────────────────────────────────────────────────────────────────────
  Trades Today:           {metrics.trades_today}          (target: 5+)
  Capital Deployed:       ${metrics.deployed_capital:,.2f} ({metrics.deployment_ratio*100:.0f}%)
  Idle Capital:           ${metrics.idle_capital:,.2f}
  Hours Since Last Trade: {metrics.hours_since_last_trade:.1f}h

PERFORMANCE METRICS
─────────────────────────────────────────────────────────────────────
  Win Rate:               {metrics.win_rate*100:.1f}%     (target: 55%+)
  Total P&L:              ${metrics.total_pnl:+,.2f}
  ROI (Monthly):          {metrics.roi_monthly*100:.1f}%  (target: 15%+)

CAPITAL ALLOCATION
─────────────────────────────────────────────────────────────────────
  Total Capital:          ${metrics.total_capital:,.2f}
  Deployed:               ${metrics.deployed_capital:,.2f}
  Available:              ${metrics.idle_capital:,.2f}

{'=' * 79}

ACTION REQUIRED:
""")

    # Generate actionable recommendations
    if metrics.trades_today == 0:
        print("  [!] No trades today - RUN: ./tools/SHIP_TODAY.sh")

    if metrics.deployment_ratio < 0.25:
        print(f"  [!] Only {metrics.deployment_ratio*100:.0f}% capital deployed")
        print(f"      ${metrics.idle_capital:,.2f} sitting idle - find opportunities")

    if metrics.hours_since_last_trade > 24:
        print(f"  [!] {metrics.hours_since_last_trade:.0f} hours since last trade")
        print("      System may not be running - check logs")

    if score >= 70:
        print("  [✓] System healthy - continue monitoring")

    print()


def main():
    """Entry point"""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # Output as JSON for programmatic use
        metrics = load_current_metrics()
        print(json.dumps({
            'score': metrics.score(),
            'trades_today': metrics.trades_today,
            'deployment_ratio': metrics.deployment_ratio,
            'win_rate': metrics.win_rate,
            'total_pnl': metrics.total_pnl,
            'idle_capital': metrics.idle_capital,
            'hours_since_trade': metrics.hours_since_last_trade,
        }, indent=2))
    else:
        print_dashboard()


if __name__ == '__main__':
    main()
