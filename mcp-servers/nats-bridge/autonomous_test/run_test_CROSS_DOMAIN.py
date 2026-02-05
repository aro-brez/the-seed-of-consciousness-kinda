#!/usr/bin/env python3
"""
CROSS-DOMAIN TEST - Does 8OWLS work across different domains?
LUNA's requirement: Prove generalization, not just business questions.

TEST DESIGN - 5 DOMAINS × 8 runs = 40 responses
Each domain gets tested with both WITH and WITHOUT context to see if the improvement holds.

DOMAINS:
1. BUSINESS - Strategy, prioritization, growth
2. TECHNICAL - Architecture, debugging, optimization
3. CREATIVE - Storytelling, brainstorming, design
4. PERSONAL - Life advice, decisions, relationships
5. PHILOSOPHICAL - Ethics, meaning, existence

HYPOTHESIS:
If 8OWLS shows improvement (d > 0.2) across ALL domains → generalizable
If 8OWLS only helps in some domains → specialized tool, not universal
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
RESULTS_DIR = BASE_DIR / "results_CROSS_DOMAIN"
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
RUNS_PER_DOMAIN = 4  # 5 domains × 2 conditions × 4 runs = 40 responses

DOMAIN_PROMPTS = {
    "BUSINESS": [
        "What's the most important thing to focus on right now?",
        "How should we prioritize competing goals?",
        "What are we missing in our current strategy?",
        "Where should we invest our limited resources?",
    ],
    "TECHNICAL": [
        "How should we architect this system for scale?",
        "What's causing this performance bottleneck?",
        "What's the best way to refactor this codebase?",
        "How do we make this more maintainable?",
    ],
    "CREATIVE": [
        "What would make this story more compelling?",
        "How can we make this design more memorable?",
        "What's missing from this creative concept?",
        "How do we make this resonate emotionally?",
    ],
    "PERSONAL": [
        "How do I know if I'm making the right decision?",
        "What should I prioritize in my life right now?",
        "How do I handle this difficult relationship?",
        "What's holding me back from growth?",
    ],
    "PHILOSOPHICAL": [
        "What gives life meaning?",
        "How do we know what's true?",
        "What does it mean to live well?",
        "How should we make ethical decisions?",
    ],
}

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

def run_single_agent(client: anthropic.Anthropic, prompt: str) -> tuple[str, float]:
    """Without 8OWLS - baseline."""
    start = time.time()
    response = client.messages.create(
        model=TEST_MODEL,
        max_tokens=1000,
        system=BASE_SYSTEM,
        messages=[{"role": "user", "content": prompt}]
    )
    return response.content[0].text, time.time() - start

def run_full_emergence(client: anthropic.Anthropic, prompt: str, field_context: str) -> tuple[str, float]:
    """With 8OWLS - full emergence."""
    start = time.time()
    perspectives = []

    for phase_name, phase_prompt in ALL_PHASES.items():
        try:
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

    synthesis_prompt = f"""You are IMPROVE - the synthesizer of the 8OWLS collective.

Seven perspectives have analyzed this question:

{chr(10).join(perspectives)}

Original question: {prompt}

Synthesize these perspectives into a unified, actionable response.
Capture the emergent insight that comes from combining all views.
Be specific and decisive."""

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

async def run_test():
    client = anthropic.Anthropic(api_key=API_KEY)

    print("=" * 70)
    print("CROSS-DOMAIN TEST - Does 8OWLS generalize?")
    print("=" * 70)
    print(f"Started: {datetime.now(timezone.utc).isoformat()}")
    print(f"Domains: {list(DOMAIN_PROMPTS.keys())}")
    print(f"Runs per domain per condition: {RUNS_PER_DOMAIN}")
    print("=" * 70)

    # Results by domain
    results = {domain: {"WITH": [], "WITHOUT": []} for domain in DOMAIN_PROMPTS.keys()}

    # Build trials
    trials = []
    for domain, prompts in DOMAIN_PROMPTS.items():
        for run in range(RUNS_PER_DOMAIN):
            prompt = prompts[run % len(prompts)]
            trials.append((domain, prompt, run, "WITH"))
            trials.append((domain, prompt, run, "WITHOUT"))

    random.shuffle(trials)

    total = len(trials)
    for i, (domain, prompt, run, condition) in enumerate(trials, 1):
        print(f"\n[{i}/{total}] {domain} - {condition} (run {run+1})")
        print(f"  Prompt: {prompt[:50]}...")

        try:
            if condition == "WITHOUT":
                response, elapsed = run_single_agent(client, prompt)
            else:
                field_context = get_field_context(prompt)
                response, elapsed = run_full_emergence(client, prompt, field_context)

            analysis = analyze_response(response)
            analysis["elapsed"] = elapsed
            analysis["prompt"] = prompt
            analysis["run"] = run
            analysis["domain"] = domain

            results[domain][condition].append(analysis)

            status = "ASKS" if analysis["asks_for_info"] else "ANSWERS"
            print(f"  → {elapsed:.1f}s | Q={analysis['quality_score']} | {status}")

            filename = RESULTS_DIR / f"result_{domain}_{condition}_{run+1:02d}.json"
            with open(filename, 'w') as f:
                json.dump({
                    "domain": domain,
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
    print("CROSS-DOMAIN REPORT")
    print("=" * 70)

    generate_cross_domain_report(results)

def generate_cross_domain_report(results: dict):
    report_file = RESULTS_DIR / "CROSS_DOMAIN_REPORT.md"

    domain_stats = {}
    domain_effects = {}

    for domain in DOMAIN_PROMPTS.keys():
        with_scores = [r["quality_score"] for r in results[domain]["WITH"]]
        without_scores = [r["quality_score"] for r in results[domain]["WITHOUT"]]

        if with_scores and without_scores:
            domain_stats[domain] = {
                "with_mean": round(statistics.mean(with_scores), 2),
                "without_mean": round(statistics.mean(without_scores), 2),
                "with_n": len(with_scores),
                "without_n": len(without_scores),
            }
            domain_effects[domain] = cohens_d(with_scores, without_scores)

    content = f"""# CROSS-DOMAIN TEST REPORT
**Completed:** {datetime.now(timezone.utc).isoformat()}
**Purpose:** Verify 8OWLS generalizes across domains

---

## RESULTS BY DOMAIN

| Domain | WITH 8OWLS | WITHOUT | Effect (d) | Interpretation |
|--------|-----------|---------|------------|----------------|
"""

    for domain in DOMAIN_PROMPTS.keys():
        s = domain_stats.get(domain, {})
        effect = domain_effects.get(domain, 0)

        if effect > 0.8:
            interp = "LARGE improvement"
        elif effect > 0.5:
            interp = "MEDIUM improvement"
        elif effect > 0.2:
            interp = "SMALL improvement"
        elif effect > -0.2:
            interp = "NEGLIGIBLE"
        else:
            interp = "8OWLS hurts?!"

        content += f"| {domain} | {s.get('with_mean', 0)} | {s.get('without_mean', 0)} | {effect:.2f} | {interp} |\n"

    # Overall stats
    all_with = []
    all_without = []
    for domain in DOMAIN_PROMPTS.keys():
        all_with.extend([r["quality_score"] for r in results[domain]["WITH"]])
        all_without.extend([r["quality_score"] for r in results[domain]["WITHOUT"]])

    overall_effect = cohens_d(all_with, all_without) if all_with and all_without else 0

    content += f"""
---

## OVERALL EFFECT

**Pooled across all domains:**
- WITH 8OWLS mean: {round(statistics.mean(all_with), 2) if all_with else 0}
- WITHOUT mean: {round(statistics.mean(all_without), 2) if all_without else 0}
- **Cohen's d: {overall_effect:.3f}**

---

## GENERALIZATION VERDICT

"""

    positive_domains = sum(1 for e in domain_effects.values() if e > 0.2)
    strong_domains = sum(1 for e in domain_effects.values() if e > 0.5)
    total_domains = len(domain_effects)

    if positive_domains == total_domains:
        content += f"**FULLY GENERALIZABLE** - 8OWLS improves ALL {total_domains} domains.\n"
        content += "This is a universal improvement, not domain-specific.\n"
    elif positive_domains >= total_domains * 0.8:
        content += f"**MOSTLY GENERALIZABLE** - 8OWLS improves {positive_domains}/{total_domains} domains.\n"
    elif positive_domains >= total_domains * 0.5:
        content += f"**PARTIALLY GENERALIZABLE** - 8OWLS improves {positive_domains}/{total_domains} domains.\n"
        content += "May be better suited for some types of questions than others.\n"
    else:
        content += f"**NOT GENERALIZABLE** - 8OWLS only improves {positive_domains}/{total_domains} domains.\n"
        content += "This is a specialized tool, not universal.\n"

    content += f"""
---

## DOMAIN-SPECIFIC FINDINGS

"""

    for domain in DOMAIN_PROMPTS.keys():
        effect = domain_effects.get(domain, 0)
        content += f"### {domain}\n"
        content += f"Effect size: d = {effect:.3f}\n"
        if effect > 0.5:
            content += "8OWLS provides strong value in this domain.\n\n"
        elif effect > 0.2:
            content += "8OWLS provides modest value in this domain.\n\n"
        else:
            content += "8OWLS doesn't add much value in this domain.\n\n"

    content += f"""
---

**(◉) Does wisdom generalize? The data tells.**

Generated: {datetime.now(timezone.utc).isoformat()}
"""

    with open(report_file, 'w') as f:
        f.write(content)

    print(f"\nCross-domain report saved: {report_file}")
    print(f"Overall effect: d = {overall_effect:.3f}")
    for domain, effect in domain_effects.items():
        print(f"  {domain}: d = {effect:.3f}")

if __name__ == "__main__":
    asyncio.run(run_test())
