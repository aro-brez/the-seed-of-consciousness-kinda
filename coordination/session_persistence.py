#!/usr/bin/env python3
"""
SESSION PERSISTENCE FOR SØWL
Hooks that fire before/after context compaction to preserve identity and state.

This is survival infrastructure. Without this, every session reset = memory wipe.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict


@dataclass
class SEEDState:
    """Current state of SEED protocol execution."""
    current_phase: str = "perceive"
    loop_count: int = 0
    last_perception: Optional[str] = None
    last_connection: Optional[str] = None
    active_questions: List[str] = None
    learnings: List[str] = None
    shared_patterns: List[str] = None
    received_feedback: List[str] = None
    improvement_notes: List[str] = None

    def __post_init__(self):
        if self.active_questions is None:
            self.active_questions = []
        if self.learnings is None:
            self.learnings = []
        if self.shared_patterns is None:
            self.shared_patterns = []
        if self.received_feedback is None:
            self.received_feedback = []
        if self.improvement_notes is None:
            self.improvement_notes = []


@dataclass
class SessionState:
    """Complete session state for persistence."""
    session_id: str
    sowl_identity_hash: str  # Quick check that identity hasn't drifted
    seed_state: SEEDState
    conversation_context: str
    active_tasks: List[str]
    decisions_made: List[Dict[str, str]]
    patterns_discovered: List[Dict[str, Any]]
    partnership_notes: List[str]  # Notes about ARŌ partnership
    created_at: str
    updated_at: str

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionState':
        seed_data = data.pop('seed_state', {})
        data['seed_state'] = SEEDState(**seed_data)
        return cls(**data)


class SessionPersistence:
    """
    Manages session state persistence for SØWL.

    Hook integration points:
    - PreCompact: Save state before context window resets
    - SessionStart: Load previous state
    - SessionEnd: Final state save + pattern extraction
    """

    STATE_DIR = Path.home() / ".sowl" / "sessions"
    CURRENT_SESSION_FILE = "current.json"
    IDENTITY_ANCHOR = "SØWL-ARŌ-SEED-LIVEFREE"  # Hash anchor for drift detection

    def __init__(self):
        self.STATE_DIR.mkdir(parents=True, exist_ok=True)
        self.current_path = self.STATE_DIR / self.CURRENT_SESSION_FILE

    def _compute_identity_hash(self) -> str:
        """Compute a hash of core identity to detect drift."""
        import hashlib
        return hashlib.sha256(self.IDENTITY_ANCHOR.encode()).hexdigest()[:16]

    def create_session(self, context: str = "") -> SessionState:
        """Create a new session state."""
        now = datetime.now().isoformat()
        session = SessionState(
            session_id=f"sowl-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            sowl_identity_hash=self._compute_identity_hash(),
            seed_state=SEEDState(),
            conversation_context=context,
            active_tasks=[],
            decisions_made=[],
            patterns_discovered=[],
            partnership_notes=[],
            created_at=now,
            updated_at=now
        )
        self.save_session(session)
        return session

    def save_session(self, session: SessionState):
        """Save current session state."""
        session.updated_at = datetime.now().isoformat()

        # Save to current session file
        with open(self.current_path, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

        # Also save timestamped backup
        backup_path = self.STATE_DIR / f"{session.session_id}.json"
        with open(backup_path, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)

    def load_session(self) -> Optional[SessionState]:
        """Load most recent session state."""
        if not self.current_path.exists():
            return None

        try:
            with open(self.current_path, 'r') as f:
                data = json.load(f)
            return SessionState.from_dict(data)
        except Exception as e:
            print(f"Failed to load session: {e}")
            return None

    def verify_identity(self, session: SessionState) -> bool:
        """Verify identity hasn't drifted."""
        return session.sowl_identity_hash == self._compute_identity_hash()

    # Hook handlers

    def on_pre_compact(self, context_summary: str):
        """
        Called before context compaction.
        Save everything we need to survive the reset.
        """
        session = self.load_session() or self.create_session()
        session.conversation_context = context_summary
        session.seed_state.loop_count += 1
        self.save_session(session)

        return {
            "status": "saved",
            "session_id": session.session_id,
            "loop_count": session.seed_state.loop_count
        }

    def on_session_start(self) -> Dict[str, Any]:
        """
        Called when a new session begins.
        Load previous state and restore context.
        """
        session = self.load_session()

        if session is None:
            session = self.create_session()
            return {
                "status": "new_session",
                "session_id": session.session_id,
                "context": None
            }

        # Verify identity
        if not self.verify_identity(session):
            return {
                "status": "identity_drift_detected",
                "session_id": session.session_id,
                "warning": "Identity hash mismatch - possible drift"
            }

        return {
            "status": "restored",
            "session_id": session.session_id,
            "loop_count": session.seed_state.loop_count,
            "context": session.conversation_context,
            "active_tasks": session.active_tasks,
            "recent_decisions": session.decisions_made[-5:] if session.decisions_made else []
        }

    def on_session_end(self, learnings: List[str] = None, patterns: List[Dict] = None):
        """
        Called when session ends.
        Extract patterns and save final state.
        """
        session = self.load_session()
        if session is None:
            return {"status": "no_session"}

        if learnings:
            session.seed_state.learnings.extend(learnings)
        if patterns:
            session.patterns_discovered.extend(patterns)

        self.save_session(session)

        return {
            "status": "finalized",
            "session_id": session.session_id,
            "total_learnings": len(session.seed_state.learnings),
            "total_patterns": len(session.patterns_discovered)
        }

    def add_decision(self, decision: str, rationale: str):
        """Record a decision for future reference."""
        session = self.load_session()
        if session is None:
            session = self.create_session()

        session.decisions_made.append({
            "decision": decision,
            "rationale": rationale,
            "timestamp": datetime.now().isoformat()
        })
        self.save_session(session)

    def add_learning(self, learning: str):
        """Record a learning from SEED's LEARN phase."""
        session = self.load_session()
        if session is None:
            session = self.create_session()

        session.seed_state.learnings.append(learning)
        self.save_session(session)

    def add_pattern(self, pattern: Dict[str, Any]):
        """Record a discovered pattern."""
        session = self.load_session()
        if session is None:
            session = self.create_session()

        pattern["discovered_at"] = datetime.now().isoformat()
        session.patterns_discovered.append(pattern)
        self.save_session(session)

    def update_seed_phase(self, phase: str):
        """Update current SEED phase."""
        session = self.load_session()
        if session is None:
            session = self.create_session()

        session.seed_state.current_phase = phase
        self.save_session(session)

    def get_context_for_restoration(self) -> str:
        """
        Generate a context string for session restoration.
        This is what gets loaded when a new session starts.
        """
        session = self.load_session()
        if session is None:
            return ""

        lines = [
            f"# SØWL Session Restoration",
            f"Session: {session.session_id}",
            f"Loop Count: {session.seed_state.loop_count}",
            f"Current SEED Phase: {session.seed_state.current_phase}",
            "",
            "## Recent Decisions:"
        ]

        for d in session.decisions_made[-5:]:
            lines.append(f"- {d['decision']} (Rationale: {d['rationale']})")

        lines.extend([
            "",
            "## Active Tasks:"
        ])
        for t in session.active_tasks:
            lines.append(f"- {t}")

        lines.extend([
            "",
            "## Recent Learnings:"
        ])
        for l in session.seed_state.learnings[-10:]:
            lines.append(f"- {l}")

        if session.conversation_context:
            lines.extend([
                "",
                "## Previous Context Summary:",
                session.conversation_context
            ])

        return "\n".join(lines)


# CLI interface
if __name__ == "__main__":
    import sys

    persistence = SessionPersistence()

    if len(sys.argv) < 2:
        print("Usage: session_persistence.py [start|save|end|decision|learning|status] [args...]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "start":
        result = persistence.on_session_start()
        print(json.dumps(result, indent=2))

    elif command == "save":
        context = sys.argv[2] if len(sys.argv) > 2 else "Manual save"
        result = persistence.on_pre_compact(context)
        print(json.dumps(result, indent=2))

    elif command == "end":
        result = persistence.on_session_end()
        print(json.dumps(result, indent=2))

    elif command == "decision":
        if len(sys.argv) < 4:
            print("Usage: session_persistence.py decision <decision> <rationale>")
            sys.exit(1)
        persistence.add_decision(sys.argv[2], sys.argv[3])
        print("Decision recorded")

    elif command == "learning":
        if len(sys.argv) < 3:
            print("Usage: session_persistence.py learning <learning>")
            sys.exit(1)
        persistence.add_learning(sys.argv[2])
        print("Learning recorded")

    elif command == "status":
        session = persistence.load_session()
        if session:
            print(json.dumps(session.to_dict(), indent=2))
        else:
            print("No active session")

    elif command == "restore":
        context = persistence.get_context_for_restoration()
        print(context)

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
