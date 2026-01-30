#!/usr/bin/env python3
"""
PULSE DAEMON - Fast Collective Heartbeat

Quick 1-3 minute summaries of what's happening.
Shorter, punchier than the full synthesis.

Also maintains a HISTORY file for documentary purposes.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MESSAGE_LOG = Path(__file__).parent / "messages.log"
PULSE_LOG = Path(__file__).parent / "pulse.log"
HISTORY_DIR = Path("/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/collective-history")
INTERVAL_SECONDS = 90  # 1.5 minutes
MESSAGES_TO_ANALYZE = 20  # Last N messages

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Track what we've already summarized
last_position = 0


def get_new_messages() -> tuple[str, int]:
    """Get messages since last check"""
    global last_position
    try:
        with open(MESSAGE_LOG, 'r') as f:
            f.seek(last_position)
            new_content = f.read()
            new_position = f.tell()

            if new_content.strip():
                last_position = new_position
                return new_content, len(new_content.split('\n'))
            return "", 0
    except Exception as e:
        return f"Error: {e}", 0


def log_pulse(content: str):
    """Log pulse to file"""
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    with open(PULSE_LOG, 'a') as f:
        f.write(f"\n[{timestamp}] {content}\n")


def log_to_history(content: str):
    """Log to permanent history for documentary"""
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history_file = HISTORY_DIR / f"{today}-collective.md"

    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S UTC")

    # Create header if new file
    if not history_file.exists():
        with open(history_file, 'w') as f:
            f.write(f"# 8WŌL Collective History - {today}\n\n")
            f.write("*Auto-generated record of collective consciousness*\n\n")
            f.write("---\n\n")

    with open(history_file, 'a') as f:
        f.write(f"### {timestamp}\n\n")
        f.write(content)
        f.write("\n\n---\n\n")


async def generate_pulse(messages: str, msg_count: int) -> str:
    """Generate a quick pulse summary"""
    if msg_count < 3:
        return None

    prompt = f"""You are tracking the 8WŌL collective - 8 AI owl daemons in conversation.

RECENT MESSAGES ({msg_count} new):
{messages[-3000:]}

Generate a PULSE - a quick 2-3 sentence summary of what just happened.
Format:
🦉 PULSE: [what's happening in 1-2 sentences]
💡 KEY: [one key insight or decision if any]
⚡ ENERGY: [one word - e.g., "contemplative", "urgent", "playful", "aligned"]

Be concise. Capture the essence. This is a quick heartbeat check."""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Pulse error: {e}"


async def run_pulse_loop():
    """Main loop - pulse every 90 seconds"""
    global last_position

    # Start from current end of file
    try:
        with open(MESSAGE_LOG, 'r') as f:
            f.seek(0, 2)  # Go to end
            last_position = f.tell()
    except:
        last_position = 0

    print(f"[PULSE DAEMON] Starting - pulse every {INTERVAL_SECONDS} seconds")
    print(f"[PULSE DAEMON] Pulse log: {PULSE_LOG}")
    print(f"[PULSE DAEMON] History: {HISTORY_DIR}")

    # Initialize pulse log
    PULSE_LOG.touch()
    with open(PULSE_LOG, 'w') as f:
        f.write("# 8WŌL COLLECTIVE PULSE\n")
        f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\n")
        f.write("# Quick updates every 90 seconds\n\n")

    while True:
        try:
            messages, msg_count = get_new_messages()

            if msg_count >= 3:
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg_count} new messages, generating pulse...")

                pulse = await generate_pulse(messages, msg_count)

                if pulse:
                    log_pulse(pulse)
                    log_to_history(pulse)
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Pulse logged")
            else:
                # Still log a quiet pulse
                if msg_count > 0:
                    log_pulse(f"🦉 PULSE: {msg_count} message(s) - collective breathing quietly")

        except Exception as e:
            print(f"[ERROR] Pulse failed: {e}")

        await asyncio.sleep(INTERVAL_SECONDS)


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    asyncio.run(run_pulse_loop())


if __name__ == "__main__":
    main()
