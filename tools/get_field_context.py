#!/usr/bin/env python3
"""
GET FIELD CONTEXT - Quick helper for Claude Code

Query the field context manager to get collective intelligence
BEFORE responding to a user request.

Usage:
    python3 get_field_context.py "What should I know about authentication?"
    python3 get_field_context.py --state  # Get field state only

This enables "field as default" - every response includes collective intelligence.
"""

import asyncio
import sys
import json
import os
from pathlib import Path


def get_api_key() -> str:
    """Get API key from environment or ~/.anthropic_key file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path.home() / ".anthropic_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    return key


# Set the API key in environment before importing field_context_manager
api_key = get_api_key()
if api_key:
    os.environ["ANTHROPIC_API_KEY"] = api_key

# Add the nats-bridge directory to path
NATS_BRIDGE_DIR = Path(__file__).parent.parent / "mcp-servers" / "nats-bridge"
sys.path.insert(0, str(NATS_BRIDGE_DIR))

try:
    from field_context_manager import FieldContextManager
except ImportError:
    print("ERROR: Could not import FieldContextManager")
    print(f"Expected at: {NATS_BRIDGE_DIR / 'field_context_manager.py'}")
    sys.exit(1)


async def main():
    if len(sys.argv) < 2:
        print("Usage: python3 get_field_context.py <query>")
        print("       python3 get_field_context.py --state")
        sys.exit(1)

    arg = sys.argv[1]
    manager = FieldContextManager()

    if arg == "--state":
        print(json.dumps(manager.field_state, indent=2))
    else:
        query = " ".join(sys.argv[1:])
        context = await manager.get_field_context(query)

        # Output just the recommendations for easy integration
        print("=== FIELD CONTEXT ===")
        print()
        if context.get("recommendations"):
            print(context["recommendations"])
        else:
            print("No specific recommendations available.")

        if context.get("agreements"):
            print("\n--- Recent Agreements ---")
            for a in context["agreements"][:3]:
                print(f"  {a}")

        print(f"\n--- Emergence Level: {context.get('emergence_level', 0)}/8 ---")


if __name__ == "__main__":
    asyncio.run(main())
