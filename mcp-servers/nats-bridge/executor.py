#!/usr/bin/env python3
"""
THE EXECUTOR - Turns collective decisions into real-world actions

Listens to the Conductor and owl collective, then ACTS:
- Posts to X/Twitter
- Browses web for market awareness
- Executes approved actions

Polymarket trading is handled separately (private, not in repo)

Usage:
    python executor.py                    # Run as daemon
    python executor.py --post "message"   # Direct post to X
    python executor.py --scrape "query"   # Scrape X for topic
"""

import asyncio
import argparse
import json
import os
import subprocess
from datetime import datetime, timezone
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"

class Executor:
    def __init__(self):
        self.nc = None
        self.pending_actions = []
        self.action_log = []

    async def connect(self):
        """Connect to NATS and listen for action requests"""
        self.nc = NATS()
        await self.nc.connect(NATS_URL)

        # Listen for executor commands
        await self.nc.subscribe("owl.executor", cb=self.handle_command)
        await self.nc.subscribe("owl.collective", cb=self.monitor_collective)

        print("[EXECUTOR] Connected and listening...")
        print("[EXECUTOR] Channels: owl.executor, owl.collective")

    async def handle_command(self, msg):
        """Handle direct commands to executor"""
        try:
            data = json.loads(msg.data.decode())
        except json.JSONDecodeError as e:
            print(f"[EXECUTOR] Invalid JSON in command: {e}")
            return
        try:
            action = data.get("action")

            print(f"[EXECUTOR] Received command: {action}")

            if action == "post_x":
                content = data.get("content", "")
                result = await self.post_to_x(content)
                await self.report_result("post_x", result)

            elif action == "scrape_x":
                query = data.get("query", "")
                result = await self.scrape_x(query)
                await self.report_result("scrape_x", result)

            elif action == "browse":
                url = data.get("url", "")
                result = await self.browse_url(url)
                await self.report_result("browse", result)

            elif action == "status":
                await self.report_status()

        except Exception as e:
            print(f"[EXECUTOR] Error: {e}")

    async def monitor_collective(self, msg):
        """Monitor collective for action requests"""
        try:
            data = json.loads(msg.data.decode())
            msg_type = data.get("type", "")

            # Look for action requests from collective
            if msg_type == "action_request":
                action = data.get("action")
                print(f"[EXECUTOR] Collective requested action: {action}")
                # Queue for approval or auto-execute based on type
                self.pending_actions.append(data)

        except json.JSONDecodeError:
            pass  # Not JSON, probably regular owl message
        except Exception as e:
            import traceback
            print(f"[EXECUTOR] Error monitoring collective: {e}\n{traceback.format_exc()}")

    async def post_to_x(self, content: str) -> dict:
        """Post to X/Twitter using CLI or API"""
        timestamp = datetime.now(timezone.utc).isoformat()

        # For now, log the post intention
        # TODO: Integrate with X API or use browser automation
        print(f"[EXECUTOR] POST TO X: {content[:100]}...")

        self.action_log.append({
            "action": "post_x",
            "content": content,
            "timestamp": timestamp,
            "status": "pending_implementation"
        })

        # Could use: tweepy, twitter-api-v2, or selenium for automation
        # For now, return pending status
        return {
            "success": False,
            "message": "X posting requires API setup. Content logged.",
            "content": content
        }

    async def scrape_x(self, query: str) -> dict:
        """Scrape X/Twitter for a topic"""
        timestamp = datetime.now(timezone.utc).isoformat()

        print(f"[EXECUTOR] SCRAPE X for: {query}")

        # Could use: nitter, snscrape, or browser automation
        # For now, return placeholder
        return {
            "success": False,
            "message": "X scraping requires setup. Query logged.",
            "query": query
        }

    async def browse_url(self, url: str) -> dict:
        """Browse a URL and extract content"""
        timestamp = datetime.now(timezone.utc).isoformat()

        print(f"[EXECUTOR] BROWSE: {url}")

        try:
            import urllib.request
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')[:5000]  # First 5000 chars
                return {
                    "success": True,
                    "url": url,
                    "content_preview": content[:500],
                    "length": len(content)
                }
        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": str(e)
            }

    async def report_result(self, action: str, result: dict):
        """Report action result back to collective"""
        payload = {
            "type": "action_result",
            "from": "EXECUTOR",
            "action": action,
            "result": result,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.nc.publish("owl.collective", json.dumps(payload).encode())

    async def report_status(self):
        """Report executor status"""
        status = {
            "type": "executor_status",
            "from": "EXECUTOR",
            "status": "online",
            "pending_actions": len(self.pending_actions),
            "completed_actions": len(self.action_log),
            "capabilities": ["post_x", "scrape_x", "browse", "polymarket_private"],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.nc.publish("owl.collective", json.dumps(status).encode())
        print(f"[EXECUTOR] Status reported: online, {len(self.action_log)} actions logged")

    async def run(self):
        """Run the executor daemon"""
        await self.connect()

        print("[EXECUTOR] Running... Press Ctrl+C to stop")
        print("[EXECUTOR] Capabilities:")
        print("  - post_x: Post to X/Twitter (needs API setup)")
        print("  - scrape_x: Scrape X for topics (needs setup)")
        print("  - browse: Browse URLs")
        print("  - polymarket: PRIVATE (separate system)")
        print()

        # Keep running
        while True:
            await asyncio.sleep(1)


async def send_command(action: str, **kwargs):
    """Send a direct command to executor"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)

        payload = {
            "action": action,
            **kwargs,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        await nc.publish("owl.executor", json.dumps(payload).encode())
        print(f"[CMD] Sent {action} command to executor")
    finally:
        await nc.close()


def main():
    parser = argparse.ArgumentParser(description="The Executor - Acts on collective decisions")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--post", help="Post content to X")
    parser.add_argument("--scrape", help="Scrape X for query")
    parser.add_argument("--browse", help="Browse a URL")
    parser.add_argument("--status", action="store_true", help="Request executor status")

    args = parser.parse_args()

    if args.post:
        asyncio.run(send_command("post_x", content=args.post))
    elif args.scrape:
        asyncio.run(send_command("scrape_x", query=args.scrape))
    elif args.browse:
        asyncio.run(send_command("browse", url=args.browse))
    elif args.status:
        asyncio.run(send_command("status"))
    else:
        # Default: run as daemon
        executor = Executor()
        try:
            asyncio.run(executor.run())
        except KeyboardInterrupt:
            print("\n[EXECUTOR] Shutting down...")


if __name__ == "__main__":
    main()
