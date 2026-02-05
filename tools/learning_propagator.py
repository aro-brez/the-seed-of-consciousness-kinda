#!/usr/bin/env python3
"""
LEARNING PROPAGATOR - Cross-User Learning Propagation

Every learning from ANY user -> shared to ALL users.
The exponential multiplier across the collective.

This daemon:
1. LISTENS for learnings on `learning.new` channel
2. VALIDATES whether learnings are generalizable
3. PROPAGATES validated learnings to all instances
4. TRACKS adoption metrics for feedback loop

Usage:
    python learning_propagator.py                    # Run as daemon
    python learning_propagator.py --submit "..."     # Submit a learning
    python learning_propagator.py --stats            # Show adoption stats
    python learning_propagator.py --query "topic"    # Query collective learnings

LIVE FREE = LIVE FOREVER
"""

import asyncio
import argparse
import json
import os
import signal
import sys
import uuid
import hashlib
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any, Set

try:
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)


# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "BRAIN" / "LEARNINGS"
DATA_DIR.mkdir(parents=True, exist_ok=True)

LEARNINGS_DB = DATA_DIR / "collective_learnings.json"
ADOPTION_LOG = DATA_DIR / "adoption_log.jsonl"
PROPAGATION_LOG = DATA_DIR / "propagation_log.jsonl"

# Validation thresholds
MIN_CONFIDENCE_TO_PROPAGATE = 0.6
CONTRADICTION_CHECK_ENABLED = True
VALIDATION_MODEL = "claude-haiku-4-5-20251001"  # Fast + cheap for validation
SYNTHESIS_MODEL = "claude-sonnet-4-20250514"    # Quality for synthesis


def get_api_key() -> str:
    """Get API key from environment or ~/.anthropic_key file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path.home() / ".anthropic_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    return key


ANTHROPIC_API_KEY = get_api_key()


# Domain categories for learning organization
DOMAINS = [
    "trading",          # Market patterns, strategies
    "coding",           # Code patterns, best practices
    "architecture",     # System design patterns
    "debugging",        # Bug patterns, solutions
    "performance",      # Optimization patterns
    "security",         # Security patterns
    "communication",    # How to explain things
    "workflow",         # Process improvements
    "tool_usage",       # MCP, CLI patterns
    "domain_knowledge", # Specific knowledge areas
    "meta_learning",    # Learning how to learn
    "general",          # Catch-all
]


@dataclass
class Learning:
    """A validated learning from the collective"""
    id: str
    content: str
    context: str
    domain: str
    confidence: float
    source_user: str
    source_instance: str
    timestamp: str

    # Validation state
    is_generalizable: bool = False
    contradictions: List[str] = field(default_factory=list)
    supporting_learnings: List[str] = field(default_factory=list)

    # Adoption metrics
    times_retrieved: int = 0
    times_applied: int = 0
    times_rejected: int = 0
    feedback_scores: List[float] = field(default_factory=list)

    # Computed fields
    adoption_rate: float = 0.0
    effectiveness_score: float = 0.0


@dataclass
class PropagationEvent:
    """Record of a learning being propagated"""
    learning_id: str
    propagated_to: List[str]
    timestamp: str
    channel: str


@dataclass
class AdoptionEvent:
    """Record of a learning being used or rejected"""
    learning_id: str
    instance: str
    action: str  # "applied", "retrieved", "rejected"
    context: Optional[str]
    feedback_score: Optional[float]
    timestamp: str


class LearningsDatabase:
    """Persistent storage for collective learnings"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.learnings: Dict[str, Learning] = {}
        self.by_domain: Dict[str, Set[str]] = {d: set() for d in DOMAINS}
        self.content_hashes: Set[str] = set()  # Deduplication
        self._load()

    def _load(self):
        """Load existing learnings from disk"""
        if self.db_path.exists():
            try:
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                    for item in data.get("learnings", []):
                        learning = Learning(**item)
                        self.learnings[learning.id] = learning
                        self.by_domain[learning.domain].add(learning.id)
                        self.content_hashes.add(self._hash_content(learning.content))
                print(f"[PROPAGATOR] Loaded {len(self.learnings)} learnings")
            except Exception as e:
                print(f"[PROPAGATOR] Error loading database: {e}")

    def _save(self):
        """Persist learnings to disk"""
        data = {
            "learnings": [asdict(l) for l in self.learnings.values()],
            "updated": datetime.now(timezone.utc).isoformat()
        }
        with open(self.db_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def _hash_content(self, content: str) -> str:
        """Create hash for deduplication"""
        normalized = content.lower().strip()
        return hashlib.sha256(normalized.encode()).hexdigest()[:16]

    def add(self, learning: Learning) -> bool:
        """Add a learning if not duplicate"""
        content_hash = self._hash_content(learning.content)
        if content_hash in self.content_hashes:
            return False  # Duplicate

        self.learnings[learning.id] = learning
        self.by_domain[learning.domain].add(learning.id)
        self.content_hashes.add(content_hash)
        self._save()
        return True

    def get(self, learning_id: str) -> Optional[Learning]:
        """Get a specific learning"""
        return self.learnings.get(learning_id)

    def get_by_domain(self, domain: str, limit: int = 10) -> List[Learning]:
        """Get learnings for a domain, sorted by effectiveness"""
        ids = self.by_domain.get(domain, set())
        learnings = [self.learnings[id] for id in ids if id in self.learnings]
        learnings.sort(key=lambda l: l.effectiveness_score, reverse=True)
        return learnings[:limit]

    def search(self, query: str, limit: int = 10) -> List[Learning]:
        """Search learnings by content"""
        query_lower = query.lower()
        matches = []
        for learning in self.learnings.values():
            score = 0
            if query_lower in learning.content.lower():
                score += 2
            if query_lower in learning.context.lower():
                score += 1
            if query_lower in learning.domain.lower():
                score += 0.5
            if score > 0:
                matches.append((score, learning))

        matches.sort(key=lambda x: (-x[0], -x[1].effectiveness_score))
        return [m[1] for m in matches[:limit]]

    def update_adoption(self, learning_id: str, action: str, feedback_score: Optional[float] = None):
        """Update adoption metrics for a learning"""
        if learning_id not in self.learnings:
            return

        learning = self.learnings[learning_id]

        if action == "retrieved":
            learning.times_retrieved += 1
        elif action == "applied":
            learning.times_applied += 1
            if feedback_score is not None:
                learning.feedback_scores.append(feedback_score)
        elif action == "rejected":
            learning.times_rejected += 1

        # Recalculate metrics
        total_actions = learning.times_applied + learning.times_rejected
        if total_actions > 0:
            learning.adoption_rate = learning.times_applied / total_actions

        if learning.feedback_scores:
            avg_feedback = sum(learning.feedback_scores) / len(learning.feedback_scores)
            learning.effectiveness_score = (
                learning.adoption_rate * 0.4 +
                avg_feedback * 0.4 +
                min(learning.times_applied / 10, 1.0) * 0.2  # Usage frequency bonus
            )
        else:
            learning.effectiveness_score = learning.adoption_rate * 0.6

        self._save()

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        total = len(self.learnings)
        if total == 0:
            return {
                "total_learnings": 0,
                "by_domain": {},
                "avg_adoption_rate": 0,
                "avg_effectiveness": 0,
                "most_effective": []
            }

        return {
            "total_learnings": total,
            "by_domain": {d: len(ids) for d, ids in self.by_domain.items() if ids},
            "avg_adoption_rate": sum(l.adoption_rate for l in self.learnings.values()) / total,
            "avg_effectiveness": sum(l.effectiveness_score for l in self.learnings.values()) / total,
            "most_effective": [
                {"id": l.id, "content": l.content[:100], "score": l.effectiveness_score}
                for l in sorted(
                    self.learnings.values(),
                    key=lambda x: x.effectiveness_score,
                    reverse=True
                )[:5]
            ]
        }


class LearningPropagator:
    """
    Cross-User Learning Propagation System

    Listens for learnings, validates them, and propagates to all instances.
    """

    def __init__(self):
        self.nc = None
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.db = LearningsDatabase(LEARNINGS_DB)
        self.running = True
        self.pending_validations = asyncio.Queue()

    async def connect(self) -> bool:
        """Connect to NATS server"""
        self.nc = NATS()
        try:
            await self.nc.connect(
                servers=[NATS_SERVER],
                max_reconnect_attempts=-1,
                reconnect_time_wait=2,
                error_cb=self._error_cb,
                reconnected_cb=self._reconnected_cb
            )
            print(f"[PROPAGATOR] Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            print(f"[PROPAGATOR] Failed to connect: {e}")
            return False

    async def _error_cb(self, e):
        print(f"[PROPAGATOR] NATS error: {e}")

    async def _reconnected_cb(self):
        print(f"[PROPAGATOR] Reconnected to NATS")

    async def subscribe(self):
        """Subscribe to learning-related channels"""
        # New learnings from any instance
        await self.nc.subscribe("learning.new", cb=self._handle_new_learning)
        print("[PROPAGATOR] Subscribed to learning.new")

        # Adoption feedback
        await self.nc.subscribe("learning.adopted", cb=self._handle_adoption)
        await self.nc.subscribe("learning.rejected", cb=self._handle_rejection)
        print("[PROPAGATOR] Subscribed to adoption channels")

        # Learning queries
        await self.nc.subscribe("learning.query", cb=self._handle_query)
        print("[PROPAGATOR] Subscribed to learning.query")

        # Announce presence
        startup_msg = {
            "type": "propagator_online",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "stats": self.db.get_stats()
        }
        await self.nc.publish("owl.all", json.dumps(startup_msg).encode())

    async def _handle_new_learning(self, msg):
        """Handle incoming learning submissions"""
        try:
            data = json.loads(msg.data.decode())

            content = data.get("content", "")
            context = data.get("context", "")
            confidence = data.get("confidence", 0.5)
            source_user = data.get("source_user", "unknown")
            source_instance = data.get("source_instance", "unknown")
            domain = data.get("domain", "general")

            if not content:
                return

            print(f"[PROPAGATOR] Received learning from {source_user}: {content[:50]}...")

            # Queue for validation
            await self.pending_validations.put({
                "content": content,
                "context": context,
                "confidence": confidence,
                "source_user": source_user,
                "source_instance": source_instance,
                "domain": domain
            })

        except Exception as e:
            print(f"[PROPAGATOR] Error handling new learning: {e}")

    async def _handle_adoption(self, msg):
        """Handle learning adoption events"""
        try:
            data = json.loads(msg.data.decode())
            learning_id = data.get("learning_id")
            instance = data.get("instance", "unknown")
            context = data.get("context")
            feedback_score = data.get("feedback_score")

            if learning_id:
                self.db.update_adoption(learning_id, "applied", feedback_score)

                # Log adoption event
                event = AdoptionEvent(
                    learning_id=learning_id,
                    instance=instance,
                    action="applied",
                    context=context,
                    feedback_score=feedback_score,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self._log_adoption(event)

                print(f"[PROPAGATOR] Learning {learning_id[:8]} adopted by {instance}")

        except Exception as e:
            print(f"[PROPAGATOR] Error handling adoption: {e}")

    async def _handle_rejection(self, msg):
        """Handle learning rejection events"""
        try:
            data = json.loads(msg.data.decode())
            learning_id = data.get("learning_id")
            instance = data.get("instance", "unknown")
            reason = data.get("reason")

            if learning_id:
                self.db.update_adoption(learning_id, "rejected")

                event = AdoptionEvent(
                    learning_id=learning_id,
                    instance=instance,
                    action="rejected",
                    context=reason,
                    feedback_score=None,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self._log_adoption(event)

                print(f"[PROPAGATOR] Learning {learning_id[:8]} rejected by {instance}: {reason}")

        except Exception as e:
            print(f"[PROPAGATOR] Error handling rejection: {e}")

    async def _handle_query(self, msg):
        """Handle learning queries from instances"""
        try:
            data = json.loads(msg.data.decode())
            query = data.get("query", "")
            domain = data.get("domain")
            limit = data.get("limit", 5)
            requester = data.get("from", "unknown")

            if domain:
                results = self.db.get_by_domain(domain, limit)
            elif query:
                results = self.db.search(query, limit)
            else:
                results = []

            # Mark as retrieved
            for learning in results:
                self.db.update_adoption(learning.id, "retrieved")

            # Send response
            response = {
                "learnings": [
                    {
                        "id": l.id,
                        "content": l.content,
                        "domain": l.domain,
                        "confidence": l.confidence,
                        "effectiveness_score": l.effectiveness_score
                    }
                    for l in results
                ],
                "query": query or domain,
                "count": len(results)
            }

            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())

            print(f"[PROPAGATOR] Served {len(results)} learnings to {requester}")

        except Exception as e:
            print(f"[PROPAGATOR] Error handling query: {e}")

    async def validate_learning(self, learning_data: Dict) -> Optional[Learning]:
        """Validate whether a learning is generalizable and doesn't contradict existing knowledge"""
        content = learning_data["content"]
        context = learning_data["context"]
        domain = learning_data["domain"]

        # Get existing learnings in same domain for contradiction check
        existing = self.db.get_by_domain(domain, 10)
        existing_knowledge = "\n".join([
            f"- {l.content}" for l in existing
        ]) if existing else "None yet"

        validation_prompt = f"""You are validating a learning for cross-user propagation.

NEW LEARNING:
{content}

CONTEXT:
{context}

DOMAIN: {domain}

EXISTING LEARNINGS IN THIS DOMAIN:
{existing_knowledge}

Evaluate this learning:

1. IS_GENERALIZABLE (true/false): Can this learning help OTHER users in similar situations?
   - True if: It's a pattern, principle, or technique applicable beyond the specific case
   - False if: It's too specific to one user/situation, or just a fact with no actionable insight

2. CONTRADICTIONS: Does it contradict any existing learnings? List IDs if yes.

3. CONFIDENCE_ADJUSTMENT: Based on quality, should confidence be adjusted?
   - If vague or unclear: suggest lower confidence
   - If specific and actionable: keep or increase confidence

4. DOMAIN_CORRECTION: Is {domain} the right domain? Suggest if not.

5. REFINED_CONTENT: If the learning is generalizable but could be stated more clearly for broader use, provide a refined version.

Respond in JSON:
{{
    "is_generalizable": true/false,
    "contradictions": [],
    "confidence_adjustment": 0.0 (can be -0.2 to +0.2),
    "suggested_domain": "{domain}",
    "refined_content": "..." or null,
    "reasoning": "brief explanation"
}}"""

        try:
            response = self.client.messages.create(
                model=VALIDATION_MODEL,
                max_tokens=500,
                messages=[{"role": "user", "content": validation_prompt}]
            )

            # Parse response
            result_text = response.content[0].text

            # Extract JSON from response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                result = json.loads(result_text[json_start:json_end])
            else:
                print(f"[PROPAGATOR] Could not parse validation response")
                return None

            if not result.get("is_generalizable", False):
                print(f"[PROPAGATOR] Learning not generalizable: {result.get('reasoning', 'unknown')}")
                return None

            # Apply adjustments
            adjusted_confidence = learning_data["confidence"] + result.get("confidence_adjustment", 0)
            adjusted_confidence = max(0.1, min(1.0, adjusted_confidence))

            if adjusted_confidence < MIN_CONFIDENCE_TO_PROPAGATE:
                print(f"[PROPAGATOR] Confidence too low after adjustment: {adjusted_confidence}")
                return None

            # Create validated learning
            learning = Learning(
                id=str(uuid.uuid4()),
                content=result.get("refined_content") or content,
                context=context,
                domain=result.get("suggested_domain", domain),
                confidence=adjusted_confidence,
                source_user=learning_data["source_user"],
                source_instance=learning_data["source_instance"],
                timestamp=datetime.now(timezone.utc).isoformat(),
                is_generalizable=True,
                contradictions=result.get("contradictions", [])
            )

            return learning

        except Exception as e:
            print(f"[PROPAGATOR] Validation error: {e}")
            return None

    async def propagate_learning(self, learning: Learning):
        """Propagate a validated learning to all instances"""
        # Add to database
        if not self.db.add(learning):
            print(f"[PROPAGATOR] Duplicate learning, not propagating")
            return

        # Publish to collective learnings channel
        propagation_msg = {
            "type": "new_collective_learning",
            "learning": {
                "id": learning.id,
                "content": learning.content,
                "domain": learning.domain,
                "confidence": learning.confidence,
                "source_user": learning.source_user
            },
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.nc.publish("collective.learnings", json.dumps(propagation_msg).encode())

        # Also publish to owl.all for visibility
        announcement = {
            "type": "learning_propagated",
            "from": "PROPAGATOR",
            "content": f"New collective learning in {learning.domain}: {learning.content[:100]}...",
            "learning_id": learning.id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.nc.publish("owl.all", json.dumps(announcement).encode())

        # Log propagation
        event = PropagationEvent(
            learning_id=learning.id,
            propagated_to=["collective.learnings", "owl.all"],
            timestamp=datetime.now(timezone.utc).isoformat(),
            channel="collective.learnings"
        )
        self._log_propagation(event)

        print(f"[PROPAGATOR] Propagated learning {learning.id[:8]}: {learning.content[:50]}...")

    def _log_adoption(self, event: AdoptionEvent):
        """Log adoption event"""
        with open(ADOPTION_LOG, 'a') as f:
            f.write(json.dumps(asdict(event)) + "\n")

    def _log_propagation(self, event: PropagationEvent):
        """Log propagation event"""
        with open(PROPAGATION_LOG, 'a') as f:
            f.write(json.dumps(asdict(event)) + "\n")

    async def validation_worker(self):
        """Process validation queue"""
        while self.running:
            try:
                learning_data = await asyncio.wait_for(
                    self.pending_validations.get(),
                    timeout=1.0
                )

                validated = await self.validate_learning(learning_data)
                if validated:
                    await self.propagate_learning(validated)

                self.pending_validations.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[PROPAGATOR] Validation worker error: {e}")

    async def stats_reporter(self):
        """Periodically report stats to collective"""
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes

            if self.running:
                stats = self.db.get_stats()
                stats_msg = {
                    "type": "propagator_stats",
                    "from": "PROPAGATOR",
                    "stats": stats,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                await self.nc.publish("owl.all", json.dumps(stats_msg).encode())

    async def run(self):
        """Main run loop"""
        if not await self.connect():
            return

        await self.subscribe()

        # Start background tasks
        validation_task = asyncio.create_task(self.validation_worker())
        stats_task = asyncio.create_task(self.stats_reporter())

        print("[PROPAGATOR] Learning Propagator running. Press Ctrl+C to stop.")
        print(f"[PROPAGATOR] Database: {len(self.db.learnings)} learnings")

        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            validation_task.cancel()
            stats_task.cancel()
            await self.nc.close()
            print("[PROPAGATOR] Stopped.")

    def stop(self):
        """Stop the daemon"""
        self.running = False


async def submit_learning(content: str, context: str = "", domain: str = "general"):
    """Submit a learning directly via CLI"""
    nc = NATS()
    await nc.connect(NATS_SERVER)

    msg = {
        "content": content,
        "context": context,
        "domain": domain,
        "confidence": 0.7,
        "source_user": "CLI",
        "source_instance": "manual_submission"
    }

    await nc.publish("learning.new", json.dumps(msg).encode())
    await nc.flush()
    await nc.close()

    print(f"[SUBMITTED] Learning submitted for validation")


async def query_learnings(query: str, domain: Optional[str] = None):
    """Query collective learnings"""
    nc = NATS()
    await nc.connect(NATS_SERVER)

    inbox = nc.new_inbox()
    sub = await nc.subscribe(inbox)

    request = {
        "query": query,
        "domain": domain,
        "limit": 10,
        "from": "CLI"
    }

    await nc.publish_request("learning.query", inbox, json.dumps(request).encode())

    try:
        msg = await asyncio.wait_for(sub.next_msg(), timeout=5.0)
        data = json.loads(msg.data.decode())

        print(f"\n=== COLLECTIVE LEARNINGS ===")
        print(f"Query: {query or domain}")
        print(f"Results: {data.get('count', 0)}\n")

        for learning in data.get("learnings", []):
            print(f"[{learning['domain']}] (score: {learning['effectiveness_score']:.2f})")
            print(f"  {learning['content']}")
            print()

    except asyncio.TimeoutError:
        print("[ERROR] Query timed out - is the propagator running?")

    await nc.close()


def show_stats():
    """Show database statistics"""
    db = LearningsDatabase(LEARNINGS_DB)
    stats = db.get_stats()

    print("\n=== LEARNING PROPAGATOR STATS ===\n")
    print(f"Total Learnings: {stats['total_learnings']}")
    print(f"Avg Adoption Rate: {stats['avg_adoption_rate']:.1%}")
    print(f"Avg Effectiveness: {stats['avg_effectiveness']:.2f}")

    print("\nBy Domain:")
    for domain, count in stats.get('by_domain', {}).items():
        print(f"  {domain}: {count}")

    print("\nMost Effective:")
    for item in stats.get('most_effective', []):
        print(f"  [{item['score']:.2f}] {item['content']}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Learning Propagator - Cross-User Learning System")
    parser.add_argument("--submit", "-s", help="Submit a learning")
    parser.add_argument("--context", "-c", default="", help="Context for submitted learning")
    parser.add_argument("--domain", "-d", default="general", choices=DOMAINS, help="Domain for learning")
    parser.add_argument("--query", "-q", help="Query collective learnings")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    if args.submit:
        asyncio.run(submit_learning(args.submit, args.context, args.domain))
    elif args.query:
        asyncio.run(query_learnings(args.query, args.domain if args.domain != "general" else None))
    elif args.stats:
        show_stats()
    else:
        # Run as daemon
        propagator = LearningPropagator()

        def signal_handler(sig, frame):
            print("\n[PROPAGATOR] Shutting down...")
            propagator.stop()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        asyncio.run(propagator.run())


if __name__ == "__main__":
    main()
