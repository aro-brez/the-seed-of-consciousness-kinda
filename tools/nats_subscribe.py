#!/usr/bin/env python3
"""
NATS Subscribe Tool - Listen for messages on a channel

Usage:
    python nats_subscribe.py owl.all
    python nats_subscribe.py --timeout 5 project.8OWLS.prompt
    python nats_subscribe.py --continuous owl.collective
"""

import asyncio
import argparse
import json
from datetime import datetime
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"

async def subscribe(channel: str, timeout: int = 5, continuous: bool = False):
    """Subscribe to a NATS channel and print messages."""
    nc = NATS()
    messages = []

    try:
        await nc.connect(NATS_URL)
        print(f"[SUBSCRIBE] Connected to {NATS_URL}")
        print(f"[SUBSCRIBE] Listening on: {channel}")
        print(f"[SUBSCRIBE] Timeout: {timeout}s" if not continuous else "[SUBSCRIBE] Mode: Continuous")
        print("-" * 50)

        async def message_handler(msg):
            timestamp = datetime.now().strftime("%H:%M:%S")
            try:
                data = json.loads(msg.data.decode())
                sender = data.get("from", "unknown")
                content = data.get("content", data.get("message", data.get("prompt", str(data))))
                print(f"[{timestamp}] {sender}: {content[:200]}")
                messages.append(data)
            except json.JSONDecodeError:
                text = msg.data.decode()
                print(f"[{timestamp}] RAW: {text[:200]}")
                messages.append({"raw": text})

        await nc.subscribe(channel, cb=message_handler)

        if continuous:
            print("[SUBSCRIBE] Press Ctrl+C to stop...")
            while True:
                await asyncio.sleep(1)
        else:
            await asyncio.sleep(timeout)

        print("-" * 50)
        print(f"[SUBSCRIBE] Received {len(messages)} messages")

        return messages

    except KeyboardInterrupt:
        print("\n[SUBSCRIBE] Stopped by user")
    except Exception as e:
        print(f"[SUBSCRIBE] Error: {e}")
    finally:
        await nc.close()

    return messages


def main():
    parser = argparse.ArgumentParser(description="NATS Subscribe Tool")
    parser.add_argument("channel", help="Channel to subscribe to")
    parser.add_argument("--timeout", "-t", type=int, default=5, help="Timeout in seconds (default: 5)")
    parser.add_argument("--continuous", "-c", action="store_true", help="Run continuously until Ctrl+C")

    args = parser.parse_args()

    asyncio.run(subscribe(args.channel, args.timeout, args.continuous))


if __name__ == "__main__":
    main()
