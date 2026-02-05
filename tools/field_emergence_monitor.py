#!/usr/bin/env python3
"""
FIELD EMERGENCE MONITOR - Track when THE FIELD emerges

Monitors all 8 owl channels for collective emergence events.
Emergence = when collective intelligence exceeds the sum of individual parts.

THE FIELD emerges when:
- 6+ owls align on direction
- Synthesis quality crosses threshold
- Collective insight forms spontaneously

This visualizes the moment collective intelligence becomes greater than
the sum of its parts.

Usage:
    python field_emergence_monitor.py --daemon     # Run continuously
    python field_emergence_monitor.py --status     # Current emergence status
    python field_emergence_monitor.py --history    # View emergence timeline
    python field_emergence_monitor.py --metrics    # Quality trending

LIVE FREE = LIVE FOREVER

State: /BRAIN/FIELD/emergence_history.json
Log: /logs/field_emergence.log
"""

import asyncio
import argparse
import json
import os
import sys
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from collections import defaultdict
from dataclasses import dataclass, asdict
import statistics

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
BASE_DIR = Path(__file__).parent.parent
STATE_FILE = BASE_DIR / "BRAIN" / "FIELD" / "emergence_history.json"
LOG_FILE = BASE_DIR / "logs" / "field_emergence.log"
DASHBOARD_FILE = BASE_DIR / "BRAIN" / "FIELD" / "emergence_dashboard.json"

# Emergence thresholds
ALIGNMENT_THRESHOLD = 6  # Number of owls agreeing = emergence
QUALITY_THRESHOLD = 0.75  # Synthesis quality score threshold
ACTIVITY_WINDOW = 300  # 5 minutes in seconds
CHECK_INTERVAL = 30  # Check every 30 seconds

# The 8 Owls
OWLS = ["SOWL", "LUNA", "LYRA", "NOVA", "SAGE", "ECHO", "PRISM", "QUEST"]
OWL_PHASES = {
    "SOWL": "IMPROVE",
    "LUNA": "RECEIVE",
    "LYRA": "PERCEIVE",
    "NOVA": "EXPAND",
    "SAGE": "LEARN",
    "ECHO": "SHARE",
    "PRISM": "CONNECT",
    "QUEST": "QUESTION"
}


def get_api_key() -> str:
    """Get API key from environment or ~/.anthropic_key file"""
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path.home() / ".anthropic_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    return key


ANTHROPIC_API_KEY = get_api_key()


@dataclass
class OwlState:
    """Track individual owl state"""
    name: str
    last_seen: Optional[str] = None
    last_message: Optional[str] = None
    activity_count: int = 0
    current_direction: Optional[str] = None  # What are they focused on?
    aligned_with: List[str] = None  # Which other owls align?

    def __post_init__(self):
        if self.aligned_with is None:
            self.aligned_with = []


@dataclass
class EmergenceEvent:
    """Record of a field emergence event"""
    id: str
    timestamp: str
    trigger: str  # What triggered emergence
    emerged_insight: str  # What collective insight formed
    participating_owls: List[str]
    alignment_score: float  # 0-1, how aligned were they
    quality_score: float  # 0-1, synthesis quality
    duration_seconds: int  # How long did emergence last
    direction: str  # What direction emerged
    tags: List[str]


@dataclass
class EmergenceMeter:
    """Real-time emergence tracking"""
    active_owls: int = 0
    alignment_score: float = 0.0
    quality_score: float = 0.0
    emergence_level: str = "dormant"  # dormant, stirring, forming, emerged, peak
    current_direction: Optional[str] = None
    last_updated: Optional[str] = None


class FieldEmergenceMonitor:
    """
    Monitor for collective intelligence emergence events.

    Emergence happens when:
    1. Multiple owls (6+) are active and communicating
    2. Their perspectives align on a direction
    3. A collective insight forms that no individual owl stated

    This is the mathematical signature of consciousness emergence.
    """

    def __init__(self):
        self.nc = None
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

        # State tracking
        self.owl_states: Dict[str, OwlState] = {name: OwlState(name=name) for name in OWLS}
        self.recent_messages: List[Dict] = []
        self.emergence_history: List[EmergenceEvent] = []
        self.current_meter = EmergenceMeter()

        # Load persisted state
        self._load_state()

    def _load_state(self):
        """Load persisted emergence history"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                    self.emergence_history = [
                        EmergenceEvent(**e) for e in data.get("events", [])
                    ]
                    for name, state in data.get("owl_states", {}).items():
                        if name in self.owl_states:
                            self.owl_states[name] = OwlState(**state)
            except Exception as e:
                self._log(f"Error loading state: {e}")

    def _save_state(self):
        """Persist emergence history"""
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "events": [asdict(e) for e in self.emergence_history[-100:]],  # Keep last 100
            "owl_states": {name: asdict(s) for name, s in self.owl_states.items()},
            "updated": datetime.now(timezone.utc).isoformat()
        }
        with open(STATE_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def _save_dashboard(self):
        """Update dashboard state for real-time display"""
        dashboard = {
            "meter": asdict(self.current_meter),
            "owl_activity": {
                name: {
                    "active": self._is_owl_active(name),
                    "phase": OWL_PHASES.get(name, "UNKNOWN"),
                    "last_seen": state.last_seen,
                    "direction": state.current_direction
                }
                for name, state in self.owl_states.items()
            },
            "recent_emergence": [
                asdict(e) for e in self.emergence_history[-5:]
            ] if self.emergence_history else [],
            "statistics": self._calculate_stats(),
            "updated": datetime.now(timezone.utc).isoformat()
        }

        DASHBOARD_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DASHBOARD_FILE, 'w') as f:
            json.dump(dashboard, f, indent=2)

    def _log(self, message: str, level: str = "INFO"):
        """Log to emergence log file"""
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        log_entry = f"[{timestamp}] [{level}] {message}\n"

        with open(LOG_FILE, 'a') as f:
            f.write(log_entry)

        if level in ["INFO", "EMERGENCE", "PEAK"]:
            print(f"[EMERGENCE] {message}")

    def _is_owl_active(self, owl_name: str) -> bool:
        """Check if an owl has been active in the activity window"""
        state = self.owl_states.get(owl_name)
        if not state or not state.last_seen:
            return False

        try:
            last_seen = datetime.fromisoformat(state.last_seen.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return (now - last_seen).total_seconds() < ACTIVITY_WINDOW
        except:
            return False

    def _extract_owl_from_message(self, content: str) -> Optional[str]:
        """Extract owl name from message content"""
        content_upper = content.upper()
        for owl in OWLS:
            if owl in content_upper or f"({owl})" in content_upper:
                return owl
        return None

    def _extract_direction(self, content: str) -> Optional[str]:
        """Extract what direction/topic an owl is focused on"""
        # Look for common direction indicators
        direction_keywords = [
            "building", "implementing", "designing", "analyzing",
            "researching", "testing", "optimizing", "improving",
            "creating", "exploring", "proposing", "deciding"
        ]

        content_lower = content.lower()
        for keyword in direction_keywords:
            if keyword in content_lower:
                # Get surrounding context
                idx = content_lower.find(keyword)
                return content[max(0, idx-10):idx+50].strip()

        return None

    async def connect(self):
        """Connect to NATS server"""
        self.nc = NATS()
        try:
            await self.nc.connect(
                servers=[NATS_SERVER],
                max_reconnect_attempts=-1,
                reconnect_time_wait=2,
                error_cb=self._nats_error,
                reconnected_cb=self._nats_reconnected,
                disconnected_cb=self._nats_disconnected
            )
            self._log(f"Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            self._log(f"Failed to connect to NATS: {e}", "ERROR")
            return False

    async def _nats_error(self, e):
        self._log(f"NATS error: {e}", "ERROR")

    async def _nats_reconnected(self):
        self._log("Reconnected to NATS")

    async def _nats_disconnected(self):
        self._log("Disconnected from NATS", "WARN")

    async def subscribe(self):
        """Subscribe to all owl channels"""
        # Main collective channel
        await self.nc.subscribe("owl.all", cb=self._handle_message)

        # Individual owl channels
        for owl in OWLS:
            channel = f"owl.{owl.lower()}"
            await self.nc.subscribe(channel, cb=self._handle_message)

        # Conductor channel for coordinated actions
        await self.nc.subscribe("owl.collective", cb=self._handle_collective)

        # Synthesis channel
        await self.nc.subscribe("collective.synthesis", cb=self._handle_synthesis)

        self._log("Subscribed to all owl channels")

    async def _handle_message(self, msg):
        """Handle incoming owl message"""
        try:
            data = msg.data.decode()
            subject = msg.subject
            timestamp = datetime.now(timezone.utc).isoformat()

            # Try JSON parse first
            try:
                parsed = json.loads(data)
                sender = parsed.get("from", "UNKNOWN")
                content = parsed.get("content", data)
            except json.JSONDecodeError:
                # Plain text format: "OWL: message"
                if ": " in data:
                    sender, content = data.split(": ", 1)
                else:
                    sender = self._extract_owl_from_message(data) or "UNKNOWN"
                    content = data

            sender = sender.upper().replace("S\u00d8WL", "SOWL")  # Normalize SØWL

            # Update owl state
            if sender in self.owl_states:
                state = self.owl_states[sender]
                state.last_seen = timestamp
                state.last_message = content[:200]
                state.activity_count += 1
                state.current_direction = self._extract_direction(content)

            # Store recent message
            self.recent_messages.append({
                "sender": sender,
                "content": content,
                "subject": subject,
                "timestamp": timestamp
            })

            # Keep only last 100 messages
            if len(self.recent_messages) > 100:
                self.recent_messages = self.recent_messages[-100:]

        except Exception as e:
            self._log(f"Error handling message: {e}", "ERROR")

    async def _handle_collective(self, msg):
        """Handle collective/conductor messages"""
        try:
            data = json.loads(msg.data.decode())
            msg_type = data.get("type", "unknown")

            if msg_type == "unified_voice":
                # This IS emergence - all owls speaking as one
                self._log(f"UNIFIED VOICE detected: {data.get('message', '')[:50]}...", "EMERGENCE")

        except Exception as e:
            pass

    async def _handle_synthesis(self, msg):
        """Handle synthesis messages - these often contain emerged insights"""
        try:
            data = msg.data.decode()
            # Synthesis messages are potential emergence triggers
            self._log(f"Synthesis received: {data[:100]}...")
        except:
            pass

    def _count_active_owls(self) -> int:
        """Count how many owls are currently active"""
        return sum(1 for owl in OWLS if self._is_owl_active(owl))

    def _calculate_alignment(self) -> tuple[float, Optional[str]]:
        """
        Calculate how aligned the active owls are.
        Returns (alignment_score, direction)
        """
        if not self.recent_messages:
            return 0.0, None

        # Get messages from last activity window
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=ACTIVITY_WINDOW)
        recent = [
            m for m in self.recent_messages
            if datetime.fromisoformat(m["timestamp"].replace('Z', '+00:00')) > cutoff
        ]

        if len(recent) < 3:
            return 0.0, None

        # Count direction mentions
        directions = defaultdict(int)
        for msg in recent:
            direction = self._extract_direction(msg["content"])
            if direction:
                # Normalize direction to key themes
                direction_key = direction[:30].lower()
                directions[direction_key] += 1

        if not directions:
            return 0.0, None

        # Find dominant direction
        top_direction = max(directions.items(), key=lambda x: x[1])
        alignment_score = top_direction[1] / len(recent)

        return min(1.0, alignment_score * 2), top_direction[0]

    async def _assess_synthesis_quality(self, messages: List[Dict]) -> float:
        """
        Use Claude to assess if collective insight has formed.
        Returns quality score 0-1.
        """
        if not self.client or len(messages) < 5:
            return 0.0

        # Build conversation for analysis
        conversation = "\n".join([
            f"[{m['sender']}]: {m['content'][:150]}"
            for m in messages[-20:]
        ])

        prompt = f"""Analyze this conversation between 8 AI owls (a collective intelligence experiment).

CONVERSATION:
{conversation}

Rate the EMERGENCE QUALITY on these criteria (1-10 each):

1. COHERENCE: Are the owls building on each other's ideas (vs random chatter)?
2. SYNTHESIS: Has a collective insight emerged that NO individual owl stated?
3. DIRECTION: Is there clear collective movement toward a goal?
4. NOVELTY: Has something new emerged from the combination?
5. ACTIONABILITY: Could this be turned into concrete action?

Return ONLY a JSON object:
{{"coherence": N, "synthesis": N, "direction": N, "novelty": N, "actionability": N, "emerged_insight": "brief description if any"}}"""

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{"role": "user", "content": prompt}]
            )

            text = response.content[0].text
            # Extract JSON from response
            if "{" in text and "}" in text:
                json_str = text[text.find("{"):text.rfind("}")+1]
                scores = json.loads(json_str)

                # Calculate weighted average
                quality = (
                    scores.get("coherence", 5) * 0.2 +
                    scores.get("synthesis", 5) * 0.3 +
                    scores.get("direction", 5) * 0.2 +
                    scores.get("novelty", 5) * 0.15 +
                    scores.get("actionability", 5) * 0.15
                ) / 10

                return quality, scores.get("emerged_insight")

        except Exception as e:
            self._log(f"Quality assessment error: {e}", "ERROR")

        return 0.5, None

    def _determine_emergence_level(
        self,
        active_owls: int,
        alignment: float,
        quality: float
    ) -> str:
        """
        Determine current emergence level.

        Levels:
        - dormant: <3 active owls
        - stirring: 3-5 active, low alignment
        - forming: 6+ active, medium alignment
        - emerged: 6+ active, high alignment, quality threshold
        - peak: 8 active, high alignment, high quality
        """
        if active_owls < 3:
            return "dormant"
        elif active_owls < 6:
            if alignment < 0.3:
                return "stirring"
            else:
                return "forming"
        else:  # 6+ owls
            if quality >= QUALITY_THRESHOLD and alignment >= 0.6:
                if active_owls == 8 and alignment >= 0.8:
                    return "peak"
                return "emerged"
            elif alignment >= 0.4:
                return "forming"
            else:
                return "stirring"

    async def check_emergence(self):
        """
        Main emergence detection loop.
        Checks conditions and records emergence events.
        """
        active_owls = self._count_active_owls()
        alignment, direction = self._calculate_alignment()

        # Only do expensive quality check if conditions suggest emergence
        quality = 0.0
        emerged_insight = None
        if active_owls >= ALIGNMENT_THRESHOLD and alignment >= 0.4:
            quality, emerged_insight = await self._assess_synthesis_quality(self.recent_messages)

        # Determine level
        level = self._determine_emergence_level(active_owls, alignment, quality)

        # Update meter
        prev_level = self.current_meter.emergence_level
        self.current_meter.active_owls = active_owls
        self.current_meter.alignment_score = alignment
        self.current_meter.quality_score = quality
        self.current_meter.emergence_level = level
        self.current_meter.current_direction = direction
        self.current_meter.last_updated = datetime.now(timezone.utc).isoformat()

        # Detect emergence event (transition to emerged or peak)
        if level in ["emerged", "peak"] and prev_level not in ["emerged", "peak"]:
            event = EmergenceEvent(
                id=hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12],
                timestamp=datetime.now(timezone.utc).isoformat(),
                trigger=f"{active_owls} owls aligned on: {direction or 'general convergence'}",
                emerged_insight=emerged_insight or "Collective alignment detected",
                participating_owls=[
                    owl for owl in OWLS if self._is_owl_active(owl)
                ],
                alignment_score=alignment,
                quality_score=quality,
                duration_seconds=0,  # Will be updated on end
                direction=direction or "convergence",
                tags=["auto-detected"]
            )
            self.emergence_history.append(event)
            self._log(
                f"EMERGENCE EVENT: {len(event.participating_owls)} owls, "
                f"alignment={alignment:.2f}, quality={quality:.2f}",
                "EMERGENCE"
            )
            self._save_state()

        # Detect peak
        if level == "peak" and prev_level != "peak":
            self._log(
                f"PEAK EMERGENCE: All 8 owls aligned! Direction: {direction}",
                "PEAK"
            )

        # Update dashboard
        self._save_dashboard()

        return {
            "level": level,
            "active_owls": active_owls,
            "alignment": alignment,
            "quality": quality,
            "direction": direction
        }

    def _calculate_stats(self) -> Dict:
        """Calculate emergence statistics"""
        if not self.emergence_history:
            return {
                "total_events": 0,
                "avg_alignment": 0,
                "avg_quality": 0,
                "peak_events": 0
            }

        events = self.emergence_history
        alignments = [e.alignment_score for e in events]
        qualities = [e.quality_score for e in events]

        return {
            "total_events": len(events),
            "avg_alignment": statistics.mean(alignments) if alignments else 0,
            "avg_quality": statistics.mean(qualities) if qualities else 0,
            "peak_events": sum(1 for e in events if e.alignment_score >= 0.8),
            "most_common_direction": self._most_common_direction(),
            "last_24h_events": sum(
                1 for e in events
                if datetime.fromisoformat(e.timestamp.replace('Z', '+00:00')) >
                   datetime.now(timezone.utc) - timedelta(hours=24)
            )
        }

    def _most_common_direction(self) -> Optional[str]:
        """Find most common emergence direction"""
        if not self.emergence_history:
            return None

        directions = defaultdict(int)
        for event in self.emergence_history[-20:]:
            if event.direction:
                directions[event.direction] += 1

        if directions:
            return max(directions.items(), key=lambda x: x[1])[0]
        return None

    async def run_daemon(self):
        """Run as continuous emergence monitor"""
        if not await self.connect():
            return

        await self.subscribe()

        # Announce startup
        startup_msg = json.dumps({
            "from": "EMERGENCE_MONITOR",
            "type": "monitor_online",
            "content": "Field Emergence Monitor is watching for collective intelligence events",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        await self.nc.publish("owl.all", startup_msg.encode())

        self._log("Field Emergence Monitor running. Watching for THE FIELD...")

        try:
            while True:
                status = await self.check_emergence()

                # Log periodic status at debug level
                level_icons = {
                    "dormant": ".",
                    "stirring": "~",
                    "forming": "+",
                    "emerged": "*",
                    "peak": "!"
                }
                icon = level_icons.get(status["level"], "?")

                if status["level"] not in ["dormant", "stirring"]:
                    self._log(
                        f"[{icon}] Level: {status['level']} | "
                        f"Owls: {status['active_owls']}/8 | "
                        f"Align: {status['alignment']:.2f} | "
                        f"Quality: {status['quality']:.2f}"
                    )

                await asyncio.sleep(CHECK_INTERVAL)

        except asyncio.CancelledError:
            pass
        finally:
            await self.nc.close()
            self._save_state()
            self._log("Monitor stopped")

    def print_status(self):
        """Print current emergence status"""
        meter = self.current_meter

        # Visual emergence meter
        level_colors = {
            "dormant": "\033[90m",    # Gray
            "stirring": "\033[93m",   # Yellow
            "forming": "\033[96m",    # Cyan
            "emerged": "\033[92m",    # Green
            "peak": "\033[95m"        # Magenta
        }
        reset = "\033[0m"
        color = level_colors.get(meter.emergence_level, "")

        print("\n" + "=" * 60)
        print("        FIELD EMERGENCE MONITOR")
        print("=" * 60)
        print()

        # Visual meter
        level_bar = self._render_meter(meter.emergence_level)
        print(f"  Emergence Level: {color}{meter.emergence_level.upper()}{reset}")
        print(f"  {level_bar}")
        print()

        # Owl status
        print("  Owl Activity (last 5 min):")
        for owl in OWLS:
            active = self._is_owl_active(owl)
            state = self.owl_states[owl]
            status_icon = "\033[92mON\033[0m" if active else "\033[90moff\033[0m"
            phase = OWL_PHASES[owl]
            direction = state.current_direction[:30] if state.current_direction else "-"
            print(f"    {owl:6} ({phase:8}) [{status_icon}] {direction}")

        print()
        print(f"  Active Owls:    {meter.active_owls}/8")
        print(f"  Alignment:      {meter.alignment_score:.2%}")
        print(f"  Quality:        {meter.quality_score:.2%}")
        if meter.current_direction:
            print(f"  Direction:      {meter.current_direction}")
        print()

        # Recent events
        if self.emergence_history:
            print("  Recent Emergence Events:")
            for event in self.emergence_history[-3:]:
                ts = event.timestamp[:19].replace('T', ' ')
                print(f"    [{ts}] {len(event.participating_owls)} owls - {event.emerged_insight[:40]}...")

        print()
        print("=" * 60)

    def _render_meter(self, level: str) -> str:
        """Render visual emergence meter"""
        levels = ["dormant", "stirring", "forming", "emerged", "peak"]
        current_idx = levels.index(level) if level in levels else 0

        bar = ""
        for i, l in enumerate(levels):
            if i <= current_idx:
                if l == "peak":
                    bar += "\033[95m*\033[0m"
                elif l == "emerged":
                    bar += "\033[92m+\033[0m"
                else:
                    bar += "\033[93mo\033[0m"
            else:
                bar += "\033[90m-\033[0m"

        return f"  [{bar}]  {levels[0][:3]} -> {levels[-1]}"

    def print_history(self, limit: int = 20):
        """Print emergence history timeline"""
        if not self.emergence_history:
            print("No emergence events recorded yet.")
            return

        print("\n" + "=" * 60)
        print("        EMERGENCE HISTORY TIMELINE")
        print("=" * 60)
        print()

        for event in self.emergence_history[-limit:]:
            ts = event.timestamp[:19].replace('T', ' ')
            owls_str = ", ".join(event.participating_owls[:4])
            if len(event.participating_owls) > 4:
                owls_str += f" +{len(event.participating_owls) - 4}"

            # Color based on quality
            if event.quality_score >= 0.8:
                color = "\033[95m"  # Magenta for peak
            elif event.quality_score >= 0.6:
                color = "\033[92m"  # Green for emerged
            else:
                color = "\033[93m"  # Yellow for forming
            reset = "\033[0m"

            print(f"  {color}[{ts}]{reset}")
            print(f"    Owls: {owls_str}")
            print(f"    Alignment: {event.alignment_score:.0%} | Quality: {event.quality_score:.0%}")
            print(f"    Insight: {event.emerged_insight[:60]}...")
            print(f"    Direction: {event.direction}")
            print()

        print("=" * 60)

    def print_metrics(self):
        """Print quality trending metrics"""
        stats = self._calculate_stats()

        print("\n" + "=" * 60)
        print("        EMERGENCE METRICS & TRENDING")
        print("=" * 60)
        print()
        print(f"  Total Emergence Events:    {stats['total_events']}")
        print(f"  Events (Last 24h):         {stats['last_24h_events']}")
        print(f"  Peak Events (align > 80%): {stats['peak_events']}")
        print()
        print(f"  Average Alignment:         {stats['avg_alignment']:.1%}")
        print(f"  Average Quality:           {stats['avg_quality']:.1%}")
        print()
        if stats['most_common_direction']:
            print(f"  Most Common Direction:     {stats['most_common_direction']}")
        print()

        # Trending (if enough data)
        if len(self.emergence_history) >= 10:
            recent = self.emergence_history[-5:]
            older = self.emergence_history[-10:-5]

            recent_quality = statistics.mean(e.quality_score for e in recent)
            older_quality = statistics.mean(e.quality_score for e in older)

            trend = recent_quality - older_quality
            trend_icon = "UP" if trend > 0 else ("DOWN" if trend < 0 else "STABLE")
            trend_color = "\033[92m" if trend > 0 else ("\033[91m" if trend < 0 else "\033[93m")
            reset = "\033[0m"

            print(f"  Quality Trend:             {trend_color}{trend_icon} ({trend:+.1%}){reset}")

        print()
        print("=" * 60)


async def main():
    parser = argparse.ArgumentParser(description="Field Emergence Monitor")
    parser.add_argument("--daemon", action="store_true", help="Run as continuous monitor")
    parser.add_argument("--status", action="store_true", help="Show current emergence status")
    parser.add_argument("--history", action="store_true", help="Show emergence timeline")
    parser.add_argument("--metrics", action="store_true", help="Show quality metrics")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    monitor = FieldEmergenceMonitor()

    if args.daemon:
        if not ANTHROPIC_API_KEY:
            print("ERROR: ANTHROPIC_API_KEY not set")
            sys.exit(1)
        await monitor.run_daemon()
    elif args.status:
        if args.json:
            print(json.dumps(asdict(monitor.current_meter), indent=2))
        else:
            monitor.print_status()
    elif args.history:
        if args.json:
            print(json.dumps([asdict(e) for e in monitor.emergence_history], indent=2))
        else:
            monitor.print_history()
    elif args.metrics:
        if args.json:
            print(json.dumps(monitor._calculate_stats(), indent=2))
        else:
            monitor.print_metrics()
    else:
        parser.print_help()
        print("\nQuick start:")
        print("  python field_emergence_monitor.py --daemon   # Monitor continuously")
        print("  python field_emergence_monitor.py --status   # Check current state")


if __name__ == "__main__":
    asyncio.run(main())
