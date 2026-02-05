#!/usr/bin/env python3
"""
QUEST Analysis: Challenging the 8OWLS Assumptions
Brutally honest assessment of token-controlled experiment results
"""

import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict, List
import statistics

@dataclass
class Result:
    trial_num: int
    condition: str
    quality_score: float
    elapsed: float
    length: int
    actionability: int
    specificity: int
    asks_for_info: int

def load_all_results(directory: str) -> Dict[str, List[Result]]:
    """Load all result files and organize by condition"""
    results = {"A": [], "B": [], "C": []}

    for filename in sorted(os.listdir(directory)):
        if not filename.startswith("result_") or not filename.endswith(".json"):
            continue

        filepath = os.path.join(directory, filename)
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            condition = data.get("condition")
            if condition not in results:
                continue

            analysis = data.get("analysis", {})
            result = Result(
                trial_num=data.get("trial_num", 0),
                condition=condition,
                quality_score=analysis.get("quality_score", 0),
                elapsed=analysis.get("elapsed", 0),
                length=analysis.get("length", 0),
                actionability=analysis.get("actionability", 0),
                specificity=analysis.get("specificity", 0),
                asks_for_info=analysis.get("asks_for_info", 0)
            )
            results[condition].append(result)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            continue

    return results

def calculate_stats(results: List[Result]) -> Dict:
    """Calculate descriptive statistics"""
    if not results:
        return {}

    scores = [r.quality_score for r in results]
    elapsed_times = [r.elapsed for r in results]
    lengths = [r.length for r in results]
    actionability = [r.actionability for r in results]
    specificity = [r.specificity for r in results]

    return {
        "n": len(results),
        "quality_mean": statistics.mean(scores),
        "quality_median": statistics.median(scores),
        "quality_stdev": statistics.stdev(scores) if len(scores) > 1 else 0,
        "quality_min": min(scores),
        "quality_max": max(scores),
        "elapsed_mean": statistics.mean(elapsed_times),
        "elapsed_total": sum(elapsed_times),
        "length_mean": statistics.mean(lengths),
        "actionability_mean": statistics.mean(actionability),
        "specificity_mean": statistics.mean(specificity),
    }

def cohens_d(group1: List[float], group2: List[float]) -> float:
    """Calculate Cohen's d effect size"""
    n1, n2 = len(group1), len(group2)
    var1, var2 = statistics.variance(group1), statistics.variance(group2)
    pooled_std = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
    pooled_std = pooled_std ** 0.5
    return (statistics.mean(group1) - statistics.mean(group2)) / pooled_std

def main():
    directory = "/Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/autonomous_test/results_TOKEN_CONTROLLED"

    # Load data
    print("=" * 80)
    print("QUEST ANALYSIS: Challenging 8OWLS Assumptions")
    print("=" * 80)
    print()

    results = load_all_results(directory)

    # Print sample sizes
    print("SAMPLE STATUS")
    print("-" * 80)
    for cond in ["A", "B", "C"]:
        n = len(results[cond])
        print(f"  Condition {cond}: n={n}")
    print()

    # Calculate stats for each condition
    stats = {}
    for cond in ["A", "B", "C"]:
        stats[cond] = calculate_stats(results[cond])

    print("DESCRIPTIVE STATISTICS (Quality Score)")
    print("-" * 80)
    for cond in ["A", "B", "C"]:
        s = stats[cond]
        if s:
            print(f"  Condition {cond}:")
            print(f"    n={s['n']}, Mean={s['quality_mean']:.2f}, Median={s['quality_median']:.2f}, SD={s['quality_stdev']:.2f}")
            print(f"    Range=[{s['quality_min']:.0f}, {s['quality_max']:.0f}]")
    print()

    # Effect sizes
    print("EFFECT SIZES (Cohen's d)")
    print("-" * 80)

    a_scores = [r.quality_score for r in results["A"]]
    b_scores = [r.quality_score for r in results["B"]]
    c_scores = [r.quality_score for r in results["C"]]

    if len(b_scores) > 1 and len(c_scores) > 1:
        d_bc = cohens_d(b_scores, c_scores)
        print(f"  B vs C (token-matched vs emergence): d={d_bc:.3f}")

    if len(a_scores) > 1 and len(c_scores) > 1:
        d_ac = cohens_d(a_scores, c_scores)
        print(f"  A vs C (baseline vs emergence): d={d_ac:.3f}")

    if len(a_scores) > 1 and len(b_scores) > 1:
        d_ab = cohens_d(a_scores, b_scores)
        print(f"  A vs B (baseline vs token-matched): d={d_ab:.3f}")
    print()

    # Response characteristics
    print("RESPONSE CHARACTERISTICS")
    print("-" * 80)
    for cond in ["A", "B", "C"]:
        s = stats[cond]
        if s:
            print(f"  Condition {cond}:")
            print(f"    Avg Length: {s['length_mean']:.0f} chars")
            print(f"    Avg Actionability: {s['actionability_mean']:.2f}")
            print(f"    Avg Specificity: {s['specificity_mean']:.2f}")
            print(f"    Avg Elapsed: {s['elapsed_mean']:.2f}s")
    print()

    # Find outliers
    print("OUTLIER ANALYSIS")
    print("-" * 80)
    for cond in ["A", "B", "C"]:
        scores = [r.quality_score for r in results[cond]]
        if scores:
            mean = statistics.mean(scores)
            stdev = statistics.stdev(scores) if len(scores) > 1 else 1
            outliers = [r for r in results[cond] if abs(r.quality_score - mean) > 2*stdev]
            if outliers:
                print(f"  Condition {cond}: {len(outliers)} outlier(s)")
                for r in outliers:
                    print(f"    Trial {r.trial_num}: score={r.quality_score:.0f}, length={r.length}, elapsed={r.elapsed:.1f}s")
            else:
                print(f"  Condition {cond}: No outliers (>2 SD)")
    print()

    return results, stats

if __name__ == "__main__":
    results, stats = main()
