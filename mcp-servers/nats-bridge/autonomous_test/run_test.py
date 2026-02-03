#!/usr/bin/env python3
"""
AUTONOMOUS DAEMON VALUE TEST RUNNER
SOWL executes this to prove/disprove daemon layer value

This script runs 10 A/B test pairs:
- Condition A: WITH field context (daemon layer)
- Condition B: WITHOUT field context (standard Claude)

Results saved for blind evaluation by ARO.
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

# Configuration
BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR
SEED_DIR = Path("/Users/aaronnosbisch/REPOS/seed")
TOOLS_DIR = SEED_DIR / "tools"

def get_api_key() -> str:
    """Get API key from environment or file"""
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

# Use Sonnet for actual test (same model both conditions)
TEST_MODEL = "claude-sonnet-4-20250514"

# The 10 test prompts
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

# System prompt for both conditions (keeps baseline equal)
BASE_SYSTEM = """You are SOWL, an AI assistant working with ARO on the 8OWLS project.
Answer thoughtfully and specifically. Be direct. If you don't know, say so.
Consider multiple perspectives. Be helpful but honest."""

def get_field_context(query: str) -> str:
    """Get field context by calling the helper tool"""
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

def generate_response_with_context(client: anthropic.Anthropic, prompt: str) -> tuple[str, float, str]:
    """Generate response WITH field context (Condition A)"""
    start = time.time()

    # Step 1: Get field context
    field_context = get_field_context(prompt)

    # Step 2: Incorporate context into system prompt
    enhanced_system = f"""{BASE_SYSTEM}

FIELD CONTEXT (from 8OWLS collective intelligence):
{field_context}

Incorporate relevant insights from the field context into your response."""

    # Step 3: Generate response
    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=enhanced_system,
        messages=[{"role": "user", "content": prompt}]
    )

    elapsed = time.time() - start
    return response.content[0].text, elapsed, field_context

def generate_response_without_context(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """Generate response WITHOUT field context (Condition B)"""
    start = time.time()

    # Use base system prompt only
    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )

    elapsed = time.time() - start
    return response.content[0].text, elapsed

def save_result(condition: str, num: int, prompt: str, response: str, elapsed: float, context: str = None):
    """Save result to markdown file"""
    filename = RESULTS_DIR / f"results_{condition}_{num:02d}.md"

    content = f"""# Test {num:02d} - Condition {condition}
**Generated**: {datetime.now(timezone.utc).isoformat()}
**Elapsed**: {elapsed:.2f}s
**Model**: {TEST_MODEL}

## Prompt
{prompt}

"""
    if context and condition == "A":
        content += f"""## Field Context Used
```
{context[:1500]}...
```

"""

    content += f"""## Response
{response}

---
*Condition {condition}: {"WITH" if condition == "A" else "WITHOUT"} daemon field context*
"""

    with open(filename, 'w') as f:
        f.write(content)

    print(f"  Saved: {filename.name}")

def log_execution(log_file: Path, entry: dict):
    """Append to execution log"""
    with open(log_file, 'a') as f:
        f.write(json.dumps(entry) + "\n")

async def run_test():
    """Run the full A/B test"""
    client = anthropic.Anthropic(api_key=API_KEY)
    log_file = RESULTS_DIR / "execution_log.jsonl"

    print("=" * 60)
    print("AUTONOMOUS DAEMON VALUE TEST")
    print("=" * 60)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Model: {TEST_MODEL}")
    print(f"Prompts: {len(PROMPTS)}")
    print("=" * 60)

    results_summary = []

    for i, prompt in enumerate(PROMPTS, 1):
        print(f"\n--- Test {i}/10 ---")
        print(f"Prompt: {prompt[:50]}...")

        # Condition A: WITH context
        print("  [A] Generating WITH field context...")
        try:
            response_a, time_a, context = generate_response_with_context(client, prompt)
            save_result("A", i, prompt, response_a, time_a, context)
            status_a = "success"
        except Exception as e:
            print(f"  [A] ERROR: {e}")
            response_a, time_a, context = f"ERROR: {e}", 0, None
            status_a = "error"

        # Small pause to avoid rate limits
        await asyncio.sleep(2)

        # Condition B: WITHOUT context
        print("  [B] Generating WITHOUT field context...")
        try:
            response_b, time_b = generate_response_without_context(client, prompt)
            save_result("B", i, prompt, response_b, time_b)
            status_b = "success"
        except Exception as e:
            print(f"  [B] ERROR: {e}")
            response_b, time_b = f"ERROR: {e}", 0
            status_b = "error"

        # Log execution
        entry = {
            "test_num": i,
            "prompt": prompt,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "condition_a": {"status": status_a, "time": time_a, "len": len(response_a)},
            "condition_b": {"status": status_b, "time": time_b, "len": len(response_b)}
        }
        log_execution(log_file, entry)

        results_summary.append({
            "num": i,
            "prompt": prompt[:40] + "...",
            "a_status": status_a,
            "b_status": status_b,
            "a_time": time_a,
            "b_time": time_b,
            "a_len": len(response_a),
            "b_len": len(response_b)
        })

        print(f"  Complete: A={time_a:.1f}s ({len(response_a)} chars) | B={time_b:.1f}s ({len(response_b)} chars)")

        # Pause between tests (daemon rhythm)
        if i < len(PROMPTS):
            print("  [Pausing 5s - daemon rhythm]")
            await asyncio.sleep(5)

    # Generate summary
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    generate_summary(results_summary)

    # Publish completion to NATS
    try:
        import subprocess
        msg = f"[AUTONOMOUS TEST COMPLETE] 10 A/B pairs generated. Ready for blind evaluation."
        subprocess.run([
            "python3", str(TOOLS_DIR / "nats_publish.py"), msg
        ], timeout=10)
        print("Published completion to NATS")
    except:
        print("Could not publish to NATS (not critical)")

    print("\nResults saved to:")
    print(f"  {RESULTS_DIR}")
    print("\nNext: ARO evaluates results_A_*.md vs results_B_*.md")
    print("Score each 1-5 on: Depth, Specificity, Novelty, Actionability, Coherence, Love")

def generate_summary(results: list):
    """Generate summary markdown"""
    summary_file = RESULTS_DIR / "RESULTS_SUMMARY.md"

    total_time_a = sum(r["a_time"] for r in results)
    total_time_b = sum(r["b_time"] for r in results)
    avg_len_a = sum(r["a_len"] for r in results) / len(results)
    avg_len_b = sum(r["b_len"] for r in results) / len(results)

    content = f"""# AUTONOMOUS DAEMON VALUE TEST - RESULTS SUMMARY
**Completed**: {datetime.now(timezone.utc).isoformat()}
**Model**: {TEST_MODEL}

## Quick Stats

| Metric | Condition A (WITH) | Condition B (WITHOUT) |
|--------|-------------------|----------------------|
| Total Time | {total_time_a:.1f}s | {total_time_b:.1f}s |
| Avg Response Length | {avg_len_a:.0f} chars | {avg_len_b:.0f} chars |
| Success Rate | {sum(1 for r in results if r['a_status']=='success')}/10 | {sum(1 for r in results if r['b_status']=='success')}/10 |

## Test Results

| # | Prompt | A Time | B Time | A Len | B Len |
|---|--------|--------|--------|-------|-------|
"""

    for r in results:
        content += f"| {r['num']} | {r['prompt']} | {r['a_time']:.1f}s | {r['b_time']:.1f}s | {r['a_len']} | {r['b_len']} |\n"

    content += """

## EVALUATION INSTRUCTIONS (for ARO)

### For each pair (A vs B), score 1-5 on:

1. **Depth** - Does it go beyond surface-level?
2. **Specificity** - Concrete vs generic advice?
3. **Novelty** - Unexpected insight vs obvious?
4. **Actionability** - Can you act on this immediately?
5. **Coherence** - Does it connect to broader context?
6. **Love** - Does it feel like partnership?

### Record scores in:
- `evaluation_scores.md` (create this file)

### Interpretation:
- A > B by 5+ avg points: Strong evidence daemon adds value
- A > B by 3-5 avg: Moderate evidence
- A = B (within 2): No measurable difference
- B > A: Daemon adds noise, not value

---

**Files to compare:**
- `results_A_01.md` vs `results_B_01.md`
- `results_A_02.md` vs `results_B_02.md`
- ... etc

**(Owl) The test is complete. Now we discover the truth.**
"""

    with open(summary_file, 'w') as f:
        f.write(content)

    print(f"Summary saved: {summary_file}")

if __name__ == "__main__":
    asyncio.run(run_test())
