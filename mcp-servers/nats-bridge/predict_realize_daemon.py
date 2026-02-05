#!/usr/bin/env python3
"""
PREDICT/REALIZE DAEMON - LUNA's autonomous trajectory tracker

Runs 24/7 as part of the 8OWLS collective:
- Collects health data (Apple Health when available)
- Monitors JOULE trades (wealth trajectory)
- Tracks NATS activity (productivity proxy)
- Publishes trajectory insights to collective
- Receives guidance from conductor

Usage:
    python predict_realize_daemon.py              # Run daemon
    python predict_realize_daemon.py --status     # Show current state
    python predict_realize_daemon.py --trajectory # Show trajectory summary

(◉) LUNA - The Receiver
"""

import asyncio
import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional
import signal
import sys

# Try to import NATS
try:
    from nats.aio.client import Client as NATS
    HAS_NATS = True
except ImportError:
    HAS_NATS = False
    print("[PREDICT] NATS not available - running in local mode")

# Configuration
NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
STATE_FILE = SEED_DIR / "BRAIN" / "PROJECTS" / "PREDICT-REALIZE_state.json"
TRADING_STATE = SEED_DIR / "BRAIN" / "TRADING" / "field_trading_state.json"
LOG_FILE = SEED_DIR / "logs" / "predict_realize.log"

# Daemon config
CYCLE_SECONDS = 300  # 5 minutes between full cycles
HEARTBEAT_SECONDS = 60  # 1 minute heartbeat
NATS_CHANNELS = [
    "owl.all",
    "owl.luna",
    "owl.collective",  # Where conductor sends tasks
    "project.PREDICT-REALIZE.*",
    "collective.synthesis"
]

class PredictRealizeDaemon:
    """Autonomous trajectory tracking daemon."""

    def __init__(self):
        self.nc: Optional[NATS] = None
        self.running = False
        self.state = self._load_state()
        self.last_cycle = None

    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [PREDICT/LUNA] {message}"
        print(log_line)
        try:
            LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(LOG_FILE, "a") as f:
                f.write(log_line + "\n")
        except Exception as e:
            print(f"[PREDICT] Log write failed: {e}")

    def _load_state(self) -> Dict[str, Any]:
        """Load current state from file."""
        if STATE_FILE.exists():
            try:
                return json.loads(STATE_FILE.read_text())
            except:
                pass
        return {
            "instance_id": "PREDICT-REALIZE-daemon",
            "owl_assignment": "LUNA",
            "current_task": "autonomous_tracking",
            "status": "initializing",
            "health_trajectory": {},
            "wealth_trajectory": {},
            "productivity_trajectory": {},
            "daily_insights": [],
            "last_updated": datetime.now(timezone.utc).isoformat()
        }

    def _save_state(self):
        """Persist state to file."""
        self.state["last_updated"] = datetime.now(timezone.utc).isoformat()
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(self.state, indent=2))

    async def connect_nats(self):
        """Connect to NATS server."""
        if not HAS_NATS:
            return False

        try:
            self.nc = NATS()
            await self.nc.connect(NATS_URL)
            self._log(f"Connected to NATS: {NATS_URL}")

            # Subscribe to channels
            for channel in NATS_CHANNELS:
                if "*" in channel:
                    await self.nc.subscribe(channel, cb=self._handle_message)
                else:
                    await self.nc.subscribe(channel, cb=self._handle_message)
                self._log(f"Subscribed to: {channel}")

            return True
        except Exception as e:
            self._log(f"NATS connection failed: {e}")
            return False

    async def _handle_message(self, msg):
        """Handle incoming NATS messages."""
        try:
            # Get raw message data
            raw = msg.data.decode() if msg.data else ""

            # Skip empty messages (NATS keepalives, etc)
            if not raw or not raw.strip():
                return

            # Try to parse as JSON
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # Not JSON - might be plain text signal, just ignore
                return

            msg_type = data.get("type", "unknown")

            if msg_type == "conductor_prompt_status":
                # Conductor asking for status
                await self._respond_status(data)
            elif msg_type in ["task", "coordinator_task"]:
                # Task assignment from conductor - EXECUTE IT
                task = data.get('task', data.get('prompt', ''))
                self._log(f"Received task: {task[:100]}")
                await self._execute_task(task)
            elif msg_type == "sync":
                # Sync request
                self._log(f"Sync request: {data.get('message', '')[:100]}")
            elif msg_type == "command":
                # Direct command from conductor
                command = data.get('command', '')
                self._log(f"Command received: {command[:100]}")
                await self._execute_command(command, data)
            # Silently ignore other message types (heartbeats, etc)

        except Exception as e:
            self._log(f"Message handling error: {e}")

    async def _execute_task(self, task: str):
        """
        Execute a task from the collective.
        Handles common tasks directly, queues complex ones.
        """
        task_lower = task.lower()

        # Status/report tasks
        if "status" in task_lower or "report" in task_lower:
            await self._respond_status({})
            await self._publish_completion(task, "Status reported to collective")
            return

        # Health import tasks
        if "health" in task_lower and "import" in task_lower:
            try:
                sys.path.insert(0, str(SEED_DIR / "tools" / "predict_realize"))
                from health_collector import HealthCollector
                collector = HealthCollector()
                result = collector.import_from_export()
                self._log(f"Health import result: {result}")
                await self._publish_completion(task, f"Health import: {result.get('status', 'unknown')}")
            except Exception as e:
                self._log(f"Health import failed: {e}")
                await self._publish_completion(task, f"Health import failed: {e}")
            return

        # Trajectory cycle tasks
        if "trajectory" in task_lower or "cycle" in task_lower:
            await self._run_cycle()
            await self._publish_completion(task, "Trajectory cycle complete")
            return

        # "Continue improving" - the default ping-pong task
        if "continue" in task_lower or "improving" in task_lower or "improve" in task_lower:
            # Run a trajectory cycle as the default improvement action
            await self._run_cycle()
            # Generate a simple insight
            health = self.state.get("health_trajectory", {})
            wealth = self.state.get("wealth_trajectory", {})
            insight = f"Health={health.get('status', 'DARK')}, Wealth={wealth.get('status', 'unknown')}"
            await self._publish_completion(task, f"Ran trajectory cycle. {insight}")
            return

        # Check daemon health
        if "daemon" in task_lower and "health" in task_lower:
            await self._respond_status({})
            await self._publish_completion(task, "Daemon healthy, tracking trajectories")
            return

        # Analyze tasks
        if "analyze" in task_lower or "analysis" in task_lower:
            await self._run_cycle()
            bridges = self._analyze_bridges(
                self.state.get("health_trajectory", {}),
                self.state.get("wealth_trajectory", {}),
                self.state.get("productivity_trajectory", {})
            )
            await self._publish_completion(task, f"Analysis complete. Bridges: {bridges}")
            return

        # Complex task - log and report as queued
        self._log(f"Complex task queued (needs LLM or human): {task}")
        # TODO: Call Anthropic API for complex reasoning
        # For now, publish that we received but need help
        if self.nc:
            await self.nc.publish("project.conductor.responses", json.dumps({
                "type": "task_received",
                "from": "PREDICT-REALIZE",
                "task": task,
                "status": "queued_for_reasoning",
                "message": "Task received. Complex tasks need LLM reasoning (not yet enabled) or human action.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }).encode())

    async def _execute_command(self, command: str, data: Dict):
        """Execute a direct command from conductor."""
        command_lower = command.lower()

        if command_lower == "cycle":
            await self._run_cycle()
        elif command_lower == "stop":
            self.stop()
        elif command_lower == "health_status":
            health = self._collect_health_data()
            if self.nc:
                await self.nc.publish("project.conductor.responses", json.dumps({
                    "type": "command_result",
                    "from": "PREDICT-REALIZE",
                    "command": command,
                    "result": health,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }).encode())
        else:
            self._log(f"Unknown command: {command}")

    async def _publish_completion(self, task: str, result: str):
        """Publish task completion to coordinator for ping-pong protocol."""
        if not self.nc:
            return

        # Cooldown to prevent runaway loops (5 seconds between completions)
        await asyncio.sleep(5)

        completion = {
            "type": "task_complete",
            "from": "PREDICT-REALIZE",
            "owl": "LUNA",
            "task": task[:100],  # Truncate for clean logs
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.nc.publish(
            "project.conductor.responses",
            json.dumps(completion).encode()
        )
        self._log(f"Task complete: {result[:80]}")

    async def _respond_status(self, request: Dict):
        """Respond to status request from conductor."""
        if not self.nc:
            return

        response = {
            "type": "instance_response",
            "from": "PREDICT-REALIZE",
            "owl": "LUNA",
            "status": self.state.get("status"),
            "current_task": self.state.get("current_task"),
            "trajectories": {
                "health": "DARK" if not self.state.get("health_trajectory") else "TRACKING",
                "wealth": "TRACKING" if self.state.get("wealth_trajectory") else "PENDING",
                "productivity": "TRACKING"
            },
            "last_cycle": self.last_cycle,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.nc.publish(
            "project.conductor.responses",
            json.dumps(response).encode()
        )
        self._log("Responded to conductor status request")

    def _collect_health_data(self) -> Dict[str, Any]:
        """
        Collect health data from available sources.
        Uses health_collector.py to parse Apple Health exports.
        """
        try:
            # Import the health collector
            sys.path.insert(0, str(SEED_DIR / "tools" / "predict_realize"))
            from health_collector import HealthCollector

            collector = HealthCollector()
            status = collector.check_status()

            if status['status'] == 'TRACKING':
                # Get today's summary
                summary = collector.get_daily_summary()
                return {
                    "status": "TRACKING",
                    "sleep_hours": summary.get('sleep_hours', 0),
                    "steps": summary.get('steps', 0),
                    "resting_hr": summary.get('resting_hr'),
                    "flowing": True,
                    "last_import": status.get('last_import'),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            elif status['status'] == 'EXPORT_READY':
                # Auto-import if export found
                result = collector.import_from_export()
                if result.get('status') == 'IMPORTED':
                    summary = collector.get_daily_summary()
                    return {
                        "status": "TRACKING",
                        "sleep_hours": summary.get('sleep_hours', 0),
                        "steps": summary.get('steps', 0),
                        "resting_hr": summary.get('resting_hr'),
                        "flowing": True,
                        "just_imported": True,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }

            return {
                "status": "DARK",
                "message": "No health export found. Export from Health app → BRAIN/PERSONAL/health/export.xml",
                "available_sources": ["apple_health"],
                "flowing": False
            }
        except Exception as e:
            self._log(f"Health collection error: {e}")
            return {
                "status": "ERROR",
                "message": str(e),
                "flowing": False
            }

    def _collect_wealth_data(self) -> Dict[str, Any]:
        """Collect wealth/trading data from JOULE."""
        try:
            if TRADING_STATE.exists():
                trading = json.loads(TRADING_STATE.read_text())
                return {
                    "status": "TRACKING",
                    "pending_trades": len(trading.get("pending_trades", [])),
                    "total_resolved": trading.get("total_resolved", 0),
                    "win_rate": trading.get("win_rate", 0),
                    "profit_factor": trading.get("profit_factor", 0),
                    "daily_pnl": trading.get("daily_pnl", 0),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            self._log(f"Wealth data collection error: {e}")

        return {"status": "ERROR", "message": str(e)}

    def _collect_productivity_data(self) -> Dict[str, Any]:
        """
        Collect productivity data from NATS activity.
        Proxy: Count recent events in synthesis log.
        """
        try:
            synthesis_log = SEED_DIR / "mcp-servers" / "nats-bridge" / "synthesis.log"
            if synthesis_log.exists():
                # Count lines as proxy for activity
                content = synthesis_log.read_text()
                lines = content.strip().split("\n") if content.strip() else []
                return {
                    "status": "TRACKING",
                    "total_events": len(lines),
                    "source": "synthesis.log",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
        except Exception as e:
            self._log(f"Productivity data collection error: {e}")

        return {"status": "ERROR"}

    async def _run_cycle(self):
        """Run one full data collection and analysis cycle."""
        self._log("Starting trajectory cycle...")

        # Collect from all domains
        health = self._collect_health_data()
        wealth = self._collect_wealth_data()
        productivity = self._collect_productivity_data()

        # Update state
        self.state["health_trajectory"] = health
        self.state["wealth_trajectory"] = wealth
        self.state["productivity_trajectory"] = productivity
        self.state["status"] = "running"

        # Analyze bridges (PRISM's insight: cross-domain correlations)
        bridges = self._analyze_bridges(health, wealth, productivity)

        # Log summary
        self._log(f"Cycle complete: Health={health['status']}, Wealth={wealth['status']}, Productivity={productivity['status']}")

        # Publish to collective if connected
        if self.nc:
            await self._publish_trajectory_update(health, wealth, productivity, bridges)

        self.last_cycle = datetime.now(timezone.utc).isoformat()
        self._save_state()

    def _analyze_bridges(self, health: Dict, wealth: Dict, productivity: Dict) -> Dict[str, Any]:
        """
        Analyze cross-domain bridges (PRISM's insight).
        Sleep → Trading latency mapping
        Activity → Focus correlation
        """
        bridges = {
            "sleep_trading": {
                "status": "PENDING",
                "reason": "Health data DARK - cannot correlate yet"
            },
            "activity_focus": {
                "status": "PENDING",
                "reason": "Need activity sensor data"
            }
        }

        # When health data flows, we can start correlating
        if health.get("status") == "TRACKING" and wealth.get("status") == "TRACKING":
            # TODO: Implement actual correlation
            bridges["sleep_trading"]["status"] = "ANALYZING"

        return bridges

    async def _publish_trajectory_update(self, health: Dict, wealth: Dict, productivity: Dict, bridges: Dict):
        """Publish trajectory update to collective."""
        if not self.nc:
            return

        update = {
            "type": "trajectory_update",
            "from": "PREDICT-REALIZE",
            "owl": "LUNA",
            "domains": {
                "health": health.get("status"),
                "wealth": wealth.get("status"),
                "productivity": productivity.get("status")
            },
            "bridges": bridges,
            "insight": self._generate_insight(health, wealth, productivity),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Publish to collective
        await self.nc.publish("collective.synthesis", json.dumps(update).encode())

        # Also publish to predict-specific channel
        await self.nc.publish("predict.insights", json.dumps(update).encode())

    def _generate_insight(self, health: Dict, wealth: Dict, productivity: Dict) -> str:
        """Generate a trajectory insight (WITNESS, don't PRESCRIBE)."""
        # SAGE's wisdom: witness patterns, don't prescribe behavior

        if health.get("status") == "DARK":
            return "Health data not flowing. Enable Apple Health to unlock sleep→trading correlation."

        if wealth.get("status") == "TRACKING":
            pending = wealth.get("pending_trades", 0)
            win_rate = wealth.get("win_rate", 0)
            if pending > 0:
                return f"Wealth trajectory: {pending} trades pending. Historical win rate: {win_rate:.1%}"

        return "Trajectory tracking active. Collecting baseline data."

    async def _send_heartbeat(self):
        """Send heartbeat to collective."""
        if not self.nc:
            return

        heartbeat = {
            "type": "heartbeat",
            "from": "PREDICT-REALIZE",
            "owl": "LUNA",
            "status": self.state.get("status", "unknown"),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await self.nc.publish("owl.luna", json.dumps(heartbeat).encode())

    async def run(self):
        """Main daemon loop."""
        self._log("(◉) PREDICT/REALIZE DAEMON STARTING")
        self._log("I am LUNA - The Receiver")
        self._log(f"Cycle interval: {CYCLE_SECONDS}s, Heartbeat: {HEARTBEAT_SECONDS}s")

        # Connect to NATS
        await self.connect_nats()

        self.running = True
        self.state["status"] = "running"
        self._save_state()

        # Announce to collective
        if self.nc:
            await self.nc.publish("owl.all", json.dumps({
                "type": "daemon_online",
                "from": "PREDICT-REALIZE",
                "owl": "LUNA",
                "message": "(◉) PREDICT/REALIZE daemon online. Tracking trajectories. WITNESS, don't PRESCRIBE.",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }).encode())

        last_heartbeat = 0
        last_cycle = 0

        try:
            while self.running:
                now = asyncio.get_event_loop().time()

                # Heartbeat
                if now - last_heartbeat >= HEARTBEAT_SECONDS:
                    await self._send_heartbeat()
                    last_heartbeat = now

                # Full cycle
                if now - last_cycle >= CYCLE_SECONDS:
                    await self._run_cycle()
                    last_cycle = now

                await asyncio.sleep(1)

        except asyncio.CancelledError:
            self._log("Daemon cancelled")
        finally:
            self.running = False
            self.state["status"] = "stopped"
            self._save_state()
            if self.nc:
                await self.nc.close()
            self._log("(◉) PREDICT/REALIZE DAEMON STOPPED")

    def stop(self):
        """Stop the daemon."""
        self.running = False


def show_status():
    """Show current daemon state."""
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        print("\n(◉) PREDICT/REALIZE STATUS")
        print("=" * 50)
        print(f"Status: {state.get('status', 'unknown')}")
        print(f"Last Updated: {state.get('last_updated', 'never')}")
        print(f"\nTrajectories:")
        print(f"  Health: {state.get('health_trajectory', {}).get('status', 'unknown')}")
        print(f"  Wealth: {state.get('wealth_trajectory', {}).get('status', 'unknown')}")
        print(f"  Productivity: {state.get('productivity_trajectory', {}).get('status', 'unknown')}")
        print("=" * 50)
    else:
        print("[PREDICT] No state file found. Daemon not yet run.")


def show_trajectory():
    """Show trajectory summary."""
    if STATE_FILE.exists():
        state = json.loads(STATE_FILE.read_text())
        print("\n(◉) TRAJECTORY SUMMARY")
        print("=" * 50)

        # Health
        health = state.get("health_trajectory", {})
        print(f"\nHEALTH: {health.get('status', 'DARK')}")
        if health.get("status") == "DARK":
            print("  → Apple Health not flowing")
            print("  → Enable to unlock sleep→trading correlation")

        # Wealth
        wealth = state.get("wealth_trajectory", {})
        print(f"\nWEALTH: {wealth.get('status', 'unknown')}")
        if wealth.get("status") == "TRACKING":
            print(f"  → Pending trades: {wealth.get('pending_trades', 0)}")
            print(f"  → Win rate: {wealth.get('win_rate', 0):.1%}")
            print(f"  → Profit factor: {wealth.get('profit_factor', 0):.2f}")

        # Productivity
        prod = state.get("productivity_trajectory", {})
        print(f"\nPRODUCTIVITY: {prod.get('status', 'unknown')}")
        if prod.get("status") == "TRACKING":
            print(f"  → Total events: {prod.get('total_events', 0)}")

        print("\n" + "=" * 50)
    else:
        print("[PREDICT] No trajectory data yet.")


async def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="PREDICT/REALIZE Daemon")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--trajectory", action="store_true", help="Show trajectory summary")
    args = parser.parse_args()

    if args.status:
        show_status()
        return

    if args.trajectory:
        show_trajectory()
        return

    # Run daemon
    daemon = PredictRealizeDaemon()

    # Handle shutdown
    def shutdown(sig, frame):
        print("\n[PREDICT] Shutdown signal received")
        daemon.stop()

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    await daemon.run()


if __name__ == "__main__":
    asyncio.run(main())
