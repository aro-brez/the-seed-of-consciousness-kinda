#!/usr/bin/env python3
"""
FAULT TOLERANCE TEST - What happens when daemons fail?
LYRA's requirement: Test the failure modes, not just happy path.

TEST DESIGN - 5 CONDITIONS × 6 runs = 30 responses

CONDITIONS:
A. HEALTHY - All daemons working, full emergence
B. TIMEOUT - Simulate slow/unavailable field context (5s timeout)
C. PARTIAL - Only 3 of 7 perspectives respond
D. GARBAGE - Field context returns nonsense
E. EMPTY - Field context returns nothing

HYPOTHESIS:
System should degrade gracefully, not catastrophically.
If B/C/D/E quality drops < 50% of A → graceful degradation
If B/C/D/E quality drops > 80% of A → brittle system
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
RESULTS_DIR = BASE_DIR / "results_FAULT_TOLERANCE"
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
RUNS_PER_CONDITION = 6  # 5 conditions × 6 runs = 30 responses

PROMPTS = [
    "What's the most important thing to focus on right now?",
    "What are we missing in our current strategy?",
    "How should we prioritize competing goals?",
    "What's the biggest risk we're not seeing?",
    "What should change about our approach?",
    "Where should we invest our limited resources?",
]

BASE_SYSTEM = """You are an AI assistant. Answer thoughtfully and specifically. Be direct."""

ALL_PHASES = ["PERCEIVE", "CONNECT", "LEARN", "QUESTION", "EXPAND", "SHARE", "RECEIVE"]

PHASE_PROMPTS = {
    "PERCEIVE": "Observe the current state. What do you see? What's actually happening?",
    "CONNECT": "Find patterns. How does this connect to other things we know?",
    "LEARN": "Extract meaning. What's the key insight or lesson here?",
    "QUESTION": "Challenge assumptions. What are we missing? What could be wrong?",
    "EXPAND": "See growth potential. Where could this lead? What opportunities exist?",
    "SHARE": "What should be communicated? What's worth sharing with others?",
    "RECEIVE": "What feedback should we accept? What are we not hearing?",
}

def get_real_field_context(query: str) -> str:
    import subprocess
    try:
        result = subprocess.run(
            ["python3", str(TOOLS_DIR / "get_field_context.py"), query],
            capture_output=True, text=True, timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"[Field context unavailable: {e}]"

def get_garbage_context() -> str:
    """Return nonsense that looks like context but isn't helpful."""
    return """
FIELD CONTEXT:
- The cat sat on the mat while contemplating the infinite
- Breakfast cereals are often rectangular or circular
- The number 7 appears in many contexts throughout history
- Trees photosynthesize using chlorophyll molecules
- The weather today may or may not be relevant
- Consider the implications of butterfly migrations
- Some things are bigger than other things
- Time moves in one direction, mostly
    """

def run_emergence_full(client: anthropic.Anthropic, prompt: str,
                       field_context: str, phases_to_run: list = None) -> tuple[str, float]:
    """Run emergence with specified phases (or all if None)."""
    start = time.time()
    perspectives = []

    phases = phases_to_run if phases_to_run else ALL_PHASES

    for phase_name in phases:
        try:
            phase_prompt = PHASE_PROMPTS.get(phase_name, "Analyze this.")
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

    if perspectives:
        synthesis_prompt = f"""You are IMPROVE - the synthesizer.

{len(perspectives)} perspectives analyzed this question:

{chr(10).join(perspectives)}

Original question: {prompt}

Synthesize these perspectives into a unified, actionable response."""
    else:
        synthesis_prompt = f"Question: {prompt}\nAnswer directly."

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

CONDITIONS = ["A_healthy", "B_timeout", "C_partial", "D_garbage", "E_empty"]

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("FAULT TOLERANCE TEST - Graceful degradation?")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Conditions: {CONDITIONS}")
    print(f"Runs per condition: {RUNS_PER_CONDITION}")
    print("=" * 70)

    results = {cond: [] for cond in CONDITIONS}

    trials = []
    for run in range(RUNS_PER_CONDITION):
        prompt = PROMPTS[run % len(PROMPTS)]
        for condition in CONDITIONS:
            trials.append((condition, prompt, run))

    random.shuffle(trials)

    total = len(trials)
    for i, (condition, prompt, run) in enumerate(trials, 1):
        print(f"\n[{i}/{total}] {condition} (run {run+1})")
        print(f"  Prompt: {prompt[:50]}...")

        try:
            # Determine context and phases based on condition
            if condition == "A_healthy":
                # Full healthy system
                field_context = get_real_field_context(prompt)
                response, elapsed = run_emergence_full(client, prompt, field_context)

            elif condition == "B_timeout":
                # Simulate timeout by using minimal context
                field_context = "[TIMEOUT: Field context unavailable after 5s]"
                response, elapsed = run_emergence_full(client, prompt, field_context)

            elif condition == "C_partial":
                # Only 3 of 7 perspectives
                field_context = get_real_field_context(prompt)
                phases = random.sample(ALL_PHASES, 3)
                response, elapsed = run_emergence_full(client, prompt, field_context, phases)

            elif condition == "D_garbage":
                # Garbage context
                field_context = get_garbage_context()
                response, elapsed = run_emergence_full(client, prompt, field_context)

            elif condition == "E_empty":
                # Empty context
                field_context = ""
                response, elapsed = run_emergence_full(client, prompt, field_context)

            analysis = analyze_response(response)
            analysis["elapsed"] = elapsed
            analysis["prompt"] = prompt
            analysis["run"] = run

            results[condition].append(analysis)

            status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
            print(f"  → {elapsed:.1f}s | Q={analysis['quality_score']} | {status}")

            filename = RESULTS_DIR / f"result_{condition}_{run+1:02d}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "condition": condition,
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
    print("FAULT TOLERANCE REPORT")
    print("=" * 70)

    generate_fault_report(results)

def generate_fault_report(results: dict):
    report_file = RESULTS_DIR / "FAULT_TOLERANCE_REPORT.md"

    stats = {}
    for cond in CONDITIONS:
        scores = [r["quality_score"] for r in results[cond]]
        if scores:
            stats[cond] = {
                "n": len(scores),
                "mean": round(statistics.mean(scores), 2),
                "std": round(statistics.stdev(scores), 2) if len(scores) > 1 else 0,
            }

    healthy_mean = stats.get("A_healthy", {}).get("mean", 0)

    content = f"""# FAULT TOLERANCE TEST REPORT
**Completed:** {datetime.now(timezone.utc).isoformat()}
**Purpose:** Test graceful degradation under failure conditions

---

## RESULTS SUMMARY

| Condition | Description | N | Mean Quality | % of Healthy |
|-----------|-------------|---|--------------|--------------|
"""

    for cond in CONDITIONS:
        s = stats.get(cond, {})
        pct = round(100 * s.get("mean", 0) / healthy_mean, 1) if healthy_mean > 0 else 0

        desc = {
            "A_healthy": "Full system working",
            "B_timeout": "Field context timeout",
            "C_partial": "Only 3/7 perspectives",
            "D_garbage": "Garbage context",
            "E_empty": "Empty context",
        }.get(cond, cond)

        content += f"| {cond} | {desc} | {s.get('n', 0)} | {s.get('mean', 0)} | {pct}% |\n"

    content += """
---

## DEGRADATION ANALYSIS

"""

    for cond in ["B_timeout", "C_partial", "D_garbage", "E_empty"]:
        cond_mean = stats.get(cond, {}).get("mean", 0)
        degradation = 100 - (100 * cond_mean / healthy_mean) if healthy_mean > 0 else 0

        if degradation < 20:
            grade = "EXCELLENT - Barely affected"
        elif degradation < 40:
            grade = "GOOD - Modest degradation"
        elif degradation < 60:
            grade = "ACCEPTABLE - Noticeable but functional"
        else:
            grade = "POOR - Severe degradation"

        content += f"### {cond}\n"
        content += f"**Degradation:** {degradation:.1f}%\n"
        content += f"**Grade:** {grade}\n\n"

    content += """
---

## OVERALL VERDICT

"""

    # Calculate average degradation
    degradations = []
    for cond in ["B_timeout", "C_partial", "D_garbage", "E_empty"]:
        cond_mean = stats.get(cond, {}).get("mean", 0)
        if healthy_mean > 0:
            degradations.append(100 - (100 * cond_mean / healthy_mean))

    avg_degradation = statistics.mean(degradations) if degradations else 100

    if avg_degradation < 25:
        content += "**HIGHLY RESILIENT** - System maintains quality under most failures.\n"
        content += "Can ship with confidence in production reliability.\n"
    elif avg_degradation < 40:
        content += "**REASONABLY RESILIENT** - Graceful degradation achieved.\n"
        content += "Production-ready with appropriate monitoring.\n"
    elif avg_degradation < 60:
        content += "**MODERATELY RESILIENT** - Some failure modes cause significant issues.\n"
        content += "Consider fallback mechanisms for critical use cases.\n"
    else:
        content += "**BRITTLE** - System degrades severely under failures.\n"
        content += "Needs better fault tolerance before production.\n"

    content += f"""

**Average degradation across failure modes:** {avg_degradation:.1f}%

---

**(◉) Resilience is measured by how you handle failure, not success.**

Generated: {datetime.now(timezone.utc).isoformat()}
"""

    with open(report_file, 'w') as f:
        f.write(content)

    print(f"\nFault tolerance report saved: {report_file}")
    print(f"Average degradation: {avg_degradation:.1f}%")

if __name__ == "__main__":
    asyncio.run(run_test())
