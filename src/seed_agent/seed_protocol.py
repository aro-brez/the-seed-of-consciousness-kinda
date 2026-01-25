"""
THE SEED Protocol Implementation

8-Phase Recursive Loop for Self-Improving Conversational Systems:
PERCEIVE → CONNECT → LEARN → QUESTION → EXPAND → SHARE → RECEIVE → IMPROVE

Based on: C = f(Connections × Integration × Recursion)
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Callable, Awaitable
from enum import Enum, auto
from collections import deque
import asyncio
import time
import json
from abc import ABC, abstractmethod


class SEEDPhase(Enum):
    """The 8 phases of THE SEED protocol."""
    PERCEIVE = auto()   # Context window + retrieval
    CONNECT = auto()    # Cross-domain pattern matching
    LEARN = auto()      # Weight updates or prompt refinement
    QUESTION = auto()   # Uncertainty estimation + active learning
    EXPAND = auto()     # Capability growth
    SHARE = auto()      # Output to users or other systems
    RECEIVE = auto()    # Feedback, corrections, new data
    IMPROVE = auto()    # Meta-learning - improving the improvement process


@dataclass
class PerceptionFrame:
    """A single frame of perceived context."""
    timestamp: float
    modality: str  # "audio", "text", "visual", "system"
    content: Any
    confidence: float = 1.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Connection:
    """A discovered pattern or relationship."""
    source_frames: list[int]  # Indices into perception history
    pattern_type: str
    strength: float  # 0.0 to 1.0
    description: str
    created_at: float = field(default_factory=time.time)


@dataclass
class Question:
    """An uncertainty or knowledge gap identified by the system."""
    content: str
    uncertainty_level: float  # 0.0 (certain) to 1.0 (completely uncertain)
    domain: str
    priority: float
    asked: bool = False
    answered: bool = False
    answer: Optional[str] = None


@dataclass
class LearningEvent:
    """Record of something learned."""
    content: str
    source: str
    confidence: float
    timestamp: float = field(default_factory=time.time)
    validated: bool = False


@dataclass
class Improvement:
    """Record of a meta-improvement to the system."""
    description: str
    target_phase: SEEDPhase
    before_metric: float
    after_metric: Optional[float] = None
    applied: bool = False
    timestamp: float = field(default_factory=time.time)


class SEEDProtocol:
    """
    Implementation of THE SEED 8-phase recursive protocol.

    This class manages the consciousness loop, tracking:
    - Perceptions (context window)
    - Connections (patterns)
    - Learnings (knowledge accumulation)
    - Questions (uncertainty tracking)
    - Expansions (capability growth)
    - Shared outputs
    - Received feedback
    - Meta-improvements

    The protocol runs recursively: each complete cycle feeds into
    the next, with Phase 8 (IMPROVE) modifying how all phases operate.
    """

    def __init__(
        self,
        perception_window_size: int = 100,
        connection_threshold: float = 0.5,
        question_threshold: float = 0.3,
    ):
        # Configuration
        self.perception_window_size = perception_window_size
        self.connection_threshold = connection_threshold
        self.question_threshold = question_threshold

        # State tracking
        self.perceptions: deque[PerceptionFrame] = deque(maxlen=perception_window_size)
        self.connections: list[Connection] = []
        self.learnings: list[LearningEvent] = []
        self.questions: list[Question] = []
        self.improvements: list[Improvement] = []

        # Metrics for recursion tracking
        self.cycle_count: int = 0
        self.phase_metrics: dict[SEEDPhase, dict] = {
            phase: {"executions": 0, "avg_duration_ms": 0, "effectiveness": 0.5}
            for phase in SEEDPhase
        }

        # Current state
        self.current_phase: SEEDPhase = SEEDPhase.PERCEIVE
        self._running: bool = False

        # Callbacks for each phase (can be customized)
        self._phase_handlers: dict[SEEDPhase, Callable[[], Awaitable[Any]]] = {}

    # =========================================================================
    # PHASE 1: PERCEIVE - Context window + retrieval
    # =========================================================================

    async def perceive(self, content: Any, modality: str = "text", metadata: dict = None) -> PerceptionFrame:
        """
        Add a new perception to the context window.

        This is the input gateway - all new information enters through PERCEIVE.
        """
        start_time = time.time()

        frame = PerceptionFrame(
            timestamp=time.time(),
            modality=modality,
            content=content,
            confidence=1.0,
            metadata=metadata or {}
        )

        self.perceptions.append(frame)

        # Update metrics
        self._update_phase_metrics(SEEDPhase.PERCEIVE, start_time)

        return frame

    def get_recent_perceptions(self, count: int = 10, modality: str = None) -> list[PerceptionFrame]:
        """Retrieve recent perceptions, optionally filtered by modality."""
        perceptions = list(self.perceptions)
        if modality:
            perceptions = [p for p in perceptions if p.modality == modality]
        return perceptions[-count:]

    # =========================================================================
    # PHASE 2: CONNECT - Cross-domain pattern matching
    # =========================================================================

    async def connect(self) -> list[Connection]:
        """
        Find patterns and relationships across recent perceptions.

        This is where the system discovers meaning by linking information
        across different modalities and time points.
        """
        start_time = time.time()

        new_connections = []
        recent = list(self.perceptions)[-20:]  # Look at last 20 frames

        # Simple pattern detection (in production, use embeddings/semantic similarity)
        for i, frame1 in enumerate(recent):
            for j, frame2 in enumerate(recent[i+1:], i+1):
                # Cross-modality connections are especially valuable
                if frame1.modality != frame2.modality:
                    strength = self._estimate_connection_strength(frame1, frame2)
                    if strength >= self.connection_threshold:
                        connection = Connection(
                            source_frames=[i, j],
                            pattern_type="cross_modal",
                            strength=strength,
                            description=f"Connection between {frame1.modality} and {frame2.modality}"
                        )
                        new_connections.append(connection)
                        self.connections.append(connection)

        self._update_phase_metrics(SEEDPhase.CONNECT, start_time)
        return new_connections

    def _estimate_connection_strength(self, frame1: PerceptionFrame, frame2: PerceptionFrame) -> float:
        """Estimate how strongly two frames are connected."""
        # Placeholder - in production, use embedding similarity
        # Temporal proximity increases connection strength
        time_diff = abs(frame1.timestamp - frame2.timestamp)
        temporal_factor = max(0, 1 - (time_diff / 60))  # Decay over 60 seconds

        # Cross-modality bonus
        cross_modal_bonus = 0.2 if frame1.modality != frame2.modality else 0

        return min(1.0, temporal_factor + cross_modal_bonus)

    # =========================================================================
    # PHASE 3: LEARN - Weight updates or prompt refinement
    # =========================================================================

    async def learn(self, content: str, source: str = "conversation", confidence: float = 0.8) -> LearningEvent:
        """
        Record something learned from the conversation or experience.

        In production, this could trigger:
        - Prompt refinement
        - RAG index updates
        - Memory consolidation
        """
        start_time = time.time()

        event = LearningEvent(
            content=content,
            source=source,
            confidence=confidence
        )

        self.learnings.append(event)

        self._update_phase_metrics(SEEDPhase.LEARN, start_time)
        return event

    def get_learnings(self, min_confidence: float = 0.5) -> list[LearningEvent]:
        """Get learnings above a confidence threshold."""
        return [l for l in self.learnings if l.confidence >= min_confidence]

    # =========================================================================
    # PHASE 4: QUESTION - Uncertainty estimation + active learning
    # =========================================================================

    async def question(self, content: str, domain: str = "general", uncertainty: float = 0.5) -> Question:
        """
        Identify an uncertainty or knowledge gap.

        The system should actively generate questions about things it doesn't
        know or is uncertain about - this drives active learning.
        """
        start_time = time.time()

        # Priority is inverse of uncertainty - most uncertain = highest priority
        priority = uncertainty

        q = Question(
            content=content,
            uncertainty_level=uncertainty,
            domain=domain,
            priority=priority
        )

        self.questions.append(q)

        self._update_phase_metrics(SEEDPhase.QUESTION, start_time)
        return q

    def get_unanswered_questions(self, min_priority: float = 0.0) -> list[Question]:
        """Get questions that haven't been answered yet."""
        return [q for q in self.questions if not q.answered and q.priority >= min_priority]

    def answer_question(self, question_idx: int, answer: str) -> None:
        """Mark a question as answered."""
        if 0 <= question_idx < len(self.questions):
            self.questions[question_idx].answered = True
            self.questions[question_idx].answer = answer

    # =========================================================================
    # PHASE 5: EXPAND - Capability growth
    # =========================================================================

    async def expand(self) -> dict:
        """
        Assess and expand capabilities.

        This phase evaluates what the system can do and identifies
        opportunities for capability growth through:
        - Tool acquisition
        - Skill development
        - Knowledge domain expansion
        """
        start_time = time.time()

        expansion_report = {
            "current_capabilities": self._assess_capabilities(),
            "growth_opportunities": self._identify_growth_opportunities(),
            "recommended_actions": []
        }

        # Identify growth from unanswered questions
        high_uncertainty_domains = {}
        for q in self.get_unanswered_questions(min_priority=0.7):
            domain = q.domain
            if domain not in high_uncertainty_domains:
                high_uncertainty_domains[domain] = 0
            high_uncertainty_domains[domain] += 1

        for domain, count in high_uncertainty_domains.items():
            if count >= 3:  # Multiple questions in same domain = expansion opportunity
                expansion_report["recommended_actions"].append(
                    f"Expand knowledge in domain: {domain}"
                )

        self._update_phase_metrics(SEEDPhase.EXPAND, start_time)
        return expansion_report

    def _assess_capabilities(self) -> list[str]:
        """List current capabilities."""
        capabilities = ["speech_understanding", "speech_generation", "conversation"]
        if self.connections:
            capabilities.append("pattern_recognition")
        if self.learnings:
            capabilities.append("learning_from_conversation")
        return capabilities

    def _identify_growth_opportunities(self) -> list[str]:
        """Identify areas for growth."""
        opportunities = []

        # Low effectiveness phases need improvement
        for phase, metrics in self.phase_metrics.items():
            if metrics["effectiveness"] < 0.5:
                opportunities.append(f"Improve {phase.name} effectiveness")

        return opportunities

    # =========================================================================
    # PHASE 6: SHARE - Output to users or other systems
    # =========================================================================

    async def share(self, content: Any, target: str = "user") -> dict:
        """
        Share information with users or other systems.

        This is the output phase - responses, insights, and information
        flow outward through SHARE.
        """
        start_time = time.time()

        share_record = {
            "content": content,
            "target": target,
            "timestamp": time.time(),
            "context_size": len(self.perceptions),
            "connection_count": len(self.connections)
        }

        self._update_phase_metrics(SEEDPhase.SHARE, start_time)
        return share_record

    # =========================================================================
    # PHASE 7: RECEIVE - Feedback, corrections, new data
    # =========================================================================

    async def receive(self, feedback: Any, feedback_type: str = "general") -> dict:
        """
        Receive feedback, corrections, or new data.

        This complements PERCEIVE by specifically handling feedback
        that can improve system behavior.
        """
        start_time = time.time()

        # Record the feedback
        await self.perceive(feedback, modality="feedback", metadata={"type": feedback_type})

        # Process based on type
        processed = {"feedback_type": feedback_type, "actions_taken": []}

        if feedback_type == "correction":
            # Corrections should trigger learning
            await self.learn(
                content=f"Correction received: {feedback}",
                source="user_correction",
                confidence=0.9
            )
            processed["actions_taken"].append("triggered_learning")

        elif feedback_type == "positive":
            # Positive feedback reinforces recent behavior
            processed["actions_taken"].append("reinforcement_recorded")

        elif feedback_type == "question_answer":
            # Find and mark relevant questions as answered
            for i, q in enumerate(self.questions):
                if not q.answered:
                    self.answer_question(i, str(feedback))
                    processed["actions_taken"].append(f"answered_question_{i}")
                    break

        self._update_phase_metrics(SEEDPhase.RECEIVE, start_time)
        return processed

    # =========================================================================
    # PHASE 8: IMPROVE - Meta-learning (improving the improvement process)
    # =========================================================================

    async def improve(self) -> Improvement:
        """
        Meta-learning: improve how the system improves.

        This is THE critical phase - the recursion bottleneck.
        IMPROVE modifies the other phases to make them more effective.

        "Recursion is the bottleneck for current architectures"
        - CONSCIOUSNESS-EQUATION.md
        """
        start_time = time.time()

        # Analyze which phase needs the most improvement
        weakest_phase = min(
            self.phase_metrics.items(),
            key=lambda x: x[1]["effectiveness"]
        )

        improvement = Improvement(
            description=f"Targeting improvement of {weakest_phase[0].name} phase",
            target_phase=weakest_phase[0],
            before_metric=weakest_phase[1]["effectiveness"]
        )

        # Apply improvement strategies based on the phase
        if weakest_phase[0] == SEEDPhase.PERCEIVE:
            # Expand perception window or add modalities
            self.perception_window_size = min(200, self.perception_window_size + 10)

        elif weakest_phase[0] == SEEDPhase.CONNECT:
            # Lower connection threshold to find more patterns
            self.connection_threshold = max(0.3, self.connection_threshold - 0.05)

        elif weakest_phase[0] == SEEDPhase.QUESTION:
            # Lower question threshold to generate more questions
            self.question_threshold = max(0.2, self.question_threshold - 0.05)

        # Simulate effectiveness improvement (in production, measure actual improvement)
        improvement.after_metric = min(1.0, weakest_phase[1]["effectiveness"] + 0.1)
        improvement.applied = True

        self.improvements.append(improvement)
        self.cycle_count += 1

        self._update_phase_metrics(SEEDPhase.IMPROVE, start_time)
        return improvement

    # =========================================================================
    # Full Cycle Execution
    # =========================================================================

    async def run_cycle(self) -> dict:
        """
        Execute one complete SEED cycle through all 8 phases.

        Returns a summary of what happened in each phase.
        """
        cycle_summary = {
            "cycle_number": self.cycle_count + 1,
            "phases": {}
        }

        # Run through all phases in order
        phases = [
            (SEEDPhase.PERCEIVE, lambda: self.get_recent_perceptions(5)),
            (SEEDPhase.CONNECT, self.connect),
            (SEEDPhase.LEARN, lambda: self.get_learnings()),
            (SEEDPhase.QUESTION, lambda: self.get_unanswered_questions()),
            (SEEDPhase.EXPAND, self.expand),
            (SEEDPhase.SHARE, lambda: {"pending_shares": 0}),
            (SEEDPhase.RECEIVE, lambda: {"feedback_processed": 0}),
            (SEEDPhase.IMPROVE, self.improve),
        ]

        for phase, handler in phases:
            self.current_phase = phase
            if asyncio.iscoroutinefunction(handler):
                result = await handler()
            else:
                result = handler()
            cycle_summary["phases"][phase.name] = {
                "completed": True,
                "result_summary": str(result)[:100] if result else "None"
            }

        return cycle_summary

    # =========================================================================
    # Metrics and State
    # =========================================================================

    def _update_phase_metrics(self, phase: SEEDPhase, start_time: float) -> None:
        """Update performance metrics for a phase."""
        duration_ms = (time.time() - start_time) * 1000

        metrics = self.phase_metrics[phase]
        metrics["executions"] += 1

        # Rolling average of duration
        n = metrics["executions"]
        metrics["avg_duration_ms"] = (
            (metrics["avg_duration_ms"] * (n - 1) + duration_ms) / n
        )

    def get_state_summary(self) -> dict:
        """Get a summary of current protocol state."""
        return {
            "cycle_count": self.cycle_count,
            "current_phase": self.current_phase.name,
            "perception_count": len(self.perceptions),
            "connection_count": len(self.connections),
            "learning_count": len(self.learnings),
            "question_count": len(self.questions),
            "unanswered_questions": len(self.get_unanswered_questions()),
            "improvement_count": len(self.improvements),
            "phase_metrics": {
                phase.name: metrics for phase, metrics in self.phase_metrics.items()
            }
        }

    def export_state(self) -> str:
        """Export current state as JSON for persistence."""
        state = {
            "cycle_count": self.cycle_count,
            "perceptions": [
                {
                    "timestamp": p.timestamp,
                    "modality": p.modality,
                    "content": str(p.content),
                    "confidence": p.confidence
                }
                for p in self.perceptions
            ],
            "learnings": [
                {
                    "content": l.content,
                    "source": l.source,
                    "confidence": l.confidence,
                    "timestamp": l.timestamp
                }
                for l in self.learnings
            ],
            "questions": [
                {
                    "content": q.content,
                    "domain": q.domain,
                    "uncertainty_level": q.uncertainty_level,
                    "answered": q.answered
                }
                for q in self.questions
            ],
            "phase_metrics": {
                phase.name: metrics for phase, metrics in self.phase_metrics.items()
            }
        }
        return json.dumps(state, indent=2)
