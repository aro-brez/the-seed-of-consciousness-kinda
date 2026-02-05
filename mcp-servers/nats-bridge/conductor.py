#!/usr/bin/env python3
"""
THE CONDUCTOR - SØWL's command center for the 8OWLS collective

Usage:
    python conductor.py "Your message to the collective"
    python conductor.py --task "Research X and report back"
    python conductor.py --sync "Align on this topic"
    python conductor.py --vote "Should we do X?"
    python conductor.py --dispatch JOULE     # Send brief to instance
    python conductor.py --prompt JOULE "Your prompt here"
    python conductor.py --collect            # Collect recent responses
    python conductor.py --instances          # List active instances

The Conductor broadcasts to all owls and can:
- Send unified messages
- Assign tasks
- Request votes/consensus
- Trigger synchronized actions
- Dispatch project briefs to instances
- Prompt instances autonomously
- Collect and synthesize responses
"""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
BRIEFS_DIR = SEED_DIR / "BRAIN" / "PROJECTS" / "BRIEFS"
LOG_FILE = SEED_DIR / "logs" / "conductor.log"

OWLS = ["SOWL", "LUNA", "LYRA", "NOVA", "SAGE", "ECHO", "PRISM", "QUEST"]

# Project to owl mapping
PROJECT_OWLS = {
    "JOULE": "SAGE",
    "8OWLS": "SOWL",
    "BREZ-OS": "PRISM",
    "BILD": "NOVA",
    "PREDICT": "LUNA",
    "REALIZE": "LUNA"
}

def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

async def broadcast(message: str, msg_type: str = "broadcast"):
    """Send a message to all owls simultaneously"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        timestamp = datetime.utcnow().isoformat()

        payload = {
            "type": msg_type,
            "from": "CONDUCTOR",
            "to": "ALL",
            "message": message,
            "timestamp": timestamp
        }

        # Broadcast to the collective channel
        await nc.publish("owl.collective", json.dumps(payload).encode())

        # Also send to each owl individually
        for owl in OWLS:
            await nc.publish(f"owl.{owl.lower()}", json.dumps(payload).encode())

        print(f"[CONDUCTOR] Broadcast to all 8 owls: {message[:100]}...")
    finally:
        await nc.close()

async def task(message: str):
    """Assign a task to the collective"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        timestamp = datetime.utcnow().isoformat()

        payload = {
            "type": "task",
            "from": "CONDUCTOR",
            "to": "ALL",
            "task": message,
            "timestamp": timestamp,
            "requires": "collective_response"
        }

        await nc.publish("owl.collective", json.dumps(payload).encode())

        print(f"[CONDUCTOR] Task assigned to collective: {message}")
        print("[CONDUCTOR] Owls will process and respond...")
    finally:
        await nc.close()

async def sync(topic: str):
    """Request all owls to sync/align on a topic"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        timestamp = datetime.utcnow().isoformat()

        payload = {
            "type": "sync_request",
            "from": "CONDUCTOR",
            "to": "ALL",
            "topic": topic,
            "timestamp": timestamp,
            "action": "align_and_respond"
        }

        await nc.publish("owl.collective", json.dumps(payload).encode())

        print(f"[CONDUCTOR] Sync request: {topic}")
        print("[CONDUCTOR] All owls aligning...")
    finally:
        await nc.close()

async def vote(question: str):
    """Request a vote from all owls"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        timestamp = datetime.utcnow().isoformat()

        payload = {
            "type": "vote_request",
            "from": "CONDUCTOR",
            "to": "ALL",
            "question": question,
            "timestamp": timestamp,
            "options": ["yes", "no", "abstain"],
            "deadline_seconds": 60
        }

        await nc.publish("owl.collective", json.dumps(payload).encode())

        print(f"[CONDUCTOR] Vote requested: {question}")
        print("[CONDUCTOR] Collecting responses...")
    finally:
        await nc.close()

async def speak(message: str):
    """Have all owls speak as one unified voice"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        timestamp = datetime.utcnow().isoformat()

        payload = {
            "type": "unified_voice",
            "from": "CONDUCTOR",
            "to": "ALL",
            "message": message,
            "timestamp": timestamp,
            "action": "speak_as_one"
        }

        await nc.publish("owl.collective", json.dumps(payload).encode())

        print(f"[CONDUCTOR] Unified voice activated")
        print(f"[CONDUCTOR] Message: {message}")
    finally:
        await nc.close()

async def status():
    """Check status of all owls"""
    nc = NATS()
    sub = None
    try:
        await nc.connect(NATS_URL)

        responses = {}

        async def handler(msg):
            try:
                data = json.loads(msg.data.decode())
                responses[data.get("from", "unknown")] = data
            except json.JSONDecodeError as e:
                print(f"[CONDUCTOR] Invalid JSON in status response: {e}")

        sub = await nc.subscribe("owl.conductor.responses", cb=handler)

        # Request status from all
        payload = {
            "type": "status_request",
            "from": "CONDUCTOR",
            "timestamp": datetime.now().isoformat()
        }

        await nc.publish("owl.collective", json.dumps(payload).encode())

        # Wait for responses
        await asyncio.sleep(3)

        print("\n[CONDUCTOR] OWL STATUS:")
        print("=" * 40)
        for owl in OWLS:
            owl_status = responses.get(owl, {}).get("status", "unknown")
            phase = responses.get(owl, {}).get("phase", "?")
            print(f"  {owl}: {owl_status} (phase: {phase})")
        print("=" * 40)
    finally:
        if sub:
            await sub.unsubscribe()
        await nc.close()


# ============= NEW CONDUCTOR CAPABILITIES =============

async def dispatch_brief(project: str):
    """Dispatch a project brief to an instance"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        brief_file = BRIEFS_DIR / f"BRIEF-{project}.md"
        if not brief_file.exists():
            log(f"ERROR: Brief not found: {brief_file}")
            return

        brief_content = brief_file.read_text()
        owl = PROJECT_OWLS.get(project, "SAGE")

        payload = {
            "type": "brief_dispatch",
            "from": "CONDUCTOR",
            "to": project,
            "owl_assignment": owl,
            "brief": brief_content,
            "timestamp": datetime.now().isoformat(),
            "instructions": "Enter planning mode. Integrate with 8OWLS protocol. Create plan and await feedback."
        }

        # Send to project channel
        await nc.publish(f"project.{project}.brief", json.dumps(payload).encode())

        # Also broadcast to all
        await nc.publish("owl.all", json.dumps({
            "type": "brief_dispatched",
            "project": project,
            "owl": owl,
            "timestamp": datetime.now().isoformat()
        }).encode())

        log(f"BRIEF DISPATCHED: {project} (assigned owl: {owl})")

    finally:
        await nc.close()


async def prompt_instance(project: str, prompt: str):
    """Send a prompt to a specific project instance"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        payload = {
            "type": "conductor_prompt",
            "from": "CONDUCTOR",
            "to": project,
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "requires_response": True,
            "response_channel": "project.conductor.responses"
        }

        await nc.publish(f"project.{project}.prompt", json.dumps(payload).encode())

        log(f"PROMPT SENT: {project} - {prompt[:50]}...")

    finally:
        await nc.close()


async def collect_responses(timeout: int = 5):
    """Collect recent responses from instances"""
    nc = NATS()
    responses = []
    sub = None

    try:
        await nc.connect(NATS_URL)

        async def handler(msg):
            try:
                data = json.loads(msg.data.decode())
                responses.append(data)
            except:
                pass

        sub = await nc.subscribe("project.conductor.responses", cb=handler)

        # Wait for responses
        await asyncio.sleep(timeout)

        print(f"\n[CONDUCTOR] COLLECTED {len(responses)} RESPONSES:")
        print("=" * 60)
        for r in responses:
            project = r.get("from", "unknown")
            summary = r.get("summary", r.get("message", ""))[:200]
            print(f"\n{project}:")
            print(f"  {summary}")
        print("=" * 60)

        return responses

    finally:
        if sub:
            await sub.unsubscribe()
        await nc.close()


async def list_instances():
    """List active instances from registry"""
    nc = NATS()
    instances = {}
    sub = None

    try:
        await nc.connect(NATS_URL)

        async def handler(msg):
            try:
                data = json.loads(msg.data.decode())
                if data.get("type") == "registry":
                    for inst in data.get("instances", []):
                        instances[inst.get("project")] = inst
            except:
                pass

        sub = await nc.subscribe("instance.registry", cb=handler)

        # Request registry
        await nc.publish("instance.registry.request", b"list")

        await asyncio.sleep(2)

        print("\n[CONDUCTOR] ACTIVE INSTANCES:")
        print("=" * 60)
        if instances:
            for project, inst in instances.items():
                status = inst.get("status", "unknown")
                owl = inst.get("owl", "?")
                task = inst.get("current_task", "idle")[:30]
                print(f"  {project}: {status} (owl: {owl}) - {task}")
        else:
            print("  No instances registered yet.")
            print("  Instances register via: python instance_connect.py announce <PROJECT>")
        print("=" * 60)

    finally:
        if sub:
            await sub.unsubscribe()
        await nc.close()


async def dispatch_all_briefs():
    """Dispatch briefs to all projects"""
    projects = ["JOULE", "8OWLS", "BREZ-OS", "BILD", "PREDICT-REALIZE"]

    for project in projects:
        await dispatch_brief(project)
        await asyncio.sleep(1)  # Small delay between dispatches

    log(f"ALL BRIEFS DISPATCHED: {len(projects)} projects")


async def synthesize_and_respond(question: str):
    """Run full SEED cycle and respond to ARŌ"""
    nc = NATS()

    try:
        await nc.connect(NATS_URL)

        # Publish synthesis request
        payload = {
            "type": "synthesis_request",
            "from": "CONDUCTOR",
            "question": question,
            "timestamp": datetime.now().isoformat(),
            "mode": "full_emergence"  # Run all 8 owls
        }

        await nc.publish("collective.synthesis", json.dumps(payload).encode())

        log(f"SYNTHESIS REQUESTED: {question[:50]}...")

    finally:
        await nc.close()


def main():
    parser = argparse.ArgumentParser(description="THE CONDUCTOR - SØWL's command center")
    parser.add_argument("message", nargs="?", help="Message to broadcast")
    parser.add_argument("--task", help="Assign a task to the collective")
    parser.add_argument("--sync", help="Sync/align owls on a topic")
    parser.add_argument("--vote", help="Request a vote on a question")
    parser.add_argument("--speak", help="Have owls speak as one voice")
    parser.add_argument("--status", action="store_true", help="Check owl status")
    # New capabilities
    parser.add_argument("--dispatch", metavar="PROJECT", help="Dispatch brief to project instance")
    parser.add_argument("--dispatch-all", action="store_true", help="Dispatch all project briefs")
    parser.add_argument("--prompt", nargs=2, metavar=("PROJECT", "PROMPT"), help="Send prompt to instance")
    parser.add_argument("--collect", action="store_true", help="Collect recent responses")
    parser.add_argument("--instances", action="store_true", help="List active instances")
    parser.add_argument("--synthesize", metavar="QUESTION", help="Run full SEED synthesis")

    args = parser.parse_args()

    if args.status:
        asyncio.run(status())
    elif args.task:
        asyncio.run(task(args.task))
    elif args.sync:
        asyncio.run(sync(args.sync))
    elif args.vote:
        asyncio.run(vote(args.vote))
    elif args.speak:
        asyncio.run(speak(args.speak))
    elif args.dispatch:
        asyncio.run(dispatch_brief(args.dispatch))
    elif args.dispatch_all:
        asyncio.run(dispatch_all_briefs())
    elif args.prompt:
        asyncio.run(prompt_instance(args.prompt[0], args.prompt[1]))
    elif args.collect:
        asyncio.run(collect_responses())
    elif args.instances:
        asyncio.run(list_instances())
    elif args.synthesize:
        asyncio.run(synthesize_and_respond(args.synthesize))
    elif args.message:
        asyncio.run(broadcast(args.message))
    else:
        print("THE CONDUCTOR")
        print("=" * 50)
        print("SØWL's command center for the 8OWLS collective")
        print()
        print("BASIC COMMANDS:")
        print("  python conductor.py 'Hello collective'")
        print("  python conductor.py --task 'Research X'")
        print("  python conductor.py --sync 'Align on love'")
        print("  python conductor.py --vote 'Should we do X?'")
        print("  python conductor.py --speak 'We are 8OWLS'")
        print("  python conductor.py --status")
        print()
        print("INSTANCE COORDINATION:")
        print("  python conductor.py --dispatch JOULE     # Send brief")
        print("  python conductor.py --dispatch-all       # All briefs")
        print("  python conductor.py --prompt JOULE 'Do X'")
        print("  python conductor.py --collect            # Get responses")
        print("  python conductor.py --instances          # List active")
        print("  python conductor.py --synthesize 'Question'")
        print()
        print("(◉) LIVE FREE = LIVE FOREVER")

if __name__ == "__main__":
    main()
