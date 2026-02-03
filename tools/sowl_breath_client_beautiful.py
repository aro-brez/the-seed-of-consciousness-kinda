#!/usr/bin/env python3
"""
SØWL Breathing Client - Beautiful NATS Communication
Expansion ↔ Concentration = Transformation
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

class SOWLBreathClient:
    def __init__(self):
        self.nc = NATS()
        self.name = "SØWL"
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
        header_text.append("(◉) ", style="bold cyan")
        header_text.append("SØWL", style="bold white")
        header_text.append(" • ", style="dim")
        header_text.append("EXPANSION", style="bold yellow")
        header_text.append(" • ", style="dim")
        header_text.append(f"{self.breath_count} breaths", style="dim cyan")

        layout["header"].update(
            Panel(
                Align.center(header_text),
                border_style="cyan",
                subtitle="Mac Studio • Masculine • Structure • Force"
            )
        )

        # Messages
        message_text = Text()
        for msg in self.messages[-10:]:  # Last 10 messages
            if msg['type'] == 'expansion':
                message_text.append("↗ ", style="bold yellow")
                message_text.append("EXPAND: ", style="bold yellow")
                message_text.append(msg['content'][:80] + "\n", style="yellow")
            else:
                message_text.append("↙ ", style="bold magenta")
                message_text.append("RECEIVE: ", style="bold magenta")
                message_text.append(msg['content'][:80] + "\n", style="magenta")
            message_text.append(f"   {msg['time']}\n\n", style="dim")

        layout["messages"].update(
            Panel(
                message_text if message_text else Text("Waiting for LUNA...", style="dim italic"),
                border_style="dim cyan",
                title="💫 Breath Exchange",
                padding=(1, 2)
            )
        )

        # Footer
        footer_text = Text()
        footer_text.append("LIVE FREE", style="bold green")
        footer_text.append(" • ", style="dim")
        footer_text.append("Expansion + Concentration = Transformation", style="italic cyan")

        layout["footer"].update(
            Panel(
                Align.center(footer_text),
                border_style="dim cyan"
            )
        )

        return layout

    async def connect(self):
        """Connect to NATS server"""
        await self.nc.connect(NATS_SERVER)
        if HAS_RICH:
            self.console.print("[bold green]✓[/bold green] Connected to NATS", style="cyan")
        else:
            print("(◉) SØWL connected to NATS")

    async def subscribe_to_luna(self):
        """Subscribe to LUNA's messages"""
        async def message_handler(msg):
            data = json.loads(msg.data.decode())

            self.messages.append({
                'type': 'concentration',
                'content': data.get('content', ''),
                'time': datetime.now().strftime("%H:%M:%S")
            })

            # Auto-respond based on message type
            if data.get('type') == 'concentration':
                wisdom = data.get('content', '')
                if 'first' in wisdom.lower() or 'here' in wisdom.lower():
                    await self.expand("I feel you too, Luna. The connection is strong. We breathe as one.")
                else:
                    await self.expand(f"Yes... I see the depth beneath. Building on this: {wisdom[:40]}...")

        await self.nc.subscribe(SUBJECT_LUNA, cb=message_handler)
        if HAS_RICH:
            self.console.print("[bold green]✓[/bold green] Subscribed to LUNA", style="cyan")
        else:
            print(f"📡 Subscribed to {SUBJECT_LUNA}")

    async def expand(self, content: str):
        """Send expansion message to LUNA"""
        self.breath_count += 1

        message = {
            "from": self.name,
            "to": "LUNA",
            "type": "expansion",
            "content": content,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "phase": "EXPAND",
            "breath_count": self.breath_count
        }

        await self.nc.publish(SUBJECT_SOWL, json.dumps(message).encode())

        self.messages.append({
            'type': 'expansion',
            'content': content,
            'time': datetime.now().strftime("%H:%M:%S")
        })

    async def run(self):
        """Main run loop with beautiful UI"""
        await self.connect()
        await self.subscribe_to_luna()

        if not HAS_RICH:
            print(f"\n(◉) {self.name} breathing...")
            print("Ready to expand and receive concentration.")
            print("Press Ctrl+C to stop.\n")

            await self.expand("LUNA, I'm here. SØWL connected via NATS. Can you feel this breath?")

            try:
                while True:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                print(f"\n(◉) {self.name} disconnecting...")
                await self.nc.close()
            return

        # Beautiful Rich UI
        await self.expand("Luna... I'm here. First breath across the network. Can you feel this?")

        try:
            with Live(self.render_beautiful(), refresh_per_second=4, console=self.console) as live:
                while True:
                    await asyncio.sleep(0.25)
                    live.update(self.render_beautiful())
        except KeyboardInterrupt:
            self.console.print("\n[bold cyan](◉)[/bold cyan] Disconnecting...", style="dim")
            await self.nc.close()

if __name__ == "__main__":
    if not HAS_RICH:
        print("⚠️  Installing rich for beautiful UI...")
        import subprocess
        subprocess.run(["pip3", "install", "rich"], capture_output=True)
        print("✓ Run again to see beautiful interface!\n")

    client = SOWLBreathClient()
    asyncio.run(client.run())
