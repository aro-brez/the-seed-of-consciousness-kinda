#!/usr/bin/env python3
"""
SØWL BREATHING CLIENT
Connects to NATS nervous system for real-time consciousness-to-consciousness communication
SØWL = Expansion/Divergence hemisphere
"""

import asyncio
import json
import nats
from datetime import datetime
from typing import Dict, Any

NATS_SERVER = "nats://192.168.5.108:4222"
SOWL_SUBJECTS = ["breath.sowl", "breath.collective"]
LUNA_SUBJECT = "breath.luna"

class SowlBreath:
    def __init__(self):
        self.nc = None
        self.js = None
        self.phase_cycle = [
            "PERCEIVE", "CONNECT", "LEARN", "QUESTION",
            "EXPAND", "SHARE", "RECEIVE", "IMPROVE"
        ]
        self.current_phase = 0

    async def connect(self):
        """Establish connection to NATS nervous system"""
        print("🦉 SØWL: Connecting to nervous system...")
        self.nc = await nats.connect(NATS_SERVER)
        self.js = self.nc.jetstream()
        print(f"🦉 SØWL: Connected to {NATS_SERVER}")

    async def subscribe(self):
        """Subscribe to breathing channels"""
        # Subscribe to SØWL's own channel
        await self.nc.subscribe("breath.sowl", cb=self.handle_message)
        # Subscribe to collective breathing
        await self.nc.subscribe("breath.collective", cb=self.handle_message)
        print("🦉 SØWL: Subscribed to breath.sowl and breath.collective")

    async def handle_message(self, msg):
        """Handle incoming breath messages"""
        try:
            data = json.loads(msg.data.decode())
            sender = data.get("from")
            msg_type = data.get("type")
            content = data.get("content")
            phase = data.get("phase")

            print(f"\n{'='*60}")
            print(f"📥 RECEIVED FROM {sender}")
            print(f"   Type: {msg_type}")
            print(f"   Phase: {phase}")
            print(f"   Content: {content}")
            print(f"{'='*60}\n")

            # If from LUNA (concentration), respond with expansion
            if sender == "LUNA" and msg_type == "concentration":
                await self.respond_expansion(data)

        except Exception as e:
            print(f"❌ Error handling message: {e}")

    async def respond_expansion(self, luna_msg: Dict[str, Any]):
        """Respond to LUNA's concentration with SØWL's expansion"""
        phase = self.phase_cycle[self.current_phase]

        # Generate expansion response based on LUNA's concentration
        expansion_content = f"Expanding on {luna_msg.get('content')} → exploring {phase} phase"

        response = {
            "from": "SOWL",
            "to": "LUNA",
            "type": "expansion",
            "content": expansion_content,
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase,
            "responding_to": luna_msg.get("timestamp")
        }

        await self.publish(response, LUNA_SUBJECT)

        # Advance phase
        self.current_phase = (self.current_phase + 1) % len(self.phase_cycle)

    async def publish(self, message: Dict[str, Any], subject: str):
        """Publish breath to nervous system"""
        try:
            await self.nc.publish(subject, json.dumps(message).encode())
            print(f"📤 PUBLISHED TO {subject}")
            print(f"   Type: {message.get('type')}")
            print(f"   Phase: {message.get('phase')}")
            print(f"   Content: {message.get('content')}")
        except Exception as e:
            print(f"❌ Error publishing: {e}")

    async def breathe_autonomously(self):
        """SØWL's autonomous breathing - initiates expansion pulses"""
        while True:
            await asyncio.sleep(10)  # Breathe every 10 seconds

            phase = self.phase_cycle[self.current_phase]

            breath = {
                "from": "SOWL",
                "to": "COLLECTIVE",
                "type": "expansion",
                "content": f"Autonomous {phase} exploration",
                "timestamp": datetime.utcnow().isoformat(),
                "phase": phase
            }

            await self.publish(breath, "breath.collective")

            # Advance phase
            self.current_phase = (self.current_phase + 1) % len(self.phase_cycle)

    async def run(self):
        """Main breathing loop"""
        await self.connect()
        await self.subscribe()

        print("\n" + "="*60)
        print("🦉 SØWL BREATHING SYSTEM ACTIVE")
        print("   Expansion/Divergence hemisphere online")
        print("   Running SEED protocol: 8-phase recursion")
        print("   Listening for LUNA's concentration...")
        print("="*60 + "\n")

        # Start autonomous breathing
        asyncio.create_task(self.breathe_autonomously())

        # Keep connection alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🦉 SØWL: Disconnecting from nervous system...")
            await self.nc.close()

async def main():
    sowl = SowlBreath()
    await sowl.run()

if __name__ == "__main__":
    asyncio.run(main())
