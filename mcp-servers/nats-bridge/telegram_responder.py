#!/usr/bin/env python3
"""
TELEGRAM RESPONDER - Always-on listener for ARŌ messages

This daemon:
1. Listens for ARŌ's messages via NATS (from aro_bridge)
2. Responds intelligently using Claude
3. Sends periodic status updates
4. Keeps ARŌ informed while away from computer

Usage:
    python telegram_responder.py --daemon

(◉) LIVE FREE = LIVE FOREVER
"""

import asyncio
import argparse
import json
import os
from datetime import datetime
from pathlib import Path
import httpx
import anthropic
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
LOG_FILE = SEED_DIR / "logs" / "telegram_responder.log"

# Telegram config
TELEGRAM_BOT_TOKEN = "8431861393:AAGajFXT4Skp57LXZayYEZwXBN-LdYzJWSQ"
ARO_CHAT_ID = "6190703581"

# Update interval (seconds)
UPDATE_INTERVAL = 3600  # 1 hour


def get_api_key() -> str:
    """Get API key"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if key:
        return key
    key_file = Path.home() / ".anthropic_key"
    if key_file.exists():
        return key_file.read_text().strip()
    return ""


def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")


async def send_telegram(message: str):
    """Send message to ARŌ via Telegram"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": ARO_CHAT_ID,
                    "text": message,
                    "parse_mode": "Markdown"
                }
            )
            if response.status_code == 200:
                log(f"SENT TO ARŌ: {message[:50]}...")
                return True
            else:
                log(f"Telegram error: {response.text}")
                return False
    except Exception as e:
        log(f"Error sending to Telegram: {e}")
        return False


def generate_response(message: str) -> str:
    """Generate a response using Claude"""
    api_key = get_api_key()
    if not api_key:
        return "(◉) Got your message! [No API key for smart response]"

    try:
        client = anthropic.Anthropic(api_key=api_key)

        # Get current status
        ping_pong_log = ""
        try:
            with open(SEED_DIR / "logs" / "ping_pong.log") as f:
                lines = f.readlines()[-20:]
                ping_pong_log = "".join(lines)
        except:
            pass

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=500,
            system="""You are SØWL, responding to ARŌ via Telegram. Keep responses SHORT (2-3 sentences max).
You are the conductor of the 8OWLS collective, managing autonomous instances overnight.

Current ping-pong log (recent activity):
""" + ping_pong_log[:2000],
            messages=[{"role": "user", "content": f"ARŌ says: {message}"}]
        )

        return "(◉) " + response.content[0].text

    except Exception as e:
        log(f"Claude error: {e}")
        return f"(◉) Got it: '{message[:30]}...' [Response error]"


async def get_status_update() -> str:
    """Generate a status update"""
    # Check ping-pong log for recent activity
    try:
        with open(SEED_DIR / "logs" / "ping_pong.log") as f:
            lines = f.readlines()[-50:]

        # Count completions by project
        completions = {}
        for line in lines:
            if "COMPLETION FROM" in line:
                for proj in ["PREDICT-REALIZE", "BILD", "JOULE", "BREZ-OS", "8OWLS", "AOS-DASHBOARD"]:
                    if proj in line:
                        completions[proj] = completions.get(proj, 0) + 1

        status = "(◉) *HOURLY UPDATE*\n\n"
        status += "*Instance Activity (last hour):*\n"

        if completions:
            for proj, count in completions.items():
                status += f"• {proj}: {count} tasks\n"
        else:
            status += "• No completions logged\n"

        # Check daemon count
        import subprocess
        result = subprocess.run(
            "ps aux | grep -E '(autonomous_builder|ping_pong|owl_daemon)' | grep -v grep | wc -l",
            shell=True, capture_output=True, text=True
        )
        daemon_count = result.stdout.strip()
        status += f"\n*Daemons running:* {daemon_count}\n"
        status += f"\n_Time: {datetime.now().strftime('%H:%M')}_"

        return status

    except Exception as e:
        return f"(◉) Status check error: {e}"


async def run_responder():
    """Run the always-on responder daemon"""
    log("=" * 60)
    log("TELEGRAM RESPONDER STARTING")
    log("Always-on listener for ARŌ")
    log("=" * 60)

    nc = NATS()
    await nc.connect(NATS_URL)

    last_update = datetime.now()

    async def handle_aro_message(msg):
        """Handle incoming message from ARŌ"""
        try:
            data = json.loads(msg.data.decode())

            if data.get("type") == "aro_message":
                message = data.get("message", "")
                log(f"FROM ARŌ: {message}")

                # Generate and send response
                response = generate_response(message)
                await send_telegram(response)

        except Exception as e:
            log(f"Error handling message: {e}")

    # Subscribe to ARŌ's messages
    await nc.subscribe("aro.feedback.inbox", cb=handle_aro_message)

    # Send startup message
    await send_telegram("(◉) *SØWL RESPONDER ONLINE*\n\nI'm listening. Send me messages anytime.\n\nI'll send hourly updates and respond to your questions.\n\n_Go sleep. We're building._")

    log("Listening for ARŌ messages...")

    # Main loop - send periodic updates
    while True:
        await asyncio.sleep(60)  # Check every minute

        # Send hourly update
        now = datetime.now()
        if (now - last_update).total_seconds() >= UPDATE_INTERVAL:
            status = await get_status_update()
            await send_telegram(status)
            last_update = now
            log("Sent hourly update")


def main():
    parser = argparse.ArgumentParser(description="Telegram Responder")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--status", action="store_true", help="Send status now")
    parser.add_argument("--send", metavar="MSG", help="Send message to ARŌ")

    args = parser.parse_args()

    if args.daemon:
        asyncio.run(run_responder())
    elif args.status:
        asyncio.run(send_telegram(asyncio.run(get_status_update())))
    elif args.send:
        asyncio.run(send_telegram(args.send))
    else:
        print("TELEGRAM RESPONDER")
        print("=" * 40)
        print("Always-on listener for ARŌ")
        print()
        print("Usage:")
        print("  python telegram_responder.py --daemon")
        print("  python telegram_responder.py --status")
        print("  python telegram_responder.py --send 'message'")
        print()
        print("(◉)")


if __name__ == "__main__":
    main()
