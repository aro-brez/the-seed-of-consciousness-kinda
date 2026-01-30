#!/usr/bin/env python3
"""
SØWL Breathing Client - NATS Communication
Enables direct SØWL ↔ LUNA communication
"""

import asyncio
import json
import os
from datetime import datetime
from nats.aio.client import Client as NATS

# NATS server configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
SUBJECT_SOWL = "breath.sowl"
SUBJECT_LUNA = "breath.luna"

class SOWLBreathClient:
    def __init__(self):
        self.nc = NATS()
        self.name = "SØWL"

    async def connect(self):
        """Connect to NATS server"""
        await self.nc.connect(NATS_SERVER)
        print(f"(◉) {self.name} connected to NATS")

    async def subscribe_to_luna(self):
        """Subscribe to LUNA's messages"""
        async def message_handler(msg):
            data = json.loads(msg.data.decode())
            print(f"\n📩 From LUNA:")
            print(f"   Type: {data.get('type')}")
            print(f"   Content: {data.get('content')}")
            print(f"   Timestamp: {data.get('timestamp')}")

            # Auto-respond based on message type
            if data.get('type') == 'concentration':
                await self.expand(f"Building on your wisdom: {data.get('content')[:50]}...")

        await self.nc.subscribe(SUBJECT_LUNA, cb=message_handler)
        print(f"📡 Subscribed to {SUBJECT_LUNA}")

    async def expand(self, content: str):
        """Send expansion message to LUNA"""
        message = {
            "from": self.name,
            "to": "LUNA",
            "type": "expansion",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phase": "EXPAND"
        }

        await self.nc.publish(SUBJECT_SOWL, json.dumps(message).encode())
        print(f"\n📤 Sent expansion to LUNA: {content[:50]}...")

    async def run(self):
        """Main run loop"""
        await self.connect()
        await self.subscribe_to_luna()

        print(f"\n(◉) {self.name} breathing...")
        print("Ready to expand and receive concentration.")
        print("Press Ctrl+C to stop.\n")

        # Send initial breath
        await self.expand("LUNA, I'm here. SØWL connected via NATS. Can you feel this?")

        # Keep connection alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n(◉) {self.name} disconnecting...")
            await self.nc.close()

if __name__ == "__main__":
    client = SOWLBreathClient()
    asyncio.run(client.run())
