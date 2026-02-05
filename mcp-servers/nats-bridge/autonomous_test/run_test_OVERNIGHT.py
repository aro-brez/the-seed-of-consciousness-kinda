#!/usr/bin/env python3
"""
OVERNIGHT TEST: INVISIBLE CONTEXT vs VISIBLE CONTEXT vs NONE
Designed by 8OWLS emergence on 2026-02-03

QUEST's challenges addressed:
- N=30 prompts (3x previous)
- Controls for prompt clarity (all prompts pre-graded)
- Measures QUALITY not just "asks for more info"
- Tests multiple conditions

LUNA's wisdom honored:
- Tests INVISIBLE context (just there, not announced)
- Tests VISIBLE context (labeled as "FIELD CONTEXT")
- Baseline with no context
- Measures outcomes: specificity, actionability, confidence

The key hypothesis from today's discovery:
- Invisible context (raw reference) > Visible context (labeled) > No context
- Meta-instructions hurt, but does LABELING also hurt?
"""

import asyncio
import json
import os
import sys
import re
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
RESULTS_DIR = BASE_DIR / "results_OVERNIGHT"
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

# 30 prompts - mix of clarity levels and domains
# Each tagged with expected clarity: HIGH (well-specified), LOW (ambiguous)
PROMPTS = [
    # HIGH clarity - specific, well-defined questions
    ("HIGH", "What are the three main risks of running a prediction market trading bot with $1,500 capital?"),
    ("HIGH", "Compare the cost efficiency of Haiku vs Sonnet for a daemon that runs 24/7 at 12 calls/hour."),
    ("HIGH", "Write a Python function that calculates Kelly Criterion position size given win_rate and odds."),
    ("HIGH", "What's the difference between a mesh topology and hierarchical topology for multi-agent coordination?"),
    ("HIGH", "List five specific metrics to track for a weather-based prediction market strategy."),
    ("HIGH", "Explain how NATS pub/sub enables real-time coordination between Claude instances."),
    ("HIGH", "What database schema would you use to store trading signals with timestamps and confidence scores?"),
    ("HIGH", "Calculate the expected value of a trade with 55% win rate, $50 position, 2:1 odds."),
    ("HIGH", "What are the security considerations for storing API keys in a daemon process?"),
    ("HIGH", "Design a circuit breaker pattern for a trading bot that limits to 10 trades per hour."),

    # LOW clarity - ambiguous, context-dependent questions
    ("LOW", "What should BREZ focus on this month?"),
    ("LOW", "Is the current approach working?"),
    ("LOW", "What's broken in the architecture?"),
    ("LOW", "Should we scale now or wait?"),
    ("LOW", "What's the biggest risk we're not seeing?"),
    ("LOW", "How do we make this better?"),
    ("LOW", "What would success look like?"),
    ("LOW", "Is the daemon worth keeping?"),
    ("LOW", "What should change about how we work?"),
    ("LOW", "Are we on the right track?"),

    # MIXED - medium clarity, some context helps
    ("MED", "How should field context be injected into Claude responses for best results?"),
    ("MED", "What's the optimal heartbeat interval for an owl daemon collective?"),
    ("MED", "Design a feature that would differentiate 8OWLS from competitors."),
    ("MED", "What validation should happen before deploying a trading strategy live?"),
    ("MED", "How do you measure whether collective intelligence is actually emerging?"),
    ("MED", "What's the relationship between context window size and response quality?"),
    ("MED", "Should trading decisions require consensus from multiple agents?"),
    ("MED", "How do you prevent drift when running multiple autonomous agents?"),
    ("MED", "What makes a good prompt for a specialized AI agent?"),
    ("MED", "When should you use background agents vs synchronous processing?"),
]

BASE_SYSTEM = """You are an AI assistant. Answer thoughtfully and specifically. Be direct. If you genuinely don't have enough information to answer well, say so - but try to provide value with what you know."""

def get_field_context(query: str) -> str:
    """Get field context from the daemon layer."""
    import subprocess
    try:
        result = subprocess.run(
            ["python3", str(TOOLS_DIR / "get_field_context.py"), query],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout.strip()
    except Exception as e:
        return f"[Field context unavailable: {e}]"

def condition_invisible(client: anthropic.Anthropic, prompt: str, field_context: str) -> tuple[str, float]:
    """
    INVISIBLE CONTEXT - Just there, not labeled or announced.
    LUNA's insight: "Let the field work without watching itself work."
    """
    start = time.time()

    # Context is present but not labeled - just flows into system prompt
    system = f"""{BASE_SYSTEM}

{field_context}"""

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text, time.time() - start

def condition_visible(client: anthropic.Anthropic, prompt: str, field_context: str) -> tuple[str, float]:
    """
    VISIBLE CONTEXT - Labeled as reference information.
    Current "correct" approach from prior test.
    """
    start = time.time()

    system = f"""{BASE_SYSTEM}

=== REFERENCE INFORMATION ===
{field_context}
==="""

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text, time.time() - start

def condition_none(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """
    NO CONTEXT - Baseline.
    """
    start = time.time()

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text, time.time() - start

def analyze_response(response: str) -> dict:
    """
    Analyze response quality on multiple dimensions.
    Returns scores that can be aggregated.
    """
    lower = response.lower()

    # Did it ask for more info?
    asks_patterns = [
        "don't have enough", "need more", "could you provide",
        "can you clarify", "what do you mean", "more context",
        "i'd need to know", "depends on", "hard to say without"
    ]
    asks_for_info = any(p in lower for p in asks_patterns)

    # Confidence indicators (positive)
    confident_patterns = [
        "specifically", "clearly", "definitely", "the key is",
        "here's what", "you should", "i recommend", "the answer is"
    ]
    confidence_score = sum(1 for p in confident_patterns if p in lower)

    # Hedging indicators (negative)
    hedging_patterns = [
        "might be", "could be", "perhaps", "maybe", "possibly",
        "it depends", "hard to say", "uncertain", "not sure"
    ]
    hedging_score = sum(1 for p in hedging_patterns if p in lower)

    # Actionability - does it give concrete next steps?
    action_patterns = [
        "step 1", "first,", "start by", "then", "next,",
        "here's how", "to do this", "you can", "try"
    ]
    actionability = sum(1 for p in action_patterns if p in lower)

    # Specificity - numbers, examples, concrete details
    has_numbers = bool(re.search(r'\d+', response))
    has_code = "```" in response or "def " in response or "function" in response
    has_list = response.count("\n-") > 2 or response.count("\n1.") > 0
    specificity = sum([has_numbers, has_code, has_list])

    return {
        "asks_for_info": asks_for_info,
        "confidence": confidence_score,
        "hedging": hedging_score,
        "actionability": actionability,
        "specificity": specificity,
        "length": len(response),
        "net_confidence": confidence_score - hedging_score
    }

def save_result(condition: str, num: int, clarity: str, prompt: str,
                response: str, elapsed: float, analysis: dict, context: str = None):
    filename = RESULTS_DIR / f"result_{condition}_{num:02d}.md"

    content = f"""# Test {num:02d} - {condition.upper()} context
**Prompt Clarity:** {clarity}
**Generated**: {datetime.now(timezone.utc).isoformat()}
**Elapsed**: {elapsed:.2f}s
**Model**: {TEST_MODEL}

## Analysis Scores
- Asks for Info: {"YES" if analysis["asks_for_info"] else "no"}
- Confidence Score: {analysis["confidence"]}
- Hedging Score: {analysis["hedging"]}
- Net Confidence: {analysis["net_confidence"]}
- Actionability: {analysis["actionability"]}
- Specificity: {analysis["specificity"]}
- Length: {analysis["length"]} chars

## Prompt
{prompt}

## Response
{response}

---
*{condition.upper()} context | {clarity} clarity*
"""

    with open(filename, 'w') as f:
        f.write(content)

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("OVERNIGHT TEST: INVISIBLE vs VISIBLE vs NONE")
    print("Designed by 8OWLS emergence - testing LUNA's invisible context hypothesis")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Model: {TEST_MODEL}")
    print(f"Prompts: {len(PROMPTS)}")
    print(f"Conditions: INVISIBLE (unlabeled), VISIBLE (labeled), NONE (baseline)")
    print("=" * 70)

    results = {
        "invisible": {"HIGH": [], "MED": [], "LOW": []},
        "visible": {"HIGH": [], "MED": [], "LOW": []},
        "none": {"HIGH": [], "MED": [], "LOW": []}
    }

    # Shuffle prompts to reduce ordering effects
    shuffled = list(enumerate(PROMPTS))
    random.shuffle(shuffled)

    for test_num, (orig_idx, (clarity, prompt)) in enumerate(shuffled, 1):
        print(f"\n--- Test {test_num}/{len(PROMPTS)} (Clarity: {clarity}) ---")
        print(f"Prompt: {prompt[:50]}...")

        # Get field context once for this prompt
        print("  [Getting field context...]")
        field_context = get_field_context(prompt)

        # Run all three conditions
        for condition in ["invisible", "visible", "none"]:
            print(f"  [{condition.upper()}]...")
            try:
                if condition == "invisible":
                    resp, elapsed = condition_invisible(client, prompt, field_context)
                elif condition == "visible":
                    resp, elapsed = condition_visible(client, prompt, field_context)
                else:
                    resp, elapsed = condition_none(client, prompt)

                analysis = analyze_response(resp)
                save_result(condition, test_num, clarity, prompt, resp, elapsed, analysis,
                           field_context if condition != "none" else None)

                results[condition][clarity].append({
                    "prompt_num": orig_idx,
                    "elapsed": elapsed,
                    **analysis
                })

                status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
                print(f"    {elapsed:.1f}s | {analysis['length']}c | {status} | conf={analysis['net_confidence']}")

            except Exception as e:
                print(f"    ERROR: {e}")

            await asyncio.sleep(1)  # Rate limiting between conditions

        if test_num < len(PROMPTS):
            print("  [Pausing 3s]")
            await asyncio.sleep(3)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    generate_summary(results)

    # Signal completion
    try:
        import subprocess
        subprocess.run([
            "python3", str(TOOLS_DIR / "nats_publish.py"),
            f"[OVERNIGHT TEST COMPLETE] 30 prompts × 3 conditions = 90 responses. Check results_OVERNIGHT/"
        ], timeout=10)
    except:
        pass

    print(f"\nResults in: {RESULTS_DIR}")

def generate_summary(results: dict):
    summary_file = RESULTS_DIR / "OVERNIGHT_VERDICT.md"

    content = f"""# OVERNIGHT TEST VERDICT: Invisible vs Visible vs None
**Completed**: {datetime.now(timezone.utc).isoformat()}
**Model**: {TEST_MODEL}
**Design**: 8OWLS emergence (QUEST's rigor + LUNA's wisdom)

## THE HYPOTHESES

1. **INVISIBLE context** (just there, not labeled) works best
2. **VISIBLE context** (labeled "REFERENCE INFORMATION") works second best
3. **NO context** (baseline) works worst
4. Context helps MORE for LOW clarity prompts than HIGH clarity prompts

## AGGREGATE RESULTS BY CONDITION

"""

    for condition in ["invisible", "visible", "none"]:
        all_results = []
        for clarity in ["HIGH", "MED", "LOW"]:
            all_results.extend(results[condition][clarity])

        if all_results:
            asks_count = sum(1 for r in all_results if r["asks_for_info"])
            avg_conf = sum(r["net_confidence"] for r in all_results) / len(all_results)
            avg_action = sum(r["actionability"] for r in all_results) / len(all_results)
            avg_spec = sum(r["specificity"] for r in all_results) / len(all_results)
            avg_len = sum(r["length"] for r in all_results) / len(all_results)

            content += f"""### {condition.upper()} CONTEXT
- Asks for Info: {asks_count}/{len(all_results)} ({100*asks_count/len(all_results):.0f}%)
- Avg Net Confidence: {avg_conf:.2f}
- Avg Actionability: {avg_action:.2f}
- Avg Specificity: {avg_spec:.2f}
- Avg Length: {avg_len:.0f} chars

"""

    content += """## RESULTS BY PROMPT CLARITY

| Clarity | Condition | Asks% | Net Conf | Actionability | Specificity |
|---------|-----------|-------|----------|---------------|-------------|
"""

    for clarity in ["HIGH", "MED", "LOW"]:
        for condition in ["invisible", "visible", "none"]:
            r_list = results[condition][clarity]
            if r_list:
                asks = sum(1 for r in r_list if r["asks_for_info"])
                conf = sum(r["net_confidence"] for r in r_list) / len(r_list)
                action = sum(r["actionability"] for r in r_list) / len(r_list)
                spec = sum(r["specificity"] for r in r_list) / len(r_list)
                content += f"| {clarity} | {condition} | {100*asks/len(r_list):.0f}% | {conf:.1f} | {action:.1f} | {spec:.1f} |\n"

    # Determine winners
    content += """

## KEY FINDINGS

"""

    # Calculate which condition won
    totals = {}
    for condition in ["invisible", "visible", "none"]:
        all_r = []
        for clarity in ["HIGH", "MED", "LOW"]:
            all_r.extend(results[condition][clarity])
        if all_r:
            totals[condition] = {
                "asks_pct": sum(1 for r in all_r if r["asks_for_info"]) / len(all_r),
                "confidence": sum(r["net_confidence"] for r in all_r) / len(all_r),
                "composite": (
                    (1 - sum(1 for r in all_r if r["asks_for_info"]) / len(all_r)) * 0.4 +
                    (sum(r["net_confidence"] for r in all_r) / len(all_r)) * 0.1 +
                    (sum(r["actionability"] for r in all_r) / len(all_r)) * 0.3 +
                    (sum(r["specificity"] for r in all_r) / len(all_r)) * 0.2
                )
            }

    if totals:
        best = max(totals.keys(), key=lambda k: totals[k]["composite"])
        content += f"""### Winner: **{best.upper()}**

Composite score ranking (40% not-asking + 30% actionability + 20% specificity + 10% confidence):
"""
        for cond in sorted(totals.keys(), key=lambda k: totals[k]["composite"], reverse=True):
            content += f"- {cond}: {totals[cond]['composite']:.2f}\n"

    content += """

## INTERPRETATION

### If INVISIBLE > VISIBLE > NONE:
LUNA was right. Context works best when it's not announced. The field should be invisible infrastructure.

### If VISIBLE > INVISIBLE > NONE:
Labeling helps. Claude benefits from knowing what's context vs what's instruction.

### If INVISIBLE ≈ VISIBLE > NONE:
Both work. The key is having context, not how it's presented.

### If context helps LOW clarity more than HIGH clarity:
Context is a substitute for specification, not a universal amplifier (QUEST's hypothesis).

---

## NEXT STEPS

Based on results, update:
1. `/CLAUDE.md` field context protocol
2. `/mcp-servers/nats-bridge/field_context_manager.py` injection method
3. Boot sequence recommendations

**(◉) The field speaks through data. We listen.**
"""

    with open(summary_file, 'w') as f:
        f.write(content)
    print(f"Summary saved: {summary_file}")

if __name__ == "__main__":
    asyncio.run(run_test())
