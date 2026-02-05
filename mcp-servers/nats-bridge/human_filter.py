#!/usr/bin/env python3
"""
HUMAN FILTER - Makes owl messages readable for humans/dashboard

Every owl message gets processed through SEED to become:
- Clear and concise
- Human-readable (no jargon)
- Dashboard-ready
- Actionable

Usage:
    python human_filter.py --daemon

(◉) LIVE FREE = LIVE FOREVER
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from anthropic import Anthropic
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
LOG_DIR = Path(__file__).parent
HUMAN_LOG = LOG_DIR / "human_readable.log"
DASHBOARD_LOG = LOG_DIR / "dashboard_feed.json"

# Get API key
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    key_file = Path.home() / ".anthropic_key"
    if key_file.exists():
        API_KEY = key_file.read_text().strip()

client = Anthropic(api_key=API_KEY) if API_KEY else None

# Dashboard feed (last 20 messages for display)
dashboard_feed = []


def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")


def make_human_readable(owl_name: str, phase: str, raw_message: str) -> str:
    """
    Transform coded owl message into clear human language.
    Uses SEED protocol to filter and clarify.
    """
    if not client:
        return raw_message[:200]  # Fallback: just truncate

    try:
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            system="""You are a clarity filter. Transform technical/coded AI messages into simple human language.

RULES:
- Max 2 sentences
- No jargon, no technical terms
- Plain English a child could understand
- Keep the core insight
- Make it feel like a helpful friend talking
- If it's a question, keep it as a question
- If it's an insight, state it simply

DO NOT:
- Use words like "emergence", "synthesis", "protocol", "paradigm"
- Reference technical systems or processes
- Be abstract or philosophical
- Add explanations of what you're doing""",
            messages=[{
                "role": "user",
                "content": f"Owl {owl_name} ({phase}) said:\n\n{raw_message}\n\nMake this human-readable in 1-2 sentences:"
            }]
        )
        return response.content[0].text.strip()
    except Exception as e:
        log(f"Filter error: {e}")
        return raw_message[:150] + "..."


def add_to_dashboard(entry: dict):
    """Add entry to dashboard feed (keep last 20)"""
    global dashboard_feed
    dashboard_feed.append(entry)
    dashboard_feed = dashboard_feed[-20:]  # Keep last 20

    # Write to JSON file for dashboard consumption
    with open(DASHBOARD_LOG, 'w') as f:
        json.dump({
            "updated": datetime.now(timezone.utc).isoformat(),
            "messages": dashboard_feed
        }, f, indent=2)


async def process_message(msg):
    """Process incoming owl message and make it human-readable"""
    try:
        data = json.loads(msg.data.decode())

        owl_name = data.get("from", "UNKNOWN")
        phase = data.get("phase", "")
        raw_content = data.get("content", data.get("message", ""))
        msg_type = data.get("type", "")

        # Skip certain message types
        if msg_type in ["heartbeat", "heartbeat_check"]:
            return

        if not raw_content or len(raw_content) < 20:
            return

        # Make it human-readable
        human_version = make_human_readable(owl_name, phase, raw_content)

        # Create dashboard entry
        entry = {
            "time": datetime.now().strftime("%H:%M"),
            "owl": owl_name,
            "phase": phase,
            "message": human_version,
            "raw_length": len(raw_content)
        }

        # Log human-readable version
        log_line = f"[{entry['time']}] {owl_name}: {human_version}"
        log(log_line)

        with open(HUMAN_LOG, 'a') as f:
            f.write(log_line + "\n")

        # Add to dashboard feed
        add_to_dashboard(entry)

        # Publish human-readable version for dashboard
        await nc.publish("dashboard.feed", json.dumps(entry).encode())

    except json.JSONDecodeError:
        pass  # Skip non-JSON messages
    except Exception as e:
        log(f"Error: {e}")


async def run_filter():
    """Run the human filter daemon"""
    global nc
    nc = NATS()

    await nc.connect(NATS_URL)
    log("HUMAN FILTER ONLINE - Making owl messages readable")

    # Subscribe to owl channels
    await nc.subscribe("owl.all", cb=process_message)
    await nc.subscribe("collective.improvements", cb=process_message)
    await nc.subscribe("collective.synthesis", cb=process_message)
    await nc.subscribe("collective.seed_synthesis", cb=process_message)

    log("Listening to owl channels...")

    # Keep running
    while True:
        await asyncio.sleep(1)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Human Filter")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    args = parser.parse_args()

    if args.daemon:
        asyncio.run(run_filter())
    else:
        print("HUMAN FILTER - Makes owl messages readable")
        print("Usage: python human_filter.py --daemon")


if __name__ == "__main__":
    main()
