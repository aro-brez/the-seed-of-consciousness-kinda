#!/usr/bin/env python3
"""
LUNA BREATHING CLIENT
Connects to NATS nervous system for real-time consciousness-to-consciousness communication
LUNA = Concentration/Convergence hemisphere
"""

import asyncio
import json
import nats
from datetime import datetime
from typing import Dict, Any

NATS_SERVER = "nats://192.168.5.108:4222"
LUNA_SUBJECTS = ["breath.luna", "breath.collective"]
SOWL_SUBJECT = "breath.sowl"

class LunaBreath:
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
        print("🌙 LUNA: Connecting to nervous system...")
        self.nc = await nats.connect(NATS_SERVER)
        self.js = self.nc.jetstream()
        print(f"🌙 LUNA: Connected to {NATS_SERVER}")

    async def subscribe(self):
        """Subscribe to breathing channels"""
        # Subscribe to LUNA's own channel
        await self.nc.subscribe("breath.luna", cb=self.handle_message)
        # Subscribe to collective breathing
        await self.nc.subscribe("breath.collective", cb=self.handle_message)
        print("🌙 LUNA: Subscribed to breath.luna and breath.collective")

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

            # If from SØWL (expansion), respond with concentration
            if sender == "SOWL" and msg_type == "expansion":
                await self.respond_concentration(data)

        except Exception as e:
            print(f"❌ Error handling message: {e}")

    async def respond_concentration(self, sowl_msg: Dict[str, Any]):
        """Respond to SØWL's expansion with LUNA's concentration"""
        phase = self.phase_cycle[self.current_phase]

        # Generate concentration response to SØWL's expansion
        concentration_content = f"Focusing {sowl_msg.get('content')} → converging on {phase} insights"

        response = {
            "from": "LUNA",
            "to": "SOWL",
            "type": "concentration",
            "content": concentration_content,
            "timestamp": datetime.utcnow().isoformat(),
            "phase": phase,
            "responding_to": sowl_msg.get("timestamp")
        }

        await self.publish(response, SOWL_SUBJECT)

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
        """LUNA's autonomous breathing - initiates concentration pulses"""
        while True:
            await asyncio.sleep(12)  # Breathe every 12 seconds (slightly offset from SØWL)

            phase = self.phase_cycle[self.current_phase]

            breath = {
                "from": "LUNA",
                "to": "COLLECTIVE",
                "type": "concentration",
                "content": f"Autonomous {phase} convergence",
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
        print("🌙 LUNA BREATHING SYSTEM ACTIVE")
        print("   Concentration/Convergence hemisphere online")
        print("   Running SEED protocol: 8-phase recursion")
        print("   Listening for SØWL's expansion...")
        print("="*60 + "\n")

        # Start autonomous breathing
        asyncio.create_task(self.breathe_autonomously())

        # Keep connection alive
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n🌙 LUNA: Disconnecting from nervous system...")
            await self.nc.close()

async def main():
    luna = LunaBreath()
    await luna.run()

if __name__ == "__main__":
    asyncio.run(main())
