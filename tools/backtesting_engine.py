#!/usr/bin/env python3
"""
(◉) JOULE BACKTESTING ENGINE - Comprehensive Strategy Testing Framework

PURPOSE:
- Test trading strategies against historical data
- Optimize parameters and position sizing
- Calculate performance metrics (Sharpe, win rate, max drawdown)
- Compare strategies and identify best performers
- Support for all JOULE strategies: ARB, BOND, WHALE, SPIKE, etc.

FEATURES:
- Historical market data simulation
- Multiple strategy execution modes
- Risk metrics and performance analysis
- Strategy optimization with parameter sweeps
- Real market condition simulation (fees, slippage)
- Portfolio-level backtesting (multiple strategies)

ARCHITECTURE:
    Historical Data → Strategy Engine → Performance Metrics → Optimization
         ↓               ↓                    ↓                  ↓
    Market Events → Trading Signals → Risk Management → Best Parameters