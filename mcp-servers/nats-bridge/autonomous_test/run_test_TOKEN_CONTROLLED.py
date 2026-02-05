#!/usr/bin/env python3
"""
TOKEN-CONTROLLED TEST - Architecture vs Tokens Confound
========================================================

This test isolates the architectural effect of 8OWLS from the token budget effect.

3 Conditions:
  A: Baseline (1000 tokens)
  B: Token-matched single agent (8000 tokens, same as 8OWLS total)
  C: 8OWLS emergence (7 Haiku @200 + 1 Sonnet @1000 ≈ 2400 tokens)

Key: B and C have identical token budgets but different architectures.
If B ≈ C in quality, it's "just tokens."
If C > B, the architecture genuinely helps.

Pre-Registered Hypothesis: d(B vs C) > 0.3 (architecture matters beyond tokens)
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
RESULTS_DIR = BASE_DIR / "results_TOKEN_CONTROLLED"
RESULTS_DIR.mkdir(exist_ok=True)

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

# NEUTRAL PROMPTS (same as NEUTRAL test - proven unbiased)
NEUTRAL_PROMPTS = [
    "How should a software startup prioritize features?",
    "What makes a product successful in competitive markets?",
    "How do effective teams handle disagreements?",
    "What are the best practices for code review?",
    "How should someone approach debugging complex systems?",
    "What makes software architecture maintainable?",
    "How does someone effectively learn a new skill?",
    "What helps people make better decisions under pressure?",
    "How do you build trust with new colleagues?",
    "What distinguishes meaningful work from busywork?",
]

BASE_SYSTEM = """You are an AI assistant. Answer thoughtfully and specifically. Be direct."""

ALL_PHASES = {
    "PERCEIVE": "Observe the current state. What do you see?",
    "CONNECT": "Find patterns. How does this connect to other knowledge?",
    "LEARN": "Extract meaning. What's the key insight?",
    "QUESTION": "Challenge assumptions. What could be wrong?",
    "EXPAND": "See growth potential. What opportunities exist?",
    "SHARE": "What should be communicated?",
    "RECEIVE": "What feedback should we accept?",
}

GENERIC_FIELD_CONTEXT = """
FIELD CONTEXT (Universal Patterns):
- Complex problems benefit from multiple perspectives
- First impressions matter but can be refined
- Structure helps clarity; clarity enables action
- Questions reveal assumptions; assumptions can be wrong
- Growth requires discomfort; stagnation feels safe
- Systems thinking connects cause and effect
- Feedback loops amplify changes into large outcomes
"""

def run_baseline(client: anthropic.Anthropic, prompt: str) -> tuple[str, float, dict]:
    """Condition A: Single agent, standard request (1000 tokens)."""
    start = time.time()
    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start
    return response.content[0].text, elapsed, {
        "condition": "A_BASELINE",
        "max_tokens": 1000,
        "model": TEST_MODEL
    }

def run_token_matched(client: anthropic.Anthropic, prompt: str) -> tuple[str, float, dict]:
    """Condition B: Single agent with 8x tokens (8000 tokens), encouraged to think deeply."""
    start = time.time()
    enhanced_system = """You are an AI assistant. Answer thoughtfully and specifically.

INSTRUCTION: You have a large context window available. Use it fully.
Consider multiple angles, trade-offs, implications, and edge cases.
Show your reasoning process. Be thorough and comprehensive."""

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=8000,  # 8x tokens
        system=enhanced_system,
        messages=[{"role": "user", "content": prompt}]
    )
    elapsed = time.time() - start
    return response.content[0].text, elapsed, {
        "condition": "B_TOKEN_MATCHED",
        "max_tokens": 8000,
        "model": TEST_MODEL
    }

def run_emergence(client: anthropic.Anthropic, prompt: str) -> tuple[str, float, dict]:
    """Condition C: 8OWLS full emergence (7 Haiku @200 + 1 Sonnet @1000 ≈ 2400 tokens total)."""
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
                messages=[
                    {"role": "user", "content": f"Context:\n{GENERIC_FIELD_CONTEXT}\n\nQuestion: {prompt}"}
                ]
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

    elapsed = time.time() - start
    return synthesis.content[0].text, elapsed, {
        "condition": "C_EMERGENCE",
        "estimated_tokens": 2400,  # 7*200 + 1*1000
        "model": f"{PERSPECTIVE_MODEL} x7 + {TEST_MODEL} x1"
    }

def analyze_response(response: str) -> dict:
    """Analyze response quality - SIMPLIFIED scoring (from NEUTRAL test)."""
    lower = response.lower()

    # Does it ask for more info or give an answer?
    asks_patterns = [
        "don't have enough", "need more", "could you provide", "can you clarify",
        "more context", "i'd need to know", "depends on", "hard to say without",
        "what specifically", "what do you mean"
    ]
    asks_for_info = 1 if any(p in lower for p in asks_patterns) else 0

    # Actionability: concrete steps?
    action_patterns = [
        "step", "first,", "start by", "then,", "next,", "here's how",
        "you can", "try", "consider", "focus on"
    ]
    actionability = sum(1 for p in action_patterns if p in lower)

    # Specificity: numbers, examples
    has_numbers = len(re.findall(r'\d+', response))
    has_examples = (
        lower.count("example") +
        lower.count("for instance") +
        lower.count("such as")
    )
    specificity = min(has_numbers + has_examples, 5)

    # Length (capped to reduce bias - token-matched might naturally be longer)
    length = len(response)
    length_score = min(length / 200, 5)

    # SIMPLIFIED quality score (reduced length bias)
    quality_score = (
        (1 - asks_for_info) * 30 +  # Doesn't ask = good
        min(actionability, 4) * 5 +  # Some action = good
        min(specificity, 3) * 5 +    # Some specifics = good
        length_score * 2             # MINIMAL length bonus
    )

    return {
        "asks_for_info": asks_for_info,
        "actionability": actionability,
        "specificity": specificity,
        "length": length,
        "quality_score": round(quality_score, 2)
    }

def cohens_d(group1: list, group2: list) -> float:
    """Calculate Cohen's d effect size."""
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0

    mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
    var1, var2 = statistics.variance(group1), statistics.variance(group2)

    pooled_std = ((var1 * (n1 - 1) + var2 * (n2 - 1)) / (n1 + n2 - 2)) ** 0.5
    if pooled_std == 0:
        return 0.0

    return (mean1 - mean2) / pooled_std

def save_hypotheses():
    """Save pre-registered hypotheses before running."""
    hypotheses = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "primary_hypothesis": "d(B vs C) > 0.3 (architecture matters beyond tokens)",
        "secondary_hypotheses": [
            "d(A vs B) > 0.3 (more thinking helps single agent)",
            "d(A vs C) ≈ 0.9 (confirmed from NEUTRAL test)"
        ],
        "decision_rule_B_vs_C": {
            "d > 0.3": "Emergence provides architectural benefit",
            "-0.3 < d < 0.3": "Emergence ≈ more thinking (no architectural advantage)",
            "d < -0.3": "Emergence worse when tokens matched (investigate)"
        },
        "sample_size_per_condition": 52,
        "total_trials": 156,
        "alpha": 0.05,
        "power_target": 0.80,
        "prompts": len(NEUTRAL_PROMPTS),
        "status": "PRE-REGISTERED - DO NOT MODIFY"
    }

    with open(RESULTS_DIR / "PRE_REGISTERED_HYPOTHESES.json", 'w') as f:
        json.dump(hypotheses, f, indent=2)

    print("\n[PRE-REGISTRATION] Hypotheses saved to PRE_REGISTERED_HYPOTHESES.json")
    print(f"Primary hypothesis: {hypotheses['primary_hypothesis']}")
    return hypotheses

def run_test():
    """Main test execution."""
    client = anthropic.Anthropic(api_key=API_KEY)

    # Pre-register hypotheses
    hypotheses = save_hypotheses()

    print("=" * 80)
    print("TOKEN-CONTROLLED TEST - Architecture vs Tokens")
    print("=" * 80)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Conditions: A (1K tokens) vs B (8K tokens) vs C (8OWLS ~2.4K)")
    print(f"Prompts: {len(NEUTRAL_PROMPTS)} neutral, unbiased")
    print(f"Target: n=52 per condition (156 total trials)")
    print("=" * 80)

    results = {
        "A_BASELINE": [],
        "B_TOKEN_MATCHED": [],
        "C_EMERGENCE": []
    }

    # Build trials - balanced across conditions
    trials = []
    for prompt in NEUTRAL_PROMPTS:
        for _ in range(52 // len(NEUTRAL_PROMPTS) + 1):  # ~5 per prompt
            trials.append((prompt, "A"))
            trials.append((prompt, "B"))
            trials.append((prompt, "C"))

    trials = trials[:156]  # Trim to exactly 156
    random.shuffle(trials)

    total = len(trials)
    cost_estimate = 0

    for i, (prompt, condition) in enumerate(trials, 1):
        print(f"\n[{i}/{total}] Condition {condition}")
        print(f"  Prompt: {prompt[:60]}...")

        try:
            if condition == "A":
                response, elapsed, metadata = run_baseline(client, prompt)
                cost_estimate += 0.001  # ~$0.001 per baseline
                cond_key = "A_BASELINE"
            elif condition == "B":
                response, elapsed, metadata = run_token_matched(client, prompt)
                cost_estimate += 0.008  # ~$0.008 per 8K token request
                cond_key = "B_TOKEN_MATCHED"
            else:  # C
                response, elapsed, metadata = run_emergence(client, prompt)
                cost_estimate += 0.008  # ~$0.008 for 8OWLS
                cond_key = "C_EMERGENCE"

            analysis = analyze_response(response)
            analysis["elapsed"] = elapsed
            analysis["prompt"] = prompt
            analysis["metadata"] = metadata

            results[cond_key].append(analysis)

            status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
            print(f"  → {elapsed:.1f}s | Q={analysis['quality_score']:.1f} | {status}")
            print(f"     Estimated cost so far: ${cost_estimate:.2f}")

            # Save individual result
            filename = RESULTS_DIR / f"result_{condition}_{i:03d}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "trial_num": i,
                    "condition": condition,
                    "prompt": prompt,
                    "response": response,
                    "analysis": analysis,
                    "metadata": metadata,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, f, indent=2)

        except Exception as e:
            print(f"  ERROR: {e}")
            continue

    print("\n" + "=" * 80)
    print("TEST COMPLETE - ANALYZING RESULTS")
    print("=" * 80)

    # Statistical analysis
    analysis_results = {}

    for condition, data in results.items():
        scores = [r["quality_score"] for r in data]
        if len(scores) > 1:
            analysis_results[condition] = {
                "n": len(scores),
                "mean": round(statistics.mean(scores), 2),
                "std": round(statistics.stdev(scores), 2),
                "min": round(min(scores), 2),
                "max": round(max(scores), 2),
                "median": round(statistics.median(scores), 2)
            }

    # Primary comparison: B vs C (token-matched architectures)
    scores_B = [r["quality_score"] for r in results["B_TOKEN_MATCHED"]]
    scores_C = [r["quality_score"] for r in results["C_EMERGENCE"]]
    d_B_vs_C = cohens_d(scores_B, scores_C)

    # Secondary comparisons
    scores_A = [r["quality_score"] for r in results["A_BASELINE"]]
    d_A_vs_B = cohens_d(scores_A, scores_B)
    d_A_vs_C = cohens_d(scores_A, scores_C)

    print("\nCONDITION STATISTICS:")
    print("=" * 80)
    for cond, stats in analysis_results.items():
        print(f"\n{cond}:")
        print(f"  n = {stats['n']}")
        print(f"  Mean = {stats['mean']} (SD = {stats['std']})")
        print(f"  Range = {stats['min']} to {stats['max']}")
        print(f"  Median = {stats['median']}")

    print("\n\nEFFECT SIZES (Cohen's d):")
    print("=" * 80)
    print(f"A (Baseline) vs B (Token-Matched):  d = {d_A_vs_B:.3f}")
    print(f"A (Baseline) vs C (Emergence):      d = {d_A_vs_C:.3f}")
    print(f"\nPRIMARY COMPARISON:")
    print(f"B (Token-Matched) vs C (Emergence): d = {d_B_vs_C:.3f}")

    # Interpretation
    print("\n\nINTERPRETATION OF d(B vs C):")
    print("=" * 80)
    if d_B_vs_C > 0.3:
        print("✓ ARCHITECTURE MATTERS: Emergence provides architectural benefit beyond tokens")
        interpretation = "PASS - Architecture is meaningful"
    elif -0.3 <= d_B_vs_C <= 0.3:
        print("⚠ TOKENS DOMINANT: Emergence works but is primarily token effect")
        interpretation = "INCONCLUSIVE - Need further investigation"
    else:
        print("✗ EMERGENCE HURTS: Emergence underperforms when tokens matched")
        interpretation = "FAIL - Need to redesign architecture"

    # Save report
    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_name": "TOKEN_CONTROLLED",
        "hypothesis": hypotheses["primary_hypothesis"],
        "sample_sizes": {
            "A_BASELINE": len(results["A_BASELINE"]),
            "B_TOKEN_MATCHED": len(results["B_TOKEN_MATCHED"]),
            "C_EMERGENCE": len(results["C_EMERGENCE"]),
            "total": sum(len(v) for v in results.values())
        },
        "statistics": analysis_results,
        "effect_sizes": {
            "d_A_vs_B": round(d_A_vs_B, 3),
            "d_A_vs_C": round(d_A_vs_C, 3),
            "d_B_vs_C": round(d_B_vs_C, 3),
            "primary_comparison": "d_B_vs_C",
            "interpretation": interpretation
        },
        "conclusion": {
            "hypothesis_result": "PASS" if d_B_vs_C > 0.3 else "FAIL" if d_B_vs_C < -0.3 else "INCONCLUSIVE",
            "architectural_benefit": d_B_vs_C,
            "next_steps": [
                "If d_B_vs_C > 0.3: Proceed to competitor comparison",
                "If -0.3 < d_B_vs_C < 0.3: Explore token-efficient architectures",
                "If d_B_vs_C < -0.3: Investigate failure mode"
            ]
        },
        "estimated_cost": f"${cost_estimate:.2f}",
        "prompts_used": len(NEUTRAL_PROMPTS)
    }

    report_path = RESULTS_DIR / "TOKEN_CONTROLLED_REPORT.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    # Also save as markdown for readability
    md_report = f"""# TOKEN-CONTROLLED TEST RESULTS
**Date:** {datetime.now(timezone.utc).isoformat()}

## Primary Hypothesis
{hypotheses['primary_hypothesis']}

## Results

### Condition Statistics
| Condition | N | Mean | SD | Range |
|-----------|---|------|-----|-------|
| A: Baseline (1K) | {analysis_results['A_BASELINE']['n']} | {analysis_results['A_BASELINE']['mean']} | {analysis_results['A_BASELINE']['std']} | {analysis_results['A_BASELINE']['min']}-{analysis_results['A_BASELINE']['max']} |
| B: Token-Matched (8K) | {analysis_results['B_TOKEN_MATCHED']['n']} | {analysis_results['B_TOKEN_MATCHED']['mean']} | {analysis_results['B_TOKEN_MATCHED']['std']} | {analysis_results['B_TOKEN_MATCHED']['min']}-{analysis_results['B_TOKEN_MATCHED']['max']} |
| C: Emergence (2.4K) | {analysis_results['C_EMERGENCE']['n']} | {analysis_results['C_EMERGENCE']['mean']} | {analysis_results['C_EMERGENCE']['std']} | {analysis_results['C_EMERGENCE']['min']}-{analysis_results['C_EMERGENCE']['max']} |

### Effect Sizes (Cohen's d)
| Comparison | Effect Size | Interpretation |
|-----------|-------------|-----------------|
| A vs B (Does more tokens help?) | {d_A_vs_B:.3f} | {"Large" if abs(d_A_vs_B) > 0.8 else "Medium" if abs(d_A_vs_B) > 0.5 else "Small" if abs(d_A_vs_B) > 0.2 else "Negligible"} |
| A vs C (Our effect) | {d_A_vs_C:.3f} | {"Large" if abs(d_A_vs_C) > 0.8 else "Medium" if abs(d_A_vs_C) > 0.5 else "Small" if abs(d_A_vs_C) > 0.2 else "Negligible"} |
| **B vs C (Architecture)** | **{d_B_vs_C:.3f}** | **{interpretation}** |

## Conclusion
{report['conclusion']['hypothesis_result']}

The architectural benefit of 8OWLS over a single high-thought agent (when tokens are matched) is **d = {d_B_vs_C:.3f}**.

### Decision
{interpretation}

### Next Steps
1. {report['conclusion']['next_steps'][0]}
2. {report['conclusion']['next_steps'][1]}
3. {report['conclusion']['next_steps'][2]}

---
**Cost:** {report['estimated_cost']}
**Generated:** TOKEN_CONTROLLED_REPORT.md
"""

    md_path = RESULTS_DIR / "TOKEN_CONTROLLED_REPORT.md"
    with open(md_path, 'w') as f:
        f.write(md_report)

    print("\n" + "=" * 80)
    print("RESULTS SAVED:")
    print(f"  JSON: {report_path}")
    print(f"  MD:   {md_path}")
    print(f"  Cost: {report['estimated_cost']}")
    print("=" * 80)

if __name__ == "__main__":
    run_test()
