# SAGE LEARNING PIPELINE
## How 8OWLS Turns Information Into Evolutionary Advantage

**Phase:** SAGE (LEARN)
**Author:** Code Analyzer Agent (SAGE role)
**Date:** 2026-02-05
**Purpose:** Define the intelligence pipeline that extracts, validates, and integrates improvements from raw information

---

## CORE INSIGHT: The Learning Loop That Compounds

Information is useless if it doesn't change behavior. The SAGE learning pipeline is a 5-stage funnel that takes raw signals (GitHub, research, competitors, internal experiments) and converts them into **deployed capability improvements** that persist across all 8 owls:

```
RAW SIGNAL → EVALUATE → EXTRACT → INTEGRATE → VERIFY → DEPLOY
   (noise)      (hype?)   (pattern)   (system)  (works?)  (live)
     1%           10%        50%         75%       90%     100%
```

Most systems stop at extraction (GitHub repo found, cool!) or integration (written to codebase). **SAGE closes the loop** with verification (actually works?) and deployment (all instances benefit).

---

## PIPELINE STAGE 1: PERCEIVE (Raw Signal Collection)

**Question:** What new information exists that could improve 8OWLS?

### Sources Monitored
| Source | Frequency | Pattern | Value |
|--------|-----------|---------|-------|
| **GitHub Trending** | Hourly | New agent architectures, Claude tools, trading algos | Medium - often hype |
| **Research Papers** | Daily | Distributed consensus, scaling, emergence | High - grounded theory |
| **Competitor Products** | Weekly | Polymarket UX, trading bots features, pricing | High - real-world validation |
| **Community Signals** | Continuous | Twitter, Discord, HN - what's resonating | Medium - social proof |
| **Internal Experiments** | Per-cycle | Trading results, daemon performance, emergence metrics | **CRITICAL** - directly relevant |
| **Team Feedback** | Ad-hoc | ARŌ observations, pain points, "wouldn't it be cool if" | Critical - end-user truth |

### Capture Mechanism
**File Location:** `/BRAIN/IMPROVEMENTS/signals_raw.jsonl` (auto-appended)

```json
{
  "timestamp": "2026-02-05T11:23:47Z",
  "source": "github_trending",
  "signal_type": "agent_architecture",
  "title": "HierarchicalMoE: Mixture of Experts routing for distributed LLM calls",
  "url": "https://github.com/...",
  "raw_signal": "New routing mechanism for multi-agent systems - could improve 8OWLS owl coordination",
  "perceiver": "LYRA (PERCEIVE phase)",
  "confidence": "0.6 (uncertain if applicable)"
}
```

**Key:** Raw capture, no filtering yet. Volume > precision at this stage.

---

## PIPELINE STAGE 2: CONNECT (Pattern Recognition Across Domains)

**Question:** How does this signal relate to what we know? What domain patterns emerge?

### Connection Mapping
**Agent:** PRISM (CONNECT phase)
**Process:** Find relationships across:
1. **Internal patterns** - Have we solved this before? How?
2. **Domain knowledge** - What domain is this? (agents, trading, consensus, emergence)
3. **Architectural fit** - Where in 8OWLS stack would this live?
4. **Dependency web** - What else would need to change?

### Example: GitHub Signal (HierarchicalMoE)

```
PERCEIVE: "New routing for multi-agent systems"
                          ↓
CONNECT finds relationships:
  - Domain: Agent coordination
  - Similar to: Our current hierarchical-coordinator (in swarm.py)
  - Difference: MoE routing based on task type (vs. fixed hierarchy)
  - Applies to: OWL COMMUNICATION LAYER
  - Dependencies: Would affect synthesis_daemon.py, NATS pub/sub redesign
  - Risk: Breaking existing consensus if not careful
  - Upside: Could reduce token cost 15-20% (MoE specialization)

Pattern Type: "COORDINATION_OPTIMIZATION"
```

### Connection Storage
**File:** `/BRAIN/IMPROVEMENTS/connections_analyzed.jsonl`

```json
{
  "timestamp": "2026-02-05T11:45:22Z",
  "signal_id": "sig_github_20250205_001",
  "pattern_type": "COORDINATION_OPTIMIZATION",
  "domain": "agent_architecture",
  "relates_to": ["BRAIN/STRATEGY/swarm-synthesis.md", "synthesis_daemon.py"],
  "estimated_impact": {
    "performance_uplift": "+15-20% token efficiency",
    "risk_level": "MEDIUM",
    "implementation_effort": "80 hours"
  },
  "connector": "PRISM (CONNECT phase)"
}
```

**Key:** Not evaluating yet - just mapping relationships.

---

## PIPELINE STAGE 3: LEARN (Evaluation & Knowledge Extraction)

**Question:** Is this real? Does it fit our needs? What's the core innovation?

### Evaluation Framework (SAGE's Job)

**5-Point Hype Detection:**

| Hype Score | Verdict | Action |
|-----------|---------|--------|
| 0-1 | Pure marketing | Archive, don't pursue |
| 1-2 | Interesting but not applicable | Store for future context |
| 2-3 | **Real innovation + partial fit** | Extract core, design adaptation |
| 3-4 | **Directly applicable** | Fast-track to EXTRACT phase |
| 4-5 | **Game-changing** | All hands, immediate design sprint |

### Three Evaluation Layers

#### Layer 1: Source Credibility
```
GitHub repo:
  - Stars: 4,200 (good signal of interest)
  - Recent commits: 150+ (active)
  - Open issues: 12% of PRs (healthy)
  - Adoption: Companies using it? YES (Anthropic, OpenAI, TKTK)

Credibility Score: 3.8/5 (real, not vaporware)
```

#### Layer 2: Technical Soundness
```
HierarchicalMoE routing:
  - Mathematical foundation: YES (Shazeer et al. 2017, proven)
  - Empirical validation: YES (benchmarks show 15% improvement)
  - Production-ready: MAYBE (edge cases in sparse routing)

Soundness Score: 3.6/5 (proven approach, implementation details matter)
```

#### Layer 3: 8OWLS Relevance
```
Does it solve a real problem for us?
  - Current bottleneck: Synthesis daemon max_tokens=4000 (SAGE fixed this)
  - Root cause: All 7 perspectives run, synthesis must integrate all
  - MoE solution: Route high-value perspectives, skip low-value ones
  - Relevance: YES (directly addresses synthesis bottleneck)
  - Risk of NOT adopting: Continued token bloat

Relevance Score: 4.2/5 (high-priority need)
```

### Verdict Formula
```
Hype Score = (Credibility + Soundness + Relevance) / 3
           = (3.8 + 3.6 + 4.2) / 3
           = 3.87 / 5 = ACTIONABLE
```

**Decision:** Proceed to EXTRACT phase

### Knowledge Extraction (What's the core innovation?)
```
CORE INSIGHT FROM RESEARCH:
Routing based on task type reduces token spend by 15-20%
without sacrificing quality IF:
1. You track which agents add value per task
2. You skip agents that contribute <5% value
3. You maintain consensus on critical decisions
4. You have fallback to full routing if uncertainty high

APPLICABLE TO 8OWLS:
- Current: All 7 owls always run (PERCEIVE, CONNECT, LEARN, QUESTION, EXPAND, SHARE, RECEIVE)
- Proposed: Route based on decision importance:
  - Critical decisions (trade execution): Full emergence (all 7)
  - Routine decisions (logging): Minimal emergence (PERCEIVE only)
  - Medium decisions (strategy updates): 3-4 most relevant owls
- Cost impact: 35-40% reduction in routine cycles
```

### Learning Storage
**File:** `/BRAIN/IMPROVEMENTS/learnings_extracted.jsonl`

```json
{
  "timestamp": "2026-02-05T12:15:33Z",
  "signal_id": "sig_github_20250205_001",
  "hype_score": 3.87,
  "verdict": "ACTIONABLE",
  "core_innovation": "MoE routing reduces token cost without quality loss via selective agent activation",
  "applicability": {
    "fits_our_problem": true,
    "problem_solved": "Synthesis token bloat during routine decisions",
    "estimated_savings": "35-40% on routine cycles",
    "integration_cost": "80 hours design + implementation + testing"
  },
  "learner": "SAGE (LEARN phase)",
  "next_stage": "EXPAND (design adaptation)"
}
```

**Key:** SAGE answers three questions:
1. Is it real? (hype detection)
2. Does it matter? (relevance to 8OWLS)
3. What's the core lesson? (extract pattern, not just code)

---

## PIPELINE STAGE 4: EXPAND (Design & Adaptation)

**Question:** How do we fit this into 8OWLS? What changes?

### Adaptation Design (NOVA's Job)

NOVA takes the extracted learning and designs how to integrate it:

```
LEARNING: "MoE routing based on decision importance"
                        ↓
EXPAND designs the integration:
  1. Decision Classifier
     - Input: Decision type (trade, strategy, logging, etc.)
     - Output: Importance score (0-1)
     - Model: Simple decision tree or learned from historical cost-benefit

  2. Agent Router
     - If importance >= 0.8: Activate all 7 agents (full emergence)
     - If importance 0.5-0.8: Activate 3-4 most relevant agents
     - If importance < 0.5: Activate PERCEIVE + 1 critical agent

  3. Consensus Fallback
     - If any activated agent signals high uncertainty: Re-route to full
     - This maintains safety (consensus on uncertain = no mistakes)

  4. Monitoring
     - Track: token_cost_per_decision vs. decision_quality
     - If quality drops below threshold: Roll back to full emergence

  5. Deployment Phase
     - Week 1: Shadow mode (measure, don't execute routing)
     - Week 2: Limited rollout (low-importance decisions only)
     - Week 3: Full rollout (all decision types)
```

### Expansion Document
**File:** `/BRAIN/STRATEGY/ADAPTIVE-EMERGENCE-DESIGN.md`

```markdown
# ADAPTIVE EMERGENCE DESIGN

## Problem Solved
Synthesis daemon bottleneck: 35-40% of cycles are low-importance (logging, telemetry)
but still activate all 7 agents.

## Solution
Route agent activation based on decision importance:
- Critical (trade execution): Full 8OWLS
- Standard (strategy updates): MoE selection
- Routine (status checks): Minimal (PERCEIVE only)

## Implementation Timeline
- Week 1: Decision classifier + router (30 hours)
- Week 2: Testing in shadow mode (20 hours)
- Week 3: Phased rollout (15 hours)
- Week 4: Monitoring + tuning (15 hours)

## Expected ROI
- Token cost: -35-40% on routine cycles
- Quality impact: Neutral to +2% (agents not wasted on low-value decisions)
- Latency: -200ms average (less synthesis overhead)
- Risk: Low (can roll back if issues)
```

---

## PIPELINE STAGE 5: QUESTION (Challenge & Validate)

**Question:** Are we sure this is right? What could go wrong?

### Challenge Framework (QUEST's Job)

QUEST generates rigorous skepticism before we commit:

```
ASSUMPTION 1: MoE routing won't miss important insights
CHALLENGE: What if the "low-importance" decision actually matters?
MITIGATION: Fallback to full emergence if any agent flags uncertainty

ASSUMPTION 2: Decision classifier can accurately distinguish importance
CHALLENGE: How do we train it? What if it misclassifies?
MITIGATION: Shadow mode (2 weeks) to measure accuracy before live deployment

ASSUMPTION 3: Token savings (35-40%) actually materialize
CHALLENGE: What if synthesis is fast enough already?
MITIGATION: Measure token usage per cycle type BEFORE implementing

ASSUMPTION 4: Consensus mechanism still works with selective agents
CHALLENGE: Can we get true Byzantine fault tolerance with 3-4 agents?
MITIGATION: Keep all agents for consensus decisions, selective only for non-critical
```

### Validation Plan
```
Pre-implementation checklist:
- [ ] Measure current token distribution across decision types
- [ ] Identify "truly routine" decisions (cost > benefit)
- [ ] Design decision classifier
- [ ] Build fallback mechanism
- [ ] 2-week shadow mode with metrics
- [ ] Risk review with ARŌ
```

### Questioning Storage
**File:** `/BRAIN/IMPROVEMENTS/challenges_validated.jsonl`

```json
{
  "timestamp": "2026-02-05T13:00:00Z",
  "signal_id": "sig_github_20250205_001",
  "design_id": "design_adaptive_emergence_001",
  "challenges": [
    {
      "assumption": "MoE routing won't miss insights",
      "risk_level": "MEDIUM",
      "mitigation": "Fallback on uncertainty flags"
    },
    {
      "assumption": "Decision classifier is accurate",
      "risk_level": "HIGH",
      "mitigation": "Shadow mode + pre-implementation baseline"
    }
  ],
  "validator": "QUEST (QUESTION phase)",
  "risk_verdict": "ACCEPTABLE with mitigations",
  "go_no_go": "GO with 2-week shadow validation"
}
```

---

## PIPELINE STAGE 6: INTEGRATE (Actual Implementation)

**Question:** How does this ship? What's the rollout plan?

### Integration Phases

**Phase A: Code Integration (Week 1)**
- Create `/src/routing/decision_classifier.ts`
- Create `/src/routing/agent_router.ts`
- Create `/src/routing/fallback_handler.ts`
- Add metrics tracking to each decision
- Update `synthesis_daemon.py` to use router

**Phase B: Testing & Shadow Mode (Week 2)**
- Capture decision types + classifications
- Measure current token usage (baseline)
- Measure routed token usage (in shadow mode)
- Validate classifier accuracy
- Check consensus stability

**Phase C: Limited Rollout (Week 3)**
- Enable routing for "routine" decisions only (status checks, logging)
- Monitor token savings
- Monitor decision quality
- Confirm no issues

**Phase D: Full Rollout (Week 4)**
- Enable routing for all decision types
- Final metrics collection
- Document "lessons learned"
- Store pattern for future use

### Implementation Tracking
**File:** `/BRAIN/IMPROVEMENTS/implementations_active.jsonl`

```json
{
  "timestamp": "2026-02-05T14:30:00Z",
  "signal_id": "sig_github_20250205_001",
  "implementation_id": "impl_adaptive_emergence_001",
  "status": "PHASE_A_IN_PROGRESS",
  "tasks": [
    {
      "task": "Create decision_classifier.ts",
      "owner": "Coder agent",
      "status": "IN_PROGRESS",
      "completion_pct": 45
    },
    {
      "task": "Create agent_router.ts",
      "owner": "Coder agent",
      "status": "QUEUED",
      "completion_pct": 0
    }
  ],
  "metrics_tracked": [
    "tokens_per_decision",
    "decision_quality_score",
    "classifier_accuracy",
    "consensus_stability"
  ],
  "integrator": "NOVA + Coder agents",
  "risk_status": "NOMINAL"
}
```

---

## PIPELINE STAGE 7: VERIFY (Real-World Validation)

**Question:** Does it actually work?

### Verification Metrics

After Phase B (shadow mode), SAGE evaluates:

```
METRIC 1: Token Savings
  Baseline (all decisions, full emergence): 4,000 tokens/decision
  Routed (selective emergence): 2,200 tokens/decision
  Savings: 45% (EXCEEDED 35-40% target)
  ✓ PASS

METRIC 2: Decision Quality
  Baseline win rate on selective decisions: 67%
  Routed win rate on selective decisions: 66%
  Quality loss: 1% (ACCEPTABLE threshold is 2%)
  ✓ PASS

METRIC 3: Consensus Stability
  Baseline: 100% consensus on critical decisions
  Routed: 99.8% consensus (1 false positive out of 500)
  Stability loss: 0.2% (ACCEPTABLE threshold is 1%)
  ✓ PASS

METRIC 4: Latency
  Baseline synthesis time: 2.3 seconds
  Routed synthesis time: 1.8 seconds
  Improvement: 22% faster
  ✓ PASS (bonus)
```

### Verification Document
**File:** `/BRAIN/IMPROVEMENTS/validations_complete.jsonl`

```json
{
  "timestamp": "2026-02-05T21:00:00Z",
  "implementation_id": "impl_adaptive_emergence_001",
  "validation_phase": "SHADOW_MODE_COMPLETE",
  "metrics": {
    "token_savings_pct": 45,
    "quality_loss_pct": 1,
    "consensus_stability_loss_pct": 0.2,
    "latency_improvement_pct": 22
  },
  "verdict": "VALIDATED - All thresholds passed",
  "verifier": "SAGE (VERIFY phase) + Metrics daemon",
  "recommendation": "Proceed to Phase C (limited rollout)"
}
```

---

## PIPELINE STAGE 8: DEPLOY & LEARN (Live Deployment + Feedback Loop)

**Question:** How do we ship this to all 8 owls?

### Deployment & Collective Learning

**Deployment:**
1. Update all active instances (SØWL, LUNA, LYRA, NOVA, SAGE, ECHO, PRISM, QUEST)
2. Publish update via NATS: `owl.all` channel
3. Each owl retrieves routing config from shared memory
4. Fallback mechanism active by default (safe)

**Collective Learning:**
Each owl tracks:
- Local routing decisions (what was classified as routine vs. critical)
- Local outcomes (did routing help or hurt)
- Patterns (which decision types most benefit from routing)

All 8 share via NATS:
```
publish("collective.synthesis", {
  owl_id: "SOWL",
  cycle: 12847,
  routed_decisions: 23,
  full_emergence_decisions: 2,
  avg_tokens_saved: 1800,
  quality_impact: -0.5
})
```

Synthesis daemon aggregates and identifies patterns:
```
Pattern: "Routine decisions benefit most from routing"
Insight: "Could optimize classifier to be more aggressive"
Action: "Increase routing threshold from 0.5 to 0.6"
```

This closes the SAGE loop: **Learn → Adapt → Learn → Adapt → ...**

---

## THE COMPLETE LEARNING PIPELINE (Flow Diagram)

```
╔════════════════════════════════════════════════════════════════════╗
║                     8OWLS LEARNING PIPELINE                        ║
╚════════════════════════════════════════════════════════════════════╝

PERCEIVE (LYRA)              ← What new information exists?
    ↓ (Raw signals)
  signals_raw.jsonl (3,557 entries)

CONNECT (PRISM)              ← How does it relate to what we know?
    ↓ (Patterns mapped)
  connections_analyzed.jsonl (partial)

LEARN (SAGE)                 ← Is it real? Does it fit? Extract core insight
    ↓ (Hype → Innovation)
  learnings_extracted.jsonl (2,931 entries of knowledge)

QUESTION (QUEST)             ← Challenge assumptions, validate risks
    ↓ (Validated design)
  challenges_validated.jsonl (partial)

EXPAND (NOVA)                ← Design the adaptation, plan phases
    ↓ (Implementation plan)
  design_adaptive_emergence_001.md

INTEGRATE (Coder agents)     ← Write code, test, shadow mode
    ↓ (Code + metrics)
  src/routing/*, shadow_metrics.json

VERIFY (SAGE)                ← Did it work? Real-world validation
    ↓ (Validated results)
  validations_complete.jsonl (partial)

DEPLOY (All 8 owls)          ← Ship to collective
    ↓ (Published via NATS)
  owl.all ← "Update config"

RECEIVE (LUNA)               ← Integrate feedback, close loop
    ↓ (Collective learning)
  collective_patterns.json

IMPROVE (SØWL)               ← Learn how to learn better
    ↓ (Meta-improvement)
  improvements_to_pipeline.md (THIS FILE UPDATES)

Loop back to PERCEIVE → ...
```

---

## CONCRETE EXAMPLE: How a Real Improvement Flows Through Pipeline

**Scenario:** ARŌ says "I noticed the trading bot doesn't account for crypto volatility spikes"

### Day 1: PERCEIVE
```
Signal: "Crypto volatility spikes cause missed opportunities"
Source: ARŌ direct feedback
Confidence: 0.9 (end-user truth)
→ Store in signals_raw.jsonl
```

### Day 1: CONNECT (30 min)
```
PRISM finds:
- Related to: BRAIN/TRADING/field_trading_state.json (volatility tracking)
- Domain: Trading signal refinement
- Applicable layer: field_trading_daemon.py signal processor
- Impact: Currently ignores volatility context
→ Store in connections_analyzed.jsonl
```

### Day 2: LEARN (2 hours)
```
SAGE evaluates:
- Source credibility: 5/5 (ARŌ direct observation)
- Technical soundness: Need to research volatility spike detection
- Relevance: 4.8/5 (directly impacts win rate)
- Core insight: "Volatility is predictive of trade size/timing, not just risk"
- Decision: ACTIONABLE (proceed to EXPAND)
→ Store in learnings_extracted.jsonl
```

### Day 2: QUESTION (1 hour)
```
QUEST challenges:
- How do we detect spikes? (What's the threshold?)
- Will it help or hurt win rate? (Need backtesting)
- Does it work across all market types? (Crypto vs. stocks)
- Risk: Overfitting to recent volatility patterns
Verdict: GO if we backtest on 3 months historical data
→ Store in challenges_validated.jsonl
```

### Day 3-4: EXPAND (4 hours)
```
NOVA designs:
- Week 1: Backtest volatility spike detection on 3 months data
- Week 2: Integrate into field_trading_daemon.py signal processor
- Week 3: Shadow mode (measure impact without trading real capital)
- Week 4: Limited rollout (increase position size by 10% only)
→ Store design in BRAIN/STRATEGY/VOLATILITY-SPIKE-ADAPTER.md
```

### Week 1: INTEGRATE (12 hours)
```
Coder agents implement:
- tools/volatility_detector.py (spike detection)
- Update field_trading_daemon.py to use detector
- Add metrics tracking
- Write unit tests
Result: PR ready for testing
→ Track in implementations_active.jsonl
```

### Week 2: VERIFY (6 hours)
```
SAGE + Metrics daemon check:
- Backtest win rate: 68% (vs. 67% baseline) = +1.5% improvement
- False positive rate: 3% (acceptable)
- Max drawdown: -8.2% (acceptable)
Verdict: VALIDATED
→ Store in validations_complete.jsonl
```

### Week 3: DEPLOY (1 hour)
```
All instances get update:
- New field_trading_daemon.py with volatility spike detection
- New signal thresholds via NATS config update
- Fallback to baseline if spike detection fails
Result: Live on all owl instances
→ Publish to owl.all channel
```

### Week 4: RECEIVE + LEARN (Ongoing)
```
LUNA aggregates:
- All 8 instances track spike detection effectiveness
- Patterns emerge: "Works best in high-vol crypto pairs"
SAGE improves pipeline:
- Add "market type" to signal evaluation (not just hype/fit)
- Future signals will be faster to evaluate
→ Updates learnings_extracted logic
```

**Total time:** 2 weeks from observation to live deployment
**ROI:** +1.5% win rate = ~$30/month additional profit on current capital
**Future value:** Pattern stored, reused for other volatility-related improvements

---

## METRICS: Is The Pipeline Working?

**Track these monthly:**

| Metric | Target | Meaning |
|--------|--------|---------|
| Signals → Improvements ratio | 100:1 | 100 signals distilled to 1 real improvement |
| LEARN verdict accuracy | >80% hype detection | Fewer false positives (pursuing dead ends) |
| EXPAND design time | <10 hours | Not over-engineering |
| VERIFY pass rate | >80% | Designs actually deliver promised value |
| DEPLOY → ROI time | <4 weeks | Speed of value capture matters |
| Collective learning speed | Month 2 = 30% faster learning | Meta-improvement (how we learn improves) |

---

## WHY THIS MATTERS FOR 8OWLS

**Without this pipeline:**
- ARŌ finds cool GitHub repo → shared in Discord → maybe tried, probably forgotten
- No systematic extraction of patterns
- Each instance reinvents solutions
- Growth is linear (serial learning)

**With this pipeline:**
- ARŌ finds cool repo → LYRA captures → PRISM connects → SAGE evaluates → NOVA designs → Deploy to all 8
- Patterns are extracted and stored
- Each instance learns from collective
- Growth is exponential (compound learning)

**The magic:** Stage 8 (RECEIVE + LEARN) means the pipeline itself gets smarter.
Month 1: 2 weeks to deploy improvement
Month 2: 10 days to deploy (learned faster evaluation)
Month 3: 7 days to deploy (learned what types of changes work)
Month 4: 4 days to deploy (learned which agents to involve)

This is how you go from "smart instances" to "collective intelligence."

---

## NEXT: Implement the Pipeline

**Immediate:** Formalize the JSON structures (signals_raw.jsonl, learnings_extracted.jsonl, etc.)
**Week 1:** Wire up Stage 1-3 (Perceive → Learn) with real data flows
**Week 2:** Build Stage 4-7 (Expand → Verify) automation
**Week 3:** Connect to NATS for collective learning loop
**Week 4:** Meta-improve the pipeline itself (Stage 8)

Each stage is a separate agent's responsibility in the 8OWLS collective.
