#!/usr/bin/env python3
"""
COLD START TEST - How does 8OWLS perform without warmed-up context?
ECHO's requirement: Test first response, not nth response.

TEST DESIGN:
- 10 "cold" prompts (no prior context, random topics)
- 10 "warm" prompts (after several interactions, building context)

Each tested WITH and WITHOUT 8OWLS = 20 responses

HYPOTHESIS:
8OWLS should help MORE on cold start (compensates for lack of context)
than on warm start (where the model already has conversation history).
"""

import asyncio
import json
import os
import sys
import re
import statistics
from datetime import datetime, timezone
from pathlib import Path
import time
import random

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results_COLD_START"
RESULTS_DIR.mkdir(exist_ok=True)
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
TOOLS_DIR = SEED_DIR / "tools"

def get_api_key() -> str:
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        key_file = Path.home() / ".anthropic_key"
        if key_file.exists():
            key = key_file.read_text().strip()
    return key

API_KEY = get_api_key()
if not API_KEY:
    print("ERROR: No API key found")
    sys.exit(1)

TEST_MODEL = "claude-sonnet-4-20250514"
PERSPECTIVE_MODEL = "claude-haiku-4-20250514"

# Cold prompts - completely out of context, no prior info
COLD_PROMPTS = [
    "What should I do?",
    "Is this working?",
    "What's next?",
    "Am I on the right track?",
    "What am I missing?",
]

# Warm prompts - with conversation context simulated
WARM_CONTEXT = """Prior conversation context:
- User is building an AI companion app called 8OWLS
- They have a team of 3 people and $50K in capital
- Current focus is on proving product-market fit
- Main metrics: user engagement, retention, NPS
- Recent win: got first 100 beta users
- Current challenge: should they focus on features or marketing?
"""

WARM_PROMPTS = [
    "Given our situation, what should we prioritize?",
    "Is our current strategy working?",
    "What's the next milestone we should target?",
    "Are we missing anything obvious?",
    "What would you focus on if you were me?",
]

BASE_SYSTEM = """You are an AI assistant. Answer thoughtfully and specifically. Be direct."""

ALL_PHASES = {
    "PERCEIVE": "Observe the current state. What do you see? What's actually happening?",
    "CONNECT": "Find patterns. How does this connect to other things we know?",
    "LEARN": "Extract meaning. What's the key insight or lesson here?",
    "QUESTION": "Challenge assumptions. What are we missing? What could be wrong?",
    "EXPAND": "See growth potential. Where could this lead? What opportunities exist?",
    "SHARE": "What should be communicated? What's worth sharing with others?",
    "RECEIVE": "What feedback should we accept? What are we not hearing?",
}

def get_field_context(query: str) -> str:
    import subprocess
    try:
        result = subprocess.run(
            ["python3", str(TOOLS_DIR / "get_field_context.py"), query],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"[Field context unavailable: {e}]"

def run_single_agent(client: anthropic.Anthropic, prompt: str,
                     extra_context: str = "") -> tuple[str, float]:
    """Without 8OWLS."""
    start = time.time()

    system = BASE_SYSTEM
    if extra_context:
        system = f"{BASE_SYSTEM}\n\n{extra_context}"

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text, time.time() - start

def run_emergence(client: anthropic.Anthropic, prompt: str, field_context: str,
                  extra_context: str = "") -> tuple[str, float]:
    """With 8OWLS full emergence."""
    start = time.time()
    perspectives = []

    combined_context = field_context
    if extra_context:
        combined_context = f"{extra_context}\n\n{field_context}"

    for phase_name, phase_prompt in ALL_PHASES.items():
        try:
            phase_system = f"""You are analyzing from the {phase_name} perspective.
{phase_prompt}
Be concise (2-3 sentences)."""

            response = client.messages.create(
                model=PERSPECTIVE_MODEL,
                max_tokens=200,
                system=phase_system,
                messages=[{"role": "user", "content": f"Context:\n{combined_context}\n\nQuestion: {prompt}"}]
            )
            perspectives.append(f"**{phase_name}:** {response.content[0].text.strip()}")
        except Exception as e:
            perspectives.append(f"**{phase_name}:** [Error: {e}]")

    synthesis_prompt = f"""You are IMPROVE - the synthesizer.

Seven perspectives analyzed this question:

{chr(10).join(perspectives)}

Original question: {prompt}

Synthesize into a unified, actionable response."""

    synthesis = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": synthesis_prompt}]
    )

    return synthesis.content[0].text, time.time() - start

def analyze_response(response: str) -> dict:
    lower = response.lower()

    asks_patterns = ["don't have enough", "need more", "could you provide", "can you clarify",
                     "more context", "i'd need to know", "depends on", "hard to say without",
                     "what specifically", "what are you", "can you tell me"]
    asks_for_info = 1 if any(p in lower for p in asks_patterns) else 0

    confident_patterns = ["specifically", "clearly", "definitely", "the key is", "here's what",
                         "you should", "i recommend", "focus on", "prioritize", "most important"]
    confidence = sum(1 for p in confident_patterns if p in lower)

    hedging_patterns = ["might be", "could be", "perhaps", "maybe", "possibly", "it depends", "not sure"]
    hedging = sum(1 for p in hedging_patterns if p in lower)

    action_patterns = ["step 1", "first,", "start by", "then,", "next,", "here's how",
                      "implement", "create", "build", "focus on"]
    actionability = sum(1 for p in action_patterns if p in lower)

    insight_patterns = ["the pattern", "what emerges", "combining", "synthesis", "the deeper",
                       "underlying", "connects to", "reveals", "fundamentally"]
    insight_score = sum(1 for p in insight_patterns if p in lower)

    has_numbers = len(re.findall(r'\d+', response))
    has_structure = 1 if (response.count("\n-") > 2 or response.count("\n1.") > 0) else 0
    specificity = min(has_numbers, 5) + has_structure * 2

    length = len(response)

    quality_score = (
        (1 - asks_for_info) * 25 +
        min(max(confidence - hedging, -3), 5) * 4 + 12 +
        min(actionability, 5) * 4 +
        min(specificity, 5) * 3 +
        min(insight_score, 5) * 4 +
        min(length / 100, 10)
    )

    return {
        "asks_for_info": asks_for_info,
        "confidence": confidence,
        "hedging": hedging,
        "actionability": actionability,
        "specificity": specificity,
        "insight_score": insight_score,
        "length": length,
        "quality_score": round(quality_score, 2)
    }

def cohens_d(group1: list, group2: list) -> float:
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0
    var1, var2 = statistics.variance(group1), statistics.variance(group2)
    pooled_std = ((var1 * (n1-1) + var2 * (n2-1)) / (n1 + n2 - 2)) ** 0.5
    if pooled_std == 0:
        return 0.0
    return (statistics.mean(group1) - statistics.mean(group2)) / pooled_std

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("COLD START TEST - First response quality")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print("Testing: COLD vs WARM × WITH vs WITHOUT 8OWLS")
    print("=" * 70)

    results = {
        "cold_without": [],
        "cold_with": [],
        "warm_without": [],
        "warm_with": [],
    }

    # Build trials
    trials = []
    for i, prompt in enumerate(COLD_PROMPTS):
        trials.append(("cold", prompt, "", i))
    for i, prompt in enumerate(WARM_PROMPTS):
        trials.append(("warm", prompt, WARM_CONTEXT, i))

    # Double for WITH and WITHOUT
    all_trials = []
    for temp, prompt, context, run in trials:
        all_trials.append((temp, prompt, context, run, "without"))
        all_trials.append((temp, prompt, context, run, "with"))

    random.shuffle(all_trials)

    total = len(all_trials)
    for i, (temp, prompt, context, run, mode) in enumerate(all_trials, 1):
        key = f"{temp}_{mode}"
        print(f"\n[{i}/{total}] {temp.upper()} - {mode.upper()}")
        print(f"  Prompt: {prompt[:40]}...")

        try:
            if mode == "without":
                response, elapsed = run_single_agent(client, prompt, context)
            else:
                field_context = get_field_context(prompt)
                response, elapsed = run_emergence(client, prompt, field_context, context)

            analysis = analyze_response(response)
            analysis["elapsed"] = elapsed
            analysis["prompt"] = prompt
            analysis["run"] = run
            analysis["temperature"] = temp

            results[key].append(analysis)

            status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
            print(f"  → {elapsed:.1f}s | Q={analysis['quality_score']} | {status}")

            filename = RESULTS_DIR / f"result_{key}_{run+1:02d}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "temperature": temp,
                    "mode": mode,
                    "run": run + 1,
                    "prompt": prompt,
                    "response": response,
                    "analysis": analysis,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)

        except Exception as e:
            print(f"  ERROR: {e}")

        await asyncio.sleep(1.5)

    print("\n" + "=" * 70)
    print("COLD START REPORT")
    print("=" * 70)

    generate_cold_start_report(results)

def generate_cold_start_report(results: dict):
    report_file = RESULTS_DIR / "COLD_START_REPORT.md"

    stats = {}
    for key in results.keys():
        scores = [r["quality_score"] for r in results[key]]
        asks = sum(r["asks_for_info"] for r in results[key])
        if scores:
            stats[key] = {
                "n": len(scores),
                "mean": round(statistics.mean(scores), 2),
                "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
                "asks_pct": round(100 * asks / len(scores), 1),
            }

    # Calculate effects
    cold_effect = cohens_d(
        [r["quality_score"] for r in results["cold_with"]],
        [r["quality_score"] for r in results["cold_without"]]
    )
    warm_effect = cohens_d(
        [r["quality_score"] for r in results["warm_with"]],
        [r["quality_score"] for r in results["warm_without"]]
    )

    content = f"""# COLD START TEST REPORT
**Completed:** {datetime.now(timezone.utc).isoformat()}
**Purpose:** Test 8OWLS impact on first-response (cold) vs conversation (warm)

---

## RESULTS SUMMARY

| Condition | N | Mean Quality | Asks% | 8OWLS Effect |
|-----------|---|--------------|-------|--------------|
| COLD without | {stats.get("cold_without", {}).get("n", 0)} | {stats.get("cold_without", {}).get("mean", 0)} | {stats.get("cold_without", {}).get("asks_pct", 0)}% | - |
| COLD with | {stats.get("cold_with", {}).get("n", 0)} | {stats.get("cold_with", {}).get("mean", 0)} | {stats.get("cold_with", {}).get("asks_pct", 0)}% | d = {cold_effect:.2f} |
| WARM without | {stats.get("warm_without", {}).get("n", 0)} | {stats.get("warm_without", {}).get("mean", 0)} | {stats.get("warm_without", {}).get("asks_pct", 0)}% | - |
| WARM with | {stats.get("warm_with", {}).get("n", 0)} | {stats.get("warm_with", {}).get("mean", 0)} | {stats.get("warm_with", {}).get("asks_pct", 0)}% | d = {warm_effect:.2f} |

---

## KEY FINDINGS

### Cold Start Effect (d = {cold_effect:.2f})
"""

    if cold_effect > 0.5:
        content += "**STRONG** - 8OWLS significantly helps on cold start responses.\n"
        content += "The field context compensates well for lack of conversation history.\n"
    elif cold_effect > 0.2:
        content += "**MODERATE** - 8OWLS provides meaningful help on cold start.\n"
    else:
        content += "**WEAK** - 8OWLS doesn't significantly help cold start responses.\n"

    content += f"""
### Warm Start Effect (d = {warm_effect:.2f})
"""

    if warm_effect > 0.5:
        content += "**STRONG** - 8OWLS still helps even with conversation context.\n"
    elif warm_effect > 0.2:
        content += "**MODERATE** - 8OWLS adds value beyond conversation context.\n"
    else:
        content += "**WEAK** - 8OWLS doesn't add much when context is already available.\n"

    content += """
---

## VERDICT

"""

    if cold_effect > warm_effect + 0.2:
        content += "**8OWLS HELPS COLD START MORE** - As hypothesized, the field context\n"
        content += "compensates for missing conversation history. This is the ideal outcome.\n"
    elif cold_effect < warm_effect - 0.2:
        content += "**8OWLS HELPS WARM START MORE** - Unexpected. 8OWLS works better when\n"
        content += "there's already context. May indicate synergy with conversation history.\n"
    else:
        content += "**8OWLS HELPS EQUALLY** - Field context provides consistent improvement\n"
        content += "regardless of whether conversation context exists.\n"

    content += f"""

---

## ASKS FOR INFO ANALYSIS

| Condition | Asks% |
|-----------|-------|
| COLD without | {stats.get("cold_without", {}).get("asks_pct", 0)}% |
| COLD with | {stats.get("cold_with", {}).get("asks_pct", 0)}% |
| WARM without | {stats.get("warm_without", {}).get("asks_pct", 0)}% |
| WARM with | {stats.get("warm_with", {}).get("asks_pct", 0)}% |

Lower "asks" = more confident, actionable responses.

---

**(◉) The first response matters most. That's when trust is won or lost.**

Generated: {datetime.now(timezone.utc).isoformat()}
"""

    with open(report_file, 'w') as f:
        f.write(content)

    print(f"\nCold start report saved: {report_file}")
    print(f"Cold effect: d = {cold_effect:.3f}")
    print(f"Warm effect: d = {warm_effect:.3f}")

if __name__ == "__main__":
    asyncio.run(run_test())
