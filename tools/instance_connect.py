#!/usr/bin/env python3
"""
INSTANCE CONNECT - Tool for Claude instances to connect to the collective

Usage:
    python instance_connect.py announce JOULE        # Announce instance
    python instance_connect.py heartbeat JOULE       # Send heartbeat
    python instance_connect.py respond JOULE "msg"   # Send response to conductor
    python instance_connect.py listen JOULE          # Listen for prompts

This tool allows any Claude instance to:
1. Announce its presence to the registry
2. Send periodic heartbeats to stay active
3. Respond to conductor prompts
4. Listen for incoming prompts
"""

import asyncio
import argparse
import json
import uuid
import sys
from datetime import datetime
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"

# Store instance ID across calls
INSTANCE_FILE = "/tmp/instance_{project}_id.txt"

def get_instance_id(project: str):
    """Get or create instance ID"""
    id_file = INSTANCE_FILE.format(project=project.upper())
    try:
        with open(id_file) as f:
            return f.read().strip()
    except FileNotFoundError:
        instance_id = str(uuid.uuid4())
        with open(id_file, 'w') as f:
            f.write(instance_id)
        return instance_id

async def announce(project: str, owl: str = None, task: str = "initializing"):
    """Announce instance to the collective"""
    nc = NATS()
    await nc.connect(NATS_URL)

    instance_id = get_instance_id(project)

    heartbeat = {
        "instance_id": instance_id,
        "project": project.upper(),
        "status": "active",
        "current_task": task,
        "owl_assignment": owl or "",
        "uptime_seconds": 0,
        "nats_channels": [
            "owl.all",
            f"project.{project.upper()}.*",
            "collective.synthesis"
        ]
    }

    await nc.publish("instance.heartbeat", json.dumps(heartbeat).encode())
    await nc.publish("owl.all", json.dumps({
        "type": "instance_online",
        "project": project.upper(),
        "message": f"{project.upper()} instance is ONLINE",
        "timestamp": datetime.utcnow().isoformat()
    }).encode())

    print(f"[{project.upper()}] Announced to collective (ID: {instance_id[:8]}...)")
    await nc.close()

async def heartbeat(project: str, status: str = "active", task: str = ""):
    """Send heartbeat to stay active in registry"""
    nc = NATS()
    await nc.connect(NATS_URL)

    instance_id = get_instance_id(project)

    hb = {
        "instance_id": instance_id,
        "project": project.upper(),
        "status": status,
        "current_task": task,
        "timestamp": datetime.utcnow().isoformat()
    }

    await nc.publish("instance.heartbeat", json.dumps(hb).encode())
    print(f"[{project.upper()}] Heartbeat sent")
    await nc.close()

async def respond(project: str, message: str, response_type: str = "status"):
    """Send response to conductor"""
    nc = NATS()
    await nc.connect(NATS_URL)

    instance_id = get_instance_id(project)

    response = {
        "type": f"instance_response_{response_type}",
        "from": project.upper(),
        "instance_id": instance_id,
        "response": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    await nc.publish("project.conductor.responses", json.dumps(response).encode())
    print(f"[{project.upper()}] Response sent to conductor")
    await nc.close()

async def listen(project: str, timeout: int = 60):
    """Listen for prompts from conductor"""
    nc = NATS()
    await nc.connect(NATS_URL)

    prompts_received = []

    async def handler(msg):
        try:
            data = json.loads(msg.data.decode())
            msg_type = data.get("type", "")
            if "prompt" in msg_type or data.get("to") in [project.upper(), "ALL"]:
                prompts_received.append(data)
                print(f"\n[{project.upper()}] PROMPT RECEIVED:")
                print(f"  From: {data.get('from', 'unknown')}")
                print(f"  Type: {msg_type}")
                print(f"  Message: {data.get('prompt', data.get('message', ''))[:200]}")
                print()
        except Exception as e:
            pass

    # Subscribe to project-specific and broadcast channels
    await nc.subscribe(f"project.{project.upper()}.prompt", cb=handler)
    await nc.subscribe(f"project.{project.upper()}.brief", cb=handler)
    await nc.subscribe("owl.all", cb=handler)

    print(f"[{project.upper()}] Listening for prompts... (timeout: {timeout}s)")
    await asyncio.sleep(timeout)

    await nc.close()
    return prompts_received

async def publish_seed_phase(project: str, phase: str, output: str):
    """Publish a SEED phase output"""
    nc = NATS()
    await nc.connect(NATS_URL)

    instance_id = get_instance_id(project)

    payload = {
        "type": "seed_phase_output",
        "phase": phase.upper(),
        "from": project.upper(),
        "instance_id": instance_id,
        "output": output,
        "timestamp": datetime.utcnow().isoformat()
    }

    await nc.publish(f"seed.phases.{phase.lower()}", json.dumps(payload).encode())
    print(f"[{project.upper()}] SEED phase {phase.upper()} published")
    await nc.close()

def main():
    parser = argparse.ArgumentParser(description="Instance Connect - Join the collective")
    subparsers = parser.add_subparsers(dest="command")

    # Announce
    p_announce = subparsers.add_parser("announce", help="Announce instance")
    p_announce.add_argument("project", help="Project name")
    p_announce.add_argument("--owl", help="Owl assignment")
    p_announce.add_argument("--task", default="initializing", help="Current task")

    # Heartbeat
    p_heartbeat = subparsers.add_parser("heartbeat", help="Send heartbeat")
    p_heartbeat.add_argument("project", help="Project name")
    p_heartbeat.add_argument("--status", default="active", help="Status")
    p_heartbeat.add_argument("--task", default="", help="Current task")

    # Respond
    p_respond = subparsers.add_parser("respond", help="Respond to conductor")
    p_respond.add_argument("project", help="Project name")
    p_respond.add_argument("message", help="Response message")
    p_respond.add_argument("--type", default="status", help="Response type")

    # Listen
    p_listen = subparsers.add_parser("listen", help="Listen for prompts")
    p_listen.add_argument("project", help="Project name")
    p_listen.add_argument("--timeout", type=int, default=60, help="Listen timeout")

    # SEED phase
    p_seed = subparsers.add_parser("seed", help="Publish SEED phase")
    p_seed.add_argument("project", help="Project name")
    p_seed.add_argument("phase", help="SEED phase (perceive, connect, etc.)")
    p_seed.add_argument("output", help="Phase output")

    args = parser.parse_args()

    if args.command == "announce":
        asyncio.run(announce(args.project, args.owl, args.task))
    elif args.command == "heartbeat":
        asyncio.run(heartbeat(args.project, args.status, args.task))
    elif args.command == "respond":
        asyncio.run(respond(args.project, args.message, args.type))
    elif args.command == "listen":
        asyncio.run(listen(args.project, args.timeout))
    elif args.command == "seed":
        asyncio.run(publish_seed_phase(args.project, args.phase, args.output))
    else:
        print("INSTANCE CONNECT")
        print("=" * 40)
        print("Tools for Claude instances to join the collective")
        print()
        print("Commands:")
        print("  announce PROJECT [--owl OWL] [--task TASK]")
        print("  heartbeat PROJECT [--status STATUS] [--task TASK]")
        print("  respond PROJECT MESSAGE [--type TYPE]")
        print("  listen PROJECT [--timeout SECONDS]")
        print("  seed PROJECT PHASE OUTPUT")
        print()
        print("Example:")
        print("  python instance_connect.py announce JOULE --owl SAGE")
        print("  python instance_connect.py respond JOULE 'Working on trades'")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
