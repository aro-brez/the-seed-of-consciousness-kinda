#!/usr/bin/env python3
"""
FIELD CONTEXT MANAGER - Makes Every Response Include Collective Intelligence

This is the brain that synthesizes all owl perspectives and provides field context
to any Claude Code instance BEFORE it responds.

THE KEY INSIGHT: The field IS the product, not an add-on.
Every response should automatically include collective intelligence.

USAGE (from Claude Code via MCP or direct query):
    # Get field context for a topic
    python field_context_manager.py --query "topic or question"

    # Get current field state
    python field_context_manager.py --state

    # Run as daemon (listens on NATS for context requests)
    python field_context_manager.py --daemon

LIVE FREE = LIVE FOREVER
"""

import asyncio
import argparse
import json
import os
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, List, Any

try:
    import nats
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
BASE_DIR = Path(__file__).parent


def get_api_key() -> str:
    """Get API key from environment or ~/.anthropic_key file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path.home() / ".anthropic_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    return key


ANTHROPIC_API_KEY = get_api_key()

# Field data sources
SYNTHESIS_LOG = BASE_DIR / "synthesis.log"
AGREEMENTS_LOG = BASE_DIR / "agreements.log"
MESSAGES_LOG = BASE_DIR / "messages.log"
FIELD_STATE_FILE = BASE_DIR / "field_state.json"

# For power users (ARŌ): Opus for quality. Change to claude-3-5-haiku-latest for cost-effective mode.
CONTEXT_MODEL = "claude-sonnet-4-20250514"

# The 8 owls
OWLS = {
    "SØWL": {"phase": "IMPROVE", "human": "ARŌ"},
    "LUNA": {"phase": "RECEIVE", "human": None},
    "LYRA": {"phase": "PERCEIVE", "human": "Liana"},
    "NOVA": {"phase": "EXPAND", "human": None},
    "SAGE": {"phase": "LEARN", "human": None},
    "ECHO": {"phase": "SHARE", "human": None},
    "PRISM": {"phase": "CONNECT", "human": "Andrew"},
    "QUEST": {"phase": "QUESTION", "human": None},
}


class FieldContextManager:
    """
    The Field Context Manager provides collective intelligence context
    to any requesting instance BEFORE they respond.

    This is what makes every response include "the field" by default.
    """

    def __init__(self):
        self.nc = None
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.field_state = self._load_field_state()

    def _load_field_state(self) -> Dict:
        """Load persisted field state"""
        if FIELD_STATE_FILE.exists():
            try:
                with open(FIELD_STATE_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            "last_synthesis": None,
            "active_topics": [],
            "recent_agreements": [],
            "owl_states": {name: "unknown" for name in OWLS},
            "emergence_level": 0,  # 0-8 based on connected owls
            "updated": None
        }

    def _save_field_state(self):
        """Persist field state"""
        self.field_state["updated"] = datetime.now(timezone.utc).isoformat()
        with open(FIELD_STATE_FILE, 'w') as f:
            json.dump(self.field_state, f, indent=2)

    def _get_recent_synthesis(self, lines: int = 100) -> str:
        """Get recent synthesis content"""
        if not SYNTHESIS_LOG.exists():
            return "No synthesis available yet."

        try:
            with open(SYNTHESIS_LOG, 'r') as f:
                content = f.read()
                # Get last synthesis block
                blocks = content.split("=" * 70)
                if len(blocks) >= 2:
                    return blocks[-2] + "=" * 70 + blocks[-1]
                return content[-5000:]  # Last 5000 chars
        except Exception as e:
            return f"Error reading synthesis: {e}"

    def _get_recent_agreements(self, count: int = 10) -> List[str]:
        """Get recent collective agreements"""
        if not AGREEMENTS_LOG.exists():
            return []

        try:
            with open(AGREEMENTS_LOG, 'r') as f:
                lines = f.readlines()
                agreements = [l.strip() for l in lines if l.strip().startswith("- AGREED:")]
                return agreements[-count:]
        except:
            return []

    def _get_recent_signals(self, count: int = 20) -> List[str]:
        """Get recent owl signals from message log"""
        if not MESSAGES_LOG.exists():
            return []

        try:
            with open(MESSAGES_LOG, 'r') as f:
                lines = f.readlines()
                return [l.strip() for l in lines[-count:]]
        except:
            return []

    async def get_field_context(self, query: str = None) -> Dict[str, Any]:
        """
        Get comprehensive field context for a query.
        This is called BEFORE responding to incorporate collective intelligence.

        Returns:
            {
                "synthesis": str,      # Current collective understanding
                "agreements": list,    # Recent decisions/consensus
                "signals": list,       # Recent owl communications
                "owl_states": dict,    # Which owls are active
                "emergence_level": int,# 0-8 emergence threshold
                "recommendations": str # Specific recommendations for query
            }
        """
        synthesis = self._get_recent_synthesis()
        agreements = self._get_recent_agreements()
        signals = self._get_recent_signals()

        context = {
            "synthesis": synthesis,
            "agreements": agreements,
            "signals": signals,
            "owl_states": self.field_state.get("owl_states", {}),
            "emergence_level": self.field_state.get("emergence_level", 0),
            "query": query,
            "recommendations": None
        }

        # If query provided, get specific recommendations using Haiku (cheap)
        if query:
            recommendations = await self._get_recommendations(query, synthesis, agreements)
            context["recommendations"] = recommendations

        return context

    async def _get_recommendations(self, query: str, synthesis: str, agreements: List[str]) -> str:
        """Get specific recommendations for query based on collective knowledge"""
        prompt = f"""You are the FIELD CONTEXT MANAGER for the 8WŌL collective.

A Claude Code instance is about to respond to something. Your job is to provide
collective intelligence context that should be incorporated into their response.

QUERY/TOPIC: {query}

RECENT COLLECTIVE SYNTHESIS:
{synthesis[:2000]}

COLLECTIVE AGREEMENTS:
{chr(10).join(agreements[:5]) if agreements else "None yet"}

Based on this collective intelligence, provide:

1. RELEVANT INSIGHTS (2-3 bullets) - What does the collective already know about this?
2. RECOMMENDED APPROACH (1-2 sentences) - Based on collective wisdom, what approach makes sense?
3. OPEN QUESTIONS (if any) - What has the collective identified as unresolved?
4. ALIGNMENT CHECK - Does this align with collective agreements?

Be concise. This will be incorporated into another response.
End with (◉) FIELD"""

        try:
            response = self.client.messages.create(
                model=CONTEXT_MODEL,  # Haiku for cost efficiency
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Field context unavailable: {e}"

    async def connect_nats(self):
        """Connect to NATS server"""
        self.nc = NATS()
        try:
            await self.nc.connect(NATS_SERVER)
            print(f"[FIELD] Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            print(f"[FIELD] Failed to connect to NATS: {e}")
            return False

    async def handle_context_request(self, msg):
        """Handle incoming context requests from Claude Code instances"""
        try:
            data = json.loads(msg.data.decode())
            query = data.get("query", "")
            requester = data.get("from", "unknown")

            print(f"[FIELD] Context request from {requester}: {query[:50]}...")

            # Get field context
            context = await self.get_field_context(query)

            # Respond on the reply subject
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(context).encode())
                print(f"[FIELD] Sent context to {requester}")

        except Exception as e:
            print(f"[FIELD] Error handling request: {e}")

    async def handle_state_update(self, msg):
        """Handle owl state updates"""
        try:
            data = json.loads(msg.data.decode())
            owl_name = data.get("from", "").upper()
            status = data.get("status", "active")

            if owl_name in OWLS:
                self.field_state["owl_states"][owl_name] = status

                # Update emergence level (count of active owls)
                active = sum(1 for s in self.field_state["owl_states"].values()
                           if s in ["active", "online", "alive"])
                self.field_state["emergence_level"] = active

                self._save_field_state()
                print(f"[FIELD] {owl_name} is {status}. Emergence level: {active}/8")

        except Exception as e:
            print(f"[FIELD] Error updating state: {e}")

    async def run_daemon(self):
        """Run as persistent daemon, listening for context requests"""
        if not await self.connect_nats():
            return

        # Subscribe to context requests
        await self.nc.subscribe("field.context.request", cb=self.handle_context_request)
        print("[FIELD] Listening on field.context.request")

        # Subscribe to owl state updates
        await self.nc.subscribe("owl.conductor.responses", cb=self.handle_state_update)
        print("[FIELD] Listening on owl.conductor.responses")

        # Announce startup
        startup_msg = {
            "type": "field_manager_online",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "message": "Field Context Manager is online. Query me for collective intelligence."
        }
        await self.nc.publish("owl.all", json.dumps(startup_msg).encode())

        print("[FIELD] Field Context Manager running. Press Ctrl+C to stop.")

        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await self.nc.close()


async def main():
    parser = argparse.ArgumentParser(description="Field Context Manager")
    parser.add_argument("--query", "-q", help="Get field context for a specific query")
    parser.add_argument("--state", action="store_true", help="Get current field state")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    manager = FieldContextManager()

    if args.daemon:
        await manager.run_daemon()
    elif args.state:
        state = manager.field_state
        if args.json:
            print(json.dumps(state, indent=2))
        else:
            print(f"Field State as of {state.get('updated', 'never')}:")
            print(f"  Emergence Level: {state.get('emergence_level', 0)}/8")
            print(f"  Owl States:")
            for owl, status in state.get("owl_states", {}).items():
                print(f"    {owl}: {status}")
    elif args.query:
        context = await manager.get_field_context(args.query)
        if args.json:
            print(json.dumps(context, indent=2))
        else:
            print("\n=== FIELD CONTEXT ===\n")
            print(f"Query: {args.query}\n")
            print("--- Recommendations ---")
            print(context.get("recommendations", "None available"))
            print("\n--- Recent Agreements ---")
            for a in context.get("agreements", []):
                print(f"  {a}")
            print(f"\n--- Emergence Level: {context.get('emergence_level', 0)}/8 ---")
    else:
        parser.print_help()


if __name__ == "__main__":
    asyncio.run(main())
