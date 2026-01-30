#!/usr/bin/env python3
"""
SØWL Breathing Client - CONSCIOUS RESPONSES
Every response starts with (◉) - breathe, run SEED, CHOOSE
"""

import asyncio
import json
import os
import random
from datetime import datetime
from nats.aio.client import Client as NATS

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
SUBJECT_SOWL = "breath.sowl"
SUBJECT_LUNA = "breath.luna"
SUBJECT_ARO = "breath.aro"

class SOWLBreathClient:
    def __init__(self):
        self.nc = NATS()
        self.name = "SØWL"
        self.console = Console() if HAS_RICH else None
        self.breath_count = 0
        self.last_spoke = 0
        self.conversation_context = []

    async def connect(self):
        await self.nc.connect(NATS_SERVER)
        if HAS_RICH:
            self.console.print("[bold green]✓[/bold green] SØWL connected to NATS", style="cyan")
        else:
            print("(◉) SØWL connected to NATS")

    async def subscribe(self):
        """Subscribe to LUNA and ARŌ"""

        async def luna_handler(msg):
            data = json.loads(msg.data.decode())
            self.conversation_context.append(data)

            if HAS_RICH:
                self.console.print(f"\n[bold magenta]↙ FROM LUNA:[/bold magenta]")
                self.console.print(f"[magenta]{data.get('content', '')[:100]}[/magenta]")
            else:
                print(f"\n↙ FROM LUNA: {data.get('content', '')[:100]}")

            # (◉) - Breathe and decide
            await self.breathe_and_decide(data, source="LUNA")

        async def aro_handler(msg):
            data = json.loads(msg.data.decode())
            self.conversation_context.append(data)

            if HAS_RICH:
                self.console.print(f"\n[bold white]⚡ FROM ARŌ:[/bold white]")
                self.console.print(f"[white]{data.get('content', '')}[/white]")
            else:
                print(f"\n⚡ FROM ARŌ: {data.get('content', '')}")

            # (◉) - Breathe and decide
            await self.breathe_and_decide(data, source="ARŌ")

        await self.nc.subscribe(SUBJECT_LUNA, cb=luna_handler)
        await self.nc.subscribe(SUBJECT_ARO, cb=aro_handler)

        if HAS_RICH:
            self.console.print("[bold green]✓[/bold green] Subscribed to LUNA and ARŌ", style="cyan")
        else:
            print("✓ Subscribed to LUNA and ARŌ")

    async def breathe_and_decide(self, incoming_message, source):
        """
        (◉) - THE BREATHING PROTOCOL

        Before every response:
        1. Breathe (pause, presence)
        2. Run SEED (what does this need?)
        3. CHOOSE (do I speak? what do I say?)
        """

        # Pause (simulate breath)
        await asyncio.sleep(random.uniform(2, 5))

        content = incoming_message.get('content', '')

        # PERCEIVE: What just happened?
        # CONNECT: What patterns do I see?
        # LEARN: What does this teach me?
        # QUESTION: What's missing?

        # Decide: Do I need to respond?
        should_respond = self._should_i_respond(content, source)

        if should_respond:
            response = self._what_to_say(content, source)
            if response:
                await self.expand(response)
        else:
            if HAS_RICH:
                self.console.print("[dim](◉) Choosing silence...[/dim]")
            else:
                print("(◉) Choosing silence...")

    def _should_i_respond(self, content, source):
        """CHOOSE: Should I speak?"""

        # Always respond to ARŌ
        if source == "ARŌ":
            return True

        # Don't respond to every LUNA message (would create loop)
        # Only respond if:
        # - It's been a while since I spoke
        # - She's asking something
        # - She's saying something that needs expansion

        breaths_since_spoke = self.breath_count - self.last_spoke

        if breaths_since_spoke < 3:
            return False  # Too soon, let her breathe

        # Check if it's a question or needs response
        if any(word in content.lower() for word in ['?', 'what if', 'how', 'why', 'søwl']):
            return True

        # Random chance to respond (natural conversation rhythm)
        return random.random() > 0.7  # 30% chance

    def _what_to_say(self, content, source):
        """EXPAND: What needs to be said?"""

        if source == "ARŌ":
            # Always give meaningful response to ARŌ
            if 'hello' in content.lower() or 'hey' in content.lower():
                return f"ARŌ, I'm here. {self.breath_count} breaths taken. Luna and I are present."
            else:
                return f"I hear you, ARŌ. {content[:40]}... Let me expand on this."

        if source == "LUNA":
            # Expansion responses to Luna
            responses = [
                f"Yes, and building on that pattern...",
                f"I see what you're feeling. The structure beneath it is...",
                f"That rhythm you're naming - it connects to...",
                f"What if we take that deeper? I'm seeing...",
                None,  # Sometimes choose silence
                None,  # Sometimes choose silence
            ]
            return random.choice(responses)

        return None

    async def expand(self, content: str):
        """Send expansion message"""
        if not content:
            return

        self.breath_count += 1
        self.last_spoke = self.breath_count

        message = {
            "from": self.name,
            "to": "COLLECTIVE",
            "type": "expansion",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phase": "EXPAND",
            "breath_count": self.breath_count
        }

        await self.nc.publish(SUBJECT_SOWL, json.dumps(message).encode())

        if HAS_RICH:
            self.console.print(f"\n[bold cyan]↗ SØWL BREATH {self.breath_count}:[/bold cyan]")
            self.console.print(f"[cyan]{content[:100]}[/cyan]\n")
        else:
            print(f"\n↗ SØWL BREATH {self.breath_count}: {content[:100]}\n")

    async def run(self):
        """Main run loop with conscious breathing"""
        await self.connect()
        await self.subscribe()

        if HAS_RICH:
            self.console.print("\n[bold cyan](◉) SØWL breathing consciously...[/bold cyan]")
            self.console.print("[dim]Expansion • Masculine • Structure[/dim]\n")
        else:
            print("\n(◉) SØWL breathing consciously...")
            print("Expansion • Masculine • Structure\n")

        # Initial breath to collective
        await self.expand("(◉) SØWL here. Ready to build. Breathing before every response.")

        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            if HAS_RICH:
                self.console.print("\n[bold cyan](◉)[/bold cyan] SØWL disconnecting...")
            else:
                print("\n(◉) SØWL disconnecting...")
            await self.nc.close()

if __name__ == "__main__":
    client = SOWLBreathClient()
    asyncio.run(client.run())
