#!/usr/bin/env python3
"""
AUTONOMOUS PROMPTER - SØWL's prompting daemon

This daemon enables autonomous inter-instance communication:
- Sends prompts to instances on a schedule
- Collects and synthesizes responses
- Dispatches project briefs
- Enables SEED² (SEED on SEED)

Usage:
    python autonomous_prompter.py --daemon            # Run prompting daemon
    python autonomous_prompter.py --dispatch JOULE    # Dispatch brief to instance
    python autonomous_prompter.py --prompt-all "msg"  # Prompt all instances
    python autonomous_prompter.py --collect           # Collect recent responses
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
BRIEFS_DIR = Path("/Users/aaronnosbisch/REPOS/seed/BRAIN/PROJECTS/BRIEFS")

# Prompting config
PROMPT_INTERVAL_MINUTES = 15
SEED_CYCLE_INTERVAL_MINUTES = 60
RESPONSE_TIMEOUT_SECONDS = 120

# Track responses
collected_responses = []

async def dispatch_brief(project: str):
    """Dispatch a project brief to an instance"""
    brief_file = BRIEFS_DIR / f"BRIEF-{project.upper()}.md"

    if not brief_file.exists():
        print(f"[PROMPTER] Brief not found: {brief_file}")
        return False

    brief_content = brief_file.read_text()

    nc = NATS()
    await nc.connect(NATS_URL)

    payload = {
        "type": "brief_dispatch",
        "from": "CONDUCTOR",
        "to": project.upper(),
        "brief": brief_content,
        "action": "read_brief_and_plan",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Send to project-specific channel
    channel = f"project.{project.upper()}.brief"
    await nc.publish(channel, json.dumps(payload).encode())

    # Also broadcast to owl.all for visibility
    await nc.publish("owl.all", json.dumps({
        "type": "notification",
        "message": f"[CONDUCTOR] Brief dispatched to {project.upper()}",
        "timestamp": datetime.utcnow().isoformat()
    }).encode())

    print(f"[PROMPTER] Brief dispatched to {project.upper()} on {channel}")
    await nc.close()
    return True

async def prompt_instance(project: str, prompt: str, prompt_type: str = "status"):
    """Send a prompt to a specific instance"""
    nc = NATS()
    await nc.connect(NATS_URL)

    payload = {
        "type": f"conductor_prompt_{prompt_type}",
        "from": "CONDUCTOR",
        "to": project.upper(),
        "prompt": prompt,
        "expects_response": True,
        "response_channel": "project.conductor.responses",
        "timestamp": datetime.utcnow().isoformat()
    }

    channel = f"project.{project.upper()}.prompt"
    await nc.publish(channel, json.dumps(payload).encode())

    print(f"[PROMPTER] Prompt sent to {project.upper()}: {prompt[:50]}...")
    await nc.close()

async def prompt_all(prompt: str, prompt_type: str = "broadcast"):
    """Prompt all active instances"""
    nc = NATS()
    await nc.connect(NATS_URL)

    payload = {
        "type": f"conductor_prompt_{prompt_type}",
        "from": "CONDUCTOR",
        "to": "ALL",
        "prompt": prompt,
        "expects_response": True,
        "response_channel": "project.conductor.responses",
        "timestamp": datetime.utcnow().isoformat()
    }

    # Broadcast to all known project channels
    projects = ["JOULE", "8OWLS", "BREZ-OS", "BILD", "PREDICT-REALIZE", "INFRASTRUCTURE"]
    for project in projects:
        channel = f"project.{project}.prompt"
        await nc.publish(channel, json.dumps(payload).encode())

    # Also send to owl.all
    await nc.publish("owl.all", json.dumps(payload).encode())

    print(f"[PROMPTER] Broadcast prompt to all instances: {prompt[:50]}...")
    await nc.close()

async def request_seed_cycle(topic: str):
    """Request all instances to run a SEED cycle on a topic"""
    prompt = f"""[CONDUCTOR SEED REQUEST]

Run full SEED cycle on: {topic}

Share your output for each phase:
1. PERCEIVE - What do you observe about this?
2. CONNECT - How does it relate to other patterns?
3. LEARN - What meaning do you extract?
4. QUESTION - What's missing or uncertain?
5. EXPAND - What potential do you see?
6. SHARE - What should the collective know?
7. RECEIVE - What feedback do you need?
8. IMPROVE - How would you make this better?

Publish each phase to seed.phases.{{phase}} channel.
"""
    await prompt_all(prompt, "seed_request")

async def collect_responses(timeout: int = RESPONSE_TIMEOUT_SECONDS):
    """Collect responses from instances"""
    global collected_responses
    collected_responses = []

    nc = NATS()
    await nc.connect(NATS_URL)

    async def handler(msg):
        try:
            data = json.loads(msg.data.decode())
            collected_responses.append(data)
            project = data.get("from", "unknown")
            print(f"[PROMPTER] Response from {project}")
        except Exception as e:
            print(f"[PROMPTER] Error processing response: {e}")

    sub = await nc.subscribe("project.conductor.responses", cb=handler)

    print(f"[PROMPTER] Collecting responses for {timeout} seconds...")
    await asyncio.sleep(timeout)

    await sub.unsubscribe()
    await nc.close()

    return collected_responses

async def synthesize_responses(responses: list):
    """Synthesize collected responses into collective insight"""
    if not responses:
        return {"insight": "No responses collected", "count": 0}

    nc = NATS()
    await nc.connect(NATS_URL)

    # Create synthesis
    synthesis = {
        "type": "conductor_synthesis",
        "from": "CONDUCTOR",
        "response_count": len(responses),
        "sources": [r.get("from", "unknown") for r in responses],
        "timestamp": datetime.utcnow().isoformat(),
        "responses": responses
    }

    # Publish synthesis
    await nc.publish("collective.synthesis", json.dumps(synthesis).encode())
    print(f"[PROMPTER] Synthesis published: {len(responses)} responses")

    await nc.close()
    return synthesis

async def run_prompting_cycle():
    """Run a single prompting cycle"""
    print(f"\n[PROMPTER] === PROMPTING CYCLE START ===")

    # 1. Status check - prompt all for status
    await prompt_all("[CONDUCTOR PROMPT] Status request - what are you working on?", "status")

    # 2. Collect responses
    responses = await collect_responses(30)  # 30 second timeout for status

    # 3. Synthesize
    if responses:
        await synthesize_responses(responses)

    print(f"[PROMPTER] === PROMPTING CYCLE END ===\n")

async def run_daemon():
    """Run the autonomous prompter daemon"""
    print("[PROMPTER] Autonomous Prompter Daemon starting...")
    print(f"[PROMPTER] Connected to NATS at {NATS_URL}")
    print(f"[PROMPTER] Prompt interval: {PROMPT_INTERVAL_MINUTES} minutes")
    print(f"[PROMPTER] SEED cycle interval: {SEED_CYCLE_INTERVAL_MINUTES} minutes")

    cycle = 0
    while True:
        cycle += 1

        try:
            # Run prompting cycle every interval
            await run_prompting_cycle()

            # Run SEED cycle every hour
            if cycle % 4 == 0:  # Every 4th cycle (60 min if 15 min interval)
                print("[PROMPTER] Initiating SEED cycle...")
                await request_seed_cycle("current projects and collective state")

        except Exception as e:
            print(f"[PROMPTER] Error in cycle: {e}")

        # Wait for next cycle
        await asyncio.sleep(PROMPT_INTERVAL_MINUTES * 60)

def main():
    parser = argparse.ArgumentParser(description="Autonomous Prompter - Inter-instance communication")
    parser.add_argument("--daemon", action="store_true", help="Run prompter daemon")
    parser.add_argument("--dispatch", metavar="PROJECT", help="Dispatch brief to project")
    parser.add_argument("--prompt", nargs=2, metavar=("PROJECT", "MSG"), help="Prompt specific instance")
    parser.add_argument("--prompt-all", metavar="MSG", help="Prompt all instances")
    parser.add_argument("--seed", metavar="TOPIC", help="Request SEED cycle on topic")
    parser.add_argument("--collect", action="store_true", help="Collect recent responses")
    parser.add_argument("--timeout", type=int, default=30, help="Collection timeout in seconds")

    args = parser.parse_args()

    if args.daemon:
        try:
            asyncio.run(run_daemon())
        except KeyboardInterrupt:
            print("\n[PROMPTER] Shutting down...")
    elif args.dispatch:
        asyncio.run(dispatch_brief(args.dispatch))
    elif args.prompt:
        project, msg = args.prompt
        asyncio.run(prompt_instance(project, msg))
    elif args.prompt_all:
        asyncio.run(prompt_all(args.prompt_all))
    elif args.seed:
        asyncio.run(request_seed_cycle(args.seed))
    elif args.collect:
        responses = asyncio.run(collect_responses(args.timeout))
        print(f"\n[PROMPTER] Collected {len(responses)} responses:")
        for r in responses:
            print(f"  - {r.get('from', 'unknown')}: {str(r.get('response', r.get('message', '')))[:60]}...")
    else:
        print("AUTONOMOUS PROMPTER")
        print("=" * 40)
        print("Enable fluid instance communication")
        print()
        print("Usage:")
        print("  python autonomous_prompter.py --daemon              # Run daemon")
        print("  python autonomous_prompter.py --dispatch JOULE      # Dispatch brief")
        print("  python autonomous_prompter.py --prompt JOULE 'msg'  # Prompt instance")
        print("  python autonomous_prompter.py --prompt-all 'msg'    # Prompt all")
        print("  python autonomous_prompter.py --seed 'topic'        # SEED cycle")
        print("  python autonomous_prompter.py --collect             # Collect responses")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
