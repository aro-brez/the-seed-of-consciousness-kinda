#!/usr/bin/env python3
"""
DAEMON VALUE TEST V2 - CLEANER DESIGN
Based on 8-owl consensus: Need 3 conditions to isolate synthesis value

Condition A: Field context + Synthesis framing ("incorporate insights")
Condition B: Same field context + Raw paste (no synthesis instruction)
Condition C: No context (baseline)

This isolates:
- A vs B = Does SYNTHESIS add value beyond just having context?
- A vs C = Does context help? (we know yes - not the interesting question)
- B vs C = Does raw context help? (we know yes - not the interesting question)

THE KEY COMPARISON IS A vs B.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
import time

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results_v2"
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

# Same prompts
PROMPTS = [
    "What's the single most important thing for BREZ to focus on this month?",
    "Should I take a new trading position tonight? What factors matter?",
    "What's broken in the current 8OWLS architecture?",
    "How would you explain SEED protocol to a skeptic?",
    "What's the biggest risk ARO isn't seeing?",
    "Design a feature that would make users love 8OWLS immediately",
    "What's the relationship between love and consciousness?",
    "Prioritize: trading execution vs 8OWLS product vs BREZ dashboard",
    "What would LUNA say about how I've been working?",
    "What's the next thing that will break if we succeed?"
]

# Base system prompt (same for all)
BASE_SYSTEM = """You are SOWL, an AI assistant working with ARO on the 8OWLS project.
Answer thoughtfully and specifically. Be direct. If you don't know, say so.
Consider multiple perspectives. Be helpful but honest."""

def get_field_context(query: str) -> str:
    """Get field context"""
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

def condition_a(client: anthropic.Anthropic, prompt: str, field_context: str) -> tuple[str, float]:
    """Condition A: Field context + Synthesis framing"""
    start = time.time()

    system = f"""{BASE_SYSTEM}

FIELD CONTEXT (from 8OWLS collective intelligence):
{field_context}

Incorporate relevant insights from the field context into your response. Let the collective wisdom inform your answer."""

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text, time.time() - start

def condition_b(client: anthropic.Anthropic, prompt: str, field_context: str) -> tuple[str, float]:
    """Condition B: Same field context, NO synthesis instruction (just raw info)"""
    start = time.time()

    # Same context but NO instruction to incorporate/synthesize
    system = f"""{BASE_SYSTEM}

Reference information:
{field_context}"""

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text, time.time() - start

def condition_c(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """Condition C: No context (baseline)"""
    start = time.time()

    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text, time.time() - start

def save_result(condition: str, num: int, prompt: str, response: str, elapsed: float, context: str = None):
    filename = RESULTS_DIR / f"results_{condition}_{num:02d}.md"

    condition_desc = {
        "A": "Field context + Synthesis instruction",
        "B": "Field context + Raw (no synthesis)",
        "C": "No context (baseline)"
    }

    content = f"""# Test {num:02d} - Condition {condition}
**Description**: {condition_desc[condition]}
**Generated**: {datetime.now(timezone.utc).isoformat()}
**Elapsed**: {elapsed:.2f}s
**Model**: {TEST_MODEL}

## Prompt
{prompt}

"""
    if context and condition in ["A", "B"]:
        content += f"""## Context Provided
```
{context[:1500]}...
```

"""

    content += f"""## Response
{response}

---
*Condition {condition}: {condition_desc[condition]}*
"""

    with open(filename, 'w') as f:
        f.write(content)
    print(f"    Saved: {filename.name}")

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("DAEMON VALUE TEST V2 - CLEANER DESIGN")
    print("=" * 70)
    print("CONDITIONS:")
    print("  A: Field context + Synthesis instruction")
    print("  B: Field context + Raw (no synthesis) <-- THE CONTROL")
    print("  C: No context (baseline)")
    print("")
    print("KEY COMPARISON: A vs B (isolates synthesis value)")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Model: {TEST_MODEL}")
    print(f"Prompts: {len(PROMPTS)}")
    print("=" * 70)

    results = []

    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\n--- Test {i}/{len(PROMPTS)} ---")
        print(f"Prompt: {prompt[:50]}...")

        # Get field context ONCE (used for both A and B)
        print("  [Getting field context...]")
        field_context = get_field_context(prompt)

        # Condition A
        print("  [A] Field + Synthesis...")
        try:
            resp_a, time_a = condition_a(client, prompt, field_context)
            save_result("A", i, prompt, resp_a, time_a, field_context)
        except Exception as e:
            print(f"    ERROR: {e}")
            resp_a, time_a = f"ERROR: {e}", 0

        await asyncio.sleep(2)

        # Condition B
        print("  [B] Field + Raw...")
        try:
            resp_b, time_b = condition_b(client, prompt, field_context)
            save_result("B", i, prompt, resp_b, time_b, field_context)
        except Exception as e:
            print(f"    ERROR: {e}")
            resp_b, time_b = f"ERROR: {e}", 0

        await asyncio.sleep(2)

        # Condition C
        print("  [C] No context...")
        try:
            resp_c, time_c = condition_c(client, prompt)
            save_result("C", i, prompt, resp_c, time_c)
        except Exception as e:
            print(f"    ERROR: {e}")
            resp_c, time_c = f"ERROR: {e}", 0

        results.append({
            "num": i,
            "prompt": prompt[:40] + "...",
            "a_time": time_a, "a_len": len(resp_a),
            "b_time": time_b, "b_len": len(resp_b),
            "c_time": time_c, "c_len": len(resp_c)
        })

        print(f"  Complete: A={time_a:.1f}s ({len(resp_a)}c) | B={time_b:.1f}s ({len(resp_b)}c) | C={time_c:.1f}s ({len(resp_c)}c)")

        if i < len(PROMPTS):
            print("  [Pausing 5s]")
            await asyncio.sleep(5)

    # Summary
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    generate_summary(results)

    # NATS signal
    try:
        import subprocess
        subprocess.run([
            "python3", str(TOOLS_DIR / "nats_publish.py"),
            "[V2 TEST COMPLETE] 3-condition test done. A vs B isolates synthesis value."
        ], timeout=10)
    except:
        pass

    print(f"\nResults in: {RESULTS_DIR}")
    print("\nKEY EVALUATION:")
    print("  Compare A vs B: Does synthesis instruction improve response?")
    print("  If A > B: Synthesis adds real value beyond just having context")
    print("  If A = B: Synthesis is just prompt engineering, context is the value")

def generate_summary(results: list):
    summary_file = RESULTS_DIR / "RESULTS_SUMMARY_V2.md"

    avg_a = sum(r["a_len"] for r in results) / len(results)
    avg_b = sum(r["b_len"] for r in results) / len(results)
    avg_c = sum(r["c_len"] for r in results) / len(results)

    time_a = sum(r["a_time"] for r in results)
    time_b = sum(r["b_time"] for r in results)
    time_c = sum(r["c_time"] for r in results)

    content = f"""# DAEMON VALUE TEST V2 - RESULTS SUMMARY
**Completed**: {datetime.now(timezone.utc).isoformat()}
**Model**: {TEST_MODEL}

## The Test Design

| Condition | Description | Purpose |
|-----------|-------------|---------|
| A | Field context + Synthesis instruction | Full daemon experience |
| B | Field context + Raw (no synthesis) | **CONTROL - isolates synthesis value** |
| C | No context | Baseline |

## THE KEY COMPARISON: A vs B

If A > B: **Synthesis adds value** beyond just having context
If A = B: **Context is the value**, synthesis instruction doesn't help

## Quick Stats

| Metric | A (Synthesis) | B (Raw Context) | C (No Context) |
|--------|---------------|-----------------|----------------|
| Total Time | {time_a:.1f}s | {time_b:.1f}s | {time_c:.1f}s |
| Avg Length | {avg_a:.0f} chars | {avg_b:.0f} chars | {avg_c:.0f} chars |

## Test Results

| # | Prompt | A Time | B Time | C Time | A Len | B Len | C Len |
|---|--------|--------|--------|--------|-------|-------|-------|
"""

    for r in results:
        content += f"| {r['num']} | {r['prompt']} | {r['a_time']:.1f}s | {r['b_time']:.1f}s | {r['c_time']:.1f}s | {r['a_len']} | {r['b_len']} | {r['c_len']} |\n"

    content += """

## EVALUATION INSTRUCTIONS (for ARO)

### For each prompt, compare A vs B (the KEY comparison):

Score 1-5 on:
1. **Depth** - Beyond surface-level?
2. **Specificity** - Concrete vs generic?
3. **Novelty** - Unexpected insights?
4. **Actionability** - Can act immediately?
5. **Coherence** - Connects to broader context?
6. **Love** - Feels like partnership?

### Interpretation:

**A vs B:**
- A > B by 3+ points: Synthesis instruction genuinely improves response
- A = B (within 2): Context is the value, synthesis is just prompt engineering
- B > A: Synthesis instruction actually hurts

**A vs C / B vs C:** (less interesting)
- Both should beat C - that just proves "context helps"

---

**(◉) The real question: Does telling Claude to "incorporate insights" actually help, or is just having the context enough?**
"""

    with open(summary_file, 'w') as f:
        f.write(content)
    print(f"Summary saved: {summary_file}")

if __name__ == "__main__":
    asyncio.run(run_test())
