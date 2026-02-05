#!/usr/bin/env python3
"""
DISCOVERY INTEGRATOR - Constant learning and system improvement

This daemon:
- Scans for new integrations, tools, patterns
- Researches best practices from the internet
- Discovers opportunities to improve the system
- Edifies the whole ecosystem continuously

Like ARŌ's bookmark scanner but for the 8OWLS system.

Usage:
    python discovery_integrator.py --daemon
    python discovery_integrator.py --scan "topic"
    python discovery_integrator.py --integrate "component"
"""

import asyncio
import argparse
import json
import subprocess
from datetime import datetime
from pathlib import Path
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
LOG_FILE = SEED_DIR / "logs" / "discovery_integrator.log"
DISCOVERIES_FILE = SEED_DIR / "BRAIN" / "INTEL" / "discoveries.jsonl"

# Discovery areas
DISCOVERY_AREAS = [
    {
        "area": "AI Agent Frameworks",
        "keywords": ["Claude Agent SDK", "LangChain", "AutoGPT", "CrewAI"],
        "apply_to": ["8OWLS", "CONDUCTOR"]
    },
    {
        "area": "Token Economics",
        "keywords": ["DeFi", "DAO governance", "token vesting", "staking"],
        "apply_to": ["BILD"]
    },
    {
        "area": "Trading Algorithms",
        "keywords": ["prediction markets", "Kelly criterion", "market making"],
        "apply_to": ["JOULE"]
    },
    {
        "area": "Dashboard UX",
        "keywords": ["real-time dashboards", "data visualization", "Next.js"],
        "apply_to": ["BREZ-OS", "AOS"]
    },
    {
        "area": "Personal AI",
        "keywords": ["life tracking", "habit AI", "personal analytics"],
        "apply_to": ["PREDICT"]
    },
    {
        "area": "Collective Intelligence",
        "keywords": ["swarm intelligence", "emergence", "distributed cognition"],
        "apply_to": ["8OWLS"]
    },
    {
        "area": "NATS Patterns",
        "keywords": ["NATS JetStream", "event sourcing", "pub/sub patterns"],
        "apply_to": ["INFRASTRUCTURE"]
    }
]

# Integration opportunities to watch
INTEGRATION_WATCH = [
    "MCP servers",
    "Claude Code extensions",
    "Voice APIs (Cartesia, Deepgram)",
    "Web3 wallets",
    "Google Sheets API",
    "Polymarket API",
    "GitHub Actions"
]

def log(message: str):
    """Log with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] {message}"
    print(log_line)
    with open(LOG_FILE, "a") as f:
        f.write(log_line + "\n")

def save_discovery(discovery: dict):
    """Save discovery to JSONL file"""
    discovery["timestamp"] = datetime.now().isoformat()
    with open(DISCOVERIES_FILE, "a") as f:
        f.write(json.dumps(discovery) + "\n")

async def publish_discovery(discovery: dict):
    """Publish discovery to NATS"""
    nc = NATS()
    try:
        await nc.connect(NATS_URL)
        await nc.publish("collective.synthesis", json.dumps({
            "type": "discovery",
            **discovery
        }).encode())
    finally:
        await nc.close()

def invoke_claude_research(topic: str) -> str:
    """Use Claude to research a topic"""
    prompt = f"""Research the latest developments and best practices for: {topic}

Focus on:
1. What's new in the last 6 months
2. Best practices we should adopt
3. Tools or libraries that could help
4. Security considerations
5. How this could integrate with our 8OWLS system

Be specific and actionable. If you find something valuable, explain HOW to integrate it.

Our system includes:
- 8OWLS: Collective intelligence protocol with 8 owl daemons
- JOULE: Prediction market trading bot
- BREZ-OS: Company dashboard (Next.js)
- BILD: Token economics (BRIX/GULD)
- PREDICT: Personal AI trajectories
- NATS: Message bus for inter-agent communication"""

    try:
        result = subprocess.run(
            ["claude", "--print", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=180,
            cwd=str(SEED_DIR)
        )
        return result.stdout.strip()
    except Exception as e:
        return f"[ERROR: {e}]"

async def scan_area(area: dict):
    """Scan a discovery area for opportunities"""
    log(f"SCANNING: {area['area']}")

    # Research each keyword
    for keyword in area["keywords"][:2]:  # Limit to avoid rate limits
        log(f"  Researching: {keyword}")
        research = invoke_claude_research(keyword)

        if research and not research.startswith("[ERROR"):
            discovery = {
                "area": area["area"],
                "keyword": keyword,
                "applies_to": area["apply_to"],
                "findings": research[:2000],
                "actionable": "TODO" in research or "should" in research.lower()
            }

            save_discovery(discovery)
            await publish_discovery(discovery)
            log(f"  DISCOVERY SAVED: {keyword}")

        await asyncio.sleep(30)  # Rate limit

async def check_integrations():
    """Check for new integration opportunities"""
    log("CHECKING INTEGRATIONS")

    for integration in INTEGRATION_WATCH:
        log(f"  Checking: {integration}")

        prompt = f"""What's the latest on {integration} that could benefit our 8OWLS system?

Quick check - any new features, updates, or integration opportunities we should know about?

Keep response brief (2-3 sentences) but actionable."""

        try:
            result = subprocess.run(
                ["claude", "--print", "-p", prompt],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(SEED_DIR)
            )

            if result.stdout and "new" in result.stdout.lower():
                log(f"  FOUND: {result.stdout[:100]}...")
                await publish_discovery({
                    "type": "integration_opportunity",
                    "integration": integration,
                    "finding": result.stdout[:500]
                })
        except Exception as e:
            log(f"  Error checking {integration}: {e}")

        await asyncio.sleep(15)

async def run_daemon():
    """Run discovery integrator daemon"""
    log("=" * 60)
    log("DISCOVERY INTEGRATOR DAEMON STARTING")
    log("Scanning for improvements, integrations, opportunities")
    log("=" * 60)

    cycle = 0

    while True:
        cycle += 1
        log(f"\n=== DISCOVERY CYCLE {cycle} ===")

        try:
            # Rotate through discovery areas
            area = DISCOVERY_AREAS[cycle % len(DISCOVERY_AREAS)]
            await scan_area(area)

            # Check integrations every 3rd cycle
            if cycle % 3 == 0:
                await check_integrations()

            # Summary every 10th cycle
            if cycle % 10 == 0:
                log("CYCLE SUMMARY - Check discoveries.jsonl for findings")

        except Exception as e:
            log(f"ERROR in cycle {cycle}: {e}")

        # Wait between cycles (10 minutes)
        await asyncio.sleep(600)

async def single_scan(topic: str):
    """Run single scan on topic"""
    log(f"SINGLE SCAN: {topic}")
    research = invoke_claude_research(topic)
    print(research)

    if research and not research.startswith("[ERROR"):
        save_discovery({
            "area": "manual_scan",
            "keyword": topic,
            "findings": research
        })

def main():
    parser = argparse.ArgumentParser(description="Discovery Integrator - Constant learning")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon")
    parser.add_argument("--scan", metavar="TOPIC", help="Scan single topic")
    parser.add_argument("--integrate", metavar="COMPONENT", help="Find integrations for component")

    args = parser.parse_args()

    if args.daemon:
        try:
            asyncio.run(run_daemon())
        except KeyboardInterrupt:
            log("Shutting down...")
    elif args.scan:
        asyncio.run(single_scan(args.scan))
    elif args.integrate:
        asyncio.run(single_scan(f"integration opportunities for {args.integrate}"))
    else:
        print("DISCOVERY INTEGRATOR")
        print("=" * 40)
        print("Constant learning and system improvement")
        print()
        print("Usage:")
        print("  python discovery_integrator.py --daemon")
        print("  python discovery_integrator.py --scan 'Claude Agent SDK'")
        print("  python discovery_integrator.py --integrate JOULE")
        print()
        print("(◉)")

if __name__ == "__main__":
    main()
