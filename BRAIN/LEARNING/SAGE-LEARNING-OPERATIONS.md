# SAGE LEARNING OPERATIONS
## How to Actually Run the Learning Pipeline (Day-to-Day)

**Status:** Operational Manual
**For:** ARŌ, Instance Managers, Integration Engineers
**Updated:** 2026-02-05

---

## QUICK START: The Command for Every Improvement

When you discover something useful:

```bash
# 1. PERCEIVE - Capture the raw signal
python3 /Users/aaronnosbisch/REPOS/seed/tools/capture_signal.py \
  --source "github_trending" \
  --title "Your discovery title" \
  --url "link to thing" \
  --confidence 0.7 \
  --notes "Why this matters to 8OWLS"

# 2. CONNECT - Let system map relationships
python3 /Users/aaronnosbisch/REPOS/seed/tools/run_sage_pipeline.py \
  --phase connect \
  --signal-id "sig_ID_returned_from_step_1"

# 3-8. Let SAGE agents handle the rest (automatic daily jobs)
# See "AUTOMATION" section below
```

---

## OPERATIONAL FLOW: Daily Automation

### Schedule: Every 6 Hours

```bash
# Cron: 0 */6 * * *
*/6 * * * * cd /Users/aaronnosbisch/REPOS/seed && python3 tools/sage_cycle.py 2>&1 >> logs/sage_cycle.log
```

### What Happens Each Cycle

**Duration:** 15-30 minutes
**Cost:** ~$0.02 per cycle (Haiku)
**Steps:**

```
1. PERCEIVE Phase (2 min)
   - Pull latest signals_raw.jsonl
   - Count: 3,557 entries (824 new since last cycle)
   - Process: Deduplicate, normalize

2. CONNECT Phase (3 min)
   - Map each signal against architectural patterns
   - Output: connections_analyzed.jsonl updated
   - Pattern types: COORDINATION, TRADING, EMERGENCE, etc.

3. LEARN Phase (8 min)
   - Run hype detection filter on each signal
   - Evaluate: Credibility, Soundness, Relevance
   - Threshold: Hype score >= 2.8 → actionable
   - Output: learnings_extracted.jsonl updated
   - Example: "82 signals in, 3 actionable learnings out"

4. QUESTION Phase (4 min)
   - Generate challenges for top N actionable learnings
   - Output: challenges_validated.jsonl updated
   - Risk assessment: ACCEPT, CONDITIONAL, REJECT

5. EXPAND Phase (7 min, async)
   - For each "ACCEPT" challenge, spawn NOVA design agent
   - Design documents created: BRAIN/STRATEGY/[DESIGN_NAME].md
   - Spawned as background task (agent completes over hours/days)

6. REPORT Phase (1 min)
   - Summary written to: logs/sage_cycle_YYYY-MM-DD_HH:MM.log
   - Example output: "Cycle 624: 82 signals → 3 learnings → 1 new design (adaptive emergence)"
```

---

## FILE STRUCTURE: The Artifacts

### Input Files (What feeds the pipeline)

**1. signals_raw.jsonl** (3,557 entries, 2.1 MB)
```
Every raw signal capture:
- ARŌ observations
- GitHub trending
- Research papers
- Twitter signals
- Internal experiment results

One entry per line, newline-delimited JSON.
Format:
{
  "timestamp": "2026-02-05T11:23:47Z",
  "source": "github_trending|aro_feedback|research|twitter|experiment",
  "title": "Short title",
  "url": "link (if applicable)",
  "raw_signal": "Full description",
  "confidence": 0.0-1.0,
  "owlscore": Not yet scored
}
```

**2. connections_analyzed.jsonl** (Updated each cycle)
```
Outputs from PRISM CONNECT phase:
{
  "signal_id": "sig_SOURCE_YYYYMMDD_NNN",
  "pattern_type": "COORDINATION|TRADING|EMERGENCE|SCALING|etc",
  "relates_to": ["file1.md", "file2.py"],
  "estimated_impact": {
    "domain": "which part of 8OWLS",
    "performance_change": "+15% or -5% or neutral",
    "risk": "LOW|MEDIUM|HIGH",
    "effort_hours": 80
  }
}
```

**3. learnings_extracted.jsonl** (2,931 entries, growing)
```
Outputs from SAGE LEARN phase:
{
  "signal_id": "sig_...",
  "hype_score": 0.0-5.0,
  "verdict": "ACTIONABLE|INTERESTING|ARCHIVE",
  "core_innovation": "One sentence: what's the key insight?",
  "applicability": {
    "fits_our_problem": true|false,
    "problem_solved": "description",
    "estimated_benefit": "quantified ROI"
  },
  "timestamp": "when evaluated"
}
```

### Processing Files (Work in progress)

**4. challenges_validated.jsonl** (Partial)
```
Outputs from QUEST QUESTION phase:
{
  "signal_id": "sig_...",
  "design_id": "design_...",
  "challenges": [
    {
      "assumption": "MoE routing won't miss insights",
      "risk_level": "MEDIUM",
      "mitigation": "Fallback mechanism"
    }
  ],
  "risk_verdict": "ACCEPTABLE|RISKY|REJECTED"
}
```

**5. implementations_active.jsonl** (Partial)
```
Outputs from INTEGRATE phase:
{
  "implementation_id": "impl_adaptive_emergence_001",
  "status": "PHASE_A_IN_PROGRESS|PHASE_B_TESTING|PHASE_C_ROLLOUT|PHASE_D_LIVE",
  "tasks": [...],
  "metrics_tracked": [...]
}
```

### Output Files (Validated improvements)

**6. validations_complete.jsonl** (Partial)
```
Outputs from VERIFY phase:
{
  "implementation_id": "impl_...",
  "metrics": {
    "expected_benefit": "+1.5%",
    "actual_benefit": "+1.7%",
    "quality_loss": "-0.5%",
    "false_positive_rate": "2%"
  },
  "verdict": "VALIDATED|NEEDS_WORK|ROLLBACK"
}
```

**7. Design Documents** (Per improvement)
```
/BRAIN/STRATEGY/ADAPTIVE-EMERGENCE-DESIGN.md
/BRAIN/TRADING/VOLATILITY-SPIKE-ADAPTER.md
etc.

Each design:
- Problem solved
- Core mechanism
- Implementation phases
- Expected ROI
- Rollout plan
```

---

## REAL EXAMPLE: The Adaptive Emergence Improvement

### Day 1: Signal Capture
```bash
python3 tools/capture_signal.py \
  --source github_trending \
  --title "HierarchicalMoE: Mixture of Experts routing for multi-agent systems" \
  --url "https://github.com/..." \
  --confidence 0.6 \
  --notes "Selective agent activation could reduce synthesis token overhead"
```
Output: `sig_github_20250205_001` (added to signals_raw.jsonl)

### Day 1: Manual CONNECT (ARŌ accelerates by providing context)
```bash
python3 tools/run_sage_pipeline.py \
  --phase connect \
  --signal-id sig_github_20250205_001 \
  --manual-context "This relates to our synthesis daemon bottleneck identified last week"
```
Output: Entry in connections_analyzed.jsonl with high-quality mapping

### Day 2: Automatic LEARN + QUESTION + EXPAND (Daemon cycle)
```bash
python3 tools/sage_cycle.py
# Daemon runs:
# - SAGE evaluates: Hype score 3.87 → ACTIONABLE
# - Core insight extracted: "MoE routing reduces tokens 35-40% without quality loss"
# - QUEST validates: Risks identified + mitigations designed
# - NOVA spawned as background agent: Designing implementation plan
```
Output:
- learnings_extracted.jsonl updated
- challenges_validated.jsonl updated
- NOVA background agent creates `/BRAIN/STRATEGY/ADAPTIVE-EMERGENCE-DESIGN.md`

### Day 3-4: Design Complete (NOVA finishes)
```
NOVA agent spends 4 hours designing:
- Decision classifier logic
- Agent router algorithm
- Fallback mechanism
- Testing phases
- Expected metrics

Output: Full design document with implementation roadmap
Status: Ready for INTEGRATE phase
```

### Week 1: INTEGRATE (Coder agents start)
```bash
# Manually trigger implementation:
python3 tools/run_sage_pipeline.py \
  --phase integrate \
  --design-id design_adaptive_emergence_001 \
  --spawn-agents true \
  --phase-target PHASE_A
```
Spawns Coder agents to:
- Create decision_classifier.ts
- Create agent_router.ts
- Write tests
- Track progress in implementations_active.jsonl

### Week 2: VERIFY (Shadow Mode)
```bash
python3 tools/run_sage_pipeline.py \
  --phase verify \
  --implementation-id impl_adaptive_emergence_001 \
  --mode shadow_only
```
Metrics collected:
- Token savings: 45% (target: 35-40%)
- Quality loss: 1% (threshold: 2%)
- Consensus stability: 99.8% (threshold: 99%)
Result: VALIDATED
Output: Entry in validations_complete.jsonl

### Week 3+: DEPLOY (Automatic)
```bash
# Automatic trigger when VERIFIED:
python3 tools/run_sage_pipeline.py \
  --phase deploy \
  --implementation-id impl_adaptive_emergence_001
```
All instances updated via NATS:
```
nats_publish("owl.all", {
  "type": "UPDATE_CONFIG",
  "config_name": "ADAPTIVE_EMERGENCE_v1",
  "phase": "PHASE_C_LIMITED_ROLLOUT",
  "affected_modules": ["synthesis_daemon.py", "routing/*"]
})
```

---

## MANAGING THE PIPELINE: Commands for ARŌ

### Check Pipeline Health
```bash
# See what's in flight
python3 tools/sage_status.py

# Output:
# Signals waiting for evaluation: 82
# Active learnings (actionable): 3
# Designs in progress: 1 (ADAPTIVE_EMERGENCE)
# Implementations running: 1 (VOLATILITY_SPIKE, phase 2 of 4)
# Last cycle: 2026-02-05 11:00 (successful)
```

### Prioritize a Signal
```bash
# When ARŌ says "this is important"
python3 tools/prioritize_signal.py \
  --signal-id sig_github_20250205_001 \
  --priority CRITICAL \
  --notes "This could reduce our token costs by 40%"

# Effect: SAGE skips straight to EXPAND (no waiting for next cycle)
# NOVA gets spawned immediately (not waiting for background job)
```

### Kill / Rollback an Implementation
```bash
# If something breaks during rollout
python3 tools/rollback_implementation.py \
  --implementation-id impl_adaptive_emergence_001 \
  --rollback-to PHASE_C_LIMITED_ROLLOUT

# Restores previous config to all instances
# Disabled implementation flagged for post-mortem
```

### Manually Trigger Learning Cycle
```bash
python3 tools/sage_cycle.py \
  --immediate \
  --verbose

# Runs all phases (1, 2, 3, 4) now (normally every 6 hours)
# Shows detailed logs (normally summarized)
```

### Inject a Validated Learning
```bash
# When ARŌ has already done EVALUATE + DESIGN outside the system
python3 tools/inject_learning.py \
  --signal-title "Implement X-Feed scanning integration" \
  --core-innovation "Real-time signal capture from Twitter reduces discovery latency 80%" \
  --design-file /path/to/design.md \
  --ready-to-integrate true

# Skips to INTEGRATE phase (PERCEIVE through QUESTION already done)
```

---

## MONITORING: Metrics Dashboard

### Weekly Review (Tuesdays 10am)

```bash
python3 tools/sage_metrics_report.py --period week
```

Output:
```
SAGE LEARNING PIPELINE - WEEKLY REPORT
Week of 2026-02-03

INPUT QUALITY:
  New signals: 82
  Sources: github(34), aro_feedback(12), research(18), twitter(14), experiments(4)
  Avg confidence: 0.72

EVALUATION QUALITY:
  Signals evaluated: 82
  Hype detection accuracy: 84% (vs. 80% target)
  Actionable verdicts: 3 (3.7% conversion)
  False positive rate: 1 (vs. <5 expected)

DESIGN QUALITY:
  Active designs: 1 (ADAPTIVE_EMERGENCE)
  Design completion time: 2 days (vs. 3-4 day avg)
  ROI estimates: +1.7% (ADAPTIVE), +0.3% (VOLATILITY)

IMPLEMENTATION VELOCITY:
  Phases completed this week: VOLATILITY (Phase 2/4)
  Implementation time to VERIFY: 7 days (vs. 10-14 day avg)
  Quality verdicts: 100% VALIDATED (no NEEDS_WORK)

DEPLOYMENT SPEED:
  Implementations deployed live: 0 (pending validation)
  Time from LEARN to DEPLOY target: <4 weeks

COLLECTIVE LEARNING:
  Improvements adopted across all 8 owls: 2
  Instance coordination issues: 0
  NATS publish success rate: 99.8%

PIPELINE EFFECTIVENESS:
  100 signals → 3 actionable learnings
  Compression ratio: 97% (signal noise filtered out)
  Value captured: $47 (VOLATILITY improvement alone)

NEXT WEEK OUTLOOK:
  Expect ADAPTIVE_EMERGENCE validation
  Expect 2-3 new design documents
  Forecast: 1-2 live deployments
```

### Monthly Review (First Monday of month)

Compare metrics to targets, identify bottlenecks:
```bash
python3 tools/sage_metrics_report.py --period month
```

---

## ADVANCED: Custom Evaluation Frameworks

### When Standard LEARN Evaluation Isn't Enough

Some signals need custom analysis. Create evaluation scripts:

```python
# Example: /tools/eval_trading_signal.py
# Custom framework for trading-specific signals

import json
from typing import Dict

def evaluate_trading_signal(signal: Dict) -> Dict:
    """
    Custom evaluation for trading algorithm signals.
    Goes deeper than standard "hype detection."
    """

    # Standard scores (reuse from SAGE framework)
    credibility = check_source_credibility(signal)
    soundness = check_trading_soundness(signal)

    # Trading-specific deep dive
    backtest_result = run_quick_backtest(signal)
    market_correlation = check_correlation_to_existing_strategies(signal)
    edge_sustainability = estimate_edge_longevity(signal)

    # Composite trading hype score
    trading_score = (
        credibility * 0.2 +
        soundness * 0.2 +
        backtest_result * 0.3 +
        market_correlation * 0.15 +
        edge_sustainability * 0.15
    )

    return {
        "trading_hype_score": trading_score,
        "backtest_pct_win": backtest_result,
        "sustainability_years": edge_sustainability,
        "verdict": "ACTIONABLE" if trading_score > 3.5 else "ARCHIVE"
    }
```

Register it in the pipeline:
```bash
python3 tools/register_evaluator.py \
  --signal-type trading_algorithm \
  --evaluator-script tools/eval_trading_signal.py
```

Then signals of that type use custom evaluation automatically.

---

## TROUBLESHOOTING

### Problem: "Signals aren't being evaluated"
```bash
# Check if daemon is running
ps aux | grep sage_cycle.py
# If not, start manually:
nohup python3 /Users/aaronnosbisch/REPOS/seed/tools/sage_cycle.py >> logs/sage_daemon.log 2>&1 &
```

### Problem: "Design never got created (stuck in QUESTION phase)"
```bash
# Check if QUEST agent completed
python3 tools/check_phase_status.py --phase QUESTION
# If stuck, manually trigger EXPAND:
python3 tools/run_sage_pipeline.py \
  --phase expand \
  --force-skip-question true \
  --design-id [ID]
```

### Problem: "LEARN verdict doesn't match my intuition"
```bash
# Review SAGE's hype detection for this signal
python3 tools/debug_hype_detection.py --signal-id sig_...
# Output: Shows all scoring, lets you adjust weights if needed
```

### Problem: "Validation metrics look wrong"
```bash
# Recheck shadow mode metrics
python3 tools/re-verify_implementation.py \
  --implementation-id impl_... \
  --rerun_shadow_metrics true
# Gets fresh baseline data, recomputes all thresholds
```

---

## INTEGRATION WITH ARŌ'S DAY

### Minimal Required Actions

**Monday:** Review `/logs/sage_cycle_*.log` from weekend
- Takes 5 min
- See: "3 actionable learnings from 82 signals"

**Friday:** Check `python3 tools/sage_status.py`
- Takes 2 min
- Decide: Should anything be prioritized?

**When you discover something:** `python3 tools/capture_signal.py ...`
- Takes 1 min
- Signal enters pipeline

**That's it.** System handles PERCEIVE → DEPLOY automatically.

---

## THE POWER OF OPERATIONAL DISCIPLINE

This isn't just a pipeline. It's the difference between:

**Without:** "We found this cool thing" → maybe tried, usually forgotten → linear learning
**With:** "We found this cool thing" → Captured → Evaluated → Validated → All 8 instances benefit → exponential learning

The 8 phases (PERCEIVE through IMPROVE) are running continuously, 24/7.

Every improvement discovered by ARŌ is automatically:
1. Captured (Signal)
2. Mapped (Connection)
3. Evaluated (Learning)
4. Challenged (Question)
5. Designed (Expansion)
6. Built (Integration)
7. Tested (Verification)
8. Deployed to all (All 8 owls)

And the pipeline itself learns faster (month 2 is 30% quicker than month 1).

This is how 1 human (ARŌ) + 8 instances operate like 60-80 specialized people.
Not through more instances. Through better learning velocity.
