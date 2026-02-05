#!/usr/bin/env python3
"""
Sonnet 5 (Fennec) Validation Script
Test availability and compare quality with Opus 4.5

Usage:
    python3 test_sonnet_5.py              # Quick availability test
    python3 test_sonnet_5.py --full       # Full comparison test
    python3 test_sonnet_5.py --benchmark  # Performance benchmark
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime

# Load API key
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    env_path = os.path.expanduser("~/.env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if line.startswith("ANTHROPIC_API_KEY="):
                    ANTHROPIC_API_KEY = line.strip().split("=", 1)[1].strip('"\'')
                    break

if not ANTHROPIC_API_KEY:
    print("ERROR: ANTHROPIC_API_KEY not found")
    sys.exit(1)

import anthropic

# Model IDs
SONNET_5 = "claude-sonnet-5-20260203"
OPUS_45 = "claude-opus-4-5-20251101"
SONNET_45 = "claude-sonnet-4-5-20250929"

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def test_model_availability(model_id: str) -> dict:
    """Test if a model is available and responding."""
    print(f"\nTesting: {model_id}")
    start = time.time()

    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=100,
            messages=[{
                "role": "user",
                "content": "Reply with only your model name and version. Nothing else."
            }]
        )

        latency = time.time() - start
        content = response.content[0].text if response.content else ""

        return {
            "model": model_id,
            "available": True,
            "response": content,
            "latency_ms": round(latency * 1000),
            "input_tokens": response.usage.input_tokens,
            "output_tokens": response.usage.output_tokens,
            "stop_reason": response.stop_reason
        }

    except anthropic.NotFoundError:
        return {"model": model_id, "available": False, "error": "Model not found"}
    except anthropic.APIError as e:
        return {"model": model_id, "available": False, "error": str(e)}


def test_coding_quality(model_id: str) -> dict:
    """Test coding capability with a standard task."""
    prompt = """Write a Python function that:
1. Takes a list of integers
2. Returns the two numbers that sum to a target value
3. Uses O(n) time complexity with a hash map
4. Handles edge cases (empty list, no solution, duplicates)

Include type hints and a docstring. Code only, no explanation."""

    start = time.time()

    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )

        latency = time.time() - start
        content = response.content[0].text if response.content else ""

        # Basic quality checks
        has_type_hints = "def " in content and "->" in content
        has_docstring = '"""' in content or "'''" in content
        has_hash_map = "dict" in content.lower() or "{}" in content
        handles_edge = "none" in content.lower() or "raise" in content.lower()

        quality_score = sum([has_type_hints, has_docstring, has_hash_map, handles_edge]) / 4

        return {
            "model": model_id,
            "latency_ms": round(latency * 1000),
            "quality_score": quality_score,
            "has_type_hints": has_type_hints,
            "has_docstring": has_docstring,
            "has_hash_map": has_hash_map,
            "handles_edge_cases": handles_edge,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "code_preview": content[:200] + "..." if len(content) > 200 else content
        }

    except Exception as e:
        return {"model": model_id, "error": str(e)}


def test_context_handling(model_id: str) -> dict:
    """Test context window handling with large input."""
    # Generate a moderate context test (not 1M, but enough to test stability)
    context_items = [f"Item {i}: Value is {i * 17 % 100}" for i in range(1000)]
    context = "\n".join(context_items)

    # Ask about item buried in the middle
    target_item = 537
    expected_value = target_item * 17 % 100

    prompt = f"""Here is a list of items:

{context}

What is the value for Item {target_item}? Reply with just the number."""

    start = time.time()

    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=50,
            messages=[{"role": "user", "content": prompt}]
        )

        latency = time.time() - start
        content = response.content[0].text.strip() if response.content else ""

        # Check if correct value retrieved
        try:
            retrieved_value = int(content)
            correct = retrieved_value == expected_value
        except ValueError:
            correct = str(expected_value) in content

        return {
            "model": model_id,
            "latency_ms": round(latency * 1000),
            "context_items": len(context_items),
            "target_item": target_item,
            "expected_value": expected_value,
            "response": content,
            "correct_retrieval": correct,
            "input_tokens": response.usage.input_tokens
        }

    except Exception as e:
        return {"model": model_id, "error": str(e)}


def test_trading_analysis(model_id: str) -> dict:
    """Test trading analysis quality (critical for our use case)."""
    prompt = """Analyze this trading scenario:

Market: Polymarket prediction market
Event: "Will BTC reach $150K by March 2026?"
Current price: YES at 0.42 (42% implied probability)
Volume: $2.1M total
Recent movement: Price dropped from 0.55 to 0.42 in 24h

External context:
- BTC current price: $97,500
- 30-day trend: +8%
- Major news: Spot ETF inflows at record levels

Provide:
1. Assessment of edge (is 42% mispriced?)
2. Recommended position (YES/NO/PASS)
3. Position size recommendation (% of bankroll)
4. Key risk factors
5. Confidence level (1-10)

Be concise but thorough."""

    start = time.time()

    try:
        response = client.messages.create(
            model=model_id,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        latency = time.time() - start
        content = response.content[0].text if response.content else ""

        # Quality checks for trading analysis
        has_edge_assessment = "edge" in content.lower() or "mispric" in content.lower()
        has_position_rec = any(x in content.upper() for x in ["YES", "NO", "PASS"])
        has_size_rec = "%" in content or "position size" in content.lower()
        has_risk_factors = "risk" in content.lower()
        has_confidence = any(f"{i}/10" in content or f"{i} out of 10" in content.lower() for i in range(1, 11))

        quality_score = sum([has_edge_assessment, has_position_rec, has_size_rec, has_risk_factors, has_confidence]) / 5

        return {
            "model": model_id,
            "latency_ms": round(latency * 1000),
            "quality_score": quality_score,
            "has_edge_assessment": has_edge_assessment,
            "has_position_recommendation": has_position_rec,
            "has_size_recommendation": has_size_rec,
            "has_risk_factors": has_risk_factors,
            "has_confidence_level": has_confidence,
            "tokens_used": response.usage.input_tokens + response.usage.output_tokens,
            "response_preview": content[:500] + "..." if len(content) > 500 else content
        }

    except Exception as e:
        return {"model": model_id, "error": str(e)}


def run_quick_test():
    """Quick availability check."""
    print("=" * 60)
    print("SONNET 5 (FENNEC) - QUICK AVAILABILITY TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    results = {}
    for model in [SONNET_5, OPUS_45, SONNET_45]:
        results[model] = test_model_availability(model)

        if results[model].get("available"):
            print(f"  [OK] Available - {results[model].get('latency_ms')}ms latency")
            print(f"       Response: {results[model].get('response', '')[:100]}")
        else:
            print(f"  [FAIL] {results[model].get('error', 'Unknown error')}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)

    sonnet5_available = results.get(SONNET_5, {}).get("available", False)
    if sonnet5_available:
        print(f"\n[SUCCESS] Sonnet 5 ({SONNET_5}) is AVAILABLE!")
        print("\nReady to migrate. Run with --full for quality comparison.")
    else:
        print(f"\n[WAITING] Sonnet 5 ({SONNET_5}) not yet available.")
        print("Check back later or verify model ID.")

    return results


def run_full_comparison():
    """Full quality comparison between models."""
    print("=" * 60)
    print("SONNET 5 (FENNEC) - FULL COMPARISON TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("=" * 60)

    models_to_test = [SONNET_5, OPUS_45]
    results = {"timestamp": datetime.now().isoformat(), "tests": {}}

    # Test 1: Availability
    print("\n--- Test 1: Model Availability ---")
    for model in models_to_test:
        result = test_model_availability(model)
        results["tests"][f"availability_{model}"] = result
        status = "[OK]" if result.get("available") else "[FAIL]"
        print(f"{status} {model}: {result.get('latency_ms', 'N/A')}ms")

    # Test 2: Coding Quality
    print("\n--- Test 2: Coding Quality ---")
    for model in models_to_test:
        result = test_coding_quality(model)
        results["tests"][f"coding_{model}"] = result
        if "error" not in result:
            print(f"[{model}]")
            print(f"  Quality Score: {result.get('quality_score', 0):.0%}")
            print(f"  Latency: {result.get('latency_ms')}ms")
            print(f"  Tokens: {result.get('tokens_used')}")
        else:
            print(f"[{model}] ERROR: {result.get('error')}")

    # Test 3: Context Handling
    print("\n--- Test 3: Context Retrieval (1000 items) ---")
    for model in models_to_test:
        result = test_context_handling(model)
        results["tests"][f"context_{model}"] = result
        if "error" not in result:
            status = "[CORRECT]" if result.get("correct_retrieval") else "[WRONG]"
            print(f"{status} {model}")
            print(f"  Response: {result.get('response')}")
            print(f"  Expected: {result.get('expected_value')}")
            print(f"  Latency: {result.get('latency_ms')}ms")
        else:
            print(f"[{model}] ERROR: {result.get('error')}")

    # Test 4: Trading Analysis
    print("\n--- Test 4: Trading Analysis Quality ---")
    for model in models_to_test:
        result = test_trading_analysis(model)
        results["tests"][f"trading_{model}"] = result
        if "error" not in result:
            print(f"[{model}]")
            print(f"  Quality Score: {result.get('quality_score', 0):.0%}")
            print(f"  Edge Assessment: {'Yes' if result.get('has_edge_assessment') else 'No'}")
            print(f"  Position Rec: {'Yes' if result.get('has_position_recommendation') else 'No'}")
            print(f"  Size Rec: {'Yes' if result.get('has_size_recommendation') else 'No'}")
            print(f"  Risk Factors: {'Yes' if result.get('has_risk_factors') else 'No'}")
            print(f"  Confidence: {'Yes' if result.get('has_confidence_level') else 'No'}")
            print(f"  Latency: {result.get('latency_ms')}ms")
        else:
            print(f"[{model}] ERROR: {result.get('error')}")

    # Summary
    print("\n" + "=" * 60)
    print("COMPARISON SUMMARY")
    print("=" * 60)

    sonnet5_coding = results["tests"].get(f"coding_{SONNET_5}", {})
    opus_coding = results["tests"].get(f"coding_{OPUS_45}", {})
    sonnet5_trading = results["tests"].get(f"trading_{SONNET_5}", {})
    opus_trading = results["tests"].get(f"trading_{OPUS_45}", {})

    if sonnet5_coding.get("quality_score") and opus_coding.get("quality_score"):
        coding_diff = sonnet5_coding["quality_score"] - opus_coding["quality_score"]
        print(f"\nCoding Quality Difference: {coding_diff:+.0%}")

    if sonnet5_trading.get("quality_score") and opus_trading.get("quality_score"):
        trading_diff = sonnet5_trading["quality_score"] - opus_trading["quality_score"]
        print(f"Trading Quality Difference: {trading_diff:+.0%}")

    if sonnet5_coding.get("latency_ms") and opus_coding.get("latency_ms"):
        latency_ratio = opus_coding["latency_ms"] / sonnet5_coding["latency_ms"]
        print(f"Speed Improvement: {latency_ratio:.1f}x faster" if latency_ratio > 1 else f"Speed: {1/latency_ratio:.1f}x slower")

    # Save results
    output_path = "/Users/aaronnosbisch/REPOS/seed/logs/sonnet5_test_results.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nFull results saved to: {output_path}")

    return results


def run_benchmark():
    """Performance benchmark with multiple iterations."""
    print("=" * 60)
    print("SONNET 5 (FENNEC) - PERFORMANCE BENCHMARK")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("Iterations: 5 per model")
    print("=" * 60)

    models = [SONNET_5, OPUS_45]
    iterations = 5
    results = {}

    for model in models:
        print(f"\nBenchmarking: {model}")
        latencies = []

        for i in range(iterations):
            start = time.time()
            try:
                response = client.messages.create(
                    model=model,
                    max_tokens=100,
                    messages=[{"role": "user", "content": f"Count from 1 to 10. Iteration {i+1}."}]
                )
                latency = (time.time() - start) * 1000
                latencies.append(latency)
                print(f"  Iteration {i+1}: {latency:.0f}ms")
            except Exception as e:
                print(f"  Iteration {i+1}: ERROR - {e}")

        if latencies:
            results[model] = {
                "iterations": len(latencies),
                "avg_latency_ms": sum(latencies) / len(latencies),
                "min_latency_ms": min(latencies),
                "max_latency_ms": max(latencies),
                "all_latencies": latencies
            }

    print("\n" + "=" * 60)
    print("BENCHMARK RESULTS")
    print("=" * 60)

    for model, data in results.items():
        print(f"\n{model}:")
        print(f"  Average: {data['avg_latency_ms']:.0f}ms")
        print(f"  Min: {data['min_latency_ms']:.0f}ms")
        print(f"  Max: {data['max_latency_ms']:.0f}ms")

    if SONNET_5 in results and OPUS_45 in results:
        ratio = results[OPUS_45]["avg_latency_ms"] / results[SONNET_5]["avg_latency_ms"]
        print(f"\nSonnet 5 is {ratio:.2f}x {'faster' if ratio > 1 else 'slower'} than Opus 4.5")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Sonnet 5 (Fennec) availability and quality")
    parser.add_argument("--full", action="store_true", help="Run full comparison test")
    parser.add_argument("--benchmark", action="store_true", help="Run performance benchmark")
    args = parser.parse_args()

    if args.benchmark:
        run_benchmark()
    elif args.full:
        run_full_comparison()
    else:
        run_quick_test()
