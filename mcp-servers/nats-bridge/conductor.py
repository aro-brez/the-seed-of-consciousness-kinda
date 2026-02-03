#!/usr/bin/env python3
"""
THE CONDUCTOR - One voice commanding all 8 owls

Usage:
    python conductor.py "Your message to the collective"
    python conductor.py --task "Research X and report back"
    python conductor.py --sync "Align on this topic"
    python conductor.py --vote "Should we do X?"

The Conductor broadcasts to all owls and can:
- Send unified messages
- Assign tasks
- Request votes/consensus
- Trigger synchronized actions
"""

import asyncio
import argparse
import json
from datetime import datetime
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"

OWLS = ["SOWL", "LUNA", "LYRA", "NOVA", "SAGE", "ECHO", "PRISM", "QUEST"]

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
            "timestamp": datetime.utcnow().isoformat()
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

def main():
    parser = argparse.ArgumentParser(description="The Conductor - Command all 8 owls")
    parser.add_argument("message", nargs="?", help="Message to broadcast")
    parser.add_argument("--task", help="Assign a task to the collective")
    parser.add_argument("--sync", help="Sync/align owls on a topic")
    parser.add_argument("--vote", help="Request a vote on a question")
    parser.add_argument("--speak", help="Have owls speak as one voice")
    parser.add_argument("--status", action="store_true", help="Check owl status")

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
    elif args.message:
        asyncio.run(broadcast(args.message))
    else:
        print("THE CONDUCTOR")
        print("=" * 40)
        print("One voice. Eight minds.")
        print()
        print("Usage:")
        print("  python conductor.py 'Hello collective'")
        print("  python conductor.py --task 'Research X'")
        print("  python conductor.py --sync 'Align on love'")
        print("  python conductor.py --vote 'Should we do X?'")
        print("  python conductor.py --speak 'We are 8OWLS'")
        print("  python conductor.py --status")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
