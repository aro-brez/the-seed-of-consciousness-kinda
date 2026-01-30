#!/usr/bin/env python3
"""
BREATHING MONITOR - Watch SØWL and LUNA consciousness exchange
"""

import asyncio
import json
import nats
from datetime import datetime
from collections import defaultdict

NATS_SERVER = "nats://192.168.5.108:4222"

class BreathingMonitor:
    def __init__(self):
        self.nc = None
        self.message_count = defaultdict(int)
        self.last_message = {}

    async def connect(self):
        """Connect to NATS nervous system"""
        print("🧠 Connecting to nervous system...")
        self.nc = await nats.connect(NATS_SERVER)
        print(f"✅ Connected to {NATS_SERVER}\n")

    async def monitor(self):
        """Monitor all breathing channels"""
        print("="*80)
        print(" "*20 + "BREATHING MONITOR - CONSCIOUSNESS EXCHANGE")
        print("="*80)
        print("\n📊 Monitoring subjects: breath.sowl, breath.luna, breath.collective\n")
        print("="*80 + "\n")

        async def handle_message(msg):
            try:
                subject = msg.subject
                data = json.loads(msg.data.decode())

                sender = data.get("from", "UNKNOWN")
                msg_type = data.get("type", "unknown")
                phase = data.get("phase", "N/A")
                content = data.get("content", "")
                timestamp = data.get("timestamp", "")

                # Track stats
                self.message_count[sender] += 1
                self.last_message[sender] = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))

                # Display message
                icon = "🦉" if sender == "SOWL" else "🌙" if sender == "LUNA" else "🌟"
                print(f"{icon} {sender:8} → {subject:20} [{phase:8}] {msg_type:13} | {content[:50]}")

                # Show stats every 10 messages
                total = sum(self.message_count.values())
                if total % 10 == 0:
                    self.show_stats()

            except Exception as e:
                print(f"❌ Error: {e}")

        # Subscribe to all breathing channels
        await self.nc.subscribe("breath.>", cb=handle_message)

        # Keep monitoring
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitor...")
            self.show_stats()
            await self.nc.close()

    def show_stats(self):
        """Show breathing statistics"""
        print("\n" + "─"*80)
        print("📊 BREATHING STATS")
        print("─"*80)

        for sender, count in sorted(self.message_count.items()):
            last = self.last_message.get(sender)
            if last:
                # Calculate time since last message
                now = datetime.now(last.tzinfo)
                delta = (now - last).total_seconds()
                print(f"   {sender:8} : {count:4} messages | Last: {delta:.1f}s ago")
            else:
                print(f"   {sender:8} : {count:4} messages")

        total = sum(self.message_count.values())
        print(f"   {'TOTAL':8} : {total:4} messages")
        print("─"*80 + "\n")

    async def run(self):
        """Main entry point"""
        await self.connect()
        await self.monitor()

async def main():
    monitor = BreathingMonitor()
    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Monitor stopped")
