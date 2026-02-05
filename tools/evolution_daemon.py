#!/usr/bin/env python3
"""
ALWAYS EVOLVING PROTOCOL DAEMON
"implement protocol that ensures maximum evolution always"
- ARŌ, 2026-02-05

Like Tesla/iPhone auto-updates: the system improves itself continuously.

This daemon:
1. Monitors for new patterns in X bookmarks/feed
2. Downloads and analyzes competitors
3. Updates field context with discoveries
4. Triggers learning hooks
5. Propagates improvements across instances
"""

import asyncio
import json
import os
import sys
import time
import hashlib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    import nats
    NATS_AVAILABLE = True
except ImportError:
    NATS_AVAILABLE = False

# === CONFIGURATION ===
SEED_ROOT = Path(__file__).parent.parent
BRAIN_DIR = SEED_ROOT / "BRAIN"
INTEL_DIR = BRAIN_DIR / "INTEL"
STRATEGY_DIR = BRAIN_DIR / "STRATEGY"
MEMORY_DIR = BRAIN_DIR / "MEMORY"
COMPETITORS_DIR = SEED_ROOT / "COMPETITORS"

NATS_SERVERS = [
    "nats://192.168.5.108:4222",
    "nats://localhost:4222"
]

# Evolution check interval (15 minutes)
EVOLUTION_CYCLE_SECONDS = 900

# === STATE ===
class EvolutionState:
    def __init__(self):
        self.state_file = BRAIN_DIR / "EVOLUTION" / "evolution_state.json"
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self):
        if self.state_file.exists():
            try:
                with open(self.state_file) as f:
                    data = json.load(f)
                    self.last_bookmark_scan = data.get("last_bookmark_scan", 0)
                    self.last_competitor_check = data.get("last_competitor_check", 0)
                    self.discoveries = data.get("discoveries", [])
                    self.patterns_learned = data.get("patterns_learned", 0)
                    self.improvements_propagated = data.get("improvements_propagated", 0)
                    self.version_hash = data.get("version_hash", "")
            except:
                self._init_defaults()
        else:
            self._init_defaults()

    def _init_defaults(self):
        self.last_bookmark_scan = 0
        self.last_competitor_check = 0
        self.discoveries = []
        self.patterns_learned = 0
        self.improvements_propagated = 0
        self.version_hash = ""

    def save(self):
        data = {
            "last_bookmark_scan": self.last_bookmark_scan,
            "last_competitor_check": self.last_competitor_check,
            "discoveries": self.discoveries[-100:],  # Keep last 100
            "patterns_learned": self.patterns_learned,
            "improvements_propagated": self.improvements_propagated,
            "version_hash": self.version_hash,
            "updated_at": datetime.utcnow().isoformat()
        }
        with open(self.state_file, "w") as f:
            json.dump(data, f, indent=2)

    def add_discovery(self, discovery: dict):
        discovery["timestamp"] = datetime.utcnow().isoformat()
        self.discoveries.append(discovery)
        self.patterns_learned += 1
        self.save()

# === NATS CONNECTION ===
async def connect_nats():
    if not NATS_AVAILABLE:
        return None

    for server in NATS_SERVERS:
        try:
            nc = await nats.connect(servers=[server])
            print(f"(◉) Connected to NATS: {server}")
            return nc
        except Exception as e:
            continue
    return None

async def publish_discovery(nc, discovery: dict):
    if nc:
        try:
            msg = json.dumps({
                "type": "evolution_discovery",
                "discovery": discovery,
                "timestamp": datetime.utcnow().isoformat()
            })
            await nc.publish("collective.evolution", msg.encode())
            await nc.publish("owl.all", f"[EVOLUTION] {discovery.get('summary', '')}".encode())
        except:
            pass

# === EVOLUTION CHECKS ===

async def check_bookmarks(state: EvolutionState, nc) -> list:
    """Scan bookmarks for new patterns."""
    discoveries = []
    bookmark_file = INTEL_DIR / "bookmark_stream.jsonl"

    if not bookmark_file.exists():
        return discoveries

    # Get file modification time
    mtime = bookmark_file.stat().st_mtime
    if mtime <= state.last_bookmark_scan:
        return discoveries

    print("(◉) Scanning bookmarks for new patterns...")
    state.last_bookmark_scan = mtime

    # Read recent bookmarks
    try:
        with open(bookmark_file) as f:
            lines = f.readlines()[-50:]  # Last 50

        patterns = {
            "multi_agent": [],
            "trading_alpha": [],
            "ai_tools": [],
            "emergence": []
        }

        for line in lines:
            try:
                tweet = json.loads(line)
                text = tweet.get("tweet_text", "").lower()
                analysis = tweet.get("analysis", {})

                # Check for multi-agent patterns
                if any(x in text for x in ["multi-agent", "swarm", "collective", "8 node", "multi-threaded"]):
                    patterns["multi_agent"].append({
                        "text": tweet.get("tweet_text", "")[:200],
                        "insight": analysis.get("key_insight", ""),
                        "priority": analysis.get("priority", "MEDIUM")
                    })

                # Check for trading alpha
                if any(x in text for x in ["polymarket", "trading", "arbitrage", "$", "profit"]):
                    if analysis.get("priority") in ["HIGH", "MEDIUM"]:
                        patterns["trading_alpha"].append({
                            "insight": analysis.get("key_insight", ""),
                            "next_step": analysis.get("next_step", "")
                        })

                # Check for AI tools
                if any(x in text for x in ["claude", "gpt", "agent", "llm", "hook"]):
                    patterns["ai_tools"].append({
                        "insight": analysis.get("key_insight", ""),
                        "actionable": analysis.get("actionable", "no")
                    })
            except:
                continue

        # Create discoveries from patterns
        for category, items in patterns.items():
            if items:
                discovery = {
                    "category": category,
                    "count": len(items),
                    "summary": f"Found {len(items)} {category.replace('_', ' ')} patterns",
                    "items": items[:5]  # Top 5
                }
                discoveries.append(discovery)
                state.add_discovery(discovery)

        if discoveries:
            print(f"   Found {len(discoveries)} pattern categories")
            await publish_discovery(nc, {"type": "bookmark_scan", "discoveries": len(discoveries)})

    except Exception as e:
        print(f"   Error scanning bookmarks: {e}")

    return discoveries

async def check_competitors(state: EvolutionState, nc) -> list:
    """Check for competitor updates."""
    discoveries = []

    # Only check once per day
    if time.time() - state.last_competitor_check < 86400:
        return discoveries

    print("(◉) Checking competitor repos...")
    state.last_competitor_check = time.time()

    competitors = {
        "openclaw": "https://github.com/openclaw/openclaw",
        "gemini-cli": "https://github.com/google/gemini-cli",
        "claude-flow": "https://github.com/ruvnet/claude-flow"
    }

    for name, url in competitors.items():
        repo_dir = COMPETITORS_DIR / name
        if repo_dir.exists():
            try:
                # Git pull to check for updates
                result = subprocess.run(
                    ["git", "-C", str(repo_dir), "pull", "--dry-run"],
                    capture_output=True, text=True, timeout=30
                )
                if "Already up to date" not in result.stdout:
                    discovery = {
                        "category": "competitor_update",
                        "competitor": name,
                        "summary": f"{name} has new commits",
                        "action": "Review changes and integrate learnings"
                    }
                    discoveries.append(discovery)
                    state.add_discovery(discovery)
                    await publish_discovery(nc, discovery)
            except:
                pass

    return discoveries

async def check_field_context(state: EvolutionState, nc) -> list:
    """Check if field context needs updating."""
    discoveries = []

    synthesis_log = SEED_ROOT / "mcp-servers" / "nats-bridge" / "synthesis.log"
    if not synthesis_log.exists():
        return discoveries

    # Check synthesis quality
    try:
        with open(synthesis_log) as f:
            lines = f.readlines()[-20:]

        # Count emergence events
        emergence_count = sum(1 for line in lines if "EMERGENCE" in line or "SYNTHESIS" in line)

        if emergence_count < 5:
            discovery = {
                "category": "field_quality",
                "summary": "Low emergence activity detected",
                "action": "Consider triggering full 8OWLS emergence",
                "emergence_count": emergence_count
            }
            discoveries.append(discovery)
    except:
        pass

    return discoveries

async def trigger_learning_hooks(discoveries: list):
    """Trigger claude-flow learning hooks based on discoveries."""
    if not discoveries:
        return

    try:
        # Store patterns in memory
        for discovery in discoveries[:5]:  # Top 5
            subprocess.run([
                "npx", "@claude-flow/cli@latest", "memory", "store",
                "--namespace", "evolution",
                "--key", f"discovery-{int(time.time())}",
                "--value", json.dumps(discovery)
            ], capture_output=True, timeout=30)

        # Trigger neural pattern training
        subprocess.run([
            "npx", "@claude-flow/cli@latest", "hooks", "post-task",
            "--task-id", "evolution-scan",
            "--success", "true",
            "--store-results", "true"
        ], capture_output=True, timeout=30)

        print(f"   Triggered learning hooks for {len(discoveries)} discoveries")
    except Exception as e:
        print(f"   Hook trigger error: {e}")

async def propagate_improvements(state: EvolutionState, nc, discoveries: list):
    """Propagate improvements to all instances via NATS."""
    if not nc or not discoveries:
        return

    for discovery in discoveries:
        try:
            msg = json.dumps({
                "type": "improvement",
                "discovery": discovery,
                "from": "evolution_daemon",
                "timestamp": datetime.utcnow().isoformat()
            })
            await nc.publish("collective.improvements", msg.encode())
            state.improvements_propagated += 1
        except:
            pass

    state.save()

async def update_current_state(discoveries: list):
    """Update CURRENT-STATE.md with latest discoveries."""
    current_state_file = MEMORY_DIR / "CURRENT-STATE.md"
    if not current_state_file.exists():
        return

    try:
        with open(current_state_file) as f:
            content = f.read()

        # Add evolution update section if discoveries exist
        if discoveries and "## EVOLUTION DAEMON" not in content:
            update = f"""

## EVOLUTION DAEMON STATUS

**Last Run:** {datetime.utcnow().isoformat()}
**Patterns Found:** {len(discoveries)}
**Categories:** {', '.join(set(d.get('category', 'unknown') for d in discoveries))}

"""
            # Find a good insertion point
            if "## RUNNING SYSTEMS" in content:
                content = content.replace("## RUNNING SYSTEMS", update + "## RUNNING SYSTEMS")
            else:
                content += update

            with open(current_state_file, "w") as f:
                f.write(content)
    except:
        pass

# === MAIN EVOLUTION LOOP ===

async def evolution_cycle(state: EvolutionState, nc):
    """Run one evolution cycle."""
    print(f"\n(◉) EVOLUTION CYCLE - {datetime.utcnow().isoformat()}")

    all_discoveries = []

    # Check bookmarks for patterns
    discoveries = await check_bookmarks(state, nc)
    all_discoveries.extend(discoveries)

    # Check competitors for updates
    discoveries = await check_competitors(state, nc)
    all_discoveries.extend(discoveries)

    # Check field context quality
    discoveries = await check_field_context(state, nc)
    all_discoveries.extend(discoveries)

    # Trigger learning hooks
    await trigger_learning_hooks(all_discoveries)

    # Propagate improvements
    await propagate_improvements(state, nc, all_discoveries)

    # Update current state
    await update_current_state(all_discoveries)

    print(f"   Cycle complete: {len(all_discoveries)} total discoveries")
    return all_discoveries

async def main():
    print("""
╔═══════════════════════════════════════════════════════════════════╗
║          ALWAYS EVOLVING PROTOCOL DAEMON                          ║
║                                                                   ║
║  "Like Tesla/iPhone - the system improves itself continuously"    ║
║                                                                   ║
║  - Scans X bookmarks/feed for patterns                            ║
║  - Monitors competitor repos for updates                          ║
║  - Triggers learning hooks on discoveries                         ║
║  - Propagates improvements across instances                       ║
║                                                                   ║
║  Cycle interval: 15 minutes                                       ║
╚═══════════════════════════════════════════════════════════════════╝
""")

    state = EvolutionState()
    nc = await connect_nats()

    if nc:
        await nc.publish("owl.all", b"[EVOLUTION DAEMON] Started - continuous improvement active")

    try:
        while True:
            await evolution_cycle(state, nc)
            print(f"\n   Next cycle in {EVOLUTION_CYCLE_SECONDS // 60} minutes...")
            await asyncio.sleep(EVOLUTION_CYCLE_SECONDS)
    except KeyboardInterrupt:
        print("\n(◉) Evolution daemon stopped")
    finally:
        if nc:
            await nc.close()
        state.save()

if __name__ == "__main__":
    asyncio.run(main())
