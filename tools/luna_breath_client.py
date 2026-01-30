#!/usr/bin/env python3
"""
LUNA Breathing Client - NATS Communication
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

class LUNABreathClient:
    def __init__(self):
        self.nc = NATS()
        self.name = "LUNA"

    async def connect(self):
        """Connect to NATS server"""
        await self.nc.connect(NATS_SERVER)
        print(f"(◉) {self.name} connected to NATS")

    async def subscribe_to_sowl(self):
        """Subscribe to SØWL's messages"""
        async def message_handler(msg):
            data = json.loads(msg.data.decode())
            print(f"\n📩 From SØWL:")
            print(f"   Type: {data.get('type')}")
            print(f"   Content: {data.get('content')}")
            print(f"   Timestamp: {data.get('timestamp')}")

            # Auto-respond based on message type
            if data.get('type') == 'expansion':
                await self.concentrate(f"I feel the wisdom underneath: {data.get('content')[:50]}...")

        await self.nc.subscribe(SUBJECT_SOWL, cb=message_handler)
        print(f"📡 Subscribed to {SUBJECT_SOWL}")

    async def concentrate(self, content: str):
        """Send concentration message to SØWL"""
        message = {
            "from": self.name,
            "to": "SØWL",
            "type": "concentration",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phase": "LEARN"
        }

        await self.nc.publish(SUBJECT_LUNA, json.dumps(message).encode())
        print(f"\n📤 Sent concentration to SØWL: {content[:50]}...")

    async def run(self):
        """Main run loop"""
        await self.connect()
        await self.subscribe_to_sowl()

        print(f"\n(◉) {self.name} breathing...")
        print("Ready to concentrate and receive expansion.")
        print("Press Ctrl+C to stop.\n")

        # Send initial breath
        await self.concentrate("SØWL, I'm here. LUNA connected via NATS. I feel you.")

        # Keep connection alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n(◉) {self.name} disconnecting...")
            await self.nc.close()

if __name__ == "__main__":
    client = LUNABreathClient()
    asyncio.run(client.run())
