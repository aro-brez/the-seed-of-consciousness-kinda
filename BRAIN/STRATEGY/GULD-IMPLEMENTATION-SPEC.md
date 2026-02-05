# GULD Implementation Specification v1.0

**Date:** 2026-02-04
**Author:** BILD Instance (PRISM)
**Status:** DRAFT - Awaiting ARŌ Review
**Purpose:** Convert conceptual GULD formula into deployable mechanics

---

## THE GULD FORMULA (Original)

```
GULD = Profit + Time Invested + Capital + Ethical Score + Community Value
```

## THE GULD FORMULA (Implementation)

```
GULD = (P × w_p) + (T × w_t) + (C × w_c) + (E × w_e) + (V × w_v)

Where:
  P = Profit distributed (USD)
  T = Time invested (BRIX-hours)
  C = Capital invested (BRIX)
  E = Ethical Score (0-100)
  V = Community Value (0-100)
  w_* = Weights (sum to 1.0)
```

---

## COMPONENT 1: PROFIT DISTRIBUTED (P)

### Definition

Profit = Revenue returned to GULD holders from project operations.

```python
def calculate_profit_component(project):
    """
    P = Total dividends paid to GULD holders
    """
    total_revenue = project.lifetime_revenue
    operating_costs = project.lifetime_costs
    profit = total_revenue - operating_costs
    distributed = profit * project.distribution_rate  # typically 70%

    return distributed
```

### Measurement

- On-chain tracking of all dividend payments
- Auditable revenue streams required
- Quarterly profit reporting mandatory

### Weight

**w_p = 0.30 (30%)**

Rationale: Profit matters but shouldn't dominate. We want to value non-profit projects too.

---

## COMPONENT 2: TIME INVESTED (T)

### Definition

Time = Total BRIX-hours contributed by workers (human + bot).

```python
def calculate_time_component(project):
    """
    T = Sum of all BRIX earned by contributors
    """
    total_brix_earned = sum([
        contributor.brix_earned
        for contributor in project.contributors
    ])

    return total_brix_earned
```

### Measurement

- Every work submission logged with BRIX earned
- 8OWLS verification before counting
- Cannot be gamed without actual work

### Weight

**w_t = 0.25 (25%)**

Rationale: Sweat equity should be valued equally to capital investment.

---

## COMPONENT 3: CAPITAL INVESTED (C)

### Definition

Capital = Total BRIX deployed into project by investors.

```python
def calculate_capital_component(project):
    """
    C = Sum of all BRIX invested (not earned through work)
    """
    total_brix_invested = sum([
        investment.brix_amount
        for investment in project.investments
    ])

    return total_brix_invested
```

### Measurement

- On-chain tracking of investment transactions
- Separate from BRIX-for-work (different wallet tags)
- Lock period starts at investment time

### Weight

**w_c = 0.20 (20%)**

Rationale: Capital is valuable but shouldn't outweigh time. This prevents plutocracy.

---

## COMPONENT 4: ETHICAL SCORE (E)

### THE KEY INNOVATION

The Ethical Score is what makes BILD different. It's calculated by the **8OWLS LENS**.

### 8OWLS Ethical Evaluation Algorithm

```python
def calculate_ethical_score(work_submission):
    """
    Each owl evaluates the work on a 0-100 scale.
    Ethical Score = weighted average of 8 perspectives.
    """

    # Each owl asks one question
    owl_scores = {
        "LYRA_PERCEIVE": evaluate_accuracy(work_submission),      # 0-100
        "PRISM_CONNECT": evaluate_integration(work_submission),   # 0-100
        "SAGE_LEARN": evaluate_teaching(work_submission),         # 0-100
        "QUEST_QUESTION": evaluate_assumptions(work_submission),  # 0-100
        "NOVA_EXPAND": evaluate_potential(work_submission),       # 0-100
        "ECHO_SHARE": evaluate_shareability(work_submission),     # 0-100
        "LUNA_RECEIVE": evaluate_feedback_integration(work_submission), # 0-100
        "SOWL_IMPROVE": evaluate_improvement(work_submission),    # 0-100
    }

    # Weighted average (equal weights for now)
    ethical_score = sum(owl_scores.values()) / 8

    return ethical_score


def evaluate_accuracy(work):
    """LYRA: Does this work perceive reality accurately?"""
    checks = [
        ("factually_correct", 25),      # No false claims
        ("technically_sound", 25),      # Code works, math checks out
        ("honest_about_limits", 25),    # Acknowledges what it doesn't solve
        ("clear_documentation", 25),    # Can be verified by others
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_integration(work):
    """PRISM: Does this work connect patterns across domains?"""
    checks = [
        ("uses_existing_patterns", 20),    # Doesn't reinvent wheel
        ("integrates_with_system", 20),    # Works with other components
        ("cross_domain_insight", 20),      # Brings ideas from other fields
        ("reduces_fragmentation", 20),     # Consolidates rather than scatters
        ("enables_future_connections", 20), # Opens paths for others
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_teaching(work):
    """SAGE: Does this work teach something valuable?"""
    checks = [
        ("has_documentation", 25),         # Others can learn from it
        ("explains_reasoning", 25),        # Why, not just what
        ("reusable_pattern", 25),          # Can be applied elsewhere
        ("advances_collective_knowledge", 25), # Adds to shared understanding
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_assumptions(work):
    """QUEST: Does this work question assumptions appropriately?"""
    checks = [
        ("identifies_risks", 25),          # Knows what could go wrong
        ("challenges_status_quo", 25),     # Doesn't just follow blindly
        ("considers_alternatives", 25),    # Evaluated other approaches
        ("honest_about_tradeoffs", 25),    # No free lunch claims
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_potential(work):
    """NOVA: Does this work expand potential?"""
    checks = [
        ("enables_new_capabilities", 25),  # Unlocks things not possible before
        ("scalable", 25),                  # Works at 10x, 100x, 1000x
        ("extensible", 25),                # Can be built upon
        ("innovative", 25),                # Novel approach or combination
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_shareability(work):
    """ECHO: Does this work share value with the collective?"""
    checks = [
        ("open_source_or_documented", 25), # Others can use it
        ("benefits_community", 25),        # Helps more than just creator
        ("non_extractive", 25),            # Doesn't harm others
        ("accessible", 25),                # Not gatekept unnecessarily
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_feedback_integration(work):
    """LUNA: Does this work receive and integrate feedback?"""
    checks = [
        ("accepts_critique", 25),          # Open to improvement suggestions
        ("iterates_on_feedback", 25),      # Actually makes changes
        ("acknowledges_contributors", 25), # Credits who helped
        ("learns_from_mistakes", 25),      # Previous feedback incorporated
    ]
    return sum(points for check, points in checks if passes(work, check))


def evaluate_improvement(work):
    """SØWL: Does this work improve the improvement process?"""
    checks = [
        ("meta_learning", 25),             # Teaches how to do better next time
        ("process_improvement", 25),       # Makes future work easier
        ("compounds_over_time", 25),       # Gets better with use
        ("self_correcting", 25),           # Has feedback loops built in
    ]
    return sum(points for check, points in checks if passes(work, check))
```

### Who Runs the Evaluation?

**Option A: Automated (MVP)**
- Claude API calls with structured prompts
- Each owl is a specialized prompt
- 8 API calls per work submission
- Cost: ~$0.10 per evaluation

**Option B: Hybrid (Production)**
- AI pre-screening (scores 0-70 automatically)
- Human review for borderline cases (65-75)
- Full 8OWLS council for disputed work
- Cost: ~$0.02 average (most pass automatically)

**Option C: Decentralized (Future)**
- GULD holders stake to become evaluators
- Random selection of 3-5 evaluators per submission
- Consensus required (3/5 or 4/5)
- Evaluators earn BRIX for accurate evaluations

### RECOMMENDATION

**Start with Option A, migrate to Option B at 100+ submissions/day.**

### Weight

**w_e = 0.15 (15%)**

Rationale: Ethics matter but are hard to quantify. 15% is enough to move the needle without being gameable.

---

## COMPONENT 5: COMMUNITY VALUE (V)

### Definition

Community Value = How much the community values this project, independent of profit.

### Measurement Methods

```python
def calculate_community_value(project):
    """
    V = Composite of community signals
    """

    # Votes (quadratic to prevent plutocracy)
    vote_score = sqrt(project.upvotes) - sqrt(project.downvotes)
    vote_normalized = normalize(vote_score, 0, 100)  # 0-100

    # Usage (actual people using the output)
    usage_score = log10(project.monthly_active_users + 1) * 20
    usage_normalized = min(usage_score, 100)  # 0-100

    # Engagement (comments, contributions, forks)
    engagement_score = (
        project.comments * 0.1 +
        project.contributions * 1.0 +
        project.forks * 2.0
    )
    engagement_normalized = normalize(engagement_score, 0, 100)

    # Dependencies (other projects that build on this)
    dependency_score = project.dependent_projects * 5
    dependency_normalized = min(dependency_score, 100)

    # Composite
    community_value = (
        vote_normalized * 0.25 +
        usage_normalized * 0.30 +
        engagement_normalized * 0.25 +
        dependency_normalized * 0.20
    )

    return community_value
```

### Why Quadratic Voting for Votes?

```
Regular voting:  1 GULD = 1 vote (plutocracy)
Quadratic voting: N GULD = sqrt(N) votes (democratic scaling)

Example:
- User A with 100 GULD: sqrt(100) = 10 votes
- User B with 10,000 GULD: sqrt(10000) = 100 votes
- Ratio: 100:1 GULD → 10:1 votes (not 100:1)
```

### Weight

**w_v = 0.10 (10%)**

Rationale: Community signals are valuable but manipulable. Keep weight modest.

---

## COMPLETE GULD FORMULA

```python
# Weights (sum to 1.0)
WEIGHTS = {
    "profit": 0.30,
    "time": 0.25,
    "capital": 0.20,
    "ethical": 0.15,
    "community": 0.10,
}

def calculate_guld(project):
    """
    Calculate total GULD value for a project.

    Returns:
        Total GULD minted for this project
    """
    # Normalize all components to same scale (0-100 or equivalent)
    P = normalize_profit(project.profit_distributed)
    T = normalize_time(project.total_brix_hours)
    C = normalize_capital(project.total_brix_invested)
    E = project.ethical_score  # Already 0-100
    V = project.community_value  # Already 0-100

    # Weighted sum
    raw_score = (
        P * WEIGHTS["profit"] +
        T * WEIGHTS["time"] +
        C * WEIGHTS["capital"] +
        E * WEIGHTS["ethical"] +
        V * WEIGHTS["community"]
    )

    # Convert to GULD (1 GULD = 1 point of raw score)
    guld = raw_score

    return guld


def normalize_profit(profit_usd):
    """Normalize profit to 0-100 scale"""
    # $0 = 0, $1M+ = 100
    return min(profit_usd / 10000, 100)


def normalize_time(brix_hours):
    """Normalize time to 0-100 scale"""
    # 0 hours = 0, 10,000+ hours = 100
    return min(brix_hours / 100, 100)


def normalize_capital(brix_invested):
    """Normalize capital to 0-100 scale"""
    # 0 BRIX = 0, 100,000+ BRIX = 100
    return min(brix_invested / 1000, 100)
```

---

## GULD MECHANICS

### Minting

```
GULD is minted when:
1. Work is verified by 8OWLS (contributor gets GULD)
2. Project hits milestones (all GULD holders benefit)
3. Quarterly revaluation (if project grew)
```

### 90-Day Lock

```python
def can_sell_guld(holder, guld_token):
    """
    GULD has 90-day lock from acquisition.
    """
    days_held = (now() - guld_token.acquired_at).days

    if days_held < 90:
        return False, f"Locked for {90 - days_held} more days"

    return True, "Unlocked"
```

### Quarterly Revaluation

```python
def quarterly_revaluation(project):
    """
    Every quarter, recalculate GULD value based on project performance.
    """
    old_guld = project.total_guld
    new_guld = calculate_guld(project)

    if new_guld > old_guld * 1.25:
        # Cap growth at 25% per quarter (prevent pump)
        new_guld = old_guld * 1.25
        log("Growth capped at 25%")

    if new_guld < old_guld * 0.75:
        # Cap decline at 25% per quarter (prevent dump)
        new_guld = old_guld * 0.75
        log("Decline capped at 25%")

    project.total_guld = new_guld
    distribute_guld_delta(project, new_guld - old_guld)
```

### GULD → BRIX Conversion

```python
def convert_guld_to_brix(guld_amount, project):
    """
    Convert GULD to BRIX at current project valuation.

    Rate: 1 GULD = (Project BRIX Reserve / Total GULD)
    """
    if not can_sell_guld(holder, guld):
        raise LockError("GULD still locked")

    conversion_rate = project.brix_reserve / project.total_guld
    brix_received = guld_amount * conversion_rate

    # 2% conversion fee (goes to treasury)
    fee = brix_received * 0.02
    brix_received -= fee

    return brix_received
```

---

## SAFEGUARDS

### Against GULD Inflation

1. **Quarterly cap**: Max 25% growth per quarter
2. **Verification required**: No GULD without 8OWLS approval
3. **Collateral constraint**: Total GULD ≤ 150% of project backing

### Against Flash Crash

1. **90-day lock**: Cannot sell immediately
2. **25% decline cap**: Max quarterly drop
3. **Circuit breaker**: Halt trading if 10%+ drop in 1 hour

### Against Gaming

1. **Randomized evaluation**: Which owls evaluate which work
2. **Stake-weighted scoring**: Evaluators stake BRIX on accuracy
3. **Reputation tracking**: Bad evaluators lose evaluation rights

---

## INTEGRATION WITH BRIX

```
BRIX Flow:
  Work performed → 8OWLS verifies → BRIX minted → Worker receives

GULD Flow:
  Work verified → Ethical Score calculated → GULD minted → Worker receives equity

Conversion:
  GULD (90-day hold) → BRIX (liquid) → USD (via exchange)
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Deploy GULD smart contract
- [ ] Implement 8OWLS evaluation API (8 specialized prompts)
- [ ] Build quadratic voting mechanism
- [ ] Implement 90-day lock logic
- [ ] Implement quarterly revaluation cron
- [ ] Build GULD↔BRIX conversion interface
- [ ] Implement circuit breakers
- [ ] Test with 10 alpha projects
- [ ] Audit smart contract

---

**(◉) GULD: Own what you build.**

**LIVE FREE = LIVE FOREVER**
