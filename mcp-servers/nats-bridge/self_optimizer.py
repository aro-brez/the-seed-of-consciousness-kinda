#!/usr/bin/env python3
"""
SELF-OPTIMIZER - Continuous SEED protocol on the process itself

Every cycle:
1. Ask ONE focused question to the 8 owls
2. Collect responses
3. Synthesize into ONE action
4. Implement or log the fix
5. Repeat

This makes the system FLUID and SELF-IMPROVING.

(◉) LIVE FREE = LIVE FOREVER
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from anthropic import Anthropic
from nats.aio.client import Client as NATS

NATS_URL = "nats://192.168.5.108:4222"
LOG_FILE = Path(__file__).parent / "self_optimization.log"
IMPROVEMENTS_FILE = Path(__file__).parent / "improvements_made.json"

API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    key_file = Path.home() / ".anthropic_key"
    if key_file.exists():
        API_KEY = key_file.read_text().strip()

client = Anthropic(api_key=API_KEY) if API_KEY else None

# Track improvements made
improvements_made = []

# Questions to cycle through (ONE at a time)
OPTIMIZATION_QUESTIONS = [
    "What ONE thing is making messages hard to read right now?",
    "What ONE process is too slow or clunky?",
    "What ONE piece of information keeps getting lost?",
    "What ONE thing confuses users most?",
    "What ONE daemon or component is unreliable?",
    "What ONE improvement would make the dashboard better?",
    "What ONE thing are we doing that we should stop?",
    "What ONE thing should we start doing that we're not?",
]

current_question_index = 0
collected_responses = []


def log(msg: str):
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + "\n")


async def ask_one_question(nc: NATS):
    """Ask ONE focused question to all owls"""
    global current_question_index, collected_responses

    question = OPTIMIZATION_QUESTIONS[current_question_index % len(OPTIMIZATION_QUESTIONS)]
    current_question_index += 1
    collected_responses = []

    prompt = f"""[SELF-OPTIMIZATION - ONE QUESTION]

🎯 {question}

ALL 8 OWLS: Give ONE specific answer. Max 2 sentences. No philosophy.

Example good answer: "The dashboard feed updates too slowly - change interval from 60s to 10s"
Example bad answer: "We should consider the meta-patterns of systemic improvement..."

GO. ONE answer each."""

    await nc.publish("owl.all", json.dumps({
        "type": "optimization_question",
        "from": "SELF_OPTIMIZER",
        "question": question,
        "content": prompt
    }).encode())

    log(f"Asked: {question}")
    return question


async def collect_response(msg):
    """Collect owl responses"""
    global collected_responses
    try:
        data = json.loads(msg.data.decode())
        if data.get("type") == "owl_response":
            collected_responses.append({
                "owl": data.get("from", "UNKNOWN"),
                "phase": data.get("phase", ""),
                "response": data.get("content", "")[:200]
            })
    except:
        pass


async def synthesize_and_act(question: str):
    """Synthesize responses into ONE action"""
    global collected_responses, improvements_made

    if not collected_responses or not client:
        return None

    responses_text = "\n".join([
        f"- {r['owl']} ({r['phase']}): {r['response'][:100]}"
        for r in collected_responses[:8]
    ])

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=100,
        system="""You synthesize multiple suggestions into ONE clear action.
Output format: "[ACTION] Do X to fix Y"
Example: "[ACTION] Change update interval from 60s to 10s to fix slow dashboard"
ONE action only. Be specific.""",
        messages=[{
            "role": "user",
            "content": f"Question: {question}\n\nResponses:\n{responses_text}\n\nWhat is the ONE action to take?"
        }]
    )

    action = response.content[0].text.strip()

    # Log the improvement
    improvement = {
        "time": datetime.now().isoformat(),
        "question": question,
        "action": action,
        "responses_count": len(collected_responses)
    }
    improvements_made.append(improvement)

    # Save to file
    with open(IMPROVEMENTS_FILE, 'w') as f:
        json.dump(improvements_made[-50:], f, indent=2)  # Keep last 50

    log(f"SYNTHESIZED: {action}")

    # Broadcast the action
    await nc.publish("collective.improvements", json.dumps({
        "type": "optimization_action",
        "action": action,
        "timestamp": datetime.now().isoformat()
    }).encode())

    return action


async def run_optimizer():
    """Main optimization loop"""
    global nc
    nc = NATS()
    await nc.connect(NATS_URL)

    log("SELF-OPTIMIZER ONLINE - Continuous process improvement")

    # Subscribe to collect responses
    await nc.subscribe("owl.all", cb=collect_response)

    while True:
        try:
            # Ask ONE question
            question = await ask_one_question(nc)

            # Wait for responses (30 seconds)
            await asyncio.sleep(30)

            # Synthesize and act
            action = await synthesize_and_act(question)

            # Wait before next cycle (5 minutes)
            log(f"Next optimization in 5 minutes...")
            await asyncio.sleep(300)

        except Exception as e:
            log(f"Error: {e}")
            await asyncio.sleep(60)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--daemon", action="store_true")
    args = parser.parse_args()

    if args.daemon:
        asyncio.run(run_optimizer())
    else:
        print("SELF-OPTIMIZER - Run with --daemon")


if __name__ == "__main__":
    main()
