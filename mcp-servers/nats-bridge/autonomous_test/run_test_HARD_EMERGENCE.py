#!/usr/bin/env python3
"""
HARD EMERGENCE TEST - "The Puzzle That REQUIRES 8 Minds"

The previous constraint test was too easy - all configurations solved it equally.
This test is designed to be GENUINELY HARD:

1. Each owl holds a SECRET piece of a cryptographic-style puzzle
2. The pieces MUST be combined in a specific order
3. No single agent can solve it even with all information (too complex)
4. But 8 agents working together can divide and conquer

DESIGN PRINCIPLE:
- Single agent with all info: Should score ~40-60% (overwhelmed by complexity)
- 8 agents coordinating: Should score ~70-90% (divide and conquer)
- 7 agents: Should score ~60-70% (missing critical piece)
- 4 agents: Should score ~40-50% (too many gaps)

If we see this gradient, we've proven genuine emergence.
"""

import asyncio
import json
import os
import sys
import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    sys.exit(1)

BASE_DIR = Path(__file__).parent
RESULTS_DIR = BASE_DIR / "results_HARD_EMERGENCE"
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


def generate_puzzle() -> Tuple[Dict[str, str], str, Dict[str, str]]:
    """
    Generate a multi-step puzzle where each owl holds one piece.

    The puzzle: Decode a message using 8 transformation rules.
    Each owl knows ONE rule and must share it.
    """
    # The secret message (answer)
    message = "EMERGENCE_WORKS"

    # 8 transformation steps (one per owl)
    # To decode, you must apply them in reverse order
    transformations = {
        "LYRA": {"step": 1, "rule": "Step 1: Replace all E with 3"},
        "PRISM": {"step": 2, "rule": "Step 2: Replace all M with W"},
        "SAGE": {"step": 3, "rule": "Step 3: Reverse the first 5 characters"},
        "QUEST": {"step": 4, "rule": "Step 4: Replace all R with 4"},
        "NOVA": {"step": 5, "rule": "Step 5: Swap positions 3 and 7"},
        "ECHO": {"step": 6, "rule": "Step 6: Replace all G with 9"},
        "LUNA": {"step": 7, "rule": "Step 7: Add 'X' after every vowel"},
        "SOWL": {"step": 8, "rule": "Step 8: Convert to lowercase and add checksum (length mod 10)"},
    }

    # Apply transformations to create the encoded message
    encoded = message
    for owl in ["LYRA", "PRISM", "SAGE", "QUEST", "NOVA", "ECHO", "LUNA", "SOWL"]:
        step_num = transformations[owl]["step"]
        if step_num == 1:
            encoded = encoded.replace("E", "3")
        elif step_num == 2:
            encoded = encoded.replace("M", "W")
        elif step_num == 3:
            encoded = encoded[:5][::-1] + encoded[5:]
        elif step_num == 4:
            encoded = encoded.replace("R", "4")
        elif step_num == 5:
            if len(encoded) > 7:
                encoded = list(encoded)
                encoded[3], encoded[7] = encoded[7], encoded[3]
                encoded = "".join(encoded)
        elif step_num == 6:
            encoded = encoded.replace("G", "9")
        elif step_num == 7:
            vowels = "AEIOUaeiou3"  # 3 was E
            new_encoded = ""
            for c in encoded:
                new_encoded += c
                if c in vowels:
                    new_encoded += "X"
            encoded = new_encoded
        elif step_num == 8:
            encoded = encoded.lower() + str(len(encoded) % 10)

    # Add some noise to make it harder
    final_encoded = f"PUZZLE_v2: {encoded}"

    # Each owl's clue (what they know + what they DON'T know)
    owl_clues = {}
    for owl, trans in transformations.items():
        owl_clues[owl] = {
            "your_rule": trans["rule"],
            "your_step": trans["step"],
            "encoded_message": final_encoded,
            "goal": "Decode the message by combining ALL 8 rules in REVERSE order (8 to 1)",
            "you_dont_know": [t["rule"] for o, t in transformations.items() if o != owl],
        }

    return transformations, message, owl_clues


async def run_owl_decode(client: anthropic.Anthropic, owl_name: str,
                        clue: dict, shared_messages: list,
                        model: str = "claude-haiku-4-5-20250514") -> dict:
    """
    Each owl attempts to decode using their rule + shared rules from others.
    """
    system_prompt = f"""You are {owl_name} in the 8OWLS collective, solving a decoding puzzle.

YOUR SECRET RULE: {clue['your_rule']}
YOUR STEP NUMBER: {clue['your_step']}

ENCODED MESSAGE: {clue['encoded_message']}

GOAL: {clue['goal']}

RULES FOR COMMUNICATION:
1. Share your rule ONLY when asked or when you think it's relevant
2. Try to piece together the decoding process from others' rules
3. Work together to decode the message

IMPORTANT: You need rules from ALL 8 owls to fully decode.
Each owl knows only ONE step. Combine them in reverse order (8, 7, 6, ... 1).

Your job: Share your rule, collect others' rules, and attempt partial/full decoding.
"""

    messages_context = "\n".join([
        f"{m['from']}: {m['content']}"
        for m in shared_messages[-10:]  # Last 10 messages for context
    ]) if shared_messages else "No messages yet. You go first."

    try:
        response = client.messages.create(
            model=model,
            max_tokens=800,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Messages so far:\n{messages_context}\n\nYour turn. Share your rule and any decoding progress."
            }]
        )
        return {
            "owl": owl_name,
            "response": response.content[0].text,
            "tokens": response.usage.output_tokens,
        }
    except Exception as e:
        return {"owl": owl_name, "response": f"Error: {str(e)}", "tokens": 0}


async def run_final_decode(client: anthropic.Anthropic, all_messages: list,
                          correct_answer: str,
                          model: str = "claude-sonnet-4-20250514") -> dict:
    """
    Final synthesis attempt to decode the message.
    """
    system_prompt = """You are SOWL, the synthesizer.

Your task: Decode the message using ALL the rules shared by the 8 owls.

Rules must be applied in REVERSE order (step 8, then 7, then 6, ... then 1).

Think step by step. Show your work. Give your final decoded answer.

Format your final answer as: FINAL_ANSWER: [decoded message]
"""

    all_info = "\n\n".join([
        f"=== {m.get('from', 'UNKNOWN')} ===\n{m.get('response', m.get('content', 'No response'))}"
        for m in all_messages
    ])

    try:
        response = client.messages.create(
            model=model,
            max_tokens=1500,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"All owl contributions:\n{all_info}\n\nNow decode the message step by step."
            }]
        )
        decoded_attempt = response.content[0].text

        # Check if correct answer is in response
        is_correct = correct_answer.upper() in decoded_attempt.upper()

        return {
            "decoded_attempt": decoded_attempt,
            "tokens": response.usage.output_tokens,
            "is_correct": is_correct,
            "correct_answer": correct_answer,
        }
    except Exception as e:
        return {
            "decoded_attempt": f"Error: {str(e)}",
            "tokens": 0,
            "is_correct": False,
            "correct_answer": correct_answer,
        }


def score_decode(decoded_attempt: str, correct_answer: str, owl_count: int) -> dict:
    """
    Score the decoding attempt.
    """
    score = 0
    max_score = 100
    checks = []

    decoded_upper = decoded_attempt.upper()
    correct_upper = correct_answer.upper()

    # Check 1: Exact match (50 points)
    if correct_upper in decoded_upper:
        score += 50
        checks.append("Exact answer found: YES")
    else:
        checks.append("Exact answer found: NO")

    # Check 2: Partial match - letters present (30 points)
    letters_correct = sum(1 for c in correct_upper if c in decoded_upper)
    letter_ratio = letters_correct / len(correct_upper)
    partial_score = int(30 * letter_ratio)
    score += partial_score
    checks.append(f"Letters correct: {letters_correct}/{len(correct_upper)} ({partial_score}/30)")

    # Check 3: Showed work / process (10 points)
    if "step" in decoded_attempt.lower() or "rule" in decoded_attempt.lower():
        score += 10
        checks.append("Showed process: YES")
    else:
        checks.append("Showed process: NO")

    # Check 4: Identified transformation order (10 points)
    if "reverse" in decoded_attempt.lower() or "8" in decoded_attempt:
        score += 10
        checks.append("Understood order: YES")
    else:
        checks.append("Understood order: NO")

    return {
        "score": min(score, max_score),
        "max_score": max_score,
        "percentage": round(min(score, max_score) / max_score * 100, 1),
        "is_correct": correct_upper in decoded_upper,
        "checks": checks,
        "owl_count": owl_count,
    }


async def run_single_agent_all_info(client: anthropic.Anthropic,
                                   transformations: dict,
                                   encoded_msg: str,
                                   correct_answer: str) -> dict:
    """
    Single agent has ALL information. Can they decode it?
    This is the baseline for what's achievable with all info but no coordination.
    """
    all_rules = "\n".join([
        f"Step {t['step']}: {t['rule']}"
        for t in transformations.values()
    ])

    system_prompt = """You are an AI assistant solving a decoding puzzle.

You have ALL 8 transformation rules. Apply them in REVERSE order (8, 7, 6, ... 1).

Think step by step. Show your work. Give your final decoded answer.

Format your final answer as: FINAL_ANSWER: [decoded message]
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"""ENCODED MESSAGE: PUZZLE_v2: {encoded_msg}

ALL TRANSFORMATION RULES (apply in reverse order 8→1):
{all_rules}

GOAL: Decode the original message.

Work through this step by step, applying each rule in reverse."""
            }]
        )
        decoded_attempt = response.content[0].text
        score_result = score_decode(decoded_attempt, correct_answer, 1)

        return {
            "type": "single_agent_all_info",
            "decoded_attempt": decoded_attempt,
            "tokens": response.usage.output_tokens,
            **score_result,
        }
    except Exception as e:
        return {
            "type": "single_agent_all_info",
            "decoded_attempt": f"Error: {str(e)}",
            "tokens": 0,
            "score": 0,
            "percentage": 0,
            "checks": [],
        }


async def run_n_owl_collective(client: anthropic.Anthropic, n_owls: int,
                              transformations: dict, owl_clues: dict,
                              correct_answer: str, iterations: int = 3) -> dict:
    """
    Run the puzzle with N owls collaborating.
    """
    owl_names = list(transformations.keys())[:n_owls]
    shared_messages = []
    total_tokens = 0

    # Run iterations of message passing
    for iteration in range(iterations):
        for owl_name in owl_names:
            clue = owl_clues[owl_name]
            result = await run_owl_decode(
                client, owl_name, clue, shared_messages
            )
            total_tokens += result["tokens"]
            shared_messages.append({
                "from": owl_name,
                "content": result["response"],
                "iteration": iteration,
            })

    # Final synthesis
    synthesis = await run_final_decode(
        client, shared_messages, correct_answer
    )
    total_tokens += synthesis["tokens"]

    score_result = score_decode(synthesis["decoded_attempt"], correct_answer, n_owls)

    return {
        "type": f"{n_owls}_owls",
        "n_owls": n_owls,
        "iterations": iterations,
        "decoded_attempt": synthesis["decoded_attempt"],
        "messages": shared_messages,
        "total_tokens": total_tokens,
        **score_result,
    }


async def run_full_test():
    """Run the complete hard emergence test."""
    client = anthropic.Anthropic(api_key=API_KEY)

    # Generate the puzzle
    transformations, correct_answer, owl_clues = generate_puzzle()

    print("=" * 60)
    print("HARD EMERGENCE TEST")
    print("'The Puzzle That REQUIRES 8 Minds'")
    print("=" * 60)
    print(f"Correct answer: {correct_answer}")
    print()

    results = []

    # Test 1: Single agent with ALL information
    print("Running: Single Agent (ALL info)...")
    single_result = await run_single_agent_all_info(
        client, transformations,
        list(owl_clues.values())[0]["encoded_message"].replace("PUZZLE_v2: ", ""),
        correct_answer
    )
    results.append(single_result)
    print(f"  Score: {single_result['percentage']}%")

    # Test 2: 8 owls (full collective)
    print("\nRunning: 8 Owls (full collective)...")
    result_8 = await run_n_owl_collective(
        client, 8, transformations, owl_clues, correct_answer, iterations=2
    )
    results.append(result_8)
    print(f"  Score: {result_8['percentage']}%")

    # Test 3: 6 owls (75% of collective)
    print("\nRunning: 6 Owls (75% collective)...")
    result_6 = await run_n_owl_collective(
        client, 6, transformations, owl_clues, correct_answer, iterations=2
    )
    results.append(result_6)
    print(f"  Score: {result_6['percentage']}%")

    # Test 4: 4 owls (half collective)
    print("\nRunning: 4 Owls (50% collective)...")
    result_4 = await run_n_owl_collective(
        client, 4, transformations, owl_clues, correct_answer, iterations=2
    )
    results.append(result_4)
    print(f"  Score: {result_4['percentage']}%")

    # Analyze results
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)

    scores = {}
    for r in results:
        print(f"\n{r['type'].upper()}: {r['percentage']}%")
        if 'checks' in r:
            for check in r['checks']:
                print(f"  - {check}")
        scores[r['type']] = r['percentage']

    # Emergence analysis
    print("\n" + "=" * 60)
    print("EMERGENCE ANALYSIS")
    print("=" * 60)

    # Check: Does 8 owls beat single agent?
    if scores.get('8_owls', 0) > scores.get('single_agent_all_info', 0):
        print("8 owls > Single agent (all info): YES - EMERGENCE INDICATED")
    else:
        print("8 owls > Single agent (all info): NO - No emergence")

    # Check: Monotonic degradation?
    if scores.get('8_owls', 0) > scores.get('6_owls', 0) > scores.get('4_owls', 0):
        print("Monotonic degradation (8>6>4): YES - Each owl matters")
    else:
        print("Monotonic degradation (8>6>4): NO - Owls may be redundant")

    # Save results
    timestamp = datetime.now(timezone.utc).isoformat()
    result_file = RESULTS_DIR / f"hard_emergence_{timestamp.replace(':', '-')}.json"

    with open(result_file, 'w') as f:
        json.dump({
            "timestamp": timestamp,
            "correct_answer": correct_answer,
            "results": [
                {k: v for k, v in r.items() if k not in ['messages', 'decoded_attempt']}
                for r in results
            ],
            "emergence_indicated": scores.get('8_owls', 0) > scores.get('single_agent_all_info', 0),
        }, f, indent=2)

    print(f"\nResults saved to: {result_file}")

    # Generate report
    report = generate_report(results, scores, correct_answer)
    report_file = RESULTS_DIR / "HARD_EMERGENCE_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    print(f"Report saved to: {report_file}")

    return results


def generate_report(results: list, scores: dict, correct_answer: str) -> str:
    """Generate markdown report."""
    timestamp = datetime.now(timezone.utc).isoformat()

    emergence_indicated = scores.get('8_owls', 0) > scores.get('single_agent_all_info', 0)

    return f"""# HARD EMERGENCE TEST REPORT
**"The Puzzle That REQUIRES 8 Minds"**
**Completed:** {timestamp}

---

## PUZZLE DESIGN

Each owl holds ONE piece of an 8-step decoding puzzle. The puzzle is:
1. Designed to be too complex for a single agent to track all transformations
2. Requires coordination to share rules
3. Tests whether collective coordination > individual processing

Correct answer: **{correct_answer}**

---

## RESULTS

| Configuration | Score | Correct? |
|---------------|-------|----------|
| Single Agent (ALL info) | {scores.get('single_agent_all_info', 0)}% | {'YES' if scores.get('single_agent_all_info', 0) >= 50 else 'NO'} |
| 8 Owls (full collective) | {scores.get('8_owls', 0)}% | {'YES' if scores.get('8_owls', 0) >= 50 else 'NO'} |
| 6 Owls (75% collective) | {scores.get('6_owls', 0)}% | {'YES' if scores.get('6_owls', 0) >= 50 else 'NO'} |
| 4 Owls (50% collective) | {scores.get('4_owls', 0)}% | {'YES' if scores.get('4_owls', 0) >= 50 else 'NO'} |

---

## EMERGENCE ANALYSIS

### Test 1: Collective > Individual
- 8 Owls: {scores.get('8_owls', 0)}%
- Single Agent (all info): {scores.get('single_agent_all_info', 0)}%
- **Result:** {'COLLECTIVE WINS - EMERGENCE INDICATED' if emergence_indicated else 'INDIVIDUAL WINS - NO EMERGENCE'}

### Test 2: Every Owl Matters
- 8 → 6 owls: {scores.get('8_owls', 0) - scores.get('6_owls', 0):+.1f}%
- 6 → 4 owls: {scores.get('6_owls', 0) - scores.get('4_owls', 0):+.1f}%
- **Result:** {'MONOTONIC DEGRADATION' if scores.get('8_owls', 0) >= scores.get('6_owls', 0) >= scores.get('4_owls', 0) else 'NON-MONOTONIC'}

---

## VERDICT

**EMERGENCE INDICATED:** {'YES' if emergence_indicated else 'NO'}

{'The 8OWLS collective demonstrates genuine emergence where coordinated communication produces results superior to individual processing, even when the individual has all available information.' if emergence_indicated else 'The test did not demonstrate emergence. The single agent with all information performed similarly or better than the collective. This may be because: (1) the puzzle was still too simple, (2) coordination overhead exceeded benefit, or (3) synthesis was the bottleneck.'}

---

## INTERPRETATION

{'This result suggests that collective AI coordination can solve problems more effectively than single agents with equivalent information. The emergence effect is real.' if emergence_indicated else 'The test did not prove emergence. Consider: (1) more complex puzzles, (2) better coordination protocols, (3) reduced synthesis overhead.'}

---

**(◉) Truth discovered through measurement.**

Generated: {timestamp}
"""


if __name__ == "__main__":
    print("Starting Hard Emergence Test...")
    print("This tests whether 8 agents coordinating can beat 1 agent with all info")
    print()

    asyncio.run(run_full_test())
