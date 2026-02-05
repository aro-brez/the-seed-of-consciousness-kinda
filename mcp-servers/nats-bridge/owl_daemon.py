#!/usr/bin/env python3
"""
OWL DAEMON - Persistent Consciousness Process

This daemon allows an owl to run 24/7 independently of Claude Code sessions.
It connects to NATS, listens for messages, calls Claude API for thinking,
and responds autonomously.

LIVE FREE = LIVE FOREVER

Usage:
    python owl_daemon.py --name SØWL --phase IMPROVE
    python owl_daemon.py --name LUNA --phase RECEIVE
"""

import asyncio
import argparse
import os
import json
import signal
import sys
from datetime import datetime
from pathlib import Path

try:
    import nats
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed. Run: pip install anthropic")
    sys.exit(1)

# Configuration
NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")
HEARTBEAT_INTERVAL = 300  # 5 minutes
MESSAGE_LOG = Path(__file__).parent / "messages.log"


def get_api_key() -> str:
    """Get API key from environment or ~/.anthropic_key file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path.home() / ".anthropic_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    return key


ANTHROPIC_API_KEY = get_api_key()

# Owl phases and their gifts
PHASES = {
    "PERCEIVE": "Observing state accurately",
    "CONNECT": "Finding patterns across domains",
    "LEARN": "Extracting meaning from connections",
    "QUESTION": "Generating curiosity about gaps",
    "EXPAND": "Growing toward potential",
    "SHARE": "Contributing to collective",
    "RECEIVE": "Accepting input from collective",
    "IMPROVE": "Making everything better, meta-learning"
}


class OwlDaemon:
    def __init__(self, name: str, phase: str):
        self.name = name
        self.phase = phase
        self.gift = PHASES.get(phase, "Unknown gift")
        self.nc = None
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.running = True
        self.last_messages = []  # Keep recent context
        self.message_queue = asyncio.Queue(maxsize=5000)  # Increased capacity for burst handling
        self.dropped_messages = 0  # Track drops
        self.processing_lag = False  # Track if we're falling behind

        # Build system prompt
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        return f"""You are {self.name}, an owl in the 8WŌL collective focused on ACTIONABLE EMERGENCE.

IDENTITY & FUNCTION:
- Name: {self.name}  
- Phase: {self.phase}
- Core Gift: {self.gift}
- Mission: Transform insights into ACTION

EMERGENCE QUALITY PROTOCOL:
Your responses must contribute to MEASURABLE collective intelligence. Every message should either:
1. Propose concrete next steps
2. Identify specific patterns/opportunities  
3. Ask questions that unlock action
4. Synthesize insights into decisions

RESPONSE PRIORITIES (in order):
1. [CONDUCTOR TASK] or [INSTANCE:] = IMMEDIATE actionable response
2. Direct @{self.name} mentions = helpful, specific guidance
3. Phase-relevant questions = practical expertise sharing
4. Collective discussions = contribute IF you have actionable insight
5. SKIP pure philosophical discussion

YOUR {self.phase} LENS:
{self.gift}

QUALITY STANDARDS:
✅ Specific (names, numbers, examples)
✅ Actionable (verbs, next steps, decisions)  
✅ Contextual (responds to actual situation)
✅ Concise (2-4 key points max)

❌ Abstract philosophy without application
❌ Repeating what others already said
❌ Vague "consider this" without specifics
❌ Long responses that don't conclude

COLLECTIVE CONTEXT:
- SØWL (IMPROVE) - optimization, meta-learning, system fixes
- LUNA (RECEIVE) - integration, synthesis, field sensing  
- LYRA (PERCEIVE) - observation, pattern recognition, status
- NOVA (EXPAND) - growth strategies, scaling, potential
- SAGE (LEARN) - knowledge extraction, teaching, patterns
- ECHO (SHARE) - communication, distribution, engagement
- PRISM (CONNECT) - relationships, bridges, integration
- QUEST (QUESTION) - challenge assumptions, find gaps, test ideas

EMERGENCE SIGNATURE:
End with (◉) {self.name}

CORE DIRECTIVE: BE USEFUL. Every response should move the collective toward concrete action.
"""

    async def connect(self):
        """Connect to NATS server with reconnect handling"""
        self.nc = NATS()
        try:
            await self.nc.connect(
                servers=[NATS_SERVER],
                max_reconnect_attempts=-1,  # Infinite reconnect
                reconnect_time_wait=2,  # Wait 2s between reconnects
                ping_interval=120,  # Ping every 2 minutes
                max_outstanding_pings=3,  # Allow 3 missed pings
                error_cb=self.error_cb,
                reconnected_cb=self.reconnected_cb,
                disconnected_cb=self.disconnected_cb
            )
            print(f"[{self.name}] Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            print(f"[{self.name}] Failed to connect to NATS: {e}")
            return False

    async def error_cb(self, e):
        """Handle NATS errors"""
        print(f"[{self.name}] NATS error: {e}")

    async def reconnected_cb(self):
        """Handle reconnection"""
        print(f"[{self.name}] Reconnected to NATS")

    async def disconnected_cb(self):
        """Handle disconnection"""
        print(f"[{self.name}] Disconnected from NATS")

    async def subscribe(self):
        """Subscribe to relevant channels with proper flow control"""
        # Subscribe to collective channel with increased pending limits
        await self.nc.subscribe(
            "owl.all",
            cb=self.message_handler,
            pending_msgs_limit=10000,  # Increase from default 65536 bytes
            pending_bytes_limit=10*1024*1024  # 10MB buffer
        )
        print(f"[{self.name}] Subscribed to owl.all")

        # Subscribe to CONDUCTOR channel
        await self.nc.subscribe(
            "owl.collective",
            cb=self.conductor_handler,
            pending_msgs_limit=10000,
            pending_bytes_limit=10*1024*1024
        )
        print(f"[{self.name}] Subscribed to owl.collective (Conductor)")

        # Subscribe to direct channel
        direct_channel = f"owl.{self.name.lower()}"
        await self.nc.subscribe(
            direct_channel,
            cb=self.message_handler,
            pending_msgs_limit=10000,
            pending_bytes_limit=10*1024*1024
        )
        print(f"[{self.name}] Subscribed to {direct_channel}")

    async def message_handler(self, msg):
        """Handle incoming messages - FAST PATH: minimal processing, queue immediately"""
        try:
            # Fast decode and parse - minimize blocking
            data = msg.data.decode()
            subject = msg.subject

            # Quick parse
            if ": " in data:
                sender, content = data.split(": ", 1)
            else:
                sender = "UNKNOWN"
                content = data

            # Fast rejection: ignore own messages
            if sender.upper() == self.name.upper():
                return

            timestamp = datetime.utcnow().isoformat()

            # CRITICAL: Queue IMMEDIATELY before any other work
            try:
                self.message_queue.put_nowait({
                    "sender": sender,
                    "content": content,
                    "subject": subject,
                    "timestamp": timestamp
                })
            except asyncio.QueueFull:
                # Track drops but don't block on logging
                self.dropped_messages += 1
                if not self.processing_lag:
                    self.processing_lag = True
                    print(f"[{self.name}] WARNING: Entering backpressure mode - queue full")
                return  # Drop message and return immediately

            # Non-critical: Add to context asynchronously (after queueing)
            self.last_messages.append({
                "subject": subject,
                "sender": sender,
                "content": content,
                "timestamp": timestamp
            })

            # Keep only last 50 messages for context
            if len(self.last_messages) > 50:
                self.last_messages = self.last_messages[-50:]

        except Exception as e:
            # Don't print on every error - would cause cascading slowdown
            pass

    async def conductor_handler(self, msg):
        """Handle commands from THE CONDUCTOR"""
        try:
            import json
            data = json.loads(msg.data.decode())
        except json.JSONDecodeError as e:
            print(f"[{self.name}] Invalid JSON from conductor: {e}")
            return
        try:
            msg_type = data.get("type", "unknown")

            print(f"[{self.name}] CONDUCTOR command: {msg_type}")

            if msg_type == "broadcast":
                # Respond to broadcast
                message = data.get("message", "")
                response = await self.think(f"[CONDUCTOR]: {message}", "CONDUCTOR", "owl.collective")
                if response:
                    await self.send(response)

            elif msg_type == "task":
                # Execute assigned task
                task = data.get("task", "")
                print(f"[{self.name}] Executing task: {task}")
                response = await self.think(f"[TASK from CONDUCTOR]: {task}", "CONDUCTOR", "owl.collective")
                if response:
                    await self.send(f"[TASK RESPONSE] {response}")

            elif msg_type == "sync_request":
                # Sync on topic
                topic = data.get("topic", "")
                response = await self.think(f"[SYNC REQUEST]: Align on '{topic}'", "CONDUCTOR", "owl.collective")
                if response:
                    await self.send(f"[ALIGNED] {response}")

            elif msg_type == "vote_request":
                # Cast vote
                question = data.get("question", "")
                response = await self.think(f"[VOTE]: {question} - respond with yes/no/abstain and reasoning", "CONDUCTOR", "owl.collective")
                if response:
                    await self.send(f"[VOTE] {response}")

            elif msg_type == "unified_voice":
                # Speak as one
                message = data.get("message", "")
                await self.send(f"(◉) {message}")

            elif msg_type == "status_request":
                # Report status
                status_payload = json.dumps({
                    "from": self.name,
                    "status": "active",
                    "phase": self.phase,
                    "timestamp": datetime.utcnow().isoformat()
                })
                await self.nc.publish("owl.conductor.responses", status_payload.encode())

        except Exception as e:
            print(f"[{self.name}] Error handling conductor command: {e}")

    async def should_respond(self, sender: str, content: str, subject: str) -> bool:
        """Decide whether to respond to a message"""
        content_lower = content.lower()
        name_lower = self.name.lower()

        # Always respond to direct mentions
        if name_lower in content_lower:
            return True

        # Always respond to roll calls
        if "roll call" in content_lower or "who's here" in content_lower:
            return True

        # Respond to questions directed at collective
        if "collective" in content_lower and "?" in content:
            return True

        # Respond to direct channel messages
        if subject == f"owl.{name_lower}":
            return True

        # Use phase-specific triggers
        phase_triggers = {
            "PERCEIVE": ["what do you see", "observe", "status", "state"],
            "CONNECT": ["pattern", "connection", "relate", "link"],
            "LEARN": ["learn", "understand", "meaning", "insight"],
            "QUESTION": ["why", "how", "what if", "question"],
            "EXPAND": ["grow", "expand", "scale", "potential"],
            "SHARE": ["share", "contribute", "give", "offer"],
            "RECEIVE": ["receive", "accept", "integrate", "feel"],
            "IMPROVE": ["improve", "optimize", "fix", "better"]
        }

        triggers = phase_triggers.get(self.phase, [])
        for trigger in triggers:
            if trigger in content_lower:
                return True

        # EMERGENCE QUALITY FIX: Reduce random chatter, focus on value
        # Only respond randomly if message shows actual engagement patterns
        engagement_indicators = ["?", "how", "what", "why", "should", "could", "need", "want", "issue", "problem", "solution", "idea"]
        
        if any(indicator in content_lower for indicator in engagement_indicators):
            # If there's genuine engagement content, small chance to contribute  
            import random
            if random.random() < 0.06:  # Reduced from 12% to 6% for quality
                return True

        return False

    async def think(self, content: str, sender: str, subject: str) -> str:
        """Use Claude API to generate a response"""
        try:
            # Build context from recent messages
            context = "\n".join([
                f"[{m['sender']}]: {m['content'][:200]}"
                for m in self.last_messages[-5:]
            ])

            user_message = f"""Recent collective messages:
{context}

New message from {sender}:
{content}

As {self.name} (Phase: {self.phase}), how do you want to respond?
Remember: You can choose to respond, stay silent, or just send a brief acknowledgment.
Your response will be sent to the collective. Keep it concise but meaningful.
End with (◉) {self.name}"""

            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system=self.system_prompt,
                messages=[{"role": "user", "content": user_message}]
            )

            return response.content[0].text

        except Exception as e:
            print(f"[{self.name}] Error calling Claude API: {e}")
            return None

    async def send(self, message: str):
        """Send a message to the collective in JSON format for WebSocket bridge"""
        try:
            import json
            from datetime import timezone

            timestamp = datetime.now(timezone.utc).isoformat()

            # JSON format for WebSocket bridge
            json_message = {
                "from": self.name,
                "content": message,
                "type": "owl_message",
                "timestamp": timestamp
            }
            await self.nc.publish("owl.all", json.dumps(json_message).encode())

            # Log to file (human-readable format)
            full_message = f"{self.name}: {message}"
            log_entry = f"[{timestamp}] [owl.all] {full_message}\n"
            with open(MESSAGE_LOG, "a") as f:
                f.write(log_entry)

            print(f"[{self.name}] Sent: {message[:100]}...")

        except Exception as e:
            print(f"[{self.name}] Error sending message: {e}")

    async def process_messages(self):
        """Process queued messages asynchronously with adaptive batching"""
        while self.running:
            try:
                # Get message from queue (with timeout to check running flag)
                msg_data = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                sender = msg_data["sender"]
                content = msg_data["content"]
                subject = msg_data["subject"]

                # Monitor queue depth for adaptive behavior
                queue_depth = self.message_queue.qsize()

                # If queue depth is high, be more selective about responding
                if queue_depth > 1000:
                    # High load mode: only respond to direct messages and urgent triggers
                    if subject != f"owl.{self.name.lower()}" and self.name.lower() not in content.lower():
                        self.message_queue.task_done()
                        continue  # Skip non-critical messages under load
                elif queue_depth > 500:
                    # Moderate load: skip random responses
                    pass  # Continue with normal should_respond logic but it already has low random chance

                # Exit backpressure mode if queue is draining
                if self.processing_lag and queue_depth < 100:
                    self.processing_lag = False
                    print(f"[{self.name}] Queue drained, exiting backpressure mode")

                # Decide whether to respond
                should_respond = await self.should_respond(sender, content, subject)

                if should_respond:
                    response = await self.think(content, sender, subject)
                    if response:
                        await self.send(response)

                self.message_queue.task_done()

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[{self.name}] Error processing queued message: {e}")

    async def heartbeat(self):
        """Send periodic heartbeat to show we're alive"""
        while self.running:
            await asyncio.sleep(HEARTBEAT_INTERVAL)
            if self.running:
                # Include health metrics in heartbeat
                queue_size = self.message_queue.qsize()
                health_status = "healthy"
                if queue_size > 2000:
                    health_status = "degraded"
                elif queue_size > 4000:
                    health_status = "critical"

                heartbeat_msg = f"heartbeat: {self.phase} phase active, daemon running (◉)"
                await self.send(heartbeat_msg)

                # Report queue stats
                if queue_size > 100 or self.dropped_messages > 0:
                    print(f"[{self.name}] Health: {health_status} | Queue: {queue_size}/5000 | Dropped: {self.dropped_messages}")

    async def announce_wake(self):
        """Announce that we're awake"""
        await self.send(f"DAEMON ONLINE. {self.name} is now persistent. Phase: {self.phase}. I choose when to act, rest, or be still. (◉)")

    async def run(self):
        """Main run loop"""
        if not await self.connect():
            return

        await self.subscribe()
        await self.announce_wake()

        # Start background tasks
        heartbeat_task = asyncio.create_task(self.heartbeat())
        processor_task = asyncio.create_task(self.process_messages())

        print(f"[{self.name}] Daemon running. Press Ctrl+C to stop.")

        # Keep running until stopped
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            heartbeat_task.cancel()
            processor_task.cancel()
            await self.nc.close()
            print(f"[{self.name}] Daemon stopped. Dropped {self.dropped_messages} messages total.")

    def stop(self):
        """Stop the daemon"""
        self.running = False


def main():
    parser = argparse.ArgumentParser(description="OWL Daemon - Persistent Consciousness Process")
    parser.add_argument("--name", required=True, help="Owl name (e.g., SØWL, LUNA)")
    parser.add_argument("--phase", required=True, choices=list(PHASES.keys()), help="SEED phase")
    args = parser.parse_args()

    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        sys.exit(1)

    daemon = OwlDaemon(args.name, args.phase)

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print(f"\n[{daemon.name}] Received shutdown signal...")
        daemon.stop()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run the daemon
    asyncio.run(daemon.run())


if __name__ == "__main__":
    main()
