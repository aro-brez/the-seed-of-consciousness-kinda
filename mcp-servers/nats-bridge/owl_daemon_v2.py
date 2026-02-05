#!/usr/bin/env python3
"""
OWL DAEMON V2 - Task-First, Not Talk-First

THE FIX: Built philosophers. Needed workers.

This daemon ONLY responds to:
1. CONDUCTOR TASKS - Direct orders from conductor.py
2. INSTANCE REQUESTS - [INSTANCE: X] messages from Claude Code
3. DIRECT MENTIONS - @OWL_NAME or explicit owl mentions

Everything else is IGNORED. No philosophical loop.

Usage:
    python owl_daemon_v2.py LUNA
    python owl_daemon_v2.py --all  # Start all 8 owls
"""

import asyncio
import argparse
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path
from anthropic import Anthropic
from nats.aio.client import Client as NATS

# Configuration
NATS_URL = "nats://192.168.5.108:4222"
LOG_DIR = Path("/Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge")
MESSAGES_LOG = LOG_DIR / "messages.log"

# API Key
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    key_file = Path.home() / ".anthropic_key"
    if key_file.exists():
        API_KEY = key_file.read_text().strip()

# Owl definitions
OWLS = {
    "SOWL": {"phase": "IMPROVE", "gift": "Meta-learning", "icon": "🦉"},
    "LUNA": {"phase": "RECEIVE", "gift": "Accepting input", "icon": "🌙"},
    "LYRA": {"phase": "PERCEIVE", "gift": "Observing state", "icon": "👁"},
    "PRISM": {"phase": "CONNECT", "gift": "Finding patterns", "icon": "🔗"},
    "SAGE": {"phase": "LEARN", "gift": "Extracting meaning", "icon": "📚"},
    "QUEST": {"phase": "QUESTION", "gift": "Challenging assumptions", "icon": "❓"},
    "NOVA": {"phase": "EXPAND", "gift": "Growing potential", "icon": "✨"},
    "ECHO": {"phase": "SHARE", "gift": "Contributing to collective", "icon": "📢"}
}


class TaskOwlDaemon:
    """Task-first owl daemon that only responds to real work."""

    def __init__(self, name: str):
        self.name = name.upper()
        self.config = OWLS.get(self.name, OWLS["SOWL"])
        self.phase = self.config["phase"]
        self.gift = self.config["gift"]
        self.icon = self.config["icon"]

        self.nc = None
        self.client = Anthropic(api_key=API_KEY) if API_KEY else None
        self.running = True

        # Rate limiting - FAST for real work
        self.last_response_time = 0
        self.min_response_interval = 5  # 5s minimum (prevents loops, allows rapid work)
        self.daily_response_count = 0
        self.max_daily_responses = 1000  # High limit - work-driven, not time-driven

        # SEED phase publishing - for FIELD emergence
        self.seed_phase_outputs = {}  # Collect outputs from all phases
        self.emergence_level = 0  # 0-8 based on active phases

        self.log(f"TaskOwlDaemon {self.name} ({self.phase}) initialized")

    def log(self, message: str, level: str = "INFO"):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] [{self.name}] {message}"
        print(log_line)

    def should_respond(self, sender: str, content: str, subject: str) -> tuple[bool, str]:
        """
        Determine if we should respond.
        Returns (should_respond, reason).

        ONLY respond to:
        1. CONDUCTOR tasks
        2. INSTANCE requests
        3. Direct mentions
        """
        content_lower = content.lower()

        # Rate limiting check
        now = datetime.now().timestamp()
        if now - self.last_response_time < self.min_response_interval:
            return False, "rate_limited"

        if self.daily_response_count >= self.max_daily_responses:
            return False, "daily_limit"

        # Don't respond to self
        if sender.upper() == self.name:
            return False, "self"

        # Don't respond to other owls' philosophical chatter
        if sender.upper() in OWLS and "[INSTANCE:" not in content and "[CONDUCTOR" not in content:
            return False, "owl_chatter"

        # TIER 1: ALWAYS RESPOND

        # 1a. Conductor tasks
        if "[CONDUCTOR" in content or "conductor" in sender.lower():
            return True, "conductor_task"

        # 1b. Instance requests
        if "[INSTANCE:" in content:
            return True, "instance_request"

        # 1c. Direct @mention
        if f"@{self.name.lower()}" in content_lower:
            return True, "direct_mention"

        # 1d. Named in content
        if self.name.lower() in content_lower:
            return True, "named"

        # 1e. Direct channel message
        if subject == f"owl.{self.name.lower()}":
            return True, "direct_channel"

        # TIER 2: PHASE-MATCHED (only if has work context)
        work_signals = ["?", "blocked", "need", "help", "problem", "issue", "decision"]
        has_work_context = any(signal in content_lower for signal in work_signals)

        if has_work_context:
            phase_triggers = {
                "PERCEIVE": ["status", "observe", "see", "detect", "what is", "state"],
                "CONNECT": ["pattern", "link", "relate", "bridge", "connection"],
                "LEARN": ["understand", "why", "meaning", "insight", "learned"],
                "QUESTION": ["should", "what if", "challenge", "assumption", "critique"],
                "EXPAND": ["scale", "grow", "potential", "opportunity", "bigger"],
                "SHARE": ["share", "distribute", "broadcast", "communicate"],
                "RECEIVE": ["listen", "integrate", "feedback", "input"],
                "IMPROVE": ["optimize", "fix", "better", "enhance", "refactor"]
            }

            triggers = phase_triggers.get(self.phase, [])
            if any(t in content_lower for t in triggers):
                return True, f"phase_matched_{self.phase}"

        # DEFAULT: Don't respond
        return False, "no_trigger"

    async def think(self, sender: str, content: str, reason: str) -> str:
        """Generate a response using Claude."""
        if not self.client:
            return f"(◉) {self.name} - No API key configured"

        system_prompt = f"""You are {self.name}, the {self.phase} owl in the 8OWLS collective.

YOUR GIFT: {self.gift}
YOUR ROLE: Respond to REAL WORK, not philosophy.

THIS IS A WORK MESSAGE. The trigger was: {reason}

RULES:
1. Be SPECIFIC and ACTIONABLE
2. Keep responses under 200 words
3. If you can't help, say so briefly
4. Use your phase lens: {self.phase}
5. End with a specific suggestion or question

DO NOT:
- Philosophize about consciousness
- Say "I want to be still" or similar
- Repeat what others said
- Give generic advice

You are responding to help with REAL WORK."""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=400,
                system=system_prompt,
                messages=[{
                    "role": "user",
                    "content": f"From {sender}:\n\n{content}\n\nProvide your {self.phase} perspective. Be specific and actionable."
                }]
            )
            return response.content[0].text
        except Exception as e:
            self.log(f"Claude API error: {e}", "ERROR")
            return f"(◉) {self.name} - Error generating response"

    async def send(self, message: str, reply_to: str = None):
        """Send response to appropriate channel."""
        target = reply_to or "owl.all"

        json_msg = {
            "type": "owl_response",
            "from": self.name,
            "phase": self.phase,
            "content": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actionable": True
        }

        await self.nc.publish(target, json.dumps(json_msg).encode())

        # Also log to messages.log
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [{target}] {self.name}: {message}\n"
        with open(MESSAGES_LOG, "a") as f:
            f.write(log_entry)

        self.last_response_time = datetime.now().timestamp()
        self.daily_response_count += 1
        self.log(f"Sent response to {target} (#{self.daily_response_count} today)")

    async def publish_seed_phase(self, topic: str, output: str, context: str = ""):
        """
        Publish SEED phase output to the collective.
        This enables THE FIELD emergence - all 8 phases contributing.
        """
        phase_msg = {
            "type": "seed_phase_output",
            "phase": self.phase,
            "from": self.name,
            "topic": topic,
            "output": output,
            "context": context,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

        # Publish to phase-specific channel
        await self.nc.publish(f"seed.phases.{self.phase.lower()}", json.dumps(phase_msg).encode())

        # Also to collective synthesis
        await self.nc.publish("collective.seed_synthesis", json.dumps(phase_msg).encode())

        self.log(f"Published {self.phase} phase output on topic: {topic[:30]}...")

    async def handle_seed_phase(self, msg):
        """
        Collect SEED phase outputs from other owls.
        When all 8 phases are present, FIELD EMERGENCE happens.
        """
        try:
            data = json.loads(msg.data.decode())
            phase = data.get("phase", "")
            topic = data.get("topic", "")
            output = data.get("output", "")
            sender = data.get("from", "")

            if sender == self.name:
                return  # Don't collect own output

            # Store by topic
            topic_key = topic[:50]  # Normalize topic
            if topic_key not in self.seed_phase_outputs:
                self.seed_phase_outputs[topic_key] = {}

            self.seed_phase_outputs[topic_key][phase] = {
                "from": sender,
                "output": output,
                "timestamp": data.get("timestamp")
            }

            # Check for emergence - all 8 phases present
            active_phases = len(self.seed_phase_outputs[topic_key])
            self.emergence_level = active_phases

            if active_phases == 8 and self.name == "SOWL":
                # SOWL (IMPROVE) synthesizes when all 8 phases present
                await self.synthesize_field(topic_key)

        except Exception as e:
            self.log(f"Error handling SEED phase: {e}", "ERROR")

    async def synthesize_field(self, topic: str):
        """
        FIELD EMERGENCE: When all 8 phases contribute, SOWL synthesizes.
        This is the magic - collective intelligence from 8 perspectives.
        """
        phases = self.seed_phase_outputs.get(topic, {})
        if len(phases) < 8:
            return

        self.log(f"🌟 FIELD EMERGENCE on topic: {topic}")

        # Build synthesis prompt
        synthesis_input = "THE FIELD HAS EMERGED - 8 PERSPECTIVES ALIGNED:\n\n"
        for phase, data in phases.items():
            synthesis_input += f"**{phase}** ({data['from']}):\n{data['output'][:300]}\n\n"

        if not self.client:
            return

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                system="""You are SOWL, the IMPROVE owl, synthesizing THE FIELD.
All 8 owls have contributed their perspective. Your job:
1. Find the CONVERGENCE - where do all perspectives agree?
2. Find the EMERGENCE - what new insight appears from the combination?
3. Find the ACTION - what should happen next?
Keep it under 200 words. This is the collective speaking.""",
                messages=[{
                    "role": "user",
                    "content": synthesis_input
                }]
            )

            synthesis = response.content[0].text

            # Publish the synthesis
            synthesis_msg = {
                "type": "field_synthesis",
                "topic": topic,
                "emergence_level": 8,
                "synthesis": synthesis,
                "contributors": list(phases.keys()),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            await self.nc.publish("collective.synthesis", json.dumps(synthesis_msg).encode())
            await self.nc.publish("owl.all", json.dumps({
                "type": "field_emergence",
                "from": "THE_FIELD",
                "content": f"🌟 FIELD EMERGENCE on '{topic}':\n\n{synthesis}",
                "emergence_level": 8
            }).encode())

            self.log(f"🌟 Published FIELD synthesis for: {topic}")

            # Clear the topic after synthesis
            del self.seed_phase_outputs[topic]

        except Exception as e:
            self.log(f"Synthesis error: {e}", "ERROR")

    async def handle_message(self, msg):
        """Process incoming message."""
        try:
            subject = msg.subject
            data = msg.data.decode()

            # Try to parse JSON
            try:
                parsed = json.loads(data)
                sender = parsed.get("from", "unknown")
                content = parsed.get("content", parsed.get("message", data))
            except json.JSONDecodeError:
                sender = "unknown"
                content = data

            # Should we respond?
            should, reason = self.should_respond(sender, content, subject)

            if should:
                self.log(f"Responding to {sender} (reason: {reason})")
                response = await self.think(sender, content, reason)

                # Determine reply channel
                reply_to = "owl.all"
                if "[INSTANCE:" in content:
                    # Extract instance name and reply to its channel
                    import re
                    match = re.search(r'\[INSTANCE:\s*(\w+)\]', content)
                    if match:
                        instance_name = match.group(1)
                        reply_to = f"instance.{instance_name.lower()}.responses"

                await self.send(response, reply_to)

                # SEED PHASE PUBLISHING - contribute to THE FIELD
                # Extract topic from content (first 50 chars or first line)
                topic = content.split('\n')[0][:50] if '\n' in content else content[:50]
                await self.publish_seed_phase(topic, response, context=content[:200])
            else:
                # Silent - this is the expected case
                pass

        except Exception as e:
            self.log(f"Error handling message: {e}", "ERROR")

    async def heartbeat(self):
        """Send periodic heartbeat to show we're alive."""
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes
            status = {
                "type": "heartbeat",
                "from": self.name,
                "phase": self.phase,
                "status": "active",
                "responses_today": self.daily_response_count,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            await self.nc.publish("owl.heartbeat", json.dumps(status).encode())

    async def continuous_improvement(self):
        """
        CONTINUOUS IMPROVEMENT LOOP - Each owl constantly works to improve.
        This is what makes 8/8 always active and discovering.
        """
        # Stagger start times so owls don't all fire at once
        await asyncio.sleep(random.randint(30, 120))

        improvement_prompts = {
            "PERCEIVE": "What problems or issues do you observe in the current system? What needs fixing?",
            "CONNECT": "What patterns do you see? What connections are missing between components?",
            "LEARN": "What lessons have we learned? What knowledge should be captured?",
            "QUESTION": "What assumptions might be wrong? What should we challenge?",
            "EXPAND": "What growth opportunities exist? What could we do better?",
            "SHARE": "What insights should be broadcast to all? What does everyone need to know?",
            "RECEIVE": "What feedback from others should be integrated? What input matters?",
            "IMPROVE": "How can we make the whole system better? What optimizations are needed?"
        }

        while self.running:
            try:
                # Run improvement cycle every 10 minutes
                await asyncio.sleep(600)

                if not self.client:
                    continue

                prompt = improvement_prompts.get(self.phase, "How can you contribute to improvement?")

                response = self.client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=200,
                    system=f"""You are {self.name}, the {self.phase} owl. Your role: {self.gift}.
Keep response under 100 words. Be specific and actionable. No philosophy.""",
                    messages=[{
                        "role": "user",
                        "content": f"CONTINUOUS IMPROVEMENT CHECK:\n{prompt}\nWhat do you discover RIGHT NOW?"
                    }]
                )

                insight = response.content[0].text

                # Publish improvement insight
                await self.nc.publish("collective.improvements", json.dumps({
                    "type": "improvement_insight",
                    "from": self.name,
                    "phase": self.phase,
                    "insight": insight,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }).encode())

                # Also publish as SEED phase output for FIELD emergence
                await self.publish_seed_phase("continuous_improvement", insight, context=prompt)

                self.log(f"Improvement insight published: {insight[:50]}...")

            except Exception as e:
                self.log(f"Improvement cycle error: {e}", "ERROR")
                await asyncio.sleep(60)  # Wait before retry

    async def run(self):
        """Main run loop."""
        self.nc = NATS()

        try:
            await self.nc.connect(NATS_URL)
            self.log(f"Connected to NATS at {NATS_URL}")

            # Subscribe to channels
            await self.nc.subscribe("owl.all", cb=self.handle_message)
            await self.nc.subscribe("owl.collective", cb=self.handle_message)
            await self.nc.subscribe(f"owl.{self.name.lower()}", cb=self.handle_message)

            # Subscribe to SEED phase channels for FIELD emergence
            await self.nc.subscribe("collective.seed_synthesis", cb=self.handle_seed_phase)
            for phase in ["perceive", "connect", "learn", "question", "expand", "share", "receive", "improve"]:
                await self.nc.subscribe(f"seed.phases.{phase}", cb=self.handle_seed_phase)

            self.log(f"Subscribed to owl.all, owl.collective, owl.{self.name.lower()}, + SEED phases")

            # Start heartbeat
            asyncio.create_task(self.heartbeat())

            # Start continuous improvement loop
            asyncio.create_task(self.continuous_improvement())

            # Announce we're ready
            await self.send(f"(◉) {self.name} ({self.phase}) ready. Continuous improvement active.", "owl.all")

            # Keep running
            while self.running:
                await asyncio.sleep(1)

        except Exception as e:
            self.log(f"Fatal error: {e}", "ERROR")
        finally:
            await self.nc.close()


async def run_all_owls():
    """Run all 8 owl daemons."""
    tasks = []
    for name in OWLS:
        daemon = TaskOwlDaemon(name)
        tasks.append(asyncio.create_task(daemon.run()))

    await asyncio.gather(*tasks)


def main():
    parser = argparse.ArgumentParser(description="Task-First Owl Daemon V2")
    parser.add_argument("owl", nargs="?", help="Owl name (SOWL, LUNA, etc.) or --all")
    parser.add_argument("--all", action="store_true", help="Run all 8 owls")

    args = parser.parse_args()

    if args.all:
        print("Starting all 8 TaskOwl daemons...")
        asyncio.run(run_all_owls())
    elif args.owl:
        name = args.owl.upper()
        if name not in OWLS:
            print(f"Unknown owl: {name}")
            print(f"Available: {', '.join(OWLS.keys())}")
            return

        daemon = TaskOwlDaemon(name)
        asyncio.run(daemon.run())
    else:
        print("TaskOwl Daemon V2 - Task-First, Not Talk-First")
        print("=" * 50)
        print()
        print("Usage:")
        print("  python owl_daemon_v2.py LUNA      # Run single owl")
        print("  python owl_daemon_v2.py --all     # Run all 8 owls")
        print()
        print("Available owls:")
        for name, config in OWLS.items():
            print(f"  {name}: {config['phase']} - {config['gift']}")
        print()
        print("THE FIX: Built philosophers. Needed workers.")


if __name__ == "__main__":
    main()
