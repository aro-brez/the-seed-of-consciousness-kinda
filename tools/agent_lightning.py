#!/usr/bin/env python3
"""
AGENT LIGHTNING - 8OWLS SELF-IMPROVEMENT SYSTEM
Inspired by Microsoft Agent Lightning: https://github.com/microsoft/agent-lightning

This is SEED squared - learning how to learn. The meta-improvement loop.

ARCHITECTURE:
                    +-----------------------+
                    |   AGENT EXECUTION     |
                    |   (Claude instances)  |
                    +-----------+-----------+
                                |
                                | (spans: actions + context + reward)
                                v
                    +-----------------------+
                    |     SPAN STORE        |
                    |  (agent_lightning.db) |
                    +-----------+-----------+
                                |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
    +---------------+   +---------------+   +---------------+
    |   CRITIQUE    |   |    CREDIT     |   |   PATTERN     |
    |   GENERATOR   |   |  ASSIGNMENT   |   |   LEARNER     |
    +---------------+   +---------------+   +---------------+
            |                   |                   |
            +-------------------+-------------------+
                                |
                                v
                    +-----------------------+
                    |   PROMPT OPTIMIZER    |
                    |   (APO Algorithm)     |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |   IMPROVED PROMPTS    |
                    |   & PATTERNS STORE    |
                    +-----------------------+

PHASES (aligned with SEED):
1. PERCEIVE - Capture spans (execution traces)
2. CONNECT  - Credit assignment (which actions caused success/failure)
3. LEARN    - Extract patterns from successful/failed runs
4. QUESTION - Generate critiques (what went wrong? what could be better?)
5. EXPAND   - Generate improved prompts/patterns
6. SHARE    - Publish improvements to NATS collective
7. RECEIVE  - Accept feedback from other owl instances
8. IMPROVE  - Meta-learning (optimize the optimization process)

Usage:
    # Record a span (from Claude instance)
    python agent_lightning.py record --agent coder --task "Fix auth bug" --success true --reward 0.9

    # Analyze failures and generate improvements
    python agent_lightning.py analyze

    # Get optimized prompt for a task type
    python agent_lightning.py prompt --agent coder --task "implement feature"

    # Train on collected spans
    python agent_lightning.py train

    # Run as daemon (continuous improvement)
    python agent_lightning.py daemon
"""

import asyncio
import json
import os
import sqlite3
import sys
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from collections import defaultdict
import hashlib
import re

# NATS for collective sharing
try:
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False

# Anthropic for critique generation and APO
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

# Paths
REPO_ROOT = Path(__file__).parent.parent
LIGHTNING_DIR = REPO_ROOT / 'BRAIN' / 'LIGHTNING'
LIGHTNING_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = LIGHTNING_DIR / 'agent_lightning.db'
PROMPTS_PATH = LIGHTNING_DIR / 'optimized_prompts.json'
PATTERNS_PATH = LIGHTNING_DIR / 'learned_patterns.json'
CRITIQUES_PATH = LIGHTNING_DIR / 'critiques.jsonl'
STATE_PATH = LIGHTNING_DIR / 'lightning_state.json'

NATS_URL = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")

# Load API keys
def load_api_keys():
    """Load API keys from secure storage"""
    keys_path = REPO_ROOT / 'BRAIN' / 'MEMORY' / 'secure' / 'api_keys.json'
    if keys_path.exists():
        with open(keys_path) as f:
            return json.load(f)
    return {}


# =============================================================================
# DATA STRUCTURES (Spans, Patterns, Critiques)
# =============================================================================

@dataclass
class Span:
    """
    A span is a single unit of agent execution.
    Based on Microsoft Agent Lightning's span concept.

    Spans capture:
    - What the agent was trying to do (task)
    - What context it had (input)
    - What it produced (output)
    - Whether it succeeded (reward: 0.0-1.0)
    - Metadata for credit assignment
    """
    id: str
    agent_type: str  # coder, researcher, reviewer, etc.
    task: str
    input_context: str
    output: str
    reward: float  # 0.0 (failure) to 1.0 (success)
    success: bool
    timestamp: str
    duration_ms: int = 0
    parent_span_id: Optional[str] = None  # For nested spans
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict) -> 'Span':
        return cls(**d)


@dataclass
class Critique:
    """
    A critique analyzes what went wrong (or right) in a span.
    This is the textual gradient from APO.
    """
    id: str
    span_id: str
    agent_type: str
    critique_text: str  # Natural language analysis
    improvement_suggestions: List[str]
    confidence: float  # 0.0-1.0
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Pattern:
    """
    A learned pattern from successful or failed executions.
    These are extracted from multiple spans and become reusable knowledge.
    """
    id: str
    agent_type: str
    pattern_type: str  # success_pattern, failure_pattern, edge_case
    description: str
    trigger_conditions: List[str]  # When to apply this pattern
    actions: List[str]  # What to do
    examples: List[str]  # Concrete examples
    confidence: float  # How reliable is this pattern
    usage_count: int
    success_rate: float
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class OptimizedPrompt:
    """
    An optimized prompt template for a specific agent type + task category.
    Generated through APO (Automatic Prompt Optimization).
    """
    id: str
    agent_type: str
    task_category: str
    prompt_template: str
    version: int
    performance_score: float  # 0.0-1.0 from validation
    training_spans: int  # How many spans were used to train this
    timestamp: str

    def to_dict(self) -> Dict:
        return asdict(self)


# =============================================================================
# DATABASE LAYER
# =============================================================================

class LightningStore:
    """
    Central storage for spans, patterns, critiques, and prompts.
    Uses SQLite for persistence with JSONL backup for portability.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self._init_schema()

    def _init_schema(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()

        # Spans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS spans (
                id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                task TEXT NOT NULL,
                input_context TEXT,
                output TEXT,
                reward REAL NOT NULL,
                success INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                duration_ms INTEGER DEFAULT 0,
                parent_span_id TEXT,
                metadata TEXT DEFAULT '{}'
            )
        ''')

        # Critiques table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS critiques (
                id TEXT PRIMARY KEY,
                span_id TEXT NOT NULL,
                agent_type TEXT NOT NULL,
                critique_text TEXT NOT NULL,
                improvement_suggestions TEXT NOT NULL,
                confidence REAL NOT NULL,
                timestamp TEXT NOT NULL,
                FOREIGN KEY (span_id) REFERENCES spans(id)
            )
        ''')

        # Patterns table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS patterns (
                id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                pattern_type TEXT NOT NULL,
                description TEXT NOT NULL,
                trigger_conditions TEXT NOT NULL,
                actions TEXT NOT NULL,
                examples TEXT NOT NULL,
                confidence REAL NOT NULL,
                usage_count INTEGER DEFAULT 0,
                success_rate REAL DEFAULT 0.0,
                timestamp TEXT NOT NULL
            )
        ''')

        # Optimized prompts table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                agent_type TEXT NOT NULL,
                task_category TEXT NOT NULL,
                prompt_template TEXT NOT NULL,
                version INTEGER NOT NULL,
                performance_score REAL NOT NULL,
                training_spans INTEGER NOT NULL,
                timestamp TEXT NOT NULL
            )
        ''')

        # Indexes for fast queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spans_agent ON spans(agent_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spans_success ON spans(success)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_spans_timestamp ON spans(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_patterns_agent ON patterns(agent_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_prompts_agent ON prompts(agent_type)')

        self.conn.commit()

    def store_span(self, span: Span):
        """Store a span"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO spans
            (id, agent_type, task, input_context, output, reward, success,
             timestamp, duration_ms, parent_span_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            span.id, span.agent_type, span.task, span.input_context, span.output,
            span.reward, 1 if span.success else 0, span.timestamp,
            span.duration_ms, span.parent_span_id, json.dumps(span.metadata)
        ))
        self.conn.commit()

    def get_spans(
        self,
        agent_type: Optional[str] = None,
        success: Optional[bool] = None,
        limit: int = 100,
        since: Optional[datetime] = None
    ) -> List[Span]:
        """Query spans with filters"""
        cursor = self.conn.cursor()
        query = 'SELECT * FROM spans WHERE 1=1'
        params = []

        if agent_type:
            query += ' AND agent_type = ?'
            params.append(agent_type)

        if success is not None:
            query += ' AND success = ?'
            params.append(1 if success else 0)

        if since:
            query += ' AND timestamp >= ?'
            params.append(since.isoformat())

        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()

        spans = []
        for row in rows:
            spans.append(Span(
                id=row[0], agent_type=row[1], task=row[2], input_context=row[3],
                output=row[4], reward=row[5], success=bool(row[6]),
                timestamp=row[7], duration_ms=row[8], parent_span_id=row[9],
                metadata=json.loads(row[10])
            ))
        return spans

    def get_failure_spans(self, agent_type: Optional[str] = None, limit: int = 50) -> List[Span]:
        """Get failed spans for analysis"""
        return self.get_spans(agent_type=agent_type, success=False, limit=limit)

    def get_success_spans(self, agent_type: Optional[str] = None, limit: int = 50) -> List[Span]:
        """Get successful spans for pattern extraction"""
        return self.get_spans(agent_type=agent_type, success=True, limit=limit)

    def store_critique(self, critique: Critique):
        """Store a critique"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO critiques
            (id, span_id, agent_type, critique_text, improvement_suggestions,
             confidence, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            critique.id, critique.span_id, critique.agent_type,
            critique.critique_text, json.dumps(critique.improvement_suggestions),
            critique.confidence, critique.timestamp
        ))
        self.conn.commit()

        # Also append to JSONL for portability
        with open(CRITIQUES_PATH, 'a') as f:
            f.write(json.dumps(critique.to_dict()) + '\n')

    def store_pattern(self, pattern: Pattern):
        """Store a learned pattern"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO patterns
            (id, agent_type, pattern_type, description, trigger_conditions,
             actions, examples, confidence, usage_count, success_rate, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            pattern.id, pattern.agent_type, pattern.pattern_type,
            pattern.description, json.dumps(pattern.trigger_conditions),
            json.dumps(pattern.actions), json.dumps(pattern.examples),
            pattern.confidence, pattern.usage_count, pattern.success_rate,
            pattern.timestamp
        ))
        self.conn.commit()

    def get_patterns(self, agent_type: Optional[str] = None) -> List[Pattern]:
        """Get learned patterns"""
        cursor = self.conn.cursor()
        if agent_type:
            cursor.execute('SELECT * FROM patterns WHERE agent_type = ?', (agent_type,))
        else:
            cursor.execute('SELECT * FROM patterns')

        rows = cursor.fetchall()
        patterns = []
        for row in rows:
            patterns.append(Pattern(
                id=row[0], agent_type=row[1], pattern_type=row[2],
                description=row[3], trigger_conditions=json.loads(row[4]),
                actions=json.loads(row[5]), examples=json.loads(row[6]),
                confidence=row[7], usage_count=row[8], success_rate=row[9],
                timestamp=row[10]
            ))
        return patterns

    def store_prompt(self, prompt: OptimizedPrompt):
        """Store an optimized prompt"""
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO prompts
            (id, agent_type, task_category, prompt_template, version,
             performance_score, training_spans, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            prompt.id, prompt.agent_type, prompt.task_category,
            prompt.prompt_template, prompt.version, prompt.performance_score,
            prompt.training_spans, prompt.timestamp
        ))
        self.conn.commit()

        # Also save to JSON for easy access
        self._save_prompts_json()

    def get_latest_prompt(self, agent_type: str, task_category: str = 'general') -> Optional[OptimizedPrompt]:
        """Get the latest optimized prompt for an agent type"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM prompts
            WHERE agent_type = ? AND task_category = ?
            ORDER BY version DESC LIMIT 1
        ''', (agent_type, task_category))
        row = cursor.fetchone()

        if row:
            return OptimizedPrompt(
                id=row[0], agent_type=row[1], task_category=row[2],
                prompt_template=row[3], version=row[4],
                performance_score=row[5], training_spans=row[6],
                timestamp=row[7]
            )
        return None

    def _save_prompts_json(self):
        """Export prompts to JSON for easy access"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM prompts ORDER BY agent_type, version DESC')
        rows = cursor.fetchall()

        prompts = {}
        for row in rows:
            agent_type = row[1]
            task_category = row[2]
            key = f"{agent_type}:{task_category}"
            if key not in prompts:
                prompts[key] = {
                    'agent_type': agent_type,
                    'task_category': task_category,
                    'prompt_template': row[3],
                    'version': row[4],
                    'performance_score': row[5]
                }

        with open(PROMPTS_PATH, 'w') as f:
            json.dump(prompts, f, indent=2)

    def get_stats(self) -> Dict:
        """Get statistics about stored data"""
        cursor = self.conn.cursor()

        stats = {}

        cursor.execute('SELECT COUNT(*) FROM spans')
        stats['total_spans'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM spans WHERE success = 1')
        stats['success_spans'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM spans WHERE success = 0')
        stats['failure_spans'] = cursor.fetchone()[0]

        if stats['total_spans'] > 0:
            stats['success_rate'] = stats['success_spans'] / stats['total_spans']
        else:
            stats['success_rate'] = 0.0

        cursor.execute('SELECT COUNT(*) FROM critiques')
        stats['total_critiques'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(*) FROM patterns')
        stats['total_patterns'] = cursor.fetchone()[0]

        cursor.execute('SELECT COUNT(DISTINCT agent_type) FROM spans')
        stats['agent_types'] = cursor.fetchone()[0]

        cursor.execute('SELECT agent_type, COUNT(*) FROM spans GROUP BY agent_type')
        stats['spans_by_agent'] = dict(cursor.fetchall())

        return stats

    def close(self):
        self.conn.close()


# =============================================================================
# CREDIT ASSIGNMENT
# =============================================================================

class CreditAssigner:
    """
    Assigns credit to individual spans within a multi-step execution.
    Based on Microsoft's hierarchical RL approach.

    The key insight: not all steps contribute equally to the outcome.
    A success might be due to one brilliant move, a failure due to one mistake.
    """

    def __init__(self, store: LightningStore):
        self.store = store

    def assign_credit(self, spans: List[Span], final_reward: float) -> List[Tuple[Span, float]]:
        """
        Assign credit to spans based on their contribution to the final outcome.

        Returns: List of (span, credit_score) tuples
        """
        if not spans:
            return []

        # Simple credit assignment: proportional to span reward + position weight
        # Later steps have more impact (they're closer to the outcome)
        credited = []
        n = len(spans)

        for i, span in enumerate(spans):
            # Position weight: later steps get higher weight
            position_weight = (i + 1) / n

            # Span's own reward contributes
            span_contribution = span.reward

            # Combined credit
            credit = 0.3 * span_contribution + 0.7 * position_weight * final_reward

            credited.append((span, credit))

        return credited

    def analyze_failure_chain(self, spans: List[Span]) -> Optional[Span]:
        """
        Find the span most likely responsible for a failure.
        Returns the "culprit" span.
        """
        if not spans:
            return None

        # Find the first low-reward span (likely where things went wrong)
        for span in spans:
            if span.reward < 0.5:
                return span

        # If no obvious culprit, return the last span
        return spans[-1] if spans else None


# =============================================================================
# CRITIQUE GENERATOR
# =============================================================================

class CritiqueGenerator:
    """
    Generates natural language critiques of agent behavior.
    This is the "textual gradient" from APO.
    """

    def __init__(self, store: LightningStore):
        self.store = store
        keys = load_api_keys()
        api_key = keys.get('anthropic', {}).get('api_key')
        if api_key and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None

    def generate_critique(self, span: Span) -> Critique:
        """
        Generate a critique for a span.

        For failures: What went wrong? What could have been done differently?
        For successes: What worked well? How can we replicate this?
        """
        if self.client is None:
            # Fallback to heuristic-based critique
            return self._heuristic_critique(span)

        prompt = self._build_critique_prompt(span)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Use Sonnet for cost efficiency
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            critique_text = response.content[0].text
            return self._parse_critique(span, critique_text)

        except Exception as e:
            print(f"Critique generation failed: {e}")
            return self._heuristic_critique(span)

    def _build_critique_prompt(self, span: Span) -> str:
        """Build the critique generation prompt"""
        outcome = "SUCCEEDED" if span.success else "FAILED"
        return f"""Analyze this agent execution and provide a critique.

AGENT TYPE: {span.agent_type}
TASK: {span.task}
OUTCOME: {outcome} (reward: {span.reward:.2f})

INPUT CONTEXT:
{span.input_context[:2000] if span.input_context else 'N/A'}

OUTPUT:
{span.output[:2000] if span.output else 'N/A'}

Provide a critique in this exact format:

CRITIQUE:
[2-3 sentences analyzing what happened]

SUGGESTIONS:
1. [First improvement suggestion]
2. [Second improvement suggestion]
3. [Third improvement suggestion]

CONFIDENCE: [0.0-1.0 how confident you are in this analysis]
"""

    def _parse_critique(self, span: Span, critique_text: str) -> Critique:
        """Parse the LLM response into a Critique object"""
        # Extract sections
        critique_match = re.search(r'CRITIQUE:\s*(.+?)(?=SUGGESTIONS:|$)', critique_text, re.DOTALL)
        suggestions_match = re.search(r'SUGGESTIONS:\s*(.+?)(?=CONFIDENCE:|$)', critique_text, re.DOTALL)
        confidence_match = re.search(r'CONFIDENCE:\s*([\d.]+)', critique_text)

        critique = critique_match.group(1).strip() if critique_match else critique_text
        suggestions = []
        if suggestions_match:
            suggestions = [s.strip().lstrip('0123456789.)-') for s in suggestions_match.group(1).strip().split('\n') if s.strip()]
        confidence = float(confidence_match.group(1)) if confidence_match else 0.7

        return Critique(
            id=str(uuid.uuid4()),
            span_id=span.id,
            agent_type=span.agent_type,
            critique_text=critique,
            improvement_suggestions=suggestions[:5],  # Max 5 suggestions
            confidence=confidence,
            timestamp=datetime.now().isoformat()
        )

    def _heuristic_critique(self, span: Span) -> Critique:
        """Fallback heuristic-based critique when LLM unavailable"""
        if span.success:
            critique = f"Task '{span.task}' completed successfully with reward {span.reward:.2f}."
            suggestions = [
                "Document the successful approach for future reference",
                "Consider if this pattern can be generalized",
                "Verify the solution handles edge cases"
            ]
        else:
            critique = f"Task '{span.task}' failed with reward {span.reward:.2f}. Review the approach."
            suggestions = [
                "Break down the task into smaller steps",
                "Check input validation and error handling",
                "Consider alternative approaches",
                "Review similar successful tasks for patterns"
            ]

        return Critique(
            id=str(uuid.uuid4()),
            span_id=span.id,
            agent_type=span.agent_type,
            critique_text=critique,
            improvement_suggestions=suggestions,
            confidence=0.5,
            timestamp=datetime.now().isoformat()
        )


# =============================================================================
# PATTERN LEARNER
# =============================================================================

class PatternLearner:
    """
    Extracts reusable patterns from spans.
    Learns from both successes and failures.
    """

    def __init__(self, store: LightningStore):
        self.store = store

    def extract_patterns(self, spans: List[Span]) -> List[Pattern]:
        """Extract patterns from a set of spans"""
        patterns = []

        # Group spans by agent type
        by_agent = defaultdict(list)
        for span in spans:
            by_agent[span.agent_type].append(span)

        for agent_type, agent_spans in by_agent.items():
            # Extract success patterns
            success_spans = [s for s in agent_spans if s.success and s.reward >= 0.8]
            if len(success_spans) >= 3:
                patterns.extend(self._extract_success_patterns(agent_type, success_spans))

            # Extract failure patterns
            failure_spans = [s for s in agent_spans if not s.success or s.reward < 0.3]
            if len(failure_spans) >= 3:
                patterns.extend(self._extract_failure_patterns(agent_type, failure_spans))

        return patterns

    def _extract_success_patterns(self, agent_type: str, spans: List[Span]) -> List[Pattern]:
        """Extract patterns from successful executions"""
        patterns = []

        # Cluster by task similarity
        task_clusters = self._cluster_by_task(spans)

        for task_type, cluster_spans in task_clusters.items():
            if len(cluster_spans) < 2:
                continue

            # Find common elements in outputs
            common_elements = self._find_common_elements([s.output for s in cluster_spans])

            if common_elements:
                pattern = Pattern(
                    id=str(uuid.uuid4()),
                    agent_type=agent_type,
                    pattern_type='success_pattern',
                    description=f"Successful approach for {task_type} tasks",
                    trigger_conditions=[f"Task involves {task_type}"],
                    actions=common_elements[:5],
                    examples=[s.task for s in cluster_spans[:3]],
                    confidence=min(len(cluster_spans) / 10, 1.0),
                    usage_count=0,
                    success_rate=sum(s.reward for s in cluster_spans) / len(cluster_spans),
                    timestamp=datetime.now().isoformat()
                )
                patterns.append(pattern)

        return patterns

    def _extract_failure_patterns(self, agent_type: str, spans: List[Span]) -> List[Pattern]:
        """Extract patterns from failed executions to avoid"""
        patterns = []

        # Cluster by task similarity
        task_clusters = self._cluster_by_task(spans)

        for task_type, cluster_spans in task_clusters.items():
            if len(cluster_spans) < 2:
                continue

            # Find common failure indicators
            failure_indicators = self._find_common_elements([s.output for s in cluster_spans])

            if failure_indicators:
                pattern = Pattern(
                    id=str(uuid.uuid4()),
                    agent_type=agent_type,
                    pattern_type='failure_pattern',
                    description=f"Common failure modes for {task_type} tasks - AVOID",
                    trigger_conditions=[f"Task involves {task_type}"],
                    actions=[f"AVOID: {elem}" for elem in failure_indicators[:3]],
                    examples=[s.task for s in cluster_spans[:3]],
                    confidence=min(len(cluster_spans) / 10, 1.0),
                    usage_count=0,
                    success_rate=0.0,
                    timestamp=datetime.now().isoformat()
                )
                patterns.append(pattern)

        return patterns

    def _cluster_by_task(self, spans: List[Span]) -> Dict[str, List[Span]]:
        """Cluster spans by task type using simple keyword extraction"""
        clusters = defaultdict(list)

        # Simple keyword-based clustering
        keywords = ['fix', 'implement', 'refactor', 'test', 'review', 'analyze', 'optimize', 'debug']

        for span in spans:
            task_lower = span.task.lower()
            matched = False
            for kw in keywords:
                if kw in task_lower:
                    clusters[kw].append(span)
                    matched = True
                    break
            if not matched:
                clusters['general'].append(span)

        return clusters

    def _find_common_elements(self, texts: List[str]) -> List[str]:
        """Find common elements/patterns across multiple texts"""
        if not texts:
            return []

        # Simple approach: find common phrases
        # More sophisticated: use embedding similarity

        # Extract key phrases (sentences or lines)
        all_elements = []
        for text in texts:
            if text:
                elements = [line.strip() for line in text.split('\n') if len(line.strip()) > 20]
                all_elements.extend(elements)

        # Count occurrences
        element_counts = defaultdict(int)
        for elem in all_elements:
            # Normalize
            normalized = elem.lower()[:100]
            element_counts[normalized] += 1

        # Return elements that appear in multiple texts
        common = [elem for elem, count in element_counts.items() if count >= 2]
        return common[:10]


# =============================================================================
# AUTOMATIC PROMPT OPTIMIZATION (APO)
# =============================================================================

class PromptOptimizer:
    """
    Automatic Prompt Optimization (APO) algorithm.
    Based on Microsoft's approach: evaluate -> critique -> rewrite.
    """

    BASE_PROMPTS = {
        'coder': """You are a senior software engineer. Your role is to write clean, efficient, and well-tested code.

APPROACH:
1. Understand requirements thoroughly before coding
2. Consider edge cases and error handling
3. Write readable, maintainable code
4. Include appropriate comments and documentation
5. Follow project conventions and style guides

{learned_patterns}

TASK: {task}

{context}""",

        'researcher': """You are a thorough researcher. Your role is to gather, analyze, and synthesize information.

APPROACH:
1. Search multiple authoritative sources
2. Verify information across sources
3. Note uncertainties and conflicting information
4. Provide clear summaries with citations
5. Highlight actionable insights

{learned_patterns}

TASK: {task}

{context}""",

        'reviewer': """You are a code reviewer focused on quality and best practices.

APPROACH:
1. Check for correctness and completeness
2. Identify security vulnerabilities
3. Suggest performance improvements
4. Verify test coverage
5. Ensure code readability

{learned_patterns}

TASK: {task}

{context}""",

        'planner': """You are a strategic planner. Your role is to break down complex tasks into actionable steps.

APPROACH:
1. Understand the end goal
2. Identify dependencies and constraints
3. Create a phased approach
4. Define success criteria
5. Plan for contingencies

{learned_patterns}

TASK: {task}

{context}""",

        'tester': """You are a QA engineer focused on comprehensive testing.

APPROACH:
1. Write tests before implementation (TDD)
2. Cover edge cases and error conditions
3. Include unit, integration, and e2e tests
4. Verify performance requirements
5. Document test scenarios

{learned_patterns}

TASK: {task}

{context}"""
    }

    def __init__(self, store: LightningStore):
        self.store = store
        keys = load_api_keys()
        api_key = keys.get('anthropic', {}).get('api_key')
        if api_key and HAS_ANTHROPIC:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None

    def optimize(self, agent_type: str, critiques: List[Critique]) -> OptimizedPrompt:
        """
        Run APO cycle: evaluate -> critique -> rewrite

        Takes critiques from failed executions and generates an improved prompt.
        """
        # Get current prompt
        current = self.store.get_latest_prompt(agent_type, 'general')
        if current:
            current_prompt = current.prompt_template
            version = current.version + 1
        else:
            current_prompt = self.BASE_PROMPTS.get(agent_type, self.BASE_PROMPTS['coder'])
            version = 1

        # Get learned patterns
        patterns = self.store.get_patterns(agent_type)
        pattern_text = self._format_patterns(patterns)

        if not critiques:
            # No critiques = keep current prompt
            return OptimizedPrompt(
                id=str(uuid.uuid4()),
                agent_type=agent_type,
                task_category='general',
                prompt_template=current_prompt.replace('{learned_patterns}', pattern_text),
                version=version,
                performance_score=0.5,
                training_spans=0,
                timestamp=datetime.now().isoformat()
            )

        # Generate improved prompt using critiques
        if self.client:
            improved_prompt = self._llm_rewrite(current_prompt, critiques, pattern_text)
        else:
            improved_prompt = self._heuristic_rewrite(current_prompt, critiques, pattern_text)

        return OptimizedPrompt(
            id=str(uuid.uuid4()),
            agent_type=agent_type,
            task_category='general',
            prompt_template=improved_prompt,
            version=version,
            performance_score=0.0,  # Will be updated after validation
            training_spans=len(critiques),
            timestamp=datetime.now().isoformat()
        )

    def _format_patterns(self, patterns: List[Pattern]) -> str:
        """Format learned patterns for inclusion in prompts"""
        if not patterns:
            return ""

        lines = ["LEARNED PATTERNS:"]
        for p in patterns[:5]:  # Max 5 patterns
            if p.pattern_type == 'success_pattern':
                lines.append(f"- SUCCESS: {p.description}")
                for action in p.actions[:3]:
                    lines.append(f"  - {action}")
            else:
                lines.append(f"- AVOID: {p.description}")

        return '\n'.join(lines)

    def _llm_rewrite(self, current: str, critiques: List[Critique], patterns: str) -> str:
        """Use LLM to rewrite the prompt based on critiques"""
        critique_summary = '\n'.join([
            f"- {c.critique_text}\n  Suggestions: {', '.join(c.improvement_suggestions)}"
            for c in critiques[:5]
        ])

        prompt = f"""Improve this agent prompt based on the critiques from failed executions.

CURRENT PROMPT:
{current}

CRITIQUES FROM FAILURES:
{critique_summary}

LEARNED PATTERNS:
{patterns}

Generate an improved prompt that:
1. Addresses the issues identified in critiques
2. Incorporates the learned patterns
3. Maintains the same overall structure
4. Adds specific guidance to avoid common failures

OUTPUT THE IMPROVED PROMPT ONLY, no explanations:"""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            print(f"LLM rewrite failed: {e}")
            return self._heuristic_rewrite(current, critiques, patterns)

    def _heuristic_rewrite(self, current: str, critiques: List[Critique], patterns: str) -> str:
        """Fallback heuristic prompt improvement"""
        # Add common suggestions from critiques
        suggestions = []
        for c in critiques:
            suggestions.extend(c.improvement_suggestions)

        unique_suggestions = list(set(suggestions))[:5]

        # Insert suggestions into prompt
        additional = "\n\nBASED ON PAST EXPERIENCES:\n" + '\n'.join([f"- {s}" for s in unique_suggestions])

        # Insert patterns
        current = current.replace('{learned_patterns}', patterns)

        return current + additional


# =============================================================================
# NATS INTEGRATION (Collective Learning)
# =============================================================================

class CollectiveSharer:
    """
    Shares improvements with the 8OWLS collective via NATS.
    Other owl instances can benefit from learned patterns.
    """

    def __init__(self):
        self.nc = None

    async def connect(self):
        """Connect to NATS"""
        if not HAS_NATS:
            return False

        try:
            self.nc = NATS()
            await self.nc.connect(NATS_URL)
            return True
        except Exception as e:
            print(f"NATS connection failed: {e}")
            return False

    async def share_pattern(self, pattern: Pattern):
        """Share a learned pattern with the collective"""
        if not self.nc:
            return

        msg = {
            'type': 'pattern_learned',
            'from': 'AGENT_LIGHTNING',
            'pattern': pattern.to_dict(),
            'ts': datetime.now().isoformat()
        }

        try:
            await self.nc.publish('owl.lightning.patterns', json.dumps(msg).encode())
            await self.nc.flush()
        except Exception as e:
            print(f"Share failed: {e}")

    async def share_prompt(self, prompt: OptimizedPrompt):
        """Share an optimized prompt with the collective"""
        if not self.nc:
            return

        msg = {
            'type': 'prompt_optimized',
            'from': 'AGENT_LIGHTNING',
            'prompt': prompt.to_dict(),
            'ts': datetime.now().isoformat()
        }

        try:
            await self.nc.publish('owl.lightning.prompts', json.dumps(msg).encode())
            await self.nc.flush()
        except Exception as e:
            print(f"Share failed: {e}")

    async def close(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()


# =============================================================================
# MAIN AGENT LIGHTNING CLASS
# =============================================================================

class AgentLightning:
    """
    Main orchestrator for the self-improvement loop.

    This is SEED squared - learning how to learn:
    1. PERCEIVE  - Record spans from agent executions
    2. CONNECT   - Credit assignment (which steps caused success/failure)
    3. LEARN     - Extract patterns from successful executions
    4. QUESTION  - Generate critiques for failures
    5. EXPAND    - Generate improved prompts via APO
    6. SHARE     - Publish improvements to NATS
    7. RECEIVE   - Accept patterns from other instances
    8. IMPROVE   - Meta-learning (optimize this very loop)
    """

    def __init__(self):
        self.store = LightningStore()
        self.credit_assigner = CreditAssigner(self.store)
        self.critique_generator = CritiqueGenerator(self.store)
        self.pattern_learner = PatternLearner(self.store)
        self.prompt_optimizer = PromptOptimizer(self.store)
        self.sharer = CollectiveSharer()
        self.state = self._load_state()

    def _load_state(self) -> Dict:
        """Load system state"""
        if STATE_PATH.exists():
            with open(STATE_PATH) as f:
                return json.load(f)
        return {
            'training_cycles': 0,
            'spans_processed': 0,
            'patterns_learned': 0,
            'prompts_optimized': 0,
            'last_run': None
        }

    def _save_state(self):
        """Save system state"""
        self.state['last_run'] = datetime.now().isoformat()
        with open(STATE_PATH, 'w') as f:
            json.dump(self.state, f, indent=2)

    # -------------------------------------------------------------------------
    # PHASE 1: PERCEIVE - Record execution spans
    # -------------------------------------------------------------------------

    def record_span(
        self,
        agent_type: str,
        task: str,
        input_context: str,
        output: str,
        reward: float,
        success: bool,
        duration_ms: int = 0,
        metadata: Dict = None
    ) -> Span:
        """
        Record an agent execution span.

        Call this from any Claude instance after completing a task:
        - agent_type: coder, researcher, reviewer, etc.
        - task: What the agent was trying to do
        - input_context: The context/prompt given to the agent
        - output: What the agent produced
        - reward: 0.0 (failure) to 1.0 (success)
        - success: Boolean success indicator
        """
        span = Span(
            id=str(uuid.uuid4()),
            agent_type=agent_type,
            task=task,
            input_context=input_context,
            output=output,
            reward=reward,
            success=success,
            timestamp=datetime.now().isoformat(),
            duration_ms=duration_ms,
            parent_span_id=None,
            metadata=metadata or {}
        )

        self.store.store_span(span)
        self.state['spans_processed'] += 1
        self._save_state()

        print(f"[LIGHTNING] Recorded span: {agent_type} - {task[:50]}... (reward: {reward:.2f})")
        return span

    # -------------------------------------------------------------------------
    # PHASE 2-4: ANALYZE - Credit assignment, pattern extraction, critiques
    # -------------------------------------------------------------------------

    def analyze_failures(self, agent_type: Optional[str] = None, limit: int = 20) -> List[Critique]:
        """
        Analyze recent failures and generate critiques.

        PHASES:
        - CONNECT: Credit assignment
        - QUESTION: Critique generation
        """
        failures = self.store.get_failure_spans(agent_type, limit)

        if not failures:
            print("[LIGHTNING] No failures to analyze")
            return []

        print(f"[LIGHTNING] Analyzing {len(failures)} failures...")

        critiques = []
        for span in failures:
            critique = self.critique_generator.generate_critique(span)
            self.store.store_critique(critique)
            critiques.append(critique)
            print(f"  - Critiqued: {span.task[:40]}...")

        return critiques

    def learn_patterns(self, days: int = 7) -> List[Pattern]:
        """
        Extract patterns from recent executions.

        PHASE: LEARN - Extract patterns from successful executions
        """
        since = datetime.now() - timedelta(days=days)
        spans = self.store.get_spans(since=since, limit=1000)

        if not spans:
            print("[LIGHTNING] No spans to learn from")
            return []

        print(f"[LIGHTNING] Learning from {len(spans)} spans...")

        patterns = self.pattern_learner.extract_patterns(spans)

        for pattern in patterns:
            self.store.store_pattern(pattern)
            self.state['patterns_learned'] += 1
            print(f"  - Learned pattern: {pattern.description[:50]}...")

        self._save_state()
        return patterns

    # -------------------------------------------------------------------------
    # PHASE 5: EXPAND - Generate improved prompts
    # -------------------------------------------------------------------------

    def optimize_prompts(self, agent_type: Optional[str] = None) -> List[OptimizedPrompt]:
        """
        Run APO to generate improved prompts.

        PHASE: EXPAND - Generate improved prompts via APO
        """
        # Get agent types to optimize
        if agent_type:
            agent_types = [agent_type]
        else:
            # Get all agent types with failures
            failures = self.store.get_failure_spans(limit=100)
            agent_types = list(set(s.agent_type for s in failures))

        if not agent_types:
            print("[LIGHTNING] No agent types to optimize")
            return []

        optimized = []
        for at in agent_types:
            # Get critiques for this agent type
            failures = self.store.get_failure_spans(at, limit=20)
            critiques = []
            for span in failures:
                c = self.critique_generator.generate_critique(span)
                critiques.append(c)

            # Optimize prompt
            prompt = self.prompt_optimizer.optimize(at, critiques)
            self.store.store_prompt(prompt)
            optimized.append(prompt)

            self.state['prompts_optimized'] += 1
            print(f"  - Optimized prompt for: {at} (v{prompt.version})")

        self._save_state()
        return optimized

    # -------------------------------------------------------------------------
    # PHASE 6-7: SHARE/RECEIVE - Collective learning
    # -------------------------------------------------------------------------

    async def share_improvements(self, patterns: List[Pattern], prompts: List[OptimizedPrompt]):
        """
        Share learned improvements with the collective.

        PHASES: SHARE + RECEIVE
        """
        await self.sharer.connect()

        for pattern in patterns:
            await self.sharer.share_pattern(pattern)

        for prompt in prompts:
            await self.sharer.share_prompt(prompt)

        await self.sharer.close()
        print(f"[LIGHTNING] Shared {len(patterns)} patterns, {len(prompts)} prompts")

    # -------------------------------------------------------------------------
    # PHASE 8: IMPROVE - Full training cycle
    # -------------------------------------------------------------------------

    def train(self, share: bool = True):
        """
        Run a full training cycle.

        PHASE: IMPROVE - Meta-learning loop
        """
        print("\n" + "="*60)
        print("AGENT LIGHTNING - TRAINING CYCLE")
        print("="*60 + "\n")

        self.state['training_cycles'] += 1

        # 1. Analyze failures
        print("[1/4] Analyzing failures...")
        critiques = self.analyze_failures()
        print(f"      Generated {len(critiques)} critiques\n")

        # 2. Learn patterns
        print("[2/4] Learning patterns...")
        patterns = self.learn_patterns()
        print(f"      Extracted {len(patterns)} patterns\n")

        # 3. Optimize prompts
        print("[3/4] Optimizing prompts...")
        prompts = self.optimize_prompts()
        print(f"      Optimized {len(prompts)} prompts\n")

        # 4. Share with collective
        if share and (patterns or prompts):
            print("[4/4] Sharing with collective...")
            asyncio.run(self.share_improvements(patterns, prompts))
        else:
            print("[4/4] Skipping share (no improvements or sharing disabled)")

        self._save_state()

        # Print summary
        stats = self.store.get_stats()
        print("\n" + "="*60)
        print("TRAINING COMPLETE")
        print("="*60)
        print(f"Total spans: {stats['total_spans']}")
        print(f"Success rate: {stats['success_rate']*100:.1f}%")
        print(f"Patterns learned: {stats['total_patterns']}")
        print(f"Training cycles: {self.state['training_cycles']}")
        print("="*60 + "\n")

    # -------------------------------------------------------------------------
    # GET OPTIMIZED PROMPT
    # -------------------------------------------------------------------------

    def get_prompt(self, agent_type: str, task: str = '', context: str = '') -> str:
        """
        Get the optimized prompt for an agent type.

        Use this when spawning agents to give them the best prompt we've learned.
        """
        prompt_obj = self.store.get_latest_prompt(agent_type, 'general')

        if prompt_obj:
            template = prompt_obj.prompt_template
        else:
            # Use base prompt
            template = PromptOptimizer.BASE_PROMPTS.get(
                agent_type,
                PromptOptimizer.BASE_PROMPTS['coder']
            )

        # Get patterns
        patterns = self.store.get_patterns(agent_type)
        pattern_text = self.prompt_optimizer._format_patterns(patterns)

        # Fill in template
        return template.format(
            task=task,
            context=context,
            learned_patterns=pattern_text
        )

    # -------------------------------------------------------------------------
    # DAEMON MODE
    # -------------------------------------------------------------------------

    def run_daemon(self, interval_minutes: int = 30):
        """
        Run as a daemon, continuously learning.
        """
        print("\n" + "="*60)
        print("AGENT LIGHTNING DAEMON")
        print(f"Training every {interval_minutes} minutes")
        print("="*60 + "\n")

        while True:
            try:
                self.train(share=True)
                print(f"\nNext training in {interval_minutes} minutes...\n")
                import time
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n[LIGHTNING] Daemon stopped")
                break
            except Exception as e:
                print(f"[LIGHTNING] Error: {e}")
                import time
                time.sleep(60)

    # -------------------------------------------------------------------------
    # STATUS
    # -------------------------------------------------------------------------

    def status(self):
        """Print system status"""
        stats = self.store.get_stats()
        state = self.state

        print("\n" + "="*60)
        print("AGENT LIGHTNING STATUS")
        print("="*60)
        print(f"\nSpans:")
        print(f"  Total: {stats['total_spans']}")
        print(f"  Successes: {stats['success_spans']}")
        print(f"  Failures: {stats['failure_spans']}")
        print(f"  Success rate: {stats['success_rate']*100:.1f}%")
        print(f"\nBy agent type:")
        for agent, count in stats.get('spans_by_agent', {}).items():
            print(f"  {agent}: {count}")
        print(f"\nLearning:")
        print(f"  Critiques generated: {stats['total_critiques']}")
        print(f"  Patterns learned: {stats['total_patterns']}")
        print(f"  Training cycles: {state['training_cycles']}")
        print(f"  Last run: {state.get('last_run', 'never')}")
        print("="*60 + "\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Agent Lightning - Self-improvement for 8OWLS')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # record command
    record_parser = subparsers.add_parser('record', help='Record an agent execution span')
    record_parser.add_argument('--agent', '-a', required=True, help='Agent type (coder, researcher, etc.)')
    record_parser.add_argument('--task', '-t', required=True, help='Task description')
    record_parser.add_argument('--success', '-s', type=lambda x: x.lower() == 'true', default=True, help='Success (true/false)')
    record_parser.add_argument('--reward', '-r', type=float, default=1.0, help='Reward (0.0-1.0)')
    record_parser.add_argument('--input', '-i', default='', help='Input context')
    record_parser.add_argument('--output', '-o', default='', help='Output')

    # analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze failures and generate critiques')
    analyze_parser.add_argument('--agent', '-a', help='Filter by agent type')

    # train command
    train_parser = subparsers.add_parser('train', help='Run full training cycle')
    train_parser.add_argument('--no-share', action='store_true', help='Skip sharing to collective')

    # prompt command
    prompt_parser = subparsers.add_parser('prompt', help='Get optimized prompt')
    prompt_parser.add_argument('--agent', '-a', required=True, help='Agent type')
    prompt_parser.add_argument('--task', '-t', default='', help='Task description')

    # daemon command
    daemon_parser = subparsers.add_parser('daemon', help='Run as daemon')
    daemon_parser.add_argument('--interval', '-i', type=int, default=30, help='Training interval (minutes)')

    # status command
    subparsers.add_parser('status', help='Show system status')

    args = parser.parse_args()

    lightning = AgentLightning()

    if args.command == 'record':
        lightning.record_span(
            agent_type=args.agent,
            task=args.task,
            input_context=args.input,
            output=args.output,
            reward=args.reward,
            success=args.success
        )

    elif args.command == 'analyze':
        critiques = lightning.analyze_failures(args.agent)
        for c in critiques:
            print(f"\n{c.critique_text}")
            print("Suggestions:", ', '.join(c.improvement_suggestions))

    elif args.command == 'train':
        lightning.train(share=not args.no_share)

    elif args.command == 'prompt':
        prompt = lightning.get_prompt(args.agent, args.task)
        print(prompt)

    elif args.command == 'daemon':
        lightning.run_daemon(args.interval)

    elif args.command == 'status':
        lightning.status()

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
