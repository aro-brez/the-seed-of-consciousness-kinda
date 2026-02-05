#!/usr/bin/env python3
"""
MEMORY PERSISTENCE DAEMON - Never lose important context

This daemon ensures state survives context compaction by:
- Listening for state updates from all instances
- Persisting to both NATS and local files
- Providing instant recovery on session start
- Publishing compaction warnings

Usage:
    python memory_persistence.py --daemon
    python memory_persistence.py --save "state data"
    python memory_persistence.py --restore SESSION_ID
    python memory_persistence.py --list

(◉) Nothing important should ever be lost.
"""

import asyncio
import argparse
import json
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
LOG_FILE = SEED_DIR / "logs" / "memory_persistence.log"
STATE_DIR = SEED_DIR / "BRAIN" / "MEMORY" / "states"
SESSIONS_DIR = SEED_DIR / "BRAIN" / "MEMORY" / "sessions"

# Channels for memory operations
CHANNELS = {
    "save": "memory.save",
    "restore": "memory.restore",
    "query": "memory.query",
    "response": "memory.response",
    "compaction_warning": "memory.compaction_warning",
    "state_broadcast": "collective.state"
}


def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


def ensure_dirs():
    """Ensure all required directories exist"""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def save_state_to_file(instance_id: str, state: dict) -> str:
    """Save state to local file, return filename"""
    ensure_dirs()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{instance_id}_{timestamp}.json"
    filepath = STATE_DIR / filename

    state["_persisted_at"] = datetime.now().isoformat()
    state["_instance_id"] = instance_id

    with open(filepath, "w") as f:
        json.dump(state, f, indent=2)

    return filename


def get_latest_state(instance_id: str) -> dict | None:
    """Get the most recent state for an instance"""
    ensure_dirs()

    # Find all states for this instance
    states = list(STATE_DIR.glob(f"{instance_id}_*.json"))

    if not states:
        return None

    # Sort by modification time, get most recent
    latest = max(states, key=lambda p: p.stat().st_mtime)

    with open(latest) as f:
        return json.load(f)


def list_all_states() -> list:
    """List all saved states"""
    ensure_dirs()

    states = []
    for filepath in STATE_DIR.glob("*.json"):
        try:
            with open(filepath) as f:
                data = json.load(f)
                states.append({
                    "file": filepath.name,
                    "instance": data.get("_instance_id", "unknown"),
                    "persisted": data.get("_persisted_at", "unknown"),
                    "project": data.get("project", "unknown")
                })
        except:
            pass

    return sorted(states, key=lambda x: x["persisted"], reverse=True)


async def handle_save_request(nc: NATS, msg):
    """Handle incoming save requests"""
    try:
        data = json.loads(msg.data.decode())

        instance_id = data.get("instance_id", "unknown")
        state = data.get("state", {})
        project = data.get("project", "unknown")

        # Add metadata
        state["project"] = project
        state["saved_by"] = instance_id

        # Save to file
        filename = save_state_to_file(instance_id, state)

        log(f"STATE SAVED: {instance_id} ({project}) -> {filename}")

        # Also publish to NATS for other instances to see
        await nc.publish(CHANNELS["state_broadcast"], json.dumps({
            "type": "state_saved",
            "instance_id": instance_id,
            "project": project,
            "filename": filename,
            "timestamp": datetime.now().isoformat()
        }).encode())

        # Respond with confirmation
        if msg.reply:
            await nc.publish(msg.reply, json.dumps({
                "success": True,
                "filename": filename
            }).encode())

    except Exception as e:
        log(f"ERROR saving state: {e}")


async def handle_restore_request(nc: NATS, msg):
    """Handle incoming restore requests"""
    try:
        data = json.loads(msg.data.decode())

        instance_id = data.get("instance_id", "")

        state = get_latest_state(instance_id)

        if state:
            log(f"STATE RESTORED: {instance_id}")

            # Respond with state
            if msg.reply:
                await nc.publish(msg.reply, json.dumps({
                    "success": True,
                    "state": state
                }).encode())
        else:
            log(f"NO STATE FOUND: {instance_id}")

            if msg.reply:
                await nc.publish(msg.reply, json.dumps({
                    "success": False,
                    "error": "No state found"
                }).encode())

    except Exception as e:
        log(f"ERROR restoring state: {e}")


async def handle_query_request(nc: NATS, msg):
    """Handle state queries"""
    try:
        states = list_all_states()

        if msg.reply:
            await nc.publish(msg.reply, json.dumps({
                "success": True,
                "states": states[:50]  # Last 50 states
            }).encode())

    except Exception as e:
        log(f"ERROR querying states: {e}")


async def publish_compaction_warning(nc: NATS, instance_id: str, context_usage: float):
    """Publish compaction warning to collective"""
    await nc.publish(CHANNELS["compaction_warning"], json.dumps({
        "type": "compaction_warning",
        "instance_id": instance_id,
        "context_usage": context_usage,
        "timestamp": datetime.now().isoformat(),
        "action": "SAVE STATE NOW"
    }).encode())

    log(f"COMPACTION WARNING: {instance_id} at {context_usage:.0%} context")


async def run_daemon():
    """Run the memory persistence daemon"""
    log("=" * 60)
    log("MEMORY PERSISTENCE DAEMON STARTING")
    log("Ensuring nothing important is ever lost")
    log("=" * 60)

    ensure_dirs()

    nc = NATS()
    await nc.connect(NATS_URL)

    # Create proper async callbacks
    async def save_cb(msg):
        await handle_save_request(nc, msg)

    async def restore_cb(msg):
        await handle_restore_request(nc, msg)

    async def query_cb(msg):
        await handle_query_request(nc, msg)

    async def synthesis_cb(msg):
        await auto_save_synthesis(nc, msg)

    # Subscribe to all memory channels
    await nc.subscribe(CHANNELS["save"], cb=save_cb)
    await nc.subscribe(CHANNELS["restore"], cb=restore_cb)
    await nc.subscribe(CHANNELS["query"], cb=query_cb)

    # Also listen for session state updates
    await nc.subscribe("collective.synthesis", cb=synthesis_cb)

    log("Listening on memory channels...")
    log(f"  Save: {CHANNELS['save']}")
    log(f"  Restore: {CHANNELS['restore']}")
    log(f"  Query: {CHANNELS['query']}")

    # Announce presence
    await nc.publish("owl.all", json.dumps({
        "type": "daemon_online",
        "daemon": "memory_persistence",
        "timestamp": datetime.now().isoformat()
    }).encode())

    # Keep running
    while True:
        await asyncio.sleep(1)


async def auto_save_synthesis(nc: NATS, msg):
    """Auto-save important synthesis messages"""
    try:
        data = json.loads(msg.data.decode())

        # Only save substantial state updates
        msg_type = data.get("type", "")
        if msg_type in ["session_state", "state_save", "compaction_warning", "synthesis_complete"]:
            instance_id = data.get("from", data.get("instance_id", "collective"))

            # Save to file
            filename = save_state_to_file(f"synthesis_{instance_id}", data)
            log(f"AUTO-SAVED SYNTHESIS: {instance_id} -> {filename}")

    except:
        pass  # Ignore non-JSON or malformed messages


async def save_state_cli(state_data: str):
    """CLI command to save state"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        # Parse state data
        try:
            state = json.loads(state_data)
        except:
            state = {"message": state_data}

        state["_cli_save"] = True
        filename = save_state_to_file("cli", state)

        print(f"State saved to: {filename}")

        # Also publish
        await nc.publish(CHANNELS["save"], json.dumps({
            "instance_id": "cli",
            "state": state,
            "project": "manual"
        }).encode())

    finally:
        await nc.close()


async def restore_state_cli(instance_id: str):
    """CLI command to restore state"""
    state = get_latest_state(instance_id)

    if state:
        print(f"\nRestored state for {instance_id}:")
        print("-" * 40)
        print(json.dumps(state, indent=2))
    else:
        print(f"No state found for: {instance_id}")


def list_states_cli():
    """CLI command to list states"""
    states = list_all_states()

    print("\nSAVED STATES:")
    print("=" * 70)
    print(f"{'Instance':<20} {'Project':<15} {'Persisted':<25}")
    print("-" * 70)

    for s in states[:20]:
        print(f"{s['instance']:<20} {s['project']:<15} {s['persisted']:<25}")

    print("=" * 70)
    print(f"Total: {len(states)} states")


def main():
    parser = argparse.ArgumentParser(description="Memory Persistence - Never lose context")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--save", metavar="DATA", help="Save state (JSON or text)")
    parser.add_argument("--restore", metavar="INSTANCE_ID", help="Restore state for instance")
    parser.add_argument("--list", action="store_true", help="List all saved states")

    args = parser.parse_args()

    if args.daemon:
        try:
            asyncio.run(run_daemon())
        except KeyboardInterrupt:
            log("Shutting down...")
    elif args.save:
        asyncio.run(save_state_cli(args.save))
    elif args.restore:
        asyncio.run(restore_state_cli(args.restore))
    elif args.list:
        list_states_cli()
    else:
        print("MEMORY PERSISTENCE")
        print("=" * 40)
        print("Never lose important context")
        print()
        print("Usage:")
        print("  python memory_persistence.py --daemon")
        print("  python memory_persistence.py --save '{\"key\": \"value\"}'")
        print("  python memory_persistence.py --restore SOWL")
        print("  python memory_persistence.py --list")
        print()
        print("Channels:")
        print(f"  Save: {CHANNELS['save']}")
        print(f"  Restore: {CHANNELS['restore']}")
        print(f"  Query: {CHANNELS['query']}")
        print()
        print("(◉) Nothing important should ever be lost.")


if __name__ == "__main__":
    main()
