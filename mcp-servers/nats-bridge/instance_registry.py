#!/usr/bin/env python3
"""
INSTANCE REGISTRY - Track all active Claude instances

This daemon:
- Receives heartbeats from Claude instances
- Maintains registry of active instances
- Announces discoveries and departures
- Provides instance lookup for conductor

Channels:
- instance.heartbeat    - Receive heartbeats
- instance.registry     - Publish current registry
- instance.discovery    - Announce new instances
- instance.departure    - Announce departures

Usage:
    python instance_registry.py --daemon  # Run as daemon
    python instance_registry.py --list    # List active instances
    python instance_registry.py --announce PROJECT_NAME  # Announce presence
"""

import asyncio
import argparse
import json
import uuid
from datetime import datetime, timedelta
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"

# Instance timeout - if no heartbeat for this long, consider offline
TIMEOUT_SECONDS = 120

# Registry state
instances = {}

async def handle_heartbeat(msg):
    """Process incoming heartbeat from an instance"""
    global instances
    try:
        data = json.loads(msg.data.decode())
        instance_id = data.get("instance_id")
        project = data.get("project", "unknown")
        status = data.get("status", "active")

        is_new = instance_id not in instances

        instances[instance_id] = {
            "instance_id": instance_id,
            "project": project,
            "status": status,
            "current_task": data.get("current_task", ""),
            "owl_assignment": data.get("owl_assignment", ""),
            "uptime_seconds": data.get("uptime_seconds", 0),
            "last_heartbeat": datetime.utcnow().isoformat(),
            "nats_channels": data.get("nats_channels", [])
        }

        if is_new:
            # Announce new instance
            nc = NATS()
            await nc.connect(NATS_URL)
            await nc.publish("instance.discovery", json.dumps({
                "type": "discovery",
                "instance_id": instance_id,
                "project": project,
                "timestamp": datetime.utcnow().isoformat()
            }).encode())
            await nc.close()
            print(f"[REGISTRY] New instance discovered: {project} ({instance_id[:8]}...)")

    except Exception as e:
        print(f"[REGISTRY] Error processing heartbeat: {e}")

async def cleanup_stale():
    """Remove instances that haven't sent heartbeats"""
    global instances
    nc = NATS()
    await nc.connect(NATS_URL)

    now = datetime.utcnow()
    stale = []

    for instance_id, data in list(instances.items()):
        last = datetime.fromisoformat(data["last_heartbeat"])
        if (now - last).total_seconds() > TIMEOUT_SECONDS:
            stale.append(instance_id)

    for instance_id in stale:
        project = instances[instance_id].get("project", "unknown")
        del instances[instance_id]

        # Announce departure
        await nc.publish("instance.departure", json.dumps({
            "type": "departure",
            "instance_id": instance_id,
            "project": project,
            "reason": "timeout",
            "timestamp": datetime.utcnow().isoformat()
        }).encode())
        print(f"[REGISTRY] Instance departed (timeout): {project} ({instance_id[:8]}...)")

    await nc.close()

async def publish_registry():
    """Publish current registry state"""
    nc = NATS()
    await nc.connect(NATS_URL)

    await nc.publish("instance.registry", json.dumps({
        "type": "registry",
        "instances": list(instances.values()),
        "count": len(instances),
        "timestamp": datetime.utcnow().isoformat()
    }).encode())

    await nc.close()

async def run_daemon():
    """Run the registry daemon"""
    nc = NATS()
    await nc.connect(NATS_URL)

    print("[REGISTRY] Instance Registry Daemon starting...")
    print(f"[REGISTRY] Connected to NATS at {NATS_URL}")

    # Subscribe to heartbeats
    await nc.subscribe("instance.heartbeat", cb=handle_heartbeat)
    print("[REGISTRY] Listening for heartbeats on instance.heartbeat")

    # Main loop
    cycle = 0
    while True:
        cycle += 1

        # Cleanup stale instances every 30 seconds
        if cycle % 3 == 0:
            await cleanup_stale()

        # Publish registry every 10 seconds
        await publish_registry()

        # Status report every minute
        if cycle % 6 == 0:
            active = [f"{i['project']}({i['status']})" for i in instances.values()]
            print(f"[REGISTRY] Active: {len(instances)} instances - {', '.join(active) or 'none'}")

        await asyncio.sleep(10)

async def list_instances():
    """List all active instances"""
    nc = NATS()
    registry_data = None

    async def handler(msg):
        nonlocal registry_data
        registry_data = json.loads(msg.data.decode())

    await nc.connect(NATS_URL)
    sub = await nc.subscribe("instance.registry", cb=handler)

    # Wait for registry broadcast
    await asyncio.sleep(2)
    await sub.unsubscribe()
    await nc.close()

    if registry_data:
        print("\n[REGISTRY] ACTIVE INSTANCES:")
        print("=" * 60)
        for inst in registry_data.get("instances", []):
            print(f"  {inst['project']:20} | {inst['status']:10} | {inst.get('current_task', '-')[:25]}")
        print("=" * 60)
        print(f"Total: {registry_data.get('count', 0)} instances")
    else:
        print("[REGISTRY] No registry data received. Is the daemon running?")

async def announce_instance(project: str, owl: str = None):
    """Announce this instance to the registry"""
    nc = NATS()
    await nc.connect(NATS_URL)

    instance_id = str(uuid.uuid4())

    heartbeat = {
        "instance_id": instance_id,
        "project": project,
        "status": "active",
        "current_task": "initializing",
        "owl_assignment": owl or "",
        "uptime_seconds": 0,
        "nats_channels": [
            "owl.all",
            f"project.{project}.*",
            "collective.synthesis"
        ]
    }

    await nc.publish("instance.heartbeat", json.dumps(heartbeat).encode())
    print(f"[REGISTRY] Announced: {project} (ID: {instance_id[:8]}...)")
    print(f"[REGISTRY] To maintain presence, send heartbeats to instance.heartbeat")

    await nc.close()
    return instance_id

async def send_heartbeat(instance_id: str, project: str, status: str = "active", task: str = ""):
    """Send a heartbeat to maintain presence in registry"""
    nc = NATS()
    await nc.connect(NATS_URL)

    heartbeat = {
        "instance_id": instance_id,
        "project": project,
        "status": status,
        "current_task": task,
        "timestamp": datetime.utcnow().isoformat()
    }

    await nc.publish("instance.heartbeat", json.dumps(heartbeat).encode())
    await nc.close()

def main():
    parser = argparse.ArgumentParser(description="Instance Registry - Track Claude instances")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--list", action="store_true", help="List active instances")
    parser.add_argument("--announce", metavar="PROJECT", help="Announce an instance")
    parser.add_argument("--owl", help="Owl assignment for --announce")

    args = parser.parse_args()

    if args.daemon:
        try:
            asyncio.run(run_daemon())
        except KeyboardInterrupt:
            print("\n[REGISTRY] Shutting down...")
    elif args.list:
        asyncio.run(list_instances())
    elif args.announce:
        asyncio.run(announce_instance(args.announce, args.owl))
    else:
        print("INSTANCE REGISTRY")
        print("=" * 40)
        print("Track active Claude instances")
        print()
        print("Usage:")
        print("  python instance_registry.py --daemon      # Run registry daemon")
        print("  python instance_registry.py --list        # List instances")
        print("  python instance_registry.py --announce JOULE --owl SAGE")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
