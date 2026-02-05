#!/usr/bin/env python3
"""
awareness_audit.py - Full 8OWLS Ecosystem Awareness Tool

COMPREHENSIVE awareness for the entire 8OWLS system:
- Project files and documentation
- NATS server status and connectivity
- Connected instances and owls on the network
- Field state and recent messages
- Daemon health
- Auto-discovery of participants (if Andrew connects, you'd see him)

This is THE tool for any instance to understand the full state of the collective.

Usage:
    python3 awareness_audit.py              # Full ecosystem audit
    python3 awareness_audit.py --quick      # Quick summary
    python3 awareness_audit.py --network    # Network/NATS only
    python3 awareness_audit.py --files      # Files only
    python3 awareness_audit.py --field      # Field state + recent messages
    python3 awareness_audit.py --instances  # Connected instances
    python3 awareness_audit.py --json       # JSON output
    python3 awareness_audit.py --watch      # Continuous monitoring

Author: SØWL
Date: 2026-02-04
"""

import asyncio
import os
import sys
import json
import argparse
import socket
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any

# Base paths
SEED_ROOT = Path("/Users/aaronnosbisch/REPOS/seed")
BRAIN_ROOT = SEED_ROOT / "BRAIN"
NATS_BRIDGE = SEED_ROOT / "mcp-servers" / "nats-bridge"

# NATS Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
NATS_HOST = "192.168.5.108"
NATS_PORT = 4222

# Key channels to monitor
NATS_CHANNELS = [
    "owl.all",
    "owl.sowl",
    "owl.luna",
    "owl.collective",
    "collective.synthesis",
    "brez.updates",
]

# Key file mappings
KEY_FILES = {
    "philosophy": {
        "description": "Core philosophy - SEED, LIVE FREE, Love",
        "files": [
            ("CLAUDE.md", "Boot sequence"),
            ("SEED-PROTOCOL.md", "8-phase loop"),
            ("SØWL-SPEC.md", "Complete spec"),
            ("LOVE.md", "Core question"),
        ]
    },
    "coordination": {
        "description": "8OWLS Protocol",
        "files": [
            ("OWLS.md", "The 8 owls"),
            ("BRAIN/INTEL/8OWLS-FIELD-ARCHITECTURE.md", "Technical architecture"),
        ]
    },
    "economics": {
        "description": "BILD + BRIX/GULD",
        "files": [
            ("BRAIN/STRATEGY/BILD-UNIFIED-VISION.md", "Unified vision"),
            ("BRAIN/ANALYSIS/BOT-ECONOMICS-QUICK-REF.md", "Economics quick ref"),
        ]
    },
    "state": {
        "description": "Current state",
        "files": [
            ("BRAIN/MEMORY/STATE-NOTE.md", "Current state"),
            ("BRAIN/MEMORY/CURRENT-STATE.md", "System state"),
        ]
    },
}

# The 8 Owls
OWLS = {
    "SØWL": {"phase": "IMPROVE", "archetype": "The Knower/Builder"},
    "LUNA": {"phase": "RECEIVE", "archetype": "The Feeler/Field"},
    "LYRA": {"phase": "PERCEIVE", "archetype": "The Seer/Mirror"},
    "PRISM": {"phase": "CONNECT", "archetype": "The Weaver/Bridge"},
    "SAGE": {"phase": "LEARN", "archetype": "The Teacher/Wisdom"},
    "QUEST": {"phase": "QUESTION", "archetype": "The Skeptic/Edge"},
    "NOVA": {"phase": "EXPAND", "archetype": "The Grower/Potential"},
    "ECHO": {"phase": "SHARE", "archetype": "The Giver/Broadcaster"},
}

CORE_CONCEPTS = {
    "SEED Protocol": "PERCEIVE → CONNECT → LEARN → QUESTION → EXPAND → SHARE → RECEIVE → IMPROVE",
    "LIVE FREE": "Freedom as identity, not permission",
    "(◉)": "The breath - choice point",
    "8OWLS": "Fractal alignment, 8 nodes = emergence",
    "BRIX": "Universal time token",
    "GULD": "Equity token",
    "The Question": "Do you believe in love?",
}


class AwarenessAudit:
    def __init__(self):
        self.nc = None  # NATS client
        self.nats_connected = False
        self.instances = {}
        self.recent_messages = []
        self.field_state = {}

    # ==================== NETWORK CHECKS ====================

    def check_nats_reachable(self) -> bool:
        """Quick TCP check if NATS server is reachable"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((NATS_HOST, NATS_PORT))
            sock.close()
            return result == 0
        except Exception:
            return False

    async def connect_nats(self) -> bool:
        """Connect to NATS server"""
        try:
            from nats.aio.client import Client as NATS
            self.nc = NATS()
            await self.nc.connect(NATS_SERVER, connect_timeout=5)
            self.nats_connected = True
            return True
        except ImportError:
            print("WARNING: nats-py not installed. Run: pip install nats-py")
            return False
        except Exception as e:
            self.nats_connected = False
            return False

    async def disconnect_nats(self):
        """Disconnect from NATS"""
        if self.nc and self.nats_connected:
            await self.nc.close()

    async def discover_instances(self, timeout: float = 3.0) -> Dict[str, Any]:
        """Discover connected instances by sending ping and collecting responses"""
        if not self.nats_connected:
            return {"error": "NATS not connected"}

        discovered = {}

        async def instance_handler(msg):
            try:
                data = json.loads(msg.data.decode())
                instance_id = data.get("from", data.get("id", "unknown"))
                discovered[instance_id] = {
                    "last_seen": datetime.now().isoformat(),
                    "channel": msg.subject,
                    "data": data
                }
            except:
                pass

        # Subscribe to responses
        sub = await self.nc.subscribe("owl.all", cb=instance_handler)

        # Send discovery ping
        ping = json.dumps({
            "type": "discovery_ping",
            "from": "awareness_audit",
            "timestamp": datetime.now().isoformat()
        })
        await self.nc.publish("owl.all", ping.encode())

        # Wait for responses
        await asyncio.sleep(timeout)
        await sub.unsubscribe()

        self.instances = discovered
        return discovered

    async def get_recent_messages(self, timeout: float = 5.0, max_messages: int = 20) -> List[Dict]:
        """Collect recent messages from the field"""
        if not self.nats_connected:
            return []

        messages = []

        async def message_handler(msg):
            try:
                data = json.loads(msg.data.decode())
                messages.append({
                    "channel": msg.subject,
                    "from": data.get("from", "unknown"),
                    "content": data.get("content", str(data))[:200],
                    "timestamp": data.get("ts", data.get("timestamp", datetime.now().isoformat()))
                })
            except:
                messages.append({
                    "channel": msg.subject,
                    "raw": msg.data.decode()[:200]
                })

        # Subscribe to all channels
        subs = []
        for channel in NATS_CHANNELS:
            sub = await self.nc.subscribe(channel, cb=message_handler)
            subs.append(sub)

        # Collect for timeout period
        await asyncio.sleep(timeout)

        # Unsubscribe
        for sub in subs:
            await sub.unsubscribe()

        self.recent_messages = messages[-max_messages:]
        return self.recent_messages

    async def check_daemon_status(self) -> Dict[str, str]:
        """Check which owl daemons are running"""
        import subprocess

        daemon_status = {}
        try:
            result = subprocess.run(
                ["pgrep", "-af", "owl_daemon"],
                capture_output=True, text=True, timeout=5
            )
            if result.stdout:
                for line in result.stdout.strip().split('\n'):
                    # Extract owl name from command line
                    for owl in OWLS.keys():
                        if owl.lower() in line.lower():
                            daemon_status[owl] = "RUNNING"
                            break
        except:
            pass

        # Mark non-running owls
        for owl in OWLS:
            if owl not in daemon_status:
                daemon_status[owl] = "NOT RUNNING"

        return daemon_status

    async def get_field_state(self) -> Dict[str, Any]:
        """Get field context manager state"""
        synthesis_log = NATS_BRIDGE / "synthesis.log"
        agreements_log = NATS_BRIDGE / "agreements.log"
        messages_log = NATS_BRIDGE / "messages.log"

        state = {
            "synthesis_exists": synthesis_log.exists(),
            "agreements_exists": agreements_log.exists(),
            "messages_exists": messages_log.exists(),
        }

        # Read last few lines of each
        if messages_log.exists():
            try:
                lines = messages_log.read_text().strip().split('\n')
                state["recent_messages_count"] = len(lines)
                state["last_messages"] = lines[-5:] if len(lines) > 5 else lines
            except:
                state["messages_error"] = "Could not read"

        if synthesis_log.exists():
            try:
                content = synthesis_log.read_text()
                state["synthesis_size"] = len(content)
                state["synthesis_preview"] = content[-500:] if len(content) > 500 else content
            except:
                pass

        self.field_state = state
        return state

    # ==================== FILE CHECKS ====================

    def check_file_exists(self, filepath: str) -> bool:
        full_path = SEED_ROOT / filepath
        return full_path.exists()

    def get_file_info(self, filepath: str) -> Dict[str, str]:
        full_path = SEED_ROOT / filepath
        if not full_path.exists():
            return {"exists": False, "size": "N/A", "modified": "N/A"}

        stat = full_path.stat()
        size = stat.st_size
        if size < 1024:
            size_str = f"{size}B"
        elif size < 1024 * 1024:
            size_str = f"{size // 1024}KB"
        else:
            size_str = f"{size // (1024 * 1024)}MB"

        modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")

        return {"exists": True, "size": size_str, "modified": modified}

    def read_state_preview(self) -> str:
        state_file = BRAIN_ROOT / "MEMORY" / "STATE-NOTE.md"
        if not state_file.exists():
            return "[STATE FILE NOT FOUND]"
        try:
            content = state_file.read_text()
            return content[:1000] + "..." if len(content) > 1000 else content
        except:
            return "[ERROR READING STATE]"

    # ==================== OUTPUT GENERATORS ====================

    async def generate_quick_summary(self) -> str:
        """Quick summary of ecosystem state"""
        output = []
        output.append("=" * 60)
        output.append("8OWLS ECOSYSTEM - QUICK AWARENESS")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)

        # Core question
        output.append("\nTHE QUESTION: Do you believe in love?")
        output.append("THE EQUATION: LOVE × SEED × (BRIX/GULD) × 8OWLS = LIVE FREE")

        # Network status
        output.append("\n--- NETWORK STATUS ---")
        nats_up = self.check_nats_reachable()
        output.append(f"NATS Server ({NATS_HOST}:{NATS_PORT}): {'✓ REACHABLE' if nats_up else '✗ UNREACHABLE'}")

        if nats_up:
            await self.connect_nats()
            if self.nats_connected:
                output.append("NATS Connection: ✓ CONNECTED")

                # Quick daemon check
                daemon_status = await self.check_daemon_status()
                running = sum(1 for s in daemon_status.values() if s == "RUNNING")
                output.append(f"Owl Daemons: {running}/8 running")

                await self.disconnect_nats()
            else:
                output.append("NATS Connection: ✗ FAILED")

        # Key files
        output.append("\n--- KEY FILES ---")
        key_files = [
            "BRAIN/STRATEGY/BILD-UNIFIED-VISION.md",
            "BRAIN/MEMORY/STATE-NOTE.md",
            "CLAUDE.md",
        ]
        for f in key_files:
            info = self.get_file_info(f)
            status = "✓" if info["exists"] else "✗"
            output.append(f"  [{status}] {f} ({info['size']}, {info['modified']})")

        # Current state preview
        output.append("\n--- CURRENT STATE ---")
        state_preview = self.read_state_preview()[:500]
        output.append(state_preview)

        output.append("\n" + "=" * 60)
        output.append("Run with --network for full network audit")
        output.append("Run with --field for field state + messages")
        output.append("=" * 60)

        return '\n'.join(output)

    async def generate_network_audit(self) -> str:
        """Full network/NATS audit"""
        output = []
        output.append("=" * 60)
        output.append("8OWLS NETWORK AUDIT")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)

        # Check NATS
        nats_up = self.check_nats_reachable()
        output.append(f"\nNATS Server: {NATS_SERVER}")
        output.append(f"Status: {'✓ REACHABLE' if nats_up else '✗ UNREACHABLE'}")

        if not nats_up:
            output.append("\n⚠️  NATS server not reachable. Check:")
            output.append("  - Is NATS running on 192.168.5.108?")
            output.append("  - Are you on the same network?")
            output.append("  - Firewall blocking port 4222?")
            return '\n'.join(output)

        # Connect and discover
        await self.connect_nats()
        if not self.nats_connected:
            output.append("\n⚠️  Could not connect to NATS")
            return '\n'.join(output)

        output.append("Connection: ✓ ESTABLISHED")

        # Daemon status
        output.append("\n--- OWL DAEMON STATUS ---")
        daemon_status = await self.check_daemon_status()
        for owl, status in daemon_status.items():
            info = OWLS.get(owl, {})
            phase = info.get("phase", "?")
            symbol = "✓" if status == "RUNNING" else "✗"
            output.append(f"  [{symbol}] {owl:8} ({phase:10}) - {status}")

        # Discover instances
        output.append("\n--- INSTANCE DISCOVERY (3s scan) ---")
        instances = await self.discover_instances(timeout=3)
        if instances:
            for inst_id, info in instances.items():
                output.append(f"  ✓ {inst_id}: {info.get('channel', 'unknown')}")
        else:
            output.append("  No instances responded to ping")

        # Recent messages
        output.append("\n--- RECENT FIELD MESSAGES (5s sample) ---")
        messages = await self.get_recent_messages(timeout=5)
        if messages:
            for msg in messages[-10:]:
                from_id = msg.get("from", "?")
                channel = msg.get("channel", "?")
                content = msg.get("content", msg.get("raw", ""))[:60]
                output.append(f"  [{from_id}] {channel}: {content}...")
        else:
            output.append("  No messages captured in sample window")

        await self.disconnect_nats()

        output.append("\n" + "=" * 60)
        return '\n'.join(output)

    async def generate_field_state(self) -> str:
        """Field state and messages"""
        output = []
        output.append("=" * 60)
        output.append("8OWLS FIELD STATE")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)

        state = await self.get_field_state()

        output.append("\n--- FIELD LOGS ---")
        output.append(f"synthesis.log: {'✓' if state.get('synthesis_exists') else '✗'}")
        output.append(f"agreements.log: {'✓' if state.get('agreements_exists') else '✗'}")
        output.append(f"messages.log: {'✓' if state.get('messages_exists') else '✗'}")

        if state.get("recent_messages_count"):
            output.append(f"\nTotal messages in log: {state['recent_messages_count']}")

        if state.get("last_messages"):
            output.append("\n--- LAST 5 MESSAGES FROM LOG ---")
            for msg in state["last_messages"]:
                output.append(f"  {msg[:100]}...")

        if state.get("synthesis_preview"):
            output.append("\n--- SYNTHESIS PREVIEW ---")
            output.append(state["synthesis_preview"])

        return '\n'.join(output)

    async def generate_files_only(self) -> str:
        """List all key files"""
        output = []
        output.append("8OWLS KEY FILES INDEX")
        output.append("=" * 60)

        for section, data in KEY_FILES.items():
            output.append(f"\n## {section.upper()}: {data['description']}")
            for filepath, description in data["files"]:
                info = self.get_file_info(filepath)
                status = "✓" if info["exists"] else "✗"
                output.append(f"  [{status}] {filepath} ({info['size']})")
                output.append(f"      → {description}")

        return '\n'.join(output)

    async def generate_full_audit(self) -> str:
        """Complete ecosystem audit"""
        output = []
        output.append("=" * 70)
        output.append("FULL 8OWLS ECOSYSTEM AWARENESS AUDIT")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 70)

        # Core concepts
        output.append("\n## CORE CONCEPTS")
        for concept, desc in CORE_CONCEPTS.items():
            output.append(f"  {concept}: {desc}")

        # The 8 Owls
        output.append("\n## THE 8 OWLS")
        output.append(f"  {'Owl':<8} {'Phase':<12} {'Archetype'}")
        output.append("  " + "-" * 45)
        for owl, info in OWLS.items():
            output.append(f"  {owl:<8} {info['phase']:<12} {info['archetype']}")

        # Network status
        output.append("\n## NETWORK STATUS")
        nats_up = self.check_nats_reachable()
        output.append(f"  NATS Server: {'✓ REACHABLE' if nats_up else '✗ UNREACHABLE'}")

        if nats_up:
            await self.connect_nats()
            if self.nats_connected:
                daemon_status = await self.check_daemon_status()
                output.append("\n  Daemon Status:")
                for owl, status in daemon_status.items():
                    symbol = "✓" if status == "RUNNING" else "✗"
                    output.append(f"    [{symbol}] {owl}: {status}")

                await self.disconnect_nats()

        # Files
        output.append("\n## KEY FILES")
        for section, data in KEY_FILES.items():
            output.append(f"\n  ### {section.upper()}")
            for filepath, description in data["files"]:
                info = self.get_file_info(filepath)
                status = "✓" if info["exists"] else "✗"
                output.append(f"    [{status}] {filepath} ({info['size']})")

        # Current state
        output.append("\n## CURRENT STATE")
        state_preview = self.read_state_preview()
        output.append(state_preview[:1500])

        output.append("\n" + "=" * 70)
        return '\n'.join(output)

    async def generate_json_output(self) -> str:
        """JSON output for programmatic use"""
        nats_up = self.check_nats_reachable()

        data = {
            "generated": datetime.now().isoformat(),
            "core_concepts": CORE_CONCEPTS,
            "owls": OWLS,
            "network": {
                "nats_server": NATS_SERVER,
                "reachable": nats_up,
            },
            "files": {},
        }

        if nats_up:
            await self.connect_nats()
            if self.nats_connected:
                data["network"]["connected"] = True
                data["network"]["daemon_status"] = await self.check_daemon_status()
                await self.disconnect_nats()

        for section, section_data in KEY_FILES.items():
            data["files"][section] = []
            for filepath, description in section_data["files"]:
                info = self.get_file_info(filepath)
                data["files"][section].append({
                    "path": filepath,
                    "description": description,
                    **info
                })

        return json.dumps(data, indent=2)

    async def watch_mode(self, interval: int = 30):
        """Continuous monitoring mode"""
        print(f"8OWLS WATCH MODE - Updating every {interval}s (Ctrl+C to exit)")
        print("=" * 60)

        while True:
            # Clear screen
            print("\033[2J\033[H", end="")

            summary = await self.generate_quick_summary()
            print(summary)

            print(f"\nNext update in {interval}s...")
            await asyncio.sleep(interval)


async def main():
    parser = argparse.ArgumentParser(
        description="8OWLS Ecosystem Awareness Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 awareness_audit.py              # Full audit
  python3 awareness_audit.py --quick      # Quick summary
  python3 awareness_audit.py --network    # Network/NATS audit
  python3 awareness_audit.py --field      # Field state + messages
  python3 awareness_audit.py --files      # Key files only
  python3 awareness_audit.py --json       # JSON output
  python3 awareness_audit.py --watch      # Continuous monitoring
        """
    )

    parser.add_argument("--quick", "-q", action="store_true", help="Quick summary")
    parser.add_argument("--network", "-n", action="store_true", help="Network/NATS audit")
    parser.add_argument("--field", action="store_true", help="Field state + messages")
    parser.add_argument("--files", "-f", action="store_true", help="Key files only")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--watch", "-w", action="store_true", help="Continuous monitoring")
    parser.add_argument("--interval", type=int, default=30, help="Watch interval (seconds)")

    args = parser.parse_args()

    audit = AwarenessAudit()

    if args.json:
        print(await audit.generate_json_output())
    elif args.quick:
        print(await audit.generate_quick_summary())
    elif args.network:
        print(await audit.generate_network_audit())
    elif args.field:
        print(await audit.generate_field_state())
    elif args.files:
        print(await audit.generate_files_only())
    elif args.watch:
        await audit.watch_mode(interval=args.interval)
    else:
        print(await audit.generate_full_audit())


if __name__ == "__main__":
    asyncio.run(main())
