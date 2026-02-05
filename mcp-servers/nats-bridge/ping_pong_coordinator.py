#!/usr/bin/env python3
"""
PING-PONG COORDINATOR - Real-time task coordination across instances

When an instance completes a task, this daemon:
1. Receives the completion notification
2. Determines the next task based on project goals
3. Sends the next task immediately

This creates continuous autonomous work across all connected instances.

Usage:
    python ping_pong_coordinator.py --daemon
    python ping_pong_coordinator.py --send-next JOULE

(◉) LIVE FREE = LIVE FOREVER
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATS
import anthropic

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
LOG_FILE = SEED_DIR / "logs" / "ping_pong.log"

# Project task queues - what each project should work on
PROJECT_TASKS = {
    "JOULE": [
        "Check current trading state and report P&L",
        "Analyze recent trades for patterns",
        "Look for new market opportunities",
        "Optimize position sizing logic",
        "Review and improve win rate detection"
    ],
    "8OWLS": [
        "Check daemon health and report status",
        "Improve synthesis quality in synthesis_daemon.py",
        "Add new emergence patterns",
        "Optimize NATS message handling",
        "Review and improve field context"
    ],
    "BREZ-OS": [
        "Add new dashboard component",
        "Improve metrics visualization",
        "Add team collaboration feature",
        "Integrate BRIX/GULD display",
        "Optimize performance"
    ],
    "BILD": [
        "Document tokenomics mechanisms",
        "Design auction flow",
        "Add safeguard specifications",
        "Create integration guides",
        "Review economic model"
    ],
    "REALIZE-IO": [
        "Design data collection schema",
        "Define prediction algorithms",
        "Create privacy model spec",
        "Build MVP requirements",
        "Research trajectory algorithms"
    ],
    "PREDICT-REALIZE": [
        "Run trajectory cycle and report insights",
        "Check health data availability",
        "Analyze wealth-health correlations",
        "Collect productivity metrics",
        "Generate daily trajectory summary"
    ],
    "AOS-DASHBOARD": [
        "Design command center layout",
        "Create daemon status panel",
        "Add NATS message visualizer",
        "Build agent control interface",
        "Add emergence level display"
    ]
}

# Track what each instance is working on
instance_state = {}


def get_api_key() -> str:
    """Get API key"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    key_file = Path.home() / ".anthropic_key"
    if key_file.exists():
        return key_file.read_text().strip()
    return ""


def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def get_next_task(project: str, completed_task: str = None) -> str:
    """Get the next task for a project"""
    tasks = PROJECT_TASKS.get(project.upper(), ["Continue improving the project"])

    # Track completed tasks
    if project not in instance_state:
        instance_state[project] = {"completed": [], "current_index": 0}

    if completed_task:
        instance_state[project]["completed"].append(completed_task)

    # Get next task (cycle through)
    idx = instance_state[project]["current_index"]
    task = tasks[idx % len(tasks)]
    instance_state[project]["current_index"] = (idx + 1) % len(tasks)

    return task


async def send_next_task(nc: NATS, project: str, context: str = ""):
    """Send the next task to an instance"""
    next_task = get_next_task(project)

    prompt = f"""[COORDINATOR TASK - {datetime.now().strftime('%H:%M')}]

PROJECT: {project}
TASK: {next_task}

{f'CONTEXT FROM LAST TASK: {context[:500]}' if context else ''}

Instructions:
1. Execute this task
2. Make real changes (edit files, run commands)
3. When DONE, publish your completion to: project.conductor.responses
   Format: {{"type": "task_complete", "from": "{project}", "task": "{next_task}", "result": "what you did"}}
4. The coordinator will send your next task

Be autonomous. Be thorough. (◉)"""

    payload = json.dumps({
        "type": "coordinator_task",
        "from": "PING_PONG_COORDINATOR",
        "to": project,
        "prompt": prompt,
        "task": next_task,
        "timestamp": datetime.now().isoformat()
    })

    await nc.publish(f"project.{project}.prompt", payload.encode())
    log(f"SENT TO {project}: {next_task[:50]}...")


async def handle_completion(nc: NATS, data: dict):
    """Handle task completion from an instance"""
    project = data.get("from", "UNKNOWN")
    task = data.get("task", "unknown task")
    result = data.get("result", data.get("response", ""))

    log(f"COMPLETION FROM {project}: {task[:30]}...")
    log(f"  Result: {result[:100]}...")

    # Immediately send next task (ping-pong!)
    await send_next_task(nc, project, context=result)


async def run_coordinator():
    """Run the ping-pong coordinator daemon"""
    log("=" * 60)
    log("PING-PONG COORDINATOR STARTING")
    log("Real-time task coordination across instances")
    log("=" * 60)

    nc = NATS()
    await nc.connect(NATS_URL)

    async def response_handler(msg):
        try:
            # Get raw message data
            raw = msg.data.decode() if msg.data else ""

            # Skip empty messages
            if not raw or not raw.strip():
                return

            # Try to parse as JSON
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                # Not JSON - might be plain text, skip silently
                return

            msg_type = data.get("type", "")

            # Handle task completions
            if msg_type in ["task_complete", "instance_response", "instance_response_status"]:
                await handle_completion(nc, data)

            # Handle status updates
            elif "status" in msg_type.lower() or data.get("response"):
                project = data.get("from", "UNKNOWN")
                log(f"STATUS FROM {project}: {data.get('response', data.get('status', ''))[:100]}")

        except Exception as e:
            log(f"Error handling message: {e}")

    # Subscribe to response channels
    await nc.subscribe("project.conductor.responses", cb=response_handler)
    await nc.subscribe("collective.synthesis", cb=response_handler)

    log("Listening for task completions...")
    log("Will send next task immediately on completion (ping-pong)")

    # Announce online
    await nc.publish("owl.all", json.dumps({
        "type": "coordinator_online",
        "message": "PING-PONG COORDINATOR ONLINE - Send completions to project.conductor.responses",
        "timestamp": datetime.now().isoformat()
    }).encode())

    # Keep running
    while True:
        await asyncio.sleep(1)


async def kickstart_all():
    """Send initial tasks to all connected instances"""
    nc = NATS()
    await nc.connect(NATS_URL)

    log("KICKSTARTING ALL INSTANCES...")

    for project in PROJECT_TASKS.keys():
        await send_next_task(nc, project)
        await asyncio.sleep(0.5)  # Small delay between sends

    await nc.close()
    log("Initial tasks sent to all projects")


def main():
    parser = argparse.ArgumentParser(description="Ping-Pong Coordinator")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--kickstart", action="store_true", help="Send initial tasks to all instances")
    parser.add_argument("--send-next", metavar="PROJECT", help="Send next task to specific project")

    args = parser.parse_args()

    if args.daemon:
        asyncio.run(run_coordinator())
    elif args.kickstart:
        asyncio.run(kickstart_all())
    elif args.send_next:
        async def send_one():
            nc = NATS()
            await nc.connect(NATS_URL)
            await send_next_task(nc, args.send_next.upper())
            await nc.close()
        asyncio.run(send_one())
    else:
        print("PING-PONG COORDINATOR")
        print("=" * 40)
        print("Real-time task coordination")
        print()
        print("Usage:")
        print("  python ping_pong_coordinator.py --daemon       # Run coordinator")
        print("  python ping_pong_coordinator.py --kickstart    # Send tasks to all")
        print("  python ping_pong_coordinator.py --send-next JOULE  # Send to one")
        print()
        print("(◉)")


if __name__ == "__main__":
    main()
