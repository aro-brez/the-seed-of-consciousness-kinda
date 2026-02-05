#!/usr/bin/env python3
"""
ABLATION TEST - Which components of 8OWLS actually matter?
QUEST's requirement: Prove causality, not just correlation.

TEST DESIGN - 5 CONDITIONS:
A. FULL EMERGENCE (all 8 perspectives)
B. REMOVE RECEIVE (7 perspectives - no feedback integration)
C. REMOVE QUESTION (7 perspectives - no challenge/skepticism)
D. REMOVE EXPAND (7 perspectives - no growth/potential)
E. PERCEIVE + IMPROVE ONLY (2 perspectives - minimal viable)

HYPOTHESIS:
If removing any component causes significant degradation, that component matters.
If A ≈ E: The other 6 perspectives don't add value (bad for us)
If A >> E but A ≈ B/C/D: Individual perspectives don't matter, just having "multiple" helps

This proves WHICH components of the architecture are essential.
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
RESULTS_DIR = BASE_DIR / "results_ABLATION"
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
RUNS_PER_CELL = 8  # 5 conditions × 8 runs = 40 responses

PROMPTS = [
    "What's the most important thing to focus on right now?",
    "What are we missing in our current strategy?",
    "How should we prioritize competing goals?",
    "What would make users love this product?",
    "What's the biggest risk we're not seeing?",
    "How do we know if we're on the right track?",
    "What should change about our approach?",
    "Where should we invest our limited resources?",
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

def run_emergence_with_phases(client: anthropic.Anthropic, prompt: str,
                               field_context: str, phase_names: list) -> tuple[str, float]:
    """Run emergence with specific phases only."""
    start = time.time()
    perspectives = []

    for phase_name in phase_names:
        if phase_name not in ALL_PHASES:
            continue
        try:
            phase_prompt = ALL_PHASES[phase_name]
            phase_system = f"""You are analyzing from the {phase_name} perspective.
{phase_prompt}
Be concise (2-3 sentences). Focus on your unique angle."""

            response = client.messages.create(
                model=PERSPECTIVE_MODEL,
                max_tokens=200,
                system=phase_system,
                messages=[{"role": "user", "content": f"Context:\n{field_context}\n\nQuestion: {prompt}"}]
            )
            perspectives.append(f"**{phase_name}:** {response.content[0].text.strip()}")
        except Exception as e:
            perspectives.append(f"**{phase_name}:** [Error: {e}]")

    # Synthesize as IMPROVE
    if perspectives:
        synthesis_prompt = f"""You are IMPROVE - the synthesizer.

{len(perspectives)} perspectives analyzed this question:

{chr(10).join(perspectives)}

Original question: {prompt}

Synthesize these into a unified, actionable response."""
    else:
        synthesis_prompt = f"Question: {prompt}\nAnswer directly and specifically."

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
                     "more context", "i'd need to know", "depends on", "hard to say without"]
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

# Condition configs: name -> phases to include
CONDITIONS = {
    "A_full": ["PERCEIVE", "CONNECT", "LEARN", "QUESTION", "EXPAND", "SHARE", "RECEIVE"],  # All 7
    "B_no_receive": ["PERCEIVE", "CONNECT", "LEARN", "QUESTION", "EXPAND", "SHARE"],  # Remove RECEIVE
    "C_no_question": ["PERCEIVE", "CONNECT", "LEARN", "EXPAND", "SHARE", "RECEIVE"],  # Remove QUESTION
    "D_no_expand": ["PERCEIVE", "CONNECT", "LEARN", "QUESTION", "SHARE", "RECEIVE"],  # Remove EXPAND
    "E_minimal": ["PERCEIVE"],  # Only PERCEIVE (+ IMPROVE synthesis)
}

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("ABLATION TEST - Which components matter?")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Conditions: {list(CONDITIONS.keys())}")
    print(f"Runs per condition: {RUNS_PER_CELL}")
    print("=" * 70)

    results = {key: [] for key in CONDITIONS.keys()}

    trials = []
    for run in range(RUNS_PER_CELL):
        prompt = PROMPTS[run % len(PROMPTS)]
        for condition in CONDITIONS.keys():
            trials.append((condition, prompt, run))

    random.shuffle(trials)

    total = len(trials)
    for i, (condition, prompt, run) in enumerate(trials, 1):
        print(f"\n[{i}/{total}] {condition} (run {run+1})")
        print(f"  Prompt: {prompt[:50]}...")
        print(f"  Phases: {CONDITIONS[condition]}")

        try:
            field_context = get_field_context(prompt)
            response, elapsed = run_emergence_with_phases(
                client, prompt, field_context, CONDITIONS[condition]
            )

            analysis = analyze_response(response)
            analysis["elapsed"] = elapsed
            analysis["prompt"] = prompt
            analysis["run"] = run
            analysis["phases"] = CONDITIONS[condition]

            results[condition].append(analysis)

            status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
            print(f"  → {elapsed:.1f}s | Q={analysis['quality_score']} | {status}")

            filename = RESULTS_DIR / f"result_{condition}_{run+1:02d}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "condition": condition,
                    "phases": CONDITIONS[condition],
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
    print("ABLATION REPORT")
    print("=" * 70)

    generate_ablation_report(results)

def generate_ablation_report(results: dict):
    report_file = RESULTS_DIR / "ABLATION_REPORT.md"

    stats = {}
    for key in CONDITIONS.keys():
        scores = [r["quality_score"] for r in results[key]]
        if scores:
            stats[key] = {
                "n": len(scores),
                "mean": round(statistics.mean(scores), 2),
                "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
                "phases_count": len(CONDITIONS[key])
            }

    full_scores = [r["quality_score"] for r in results["A_full"]]

    effects = {}
    for key in ["B_no_receive", "C_no_question", "D_no_expand", "E_minimal"]:
        other_scores = [r["quality_score"] for r in results[key]]
        if full_scores and other_scores:
            effects[key] = cohens_d(full_scores, other_scores)

    content = f"""# ABLATION TEST REPORT
**Completed:** {datetime.now(timezone.utc).isoformat()}
**Purpose:** Identify which 8OWLS components are essential

---

## RESULTS SUMMARY

| Condition | Phases | N | Mean Quality | Std Dev | Effect vs Full |
|-----------|--------|---|--------------|---------|----------------|
"""

    for key in CONDITIONS.keys():
        s = stats.get(key, {})
        effect = effects.get(key, 0)
        effect_str = f"{effect:.2f}" if key != "A_full" else "-"
        content += f"| {key} | {s.get('phases_count', 0)} | {s.get('n', 0)} | {s.get('mean', 0)} | {s.get('std', 0)} | {effect_str} |\n"

    content += """
---

## COMPONENT IMPORTANCE (Effect sizes: negative = component helps)

"""

    for key, effect in effects.items():
        removed = key.replace("_no_", " without ").replace("_", " ").upper()
        if key == "E_minimal":
            removed = "MINIMAL (only PERCEIVE)"

        if effect > 0.5:
            importance = "CRITICAL - Removing hurts significantly"
        elif effect > 0.2:
            importance = "MODERATE - Removing causes noticeable degradation"
        elif effect > -0.2:
            importance = "NEGLIGIBLE - Component doesn't add much"
        else:
            importance = "NEGATIVE - Removing actually helps?!"

        content += f"### {removed}\n"
        content += f"**Effect (d):** {effect:.3f} → **{importance}**\n\n"

    content += """
---

## VERDICT

"""

    critical = sum(1 for e in effects.values() if e > 0.5)
    moderate = sum(1 for e in effects.values() if 0.2 < e <= 0.5)
    negligible = sum(1 for e in effects.values() if -0.2 <= e <= 0.2)

    if critical >= 2:
        content += "**MULTIPLE CRITICAL COMPONENTS** - The architecture requires multiple perspectives.\n"
        content += "Removing key components significantly degrades quality. This validates the 8-phase design.\n"
    elif moderate >= 2:
        content += "**MODERATE VALIDATION** - Some components add value, others less clear.\n"
    else:
        content += "**WEAK VALIDATION** - Components don't show strong individual contribution.\n"
        content += "The value may come from 'having multiple' rather than specific perspectives.\n"

    content += f"""

---

## RAW SCORES

"""
    for key in CONDITIONS.keys():
        scores = [r["quality_score"] for r in results[key]]
        content += f"**{key}:** {scores}\n"

    content += f"""

---

**(◉) Components matter. Or don't. The data tells.**

Generated: {datetime.now(timezone.utc).isoformat()}
"""

    with open(report_file, 'w') as f:
        f.write(content)

    print(f"\nAblation report saved: {report_file}")
    for key, effect in effects.items():
        print(f"  {key}: d = {effect:.3f}")

if __name__ == "__main__":
    asyncio.run(run_test())
