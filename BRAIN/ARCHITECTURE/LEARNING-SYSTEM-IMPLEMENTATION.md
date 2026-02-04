# LEARNING SYSTEM IMPLEMENTATION SPEC
**Build the Compound Learning Architecture**

**Phase:** Implementation Architecture
**Author:** SAGE (with NOVA for expansion guidance)
**Target:** 4-week production deployment

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────┐
│                      LEARNING SYSTEM LAYERS                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Layer 5: Dashboard & Monitoring                                    │
│           ↑                                                         │
│  Layer 4: System Learning (Conductor)                              │
│           ↑                                                         │
│  Layer 3: Cross-Learning Hub                                       │
│           ↑                                                         │
│  Layer 2: Self-Learning Engines                                    │
│           ↑                                                         │
│  Layer 1: Metrics Collection & Storage                             │
│           ↑                                                         │
│     ┌─────────────────┐                                            │
│     │ Field Daemon    │                                            │
│     │ (Trade Exec)    │                                            │
│     └─────────────────┘                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## LAYER 1: METRICS COLLECTION & STORAGE

### Data Model: Trade Record

```python
# /BRAIN/ARCHITECTURE/learning_system/models/trade_record.py

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Dict, List, Optional

@dataclass
class MarketConditions:
    volatility: float  # -1.0 to 1.0 (std dev of returns)
    volume: int       # Total market volume
    bid_ask_spread: float  # Percentage
    time_to_resolution: str  # ISO duration
    momentum: float   # -1.0 to 1.0 (price trend strength)

@dataclass
class SignalMetrics:
    signal_strength: float  # 0.0-1.0 (strategy's confidence)
    signal_type: str  # whale_tracking, arbitrage, spike, etc
    market_conditions: MarketConditions
    position_size: float  # Dollar amount
    entry_price: float
    exit_price: Optional[float] = None

@dataclass
class OutcomeMetrics:
    resolved: bool
    pnl: float
    pnl_pct: float
    was_profitable: bool
    time_to_resolution_actual: str
    execution_slippage: float  # Entry vs exit price quality

@dataclass
class QualityMetrics:
    signal_quality: float  # How well signal predicted outcome
    market_timing_quality: float  # Entry/exit timing quality
    position_sizing_quality: float  # Was size appropriate?
    overall_execution_quality: float  # Weighted average

@dataclass
class ComparisonMetrics:
    vs_baseline_entry: float  # Better/worse than market entry
    vs_buy_hold: float  # vs simple hold strategy
    vs_other_strategies: Dict[str, float]  # vs peers

@dataclass
class TradeRecord:
    strategy_id: str
    cycle_num: int
    timestamp: datetime
    trade_id: str

    signal: SignalMetrics
    outcome: OutcomeMetrics
    quality: QualityMetrics
    comparison: ComparisonMetrics

    def to_dict(self):
        """Flatten for storage"""
        return asdict(self)
```

### Storage: SQLite + JSON for Fast Access

```python
# /BRAIN/ARCHITECTURE/learning_system/storage/trade_store.py

import sqlite3
import json
from pathlib import Path
from datetime import datetime, timedelta

class TradeStore:
    def __init__(self, db_path: str = "/BRAIN/TRADING/learning_db.sqlite"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Create tables if not exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Main trades table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                strategy_id TEXT,
                cycle_num INTEGER,
                timestamp DATETIME,
                signal_strength REAL,
                pnl REAL,
                was_profitable BOOLEAN,
                execution_quality REAL,
                data_json TEXT
            )
        """)

        # Strategy aggregates (for fast queries)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_aggregates (
                strategy_id TEXT PRIMARY KEY,
                updated_at DATETIME,
                win_rate REAL,
                avg_pnl REAL,
                edge REAL,
                signal_threshold REAL,
                trades_count INTEGER,
                data_json TEXT
            )
        """)

        # Insights (transferable learning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS insights (
                insight_id TEXT PRIMARY KEY,
                source_strategy TEXT,
                target_strategies TEXT,
                insight_type TEXT,
                confidence REAL,
                data_json TEXT,
                created_at DATETIME
            )
        """)

        conn.commit()
        conn.close()

    def record_trade(self, trade_record: TradeRecord):
        """Store a completed trade"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO trades
            (trade_id, strategy_id, cycle_num, timestamp,
             signal_strength, pnl, was_profitable, execution_quality, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            trade_record.trade_id,
            trade_record.strategy_id,
            trade_record.cycle_num,
            trade_record.timestamp.isoformat(),
            trade_record.signal.signal_strength,
            trade_record.outcome.pnl,
            trade_record.outcome.was_profitable,
            trade_record.quality.overall_execution_quality,
            json.dumps(trade_record.to_dict(), default=str)
        ))

        conn.commit()
        conn.close()

    def get_recent_trades(self, strategy_id: str, n: int = 30):
        """Get last n trades for strategy"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT data_json FROM trades
            WHERE strategy_id = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (strategy_id, n))

        trades = [json.loads(row[0]) for row in cursor.fetchall()]
        conn.close()
        return trades

    def update_strategy_aggregate(self, strategy_id: str, agg_data: dict):
        """Update cached aggregate for fast queries"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR REPLACE INTO strategy_aggregates
            (strategy_id, updated_at, win_rate, avg_pnl, edge,
             signal_threshold, trades_count, data_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            strategy_id,
            datetime.now().isoformat(),
            agg_data['win_rate'],
            agg_data['avg_pnl'],
            agg_data['edge'],
            agg_data['signal_threshold'],
            agg_data['trades_count'],
            json.dumps(agg_data)
        ))

        conn.commit()
        conn.close()
```

---

## LAYER 2: SELF-LEARNING ENGINES

### Strategy Learner Class

```python
# /BRAIN/ARCHITECTURE/learning_system/self_learning/strategy_learner.py

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import statistics

@dataclass
class SignalQualityAnalysis:
    cohort: str  # 'high', 'medium', 'low'
    threshold_range: Tuple[float, float]
    win_rate: float
    avg_pnl: float
    sample_count: int
    trend: str  # 'improving', 'stable', 'degrading'

class StrategyLearner:
    """Self-learning engine for a single strategy"""

    def __init__(self, strategy_id: str, trade_store: TradeStore):
        self.strategy_id = strategy_id
        self.trade_store = trade_store

        # Parameters that adapt
        self.parameters = {
            'signal_threshold': 0.65,
            'position_size_max': 100,
            'min_edge_confidence': 0.50,
        }

        # Learning state
        self.parameter_history = []
        self.insights = {}

    def learn_from_trade(self, trade_record: TradeRecord):
        """Called whenever trade resolves"""

        # Store the trade
        self.trade_store.record_trade(trade_record)

        # Extract what we learned
        self.analyze_signal_quality()
        self.update_thresholds()
        self.assess_learning_velocity()

    def analyze_signal_quality(self) -> Dict[str, SignalQualityAnalysis]:
        """Break down: what signal strengths predict success?"""

        trades = self.trade_store.get_recent_trades(self.strategy_id, n=30)
        if not trades:
            return {}

        # Cohort trades by signal strength
        high_signal = [t for t in trades if t['signal']['signal_strength'] > 0.75]
        med_signal = [t for t in trades if 0.65 <= t['signal']['signal_strength'] <= 0.75]
        low_signal = [t for t in trades if t['signal']['signal_strength'] < 0.65]

        def analyze_cohort(trades, label, range_tuple):
            if not trades:
                return None

            profitable_count = sum(1 for t in trades if t['outcome']['was_profitable'])
            win_rate = profitable_count / len(trades)
            avg_pnl = statistics.mean([t['outcome']['pnl'] for t in trades])

            # Detect trend (last 5 vs previous 5)
            if len(trades) >= 10:
                prev_wr = sum(1 for t in trades[-10:-5] if t['outcome']['was_profitable']) / 5
                curr_wr = sum(1 for t in trades[-5:] if t['outcome']['was_profitable']) / 5
                trend = 'improving' if curr_wr > prev_wr else ('degrading' if curr_wr < prev_wr else 'stable')
            else:
                trend = 'insufficient_data'

            return SignalQualityAnalysis(
                cohort=label,
                threshold_range=range_tuple,
                win_rate=win_rate,
                avg_pnl=avg_pnl,
                sample_count=len(trades),
                trend=trend
            )

        analysis = {}
        if high_signal:
            analysis['high'] = analyze_cohort(high_signal, 'high', (0.75, 1.0))
        if med_signal:
            analysis['medium'] = analyze_cohort(med_signal, 'medium', (0.65, 0.75))
        if low_signal:
            analysis['low'] = analyze_cohort(low_signal, 'low', (0.0, 0.65))

        self.insights['signal_quality_analysis'] = analysis
        return analysis

    def update_thresholds(self):
        """Update decision thresholds based on learning"""

        analysis = self.insights.get('signal_quality_analysis', {})
        if not analysis:
            return

        # Strategy: raise threshold if signal quality is reliable
        if 'high' in analysis and 'low' in analysis:
            high_wr = analysis['high'].win_rate
            low_wr = analysis['low'].win_rate

            if high_wr > low_wr + 0.10:  # Clear difference
                # Signal quality is predictive - raise threshold
                new_threshold = min(
                    analysis['high'].threshold_range[0] + 0.02,
                    0.85  # Don't go higher than 0.85
                )
                old_threshold = self.parameters['signal_threshold']
                self.parameters['signal_threshold'] = new_threshold

                self.parameter_history.append({
                    'timestamp': datetime.now().isoformat(),
                    'param': 'signal_threshold',
                    'old_value': old_threshold,
                    'new_value': new_threshold,
                    'reason': f'signal_quality_predictive (high:{high_wr:.1%} vs low:{low_wr:.1%})'
                })

    def assess_learning_velocity(self) -> float:
        """How fast is this strategy improving?"""

        trades = self.trade_store.get_recent_trades(self.strategy_id, n=60)
        if len(trades) < 30:
            return 0.0

        # Compare first 30 vs last 30
        first_30 = trades[-30:]
        last_30 = trades[:30]

        first_wr = sum(1 for t in first_30 if t['outcome']['was_profitable']) / 30
        last_wr = sum(1 for t in last_30 if t['outcome']['was_profitable']) / 30

        # Learning velocity = improvement per trade
        improvement = (last_wr - first_wr) / 30
        return improvement

    def get_current_edge(self) -> float:
        """Calculate expected value per trade"""

        trades = self.trade_store.get_recent_trades(self.strategy_id, n=30)
        if not trades:
            return 0.0

        profitable = [t for t in trades if t['outcome']['was_profitable']]
        unprofitable = [t for t in trades if not t['outcome']['was_profitable']]

        if not profitable or not unprofitable:
            return 0.0

        win_rate = len(profitable) / len(trades)
        avg_win = statistics.mean([t['outcome']['pnl'] for t in profitable])
        avg_loss = statistics.mean([abs(t['outcome']['pnl']) for t in unprofitable])

        edge = (win_rate * avg_win) - ((1 - win_rate) * avg_loss)
        return edge

    def get_state(self) -> Dict:
        """Return current state for monitoring"""
        trades = self.trade_store.get_recent_trades(self.strategy_id, n=30)
        return {
            'strategy_id': self.strategy_id,
            'win_rate': sum(1 for t in trades if t['outcome']['was_profitable']) / len(trades) if trades else 0,
            'edge': self.get_current_edge(),
            'signal_threshold': self.parameters['signal_threshold'],
            'learning_velocity': self.assess_learning_velocity(),
            'insights': self.insights,
            'parameters': self.parameters,
            'recent_updates': self.parameter_history[-5:] if self.parameter_history else []
        }
```

---

## LAYER 3: CROSS-LEARNING HUB

### Insight Extraction & Distribution

```python
# /BRAIN/ARCHITECTURE/learning_system/cross_learning/insight_hub.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class InsightType(Enum):
    MARKET_STRUCTURE = "market_structure"
    TIMING_PATTERN = "timing_pattern"
    RISK_FACTOR = "risk_factor"
    POSITION_SIZING = "position_sizing"
    SIGNAL_QUALITY = "signal_quality"

@dataclass
class Insight:
    insight_type: InsightType
    source_strategy: str
    pattern: str
    confidence: float  # 0.0-1.0
    applicable_strategies: List[str]
    details: Dict
    timestamp: datetime

class InsightHub:
    """Manages insight extraction and distribution"""

    def __init__(self, trade_store: TradeStore):
        self.trade_store = trade_store
        self.insights = []
        self.strategy_learners = {}

    def register_strategy(self, strategy_id: str, learner: StrategyLearner):
        """Register a strategy for cross-learning"""
        self.strategy_learners[strategy_id] = learner

    def extract_insights(self, source_strategy_id: str) -> List[Insight]:
        """Extract transferable insights from a strategy"""

        learner = self.strategy_learners[source_strategy_id]
        state = learner.get_state()

        insights = []

        # Insight 1: Market structure insights from signal analysis
        signal_analysis = state['insights'].get('signal_quality_analysis', {})
        if signal_analysis:
            # If high-confidence signals have different spreads/volatility patterns
            high_trades = self.trade_store.get_recent_trades(source_strategy_id, n=30)
            high_trades = [t for t in high_trades if t['signal']['signal_strength'] > 0.75]

            if high_trades:
                avg_spread = statistics.mean([t['signal']['market_conditions']['bid_ask_spread'] for t in high_trades])

                insights.append(Insight(
                    insight_type=InsightType.MARKET_STRUCTURE,
                    source_strategy=source_strategy_id,
                    pattern=f"high_confidence_trades_have_spread_{avg_spread:.2%}",
                    confidence=signal_analysis.get('high', {}).win_rate if 'high' in signal_analysis else 0.5,
                    applicable_strategies=[s for s in self.strategy_learners.keys() if s != source_strategy_id],
                    details={
                        'avg_spread': avg_spread,
                        'avoid_spread_above': avg_spread * 1.5,
                        'trades_analyzed': len(high_trades)
                    },
                    timestamp=datetime.now()
                ))

        return insights

    def broadcast_insights(self, insights: List[Insight]):
        """Send insights to applicable strategies"""

        for insight in insights:
            for target_strategy_id in insight.applicable_strategies:
                learner = self.strategy_learners.get(target_strategy_id)
                if learner:
                    learner.apply_external_insight(insight)

        self.insights.extend(insights)
```

### Strategy Application of External Insights

```python
# Add to StrategyLearner class

def apply_external_insight(self, insight: Insight):
    """Apply learning from another strategy"""

    if insight.insight_type == InsightType.MARKET_STRUCTURE:
        # Example: avoid trades with spreads > X
        if 'avoid_spread_above' in insight.details:
            self.parameter_history.append({
                'timestamp': datetime.now().isoformat(),
                'param': 'avoid_spread_above',
                'value': insight.details['avoid_spread_above'],
                'source': insight.source_strategy,
                'confidence': insight.confidence
            })

    # Store for next decision
    self.insights[f'external_{insight.source_strategy}'] = insight.details
```

---

## LAYER 4: SYSTEM LEARNING (CONDUCTOR)

### Portfolio Optimization

```python
# /BRAIN/ARCHITECTURE/learning_system/system_learning/conductor.py

import numpy as np
from typing import Dict, List

class CentralConductor:
    """Portfolio-level learning and optimization"""

    def __init__(self, trade_store: TradeStore, insight_hub: InsightHub):
        self.trade_store = trade_store
        self.insight_hub = insight_hub
        self.allocation = {}
        self.allocation_history = []

    def calculate_correlation_matrix(self, strategy_ids: List[str]) -> np.ndarray:
        """Calculate strategy correlations"""

        # Get recent trades for each strategy
        strategies_trades = {}
        for sid in strategy_ids:
            trades = self.trade_store.get_recent_trades(sid, n=30)
            strategies_trades[sid] = [t['outcome']['pnl'] for t in trades]

        # Calculate correlation matrix
        n = len(strategy_ids)
        corr_matrix = np.zeros((n, n))

        for i, sid1 in enumerate(strategy_ids):
            for j, sid2 in enumerate(strategy_ids):
                if i == j:
                    corr_matrix[i][j] = 1.0
                else:
                    pnl1 = strategies_trades[sid1]
                    pnl2 = strategies_trades[sid2]

                    if len(pnl1) > 1 and len(pnl2) > 1:
                        corr = np.corrcoef(pnl1, pnl2)[0, 1]
                        corr_matrix[i][j] = corr if not np.isnan(corr) else 0.0

        return corr_matrix

    def identify_redundant_strategies(self, strategy_ids: List[str]) -> List[Tuple[str, str, float]]:
        """Find highly correlated (redundant) strategy pairs"""

        corr_matrix = self.calculate_correlation_matrix(strategy_ids)

        redundant = []
        for i, sid1 in enumerate(strategy_ids):
            for j, sid2 in enumerate(strategy_ids):
                if i < j and corr_matrix[i][j] > 0.65:
                    redundant.append((sid1, sid2, corr_matrix[i][j]))

        return redundant

    def optimize_allocation(self,
                           strategy_ids: List[str],
                           total_capital: float,
                           learners: Dict[str, StrategyLearner]) -> Dict[str, float]:
        """
        Allocate capital to maximize portfolio edge while minimizing correlation

        Formula:
        allocation = capital * (
            (edge / max_edge) * 0.6 +
            ((1 - avg_correlation) / 2) * 0.4
        )
        """

        allocation = {}
        edges = {sid: learners[sid].get_current_edge() for sid in strategy_ids}
        max_edge = max(edges.values()) if edges else 1.0

        corr_matrix = self.calculate_correlation_matrix(strategy_ids)

        for i, strategy_id in enumerate(strategy_ids):
            # Edge component (higher edge = more capital)
            edge_score = edges[strategy_id] / max_edge if max_edge > 0 else 0.5

            # Diversification component (lower correlation = more capital)
            avg_corr = np.mean([corr_matrix[i][j] for j in range(len(strategy_ids)) if j != i])
            diversity_score = (1 - avg_corr) / 2

            # Weighted allocation
            score = (edge_score * 0.6) + (diversity_score * 0.4)
            allocation[strategy_id] = total_capital * score

        # Normalize to total capital
        total_allocated = sum(allocation.values())
        if total_allocated > 0:
            allocation = {k: v * (total_capital / total_allocated) for k, v in allocation.items()}

        return allocation

    def rebalance_portfolio(self, strategy_ids: List[str],
                          total_capital: float,
                          learners: Dict[str, StrategyLearner]):
        """Periodically rebalance based on learning"""

        new_allocation = self.optimize_allocation(strategy_ids, total_capital, learners)

        self.allocation_history.append({
            'timestamp': datetime.now().isoformat(),
            'allocation': new_allocation,
            'reasoning': {
                'redundancy': self.identify_redundant_strategies(strategy_ids),
                'edges': {sid: learners[sid].get_current_edge() for sid in strategy_ids}
            }
        })

        self.allocation = new_allocation
        return new_allocation

    def get_state(self) -> Dict:
        """Return current conductor state"""
        return {
            'current_allocation': self.allocation,
            'recent_rebalances': self.allocation_history[-5:],
            'timestamp': datetime.now().isoformat()
        }
```

---

## LAYER 5: MONITORING & DASHBOARD

### Metrics Server

```python
# /BRAIN/ARCHITECTURE/learning_system/monitoring/metrics_server.py

from fastapi import FastAPI
from datetime import datetime

app = FastAPI()

class MetricsAggregator:
    def __init__(self, trade_store, learners, conductor, insight_hub):
        self.trade_store = trade_store
        self.learners = learners
        self.conductor = conductor
        self.insight_hub = insight_hub

    def get_all_metrics(self) -> Dict:
        """Compile complete metrics snapshot"""

        strategies_metrics = {}
        for sid, learner in self.learners.items():
            strategies_metrics[sid] = learner.get_state()

        return {
            'timestamp': datetime.now().isoformat(),
            'per_strategy': strategies_metrics,
            'portfolio': {
                'allocation': self.conductor.allocation,
                'correlation_analysis': self._analyze_correlations()
            },
            'learning': {
                'total_learning_velocity': self._calculate_total_learning_velocity(),
                'active_insights': len(self.insight_hub.insights)
            }
        }

    def _analyze_correlations(self) -> Dict:
        strategy_ids = list(self.learners.keys())
        return {
            'matrix': self.conductor.calculate_correlation_matrix(strategy_ids),
            'redundant_pairs': self.conductor.identify_redundant_strategies(strategy_ids)
        }

    def _calculate_total_learning_velocity(self) -> float:
        velocities = []
        for learner in self.learners.values():
            velocities.append(learner.assess_learning_velocity())
        return sum(velocities) / len(velocities) if velocities else 0

# API Endpoints
@app.get("/metrics")
def get_metrics():
    return aggregator.get_all_metrics()

@app.get("/strategy/{strategy_id}")
def get_strategy_metrics(strategy_id: str):
    return aggregator.learners[strategy_id].get_state()
```

---

## INTEGRATION WITH FIELD TRADING DAEMON

### Updated field_trading_daemon.py

```python
# /tools/field_trading_daemon.py (additions)

from BRAIN.ARCHITECTURE.learning_system.models.trade_record import TradeRecord
from BRAIN.ARCHITECTURE.learning_system.storage.trade_store import TradeStore
from BRAIN.ARCHITECTURE.learning_system.self_learning.strategy_learner import StrategyLearner
from BRAIN.ARCHITECTURE.learning_system.cross_learning.insight_hub import InsightHub
from BRAIN.ARCHITECTURE.learning_system.system_learning.conductor import CentralConductor

class FieldTradingDaemonWithLearning:
    def __init__(self):
        # Existing components
        self.trading_loop = ...
        self.nats_connection = ...

        # New learning components
        self.trade_store = TradeStore()
        self.insight_hub = InsightHub(self.trade_store)
        self.conductor = CentralConductor(self.trade_store, self.insight_hub)

        # Register strategies
        for strategy_id in ['whale_tracking', 'cross_platform_arb', 'spike_detection']:
            learner = StrategyLearner(strategy_id, self.trade_store)
            self.insight_hub.register_strategy(strategy_id, learner)

    def execute_trading_cycle(self):
        """Main trading loop with learning integrated"""

        # Existing: market scan, decision, execution
        markets = self.scan_markets()
        decision = self.make_decision(markets)
        trade_result = self.execute_trade(decision)

        # NEW: Record learning data
        trade_record = self.build_trade_record(decision, trade_result)

        # Trigger self-learning
        for strategy_id in trade_result.strategies_used:
            learner = self.insight_hub.strategy_learners[strategy_id]
            learner.learn_from_trade(trade_record)

        # Trigger cross-learning (every 10 trades)
        if trade_result.total_trades % 10 == 0:
            for strategy_id in self.insight_hub.strategy_learners.keys():
                insights = self.insight_hub.extract_insights(strategy_id)
                self.insight_hub.broadcast_insights(insights)

        # Trigger system learning (every 100 trades)
        if trade_result.total_trades % 100 == 0:
            new_allocation = self.conductor.rebalance_portfolio(
                list(self.insight_hub.strategy_learners.keys()),
                self.available_capital,
                self.insight_hub.strategy_learners
            )
            self.update_capital_allocation(new_allocation)

        # Publish to NATS
        self.publish_learning_metrics()

    def build_trade_record(self, decision, result) -> TradeRecord:
        """Convert trade execution to learning record"""
        # Implementation: map trade result to TradeRecord format
        pass

    def publish_learning_metrics(self):
        """Publish learning state to NATS"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'per_strategy': {
                sid: learner.get_state()
                for sid, learner in self.insight_hub.strategy_learners.items()
            },
            'portfolio_allocation': self.conductor.allocation,
            'conductor_state': self.conductor.get_state()
        }

        self.nats_connection.publish(
            'owl.learning.metrics',
            json.dumps(metrics)
        )
```

---

## DEPLOYMENT CHECKLIST

### Week 1: Self-Learning
- [ ] Create models and storage layer
- [ ] Implement TradeRecord and TradeStore
- [ ] Build StrategyLearner class
- [ ] Test with 50 trades
- [ ] Integrate into field daemon

### Week 2: Cross-Learning
- [ ] Build insight extraction engine
- [ ] Create InsightHub class
- [ ] Test insight broadcasting
- [ ] Test strategy application of insights
- [ ] Run 100 trades with cross-learning

### Week 3: System Learning
- [ ] Build correlation analysis
- [ ] Implement CentralConductor
- [ ] Create allocation optimization
- [ ] Test portfolio rebalancing
- [ ] Run 200 trades with full system

### Week 4: Monitoring & Production
- [ ] Build metrics aggregator
- [ ] Create FastAPI dashboard
- [ ] Add NATS publishing
- [ ] Run full production validation
- [ ] Document operations

---

## SUCCESS CRITERIA

1. **Edge improvement:** 0.025 → 0.041 in 30 days
2. **Learning velocity:** 0.025 (2.5% daily improvement)
3. **Portfolio Sharpe:** 0.94 → 1.42 in 30 days
4. **Insight adoption:** >50% of improvements from cross-learning
5. **System stability:** No crashes, all safety guardrails active

**SAGE validates the learning. NOVA expands to new opportunities. SØWL improves the improvement system itself.**
