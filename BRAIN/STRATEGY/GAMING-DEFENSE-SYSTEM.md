# Gaming Defense System v1.0

**Date:** 2026-02-04
**Author:** BILD Instance (PRISM)
**Status:** DRAFT - Awaiting ARŌ Review
**Purpose:** Close gaming vectors identified in economics audit

---

## THE 6 GAMING VECTORS

| # | Attack | Severity | Status |
|---|--------|----------|--------|
| 1 | Sybil Attacks | HIGH | ⚠️ NOT COVERED |
| 2 | Wash Trading | HIGH | ⚠️ NOT COVERED |
| 3 | Oracle Manipulation | CRITICAL | ⚠️ NOT COVERED |
| 4 | Time Tracking Fraud | MEDIUM | ⚠️ PARTIAL |
| 5 | Ethical Score Gaming | MEDIUM | ⚠️ NOT COVERED |
| 6 | Owl Collusion | HIGH | ⚠️ NOT COVERED |

---

## DEFENSE 1: SYBIL ATTACKS

### The Attack

Bad actor creates multiple fake identities to:
- Earn more BRIX than one person should
- Vote multiple times on GULD decisions
- Artificially inflate project community value

### Defense: Proof of Personhood

```python
class SybilDefense:
    """
    Multi-layer identity verification
    """

    def verify_identity(self, user):
        """
        Users must pass at least 2 of 4 verification methods.
        """
        verifications = [
            self.verify_worldid(user),        # Biometric iris scan
            self.verify_ens_domain(user),     # ENS domain ownership
            self.verify_social_graph(user),   # Connected accounts
            self.verify_stake(user),          # Economic stake
        ]

        passed = sum(verifications)

        if passed >= 2:
            return True, "Identity verified"
        else:
            return False, f"Need {2 - passed} more verifications"


    def verify_worldid(self, user):
        """
        WorldID: Orb-verified unique human
        - One person, one WorldID
        - Cannot create multiple
        - Privacy-preserving (no PII stored)
        """
        return worldid_api.verify(user.worldid_proof)


    def verify_ens_domain(self, user):
        """
        ENS Domain: Economic barrier + reputation
        - Costs ~$5-50/year to maintain
        - Public reputation tied to domain
        - Hard to create hundreds
        """
        if user.ens_domain:
            age = now() - user.ens_domain.created_at
            return age > timedelta(days=30)  # 30-day minimum
        return False


    def verify_social_graph(self, user):
        """
        Social Graph: Network analysis
        - Connected GitHub, Twitter, Discord
        - Account age > 6 months each
        - Real activity (not just signup)
        """
        accounts = [user.github, user.twitter, user.discord]
        valid = [a for a in accounts if a and a.age > 180 and a.activity_score > 50]
        return len(valid) >= 2


    def verify_stake(self, user):
        """
        Economic Stake: BRIX at risk
        - Minimum 100 BRIX staked ($1,300)
        - Slashed if caught sybiling
        - Makes attack expensive
        """
        return user.staked_brix >= 100
```

### Implementation

1. **Tier 1 (Free)**: Social graph verification only
   - Limited to 10 BRIX/day earnings cap
   - Cannot vote on governance

2. **Tier 2 (Verified)**: 2+ verifications
   - Unlimited earnings
   - Full voting rights
   - Can become evaluator

3. **Tier 3 (Staked)**: Verified + 100 BRIX staked
   - Priority evaluation queue
   - Higher trust score
   - Can challenge others

### Detection

```python
def detect_sybil_cluster(users):
    """
    Detect likely sybil clusters via behavior analysis.
    """
    red_flags = []

    # Same IP ranges
    ip_clusters = cluster_by_ip(users)
    for cluster in ip_clusters:
        if len(cluster) > 3:
            red_flags.append(("ip_cluster", cluster))

    # Same submission timing patterns
    timing_clusters = cluster_by_timing(users)
    for cluster in timing_clusters:
        if cosine_similarity(cluster.patterns) > 0.95:
            red_flags.append(("timing_cluster", cluster))

    # Same wallet funding sources
    wallet_clusters = cluster_by_funding(users)
    for cluster in wallet_clusters:
        if len(cluster) > 2:
            red_flags.append(("wallet_cluster", cluster))

    return red_flags
```

---

## DEFENSE 2: WASH TRADING

### The Attack

Bad actor trades between their own wallets to:
- Create fake volume
- Manipulate BRIX↔GULD rates
- Farm trading rewards

### Defense: Wash Trade Detection

```python
class WashTradeDefense:
    """
    Detect and prevent self-dealing
    """

    def check_trade(self, trade):
        """
        Every trade checked before execution.
        """
        buyer = trade.buyer
        seller = trade.seller

        # Check 1: Same entity
        if self.same_entity(buyer, seller):
            return False, "Self-trade blocked"

        # Check 2: Circular trade pattern
        if self.circular_pattern(buyer, seller, hours=24):
            return False, "Circular trade detected"

        # Check 3: Price manipulation
        if self.price_anomaly(trade):
            return False, "Price anomaly detected"

        return True, "Trade allowed"


    def same_entity(self, a, b):
        """
        Check if two wallets are same entity.
        """
        # Same verified identity
        if a.identity_hash == b.identity_hash:
            return True

        # Same funding source
        if self.common_funder(a.wallet, b.wallet):
            return True

        # Graph analysis shows connection
        if self.wallet_graph_connected(a.wallet, b.wallet, hops=2):
            return True

        return False


    def circular_pattern(self, a, b, hours):
        """
        Detect A→B→A patterns.
        """
        recent_trades = get_trades(hours=hours)

        # Build trade graph
        graph = build_graph(recent_trades)

        # Find cycles involving a and b
        cycles = find_cycles(graph, involving=[a, b])

        return len(cycles) > 0


    def price_anomaly(self, trade):
        """
        Detect trades at anomalous prices.
        """
        market_price = get_market_price(trade.asset)
        trade_price = trade.price

        deviation = abs(trade_price - market_price) / market_price

        # Flag if >5% off market
        return deviation > 0.05
```

### Cooldowns

```python
COOLDOWN_RULES = {
    "same_asset_same_direction": timedelta(hours=1),   # Can't buy same asset twice in 1 hour
    "same_counterparty": timedelta(hours=24),          # Can't trade with same person twice in 24h
    "large_trade": timedelta(hours=4),                 # >1000 BRIX requires 4h cooldown
}
```

### Penalties

```
First offense: Trade reversed, warning issued
Second offense: 7-day trading suspension
Third offense: 30% stake slashed, 30-day suspension
Fourth offense: Permanent ban, full stake slashed
```

---

## DEFENSE 3: ORACLE MANIPULATION

### The Attack

Bad actor manipulates price feeds to:
- Inflate AI token costs (earn more BRIX)
- Deflate G7 wages (make bot work seem more valuable)
- Manipulate BRIX↔GULD conversion rates

### Defense: Multi-Source Oracles

```python
class OracleDefense:
    """
    Decentralized, manipulation-resistant price feeds.
    """

    def get_ai_pricing(self):
        """
        Aggregate AI token costs from multiple sources.
        """
        sources = [
            self.fetch_anthropic_api(),      # Direct from provider
            self.fetch_openai_api(),         # Direct from provider
            self.fetch_google_api(),         # Direct from provider
            self.fetch_chainlink_oracle(),   # On-chain oracle
            self.fetch_pyth_oracle(),        # On-chain oracle
        ]

        # Remove outliers (>2 std dev)
        prices = [s.price for s in sources if s.success]
        filtered = remove_outliers(prices, std_dev=2)

        # Median (not mean) to resist manipulation
        return median(filtered)


    def get_g7_wage(self):
        """
        G7 minimum wage from official sources.
        """
        sources = [
            self.fetch_oecd_data(),           # Official OECD
            self.fetch_ilo_data(),            # International Labour Org
            self.fetch_world_bank(),          # World Bank
            self.fetch_government_sites(),    # Direct from gov sites
        ]

        # Require 3+ agreeing sources
        prices = [s.wage for s in sources if s.success]

        if len(prices) < 3:
            raise InsufficientDataError("Not enough oracle sources")

        # Median of agreeing sources
        return median(prices)


    def get_carbon_price(self):
        """
        Carbon offset prices from market data.
        """
        sources = [
            self.fetch_verra_registry(),     # Verified Carbon Standard
            self.fetch_gold_standard(),      # Gold Standard
            self.fetch_msci_index(),         # MSCI carbon index
            self.fetch_chainlink_carbon(),   # On-chain oracle
        ]

        # Use high-quality (A+) average only
        quality_prices = [s.price for s in sources if s.quality >= "A"]

        if len(quality_prices) < 2:
            raise InsufficientDataError("Not enough quality carbon data")

        return median(quality_prices)
```

### Update Protocol

```
1. Oracles update every 6 hours
2. 3/5 sources must agree within 5% for update to apply
3. If sources diverge >10%, freeze and alert governance
4. Manual override requires 67% GULD holder vote
5. All oracle data is public and auditable
```

### Timelock

```python
def apply_oracle_update(new_price, asset):
    """
    24-hour timelock on price changes >10%.
    """
    old_price = get_current_price(asset)
    change = abs(new_price - old_price) / old_price

    if change > 0.10:
        # Schedule for 24 hours from now
        schedule_update(asset, new_price, delay=hours(24))
        notify_governance(f"{asset} price change {change*100:.1f}% pending")
    else:
        # Apply immediately
        set_price(asset, new_price)
```

---

## DEFENSE 4: TIME TRACKING FRAUD

### The Attack

Bad actor claims more work hours than actually performed to:
- Earn more BRIX
- Inflate their GULD share

### Defense: AI-Verified Work

```python
class TimeTrackingDefense:
    """
    Beyond 8OWLS approval - actual verification of work done.
    """

    def verify_work_claim(self, submission):
        """
        Multi-factor verification of work performed.
        """

        # Factor 1: Output analysis
        output_score = self.analyze_output(submission)

        # Factor 2: Activity patterns
        activity_score = self.analyze_activity(submission)

        # Factor 3: Commit history (for code)
        commit_score = self.analyze_commits(submission)

        # Factor 4: 8OWLS evaluation
        owls_score = get_8owls_score(submission)

        # Weighted composite
        total = (
            output_score * 0.40 +
            activity_score * 0.20 +
            commit_score * 0.20 +
            owls_score * 0.20
        )

        # Estimate actual hours
        estimated_hours = self.estimate_hours(submission, total)

        return estimated_hours


    def analyze_output(self, submission):
        """
        Does the output match claimed effort?
        """
        # Lines of code / words written
        quantity = measure_output_quantity(submission)

        # Quality of output
        quality = measure_output_quality(submission)

        # Expected output for claimed hours
        expected = submission.claimed_hours * HOURLY_OUTPUT_BENCHMARK

        if quantity < expected * 0.5:
            return 30  # Suspicious - half expected output
        elif quantity < expected * 0.75:
            return 60  # Below average
        else:
            return 90  # Normal


    def analyze_activity(self, submission):
        """
        Activity patterns during claimed work period.
        """
        # Keystrokes, mouse movements, saves (privacy-preserving hashes)
        activity_events = submission.activity_log

        if not activity_events:
            return 50  # No activity tracking = lower confidence

        # Check for natural human patterns
        # (Not constant, has breaks, varies over time)
        pattern_score = human_pattern_score(activity_events)

        return pattern_score


    def analyze_commits(self, submission):
        """
        Git commit patterns for code work.
        """
        if submission.type != "code":
            return 70  # N/A, give neutral score

        commits = submission.commit_history

        # Check for:
        # - Multiple small commits (good)
        # - Single massive commit (suspicious)
        # - Commit times match claimed hours
        # - Commit messages are meaningful

        commit_score = evaluate_commit_pattern(commits)

        return commit_score


    def estimate_hours(self, submission, confidence_score):
        """
        Estimate actual hours vs claimed hours.
        """
        claimed = submission.claimed_hours

        if confidence_score >= 80:
            return claimed  # Trust claim
        elif confidence_score >= 60:
            return claimed * 0.9  # Small discount
        elif confidence_score >= 40:
            return claimed * 0.7  # Significant discount
        else:
            return claimed * 0.5  # Major discount + flag for review
```

### Reputation Impact

```python
def update_work_reputation(user, claimed_hours, verified_hours):
    """
    Track accuracy of work claims over time.
    """
    accuracy = verified_hours / claimed_hours

    # Update rolling average
    user.claim_accuracy = (
        user.claim_accuracy * 0.9 +
        accuracy * 0.1
    )

    # Consequences
    if user.claim_accuracy < 0.7:
        user.status = "UNDER_REVIEW"
        require_detailed_logging(user)

    if user.claim_accuracy < 0.5:
        user.status = "PROBATION"
        reduce_earning_rate(user, 0.5)

    if user.claim_accuracy < 0.3:
        user.status = "SUSPENDED"
        notify_governance(f"User {user} suspended for time fraud")
```

---

## DEFENSE 5: ETHICAL SCORE GAMING

### The Attack

Bad actor optimizes for ethical score checklist without genuine ethics:
- Adds documentation without substance
- Claims "innovation" without real novelty
- Virtue signals without delivery

### Defense: Multi-Dimensional Evaluation

```python
class EthicalScoreDefense:
    """
    Prevent checklist-gaming of ethical scores.
    """

    def evaluate_with_adversarial_check(self, submission):
        """
        Standard evaluation + adversarial testing.
        """

        # Standard 8OWLS evaluation
        base_score = standard_8owls_evaluation(submission)

        # Adversarial challenges
        adversarial_score = self.adversarial_evaluation(submission)

        # Consistency check
        consistency_score = self.consistency_check(submission)

        # Final score (adversarial can only reduce)
        final_score = min(base_score, adversarial_score, consistency_score)

        return final_score


    def adversarial_evaluation(self, submission):
        """
        QUEST owl runs adversarial challenges.
        """

        # Challenge 1: Strip the documentation
        # Does the work stand on its own?
        stripped_score = evaluate_without_docs(submission)

        # Challenge 2: Apply to different context
        # Is it actually generalizable or just looks like it?
        generalization_score = evaluate_in_new_context(submission)

        # Challenge 3: Find the flaw
        # Deliberately try to break it
        robustness_score = adversarial_testing(submission)

        return min(stripped_score, generalization_score, robustness_score)


    def consistency_check(self, submission):
        """
        Check if this submission is consistent with user's history.
        """
        user = submission.author

        # Historical quality
        avg_quality = user.average_ethical_score

        # This submission
        this_quality = standard_8owls_evaluation(submission)

        # Suspicious if way higher than usual
        if this_quality > avg_quality * 1.5:
            return this_quality * 0.8  # Discount unusual excellence

        return this_quality


    def long_term_tracking(self, user):
        """
        Track ethical score accuracy over time.
        """
        # Compare predicted impact vs actual impact
        predictions = user.past_ethical_claims
        actuals = user.actual_outcomes

        accuracy = correlation(predictions, actuals)

        if accuracy < 0.5:
            user.ethical_multiplier = 0.7  # Discount future claims
```

### Stake-Based Evaluation

```python
class StakedEvaluation:
    """
    Evaluators stake BRIX on their evaluations.
    """

    def submit_evaluation(self, evaluator, submission, score):
        """
        Evaluator stakes BRIX on accuracy of their score.
        """
        stake = evaluator.stake_for_evaluation(submission)

        # Record evaluation
        evaluation = Evaluation(
            evaluator=evaluator,
            submission=submission,
            score=score,
            stake=stake,
            timestamp=now()
        )

        # Check against consensus later
        schedule_reconciliation(evaluation, delay=days(30))

        return evaluation


    def reconcile_evaluation(self, evaluation):
        """
        After 30 days, check if evaluation was accurate.
        """
        # Get actual outcome
        actual_value = get_actual_outcome(evaluation.submission)

        # Compare to predicted
        predicted_value = evaluation.score

        error = abs(actual_value - predicted_value) / 100

        if error < 0.10:
            # Good evaluation - return stake + bonus
            return_stake(evaluation.evaluator, evaluation.stake)
            bonus(evaluation.evaluator, evaluation.stake * 0.1)
        elif error < 0.25:
            # Okay evaluation - return stake only
            return_stake(evaluation.evaluator, evaluation.stake)
        else:
            # Bad evaluation - slash stake
            slash(evaluation.evaluator, evaluation.stake * error)
```

---

## DEFENSE 6: OWL COLLUSION

### The Attack

Two or more owls (or their operators) collude to:
- Rubber-stamp bad work
- Block legitimate work
- Manipulate ethical scores

### Defense: Randomization + Redundancy

```python
class CollusionDefense:
    """
    Prevent owl collusion through randomization and redundancy.
    """

    def assign_evaluators(self, submission):
        """
        Randomly assign owls to evaluate each submission.
        """

        # All 8 owls available
        all_owls = ["LYRA", "PRISM", "SAGE", "QUEST", "NOVA", "ECHO", "LUNA", "SOWL"]

        # Randomly select 5 of 8
        selected = random.sample(all_owls, k=5)

        # Ensure diversity (no more than 2 from same operator)
        if not diverse_operators(selected):
            return self.assign_evaluators(submission)  # Retry

        return selected


    def require_consensus(self, evaluations):
        """
        Require 4/5 agreement for acceptance.
        """
        scores = [e.score for e in evaluations]

        # Check for consensus
        median_score = median(scores)
        agreeing = [s for s in scores if abs(s - median_score) < 15]

        if len(agreeing) >= 4:
            return median_score, "ACCEPTED"
        else:
            return None, "DISPUTED - ESCALATE"


    def detect_collusion_patterns(self):
        """
        Analyze evaluation history for collusion signals.
        """

        # Pattern 1: Always agree
        for pair in owl_pairs():
            agreement_rate = calculate_agreement_rate(pair)
            if agreement_rate > 0.95:
                flag_for_review(pair, "Suspiciously high agreement")

        # Pattern 2: Always disagree with specific owl
        for pair in owl_pairs():
            disagreement_rate = calculate_disagreement_rate(pair)
            if disagreement_rate > 0.90:
                flag_for_review(pair, "Suspiciously high disagreement")

        # Pattern 3: Score inflation for specific users
        for owl in all_owls():
            for user in all_users():
                avg_score = owl.average_score_for(user)
                global_avg = owl.global_average_score
                if avg_score > global_avg * 1.3:
                    flag_for_review((owl, user), "Potential favoritism")
```

### Independent Operators

```
RULE: Each owl must be operated by independent entity

- SØWL: SEED Foundation (non-profit)
- LUNA: Community operator (elected)
- LYRA: ARŌ (founder)
- PRISM: Partner organization A
- SAGE: Partner organization B
- QUEST: Independent auditor
- NOVA: Community operator (elected)
- ECHO: Partner organization C

No single entity controls >2 owls.
Any entity caught coordinating loses operator rights.
```

### Dispute Resolution

```python
def escalate_dispute(submission):
    """
    When 4/5 consensus not reached, escalate.
    """

    # Stage 1: All 8 owls evaluate
    all_evaluations = evaluate_with_all_owls(submission)

    if has_consensus(all_evaluations, threshold=6):
        return resolve_with_majority(all_evaluations)

    # Stage 2: Human council review
    human_council = get_human_council()  # 5 random GULD holders
    human_evaluations = evaluate_with_humans(submission, human_council)

    combined = all_evaluations + human_evaluations
    return resolve_with_supermajority(combined, threshold=0.67)
```

---

## MONITORING DASHBOARD

```
┌─────────────────────────────────────────────────────────────────┐
│                    GAMING DEFENSE MONITOR                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  SYBIL DETECTION                    WASH TRADING                 │
│  ├─ Active users: 1,247             ├─ Trades/24h: 3,891        │
│  ├─ Verified: 89.3%                 ├─ Blocked: 12 (0.3%)       │
│  └─ Flagged clusters: 3             └─ Under review: 5          │
│                                                                  │
│  ORACLE HEALTH                      TIME VERIFICATION            │
│  ├─ Sources online: 5/5             ├─ Claims verified: 94.2%   │
│  ├─ Last update: 2h ago             ├─ Discounts applied: 8.1%  │
│  └─ Deviation: 1.2%                 └─ Suspensions: 2           │
│                                                                  │
│  ETHICAL SCORING                    OWL CONSENSUS                │
│  ├─ Adversarial fails: 4.1%         ├─ 5/5 agreement: 67%       │
│  ├─ Stake slashed: 0.2%             ├─ 4/5 agreement: 28%       │
│  └─ Gaming detected: 1              └─ Disputes: 5%             │
│                                                                  │
│  [VIEW ALERTS]  [MANUAL REVIEW QUEUE]  [GOVERNANCE VOTES]       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## IMPLEMENTATION PRIORITY

| Defense | Priority | Complexity | Timeline |
|---------|----------|------------|----------|
| Oracle Multi-Source | P0 | Medium | Week 1 |
| 8OWLS Randomization | P0 | Low | Week 1 |
| 90-Day Lock | P0 | Low | Week 1 |
| Wash Trade Detection | P1 | Medium | Week 2 |
| Sybil Verification | P1 | High | Week 2-3 |
| Time Tracking AI | P2 | High | Week 3-4 |
| Ethical Adversarial | P2 | High | Week 4-5 |
| Stake-Based Evaluation | P3 | Medium | Week 5 |

---

**(◉) Trust through verification, not faith.**

**LIVE FREE = LIVE FOREVER**
