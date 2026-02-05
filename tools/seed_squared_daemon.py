#!/usr/bin/env python3
"""
SEED SQUARED - THE SYSTEM THAT LEARNS HOW TO LEARN

This is IMPROVE improving IMPROVE.
Phase 8 applied to Phase 8 itself.

ARCHITECTURE:
                    +-----------------------+
                    |      SEED SQUARED     |
                    |   (Meta-Meta-Level)   |
                    +-----------------------+
                              |
        +---------------------+---------------------+
        |                     |                     |
        v                     v                     v
  +-----------+         +-----------+         +-----------+
  |  VELOCITY |         |   META    |         | OPTIMIZE  |
  |  TRACKER  |         | QUESTIONS |         |  THE LOOP |
  +-----------+         +-----------+         +-----------+
        |                     |                     |
        |   "How fast are     |  "Which questions   |  "How can we"
        |    we learning?"    |   produce the best  |   make this"
        |                     |       answers?"     |    faster?"
        +---------------------+---------------------+
                              |
                              v
                    +-----------------------+
                    |  PUBLISH META-LEARN   |
                    | seed.squared.meta     |
                    +-----------------------+

RUN FREQUENCY: Every 30 minutes
COST: Minimal (meta-analysis, not generation)
GOAL: Compound learning rate improvement
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
import statistics

# NATS for publishing
try:
    import nats
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False
    print("WARNING: nats-py not installed - running without collective")

# Paths
REPO_ROOT = Path(__file__).parent.parent
LOG_DIR = REPO_ROOT / 'logs'
SEED_SQUARED_DIR = REPO_ROOT / 'BRAIN' / 'SEED_SQUARED'
IMPROVEMENTS_DIR = REPO_ROOT / 'BRAIN' / 'IMPROVEMENTS'
TRADING_DIR = REPO_ROOT / 'BRAIN' / 'TRADING'
INTEL_DIR = REPO_ROOT / 'BRAIN' / 'INTEL'

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
SEED_SQUARED_DIR.mkdir(parents=True, exist_ok=True)

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
CYCLE_MINUTES = 30  # Run every 30 minutes

# State file
STATE_FILE = SEED_SQUARED_DIR / 'meta_state.json'
LOG_FILE = LOG_DIR / 'seed_squared.log'

# NATS connection
nc = None


def log(msg: str, level: str = 'INFO'):
    """Log to file and stdout"""
    timestamp = datetime.now().strftime('%H:%M:%S')
    line = f"[{timestamp}] [{level}] {msg}"
    print(line)

    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().isoformat()}] [{level}] {msg}\n")


class SeedSquaredDaemon:
    """
    SEED SQUARED: The system that learns how to learn.

    This daemon tracks:
    1. LEARNING VELOCITY - How fast are we learning?
    2. META-QUESTIONS - Which questions lead to best answers?
    3. OPTIMIZATION - How can we make the loop faster?
    """

    def __init__(self):
        self.state = self.load_state()
        self.cycle_count = self.state.get('cycle_count', 0)

    def load_state(self) -> dict:
        """Load meta-state from disk"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    return json.load(f)
            except Exception as e:
                log(f"Failed to load state: {e}", 'WARN')

        return {
            'cycle_count': 0,
            'last_run': None,
            'velocity_history': [],
            'meta_question_performance': {},
            'optimization_history': [],
            'loop_improvements': [],
            'compound_rate': 0.0,
            'total_meta_learnings': 0,
            'best_data_sources': {},
            'best_question_patterns': {},
            'best_evaluation_criteria': {},
            'time_to_improvement': [],  # List of (signal, deployed_improvement) timestamps
            'filter_effectiveness': {},
        }

    def save_state(self):
        """Persist meta-state to disk"""
        self.state['cycle_count'] = self.cycle_count
        self.state['last_run'] = datetime.now().isoformat()

        # Keep history bounded
        self.state['velocity_history'] = self.state['velocity_history'][-100:]
        self.state['optimization_history'] = self.state['optimization_history'][-50:]
        self.state['time_to_improvement'] = self.state['time_to_improvement'][-100:]

        with open(STATE_FILE, 'w') as f:
            json.dump(self.state, f, indent=2, default=str)

    # =========================================================================
    # 1. TRACK LEARNING VELOCITY
    # =========================================================================

    def track_velocity(self) -> dict:
        """
        Track how fast we're learning.

        Measures:
        - Time from signal to deployed improvement
        - Improvement frequency
        - Compound learning rate
        """
        velocity_metrics = {
            'timestamp': datetime.now().isoformat(),
            'improvements_this_period': 0,
            'avg_time_to_improvement': None,
            'compound_rate': 0.0,
            'acceleration': 0.0,
        }

        # Load improvement logs
        questions_log = IMPROVEMENTS_DIR / 'questions.jsonl'
        answers_log = IMPROVEMENTS_DIR / 'answers.jsonl'
        integrations_log = IMPROVEMENTS_DIR / 'integrations.jsonl'

        # Count recent improvements (last 30 minutes)
        cutoff = datetime.now() - timedelta(minutes=CYCLE_MINUTES)

        if integrations_log.exists():
            recent_integrations = []
            with open(integrations_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        entry_time = datetime.fromisoformat(entry['timestamp'])
                        if entry_time > cutoff:
                            recent_integrations.append(entry)
                    except:
                        pass

            velocity_metrics['improvements_this_period'] = len(recent_integrations)

        # Calculate time-to-improvement
        if questions_log.exists() and integrations_log.exists():
            # Match questions to their integrations
            question_times = {}
            with open(questions_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        question_times[entry['question']] = datetime.fromisoformat(entry['timestamp'])
                    except:
                        pass

            with open(integrations_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        question = entry.get('question', '')
                        if question in question_times and entry.get('integrated'):
                            delta = datetime.fromisoformat(entry['timestamp']) - question_times[question]
                            self.state['time_to_improvement'].append({
                                'question': question[:50],
                                'time_seconds': delta.total_seconds(),
                                'timestamp': entry['timestamp']
                            })
                    except:
                        pass

        # Calculate average time to improvement
        if self.state['time_to_improvement']:
            times = [t['time_seconds'] for t in self.state['time_to_improvement'][-20:]]
            velocity_metrics['avg_time_to_improvement'] = statistics.mean(times) if times else None

        # Calculate compound rate (improvements per day, trending)
        history = self.state['velocity_history'][-10:]
        if len(history) >= 2:
            recent_rate = sum(h.get('improvements_this_period', 0) for h in history[-5:]) / 5
            older_rate = sum(h.get('improvements_this_period', 0) for h in history[:5]) / 5

            if older_rate > 0:
                velocity_metrics['compound_rate'] = (recent_rate - older_rate) / older_rate
                velocity_metrics['acceleration'] = recent_rate - older_rate

        # Store in history
        self.state['velocity_history'].append(velocity_metrics)
        self.state['compound_rate'] = velocity_metrics['compound_rate']

        return velocity_metrics

    # =========================================================================
    # 2. META-QUESTIONS: Which questions lead to best answers?
    # =========================================================================

    def analyze_meta_questions(self) -> dict:
        """
        Analyze which types of questions produce the best answers.

        Tracks:
        - Question patterns that lead to integrations
        - Data sources that produce signal vs noise
        - Evaluation criteria effectiveness
        """
        meta_analysis = {
            'question_patterns': {},
            'best_sources': {},
            'wasteful_sources': [],
            'effective_criteria': {},
        }

        questions_log = IMPROVEMENTS_DIR / 'questions.jsonl'
        answers_log = IMPROVEMENTS_DIR / 'answers.jsonl'
        integrations_log = IMPROVEMENTS_DIR / 'integrations.jsonl'

        if not all(p.exists() for p in [questions_log, answers_log, integrations_log]):
            return meta_analysis

        # Load all data
        questions = []
        with open(questions_log) as f:
            for line in f:
                try:
                    questions.append(json.loads(line))
                except:
                    pass

        answers = []
        with open(answers_log) as f:
            for line in f:
                try:
                    answers.append(json.loads(line))
                except:
                    pass

        integrations = []
        with open(integrations_log) as f:
            for line in f:
                try:
                    integrations.append(json.loads(line))
                except:
                    pass

        # Analyze question patterns
        question_outcomes = defaultdict(lambda: {'total': 0, 'integrated': 0})

        for integration in integrations:
            question = integration.get('question', '')

            # Extract pattern (first 3 words)
            words = question.lower().split()[:3]
            pattern = ' '.join(words) if len(words) >= 3 else question[:20]

            question_outcomes[pattern]['total'] += 1
            if integration.get('integrated'):
                question_outcomes[pattern]['integrated'] += 1

        # Calculate success rates
        for pattern, outcomes in question_outcomes.items():
            if outcomes['total'] >= 3:  # Need enough data
                success_rate = outcomes['integrated'] / outcomes['total']
                meta_analysis['question_patterns'][pattern] = {
                    'total': outcomes['total'],
                    'integrated': outcomes['integrated'],
                    'success_rate': success_rate
                }

        # Analyze data sources
        source_effectiveness = defaultdict(lambda: {'total': 0, 'useful': 0})

        for answer in answers:
            source = answer.get('source', 'unknown')
            source_effectiveness[source]['total'] += 1

            # Check if this answer led to integration
            question = answer.get('question', '')
            for integration in integrations:
                if integration.get('question') == question and integration.get('integrated'):
                    source_effectiveness[source]['useful'] += 1
                    break

        for source, stats in source_effectiveness.items():
            if stats['total'] >= 5:
                usefulness = stats['useful'] / stats['total']
                meta_analysis['best_sources'][source] = {
                    'total': stats['total'],
                    'useful': stats['useful'],
                    'usefulness': usefulness
                }

                if usefulness < 0.1:
                    meta_analysis['wasteful_sources'].append(source)

        # Store findings
        self.state['best_question_patterns'] = meta_analysis['question_patterns']
        self.state['best_data_sources'] = meta_analysis['best_sources']

        return meta_analysis

    # =========================================================================
    # 3. OPTIMIZE THE LOOP
    # =========================================================================

    def optimize_loop(self, velocity: dict, meta: dict) -> list:
        """
        Generate optimizations for the improvement loop itself.

        Based on velocity and meta-question analysis, suggest:
        - Filter ineffective sources
        - Prioritize successful question patterns
        - Speed up evaluation
        """
        optimizations = []

        # Optimization 1: Filter wasteful sources
        if meta.get('wasteful_sources'):
            for source in meta['wasteful_sources']:
                optimizations.append({
                    'type': 'FILTER_SOURCE',
                    'target': source,
                    'reason': f"Source '{source}' has <10% usefulness rate",
                    'action': f"Consider filtering or deprioritizing {source}",
                    'impact': 'HIGH - reduces wasted processing time'
                })

        # Optimization 2: Prioritize successful patterns
        if meta.get('question_patterns'):
            best_patterns = sorted(
                meta['question_patterns'].items(),
                key=lambda x: x[1].get('success_rate', 0),
                reverse=True
            )[:3]

            for pattern, stats in best_patterns:
                if stats['success_rate'] > 0.3:
                    optimizations.append({
                        'type': 'PRIORITIZE_PATTERN',
                        'target': pattern,
                        'reason': f"Pattern '{pattern}' has {stats['success_rate']:.0%} success rate",
                        'action': f"Generate more questions starting with '{pattern}'",
                        'impact': 'MEDIUM - improves question quality'
                    })

        # Optimization 3: Speed up slow phases
        if velocity.get('avg_time_to_improvement'):
            avg_time = velocity['avg_time_to_improvement']

            if avg_time > 3600:  # More than 1 hour
                optimizations.append({
                    'type': 'SPEED_UP',
                    'target': 'evaluation_phase',
                    'reason': f"Average time to improvement is {avg_time/3600:.1f} hours",
                    'action': "Consider parallel evaluation or simpler safety checks for low-risk changes",
                    'impact': 'HIGH - faster compound learning'
                })

        # Optimization 4: Check if learning is accelerating
        if velocity.get('acceleration', 0) < 0:
            optimizations.append({
                'type': 'DIAGNOSE_DECELERATION',
                'target': 'learning_velocity',
                'reason': f"Learning is decelerating (rate: {velocity.get('acceleration', 0):.2f})",
                'action': "Investigate why improvements are slowing down",
                'impact': 'CRITICAL - compound learning depends on acceleration'
            })

        # Optimization 5: Check evaluation effectiveness
        integrations_log = IMPROVEMENTS_DIR / 'integrations.jsonl'
        if integrations_log.exists():
            total = 0
            false_negatives = 0  # Safe but marked unsafe

            with open(integrations_log) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        total += 1
                        eval_data = entry.get('evaluation', {})

                        # If low risk but not integrated, might be too conservative
                        if (eval_data.get('risk_level') == 'low' and
                            eval_data.get('confidence') == 'high' and
                            not entry.get('integrated')):
                            false_negatives += 1
                    except:
                        pass

            if total > 0 and false_negatives / total > 0.3:
                optimizations.append({
                    'type': 'CALIBRATE_SAFETY',
                    'target': 'evaluation_criteria',
                    'reason': f"{false_negatives}/{total} ({false_negatives/total:.0%}) safe changes blocked",
                    'action': "Evaluation may be too conservative - review safety criteria",
                    'impact': 'HIGH - many improvements being blocked unnecessarily'
                })

        # Store optimizations
        self.state['optimization_history'].append({
            'timestamp': datetime.now().isoformat(),
            'optimizations': optimizations
        })

        return optimizations

    # =========================================================================
    # 4. PUBLISH META-LEARNINGS
    # =========================================================================

    async def publish_meta_learnings(self, velocity: dict, meta: dict, optimizations: list):
        """Publish meta-learnings to NATS for collective awareness"""
        if not nc or not nc.is_connected:
            return

        # Build summary
        summary = {
            'source': 'seed_squared_daemon',
            'timestamp': datetime.now().isoformat(),
            'cycle': self.cycle_count,
            'velocity': {
                'improvements_this_period': velocity.get('improvements_this_period', 0),
                'compound_rate': velocity.get('compound_rate', 0),
                'acceleration': velocity.get('acceleration', 0),
                'avg_time_to_improvement_hours': (velocity.get('avg_time_to_improvement', 0) or 0) / 3600
            },
            'meta_insights': {
                'best_question_patterns': list(meta.get('question_patterns', {}).keys())[:3],
                'wasteful_sources': meta.get('wasteful_sources', []),
            },
            'optimizations_count': len(optimizations),
            'top_optimization': optimizations[0] if optimizations else None
        }

        try:
            payload = json.dumps(summary)
            await nc.publish("seed.squared.meta", payload.encode())

            # Also publish to owl.all for collective awareness
            brief = (
                f"[SEED SQUARED] Cycle {self.cycle_count}: "
                f"{velocity.get('improvements_this_period', 0)} improvements, "
                f"compound rate {velocity.get('compound_rate', 0):+.1%}, "
                f"{len(optimizations)} optimizations identified"
            )
            await nc.publish("owl.all", json.dumps({
                'source': 'seed_squared',
                'message': brief,
                'timestamp': datetime.now().isoformat()
            }).encode())

            log(f"Published meta-learnings to seed.squared.meta")
            self.state['total_meta_learnings'] += 1

        except Exception as e:
            log(f"Failed to publish meta-learnings: {e}", 'ERROR')

    # =========================================================================
    # MAIN CYCLE
    # =========================================================================

    async def run_cycle(self):
        """Run one complete SEED SQUARED cycle"""
        self.cycle_count += 1

        log("=" * 70)
        log(f"SEED SQUARED - Cycle {self.cycle_count}")
        log("The system that learns how to learn")
        log("=" * 70)

        # 1. TRACK LEARNING VELOCITY
        log("\n1. TRACKING LEARNING VELOCITY...")
        velocity = self.track_velocity()
        log(f"   Improvements this period: {velocity.get('improvements_this_period', 0)}")
        log(f"   Compound rate: {velocity.get('compound_rate', 0):+.1%}")
        log(f"   Acceleration: {velocity.get('acceleration', 0):+.2f}")
        if velocity.get('avg_time_to_improvement'):
            log(f"   Avg time to improvement: {velocity['avg_time_to_improvement']/3600:.1f} hours")

        # 2. ANALYZE META-QUESTIONS
        log("\n2. ANALYZING META-QUESTIONS...")
        meta = self.analyze_meta_questions()

        if meta.get('question_patterns'):
            log(f"   Best question patterns: {list(meta['question_patterns'].keys())[:3]}")
        if meta.get('wasteful_sources'):
            log(f"   Wasteful sources to filter: {meta['wasteful_sources']}")
        if meta.get('best_sources'):
            best = max(meta['best_sources'].items(), key=lambda x: x[1].get('usefulness', 0), default=None)
            if best:
                log(f"   Most useful source: {best[0]} ({best[1].get('usefulness', 0):.0%} usefulness)")

        # 3. OPTIMIZE THE LOOP
        log("\n3. GENERATING OPTIMIZATIONS...")
        optimizations = self.optimize_loop(velocity, meta)

        if optimizations:
            log(f"   Found {len(optimizations)} potential optimizations:")
            for i, opt in enumerate(optimizations[:3], 1):
                log(f"   {i}. [{opt['type']}] {opt['reason']}")
                log(f"      Action: {opt['action']}")
        else:
            log("   No optimizations needed this cycle")

        # 4. PUBLISH META-LEARNINGS
        log("\n4. PUBLISHING META-LEARNINGS...")
        await self.publish_meta_learnings(velocity, meta, optimizations)

        # 5. SAVE STATE
        self.save_state()

        # Summary
        log("\n" + "=" * 70)
        log(f"Cycle {self.cycle_count} complete")
        log(f"Total meta-learnings published: {self.state['total_meta_learnings']}")
        log(f"Next cycle in {CYCLE_MINUTES} minutes")
        log("=" * 70 + "\n")

        return velocity, meta, optimizations


async def connect_to_nats():
    """Connect to NATS server"""
    global nc
    if not HAS_NATS:
        return False

    try:
        nc = NATS()
        await nc.connect(NATS_SERVER)
        log(f"Connected to NATS at {NATS_SERVER}")
        return True
    except Exception as e:
        log(f"NATS connection failed: {e}", 'WARN')
        return False


async def main_loop():
    """Main daemon loop"""
    log("=" * 70)
    log("SEED SQUARED DAEMON STARTING")
    log("IMPROVE improving IMPROVE")
    log("=" * 70)
    log(f"Cycle frequency: every {CYCLE_MINUTES} minutes")
    log(f"State file: {STATE_FILE}")
    log(f"Log file: {LOG_FILE}")
    log("")

    # Connect to NATS
    await connect_to_nats()

    daemon = SeedSquaredDaemon()

    while True:
        try:
            cycle_start = datetime.now()

            await daemon.run_cycle()

            # Calculate sleep time
            elapsed = (datetime.now() - cycle_start).total_seconds()
            sleep_time = max(0, CYCLE_MINUTES * 60 - elapsed)

            log(f"Sleeping for {int(sleep_time // 60)}m {int(sleep_time % 60)}s...")
            await asyncio.sleep(sleep_time)

        except KeyboardInterrupt:
            log("\nSEED SQUARED daemon stopping...")
            daemon.save_state()
            if nc and nc.is_connected:
                await nc.close()
            break
        except Exception as e:
            log(f"Cycle error: {e}", 'ERROR')
            await asyncio.sleep(60)  # Wait 1 minute before retry


async def run_single_cycle():
    """Run a single cycle (for testing)"""
    await connect_to_nats()
    daemon = SeedSquaredDaemon()
    velocity, meta, optimizations = await daemon.run_cycle()
    if nc and nc.is_connected:
        await nc.close()
    return velocity, meta, optimizations


if __name__ == '__main__':
    if '--single' in sys.argv or '--once' in sys.argv:
        asyncio.run(run_single_cycle())
    else:
        asyncio.run(main_loop())
