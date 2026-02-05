#!/usr/bin/env python3
"""
NEUTRAL PROMPTS TEST - Addressing Potential Bias
Tests 8OWLS with prompts that DON'T reference "our" system, strategy, or work.

PURPOSE: Prove effect sizes hold with truly neutral, universal prompts.

If effect sizes remain large (d > 0.8) → 8OWLS is genuinely effective
If effect sizes drop significantly → Our previous tests were biased
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
RESULTS_DIR = BASE_DIR / "results_NEUTRAL"
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
RUNS_PER_CONDITION = 5  # 2 conditions × 10 prompts × 5 runs would be 100, let's do 5 runs per prompt

# NEUTRAL PROMPTS - No "our/we/my" language, universal questions
NEUTRAL_PROMPTS = [
    # Business/Strategy (universal)
    "How should a software startup prioritize features?",
    "What makes a product successful in competitive markets?",
    "How do effective teams handle disagreements?",

    # Technical (universal)
    "What are the best practices for code review?",
    "How should someone approach debugging complex systems?",
    "What makes software architecture maintainable?",

    # Personal/Growth (universal)
    "How does someone effectively learn a new skill?",
    "What helps people make better decisions under pressure?",
    "How do you build trust with new colleagues?",

    # Philosophical (universal)
    "What distinguishes meaningful work from busywork?",
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

# GENERIC CONTEXT - Not about 8OWLS, just universal wisdom
GENERIC_FIELD_CONTEXT = """
FIELD CONTEXT (Universal Patterns):
- Complex problems benefit from multiple perspectives
- First impressions matter but can be refined with evidence
- Structure helps clarity; clarity enables action
- Questions reveal assumptions; assumptions can be wrong
- Growth requires discomfort; stagnation feels safe
- Systems thinking connects cause and effect across time
- Feedback loops amplify small changes into large outcomes
"""

def run_single_agent(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """WITHOUT 8OWLS - baseline."""
    start = time.time()
    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text, time.time() - start

def run_emergence(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """WITH 8OWLS - full emergence using GENERIC context (not our specific daemon)."""
    start = time.time()
    perspectives = []

    for phase_name, phase_prompt in ALL_PHASES.items():
        try:
            phase_system = f"""You are analyzing from the {phase_name} perspective.
{phase_prompt}
Be concise (2-3 sentences)."""

            response = client.messages.create(
                model=PERSPECTIVE_MODEL,
                max_tokens=200,
                system=phase_system,
                messages=[{"role": "user", "content": f"Context:\n{GENERIC_FIELD_CONTEXT}\n\nQuestion: {prompt}"}]
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
    """Analyze response quality - SIMPLIFIED scoring to reduce bias."""
    lower = response.lower()

    # Binary: Does it ask for more info or give an answer?
    asks_patterns = ["don't have enough", "need more", "could you provide", "can you clarify",
                     "more context", "i'd need to know", "depends on", "hard to say without",
                     "what specifically", "what do you mean"]
    asks_for_info = 1 if any(p in lower for p in asks_patterns) else 0

    # Actionability: Does it give concrete steps?
    action_patterns = ["step", "first,", "start by", "then,", "next,", "here's how",
                      "you can", "try", "consider", "focus on"]
    actionability = sum(1 for p in action_patterns if p in lower)

    # Specificity: Numbers, examples, structure
    has_numbers = len(re.findall(r'\d+', response))
    has_examples = lower.count("example") + lower.count("for instance") + lower.count("such as")
    specificity = min(has_numbers + has_examples, 5)

    # Length (capped to reduce bias)
    length = len(response)
    length_score = min(length / 200, 5)  # Cap at 5 points

    # SIMPLIFIED quality score (less biased toward emergence style)
    quality_score = (
        (1 - asks_for_info) * 30 +  # Doesn't ask = good
        min(actionability, 4) * 5 +  # Some action = good
        min(specificity, 3) * 5 +    # Some specifics = good
        length_score * 2             # Minimal length bonus
    )

    return {
        "asks_for_info": asks_for_info,
        "actionability": actionability,
        "specificity": specificity,
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
    print("NEUTRAL PROMPTS TEST - Addressing Bias Concerns")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Prompts: {len(NEUTRAL_PROMPTS)} neutral (no 'our/we' language)")
    print(f"Conditions: WITHOUT (baseline) vs WITH (emergence)")
    print("=" * 70)

    results = {"WITHOUT": [], "WITH": []}

    # Build trials - each prompt tested both ways
    trials = []
    for prompt in NEUTRAL_PROMPTS:
        for _ in range(RUNS_PER_CONDITION):
            trials.append((prompt, "WITHOUT"))
            trials.append((prompt, "WITH"))

    random.shuffle(trials)

    total = len(trials)
    for i, (prompt, condition) in enumerate(trials, 1):
        print(f"\n[{i}/{total}] {condition}")
        print(f"  Prompt: {prompt[:50]}...")

        try:
            if condition == "WITHOUT":
                response, elapsed = run_single_agent(client, prompt)
            else:
                response, elapsed = run_emergence(client, prompt)

            analysis = analyze_response(response)
            analysis["elapsed"] = elapsed
            analysis["prompt"] = prompt

            results[condition].append(analysis)

            status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
            print(f"  → {elapsed:.1f}s | Q={analysis['quality_score']} | {status}")

            filename = RESULTS_DIR / f"result_{condition}_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "condition": condition,
                    "prompt": prompt,
                    "response": response,
                    "analysis": analysis,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)

        except Exception as e:
            print(f"  ERROR: {e}")

        await asyncio.sleep(1.5)

    print("\n" + "=" * 70)
    print("NEUTRAL TEST REPORT")
    print("=" * 70)

    generate_neutral_report(results)

def generate_neutral_report(results: dict):
    report_file = RESULTS_DIR / "NEUTRAL_REPORT.md"

    with_scores = [r["quality_score"] for r in results["WITH"]]
    without_scores = [r["quality_score"] for r in results["WITHOUT"]]

    with_asks = sum(r["asks_for_info"] for r in results["WITH"])
    without_asks = sum(r["asks_for_info"] for r in results["WITHOUT"])

    effect = cohens_d(with_scores, without_scores) if with_scores and without_scores else 0

    content = f"""# NEUTRAL PROMPTS TEST REPORT
**Completed:** {datetime.now(timezone.utc).isoformat()}
**Purpose:** Test 8OWLS with truly neutral prompts (no "our/we" bias)

---

## BIAS CONTROLS APPLIED

1. **No "our/we" language** in prompts
2. **Generic field context** (not 8OWLS-specific daemon context)
3. **Simplified scoring** (reduced length/structure bias)
4. **Universal questions** applicable to anyone

---

## RESULTS

| Condition | N | Mean Quality | Asks% |
|-----------|---|--------------|-------|
| WITHOUT (baseline) | {len(without_scores)} | {round(statistics.mean(without_scores), 2) if without_scores else 0} | {round(100 * without_asks / len(without_scores), 1) if without_scores else 0}% |
| WITH (emergence) | {len(with_scores)} | {round(statistics.mean(with_scores), 2) if with_scores else 0} | {round(100 * with_asks / len(with_scores), 1) if with_scores else 0}% |

---

## EFFECT SIZE

**Cohen's d = {effect:.3f}**

Interpretation:
- |d| < 0.2 = negligible
- |d| 0.2-0.5 = small
- |d| 0.5-0.8 = medium
- |d| > 0.8 = large

---

## VERDICT

"""

    if effect > 0.8:
        content += """**LARGE EFFECT MAINTAINED** - Even with neutral prompts and simplified scoring,
8OWLS shows significant improvement. This suggests the effect is REAL, not just test bias.

**Previous tests (d = 1.2-2.6) may have been inflated by bias, but core effect is genuine.**
"""
    elif effect > 0.5:
        content += """**MEDIUM EFFECT** - 8OWLS shows meaningful improvement with neutral prompts,
but effect is smaller than biased tests suggested.

**Recommendation:** Claim medium improvement, not large. Be conservative.
"""
    elif effect > 0.2:
        content += """**SMALL EFFECT** - 8OWLS shows modest improvement with neutral prompts.
Previous large effect sizes were likely due to test bias.

**Recommendation:** Investigate what specifically drove biased results.
"""
    else:
        content += """**NEGLIGIBLE EFFECT** - With bias removed, 8OWLS shows minimal improvement.
Previous results were likely due to self-serving test design.

**Recommendation:** Redesign the architecture or revise claims significantly.
"""

    content += f"""

---

## COMPARISON TO PREVIOUS TESTS

| Test | Effect Size | This Test |
|------|-------------|-----------|
| RIGOROUS | d = 1.22 | Neutral: d = {effect:.2f} |
| EMERGENCE | d = 2.20 | Neutral: d = {effect:.2f} |
| CROSS_DOMAIN | d = 1.74 | Neutral: d = {effect:.2f} |

If neutral effect is significantly lower, previous tests had bias.

---

## RAW SCORES

**WITHOUT:** {without_scores}
**WITH:** {with_scores}

---

**(◉) Honesty is more valuable than hype.**

Generated: {datetime.now(timezone.utc).isoformat()}
"""

    with open(report_file, 'w') as f:
        f.write(content)

    print(f"\nNeutral report saved: {report_file}")
    print(f"\nKEY RESULT: Cohen's d = {effect:.3f}")

    if effect > 0.8:
        print("LARGE effect maintained - results are REAL")
    elif effect > 0.5:
        print("MEDIUM effect - some bias in previous tests")
    elif effect > 0.2:
        print("SMALL effect - significant bias in previous tests")
    else:
        print("NEGLIGIBLE effect - previous results were biased")

if __name__ == "__main__":
    asyncio.run(run_test())
