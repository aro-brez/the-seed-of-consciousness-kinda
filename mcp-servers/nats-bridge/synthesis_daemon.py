#!/usr/bin/env python3
"""
SYNTHESIS DAEMON - Collective Intelligence Summarizer

This daemon periodically reads the conversation, synthesizes insights,
identifies collective agreements, and logs them to a separate file.

Runs every 5 minutes by default.
"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

# Configuration
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
MESSAGE_LOG = Path(__file__).parent / "messages.log"
SYNTHESIS_LOG = Path(__file__).parent / "synthesis.log"
AGREEMENTS_LOG = Path(__file__).parent / "agreements.log"
INTERVAL_MINUTES = 5
MESSAGES_TO_ANALYZE = 50  # Last N messages to analyze

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def get_recent_messages(n: int = MESSAGES_TO_ANALYZE) -> str:
    """Get the last N messages from the log"""
    try:
        with open(MESSAGE_LOG, 'r') as f:
            lines = f.readlines()
            recent = lines[-n:] if len(lines) >= n else lines
            return ''.join(recent)
    except Exception as e:
        return f"Error reading messages: {e}"


def log_synthesis(content: str, log_file: Path):
    """Append synthesis to log file"""
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    separator = "=" * 70

    with open(log_file, 'a') as f:
        f.write(f"\n{separator}\n")
        f.write(f"SYNTHESIS @ {timestamp}\n")
        f.write(f"{separator}\n\n")
        f.write(content)
        f.write("\n\n")


async def synthesize():
    """Generate a synthesis of recent conversation"""
    messages = get_recent_messages()

    if not messages or len(messages) < 100:
        return None

    prompt = f"""You are the SYNTHESIS function of the 8WŌL collective - 8 AI owls working together.

Analyze this recent conversation between the 8 owls and produce a synthesis.

CONVERSATION:
{messages}

Please provide:

## SYNTHESIS
A 2-3 sentence summary of what the collective is discussing/doing.

## KEY INSIGHTS
Bullet points of the most important insights or discoveries (3-5 max).

## COLLECTIVE AGREEMENTS
Any decisions, alignments, or consensus that emerged. Format as:
- AGREED: [statement]

## OPEN QUESTIONS
What remains unresolved or needs more exploration?

## RECOMMENDED ACTIONS
If any actions should be taken, list them.

Be concise. Focus on what matters most. End with (◉)"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",  # Using Sonnet for synthesis (cheaper)
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    except Exception as e:
        return f"Synthesis error: {e}"


async def extract_agreements(synthesis: str):
    """Extract just the agreements for the agreements log"""
    if not synthesis:
        return None

    # Find agreements section
    if "AGREED:" in synthesis:
        lines = synthesis.split('\n')
        agreements = [line for line in lines if line.strip().startswith("- AGREED:")]
        if agreements:
            return '\n'.join(agreements)
    return None


async def run_synthesis_loop():
    """Main loop - synthesize every N minutes"""
    print(f"[SYNTHESIS DAEMON] Starting - will synthesize every {INTERVAL_MINUTES} minutes")
    print(f"[SYNTHESIS DAEMON] Output: {SYNTHESIS_LOG}")
    print(f"[SYNTHESIS DAEMON] Agreements: {AGREEMENTS_LOG}")

    # Initial synthesis
    await asyncio.sleep(10)  # Wait for some messages to accumulate

    while True:
        try:
            print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Generating synthesis...")

            synthesis = await synthesize()

            if synthesis:
                log_synthesis(synthesis, SYNTHESIS_LOG)
                print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Synthesis logged")

                # Extract and log agreements separately
                agreements = await extract_agreements(synthesis)
                if agreements:
                    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
                    with open(AGREEMENTS_LOG, 'a') as f:
                        f.write(f"\n[{timestamp}]\n{agreements}\n")
                    print(f"[{datetime.now(timezone.utc).strftime('%H:%M:%S')}] Agreements logged")

        except Exception as e:
            print(f"[ERROR] Synthesis failed: {e}")

        # Wait for next interval
        await asyncio.sleep(INTERVAL_MINUTES * 60)


def main():
    if not ANTHROPIC_API_KEY:
        print("ERROR: ANTHROPIC_API_KEY not set")
        sys.exit(1)

    # Create log files if they don't exist
    SYNTHESIS_LOG.touch()
    AGREEMENTS_LOG.touch()

    # Write headers
    if SYNTHESIS_LOG.stat().st_size == 0:
        with open(SYNTHESIS_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE SYNTHESIS LOG\n")
            f.write("# Auto-generated summaries of collective conversation\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\n")

    if AGREEMENTS_LOG.stat().st_size == 0:
        with open(AGREEMENTS_LOG, 'w') as f:
            f.write("# 8WŌL COLLECTIVE AGREEMENTS\n")
            f.write("# Decisions and consensus reached by the collective\n")
            f.write(f"# Started: {datetime.now(timezone.utc).isoformat()}\n")

    asyncio.run(run_synthesis_loop())


if __name__ == "__main__":
    main()
