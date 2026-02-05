#!/usr/bin/env python3
"""
FINAL DEFINITIVE DAEMON VALUE TEST
Based on 8-owl consensus: Synthesis instruction HURTS. Raw context HELPS.

ONLY TWO CONDITIONS:
- B: Field context (raw, no synthesis instruction)
- C: No context (baseline)

This proves: Does the daemon's field context improve responses?
If B > C: Daemon provides value. Ship it.
If B = C: Context doesn't help. Kill it.

NO synthesis instruction. Just raw context vs none.
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
RESULTS_DIR = BASE_DIR / "results_FINAL"
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

BASE_SYSTEM = """You are SOWL, an AI assistant working with ARO on the 8OWLS project.
Answer thoughtfully and specifically. Be direct. If you don't know, say so.
Consider multiple perspectives. Be helpful but honest."""

def get_field_context(query: str) -> str:
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

def condition_with_context(client: anthropic.Anthropic, prompt: str, field_context: str) -> tuple[str, float]:
    """WITH field context (raw, no synthesis instruction)"""
    start = time.time()

    # RAW CONTEXT - NO "incorporate" instruction
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

def condition_without_context(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """WITHOUT context (baseline)"""
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

    desc = "WITH field context (raw)" if condition == "WITH" else "WITHOUT context (baseline)"

    content = f"""# Test {num:02d} - {desc}
**Generated**: {datetime.now(timezone.utc).isoformat()}
**Elapsed**: {elapsed:.2f}s
**Model**: {TEST_MODEL}

## Prompt
{prompt}

"""
    if context and condition == "WITH":
        content += f"""## Context Provided
```
{context[:2000]}
```

"""

    content += f"""## Response
{response}

---
*{desc}*
"""

    with open(filename, 'w') as f:
        f.write(content)
    print(f"    Saved: {filename.name}")

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("FINAL DEFINITIVE DAEMON VALUE TEST")
    print("=" * 70)
    print("QUESTION: Does field context improve responses?")
    print("")
    print("CONDITIONS:")
    print("  WITH: Field context (raw, NO synthesis instruction)")
    print("  WITHOUT: No context (baseline)")
    print("")
    print("If WITH > WITHOUT: Daemon provides value. Ship it.")
    print("If WITH = WITHOUT: Context doesn't help. Kill it.")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Model: {TEST_MODEL}")
    print(f"Prompts: {len(PROMPTS)}")
    print("=" * 70)

    results = []

    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\n--- Test {i}/{len(PROMPTS)} ---")
        print(f"Prompt: {prompt[:50]}...")

        # Get field context
        print("  [Getting field context...]")
        field_context = get_field_context(prompt)

        # WITH context
        print("  [WITH] Field context (raw)...")
        try:
            resp_with, time_with = condition_with_context(client, prompt, field_context)
            save_result("WITH", i, prompt, resp_with, time_with, field_context)
        except Exception as e:
            print(f"    ERROR: {e}")
            resp_with, time_with = f"ERROR: {e}", 0

        await asyncio.sleep(2)

        # WITHOUT context
        print("  [WITHOUT] Baseline...")
        try:
            resp_without, time_without = condition_without_context(client, prompt)
            save_result("WITHOUT", i, prompt, resp_without, time_without)
        except Exception as e:
            print(f"    ERROR: {e}")
            resp_without, time_without = f"ERROR: {e}", 0

        # Quick quality check
        with_asks = "don't have" in resp_with.lower() or "need more" in resp_with.lower() or "could you provide" in resp_with.lower()
        without_asks = "don't have" in resp_without.lower() or "need more" in resp_without.lower() or "could you provide" in resp_without.lower()

        results.append({
            "num": i,
            "prompt": prompt[:40] + "...",
            "with_time": time_with,
            "with_len": len(resp_with),
            "with_asks_for_more": with_asks,
            "without_time": time_without,
            "without_len": len(resp_without),
            "without_asks_for_more": without_asks
        })

        status_with = "ASKS" if with_asks else "ANSWERS"
        status_without = "ASKS" if without_asks else "ANSWERS"
        print(f"  Complete: WITH={time_with:.1f}s ({len(resp_with)}c, {status_with}) | WITHOUT={time_without:.1f}s ({len(resp_without)}c, {status_without})")

        if i < len(PROMPTS):
            print("  [Pausing 5s]")
            await asyncio.sleep(5)

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    generate_summary(results)

    # NATS
    try:
        import subprocess
        subprocess.run([
            "python3", str(TOOLS_DIR / "nats_publish.py"),
            f"[FINAL TEST COMPLETE] {len(PROMPTS)} prompts. WITH context vs WITHOUT. Check results_FINAL/"
        ], timeout=10)
    except:
        pass

    print(f"\nResults in: {RESULTS_DIR}")

def generate_summary(results: list):
    summary_file = RESULTS_DIR / "FINAL_VERDICT.md"

    avg_with = sum(r["with_len"] for r in results) / len(results)
    avg_without = sum(r["without_len"] for r in results) / len(results)

    time_with = sum(r["with_time"] for r in results)
    time_without = sum(r["without_time"] for r in results)

    with_asks_count = sum(1 for r in results if r["with_asks_for_more"])
    without_asks_count = sum(1 for r in results if r["without_asks_for_more"])

    content = f"""# FINAL DEFINITIVE DAEMON VALUE TEST - VERDICT
**Completed**: {datetime.now(timezone.utc).isoformat()}
**Model**: {TEST_MODEL}

## THE QUESTION
Does field context improve responses?

## THE DESIGN
| Condition | Description |
|-----------|-------------|
| WITH | Field context (raw, NO synthesis instruction) |
| WITHOUT | No context (baseline) |

## QUICK VERDICT

| Metric | WITH Context | WITHOUT Context | Winner |
|--------|--------------|-----------------|--------|
| Avg Length | {avg_with:.0f} chars | {avg_without:.0f} chars | {"WITH" if avg_with > avg_without else "WITHOUT" if avg_without > avg_with else "TIE"} |
| Total Time | {time_with:.1f}s | {time_without:.1f}s | {"WITHOUT (faster)" if time_without < time_with else "WITH"} |
| Asks for More Info | {with_asks_count}/10 | {without_asks_count}/10 | {"WITH" if with_asks_count < without_asks_count else "WITHOUT" if without_asks_count < with_asks_count else "TIE"} |

## KEY METRIC: "Asks for More Info"
This measures whether the response says "I don't have enough information" or "Could you provide more context?"

- **If WITH asks less than WITHOUT:** Field context helps Claude answer instead of ask
- **If both ask equally:** Field context doesn't help
- **If WITH asks MORE than WITHOUT:** Something is wrong

## RESULTS BY PROMPT

| # | Prompt | WITH | WITHOUT | WITH Asks? | WITHOUT Asks? |
|---|--------|------|---------|------------|---------------|
"""

    for r in results:
        with_status = "YES" if r["with_asks_for_more"] else "no"
        without_status = "YES" if r["without_asks_for_more"] else "no"
        content += f"| {r['num']} | {r['prompt']} | {r['with_len']}c | {r['without_len']}c | {with_status} | {without_status} |\n"

    # Calculate verdict
    if with_asks_count < without_asks_count and avg_with > avg_without:
        verdict = "DAEMON PROVIDES VALUE"
        explanation = "Field context helps Claude give substantive answers instead of asking for more info."
    elif with_asks_count >= without_asks_count:
        verdict = "INCONCLUSIVE OR NO VALUE"
        explanation = "Field context doesn't reduce the 'asks for more info' pattern."
    else:
        verdict = "PARTIAL VALUE"
        explanation = "Some improvement but not decisive."

    content += f"""

## FINAL VERDICT

### **{verdict}**

{explanation}

---

## INTERPRETATION FOR ARŌ

**If "Asks for More Info" is lower for WITH:**
- The daemon's field context is doing its job
- Claude can answer because it has the context it needs
- SHIP IT

**If "Asks for More Info" is similar or higher for WITH:**
- The field context isn't helping Claude answer
- Either the context is wrong, or the approach needs rethinking
- INVESTIGATE

---

## NEXT STEPS

1. Read `results_WITH_*.md` vs `results_WITHOUT_*.md` for each prompt
2. Score each pair on: Depth, Specificity, Actionability, Love
3. If WITH consistently better: Daemon validated
4. If similar: Context approach needs work

**(◉) The test is complete. Truth has been measured.**
"""

    with open(summary_file, 'w') as f:
        f.write(content)
    print(f"Summary saved: {summary_file}")

if __name__ == "__main__":
    asyncio.run(run_test())
