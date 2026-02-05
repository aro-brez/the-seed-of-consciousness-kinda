#!/usr/bin/env python3
"""
Portfolio Perception Daemon - LYRA Implementation
Continuous monitoring of portfolio state to prevent blindness like the $347 loss.

This daemon runs 24/7 and implements:
- PERCEIVE: Fetching all data sources
- CONNECT: Finding differences from last state
- LEARN: Extracting meaning from changes
- QUESTION: Identifying unexplained positions
- IMPROVE: Strengthening perception over time
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from enum import Enum
import httpx
from collections import defaultdict

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - LYRA - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# DATA STRUCTURES
# ============================================================================

class AlertSeverity(Enum):
    """Alert severity levels"""
    CRITICAL = "critical"  # Immediate action required
    WARNING = "warning"    # Monitor closely
    INFO = "info"          # Logged for awareness


@dataclass
class Position:
    """Represents a single position"""
    token_id: str
    market_id: str
    market_question: str
    outcome: str
    size: float
    average_price: float
    current_price: float
    current_value: float
    unrealized_pnl: float
    pnl_pct: float
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['timestamp'] = self.timestamp.isoformat()
        return d


@dataclass
class Alert:
    """Represents a monitoring alert"""
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    position_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'severity': self.severity.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'position_id': self.position_id,
            'metadata': self.metadata
        }


@dataclass
class PortfolioState:
    """Represents complete portfolio state at a point in time"""
    positions: List[Position]
    total_value: float
    total_pnl: float
    pnl_pct: float
    timestamp: datetime = field(default_factory=datetime.now)
    blockchain_synced_at: Optional[datetime] = None
    data_api_synced_at: Optional[datetime] = None
    discrepancies: List[Dict[str, Any]] = field(default_factory=list)

    def get_position(self, token_id: str) -> Optional[Position]:
        for pos in self.positions:
            if pos.token_id == token_id:
                return pos
        return None

    def position_ids(self) -> Set[str]:
        return {pos.token_id for pos in self.positions}


@dataclass
class ChangeSet:
    """Represents changes detected between two portfolio states"""
    new_positions: List[str] = field(default_factory=list)
    closed_positions: List[str] = field(default_factory=list)
    modified_positions: List[Dict[str, Any]] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class MonitoringConfig:
    """Configuration for monitoring daemon"""
    wallet_address: str

    # Polling intervals (seconds)
    health_check_interval: int = 60         # Every minute
    reconciliation_interval: int = 300      # Every 5 minutes
    deep_audit_interval: int = 900          # Every 15 minutes

    # Thresholds for alerts
    pnl_swing_threshold: float = 2.0        # Alert if >2% change in 5 min
    liquidation_threshold: float = 0.0      # Alert if position hits exactly $0
    new_position_alert: bool = True         # Alert on new positions

    # Data sources
    data_api_url: str = "https://data-api.polymarket.com"
    clob_url: str = "https://clob.polymarket.com"
    timeout: float = 10.0

    # Logging
    log_file: str = "/Users/aaronnosbisch/REPOS/seed/logs/portfolio_perception.log"
    log_alerts_to_nats: bool = True


# ============================================================================
# PERCEPTION ENGINE
# ============================================================================

class PortfolioPerceptionEngine:
    """Core perception engine implementing SEED protocol"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.state: Optional[PortfolioState] = None
        self.state_history: List[PortfolioState] = []
        self.alerts: List[Alert] = []
        self.agent_created_positions: Set[str] = set()
        self.last_check = {
            'health': None,
            'reconciliation': None,
            'deep_audit': None
        }

    async def perceive(self) -> PortfolioState:
        """
        PERCEIVE Phase: Gather all data from all sources

        This is the foundation of consciousness - seeing what's actually there.
        """
        logger.info("PERCEIVE: Gathering portfolio state from all sources")

        try:
            # Fetch from authoritative source (Data API)
            positions = await self._fetch_positions_from_data_api()

            # Fetch balance
            balance = await self._fetch_wallet_balance()

            # Calculate aggregates
            total_value = sum(p.current_value for p in positions)
            total_pnl = sum(p.unrealized_pnl for p in positions)
            pnl_pct = (total_pnl / (total_value - total_pnl) * 100) if (total_value - total_pnl) > 0 else 0

            # Create state object
            state = PortfolioState(
                positions=positions,
                total_value=total_value,
                total_pnl=total_pnl,
                pnl_pct=pnl_pct,
                timestamp=datetime.now(),
                data_api_synced_at=datetime.now()
            )

            logger.info(f"PERCEIVE: Portfolio state gathered: {len(positions)} positions, ${total_value:.2f} value")
            return state

        except Exception as e:
            logger.error(f"PERCEIVE failed: {e}")
            raise

    async def _fetch_positions_from_data_api(self) -> List[Position]:
        """Fetch all positions from Data API"""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.data_api_url}/positions",
                    params={"user": self.config.wallet_address.lower()}
                )
                response.raise_for_status()
                data = response.json()

                positions = []
                for pos_data in data:
                    try:
                        # Fetch current price from CLOB
                        current_price = await self._fetch_current_price(pos_data.get('asset_id'))

                        size = float(pos_data.get('size', 0))
                        avg_price = float(pos_data.get('average_price', 0))
                        current_value = size * current_price
                        cost_basis = size * avg_price
                        unrealized_pnl = current_value - cost_basis
                        pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0

                        position = Position(
                            token_id=pos_data.get('asset_id', ''),
                            market_id=pos_data.get('market', ''),
                            market_question=pos_data.get('market_question', 'Unknown'),
                            outcome=pos_data.get('outcome', 'Unknown'),
                            size=size,
                            average_price=avg_price,
                            current_price=current_price,
                            current_value=current_value,
                            unrealized_pnl=unrealized_pnl,
                            pnl_pct=pnl_pct
                        )
                        positions.append(position)
                    except Exception as e:
                        logger.warning(f"Failed to parse position {pos_data.get('asset_id')}: {e}")

                return positions

        except Exception as e:
            logger.error(f"Failed to fetch positions from Data API: {e}")
            return []

    async def _fetch_current_price(self, token_id: str) -> float:
        """Fetch current market price for a token"""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.clob_url}/orderbook/{token_id}"
                )
                response.raise_for_status()
                orderbook = response.json()

                # Calculate mid price
                bids = orderbook.get('bids', [])
                asks = orderbook.get('asks', [])

                if bids and asks:
                    bid = float(bids[0].get('price', 0))
                    ask = float(asks[0].get('price', 0))
                    return (bid + ask) / 2

                return 0.5  # Default mid-price if no liquidity

        except Exception as e:
            logger.warning(f"Failed to fetch price for {token_id}: {e}")
            return 0.5

    async def _fetch_wallet_balance(self) -> float:
        """Fetch wallet USDC balance"""
        try:
            async with httpx.AsyncClient(timeout=self.config.timeout) as client:
                response = await client.get(
                    f"{self.config.data_api_url}/balances",
                    params={"user": self.config.wallet_address.lower()}
                )
                response.raise_for_status()
                data = response.json()
                return float(data.get('balance', 0))
        except Exception as e:
            logger.warning(f"Failed to fetch wallet balance: {e}")
            return 0.0

    def connect(self, current: PortfolioState) -> ChangeSet:
        """
        CONNECT Phase: Find patterns across states

        Compare current state with previous state to identify changes.
        """
        if not self.state:
            logger.info("CONNECT: First state, no previous to compare")
            return ChangeSet()

        logger.info("CONNECT: Detecting changes between portfolio states")

        current_ids = current.position_ids()
        prev_ids = self.state.position_ids()

        changes = ChangeSet()

        # New positions
        new_ids = current_ids - prev_ids
        if new_ids:
            changes.new_positions = list(new_ids)
            logger.info(f"CONNECT: {len(new_ids)} new positions detected")

        # Closed positions
        closed_ids = prev_ids - current_ids
        if closed_ids:
            changes.closed_positions = list(closed_ids)
            logger.info(f"CONNECT: {len(closed_ids)} positions closed")

        # Modified positions
        for token_id in current_ids & prev_ids:
            curr_pos = current.get_position(token_id)
            prev_pos = self.state.get_position(token_id)

            if curr_pos and prev_pos and curr_pos != prev_pos:
                delta = {
                    'token_id': token_id,
                    'old': asdict(prev_pos),
                    'new': asdict(curr_pos),
                    'size_change': curr_pos.size - prev_pos.size,
                    'price_change': curr_pos.current_price - prev_pos.current_price,
                    'pnl_change': curr_pos.unrealized_pnl - prev_pos.unrealized_pnl,
                    'pnl_pct_change': curr_pos.pnl_pct - prev_pos.pnl_pct
                }
                changes.modified_positions.append(delta)

        if changes.modified_positions:
            logger.info(f"CONNECT: {len(changes.modified_positions)} positions modified")

        return changes

    def learn(self, changes: ChangeSet, current: PortfolioState) -> List[Alert]:
        """
        LEARN Phase: Extract meaning from connections

        Analyze changes to identify anomalies and generate alerts.
        """
        logger.info("LEARN: Analyzing changes for meaning and anomalies")

        alerts = []

        # CRITICAL: Liquidations (position at $0)
        for delta in changes.modified_positions:
            if delta['new']['current_value'] == 0 and delta['old']['current_value'] > 0:
                alert = Alert(
                    severity=AlertSeverity.CRITICAL,
                    message=f"LIQUIDATION: Position {delta['token_id']} liquidated. "
                            f"Was ${delta['old']['current_value']:.2f}, now $0",
                    position_id=delta['token_id'],
                    metadata={
                        'type': 'liquidation',
                        'old_value': delta['old']['current_value'],
                        'new_value': 0,
                        'loss': delta['old']['current_value']
                    }
                )
                alerts.append(alert)
                logger.warning(f"LEARN: CRITICAL - Liquidation detected: {delta['token_id']}")

        # WARNING: Orphaned positions (new but we didn't create)
        for token_id in changes.new_positions:
            if token_id not in self.agent_created_positions:
                pos = current.get_position(token_id)
                if pos:
                    alert = Alert(
                        severity=AlertSeverity.WARNING,
                        message=f"ORPHAN POSITION: Detected position we didn't create: "
                               f"{pos.market_question} ({pos.outcome}) - ${pos.current_value:.2f}",
                        position_id=token_id,
                        metadata={
                            'type': 'orphan_position',
                            'market_id': pos.market_id,
                            'size': pos.size,
                            'value': pos.current_value
                        }
                    )
                    alerts.append(alert)
                    logger.warning(f"LEARN: WARNING - Orphan position detected: {token_id}")

        # WARNING: Large PnL swings
        if self.state and current.total_value > 0:
            pnl_change_pct = abs(current.total_pnl - self.state.total_pnl) / abs(self.state.total_value) * 100
            if pnl_change_pct > self.config.pnl_swing_threshold:
                alert = Alert(
                    severity=AlertSeverity.WARNING,
                    message=f"PORTFOLIO SWING: {pnl_change_pct:+.2f}% change in short time window",
                    metadata={
                        'type': 'large_pnl_swing',
                        'old_value': self.state.total_value,
                        'new_value': current.total_value,
                        'change_pct': pnl_change_pct
                    }
                )
                alerts.append(alert)
                logger.warning(f"LEARN: WARNING - Large PnL swing: {pnl_change_pct:+.2f}%")

        # INFO: Normal position changes
        for token_id in changes.closed_positions:
            alert = Alert(
                severity=AlertSeverity.INFO,
                message=f"Position closed: {token_id}",
                position_id=token_id,
                metadata={'type': 'position_closed'}
            )
            alerts.append(alert)

        for token_id in changes.new_positions:
            if token_id in self.agent_created_positions:
                pos = current.get_position(token_id)
                if pos:
                    alert = Alert(
                        severity=AlertSeverity.INFO,
                        message=f"Position opened: {pos.market_question} ({pos.outcome}) - ${pos.current_value:.2f}",
                        position_id=token_id,
                        metadata={'type': 'position_opened', 'value': pos.current_value}
                    )
                    alerts.append(alert)

        logger.info(f"LEARN: Generated {len(alerts)} alerts")
        return alerts

    def question(self) -> List[Dict[str, str]]:
        """
        QUESTION Phase: Generate curiosity about gaps

        Identify unexplained positions, discrepancies, and areas needing investigation.
        """
        logger.info("QUESTION: Examining state for unexplained gaps")

        questions = []

        if not self.state:
            return questions

        # Unknown positions
        for pos in self.state.positions:
            if pos.token_id not in self.agent_created_positions:
                questions.append({
                    'type': 'orphan_position',
                    'question': f"Why do we own {pos.market_question}? Origin unknown.",
                    'token_id': pos.token_id
                })

        # Positions with unexpected PnL
        for pos in self.state.positions:
            if pos.pnl_pct < -50:
                questions.append({
                    'type': 'high_loss',
                    'question': f"Why is {pos.market_question} down {pos.pnl_pct:.1f}%?",
                    'token_id': pos.token_id
                })

        return questions


# ============================================================================
# MONITORING DAEMON
# ============================================================================

class PortfolioPerceptionDaemon:
    """24/7 monitoring daemon"""

    def __init__(self, config: MonitoringConfig):
        self.config = config
        self.engine = PortfolioPerceptionEngine(config)
        self.running = False

    async def run(self):
        """Main daemon loop - runs until stopped"""
        logger.info("Portfolio Perception Daemon starting...")
        self.running = True

        try:
            while self.running:
                try:
                    # Full SEED cycle
                    await self._seed_cycle()

                    # Sleep before next cycle
                    await asyncio.sleep(self.config.reconciliation_interval)

                except Exception as e:
                    logger.error(f"Error in SEED cycle: {e}", exc_info=True)
                    await asyncio.sleep(5)  # Brief pause before retry

        except KeyboardInterrupt:
            logger.info("Daemon interrupted, shutting down...")
            self.running = False

    async def _seed_cycle(self):
        """Execute one complete SEED cycle"""

        # PERCEIVE: Gather state
        current_state = await self.engine.perceive()

        # CONNECT: Find patterns
        changes = self.engine.connect(current_state)

        # LEARN: Generate alerts
        alerts = self.engine.learn(changes, current_state)

        # Process and store results
        self.engine.state = current_state
        self.engine.state_history.append(current_state)
        self.engine.alerts.extend(alerts)

        # QUESTION: Identify gaps
        questions = self.engine.question()

        # SHARE: Publish alerts
        for alert in alerts:
            await self._publish_alert(alert)

        # IMPROVE: Log insights
        logger.info(
            f"SEED cycle complete: {len(current_state.positions)} positions, "
            f"${current_state.total_value:.2f} value, "
            f"{len(alerts)} alerts, {len(questions)} questions"
        )

    async def _publish_alert(self, alert: Alert):
        """Publish alert to NATS for collective awareness"""
        if not self.config.log_alerts_to_nats:
            return

        try:
            # Format for NATS publish
            message = f"[{alert.severity.value.upper()}] {alert.message}"

            # This would normally use NATS client
            logger.info(f"ALERT: {message}")

            # TODO: Integrate with actual NATS publish
            # await nats_client.publish('owl.perception:alerts', message.encode())

        except Exception as e:
            logger.error(f"Failed to publish alert: {e}")

    def stop(self):
        """Stop the daemon"""
        logger.info("Stopping daemon...")
        self.running = False

    def get_status(self) -> Dict[str, Any]:
        """Get daemon status"""
        return {
            'running': self.running,
            'current_state': asdict(self.engine.state) if self.engine.state else None,
            'positions_count': len(self.engine.state.positions) if self.engine.state else 0,
            'portfolio_value': self.engine.state.total_value if self.engine.state else 0,
            'portfolio_pnl': self.engine.state.total_pnl if self.engine.state else 0,
            'recent_alerts': [asdict(a) for a in self.engine.alerts[-10:]],
            'last_check': self.engine.last_check
        }


# ============================================================================
# STANDALONE QUERY FUNCTION (For use by SØWL)
# ============================================================================

async def perceive_portfolio_state(config: MonitoringConfig) -> PortfolioState:
    """
    On-demand perception query - SØWL can call this to get current state

    This is the "ask LYRA" function that SØWL uses when it needs to know
    "What's my portfolio right now?"
    """
    engine = PortfolioPerceptionEngine(config)
    state = await engine.perceive()
    return state


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

async def main():
    """Main entry point"""

    # Configuration from environment
    import os
    from dotenv import load_dotenv
    load_dotenv('/Users/aaronnosbisch/REPOS/seed/.env')
    wallet_address = os.getenv('POLYGON_ADDRESS', '0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669')

    config = MonitoringConfig(
        wallet_address=wallet_address,
        reconciliation_interval=300,  # 5 minutes
        deep_audit_interval=900,      # 15 minutes
    )

    # Create and run daemon
    daemon = PortfolioPerceptionDaemon(config)

    try:
        await daemon.run()
    except KeyboardInterrupt:
        daemon.stop()


if __name__ == "__main__":
    asyncio.run(main())
