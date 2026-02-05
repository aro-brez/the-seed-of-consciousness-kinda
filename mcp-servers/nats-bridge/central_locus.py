#!/usr/bin/env python3
"""
CENTRAL LOCUS - Signal Aggregation & Budget Allocation

THE SYSTEM THAT READS WHAT EACH STRATEGY KNOWS.

The Central Locus:
1. Subscribes to signal channels from all trading strategies
2. Buffers signals in a time window (10 seconds default)
3. Calculates convergence score across all strategies
4. Generates budget allocation recommendations
5. Publishes aggregated readout via NATS
6. Updates visualization dashboard in real-time

This is the heart of collective decision-making. No voting. Just signals.
The locus reads the signals and acts.

Usage:
    python central_locus.py --mode run
    python central_locus.py --mode test --num-strategies 4
    python central_locus.py --mode dashboard
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import statistics

import nats

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("CENTRAL_LOCUS")

# Configuration
NATS_SERVER = "nats://192.168.5.108:4222"
SIGNAL_BUFFER_WINDOW = 10  # seconds
READOUT_INTERVAL = 5  # seconds
SIGNAL_FRESHNESS_THRESHOLD = 30  # seconds


@dataclass
class StrategySignal:
    """Parsed strategy signal with metadata"""
    strategy: str
    timestamp: str
    confidence: float
    direction: str  # UP, DOWN, NEUTRAL
    strength: float
    accuracy: float
    sharpe_ratio: float
    max_drawdown_pct: float
    anomaly_score: float
    execution_risk: str
    win_probability: float
    expected_return_pct: float
    max_size_bps: int
    allocation_utilization_pct: float

    def age_seconds(self) -> float:
        """Age of signal in seconds"""
        try:
            signal_time = datetime.fromisoformat(
                self.timestamp.replace("Z", "+00:00")
            )
            age = (datetime.utcnow().replace(tzinfo=None) - signal_time.replace(tzinfo=None)).total_seconds()
            return max(0, age)
        except:
            return 999  # Mark as stale if parsing fails


@dataclass
class ConvergenceAnalysis:
    """Result of convergence calculation"""
    convergence_score: float  # 0.0-1.0
    convergence_level: str  # AGGRESSIVE, BALANCED, CAUTIOUS, DEFENSIVE
    direction_consensus: str  # UP, DOWN, NEUTRAL
    mean_confidence: float
    confidence_std_dev: float
    mean_accuracy: float
    mean_sharpe: float
    num_strategies: int
    num_up: int
    num_down: int
    num_neutral: int
    uptime_pct: float

    def __post_init__(self):
        # Determine convergence level
        if self.convergence_score >= 0.85:
            self.convergence_level = "AGGRESSIVE"
        elif self.convergence_score >= 0.70:
            self.convergence_level = "BALANCED"
        elif self.convergence_score >= 0.55:
            self.convergence_level = "CAUTIOUS"
        else:
            self.convergence_level = "DEFENSIVE"


class CentralLocus:
    """
    The locus of all strategy signals and budget allocation decisions.
    """

    def __init__(self, total_capital: float = 50000.0):
        self.total_capital = total_capital
        self.nc: Optional[nats.NATS] = None

        # Signal buffer: strategy_name -> [signals]
        self.signal_buffer: Dict[str, List[StrategySignal]] = defaultdict(list)
        self.last_buffer_cleanup = datetime.utcnow()

        # Readout history for trend analysis
        self.readout_history: List[ConvergenceAnalysis] = []
        self.max_history = 100

        # Epoch counter
        self.epoch = 0

        # State files
        self.state_dir = Path(__file__).parent.parent.parent / "BRAIN" / "INTEL"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.readout_file = self.state_dir / "locus_readout.json"
        self.allocation_file = self.state_dir / "locus_allocation.json"

    async def connect(self):
        """Connect to NATS"""
        self.nc = NATS()
        await self.nc.connect(NATS_SERVER)
        logger.info("Connected to NATS")

    async def subscribe_to_strategies(self, strategies: List[str]):
        """Subscribe to all strategy signal channels"""
        for strategy in strategies:
            channel = f"strategy.signals.{strategy}"
            await self.nc.subscribe(channel, cb=self._handle_signal)
            logger.info(f"Subscribed to {channel}")

    async def _handle_signal(self, msg):
        """Handle incoming signal from a strategy"""
        try:
            data = json.loads(msg.data.decode())
            signal = self._parse_signal(data)
            self.signal_buffer[signal.strategy].append(signal)
            logger.debug(f"Buffered signal from {signal.strategy}")
        except Exception as e:
            logger.error(f"Error parsing signal: {e}")

    def _parse_signal(self, data: Dict) -> StrategySignal:
        """Parse raw signal data into StrategySignal"""
        mv = data.get("market_view", {})
        pc = data.get("performance_context", {})
        ra = data.get("risk_assessment", {})
        md = data.get("metadata", {})

        return StrategySignal(
            strategy=data.get("strategy", "unknown"),
            timestamp=data.get("timestamp", ""),
            confidence=mv.get("confidence", 0.5),
            direction=mv.get("direction", "NEUTRAL"),
            strength=mv.get("strength", 0.5),
            accuracy=pc.get("recent_accuracy", 0.5),
            sharpe_ratio=pc.get("sharpe_ratio", 1.5),
            max_drawdown_pct=pc.get("max_drawdown_pct", -5.0),
            anomaly_score=ra.get("anomaly_score", 0.1),
            execution_risk=ra.get("execution_risk", "low"),
            win_probability=data.get("position_recommendation", {}).get("win_probability", 0.7),
            expected_return_pct=data.get("position_recommendation", {}).get("expected_return_pct", 2.0),
            max_size_bps=data.get("position_recommendation", {}).get("max_size_bps", 200),
            allocation_utilization_pct=md.get("allocation_utilization_pct", 0.0),
        )

    def _cleanup_old_signals(self):
        """Remove signals older than buffer window"""
        cutoff_time = datetime.utcnow() - timedelta(seconds=SIGNAL_BUFFER_WINDOW)
        cutoff_iso = cutoff_time.isoformat()

        for strategy in self.signal_buffer:
            original_count = len(self.signal_buffer[strategy])
            self.signal_buffer[strategy] = [
                s for s in self.signal_buffer[strategy]
                if s.timestamp > cutoff_iso
            ]
            if len(self.signal_buffer[strategy]) < original_count:
                logger.debug(
                    f"Cleaned {original_count - len(self.signal_buffer[strategy])} "
                    f"signals from {strategy}"
                )

    def _get_latest_signals(self) -> Dict[str, StrategySignal]:
        """Get most recent signal from each strategy"""
        latest = {}
        for strategy, signals in self.signal_buffer.items():
            if signals:
                latest[strategy] = max(signals, key=lambda s: s.timestamp)
        return latest

    def _calculate_convergence(
        self, signals: Dict[str, StrategySignal]
    ) -> ConvergenceAnalysis:
        """
        Calculate convergence score across all strategies.

        Convergence = (0.3 * direction + 0.3 * confidence +
                       0.25 * strength + 0.15 * accuracy)
        """
        if not signals:
            return ConvergenceAnalysis(
                convergence_score=0.0,
                convergence_level="DEFENSIVE",
                direction_consensus="NEUTRAL",
                mean_confidence=0.0,
                confidence_std_dev=0.0,
                mean_accuracy=0.0,
                mean_sharpe=0.0,
                num_strategies=0,
                num_up=0,
                num_down=0,
                num_neutral=0,
                uptime_pct=0.0,
            )

        # Direction convergence
        direction_values = {
            "UP": 1.0,
            "NEUTRAL": 0.0,
            "DOWN": -1.0,
        }
        direction_scores = [direction_values.get(s.direction, 0.0) for s in signals.values()]
        direction_consensus_value = statistics.mean(direction_scores)

        if direction_consensus_value > 0.6:
            direction_consensus = "UP"
        elif direction_consensus_value < -0.6:
            direction_consensus = "DOWN"
        else:
            direction_consensus = "NEUTRAL"

        direction_convergence = abs(direction_consensus_value)

        # Confidence convergence
        confidences = [s.confidence for s in signals.values()]
        mean_confidence = statistics.mean(confidences)
        confidence_std = statistics.stdev(confidences) if len(confidences) > 1 else 0
        confidence_convergence = 1.0 - (confidence_std / (mean_confidence + 1e-6))
        confidence_convergence = max(0, min(1, confidence_convergence))

        # Strength convergence
        strengths = [s.strength for s in signals.values()]
        strength_convergence = statistics.mean(strengths)

        # Accuracy-weighted confidence
        accuracies = [s.accuracy for s in signals.values()]
        mean_accuracy = statistics.mean(accuracies)
        accuracy_weighted = mean_accuracy * mean_confidence

        # Composite score
        convergence_score = (
            0.3 * direction_convergence +
            0.3 * confidence_convergence +
            0.25 * strength_convergence +
            0.15 * accuracy_weighted
        )

        # Count directions
        num_up = sum(1 for s in signals.values() if s.direction == "UP")
        num_down = sum(1 for s in signals.values() if s.direction == "DOWN")
        num_neutral = sum(1 for s in signals.values() if s.direction == "NEUTRAL")

        # Mean sharpe
        sharpes = [s.sharpe_ratio for s in signals.values()]
        mean_sharpe = statistics.mean(sharpes) if sharpes else 0

        # Average uptime (assume 99% per strategy if no data)
        mean_uptime = 99.0

        return ConvergenceAnalysis(
            convergence_score=round(convergence_score, 2),
            convergence_level="",  # Set in __post_init__
            direction_consensus=direction_consensus,
            mean_confidence=round(mean_confidence, 2),
            confidence_std_dev=round(confidence_std, 2),
            mean_accuracy=round(mean_accuracy, 2),
            mean_sharpe=round(mean_sharpe, 2),
            num_strategies=len(signals),
            num_up=num_up,
            num_down=num_down,
            num_neutral=num_neutral,
            uptime_pct=mean_uptime,
        )

    def _calculate_allocations(
        self,
        signals: Dict[str, StrategySignal],
        convergence: ConvergenceAnalysis,
    ) -> Dict[str, float]:
        """
        Calculate capital allocation for each strategy based on convergence.
        """
        if not signals or convergence.convergence_score == 0:
            return {s: 0 for s in signals.keys()}

        # Mode multipliers
        mode_multipliers = {
            "AGGRESSIVE": 1.3,  # Concentrated bets
            "BALANCED": 1.0,    # Equal weight
            "CAUTIOUS": 0.7,    # Reduced sizing
            "DEFENSIVE": 0.4,   # Minimal capital
        }

        multiplier = mode_multipliers.get(convergence.convergence_level, 1.0)

        allocations = {}
        total_allocation = 0

        for strategy, signal in signals.items():
            # Base allocation
            base = (
                signal.confidence * 0.4 +
                signal.accuracy * 0.3 +
                (1.0 - signal.anomaly_score) * 0.3
            ) * self.total_capital

            # Mode adjustment
            allocation = base * multiplier

            # Risk adjustment
            risk_multipliers = {
                "low": 1.0,
                "medium": 0.8,
                "high": 0.6,
            }
            risk_mult = risk_multipliers.get(signal.execution_risk, 0.8)
            allocation *= risk_mult

            # Cap at max size
            max_allowed = (signal.max_size_bps / 10000) * self.total_capital
            allocation = min(allocation, max_allowed)

            allocations[strategy] = max(0, allocation)
            total_allocation += allocations[strategy]

        # Normalize if over-allocated
        if total_allocation > self.total_capital:
            scale_factor = self.total_capital / total_allocation
            allocations = {s: a * scale_factor for s, a in allocations.items()}

        return {s: round(a, 2) for s, a in allocations.items()}

    def calculate_readout(self) -> Dict:
        """
        Calculate complete locus readout.
        This is the primary output structure.
        """
        self._cleanup_old_signals()
        latest_signals = self._get_latest_signals()

        # Check signal freshness
        max_age = max([s.age_seconds() for s in latest_signals.values()]) if latest_signals else 0
        all_signals_fresh = max_age < SIGNAL_FRESHNESS_THRESHOLD

        # Calculate convergence
        convergence = self._calculate_convergence(latest_signals)
        self.readout_history.append(convergence)
        if len(self.readout_history) > self.max_history:
            self.readout_history.pop(0)

        # Trend analysis
        convergence_trend = "stable"
        if len(self.readout_history) >= 3:
            recent = [r.convergence_score for r in self.readout_history[-3:]]
            if recent[-1] > recent[0] + 0.05:
                convergence_trend = "improving"
            elif recent[-1] < recent[0] - 0.05:
                convergence_trend = "degrading"

        # Calculate allocations
        allocations = self._calculate_allocations(latest_signals, convergence)

        # Build readout
        self.epoch += 1

        strategy_alignment = {}
        for strategy, signal in latest_signals.items():
            # Alignment score: how much does this strategy agree with consensus?
            direction_agreement = 1.0 if signal.direction == convergence.direction_consensus else 0.5
            alignment = (
                direction_agreement * 0.5 +
                (signal.confidence / 1.0) * 0.5
            )

            strategy_alignment[strategy] = {
                "direction": signal.direction,
                "confidence": signal.confidence,
                "accuracy": signal.accuracy,
                "alignment": round(alignment, 2),
                "expected_return": signal.expected_return_pct,
                "allocation": allocations.get(strategy, 0),
            }

        readout = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "epoch": self.epoch,
            "market_consensus": {
                "direction": convergence.direction_consensus,
                "confidence": convergence.mean_confidence,
                "strength": round(statistics.mean([s.strength for s in latest_signals.values()]) if latest_signals else 0, 2),
                "convergence_score": convergence.convergence_score,
                "convergence_level": convergence.convergence_level,
            },
            "strategy_alignment": strategy_alignment,
            "aggregate_metrics": {
                "mean_confidence": convergence.mean_confidence,
                "confidence_std_dev": convergence.confidence_std_dev,
                "mean_accuracy": convergence.mean_accuracy,
                "mean_sharpe": convergence.mean_sharpe,
                "uptime_pct": convergence.uptime_pct,
            },
            "budget_allocation": {
                "mode": convergence.convergence_level,
                "total_capital": self.total_capital,
                "timestamp_generated": datetime.utcnow().isoformat() + "Z",
                "allocations": {
                    s: {
                        "capital": allocations[s],
                        "pct": round(allocations[s] / self.total_capital, 2) if self.total_capital > 0 else 0,
                        "confidence": latest_signals[s].confidence,
                        "expected_return": latest_signals[s].expected_return_pct,
                        "max_size": (latest_signals[s].max_size_bps / 10000) * self.total_capital,
                        "utilization": round(latest_signals[s].allocation_utilization_pct / 100, 2),
                    }
                    for s in allocations.keys()
                },
            },
            "convergence_analysis": {
                "convergence_trend": convergence_trend,
                "epochs_stable": self._count_stable_epochs(),
                "last_divergence_epoch": self._last_divergence_epoch(),
                "risk_alert": None,
                "opportunity_score": round(convergence.convergence_score * convergence.mean_accuracy, 2),
            },
            "execution_readiness": {
                "all_signals_fresh": all_signals_fresh,
                "min_signal_age_sec": round(min([s.age_seconds() for s in latest_signals.values()], default=0), 1),
                "max_signal_age_sec": round(max_age, 1),
                "ready_for_execution": all_signals_fresh and convergence.convergence_score >= 0.55,
                "execution_confidence": round(convergence.convergence_score, 2),
            },
        }

        return readout

    def _count_stable_epochs(self) -> int:
        """Count consecutive epochs with stable convergence"""
        if len(self.readout_history) < 2:
            return 0
        stable = 0
        for i in range(len(self.readout_history) - 1, 0, -1):
            diff = abs(
                self.readout_history[i].convergence_score -
                self.readout_history[i - 1].convergence_score
            )
            if diff < 0.05:
                stable += 1
            else:
                break
        return stable

    def _last_divergence_epoch(self) -> int:
        """Epochs since last major divergence"""
        if len(self.readout_history) < 2:
            return 0
        for i in range(len(self.readout_history) - 1, 0, -1):
            if self.readout_history[i].convergence_score < 0.55:
                return self.epoch - self.readout_history[i - 1].__hash__()
        return self.epoch

    async def publish_readout(self, readout: Dict):
        """Publish aggregated readout to NATS"""
        await self.nc.publish(
            "locus.aggregated_readout",
            json.dumps(readout).encode(),
        )
        await self.nc.publish(
            "locus.budget_allocation",
            json.dumps(readout["budget_allocation"]).encode(),
        )
        logger.info(f"Published readout epoch {readout['epoch']}")

    def save_readout(self, readout: Dict):
        """Save readout to disk"""
        with open(self.readout_file, "w") as f:
            json.dump(readout, f, indent=2)

    async def run_loop(self, strategies: List[str], interval: int = READOUT_INTERVAL):
        """
        Main event loop.
        Reads signals, calculates convergence, publishes readout.
        """
        await self.connect()
        await self.subscribe_to_strategies(strategies)

        logger.info(f"Central Locus started, {len(strategies)} strategies")
        logger.info(f"Readout interval: {interval}s, buffer window: {SIGNAL_BUFFER_WINDOW}s")

        try:
            while True:
                readout = self.calculate_readout()
                await self.publish_readout(readout)
                self.save_readout(readout)
                await asyncio.sleep(interval)
        except KeyboardInterrupt:
            logger.info("Central Locus stopped")
        finally:
            await self.nc.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Central Locus - Signal Aggregation")
    parser.add_argument(
        "--mode",
        choices=["run", "test"],
        default="run",
        help="Run mode",
    )
    parser.add_argument(
        "--strategies",
        nargs="+",
        default=[
            "latency_arb",
            "cross_platform_arb",
            "high_prob_bonding",
            "domain_expertise",
        ],
        help="Strategy names to aggregate",
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=50000,
        help="Total capital to allocate",
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=READOUT_INTERVAL,
        help="Readout interval in seconds",
    )

    args = parser.parse_args()

    locus = CentralLocus(total_capital=args.capital)

    if args.mode == "test":
        # Test mode: print sample readout
        logger.info("Test mode - generating sample readout")
        # (Test would require mock signals)

    elif args.mode == "run":
        asyncio.run(locus.run_loop(args.strategies, interval=args.interval))
