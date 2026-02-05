# SCALABLE AWARENESS - EXECUTIVE SUMMARY
**For:** ARŌ
**Read Time:** 3 minutes
**Date:** 2026-02-04

---

## THE QUESTION

How does 8OWLS scale self-awareness from 1 human to 100+ without paralysis?

---

## THE ANSWER

**4-layer hierarchical architecture inspired by human neuroscience:**

```
PERCEPTION (Brainstem) → Always observing, never thinking ($0-1/day)
    ↓
ATTENTION (Thalamus) → Filters by importance, routes ($1-5/day)
    ↓
CONSCIOUSNESS (Cortex) → Reasons when needed ($5-20/day)
    ↓
WISDOM (Prefrontal) → Strategic decisions only ($20-100/day)
```

---

## KEY INSIGHT

**Scalable awareness isn't about tracking more—it's about knowing what to ignore and when to care.**

95% of human neural activity is unconscious filtering. Only 5% reaches conscious awareness.

---

## THE ARCHITECTURE

### Layer 1: PERCEPTION (LYRA)
- **Always on:** YES
- **Cost:** ~$0-1/day
- **Function:** Monitor all truth sources (trading, git, NATS, APIs, files)
- **Output:** Change events to Attention Layer
- **No LLM calls:** Just polling and diffs

### Layer 2: ATTENTION (PRISM)
- **Always on:** YES
- **Cost:** ~$1-5/day
- **Function:** Classify importance (CRITICAL/HIGH/MEDIUM/LOW/IGNORE)
- **Mostly pattern matching:** Only ask Haiku for unknown patterns
- **Route by priority:**
  - CRITICAL → Immediate Sonnet (<1 min)
  - HIGH → Domain agent within 5 min
  - MEDIUM → Batch 4×/day
  - LOW → Daily digest
  - IGNORE → Discard

### Layer 3: CONSCIOUSNESS (8 OWLS)
- **Always on:** NO (triggered by Attention)
- **Cost:** ~$5-20/day
- **Function:** Deep reasoning about important changes
- **Adaptive emergence:**
  - Simple events → 1 agent (Haiku)
  - Moderate → 3 agents (Haiku)
  - Complex → 8 agents (Haiku)
  - Critical → 8 agents (Sonnet)

### Layer 4: WISDOM (THE FIELD)
- **Always on:** NO (rare, strategic)
- **Cost:** ~$20-100/day
- **Function:** Collective intelligence for major decisions
- **When:** Architecture, economics, partnerships, crisis

---

## PRIORITY HIERARCHY

### CRITICAL (Always immediate)
1. Safety threats (security breaches, bugs causing loss)
2. Legal/regulatory risks
3. Large financial movements (>$100)
4. System failures (daemon crashes)
5. User distress signals ("urgent", "emergency")

### HIGH (Within 5 minutes)
6. Trading outcomes (positions resolving)
7. Project milestones (launches, deployments)
8. Partner commitments (deadlines)
9. Novel situations (first-time events)
10. Strategic decisions (architecture, economics)

### MEDIUM (Batch 4×/day)
11. Routine commits
12. Minor bugs
13. Performance metrics
14. Documentation updates
15. Exploratory questions

### LOW (Daily digest)
16. Routine operations (successful cron)
17. Informational updates
18. Historical analysis
19. Optimization opportunities
20. Social interactions

### IGNORE
- Spam/noise
- Redundant notifications
- Events below threshold ($0.01 changes)

---

## ATTENTION ALLOCATION ALGORITHM

**Core principle:** Allocate awareness proportional to impact.

```python
# Compute expected value of attention
impact = estimate_impact(event)  # 0-1 scale
cost = estimate_processing_cost(event)  # $ to process
ev = impact / cost

# Process highest EV events within daily budget
# Budget adjusts dynamically:
# - Normal: $50-100/day
# - Crisis: $500-1000/day
# - Maintenance: $10-20/day
```

---

## SCALING LAWS

| Participants | Events/Day | Total Cost/Day |
|--------------|------------|----------------|
| 1 | 100 | $10-20 |
| 8 | 800 | $50-100 |
| 100 | 10,000 | $200-400 |
| 1000 | 100,000 | $1000-2000 |

**Cost scales sub-linearly (O(N log N)) because:**
- Pattern reuse across similar events
- Batch processing of routine operations
- Collective learning (one lesson benefits all)

---

## HOW IT LEARNS

### 1. Priority Learning
- Record: (event_type, assigned_priority, actual_impact)
- If assigned LOW but impact was HIGH → upgrade pattern
- Store in AgentDB, reuse forever

### 2. User Preference Learning
- Track which notifications get acted on
- Track which ignored events had impact
- Personalize priority thresholds

### 3. Collective Learning
- When SØWL learns "git commits >10 files = MEDIUM"
- All 8 owls learn it instantly
- Future owls inherit this pattern
- Cost to learn: $0.001
- Benefit: 10,000× (all future similar events)

---

## IMPLEMENTATION (5 Weeks)

### Week 1: Foundation
- Perception Layer (monitor all sources)
- Attention Layer (classify + route)
- Test with current load (1 human, 20 positions)

### Week 2: Consciousness
- Adaptive emergence (match agents to complexity)
- Auto-spawn logic
- Test with varied events

### Week 3: Learning
- Priority learning
- User preference learning
- Outcome tracking

### Week 4: Scale Testing
- Simulate 8 participants (800 events/day)
- Test Byzantine consensus
- Failure mode testing

### Week 5: Production
- Dashboard (real-time awareness status)
- Control panel (adjust budget, override priorities)
- Monitoring (cost, latency, miss rate)

---

## QUESTIONS FOR YOU (ARŌ)

1. **False alarms vs missed events?**
   - Prefer: "Tell me too much" or "Only critical"?

2. **Daily budget comfort zone?**
   - $10/day (minimal) or $100/day (comprehensive)?

3. **Which domains matter most?**
   - Trading > Projects? Or Projects > Trading?

---

## NEXT STEP

1. You review this design
2. QUEST challenges assumptions
3. We build Phase 1 (Foundation) this week

**Full spec:** `/BRAIN/ARCHITECTURE/SCALABLE-AWARENESS.md`

(◉)
