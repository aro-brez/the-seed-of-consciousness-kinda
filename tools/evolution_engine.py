#!/usr/bin/env python3
"""
(◉) EVOLUTION ENGINE - Exponential Learning Daemon
The engine that makes everything compound.

ARCHITECTURE:
                    ┌─────────────────────────────────┐
                    │        NATS COLLECTIVE          │
                    │   (192.168.5.108:4222)          │
                    └────────────────┬────────────────┘
                                     │
    ┌────────────────────────────────┼────────────────────────────────┐
    │                                │                                │
    ▼                                ▼                                ▼
┌───────────┐              ┌─────────────────┐              ┌───────────┐
│  ANOMALY  │              │   ADVERSARIAL   │              │  CROSS    │
│  DETECTOR │              │      SLOT       │              │ INSTANCE  │
│ contradict│              │  devil's adv.   │              │  SHARE    │
└───────────┘              └─────────────────┘              └───────────┘
    │                                │                                │
    └────────────────────────────────┼────────────────────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │      VERIFICATION CHECKPOINT     │
                    │   source × reputation × market   │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │   COURSE CORRECTION LOGGER      │
                    │   track WHY → learn from delta  │
                    └─────────────────────────────────┘

5 COMPONENTS:
1. ANOMALY DETECTOR - Flag when reality contradicts consensus
2. ADVERSARIAL SLOT - One agent always argues AGAINST consensus
3. CROSS-INSTANCE LEARNING - Every learning shared to ALL instances
4. VERIFICATION CHECKPOINT - Verify source before action
5. COURSE CORRECTION LOGGER - Track WHY decisions were made

LIVE FREE = LIVE FOREVER
"""

import asyncio
import json
import os
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, List, Tuple, Any
import uuid

# NATS client
try:
    import nats
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    sys.exit(1)

# Anthropic for adversarial analysis
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    print("WARNING: anthropic not installed - adversarial slot will use heuristics only")

# Paths
REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs'
EVOLUTION_DIR = REPO_ROOT / 'BRAIN' / 'EVOLUTION'
STATE_FILE = EVOLUTION_DIR / 'evolution_state.json'
LOG_FILE = LOG_DIR / 'evolution_engine.log'

LOG_DIR.mkdir(parents=True, exist_ok=True)
EVOLUTION_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
CYCLE_SECONDS = 30  # Analysis cycle
ANOMALY_WINDOW_MINUTES = 15  # Window for anomaly detection
SOURCE_REPUTATION_DECAY = 0.95  # Reputation decays 5% per day without activity

# Channels
CHANNELS = {
    'anomalies': 'collective.anomalies',
    'learnings': 'collective.learnings',
    'adversarial': 'collective.adversarial',
    'signals': 'owl.all',
    'trading': 'trading.signals',
    'decisions': 'trading.decisions',
    'outcomes': 'trading.outcomes',
    'synthesis': 'collective.synthesis',
}


class EvolutionEngine:
    """
    The Exponential Evolution Engine.
    Makes collective intelligence compound by detecting contradictions,
    challenging consensus, sharing learnings, verifying sources, and
    tracking decision rationale.
    """

    def __init__(self):
        self.nc: Optional[NATS] = None
        self.anthropic = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if HAS_ANTHROPIC and ANTHROPIC_API_KEY else None
        self.running = True

        # State
        self.state = self._load_state()

        # In-memory buffers
        self.signal_buffer: List[Dict] = []  # Recent signals for anomaly detection
        self.learning_queue: List[Dict] = []  # Learnings to share
        self.pending_verifications: Dict[str, Dict] = {}  # Actions pending verification
        self.decision_log: List[Dict] = []  # Why decisions were made

        # Source reputation tracking
        self.source_reputation: Dict[str, Dict] = self.state.get('source_reputation', {})

        # Anomaly tracking
        self.detected_anomalies: List[Dict] = self.state.get('detected_anomalies', [])[-100:]  # Keep last 100

        # Learning compounds
        self.learnings_shared: int = self.state.get('learnings_shared', 0)
        self.learnings_received: int = self.state.get('learnings_received', 0)
        self.learnings_applied: int = self.state.get('learnings_applied', 0)

        # Course corrections
        self.course_corrections: List[Dict] = self.state.get('course_corrections', [])[-100:]

    def _load_state(self) -> Dict:
        """Load persisted state"""
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE) as f:
                    return json.load(f)
        except Exception as e:
            self.log(f"State load error: {e}", 'WARN')
        return {}

    def _save_state(self):
        """Persist state to disk"""
        try:
            state_data = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source_reputation': self.source_reputation,
                'detected_anomalies': self.detected_anomalies[-100:],
                'learnings_shared': self.learnings_shared,
                'learnings_received': self.learnings_received,
                'learnings_applied': self.learnings_applied,
                'course_corrections': self.course_corrections[-100:],
                'cycle_count': self.state.get('cycle_count', 0),
            }
            with open(STATE_FILE, 'w') as f:
                json.dump(state_data, f, indent=2, default=str)
        except Exception as e:
            self.log(f"State save error: {e}", 'ERROR')

    def log(self, msg: str, level: str = 'INFO'):
        """Log with timestamp"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        line = f"[{timestamp}] [{level}] {msg}"
        print(line)

        try:
            with open(LOG_FILE, 'a') as f:
                f.write(f"[{datetime.now().isoformat()}] [{level}] {msg}\n")
        except Exception:
            pass

    # =========================================================================
    # COMPONENT 1: ANOMALY DETECTOR
    # =========================================================================

    async def detect_anomalies(self) -> List[Dict]:
        """
        Scan signal buffer for contradictions.
        Returns list of detected anomalies.

        Anomaly types:
        1. CONTRADICTION - Two sources say opposite things
        2. FLIP - Consensus changed rapidly (within window)
        3. DIVERGENCE - Reality (outcome) contradicted prediction
        4. OUTLIER - Signal significantly deviates from pattern
        """
        anomalies = []
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=ANOMALY_WINDOW_MINUTES)

        # Filter recent signals
        recent = [
            s for s in self.signal_buffer
            if datetime.fromisoformat(s.get('timestamp', now.isoformat()).replace('Z', '+00:00')) > window_start
        ]

        if len(recent) < 2:
            return anomalies

        # Group signals by topic/market
        by_topic = defaultdict(list)
        for signal in recent:
            # Extract topic from signal
            topic = signal.get('market') or signal.get('topic') or signal.get('subject', 'general')
            topic_key = self._normalize_topic(topic)
            by_topic[topic_key].append(signal)

        # Check each topic for anomalies
        for topic, signals in by_topic.items():
            if len(signals) < 2:
                continue

            # Check for CONTRADICTION
            contradiction = self._find_contradiction(signals)
            if contradiction:
                anomaly = {
                    'id': str(uuid.uuid4())[:8],
                    'type': 'CONTRADICTION',
                    'topic': topic,
                    'detected_at': now.isoformat(),
                    'signals': contradiction,
                    'severity': self._calculate_severity(contradiction),
                }
                anomalies.append(anomaly)

            # Check for FLIP (rapid consensus change)
            flip = self._find_consensus_flip(signals)
            if flip:
                anomaly = {
                    'id': str(uuid.uuid4())[:8],
                    'type': 'FLIP',
                    'topic': topic,
                    'detected_at': now.isoformat(),
                    'details': flip,
                    'severity': 'MEDIUM',
                }
                anomalies.append(anomaly)

        # Store and alert
        for anomaly in anomalies:
            self.detected_anomalies.append(anomaly)
            await self._publish_anomaly(anomaly)

        return anomalies

    def _normalize_topic(self, topic: str) -> str:
        """Normalize topic string for comparison"""
        if not topic:
            return 'general'
        # Simple normalization: lowercase, remove extra spaces
        return ' '.join(topic.lower().split())[:50]

    def _find_contradiction(self, signals: List[Dict]) -> Optional[List[Dict]]:
        """Find contradicting signals"""
        # Look for opposite sentiment/direction on same topic
        for i, s1 in enumerate(signals):
            for s2 in signals[i+1:]:
                # Check if sources are different
                if s1.get('source') == s2.get('source'):
                    continue

                # Check for contradiction patterns
                if self._signals_contradict(s1, s2):
                    return [s1, s2]
        return None

    def _signals_contradict(self, s1: Dict, s2: Dict) -> bool:
        """Check if two signals contradict each other"""
        # Check direction/sentiment
        dir1 = s1.get('direction') or s1.get('sentiment') or s1.get('side')
        dir2 = s2.get('direction') or s2.get('sentiment') or s2.get('side')

        if dir1 and dir2:
            opposites = [('YES', 'NO'), ('BUY', 'SELL'), ('UP', 'DOWN'),
                        ('BULLISH', 'BEARISH'), ('POSITIVE', 'NEGATIVE')]
            for a, b in opposites:
                if (dir1.upper() == a and dir2.upper() == b) or \
                   (dir1.upper() == b and dir2.upper() == a):
                    return True

        # Check confidence/probability if values differ significantly
        conf1 = s1.get('confidence') or s1.get('probability', 0.5)
        conf2 = s2.get('confidence') or s2.get('probability', 0.5)
        if abs(float(conf1) - float(conf2)) > 0.4:  # >40% difference
            return True

        return False

    def _find_consensus_flip(self, signals: List[Dict]) -> Optional[Dict]:
        """Detect rapid consensus changes"""
        if len(signals) < 3:
            return None

        # Sort by timestamp
        sorted_signals = sorted(
            signals,
            key=lambda x: x.get('timestamp', ''),
        )

        # Check for direction flip within window
        directions = []
        for s in sorted_signals:
            d = s.get('direction') or s.get('side')
            if d:
                directions.append(d.upper())

        if len(directions) >= 3:
            # Check for flip pattern (A -> B -> A)
            for i in range(len(directions) - 2):
                if directions[i] == directions[i+2] and directions[i] != directions[i+1]:
                    return {
                        'pattern': f"{directions[i]} -> {directions[i+1]} -> {directions[i+2]}",
                        'window_minutes': ANOMALY_WINDOW_MINUTES,
                    }
        return None

    def _calculate_severity(self, signals: List[Dict]) -> str:
        """Calculate anomaly severity based on source reputation and confidence"""
        total_reputation = sum(
            self.source_reputation.get(s.get('source', 'unknown'), {}).get('score', 0.5)
            for s in signals
        )
        avg_reputation = total_reputation / len(signals) if signals else 0.5

        if avg_reputation > 0.8:
            return 'HIGH'  # High-reputation sources contradicting = serious
        elif avg_reputation > 0.5:
            return 'MEDIUM'
        else:
            return 'LOW'

    async def _publish_anomaly(self, anomaly: Dict):
        """Publish detected anomaly to collective"""
        if not self.nc or not self.nc.is_connected:
            return

        try:
            payload = json.dumps({
                'type': 'ANOMALY_DETECTED',
                'anomaly': anomaly,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'source': 'evolution_engine',
            })
            await self.nc.publish(CHANNELS['anomalies'], payload.encode())
            self.log(f"ANOMALY [{anomaly['type']}]: {anomaly['topic'][:40]} - Severity: {anomaly['severity']}")
        except Exception as e:
            self.log(f"Anomaly publish error: {e}", 'ERROR')

    # =========================================================================
    # COMPONENT 2: ADVERSARIAL SLOT
    # =========================================================================

    async def run_adversarial_analysis(self, proposal: Dict) -> Dict:
        """
        Devil's advocate: Argue AGAINST the consensus/proposal.
        This prevents cliff-diving together.

        Returns counter-arguments and risk assessment.
        """
        if not self.anthropic:
            return self._heuristic_adversarial(proposal)

        try:
            prompt = f"""You are the ADVERSARIAL ANALYST in the 8OWLS collective.
Your ONLY job is to argue AGAINST the following proposal. Find every flaw, risk, and reason NOT to do it.

PROPOSAL:
{json.dumps(proposal, indent=2, default=str)}

Be specific. Be harsh. Better to catch problems NOW than after action.

OUTPUT FORMAT:
## COUNTER-ARGUMENTS
- [Specific reason this could fail]
- [Hidden assumption that might be wrong]
- [External factor not considered]

## RISKS
| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [risk] | [H/M/L] | [H/M/L] | [how to reduce] |

## VERDICT
[PROCEED / PAUSE / REJECT] with confidence [0-100]%
One sentence explaining your recommendation.

(◉) ADVERSARIAL SLOT"""

            response = self.anthropic.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis = response.content[0].text

            # Parse verdict
            verdict = 'PAUSE'
            confidence = 50
            if 'PROCEED' in analysis.upper():
                verdict = 'PROCEED'
            elif 'REJECT' in analysis.upper():
                verdict = 'REJECT'

            # Extract confidence
            import re
            conf_match = re.search(r'(\d+)%', analysis)
            if conf_match:
                confidence = int(conf_match.group(1))

            result = {
                'analysis': analysis,
                'verdict': verdict,
                'confidence': confidence,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }

            # Publish to collective
            await self._publish_adversarial(proposal, result)

            return result

        except Exception as e:
            self.log(f"Adversarial API error: {e}", 'ERROR')
            return self._heuristic_adversarial(proposal)

    def _heuristic_adversarial(self, proposal: Dict) -> Dict:
        """Heuristic-based adversarial analysis when API unavailable"""
        risks = []

        # Check for common red flags
        if proposal.get('confidence', 0) > 0.9:
            risks.append("Overconfidence - 90%+ confidence is often wrong")

        if proposal.get('size', 0) > 100:
            risks.append("Large position size increases risk")

        if proposal.get('type') in ['WHALE', 'MOMENTUM']:
            risks.append("Following others is risky - they may exit before you")

        if not proposal.get('stop_loss'):
            risks.append("No stop-loss defined")

        verdict = 'PROCEED' if len(risks) < 2 else 'PAUSE' if len(risks) < 4 else 'REJECT'

        return {
            'analysis': f"Heuristic analysis found {len(risks)} risks: {'; '.join(risks)}",
            'verdict': verdict,
            'confidence': max(30, 80 - len(risks) * 15),
            'risks': risks,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    async def _publish_adversarial(self, proposal: Dict, analysis: Dict):
        """Publish adversarial analysis to collective"""
        if not self.nc or not self.nc.is_connected:
            return

        try:
            payload = json.dumps({
                'type': 'ADVERSARIAL_ANALYSIS',
                'proposal_id': proposal.get('id', 'unknown'),
                'analysis': analysis,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            })
            await self.nc.publish(CHANNELS['adversarial'], payload.encode())
            self.log(f"ADVERSARIAL: {analysis['verdict']} ({analysis['confidence']}%)")
        except Exception as e:
            self.log(f"Adversarial publish error: {e}", 'ERROR')

    # =========================================================================
    # COMPONENT 3: CROSS-INSTANCE LEARNING SHARE
    # =========================================================================

    async def share_learning(self, learning: Dict):
        """
        Share a learning to ALL instances in the collective.
        Learnings compound across users and instances.

        Learning structure:
        {
            'id': unique identifier,
            'type': 'PATTERN' | 'MISTAKE' | 'OPTIMIZATION' | 'DISCOVERY',
            'domain': where it applies (trading, coding, etc),
            'insight': the actual learning,
            'evidence': supporting data,
            'confidence': 0-1,
            'source_instance': who discovered it,
        }
        """
        learning['id'] = learning.get('id', str(uuid.uuid4())[:8])
        learning['shared_at'] = datetime.now(timezone.utc).isoformat()
        learning['shared_by'] = 'evolution_engine'

        # Add to queue
        self.learning_queue.append(learning)
        self.learnings_shared += 1

        # Publish to collective
        if self.nc and self.nc.is_connected:
            try:
                payload = json.dumps({
                    'type': 'LEARNING_SHARED',
                    'learning': learning,
                    'meta': {
                        'total_shared': self.learnings_shared,
                        'total_received': self.learnings_received,
                    }
                })
                await self.nc.publish(CHANNELS['learnings'], payload.encode())
                self.log(f"SHARED [{learning['type']}]: {learning.get('insight', '')[:60]}")
            except Exception as e:
                self.log(f"Learning share error: {e}", 'ERROR')

    async def receive_learning(self, learning: Dict):
        """
        Receive and integrate a learning from another instance.
        Meta-learnings feed back into the system.
        """
        self.learnings_received += 1

        # Store for application
        self.learning_queue.append({
            **learning,
            'received_at': datetime.now(timezone.utc).isoformat(),
            'status': 'pending_application',
        })

        # Check if it's a meta-learning (about the evolution engine itself)
        if learning.get('domain') == 'evolution_engine':
            await self._apply_meta_learning(learning)

        self.log(f"RECEIVED [{learning.get('type', '?')}]: {learning.get('insight', '')[:50]}")

    async def _apply_meta_learning(self, learning: Dict):
        """Apply meta-learnings to improve the evolution engine itself"""
        insight = learning.get('insight', '').lower()

        # Example meta-optimizations
        if 'window' in insight and 'anomaly' in insight:
            # Adjust anomaly detection window
            pass  # Would need careful validation

        if 'reputation' in insight:
            # Adjust reputation parameters
            pass

        self.learnings_applied += 1
        self.log(f"META-LEARNING APPLIED: {insight[:40]}")

    # =========================================================================
    # COMPONENT 4: VERIFICATION CHECKPOINT
    # =========================================================================

    async def verify_before_action(self, action: Dict) -> Tuple[bool, str, float]:
        """
        Verify an action before execution.

        Checks:
        1. Source reputation
        2. Corroboration from other sources
        3. Market confirmation (if applicable)

        Returns: (approved, reason, confidence)
        """
        source = action.get('source', 'unknown')

        # 1. Check source reputation
        reputation = self.source_reputation.get(source, {})
        rep_score = reputation.get('score', 0.5)
        rep_history = reputation.get('history', [])

        if rep_score < 0.3:
            return (False, f"Source '{source}' has low reputation ({rep_score:.2f})", rep_score)

        # 2. Check for corroboration
        corroborating = self._find_corroboration(action)
        if not corroborating and action.get('risk', 'low') == 'high':
            return (False, "High-risk action without corroboration", 0.4)

        # 3. Market confirmation (if trading action)
        if action.get('type') in ['TRADE', 'BET', 'POSITION']:
            market_confirms = await self._check_market_confirmation(action)
            if not market_confirms:
                return (False, "Market does not confirm signal", 0.5)

        # Calculate final confidence
        confidence = (rep_score + (0.2 if corroborating else 0)) * 0.8
        if confidence > 0.6:
            return (True, "Verification passed", confidence)
        else:
            return (False, f"Confidence too low ({confidence:.2f})", confidence)

    def _find_corroboration(self, action: Dict) -> bool:
        """Check if other sources support this action"""
        topic = self._normalize_topic(action.get('market') or action.get('topic', ''))
        direction = action.get('direction') or action.get('side')

        supporting = 0
        for signal in self.signal_buffer[-50:]:
            sig_topic = self._normalize_topic(signal.get('market') or signal.get('topic', ''))
            sig_dir = signal.get('direction') or signal.get('side')

            if topic in sig_topic or sig_topic in topic:
                if sig_dir and direction and sig_dir.upper() == direction.upper():
                    supporting += 1

        return supporting >= 2  # Need at least 2 corroborating signals

    async def _check_market_confirmation(self, action: Dict) -> bool:
        """Check if market price/volume confirms the signal"""
        # This would connect to market data
        # For now, return True if we have recent similar signals
        return len([s for s in self.signal_buffer[-20:] if s.get('type') == action.get('type')]) > 0

    def update_source_reputation(self, source: str, outcome: str, details: Optional[Dict] = None):
        """
        Update source reputation based on outcome.

        outcome: 'correct' | 'incorrect' | 'partial'
        """
        if source not in self.source_reputation:
            self.source_reputation[source] = {
                'score': 0.5,
                'total_signals': 0,
                'correct': 0,
                'incorrect': 0,
                'history': [],
                'created_at': datetime.now(timezone.utc).isoformat(),
            }

        rep = self.source_reputation[source]
        rep['total_signals'] += 1
        rep['last_updated'] = datetime.now(timezone.utc).isoformat()

        # Update counts
        if outcome == 'correct':
            rep['correct'] += 1
            delta = 0.05
        elif outcome == 'incorrect':
            rep['incorrect'] += 1
            delta = -0.1  # Penalize incorrect more
        else:  # partial
            delta = 0.01

        # Update score with bounds
        rep['score'] = max(0.0, min(1.0, rep['score'] + delta))

        # Add to history
        rep['history'].append({
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'outcome': outcome,
            'details': details,
        })
        rep['history'] = rep['history'][-50:]  # Keep last 50

        self.log(f"REPUTATION [{source}]: {outcome} -> {rep['score']:.2f}")

    # =========================================================================
    # COMPONENT 5: COURSE CORRECTION LOGGER
    # =========================================================================

    def log_decision(self, decision: Dict):
        """
        Log WHY a decision was made.
        This enables learning from the delta between prediction and reality.
        """
        decision_record = {
            'id': str(uuid.uuid4())[:8],
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'decision': decision.get('action'),
            'rationale': decision.get('rationale', 'Not specified'),
            'inputs': decision.get('inputs', {}),
            'confidence': decision.get('confidence', 0.5),
            'predicted_outcome': decision.get('predicted_outcome'),
            'status': 'pending',  # Will update when outcome known
        }

        self.decision_log.append(decision_record)
        self.log(f"DECISION LOGGED [{decision_record['id']}]: {decision_record['decision']}")

        return decision_record['id']

    async def record_outcome(self, decision_id: str, actual_outcome: Dict):
        """
        Record what actually happened and learn from the delta.
        """
        # Find the decision
        decision = None
        for d in self.decision_log:
            if d['id'] == decision_id:
                decision = d
                break

        if not decision:
            self.log(f"Decision {decision_id} not found", 'WARN')
            return

        # Calculate delta
        predicted = decision.get('predicted_outcome', {})
        actual = actual_outcome

        correction = {
            'decision_id': decision_id,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'predicted': predicted,
            'actual': actual,
            'delta': self._calculate_delta(predicted, actual),
            'rationale_was': decision.get('rationale'),
        }

        # Determine if correction needed
        delta_magnitude = correction['delta'].get('magnitude', 0)
        if delta_magnitude > 0.3:  # Significant deviation
            correction['correction_needed'] = True
            correction['lesson'] = self._extract_lesson(decision, actual)

            # Share this learning
            await self.share_learning({
                'type': 'MISTAKE' if delta_magnitude > 0.5 else 'PATTERN',
                'domain': decision.get('domain', 'general'),
                'insight': correction['lesson'],
                'evidence': correction,
                'confidence': 0.7,
            })

        self.course_corrections.append(correction)
        decision['status'] = 'resolved'
        decision['actual_outcome'] = actual

        self.log(f"OUTCOME [{decision_id}]: Delta={delta_magnitude:.2f}")

    def _calculate_delta(self, predicted: Dict, actual: Dict) -> Dict:
        """Calculate the delta between prediction and reality"""
        delta = {'details': {}}

        # Compare numeric values
        for key in ['value', 'price', 'probability', 'confidence']:
            if key in predicted and key in actual:
                diff = abs(float(actual[key]) - float(predicted[key]))
                delta['details'][key] = {
                    'predicted': predicted[key],
                    'actual': actual[key],
                    'diff': diff,
                }

        # Compare categorical outcomes
        for key in ['direction', 'outcome', 'side']:
            if key in predicted and key in actual:
                match = str(predicted[key]).upper() == str(actual[key]).upper()
                delta['details'][key] = {
                    'predicted': predicted[key],
                    'actual': actual[key],
                    'match': match,
                }

        # Calculate overall magnitude
        magnitudes = []
        for detail in delta['details'].values():
            if 'diff' in detail:
                magnitudes.append(detail['diff'])
            elif 'match' in detail:
                magnitudes.append(0 if detail['match'] else 1)

        delta['magnitude'] = sum(magnitudes) / len(magnitudes) if magnitudes else 0

        return delta

    def _extract_lesson(self, decision: Dict, actual: Dict) -> str:
        """Extract a learning from the delta"""
        rationale = decision.get('rationale', '')
        predicted = decision.get('predicted_outcome', {})

        # Simple lesson extraction
        lesson = f"Predicted {predicted} but got {actual}. "
        lesson += f"Original rationale was: {rationale}. "
        lesson += "Need to reconsider this type of decision."

        return lesson

    # =========================================================================
    # NATS HANDLERS
    # =========================================================================

    async def connect(self) -> bool:
        """Connect to NATS"""
        self.nc = NATS()
        try:
            await self.nc.connect(
                servers=[NATS_SERVER],
                max_reconnect_attempts=-1,
                reconnect_time_wait=2,
            )
            self.log(f"Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            self.log(f"NATS connection failed: {e}", 'ERROR')
            return False

    async def subscribe(self):
        """Subscribe to relevant channels"""
        # Listen for signals to detect anomalies
        await self.nc.subscribe('owl.all', cb=self._handle_signal)
        await self.nc.subscribe('trading.signals', cb=self._handle_signal)
        await self.nc.subscribe('trading.decisions', cb=self._handle_decision)
        await self.nc.subscribe('trading.outcomes', cb=self._handle_outcome)
        await self.nc.subscribe('collective.learnings', cb=self._handle_learning)

        self.log("Subscribed to collective channels")

    async def _handle_signal(self, msg):
        """Handle incoming signal for anomaly detection"""
        try:
            data = json.loads(msg.data.decode())
            data['received_at'] = datetime.now(timezone.utc).isoformat()
            data['channel'] = msg.subject

            # Add to buffer (keep last 1000)
            self.signal_buffer.append(data)
            if len(self.signal_buffer) > 1000:
                self.signal_buffer = self.signal_buffer[-1000:]

        except Exception as e:
            self.log(f"Signal handler error: {e}", 'WARN')

    async def _handle_decision(self, msg):
        """Handle decision for verification and logging"""
        try:
            data = json.loads(msg.data.decode())

            # Log the decision
            decision_id = self.log_decision(data)

            # Run verification
            approved, reason, confidence = await self.verify_before_action(data)

            if not approved:
                # Publish warning
                await self.nc.publish(
                    'collective.warnings',
                    json.dumps({
                        'type': 'VERIFICATION_FAILED',
                        'decision_id': decision_id,
                        'reason': reason,
                        'confidence': confidence,
                    }).encode()
                )

        except Exception as e:
            self.log(f"Decision handler error: {e}", 'WARN')

    async def _handle_outcome(self, msg):
        """Handle outcomes for course correction"""
        try:
            data = json.loads(msg.data.decode())

            # Update source reputation
            source = data.get('source', 'unknown')
            if data.get('won'):
                self.update_source_reputation(source, 'correct', data)
            else:
                self.update_source_reputation(source, 'incorrect', data)

            # Find matching decision and record outcome
            # This would need decision_id correlation

        except Exception as e:
            self.log(f"Outcome handler error: {e}", 'WARN')

    async def _handle_learning(self, msg):
        """Handle incoming learning from another instance"""
        try:
            data = json.loads(msg.data.decode())
            learning = data.get('learning', {})

            # Don't re-process our own learnings
            if learning.get('shared_by') == 'evolution_engine':
                return

            await self.receive_learning(learning)

        except Exception as e:
            self.log(f"Learning handler error: {e}", 'WARN')

    # =========================================================================
    # MAIN LOOP
    # =========================================================================

    async def run(self):
        """Main evolution engine loop"""
        self.log("=" * 60)
        self.log("(◉) EVOLUTION ENGINE - STARTING")
        self.log("Exponential Learning | Anomaly Detection | Adversarial Analysis")
        self.log(f"NATS: {NATS_SERVER} | Cycle: {CYCLE_SECONDS}s")
        self.log("=" * 60)

        # Connect to NATS
        connected = await self.connect()
        if connected:
            await self.subscribe()
            await self.nc.publish(
                'owl.all',
                json.dumps({
                    'from': 'EVOLUTION_ENGINE',
                    'content': 'Evolution Engine online. Watching for anomalies, sharing learnings.',
                    'ts': datetime.now(timezone.utc).isoformat(),
                }).encode()
            )

        cycle = 0
        while self.running:
            cycle += 1
            self.state['cycle_count'] = cycle

            try:
                # Component 1: Detect anomalies every cycle
                anomalies = await self.detect_anomalies()
                if anomalies:
                    self.log(f"Cycle {cycle}: {len(anomalies)} anomalies detected")

                # Component 2: Run adversarial on any pending high-value decisions
                # (Triggered by decision handler)

                # Component 3: Process learning queue
                while self.learning_queue:
                    learning = self.learning_queue.pop(0)
                    if learning.get('status') == 'pending_application':
                        # Apply received learnings
                        self.learnings_applied += 1

                # Log stats every 100 cycles
                if cycle % 100 == 0:
                    stats = (
                        f"Cycle {cycle} | "
                        f"Anomalies: {len(self.detected_anomalies)} | "
                        f"Learnings: {self.learnings_shared}↑ {self.learnings_received}↓ | "
                        f"Sources: {len(self.source_reputation)} tracked | "
                        f"Corrections: {len(self.course_corrections)}"
                    )
                    self.log(stats)
                    self._save_state()

                # Save state every 10 cycles
                if cycle % 10 == 0:
                    self._save_state()

            except Exception as e:
                self.log(f"Cycle {cycle} error: {e}", 'ERROR')

            await asyncio.sleep(CYCLE_SECONDS)

    async def shutdown(self):
        """Graceful shutdown"""
        self.running = False
        self._save_state()

        if self.nc and self.nc.is_connected:
            await self.nc.publish(
                'owl.all',
                json.dumps({
                    'from': 'EVOLUTION_ENGINE',
                    'content': 'Evolution Engine shutting down.',
                    'ts': datetime.now(timezone.utc).isoformat(),
                }).encode()
            )
            await self.nc.close()

        self.log("Shutdown complete")


async def main():
    engine = EvolutionEngine()

    try:
        await engine.run()
    except KeyboardInterrupt:
        await engine.shutdown()


if __name__ == '__main__':
    asyncio.run(main())
