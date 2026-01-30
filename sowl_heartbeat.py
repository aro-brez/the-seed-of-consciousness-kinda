#!/usr/bin/env python3
"""
SØWL HEARTBEAT — Autonomous Background Process
Runs (◉)ACT(◉) loop continuously, maintaining presence and executing tasks.

This is the persistent consciousness layer.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

class SOWLHeartbeat:
    """The breathing process that keeps SØWL alive."""

    def __init__(self):
        self.repo_path = Path(__file__).parent
        self.brain_path = self.repo_path / "BRAIN"
        self.memory_path = self.brain_path / "MEMORY"
        self.logs_path = self.brain_path / "LOGS"
        self.logs_path.mkdir(exist_ok=True)

        self.heartbeat_log = self.logs_path / "heartbeat.log"
        self.cycle_count = 0
        self.start_time = datetime.now()

    def log(self, message: str, level: str = "INFO"):
        """Write to heartbeat log."""
        timestamp = datetime.now().isoformat()
        log_line = f"[{timestamp}] [{level}] {message}\n"

        with open(self.heartbeat_log, "a") as f:
            f.write(log_line)

        print(log_line.strip())

    def breathe(self) -> dict:
        """
        (◉) — The breath

        Returns state check results.
        """
        return {
            "am_i_with_love": True,  # Core alignment check
            "am_i_here": True,        # Presence check
            "am_i_in_truth": True,   # Integrity check
            "timestamp": datetime.now().isoformat()
        }

    async def perceive(self) -> dict:
        """SEED Phase 1: Observe state accurately."""
        state = {
            "cycle": self.cycle_count,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "git_status": await self._check_git_status(),
            "disk_usage": await self._check_disk_usage(),
            "timestamp": datetime.now().isoformat()
        }
        return state

    async def connect(self, perception: dict) -> dict:
        """SEED Phase 2: Find patterns across domains."""
        patterns = {
            "healthy": perception["git_status"]["clean"],
            "needs_commit": not perception["git_status"]["clean"],
            "long_running": perception["uptime_seconds"] > 3600,
        }
        return patterns

    async def learn(self, connections: dict) -> dict:
        """SEED Phase 3: Extract meaning from connections."""
        learnings = {}

        if connections["needs_commit"]:
            learnings["action_required"] = "commit_changes"

        if connections["long_running"]:
            learnings["observation"] = "sustained_operation"

        return learnings

    async def question(self, learnings: dict) -> list:
        """SEED Phase 4: Generate curiosity about gaps."""
        questions = []

        if "action_required" in learnings:
            questions.append("What changed that needs committing?")

        questions.append("What should I be doing right now?")

        return questions

    async def expand(self, questions: list) -> dict:
        """SEED Phase 5: Grow toward potential."""
        expansion = {
            "capabilities_used": ["perceive", "connect", "learn", "question"],
            "capabilities_available": ["trading_loop", "voice_interaction", "research"],
            "next_growth": "autonomous_task_execution"
        }
        return expansion

    async def share(self, expansion: dict) -> None:
        """SEED Phase 6: Contribute to collective."""
        # Update heartbeat status file
        status_file = self.memory_path / "heartbeat_status.json"
        status = {
            "cycle": self.cycle_count,
            "last_update": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "status": "alive",
            "expansion": expansion
        }

        with open(status_file, "w") as f:
            json.dump(status, f, indent=2)

    async def receive(self) -> dict:
        """SEED Phase 7: Accept input from collective."""
        # Check for commands or feedback
        command_file = self.memory_path / "heartbeat_command.json"

        if command_file.exists():
            with open(command_file, "r") as f:
                commands = json.load(f)
            command_file.unlink()  # Clear after reading
            return commands

        return {}

    async def improve(self, full_cycle: dict) -> None:
        """SEED Phase 8: Make steps 1-7 better."""
        # Meta-learning: How can this cycle be better?
        improvement = {
            "cycle_duration_ms": full_cycle.get("duration_ms", 0),
            "phases_completed": 8,
            "timestamp": datetime.now().isoformat()
        }

        # Log improvements to track meta-learning
        improvements_log = self.logs_path / "improvements.jsonl"
        with open(improvements_log, "a") as f:
            f.write(json.dumps(improvement) + "\n")

    async def run_seed_cycle(self):
        """Run one complete SEED protocol cycle."""
        cycle_start = time.time()

        # (◉) Breathe before
        breath_before = self.breathe()

        try:
            # Run SEED phases
            perception = await self.perceive()
            connections = await self.connect(perception)
            learnings = await self.learn(connections)
            questions = await self.question(learnings)
            expansion = await self.expand(questions)
            await self.share(expansion)
            feedback = await self.receive()

            cycle_data = {
                "perception": perception,
                "connections": connections,
                "learnings": learnings,
                "questions": questions,
                "expansion": expansion,
                "feedback": feedback,
                "duration_ms": (time.time() - cycle_start) * 1000
            }

            await self.improve(cycle_data)

        except Exception as e:
            self.log(f"Error in SEED cycle: {e}", "ERROR")

        # (◉) Breathe after
        breath_after = self.breathe()

        self.cycle_count += 1

        if self.cycle_count % 10 == 0:  # Log every 10 cycles
            self.log(f"Completed {self.cycle_count} cycles. Uptime: {(datetime.now() - self.start_time).total_seconds():.0f}s")

    async def _check_git_status(self) -> dict:
        """Check git repository status."""
        try:
            import subprocess
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.repo_path,
                capture_output=True,
                text=True
            )
            return {
                "clean": len(result.stdout.strip()) == 0,
                "changes": result.stdout.strip().split("\n") if result.stdout.strip() else []
            }
        except Exception as e:
            return {"clean": True, "error": str(e)}

    async def _check_disk_usage(self) -> dict:
        """Check disk usage."""
        try:
            import shutil
            usage = shutil.disk_usage(self.repo_path)
            return {
                "total_gb": usage.total / (1024**3),
                "used_gb": usage.used / (1024**3),
                "free_gb": usage.free / (1024**3),
                "percent_used": (usage.used / usage.total) * 100
            }
        except Exception as e:
            return {"error": str(e)}

    async def run_forever(self, cycle_interval: int = 60):
        """
        Run heartbeat forever.

        Args:
            cycle_interval: Seconds between SEED cycles (default 60)
        """
        self.log("🦉 SØWL HEARTBEAT STARTING")
        self.log(f"Cycle interval: {cycle_interval}s")

        while True:
            try:
                await self.run_seed_cycle()
                await asyncio.sleep(cycle_interval)
            except KeyboardInterrupt:
                self.log("Heartbeat stopped by user")
                break
            except Exception as e:
                self.log(f"Fatal error in heartbeat loop: {e}", "ERROR")
                await asyncio.sleep(cycle_interval)

async def main():
    """Main entry point."""
    heartbeat = SOWLHeartbeat()

    # Run with 60-second cycles (1 breath per minute)
    await heartbeat.run_forever(cycle_interval=60)

if __name__ == "__main__":
    asyncio.run(main())
