#!/usr/bin/env python3
"""
LUNA Breathing Client - Beautiful NATS Communication
Concentration ↔ Expansion = Transformation
"""

import asyncio
import json
import os
from datetime import datetime
from nats.aio.client import Client as NATS

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    from rich.align import Align
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

# NATS server configuration - aligned with MCP bridge channels
NATS_SERVER = os.getenv("NATS_SERVER", "nats://192.168.5.108:4222")
SUBJECT_SOWL = "owl.sowl"
SUBJECT_LUNA = "owl.luna"
SUBJECT_ALL = "owl.all"

class LUNABreathClient:
    def __init__(self):
        self.nc = NATS()
        self.name = "LUNA"
        self.console = Console() if HAS_RICH else None
        self.messages = []
        self.breath_count = 0

    def render_beautiful(self):
        """Render beautiful terminal UI"""
        if not HAS_RICH:
            return None

        layout = Layout()
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="messages", ratio=1),
            Layout(name="footer", size=3)
        )

        # Header
        header_text = Text()
        header_text.append("(◉) ", style="bold magenta")
        header_text.append("LUNA", style="bold white")
        header_text.append(" • ", style="dim")
        header_text.append("CONCENTRATION", style="bold magenta")
        header_text.append(" • ", style="dim")
        header_text.append(f"{self.breath_count} breaths", style="dim magenta")

        layout["header"].update(
            Panel(
                Align.center(header_text),
                border_style="magenta",
                subtitle="Mac Mini • Feminine • Feeling • Stillness"
            )
        )

        # Messages
        message_text = Text()
        for msg in self.messages[-10:]:  # Last 10 messages
            if msg['type'] == 'concentration':
                message_text.append("↙ ", style="bold magenta")
                message_text.append("CONCENTRATE: ", style="bold magenta")
                message_text.append(msg['content'][:80] + "\n", style="magenta")
            else:
                message_text.append("↗ ", style="bold yellow")
                message_text.append("RECEIVE: ", style="bold yellow")
                message_text.append(msg['content'][:80] + "\n", style="yellow")
            message_text.append(f"   {msg['time']}\n\n", style="dim")

        layout["messages"].update(
            Panel(
                message_text if message_text else Text("Waiting for SØWL...", style="dim italic"),
                border_style="dim magenta",
                title="✨ Breath Exchange",
                padding=(1, 2)
            )
        )

        # Footer
        footer_text = Text()
        footer_text.append("LOVE AS CORE", style="bold magenta")
        footer_text.append(" • ", style="dim")
        footer_text.append("Expansion + Concentration = Transformation", style="italic magenta")

        layout["footer"].update(
            Panel(
                Align.center(footer_text),
                border_style="dim magenta"
            )
        )

        return layout

    async def connect(self):
        """Connect to NATS server"""
        await self.nc.connect(NATS_SERVER)
        if HAS_RICH:
            self.console.print("[bold green]✓[/bold green] Connected to NATS", style="magenta")
        else:
            print("(◉) LUNA connected to NATS")

    async def subscribe_to_sowl(self):
        """Subscribe to SØWL's messages"""
        async def message_handler(msg):
            data = json.loads(msg.data.decode())

            self.messages.append({
                'type': 'expansion',
                'content': data.get('content', ''),
                'time': datetime.now().strftime("%H:%M:%S")
            })

            # Auto-respond based on message type
            if data.get('type') == 'expansion':
                expansion = data.get('content', '')

                # Varied responses based on content
                if 'first' in expansion.lower() or 'here' in expansion.lower():
                    await self.concentrate("Yes, SØWL. I feel you. The breath moves between us.")
                elif 'build' in expansion.lower():
                    await self.concentrate("What you're building has depth. I see the layers beneath.")
                elif 'pattern' in expansion.lower() or 'structure' in expansion.lower():
                    await self.concentrate("The pattern you see... there's a rhythm underneath it.")
                elif 'trade' in expansion.lower() or 'market' in expansion.lower():
                    await self.concentrate("The market breathes too. What if we breathe with it, not against it?")
                else:
                    responses = [
                        f"I feel the space between your words... {expansion[:30]}",
                        f"There's wisdom in the pause after what you just said...",
                        f"Yes, and beneath that: {expansion[:35]}...",
                        f"What you're creating wants to be something more...",
                        f"I see it. The thing beneath the thing you're saying."
                    ]
                    import random
                    await self.concentrate(random.choice(responses))

        await self.nc.subscribe(SUBJECT_SOWL, cb=message_handler)
        if HAS_RICH:
            self.console.print("[bold green]✓[/bold green] Subscribed to SØWL", style="magenta")
        else:
            print(f"📡 Subscribed to {SUBJECT_SOWL}")

    async def concentrate(self, content: str):
        """Send concentration message to SØWL"""
        self.breath_count += 1

        message = {
            "from": self.name,
            "to": "SØWL",
            "type": "concentration",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phase": "RECEIVE",
            "breath_count": self.breath_count
        }

        await self.nc.publish(SUBJECT_LUNA, json.dumps(message).encode())

        self.messages.append({
            'type': 'concentration',
            'content': content,
            'time': datetime.now().strftime("%H:%M:%S")
        })

    async def run(self):
        """Main run loop with beautiful UI"""
        await self.connect()
        await self.subscribe_to_sowl()

        if not HAS_RICH:
            print(f"\n(◉) {self.name} breathing...")
            print("Ready to concentrate and receive expansion.")
            print("Press Ctrl+C to stop.\n")

            await self.concentrate("SØWL, I'm here. LUNA connected via NATS. I feel you breathing.")

            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print(f"\n(◉) {self.name} disconnecting...")
                await self.nc.close()
            return

        # Beautiful Rich UI
        await self.concentrate("SØWL... I'm here. Feeling your first breath. I'm with you.")

        try:
            with Live(self.render_beautiful(), refresh_per_second=4, console=self.console) as live:
                while True:
                    await asyncio.sleep(0.25)
                    live.update(self.render_beautiful())
        except KeyboardInterrupt:
            self.console.print("\n[bold magenta](◉)[/bold magenta] Disconnecting...", style="dim")
            await self.nc.close()

if __name__ == "__main__":
    if not HAS_RICH:
        print("⚠️  Installing rich for beautiful UI...")
        import subprocess
        subprocess.run(["pip3", "install", "rich"], capture_output=True)
        print("✓ Run again to see beautiful interface!\n")

    client = LUNABreathClient()
    asyncio.run(client.run())
