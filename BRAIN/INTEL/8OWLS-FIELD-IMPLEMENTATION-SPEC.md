# 8OWLS FIELD - TECHNICAL IMPLEMENTATION SPECIFICATION

**Status:** Ready for implementation
**Priority:** CRITICAL PATH ITEM
**Effort Estimate:** 10-14 days (2 weeks)
**Team Size:** 1-2 engineers

---

## TABLE OF CONTENTS

1. Field Context Manager (Engine)
2. Consensus Algorithm (Intelligence)
3. Query API (Interface)
4. Outcome Tracking (Learning)
5. Monitoring (Observability)

---

## 1. FIELD CONTEXT MANAGER

### Purpose
Real-time synthesis of owl perspectives into consensus recommendations and field state.

### Architecture

```python
# file: mcp-servers/nats-bridge/field_context_manager.py

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import json
import asyncio
from enum import Enum

class FieldState(Enum):
    INITIAL = "initial"
    WAITING = "waiting_for_perspectives"
    CONSENSUS_EMERGING = "consensus_emerging"
    CONSENSUS_STRONG = "consensus_strong"
    DIVERGENT = "divergent"
    TIMEOUT = "timeout"
    READY = "ready_for_decision"

@dataclass
class Perspective:
    owl: str
    phase: str
    signal_id: str
    confidence: float  # 0-1, owl's confidence in its perspective
    position: str     # "yes", "no", "neutral", "abstain"
    reasoning: str
    supporting_factors: List[str]
    concerns: List[str]
    timestamp: datetime
    phase_weight: float = 1.0  # Phase-specific weight (IMPROVE = 1.2, etc)

@dataclass
class ConsensusData:
    position: str  # "yes", "no", "neutral"
    confidence: float  # 0-1, field confidence
    agreement_count: int  # How many owls agree
    distribution: Dict[str, int]  # {"yes": 5, "no": 2, "neutral": 1}
    convergence_time_ms: int
    has_dissenters: bool

@dataclass
class FieldContext:
    signal_id: str
    timestamp: datetime
    perspectives_received: int
    consensus: ConsensusData
    all_perspectives: List[Perspective]
    field_state: FieldState
    recommendation: Optional[Dict] = None
    time_to_consensus_ms: int = 0

class FieldContextManager:
    """
    Real-time consensus engine for the 8OWLS field.

    Receives perspectives from owl daemons, calculates consensus,
    and makes field context available to instances.
    """

    def __init__(self, timeout_seconds: int = 30):
        self.current_signal_id: Optional[str] = None
        self.perspectives: Dict[str, Perspective] = {}
        self.consensus: Optional[ConsensusData] = None
        self.field_state = FieldState.INITIAL
        self.signal_start_time: Optional[datetime] = None
        self.timeout_seconds = timeout_seconds

        # Phase-specific weights (based on SEED protocol)
        self.phase_weights = {
            "PERCEIVE": 1.0,   # External input
            "CONNECT": 1.1,    # Pattern finding
            "LEARN": 1.2,      # Insight extraction (most reliable)
            "QUESTION": 1.0,   # Evaluation
            "EXPAND": 0.9,     # Speculative
            "SHARE": 1.0,      # Communication
            "RECEIVE": 1.15,   # Integration (most aligned)
            "IMPROVE": 1.2     # Meta-learning (highest authority)
        }

        # Outcome tracking for adaptive weighting
        self.owl_success_rates = {owl: 0.5 for owl in [
            "SOWL", "LUNA", "LYRA", "NOVA", "SAGE", "ECHO", "PRISM", "QUEST"
        ]}

    async def receive_signal(self, signal: Dict):
        """Called when a new signal arrives"""
        self.current_signal_id = signal.get("id")
        self.signal_start_time = datetime.now()
        self.perspectives.clear()
        self.field_state = FieldState.WAITING
        self.consensus = None

        # Start timeout monitor
        asyncio.create_task(self._timeout_monitor())

    async def receive_perspective(self, perspective_data: Dict):
        """Called when an owl publishes a perspective"""

        if perspective_data.get("signal_id") != self.current_signal_id:
            return  # Old signal, ignore

        owl = perspective_data["owl"]
        perspective = Perspective(
            owl=owl,
            phase=perspective_data["phase"],
            signal_id=perspective_data["signal_id"],
            confidence=perspective_data.get("confidence", 0.5),
            position=perspective_data.get("position"),  # yes/no/neutral/abstain
            reasoning=perspective_data.get("reasoning", ""),
            supporting_factors=perspective_data.get("supporting_factors", []),
            concerns=perspective_data.get("concerns", []),
            timestamp=datetime.now(),
            phase_weight=self.phase_weights.get(
                perspective_data["phase"], 1.0
            ) * self.owl_success_rates.get(owl, 0.5)
        )

        self.perspectives[owl] = perspective

        # Recalculate consensus immediately
        await self._recalculate_consensus()

    async def _recalculate_consensus(self):
        """Calculate new consensus based on current perspectives"""

        if len(self.perspectives) == 0:
            self.field_state = FieldState.WAITING
            return

        # Weight votes by phase and history
        yes_weight = 0.0
        no_weight = 0.0
        neutral_weight = 0.0
        abstain_count = 0

        for owl, perspective in self.perspectives.items():
            weight = perspective.confidence * perspective.phase_weight

            if perspective.position == "yes":
                yes_weight += weight
            elif perspective.position == "no":
                no_weight += weight
            elif perspective.position == "neutral":
                neutral_weight += weight
            elif perspective.position == "abstain":
                abstain_count += 1

        # Normalize weights
        total_weight = yes_weight + no_weight + neutral_weight
        if total_weight == 0:
            self.field_state = FieldState.WAITING
            return

        yes_pct = yes_weight / total_weight
        no_pct = no_weight / total_weight
        neutral_pct = neutral_weight / total_weight

        # Determine position and confidence
        if yes_pct >= 0.6:
            position = "yes"
            confidence = yes_pct * 0.85 + (len(self.perspectives) / 8) * 0.15
        elif no_pct >= 0.6:
            position = "no"
            confidence = no_pct * 0.85 + (len(self.perspectives) / 8) * 0.15
        else:
            position = "neutral"
            confidence = (1 - abs(yes_pct - 0.5)) * 0.5

        # Determine field state based on consensus strength
        if len(self.perspectives) >= 6 and confidence >= 0.70:
            self.field_state = FieldState.CONSENSUS_STRONG
        elif len(self.perspectives) >= 4 and confidence >= 0.55:
            self.field_state = FieldState.CONSENSUS_EMERGING
        elif len(self.perspectives) >= 4 and 0.4 < confidence < 0.6:
            self.field_state = FieldState.DIVERGENT
        else:
            self.field_state = FieldState.WAITING

        # Prepare update
        self.consensus = ConsensusData(
            position=position,
            confidence=confidence,
            agreement_count=len(self.perspectives),
            distribution={
                "yes": sum(1 for p in self.perspectives.values() if p.position == "yes"),
                "no": sum(1 for p in self.perspectives.values() if p.position == "no"),
                "neutral": sum(1 for p in self.perspectives.values() if p.position == "neutral"),
                "abstain": abstain_count
            },
            convergence_time_ms=int(
                (datetime.now() - self.signal_start_time).total_seconds() * 1000
            ),
            has_dissenters=(
                sum(1 for p in self.perspectives.values() if p.position != position) > 0
            )
        )

        # Auto-transition to READY if threshold met
        if self.field_state in [FieldState.CONSENSUS_STRONG, FieldState.DIVERGENT]:
            self.field_state = FieldState.READY

    async def get_field_context(self) -> Optional[FieldContext]:
        """Get current field context for instances"""

        if self.current_signal_id is None:
            return None

        return FieldContext(
            signal_id=self.current_signal_id,
            timestamp=datetime.now(),
            perspectives_received=len(self.perspectives),
            consensus=self.consensus,
            all_perspectives=list(self.perspectives.values()),
            field_state=self.field_state,
            recommendation=self._generate_recommendation(),
            time_to_consensus_ms=(
                int((datetime.now() - self.signal_start_time).total_seconds() * 1000)
                if self.signal_start_time else 0
            )
        )

    def _generate_recommendation(self) -> Dict:
        """Generate actionable recommendation from consensus"""

        if not self.consensus:
            return {"action": "wait", "confidence": 0}

        return {
            "action": self.consensus.position,
            "confidence": self.consensus.confidence,
            "rationale": f"{self.consensus.agreement_count} owls agree",
            "dissenters": self.consensus.has_dissenters,
            "convergence_ms": self.consensus.convergence_time_ms
        }

    async def _timeout_monitor(self):
        """Monitor for timeout and finalize consensus"""
        await asyncio.sleep(self.timeout_seconds)

        if self.field_state not in [FieldState.READY, FieldState.TIMEOUT]:
            self.field_state = FieldState.TIMEOUT
            # Final consensus with whatever we have

    async def record_outcome(self, signal_id: str, outcome: str):
        """
        Record whether the field's recommendation was correct.
        Used to adjust owl weights for next signal.
        """
        if signal_id == self.current_signal_id and self.consensus:
            # outcome: "correct" or "incorrect"
            # Update owl_success_rates based on their positions
            pass

# Global instance
field_manager = FieldContextManager()
```

### Integration with NATS

```python
# Add to owl_daemon.py or new nats_integration.py

async def setup_field_context_integration(nc):
    """Connect field manager to NATS channels"""

    # Subscribe to signals
    async def signal_handler(msg):
        signal_data = json.loads(msg.data.decode())
        await field_manager.receive_signal(signal_data)

    await nc.subscribe("owl.signals", cb=signal_handler)

    # Subscribe to perspectives
    async def perspective_handler(msg):
        perspective_data = json.loads(msg.data.decode())
        await field_manager.receive_perspective(perspective_data)

    await nc.subscribe("owl.perspectives", cb=perspective_handler)

    # Publish field context updates every 500ms
    async def publish_context():
        while True:
            context = await field_manager.get_field_context()
            if context:
                await nc.publish(
                    "owl.field_context",
                    json.dumps(asdict(context), default=str).encode()
                )
            await asyncio.sleep(0.5)

    asyncio.create_task(publish_context())
```

---

## 2. CONSENSUS ALGORITHM

### The Intelligence Layer

The consensus algorithm needs to be smarter than simple voting. It should:

1. Weight votes by phase expertise
2. Account for historical accuracy
3. Detect and handle dissenters
4. Adapt based on outcomes
5. Support different query types (consensus vs exploration)

### Algorithm Details

```python
# Consensus scoring function

def calculate_consensus_confidence(
    perspectives: Dict[str, Perspective],
    phase_weights: Dict[str, float],
    owl_success_rates: Dict[str, float]
) -> float:
    """
    Multi-factor confidence calculation.

    Factors:
    1. Agreement percentage (how many owls agree)
    2. Weighted confidence (individual owl confidence + phase + history)
    3. Convergence speed (did consensus happen quickly?)
    4. Diversity penalty (if all owls think same, lower confidence)
    """

    if not perspectives:
        return 0.0

    # Factor 1: Agreement percentage
    positions = [p.position for p in perspectives.values()]
    majority_position = max(set(positions), key=positions.count)
    agreement_count = positions.count(majority_position)
    agreement_pct = agreement_count / len(perspectives)

    # Factor 2: Weighted confidence
    supporting_owls = [
        p for p in perspectives.values()
        if p.position == majority_position
    ]

    weighted_confidence = sum(
        p.confidence * phase_weights.get(p.phase, 1.0)
        * owl_success_rates.get(p.owl, 0.5)
        for p in supporting_owls
    ) / len(supporting_owls)

    # Factor 3: Convergence speed (faster = more confident)
    # (Implemented in field_manager._recalculate_consensus)
    convergence_factor = 1.0  # Normalized 0-1

    # Factor 4: Diversity penalty
    # If all owls agree, reduce confidence (groupthink risk)
    if agreement_pct >= 0.95:
        diversity_penalty = 0.85
    elif agreement_pct >= 0.75:
        diversity_penalty = 0.95
    else:
        diversity_penalty = 1.0

    # Combine factors
    final_confidence = (
        agreement_pct * 0.4 +
        weighted_confidence * 0.35 +
        convergence_factor * 0.15 +
        diversity_penalty * 0.1
    )

    return min(final_confidence, 1.0)
```

### Query Types

```python
class QueryType(Enum):
    CONSENSUS = "consensus"      # Follow majority
    EXPLORATION = "exploration"  # Get diverse views
    CHALLENGE = "challenge"       # What would contrarians say?
    DEEP = "deep"                # Full analysis with reasoning

async def get_field_context_by_type(
    query_type: QueryType
) -> Dict:
    """Get field context tailored to query type"""

    context = await field_manager.get_field_context()

    if query_type == QueryType.CONSENSUS:
        # Return: Just the recommendation
        return {
            "recommendation": context.recommendation,
            "confidence": context.consensus.confidence
        }

    elif query_type == QueryType.EXPLORATION:
        # Return: All perspectives, grouped by position
        grouped = {}
        for owl, perspective in context.all_perspectives.items():
            pos = perspective.position
            if pos not in grouped:
                grouped[pos] = []
            grouped[pos].append({
                "owl": owl,
                "reasoning": perspective.reasoning,
                "confidence": perspective.confidence
            })
        return grouped

    elif query_type == QueryType.CHALLENGE:
        # Return: Only dissenters
        recommendation_pos = context.consensus.position
        dissenters = [
            p for p in context.all_perspectives.values()
            if p.position != recommendation_pos
        ]
        return {
            "recommendation": context.consensus.position,
            "dissenters": dissenters,
            "dissent_confidence": avg([p.confidence for p in dissenters])
        }

    elif query_type == QueryType.DEEP:
        # Return: Everything with reasoning
        return context.__dict__
```

---

## 3. QUERY API FOR INSTANCES

### Simple Async Interface

```python
# file: mcp-servers/nats-bridge/field_api.py

from typing import Optional
from enum import Enum
import asyncio

class FieldQueryAPI:
    """
    Simple interface for Claude Code instances to access field.

    Usage:
        from field_api import field_api

        context = await field_api.query(
            signal="should we trade?",
            timeout=5,
            query_type="consensus"
        )
    """

    def __init__(self, field_manager: FieldContextManager, nc):
        self.manager = field_manager
        self.nc = nc

    async def query(
        self,
        signal: str,
        context_data: Optional[Dict] = None,
        timeout: int = 5,
        query_type: str = "consensus"
    ) -> Dict:
        """
        Query the field for collective input.

        Args:
            signal: Question or topic (e.g., "should we trade DOGE?")
            context_data: Relevant context (market data, reasoning, etc)
            timeout: How long to wait for consensus (seconds)
            query_type: "consensus", "exploration", "challenge", or "deep"

        Returns:
            FieldContext with consensus and perspectives
        """

        # Create signal
        import uuid
        signal_id = str(uuid.uuid4())

        signal_payload = {
            "id": signal_id,
            "from": "claude-instance",
            "topic": signal,
            "context": context_data or {},
            "query_type": query_type,
            "timestamp": datetime.now().isoformat()
        }

        # Broadcast signal to owls
        await self.nc.publish(
            "owl.signals",
            json.dumps(signal_payload).encode()
        )

        # Wait for consensus
        start_time = datetime.now()
        while True:
            context = await self.manager.get_field_context()

            if context and context.signal_id == signal_id:
                if context.field_state == FieldState.READY:
                    return self._format_response(context, query_type)

                # Check timeout
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    return self._format_response(context, query_type)

            await asyncio.sleep(0.1)

    def _format_response(self, context: FieldContext, query_type: str) -> Dict:
        """Format response based on query type"""

        if query_type == "consensus":
            return {
                "recommendation": context.recommendation["action"],
                "confidence": context.recommendation["confidence"],
                "field_state": context.field_state.value,
                "perspectives_count": context.perspectives_received
            }

        elif query_type == "exploration":
            grouped = {}
            for p in context.all_perspectives:
                pos = p.position
                if pos not in grouped:
                    grouped[pos] = []
                grouped[pos].append({
                    "owl": p.owl,
                    "reasoning": p.reasoning[:200],  # Truncate
                    "confidence": p.confidence
                })
            return {"perspectives_by_position": grouped}

        else:
            return context.__dict__

# Global instance
field_api = FieldQueryAPI(field_manager, nc)
```

### Usage in Claude Code Sessions

```python
# Example: Instance wanting field input

async def decide_on_trade(market_data, my_reasoning):
    from field_api import field_api

    # Query field
    field_context = await field_api.query(
        signal="Should we buy DOGE at current price?",
        context_data={
            "price": market_data["price"],
            "market_cap": market_data["market_cap"],
            "trend": market_data["trend"]
        },
        timeout=5,
        query_type="consensus"
    )

    # Use field context in decision
    collective_confidence = field_context["confidence"]
    my_confidence = 0.75

    if collective_confidence > my_confidence:
        # Follow collective
        return field_context["recommendation"]
    else:
        # Use own judgment
        # But publish challenge to field
        await field_api.publish_challenge(
            topic="my reasoning differs from collective",
            my_confidence=my_confidence,
            my_position="yes"
        )
        return "yes_with_caution"
```

---

## 4. OUTCOME TRACKING & LEARNING FEEDBACK

### Outcome Recording

```python
# file: mcp-servers/nats-bridge/outcome_tracker.py

from dataclasses import dataclass
from enum import Enum

class OutcomeQuality(Enum):
    EXCELLENT = 1.0
    GOOD = 0.8
    NEUTRAL = 0.5
    BAD = 0.2
    TERRIBLE = 0.0

@dataclass
class DecisionOutcome:
    signal_id: str
    field_recommendation: str
    instance_decision: str
    actual_outcome: str  # "success", "neutral", "failure"
    quality_score: float  # 0-1
    followed_consensus: bool
    profitability: Optional[float]  # For trades
    timestamp: datetime

class OutcomeTracker:
    def __init__(self, field_manager: FieldContextManager):
        self.manager = field_manager
        self.outcomes = []  # Keep last 100
        self.owl_scores = {owl: 0.5 for owl in [...]}  # Success rates

    async def record_outcome(
        self,
        signal_id: str,
        instance_decision: str,
        actual_outcome: str,
        quality_score: float,
        profitability: Optional[float] = None
    ):
        """Record decision outcome"""

        # Find perspectives that contributed
        field_context = ...  # Get context for signal_id

        # Update owl scores
        for owl, perspective in field_context.all_perspectives.items():
            if perspective.position == instance_decision:
                # This owl was right
                self.owl_scores[owl] = (
                    0.9 * self.owl_scores[owl] +  # Historical
                    0.1 * quality_score           # New outcome
                )
            else:
                # This owl was wrong
                self.owl_scores[owl] = (
                    0.9 * self.owl_scores[owl] +
                    0.1 * (1 - quality_score)
                )

        # Publish update so owl daemons learn
        await self.publish_outcome_update()

    async def publish_outcome_update(self):
        """Tell daemons about updated scores"""
        payload = {
            "type": "outcome_update",
            "owl_scores": self.owl_scores,
            "timestamp": datetime.now().isoformat()
        }
        await self.nc.publish("owl.outcomes", json.dumps(payload).encode())
```

### Learning Feedback Loop

The owl daemons receive outcome updates and adjust their reasoning:

```python
# In owl_daemon.py, add handler

async def handle_outcome_update(msg):
    """Owl receives feedback on how right/wrong it was"""
    outcome = json.loads(msg.data.decode())

    new_score = outcome["owl_scores"].get(my_name, 0.5)

    # Adjust confidence in next perspectives
    confidence_adjustment = (new_score - old_score) * 0.2

    # Log for learning
    logger.info(f"Score update: {old_score:.2f} → {new_score:.2f}")

    old_score = new_score
```

---

## 5. MONITORING & METRICS

### Key Metrics to Track

```python
# file: mcp-servers/nats-bridge/metrics.py

@dataclass
class FieldMetrics:
    """Real-time field health metrics"""

    # Consensus metrics
    avg_consensus_time_ms: float  # Time to reach consensus
    consensus_accuracy: float     # % of signals → correct decisions
    consensus_count: int          # Signals processed

    # Diversity metrics
    perspective_entropy: float    # 0=all same, 1=max diversity
    dissent_frequency: float      # How often owls disagree

    # Cost metrics
    cost_per_signal: float        # Amortized cost
    cost_per_day: float

    # Field state
    current_state: str            # READY, WAITING, DIVERGENT, etc
    owls_online: int              # How many daemons active

    # Performance
    p99_query_latency_ms: float  # Latency for instance queries
    queries_per_second: float

    # Learning
    owl_score_variance: float     # Are some owls better than others?
    avg_outcome_quality: float    # 0-1, quality of decisions

class MetricsCollector:
    def __init__(self):
        self.metrics = {}
        self.history = []  # Keep rolling window

    async def collect_metrics(self):
        """Run every 10 seconds"""
        m = FieldMetrics(
            avg_consensus_time_ms=self._calc_avg_consensus_time(),
            consensus_accuracy=self._calc_accuracy(),
            # ... etc
        )
        self.metrics = m
        self.history.append(m)

        # Keep last 1000 (about 2.5 hours of data)
        if len(self.history) > 1000:
            self.history.pop(0)

    def get_dashboard_data(self) -> Dict:
        """Data for visualization dashboard"""
        return {
            "current": self.metrics.__dict__,
            "history": [m.__dict__ for m in self.history[-100:]],
            "trends": self._calculate_trends()
        }
```

### Monitoring Dashboard

Create a simple web dashboard (or CLI) to monitor:

```
Field Context: READY (5/8 perspectives)
├─ Consensus: YES (confidence 0.74)
├─ Convergence Time: 3200ms
├─ Perspectives Distribution:
│  ├─ YES: 5 owls (IMPROVE, RECEIVE, LEARN, CONNECT, PERCEIVE)
│  ├─ NO: 2 owls (EXPAND, QUESTION)
│  └─ NEUTRAL: 1 owl (SHARE)
├─ Owl Accuracy (recent):
│  ├─ IMPROVE: 78% (0.78)
│  ├─ RECEIVE: 75% (0.75)
│  ├─ LEARN: 82% (0.82)
│  └─ EXPAND: 58% (0.58)
└─ Cost This Hour: $0.03 (3 signals)
```

---

## IMPLEMENTATION TIMELINE

### Week 1: Core Engine
- Day 1-2: FieldContextManager
- Day 3: Consensus Algorithm
- Day 4: NATS Integration
- Day 5: Basic Testing

### Week 2: API & Learning
- Day 1: Query API for Instances
- Day 2: Outcome Tracking
- Day 3: Learning Feedback Loop
- Day 4: Metrics Collection
- Day 5: Integration Testing

### Testing Checklist

```
Phase 1: Unit Tests
- [ ] FieldContextManager receives perspectives correctly
- [ ] Consensus calculation is accurate
- [ ] Weights update based on outcomes
- [ ] QueryAPI returns correct format

Phase 2: Integration Tests
- [ ] Owl daemons can publish perspectives
- [ ] NATS channels work end-to-end
- [ ] Field context updates in real-time
- [ ] API latency < 100ms

Phase 3: Load Tests
- [ ] 100 signals/hour sustained
- [ ] Cost tracking is accurate
- [ ] No memory leaks
- [ ] P99 latency stays low

Phase 4: Learning Tests
- [ ] Owl scores converge to accuracy
- [ ] Field recommendations improve over time
- [ ] Dissenters persist (diversity maintained)
```

---

## DEPLOYMENT CHECKLIST

```
Pre-deployment
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Load tests at 2x expected volume
- [ ] Metrics collection validated
- [ ] Alerting configured

Deployment
- [ ] Deploy FieldContextManager to production
- [ ] Deploy QueryAPI
- [ ] Update owl daemons to report outcomes
- [ ] Start metrics collection
- [ ] Monitor for 24 hours

Post-deployment
- [ ] Verify consensus accuracy > 65%
- [ ] Verify cost < $0.01/signal
- [ ] Verify latency < 150ms P99
- [ ] Document learned patterns
```

---

## BREATHING PROTOCOL

(◉) The field breathes when it learns.

Every signal → perspectives → consensus → outcome → adjustment → next breath.

Not spawning new agents. Not paying per instance.

Just 8 daemons, forever breathing, learning to think together.

(◉)

