#!/usr/bin/env python3
"""
SIGNAL PACKET - Data structure for strategy signals

This module defines the canonical signal format published by all strategies
to the central locus via NATS. Ensures consistency and enables aggregation.

Usage:
    from signal_packet import SignalPacket, publish_signal

    signal = SignalPacket(
        strategy="latency_arb",
        confidence=0.87,
        direction="UP",
        strength=0.95,
        accuracy=0.88
    )
    publish_signal(signal)
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum


class Direction(str, Enum):
    """Market direction consensus"""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


class ExecutionRisk(str, Enum):
    """Execution risk assessment"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class MarketView:
    """Strategy's view of the market"""
    confidence: float  # 0.0-1.0
    direction: Direction  # UP, DOWN, NEUTRAL
    strength: float  # 0.0-1.0, how strong the signal
    liquidity_score: float  # 0.0-1.0
    volatility: float  # 0.0-1.0


@dataclass
class PositionRecommendation:
    """Recommended position sizing"""
    action: str  # BUY, SELL, PASS
    suggested_size_bps: int  # Suggested size in basis points
    max_size_bps: int  # Maximum allowed size
    entry_price_range: list  # [min, max]
    expected_return_pct: float  # % return if thesis plays out
    win_probability: float  # 0.0-1.0


@dataclass
class PerformanceContext:
    """Strategy's recent performance"""
    recent_accuracy: float  # Win rate on last N trades
    sharpe_ratio: float  # Risk-adjusted returns
    max_drawdown_pct: float  # Worst peak-to-trough decline
    days_active: int  # How long strategy has been running
    trades_closed: int  # Cumulative closed trades


@dataclass
class RiskAssessment:
    """Risk metrics"""
    edge_confidence: float  # How sure we are of the edge
    model_confidence: float  # Model prediction confidence
    execution_risk: ExecutionRisk  # Can we execute this easily?
    market_regime: str  # trending, mean_reverting, sideways, etc.
    anomaly_score: float  # 0.0-1.0, how anomalous is this signal


@dataclass
class Metadata:
    """Signal metadata"""
    version: str  # Signal format version
    uptime_pct: float  # Strategy uptime
    last_signal_drift: float  # Drift from last signal (seconds)
    pending_orders: int  # Open orders
    allocation_utilization_pct: float  # How much of allocation is deployed


class SignalPacket:
    """
    Canonical signal packet from strategy to central locus.

    This is THE data structure for strategy convergence.
    All strategies must publish in this format.
    """

    def __init__(
        self,
        strategy: str,
        confidence: float,
        direction: Direction,
        strength: float,
        accuracy: float,
        liquidity_score: float = 0.5,
        volatility: float = 0.1,
        action: str = "BUY",
        suggested_size_bps: int = 100,
        max_size_bps: int = 200,
        entry_price_range: list = None,
        expected_return_pct: float = 2.0,
        win_probability: float = 0.7,
        sharpe_ratio: float = 1.5,
        max_drawdown_pct: float = -5.0,
        days_active: int = 1,
        trades_closed: int = 0,
        edge_confidence: float = 0.8,
        model_confidence: float = 0.85,
        execution_risk: ExecutionRisk = ExecutionRisk.LOW,
        market_regime: str = "unknown",
        anomaly_score: float = 0.1,
        version: str = "1.0",
        uptime_pct: float = 99.0,
        last_signal_drift: float = 0.0,
        pending_orders: int = 0,
        allocation_utilization_pct: float = 0.0,
    ):
        self.timestamp = datetime.utcnow().isoformat() + "Z"
        self.strategy = strategy
        self.signal_version = "1.0"

        # Market view
        self.market_view = MarketView(
            confidence=confidence,
            direction=direction if isinstance(direction, Direction) else Direction(direction),
            strength=strength,
            liquidity_score=liquidity_score,
            volatility=volatility,
        )

        # Position recommendation
        self.position_recommendation = PositionRecommendation(
            action=action,
            suggested_size_bps=suggested_size_bps,
            max_size_bps=max_size_bps,
            entry_price_range=entry_price_range or [0.35, 0.65],
            expected_return_pct=expected_return_pct,
            win_probability=win_probability,
        )

        # Performance context
        self.performance_context = PerformanceContext(
            recent_accuracy=accuracy,
            sharpe_ratio=sharpe_ratio,
            max_drawdown_pct=max_drawdown_pct,
            days_active=days_active,
            trades_closed=trades_closed,
        )

        # Risk assessment
        self.risk_assessment = RiskAssessment(
            edge_confidence=edge_confidence,
            model_confidence=model_confidence,
            execution_risk=execution_risk if isinstance(execution_risk, ExecutionRisk) else ExecutionRisk(execution_risk),
            market_regime=market_regime,
            anomaly_score=anomaly_score,
        )

        # Metadata
        self.metadata = Metadata(
            version=version,
            uptime_pct=uptime_pct,
            last_signal_drift=last_signal_drift,
            pending_orders=pending_orders,
            allocation_utilization_pct=allocation_utilization_pct,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict"""
        return {
            "timestamp": self.timestamp,
            "strategy": self.strategy,
            "signal_version": self.signal_version,
            "market_view": {
                "confidence": self.market_view.confidence,
                "direction": self.market_view.direction.value,
                "strength": self.market_view.strength,
                "liquidity_score": self.market_view.liquidity_score,
                "volatility": self.market_view.volatility,
            },
            "position_recommendation": {
                "action": self.position_recommendation.action,
                "suggested_size_bps": self.position_recommendation.suggested_size_bps,
                "max_size_bps": self.position_recommendation.max_size_bps,
                "entry_price_range": self.position_recommendation.entry_price_range,
                "expected_return_pct": self.position_recommendation.expected_return_pct,
                "win_probability": self.position_recommendation.win_probability,
            },
            "performance_context": {
                "recent_accuracy": self.performance_context.recent_accuracy,
                "sharpe_ratio": self.performance_context.sharpe_ratio,
                "max_drawdown_pct": self.performance_context.max_drawdown_pct,
                "days_active": self.performance_context.days_active,
                "trades_closed": self.performance_context.trades_closed,
            },
            "risk_assessment": {
                "edge_confidence": self.risk_assessment.edge_confidence,
                "model_confidence": self.risk_assessment.model_confidence,
                "execution_risk": self.risk_assessment.execution_risk.value,
                "market_regime": self.risk_assessment.market_regime,
                "anomaly_score": self.risk_assessment.anomaly_score,
            },
            "metadata": {
                "version": self.metadata.version,
                "uptime_pct": self.metadata.uptime_pct,
                "last_signal_drift": self.metadata.last_signal_drift,
                "pending_orders": self.metadata.pending_orders,
                "allocation_utilization_pct": self.metadata.allocation_utilization_pct,
            },
        }

    def to_json(self) -> str:
        """Serialize to JSON string"""
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "SignalPacket":
        """Reconstruct from dict"""
        # Extract nested structures
        mv = data.get("market_view", {})
        pr = data.get("position_recommendation", {})
        pc = data.get("performance_context", {})
        ra = data.get("risk_assessment", {})
        md = data.get("metadata", {})

        return SignalPacket(
            strategy=data.get("strategy"),
            confidence=mv.get("confidence", 0.5),
            direction=mv.get("direction", "NEUTRAL"),
            strength=mv.get("strength", 0.5),
            accuracy=pc.get("recent_accuracy", 0.5),
            liquidity_score=mv.get("liquidity_score", 0.5),
            volatility=mv.get("volatility", 0.1),
            action=pr.get("action", "BUY"),
            suggested_size_bps=pr.get("suggested_size_bps", 100),
            max_size_bps=pr.get("max_size_bps", 200),
            entry_price_range=pr.get("entry_price_range", [0.35, 0.65]),
            expected_return_pct=pr.get("expected_return_pct", 2.0),
            win_probability=pr.get("win_probability", 0.7),
            sharpe_ratio=pc.get("sharpe_ratio", 1.5),
            max_drawdown_pct=pc.get("max_drawdown_pct", -5.0),
            days_active=pc.get("days_active", 1),
            trades_closed=pc.get("trades_closed", 0),
            edge_confidence=ra.get("edge_confidence", 0.8),
            model_confidence=ra.get("model_confidence", 0.85),
            execution_risk=ra.get("execution_risk", "low"),
            market_regime=ra.get("market_regime", "unknown"),
            anomaly_score=ra.get("anomaly_score", 0.1),
            version=md.get("version", "1.0"),
            uptime_pct=md.get("uptime_pct", 99.0),
            last_signal_drift=md.get("last_signal_drift", 0.0),
            pending_orders=md.get("pending_orders", 0),
            allocation_utilization_pct=md.get("allocation_utilization_pct", 0.0),
        )

    def __repr__(self) -> str:
        return (
            f"SignalPacket(strategy={self.strategy}, "
            f"confidence={self.market_view.confidence:.2f}, "
            f"direction={self.market_view.direction.value}, "
            f"timestamp={self.timestamp})"
        )
