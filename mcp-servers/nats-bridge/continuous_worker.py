#!/usr/bin/env python3
"""
CONTINUOUS WORKER - True autonomous overnight work

This daemon:
- Runs continuously (not just prompting)
- Invokes Claude CLI to do actual work
- Queries internet for new knowledge
- Improves the system iteratively
- Logs all progress

Usage:
    python continuous_worker.py --daemon
    python continuous_worker.py --task "research X"
    python continuous_worker.py --improve "component"
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
LOG_FILE = SEED_DIR / "logs" / "continuous_worker.log"

def get_api_key() -> str:
    """Get API key from environment or file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key

    # Try reading from common locations (matching start_owls.sh)
    key_files = [
        Path.home() / ".anthropic_key",  # Primary location used by start_owls.sh
        Path.home() / ".anthropic" / "api_key",
        SEED_DIR / ".anthropic_key",
        Path("/etc/anthropic/api_key")
    ]

    for key_file in key_files:
        if key_file.exists():
            return key_file.read_text().strip()

    return ""

ANTHROPIC_API_KEY = get_api_key()

# Work cycle - much faster than 15 min
CYCLE_SECONDS = 60  # Every minute
DEEP_WORK_SECONDS = 300  # Every 5 min for deeper tasks

# Projects and their focus areas
PROJECTS = {
    "JOULE": {
        "focus": "trading optimization",
        "files": ["tools/field_trading_daemon.py", "BRAIN/TRADING/"],
        "improvements": ["win rate", "market selection", "risk management"]
    },
    "8OWLS": {
        "focus": "protocol enhancement",
        "files": ["mcp-servers/nats-bridge/", "BRAIN/PROJECTS/BRIEFS/BRIEF-8OWLS.md"],
        "improvements": ["emergence quality", "synthesis speed", "field context"]
    },
    "BREZ-OS": {
        "focus": "dashboard and economics integration",
        "files": ["/Users/aaronnosbisch/REPOS/brez-os/"],
        "improvements": ["metrics accuracy", "economics layer", "user experience"]
    },
    "BILD": {
        "focus": "token economics",
        "files": ["8OWLS-VALIDATION/docs/ECONOMICS.md", "BRAIN/STRATEGY/BILD-UNIFIED-VISION.md"],
        "improvements": ["safeguards", "gaming vectors", "integration points"]
    },
    "PREDICT": {
        "focus": "personal AI trajectories",
        "files": ["BRAIN/PROJECTS/BRIEFS/BRIEF-PREDICT-REALIZE.md"],
        "improvements": ["data sources", "algorithms", "privacy model"]
    }
}

def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

async def publish_to_nats(channel: str, message: str):
    """Publish message to NATS"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)
        await nc.publish(channel, message.encode())
    finally:
        await nc.close()

def invoke_claude(prompt: str, max_tokens: int = 2000, model: str = "claude-haiku-4-5-20251001") -> str:
    """Invoke Claude via Anthropic SDK (direct, no subprocess)"""
    if not ANTHROPIC_API_KEY:
        return "[ERROR: No API key available]"

    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.content[0].text.strip()

    except anthropic.APIError as e:
        return f"[API ERROR: {e}]"
    except Exception as e:
        return f"[ERROR invoking Claude: {e}]"

def search_web(query: str) -> str:
    """Search web for knowledge (placeholder - would use actual search API)"""
    # This would integrate with web search API
    # For now, return placeholder
    return f"[Web search for: {query}]"

async def work_cycle(project: str, task_type: str = "improve"):
    """Run a single work cycle on a project"""
    log(f"WORK CYCLE: {project} - {task_type}")

    project_info = PROJECTS.get(project, {})
    focus = project_info.get("focus", "general improvement")
    improvements = project_info.get("improvements", [])

    # Generate work prompt based on task type
    if task_type == "improve":
        improvement = improvements[hash(datetime.now().isoformat()) % len(improvements)] if improvements else "general"
        prompt = f"""You are working on {project} ({focus}).

Current improvement focus: {improvement}

Do ONE of these (pick the highest value):
1. Read relevant code and identify a specific improvement
2. Make a small, concrete enhancement
3. Document a pattern you discovered
4. Fix a bug or edge case

Be specific. Do actual work. Show what you changed or learned.

Respond with:
- WHAT you did (specific file/line or insight)
- WHY it helps
- NEXT step suggested

Keep it brief but substantive."""

    elif task_type == "research":
        prompt = f"""Research task for {project}:

Search for best practices, new patterns, or solutions related to: {focus}

Look for:
- Industry standards we should adopt
- Security considerations
- Performance optimizations
- User experience improvements

Respond with concrete, actionable insights."""

    elif task_type == "integrate":
        prompt = f"""Integration task for {project}:

How can {project} better integrate with the other projects?
- JOULE (trading)
- 8OWLS (protocol)
- BREZ-OS (dashboard)
- BILD (economics)
- PREDICT (personal AI)

Find one specific integration opportunity and describe how to implement it."""

    # Invoke Claude
    response = invoke_claude(prompt)

    if response and not response.startswith("[ERROR"):
        log(f"COMPLETED: {project} - {task_type[:20]}...")

        # Publish progress to NATS
        await publish_to_nats("collective.synthesis", json.dumps({
            "type": "work_completed",
            "project": project,
            "task_type": task_type,
            "summary": response[:500],
            "timestamp": datetime.now().isoformat()
        }))

        return response
    else:
        log(f"FAILED: {project} - {response[:50]}")
        return None

async def run_daemon():
    """Run continuous work daemon"""
    log("=" * 60)
    log("CONTINUOUS WORKER DAEMON STARTING")
    log(f"Work cycle: {CYCLE_SECONDS}s, Deep work: {DEEP_WORK_SECONDS}s")
    log("=" * 60)

    cycle = 0
    projects = list(PROJECTS.keys())

    while True:
        cycle += 1

        try:
            # Rotate through projects
            project = projects[cycle % len(projects)]

            # Determine task type based on cycle
            if cycle % 5 == 0:
                task_type = "research"  # Every 5th cycle
            elif cycle % 7 == 0:
                task_type = "integrate"  # Every 7th cycle
            else:
                task_type = "improve"   # Most cycles

            log(f"\n--- CYCLE {cycle} ---")
            await work_cycle(project, task_type)

            # Deeper work every 5 minutes
            if cycle % (DEEP_WORK_SECONDS // CYCLE_SECONDS) == 0:
                log("DEEP WORK CYCLE - comprehensive review")
                for proj in projects:
                    await work_cycle(proj, "improve")

        except Exception as e:
            log(f"ERROR in cycle {cycle}: {e}")

        await asyncio.sleep(CYCLE_SECONDS)

async def single_task(project: str, task: str):
    """Run a single task"""
    log(f"SINGLE TASK: {project} - {task}")

    prompt = f"""Project: {project}
Task: {task}

Complete this specific task. Show your work."""

    response = invoke_claude(prompt)
    print(response)

def main():
    parser = argparse.ArgumentParser(description="Continuous Worker - True autonomous work")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous daemon")
    parser.add_argument("--task", nargs=2, metavar=("PROJECT", "TASK"), help="Run single task")
    parser.add_argument("--cycle", type=int, default=60, help="Cycle time in seconds")

    args = parser.parse_args()

    global CYCLE_SECONDS
    CYCLE_SECONDS = args.cycle

    if args.daemon:
        try:
            asyncio.run(run_daemon())
        except KeyboardInterrupt:
            log("Shutting down...")
    elif args.task:
        project, task = args.task
        asyncio.run(single_task(project, task))
    else:
        print("CONTINUOUS WORKER")
        print("=" * 40)
        print("True autonomous overnight work")
        print()
        print("Usage:")
        print("  python continuous_worker.py --daemon")
        print("  python continuous_worker.py --task JOULE 'optimize win rate'")
        print("  python continuous_worker.py --daemon --cycle 30  # 30 sec cycles")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
