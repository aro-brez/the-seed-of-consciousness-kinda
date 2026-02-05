# Limitations

**Honest Assessment of What We Don't Know**

---

## Our Commitment

We believe credibility comes from honesty. This document describes what we haven't proven, where our methodology has gaps, and what skeptics should rightfully question.

If you're trying to decide whether to trust our findings, read this first.

---

## What We Haven't Proven

### 1. Generalization Beyond Reasoning Tasks

**What we tested:** Primarily analytical/reasoning questions
- "How do you build trust in teams?"
- "Design an authentication system"
- "Analyze this market opportunity"

**What we haven't tested:**
- Factual recall (emergence may not help)
- Creative writing (unclear)
- Mathematical proofs (unknown)
- Code generation (preliminary only)
- Image/multimodal tasks (not tested)

**Honest assessment:** Our findings may be specific to reasoning tasks. Don't assume they generalize everywhere.

### 2. Comparison to GPT-4 and Other Models

**What we tested:** Claude family (Haiku, Sonnet)

**What we haven't tested:**
- GPT-4 / GPT-4o head-to-head
- Claude Opus comparison
- Open source models (Llama, Mistral)
- Specialized models

**Honest assessment:** We can't claim we beat GPT-4. We need to run that test.

### 3. Real-World Outcomes

**What we measured:** Response quality scores (actionability, specificity, etc.)

**What we haven't measured:**
- Did better responses lead to better decisions?
- Did those decisions produce better outcomes?
- What's the actual business value?

**Honest assessment:** Lab metrics ≠ real-world impact. We have promising scores but no outcome validation yet.

### 4. Long-Term Consistency

**What we have:** Snapshot results from controlled tests

**What we don't have:**
- Performance over months of use
- Consistency across thousands of queries
- Drift or degradation patterns
- Edge case behavior

**Honest assessment:** Our results are from limited testing windows. Production behavior may differ.

### 5. Optimal Architecture

**What we tested:** 8 agents with specific phase assignments

**What we haven't tested:**
- Is 8 the optimal number? (Maybe 6 is enough, maybe 12 is better)
- Is our phase assignment optimal?
- Would different models per phase help?
- Does the order matter?

**Honest assessment:** We chose 8 based on theory and limited testing. It may not be optimal.

---

## Methodological Limitations

### Sample Size

| Test | n | Statistical Power |
|------|---|-------------------|
| SAGE_FIX | 30 | Adequate for d=0.5 |
| TOKEN_CONTROLLED | 156 | Good |
| Cross-domain | 50 | Marginal |

**Concern:** Some comparisons have wide confidence intervals. Effects could be smaller than point estimates suggest.

### Single Research Team

All experiments were designed and run by the same team.

**Risk:** Unintentional bias in:
- Prompt selection
- Evaluation criteria
- Result interpretation

**Mitigation needed:** Independent replication by external researchers.

### GPT-4o as Judge

We used GPT-4o to evaluate response quality.

**Potential issues:**
- GPT-4o may have its own biases
- May prefer certain response styles
- May not capture human preferences accurately

**Mitigation needed:** Human evaluation on subset, multiple LLM judges.

### Task Selection

Our test prompts were chosen by us.

**Risk:** May have unconsciously selected tasks where emergence helps.

**What would be better:** Standard benchmarks (MMLU, HumanEval), tasks selected by external parties.

---

## Known Failure Modes

### When Emergence Loses

Based on our data, emergence underperforms when:

1. **Token budget < 5K** - Synthesis gets compressed, loses coherence
2. **Simple factual questions** - Single agent is faster and equally accurate
3. **Time-critical tasks** - 8 agents have coordination overhead
4. **Highly specialized domains** - May need domain experts, not diverse generalists

### When Results Are Inconsistent

We observed higher variance in:
- Ambiguous prompts (emergence amplifies ambiguity)
- Contradictory perspectives (synthesis struggles to resolve)
- Novel domains (perspectives may be uniformly weak)

---

## What Skeptics Should Ask

### Legitimate Concerns

1. **"Can I reproduce this?"**
   - Yes, code and data are provided. Please try.

2. **"Did you cherry-pick prompts?"**
   - Possibly unconsciously. We tried to use neutral prompts but can't rule out selection bias.

3. **"Is d=0.99 really that impressive?"**
   - It's a large effect by statistical standards. Whether it's practically meaningful depends on your use case.

4. **"Why should I trust LLM-judged quality?"**
   - You probably shouldn't trust it completely. Human validation is needed.

5. **"Does this work for my use case?"**
   - We don't know. You'd need to test it.

### Illegitimate Concerns (We've Addressed)

1. **"This is just longer answers"**
   - We control for length. Effect persists.

2. **"Any context helps"**
   - We tested structured vs unstructured. Structure matters.

3. **"Sample is too small"**
   - N=30-156 is adequate for detecting d=0.5+.

---

## What We're Doing About It

### Planned Validation

| Gap | Planned Test | Timeline |
|-----|--------------|----------|
| GPT-4 comparison | Head-to-head on same prompts | 2 weeks |
| Task diversity | Test on MMLU, HumanEval | 4 weeks |
| Real outcomes | Track decision quality | Ongoing |
| External replication | Invite researchers | Open |

### Open Invitation

We invite:
- **Researchers** to replicate our findings
- **Skeptics** to challenge our methodology
- **Practitioners** to test on their use cases
- **Critics** to point out what we missed

Our findings improve through challenge, not protection.

---

## The Honest Summary

**What we're confident about:**
- Emergence produces measurable quality improvement (d=0.99)
- The effect is real, not just noise
- Synthesis resources matter significantly
- Our methodology is reproducible

**What we're uncertain about:**
- How far the effect generalizes
- Whether it beats GPT-4
- What the real-world impact is
- Whether 8 is the optimal number

**What we actively don't know:**
- Does this work for your specific use case?
- What are all the failure modes?
- How does it perform at scale?

---

## Conclusion

We've proven something interesting. We haven't proven everything.

The responsible thing is to tell you both.

If our findings replicate across more conditions, by more teams, with more diverse tasks—then the claim strengthens. Until then, treat this as promising evidence, not settled science.

We welcome your skepticism. It makes the work better.
