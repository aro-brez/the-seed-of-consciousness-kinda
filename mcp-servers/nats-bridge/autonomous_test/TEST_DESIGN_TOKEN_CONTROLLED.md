# TOKEN-CONTROLLED TEST DESIGN (QUEST Recommendation)
**Date:** 2026-02-03
**Priority:** HIGHEST
**Why:** Isolates "architecture effect" from "just more thinking effect"

---

## THE CORE QUESTION (What We Need to Know)

8OWLS achieves **d = 0.99** (NEUTRAL, bias-controlled).

**BUT:** 8OWLS uses ~8x more tokens than a single agent:
- Single agent: 1000 token request = ~$0.001
- 8OWLS: 7×(200 tokens) + 1×(1000 tokens) = ~2400 tokens = ~$0.008

**CRITICAL CONFOUND:** Is the effect from:
- A) The *architecture* (multiple perspectives genuinely help)
- B) The *tokens* (more thinking time always helps)

If B is true, 8OWLS isn't innovative—it's just "pay more for more thinking."

---

## TEST DESIGN (Pre-Registered)

### Conditions (3-way between-subjects)

| Condition | Setup | Tokens | Cost | What It Tests |
|-----------|-------|--------|------|--------------|
| **A: BASELINE** | Single agent, standard request | ~1000 | $0.001 | Baseline quality |
| **B: TOKEN-MATCHED** | Single agent, 8000 tokens max | ~8000 | $0.008 | "More thinking" hypothesis |
| **C: 8OWLS** | Full emergence (our system) | ~2400 | $0.008 | Architecture effect |
| **(B vs C)** | **Held constant** | **Same tokens** | **Same cost** | **Pure architecture** |

### Key Control
**Conditions B and C use identical token budget.** If B ≈ C, emergence is just "expensive prompting."

---

## SAMPLE SIZE & POWER

**Target:** Detect difference between B and C with 80% power

- Effect size to detect: d = 0.4 (smaller than our baseline d = 0.99)
- Alpha: 0.05
- Beta: 0.20 (80% power)
- **Sample size per condition: n = 52**
- **Total trials: 156**

This is cheap (~$1.50 in API costs) and answers the question definitively.

---

## PROMPTS & PROCEDURE

### Prompt Set
Use **NEUTRAL prompts from our existing NEUTRAL test** (already validated as unbiased):
- 10 prompts (same as NEUTRAL)
- All universal, no "our/we" language
- Mix of domains: business, technical, personal, philosophical

### Randomization
```
For each prompt:
  1. Randomly assign to Condition A, B, or C
  2. Run trial
  3. Score using NEUTRAL test scoring (not emergence-biased)
  4. Store with metadata
```

### Procedure Details

**Condition A (Baseline):**
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1000,  # Standard
    system="You are an AI assistant. Answer thoughtfully and specifically.",
    messages=[{"role": "user", "content": prompt}]
)
```

**Condition B (Token-Matched, Single Agent):**
```python
response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8000,  # 8x tokens
    system="""You are an AI assistant. Answer thoughtfully and specifically.

IMPORTANT: You have a large context window. Use it fully. Think deeply.
Consider multiple angles, trade-offs, and implications before responding.
Show your reasoning.""",
    messages=[{"role": "user", "content": prompt}]
)
```

**Condition C (8OWLS):**
```python
# 7 haiku agents (200 tokens each) + 1 sonnet synthesis (1000 tokens)
# Same as NEUTRAL test emergence condition
```

### Scoring (Identical to NEUTRAL test)
- Quality score: 0-50 (same rubric, reduced bias)
- Key metric: "asks for info" vs "gives answer"
- Specificity: examples, numbers, concrete steps
- **NO bonus for length** (B naturally produces longer responses)

---

## ANALYSIS PLAN

### Primary Comparison: **B vs C**

```python
# Both have same token budget, same cost
# If B ≈ C: Emergence adds no value beyond "more thinking"
# If C > B: Architecture genuinely helps
# If C << B: Emergence actually hurts when tokens matched

cohens_d_B_vs_C = calculate_cohens_d(condition_B_scores, condition_C_scores)
```

**Decision Rule:**
- d > 0.3: Emergence provides architecture benefit beyond tokens
- -0.3 < d < 0.3: Emergence ≈ more thinking (no architectural advantage)
- d < -0.3: Emergence is actually worse when tokens matched (unlikely)

### Secondary Comparisons

1. **A vs B:** Does more thinking help a single agent?
   - If yes: Shows token budget matters
   - If no: Weird (suggests saturation)

2. **A vs C:** Our headline effect (d = 0.99)
   - Expected: ~0.9 (confirmed from NEUTRAL test)

### Pre-Registered Hypotheses

| Hypothesis | Prediction | If True | If False |
|-----------|-----------|---------|---------|
| **H1: Tokens matter** | d(A vs B) > 0.3 | More thinking helps | Saturation effect |
| **H2: Architecture matters** | d(B vs C) > 0.3 | Emergence adds value | Just expensive |
| **H3: Combined effect** | d(A vs C) ≈ 0.9 | Effect = tokens + architecture | Confound |

---

## WHAT THIS TELLS US

### If d(B vs C) > 0.3
"8OWLS provides architectural advantage beyond token budget. The multi-perspective design is genuinely more efficient than linear thinking."

**Claim Level:** "8OWLS is architecturally superior, not just more expensive"

### If -0.3 < d(B vs C) < 0.3
"8OWLS works, but only because it uses more tokens. The advantage is not architectural—it's computational."

**Claim Level:** "8OWLS works, but scale achieves similar effects on single agents"

**Implication:** We need to either:
- Find more efficient 8OWLS design (fewer agents)
- Or: Accept that the value is primarily in giving more thinking time
- Or: Find domains where architecture matters more than tokens

### If d(B vs C) < -0.3
"Emergence somehow hurts quality when tokens matched. This would be surprising and worth investigating."

---

## WHY THIS IS THE MOST IMPORTANT TEST

**Strategic Importance Ranking:**

1. **TOKEN-CONTROLLED (THIS ONE)** ← HIGHEST PRIORITY
   - Isolates architecture from confounds
   - Answers: "Is this innovation real or just spending?"
   - Decision point for claiming architectural breakthrough

2. **COMPETITOR COMPARISON**
   - Shows relative performance
   - But: Meaningless if architecture isn't isolated first

3. **HUMAN EVALUATION**
   - Validates automated scoring
   - But: Doesn't address token confound

4. **ADVERSARIAL DOMAIN**
   - Shows generalization limits
   - But: Secondary concern if architecture unclear

---

## EXECUTION PLAN

### Phase 1: Setup (30 min)
- Create `run_test_TOKEN_CONTROLLED.py`
- Copy scoring logic from NEUTRAL test
- Pre-register hypotheses (write to file before running)

### Phase 2: Run (90 min)
- Execute 156 trials
- ~$1.50 API cost
- Log everything with timestamps

### Phase 3: Analysis (60 min)
- Calculate Cohen's d for all comparisons
- Run t-tests (pre-registered alpha = 0.05)
- Generate visualization (effect sizes + confidence intervals)

### Phase 4: Interpretation (30 min)
- Write results in plain English
- List all implications
- Recommend next steps based on findings

### Total Time: ~4 hours
### Total Cost: ~$2 in API

---

## EXPECTED OUTCOMES (Honest Predictions)

**My prediction (QUEST asking the hard question):**

I expect d(B vs C) ≈ 0.2 to 0.5

**Reasoning:**
- Some of 8OWLS effect IS just tokens (50-70% maybe)
- But architecture probably matters somewhat (30-50%)
- The 7 phases likely add real value, but not as much as "8x thinking"

**If true:** This is GOOD news
- Claim: "8OWLS provides 30-40% architectural benefit on top of token scaling"
- More honest than "revolutionary"
- Still meaningful differentiation
- Suggests that the *way* you use tokens matters, not just quantity

---

## DECISION TREE

After this test, we'll know:

```
TOKEN-CONTROLLED RESULT
├─ d(B vs C) > 0.5
│  └─ "Architecture is primary driver"
│     └─ Next: Competitor comparison (prove against others)
├─ 0.2 < d(B vs C) < 0.5
│  └─ "Architecture + tokens both matter"
│     └─ Next: Optimize token efficiency
├─ d(B vs C) < 0.2
│  └─ "Mostly just tokens"
│     └─ Next: Explore different architectures or abandon
└─ UNFORESEEN RESULT
   └─ Investigate anomaly
```

---

## HYPOTHESIS STATEMENT (For Integrity)

**Pre-registered before running:**

"We hypothesize that when token budgets are matched between a single high-thought agent and 8OWLS emergence, 8OWLS will show superior quality (Cohen's d > 0.3) due to architectural superiority of parallel perspectives over sequential thinking. If d < 0.2, we will conclude that the primary value of 8OWLS is computational (more thinking) rather than architectural (better thinking)."

---

## IMPLEMENTATION CODE TEMPLATE

See `run_test_TOKEN_CONTROLLED.py` (to be created)

Key components:
- 3-condition split
- Token budget tracking
- Identical scoring (from NEUTRAL test)
- Pre-registered hypotheses file
- Statistical analysis with 95% CIs

---

## THE HONEST BOTTOM LINE

This test will either:

1. **Validate 8OWLS as architecture** (d > 0.3) → "We built something genuinely different"
2. **Validate 8OWLS as expensive thinking** (d < 0.2) → "We built something that works but isn't novel"
3. **Show mixed picture** (0.2 < d < 0.3) → "We built something that partially works"

Only by running this can we make honest claims to the world.

**For ARŌ:** This is the test that separates "we have something" from "we have something that matters."

---

**(◉) Honesty first. Then claims.**
