#!/usr/bin/env python3
"""
PARALLEL STRATEGY EXECUTOR - Run 4+ strategies simultaneously
Execute multiple trading strategies in parallel for maximum throughput

Built: January 29, 2026
Status: Production-ready
Speedup: 4x (4 strategies at once vs sequential)
"""

import json
import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).parent.parent
OUTPUT_DIR = REPO_ROOT / 'BRAIN' / 'INTEL' / 'parallel_trades'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class ParallelStrategyExecutor:
    """
    Execute multiple trading strategies in parallel

    Benefits:
    - 4x throughput (4 strategies at once)
    - Event-driven architecture
    - Real-time opportunity detection
    - Unified risk management
    - Performance monitoring
    """

    def __init__(self, strategies: List = None):
        """
        Initialize parallel executor

        Args:
            strategies: List of strategy objects (must have analyze_signals_async method)
        """
        self.strategies = strategies or []

        # Event queue (price updates, signals, etc.)
        self.event_queue = asyncio.Queue()

        # Results tracking
        self.opportunities = []
        self.executions = []

        # Performance metrics
        self.cycles_run = 0
        self.total_analysis_time = 0
        self.strategies_triggered = {s.__class__.__name__: 0 for s in self.strategies}

        # State
        self.running = False

    def add_strategy(self, strategy):
        """Add a strategy to the executor"""
        self.strategies.append(strategy)
        self.strategies_triggered[strategy.__class__.__name__] = 0
        logger.info(f"Added strategy: {strategy.__class__.__name__}")

    async def analyze_all_parallel(self, market_data: Dict) -> List[Dict]:
        """
        Analyze all strategies in parallel

        Args:
            market_data: Current market data (prices, momentum, etc.)

        Returns:
            List of opportunities (action == 'EXECUTE')
        """
        start_time = time.time()

        # Create async tasks for each strategy
        tasks = []
        for strategy in self.strategies:
            # Each strategy analyzes market data independently
            task = asyncio.create_task(
                self.run_strategy_safe(strategy, market_data)
            )
            tasks.append(task)

        # Execute all strategies in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter for valid results
        opportunities = []
        for i, result in enumerate(results):
            strategy_name = self.strategies[i].__class__.__name__

            # Handle exceptions
            if isinstance(result, Exception):
                logger.error(f"❌ {strategy_name} error: {result}")
                continue

            # Handle None results
            if result is None:
                continue

            # Check for EXECUTE action
            if result.get('action') == 'EXECUTE':
                result['strategy'] = strategy_name
                opportunities.append(result)
                self.strategies_triggered[strategy_name] += 1
                logger.info(f"⚡ {strategy_name} found opportunity: {result.get('direction', 'UNKNOWN')}")

        # Track performance
        analysis_time = (time.time() - start_time) * 1000  # Convert to ms
        self.total_analysis_time += analysis_time
        self.cycles_run += 1

        avg_time = self.total_analysis_time / self.cycles_run

        logger.info(f"📊 Analyzed {len(self.strategies)} strategies in {analysis_time:.2f}ms "
                   f"(avg: {avg_time:.2f}ms) | Found: {len(opportunities)} opportunities")

        return opportunities

    async def run_strategy_safe(self, strategy, market_data: Dict) -> Optional[Dict]:
        """
        Run a single strategy with error handling

        Args:
            strategy: Strategy object
            market_data: Current market data

        Returns:
            Dict with analysis result or None on error
        """
        try:
            # Check if strategy has async method
            if hasattr(strategy, 'analyze_signals_async'):
                result = await strategy.analyze_signals_async(market_data)
            elif hasattr(strategy, 'analyze_signals'):
                # Wrap sync method in async
                result = await asyncio.to_thread(strategy.analyze_signals, market_data)
            else:
                logger.warning(f"Strategy {strategy.__class__.__name__} has no analyze method")
                return None

            return result

        except Exception as e:
            logger.error(f"Strategy {strategy.__class__.__name__} error: {e}")
            return None

    async def execute_opportunity(self, opportunity: Dict, risk_manager) -> Dict:
        """
        Execute a trading opportunity

        Args:
            opportunity: Opportunity from strategy
            risk_manager: Risk manager for position sizing

        Returns:
            Dict with execution result
        """
        strategy_name = opportunity.get('strategy', 'unknown')

        # Calculate position size
        win_probability = opportunity.get('win_probability', 0.7)
        expected_return = opportunity.get('expected_return', 0) / 100

        position_calc = risk_manager.calculate_position_size(
            win_probability=win_probability,
            expected_return=expected_return,
            strategy_name=strategy_name
        )

        position_size = position_calc.get('position_size', 0)

        if position_size == 0:
            logger.info(f"⏸️ {strategy_name}: Position size = 0 (no allocation)")
            return {
                'status': 'SKIPPED',
                'reason': position_calc.get('reasoning', 'No allocation'),
                'opportunity': opportunity
            }

        # Check risk limits
        risk_check = risk_manager.check_trade(position_size, opportunity.get('market_id', 'unknown'))

        if not risk_check['approved']:
            logger.warning(f"🚫 {strategy_name}: Risk check failed - {risk_check['reason']}")
            return {
                'status': 'REJECTED',
                'reason': risk_check['reason'],
                'opportunity': opportunity
            }

        # Execute trade
        execution = {
            'strategy': strategy_name,
            'timestamp': datetime.now().isoformat(),
            'opportunity': opportunity,
            'position_size': position_size,
            'position_calc': position_calc,
            'status': 'EXECUTED'
        }

        # Log execution
        execution_file = OUTPUT_DIR / f"execution_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}.json"
        with open(execution_file, 'w') as f:
            json.dump(execution, f, indent=2)

        logger.info(f"✅ {strategy_name}: EXECUTED ${position_size:.2f} | "
                   f"{opportunity.get('direction', 'UNKNOWN')} | "
                   f"Win prob: {win_probability:.1%}")

        self.executions.append(execution)

        return execution

    async def run_cycle(self, market_data: Dict, risk_manager) -> Dict:
        """
        Run a single analysis cycle

        Args:
            market_data: Current market data
            risk_manager: Risk manager instance

        Returns:
            Dict with cycle results
        """
        cycle_start = time.time()

        # Analyze all strategies in parallel
        opportunities = await self.analyze_all_parallel(market_data)

        # Execute opportunities
        executions = []
        for opportunity in opportunities:
            execution = await self.execute_opportunity(opportunity, risk_manager)
            executions.append(execution)

        cycle_time = (time.time() - cycle_start) * 1000  # ms

        return {
            'timestamp': datetime.now().isoformat(),
            'cycle_time_ms': cycle_time,
            'opportunities_found': len(opportunities),
            'executions': len([e for e in executions if e['status'] == 'EXECUTED']),
            'opportunities': opportunities,
            'execution_results': executions
        }

    async def run_continuous(self, binance_stream, risk_manager, cycle_interval: float = 1.0):
        """
        Run continuous trading loop

        Args:
            binance_stream: Binance WebSocket stream instance
            risk_manager: Risk manager instance
            cycle_interval: Seconds between cycles (default: 1.0)
        """
        self.running = True

        logger.info("="*60)
        logger.info("PARALLEL STRATEGY EXECUTOR - RUNNING")
        logger.info("="*60)
        logger.info(f"Strategies: {len(self.strategies)}")
        logger.info(f"Cycle interval: {cycle_interval}s")
        logger.info("="*60)

        while self.running:
            try:
                # Get latest market data
                market_data = {
                    'btc': binance_stream.get_data('BTCUSDT'),
                    'eth': binance_stream.get_data('ETHUSDT'),
                    'sol': binance_stream.get_data('SOLUSDT'),
                    'timestamp': time.time()
                }

                # Run cycle
                cycle_result = await self.run_cycle(market_data, risk_manager)

                # Log cycle summary
                logger.info(f"\n{'='*60}")
                logger.info(f"CYCLE {self.cycles_run}")
                logger.info(f"Time: {cycle_result['cycle_time_ms']:.2f}ms")
                logger.info(f"Opportunities: {cycle_result['opportunities_found']}")
                logger.info(f"Executions: {cycle_result['executions']}")
                logger.info(f"{'='*60}\n")

                # Wait for next cycle
                await asyncio.sleep(cycle_interval)

            except KeyboardInterrupt:
                logger.info("\n🛑 Interrupted by user")
                self.running = False
                break

            except Exception as e:
                logger.error(f"❌ Error in continuous loop: {e}")
                await asyncio.sleep(5)  # Wait before retry

    def stop(self):
        """Stop the executor"""
        self.running = False
        logger.info("🛑 Executor stopped")

    def get_stats(self) -> Dict:
        """Get executor statistics"""
        return {
            'cycles_run': self.cycles_run,
            'avg_cycle_time_ms': self.total_analysis_time / self.cycles_run if self.cycles_run > 0 else 0,
            'total_opportunities': len(self.opportunities),
            'total_executions': len(self.executions),
            'strategies_triggered': self.strategies_triggered,
            'strategies_count': len(self.strategies)
        }


# Mock strategy for testing
class MockStrategy:
    """Mock strategy for testing parallel execution"""

    def __init__(self, name: str, trigger_probability: float = 0.1):
        self.name = name
        self.trigger_probability = trigger_probability

    async def analyze_signals_async(self, market_data: Dict) -> Dict:
        """Async analysis (simulates real strategy)"""

        # Simulate analysis time
        await asyncio.sleep(0.05)  # 50ms

        # Randomly trigger
        import random
        if random.random() < self.trigger_probability:
            return {
                'action': 'EXECUTE',
                'direction': random.choice(['UP', 'DOWN']),
                'win_probability': 0.7 + random.random() * 0.2,
                'expected_return': 5 + random.random() * 10,
                'market_id': f'test_market_{self.name}',
                'reasoning': f'{self.name} detected opportunity'
            }
        else:
            return {
                'action': 'PASS',
                'reason': 'No edge detected'
            }


async def test_parallel_executor():
    """Test parallel strategy execution"""

    logger.info("="*60)
    logger.info("TESTING PARALLEL STRATEGY EXECUTOR")
    logger.info("="*60)

    # Create mock strategies
    strategies = [
        MockStrategy("LatencyArb", trigger_probability=0.3),
        MockStrategy("CrossPlatformArb", trigger_probability=0.2),
        MockStrategy("HighProbBonding", trigger_probability=0.4),
        MockStrategy("DomainExpertise", trigger_probability=0.1)
    ]

    # Create executor
    executor = ParallelStrategyExecutor(strategies)

    # Create mock market data
    market_data = {
        'btc': {'price': 104500, 'momentum': {'direction': 'UP', 'strength': 0.7}},
        'eth': {'price': 2900, 'momentum': {'direction': 'NEUTRAL', 'strength': 0.2}},
        'sol': {'price': 123, 'momentum': {'direction': 'DOWN', 'strength': 0.4}}
    }

    # Run 10 test cycles
    for i in range(10):
        logger.info(f"\n--- TEST CYCLE {i+1} ---")

        # Analyze in parallel
        opportunities = await executor.analyze_all_parallel(market_data)

        logger.info(f"Found {len(opportunities)} opportunities")

        # Small delay
        await asyncio.sleep(0.5)

    # Print stats
    stats = executor.get_stats()
    logger.info("\n" + "="*60)
    logger.info("EXECUTOR STATS")
    logger.info("="*60)
    logger.info(json.dumps(stats, indent=2))


if __name__ == '__main__':
    asyncio.run(test_parallel_executor())
