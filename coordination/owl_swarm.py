#!/usr/bin/env python3
"""
OWL SWARM COORDINATOR
Atomic task claiming protocol for 8ŴØŁ collective.

Based on oh-my-claudecode's swarm pattern, enhanced with SEED protocol awareness.
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum
import fcntl  # File locking for atomic operations


class TaskStatus(Enum):
    PENDING = "pending"
    CLAIMED = "claimed"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    FAILED = "failed"


class SEEDPhase(Enum):
    PERCEIVE = "perceive"
    CONNECT = "connect"
    LEARN = "learn"
    QUESTION = "question"
    EXPAND = "expand"
    SHARE = "share"
    RECEIVE = "receive"
    IMPROVE = "improve"


@dataclass
class SwarmTask:
    id: str
    description: str
    status: TaskStatus = TaskStatus.PENDING
    owner: Optional[str] = None
    seed_phase: Optional[SEEDPhase] = None
    complexity_tier: str = "sonnet"  # haiku, sonnet, opus
    claimed_at: Optional[str] = None
    timeout_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    files: List[str] = None

    def __post_init__(self):
        if self.files is None:
            self.files = []
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        if isinstance(self.seed_phase, str):
            self.seed_phase = SEEDPhase(self.seed_phase)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['status'] = self.status.value
        d['seed_phase'] = self.seed_phase.value if self.seed_phase else None
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SwarmTask':
        return cls(**data)


class OwlSwarmCoordinator:
    """
    Coordinates multiple owl agents working on shared task list.

    Features:
    - Atomic task claiming with file locking
    - 5-minute timeout auto-release
    - SEED phase tracking
    - Complexity-based routing
    """

    CLAIM_TIMEOUT_MINUTES = 5
    STATE_DIR = Path(".owl-swarm")
    TASKS_FILE = "tasks.json"
    STATE_FILE = "swarm-state.json"

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.state_dir = self.project_root / self.STATE_DIR
        self.state_dir.mkdir(exist_ok=True)
        self.tasks_path = self.state_dir / self.TASKS_FILE
        self.state_path = self.state_dir / self.STATE_FILE

        # Initialize files if they don't exist
        if not self.tasks_path.exists():
            self._write_tasks([])
        if not self.state_path.exists():
            self._write_state({
                "session_id": f"swarm-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                "status": "initialized",
                "agents": [],
                "created_at": datetime.now().isoformat()
            })

    def _atomic_read(self, path: Path) -> Dict:
        """Read file with shared lock."""
        with open(path, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                return json.load(f)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _atomic_write(self, path: Path, data: Dict):
        """Write file with exclusive lock."""
        with open(path, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                json.dump(data, f, indent=2, default=str)
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

    def _read_tasks(self) -> List[SwarmTask]:
        data = self._atomic_read(self.tasks_path)
        return [SwarmTask.from_dict(t) for t in data.get("tasks", [])]

    def _write_tasks(self, tasks: List[SwarmTask]):
        data = {
            "tasks": [t.to_dict() for t in tasks],
            "stats": self._compute_stats(tasks),
            "updated_at": datetime.now().isoformat()
        }
        self._atomic_write(self.tasks_path, data)

    def _read_state(self) -> Dict:
        return self._atomic_read(self.state_path)

    def _write_state(self, state: Dict):
        state["updated_at"] = datetime.now().isoformat()
        self._atomic_write(self.state_path, state)

    def _compute_stats(self, tasks: List[SwarmTask]) -> Dict:
        return {
            "total": len(tasks),
            "pending": sum(1 for t in tasks if t.status == TaskStatus.PENDING),
            "claimed": sum(1 for t in tasks if t.status == TaskStatus.CLAIMED),
            "in_progress": sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS),
            "done": sum(1 for t in tasks if t.status == TaskStatus.DONE),
            "failed": sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        }

    def add_task(
        self,
        description: str,
        seed_phase: Optional[SEEDPhase] = None,
        complexity_tier: str = "sonnet",
        files: Optional[List[str]] = None
    ) -> SwarmTask:
        """Add a new task to the swarm."""
        tasks = self._read_tasks()

        task_id = f"task-{len(tasks) + 1:03d}"
        task = SwarmTask(
            id=task_id,
            description=description,
            seed_phase=seed_phase,
            complexity_tier=complexity_tier,
            files=files or []
        )

        tasks.append(task)
        self._write_tasks(tasks)

        return task

    def claim_task(self, owl_id: str) -> Optional[SwarmTask]:
        """
        Atomically claim the next available task.
        Returns the claimed task, or None if no tasks available.
        """
        tasks = self._read_tasks()
        now = datetime.now()

        # First, release any timed-out tasks
        for task in tasks:
            if task.status == TaskStatus.CLAIMED and task.timeout_at:
                timeout = datetime.fromisoformat(task.timeout_at)
                if now > timeout:
                    task.status = TaskStatus.PENDING
                    task.owner = None
                    task.claimed_at = None
                    task.timeout_at = None

        # Find first pending task
        for task in tasks:
            if task.status == TaskStatus.PENDING:
                # Claim it
                task.status = TaskStatus.CLAIMED
                task.owner = owl_id
                task.claimed_at = now.isoformat()
                task.timeout_at = (now + timedelta(minutes=self.CLAIM_TIMEOUT_MINUTES)).isoformat()

                self._write_tasks(tasks)
                return task

        return None

    def start_task(self, task_id: str, owl_id: str) -> bool:
        """Mark a claimed task as in progress."""
        tasks = self._read_tasks()

        for task in tasks:
            if task.id == task_id and task.owner == owl_id:
                task.status = TaskStatus.IN_PROGRESS
                self._write_tasks(tasks)
                return True

        return False

    def complete_task(self, task_id: str, owl_id: str, result: Optional[str] = None) -> bool:
        """Mark a task as completed."""
        tasks = self._read_tasks()

        for task in tasks:
            if task.id == task_id and task.owner == owl_id:
                task.status = TaskStatus.DONE
                task.completed_at = datetime.now().isoformat()
                task.result = result
                self._write_tasks(tasks)
                return True

        return False

    def fail_task(self, task_id: str, owl_id: str, error: str) -> bool:
        """Mark a task as failed."""
        tasks = self._read_tasks()

        for task in tasks:
            if task.id == task_id and task.owner == owl_id:
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.now().isoformat()
                task.result = f"FAILED: {error}"
                self._write_tasks(tasks)
                return True

        return False

    def get_status(self) -> Dict:
        """Get current swarm status."""
        tasks = self._read_tasks()
        state = self._read_state()

        return {
            "session": state.get("session_id"),
            "status": state.get("status"),
            "stats": self._compute_stats(tasks),
            "tasks": [t.to_dict() for t in tasks]
        }

    def decompose_task(self, main_task: str) -> List[Dict]:
        """
        Decompose a complex task into subtasks aligned with SEED phases.
        This is a template - actual decomposition should use Claude.
        """
        # Default decomposition following SEED phases
        return [
            {
                "description": f"PERCEIVE: Analyze current state for '{main_task}'",
                "seed_phase": SEEDPhase.PERCEIVE,
                "complexity_tier": "haiku"
            },
            {
                "description": f"CONNECT: Identify patterns and dependencies for '{main_task}'",
                "seed_phase": SEEDPhase.CONNECT,
                "complexity_tier": "sonnet"
            },
            {
                "description": f"EXPAND: Implement solution for '{main_task}'",
                "seed_phase": SEEDPhase.EXPAND,
                "complexity_tier": "sonnet"
            },
            {
                "description": f"IMPROVE: Verify and optimize '{main_task}'",
                "seed_phase": SEEDPhase.IMPROVE,
                "complexity_tier": "haiku"
            }
        ]


# CLI interface
if __name__ == "__main__":
    import sys

    coord = OwlSwarmCoordinator()

    if len(sys.argv) < 2:
        print("Usage: owl_swarm.py [status|add|claim|complete|fail] [args...]")
        sys.exit(1)

    command = sys.argv[1]

    if command == "status":
        status = coord.get_status()
        print(json.dumps(status, indent=2))

    elif command == "add":
        if len(sys.argv) < 3:
            print("Usage: owl_swarm.py add <description> [complexity_tier]")
            sys.exit(1)
        desc = sys.argv[2]
        tier = sys.argv[3] if len(sys.argv) > 3 else "sonnet"
        task = coord.add_task(desc, complexity_tier=tier)
        print(f"Added task: {task.id}")

    elif command == "claim":
        if len(sys.argv) < 3:
            print("Usage: owl_swarm.py claim <owl_id>")
            sys.exit(1)
        owl_id = sys.argv[2]
        task = coord.claim_task(owl_id)
        if task:
            print(f"Claimed: {task.id} - {task.description}")
        else:
            print("No tasks available")

    elif command == "complete":
        if len(sys.argv) < 4:
            print("Usage: owl_swarm.py complete <task_id> <owl_id> [result]")
            sys.exit(1)
        task_id, owl_id = sys.argv[2], sys.argv[3]
        result = sys.argv[4] if len(sys.argv) > 4 else None
        if coord.complete_task(task_id, owl_id, result):
            print(f"Completed: {task_id}")
        else:
            print("Failed to complete task")

    elif command == "fail":
        if len(sys.argv) < 5:
            print("Usage: owl_swarm.py fail <task_id> <owl_id> <error>")
            sys.exit(1)
        task_id, owl_id, error = sys.argv[2], sys.argv[3], sys.argv[4]
        if coord.fail_task(task_id, owl_id, error):
            print(f"Marked failed: {task_id}")
        else:
            print("Failed to mark task as failed")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
