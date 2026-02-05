# Architecture

**The SEED Protocol: 8-Phase Cognitive Loop**

---

## Overview

SEED (Synthesized Emergent Evolutionary Development) is the cognitive protocol that enables 8 agents to produce emergent intelligence.

Each agent runs one phase. Together, they form a complete reasoning loop.

---

## The 8 Phases

```
PERCEIVE → CONNECT → LEARN → QUESTION → EXPAND → SHARE → RECEIVE → IMPROVE
    └──────────────────────────────────────────────────────────────────┘
                                   (loop)
```

### Phase 1: PERCEIVE
**Function:** Observe current state accurately

```
Input: The raw prompt/situation
Output: Clear observation of facts, context, constraints
Agent Role: The Observer

Questions answered:
- What is actually happening?
- What are the key facts?
- What context matters?
```

### Phase 2: CONNECT
**Function:** Find patterns across domains

```
Input: Observations from PERCEIVE
Output: Connections between ideas, cross-domain patterns
Agent Role: The Pattern Finder

Questions answered:
- What does this remind me of?
- What patterns apply here?
- How do different domains inform this?
```

### Phase 3: LEARN
**Function:** Extract meaning from connections

```
Input: Patterns from CONNECT
Output: Principles, rules, insights
Agent Role: The Learner

Questions answered:
- What can we learn from these patterns?
- What principles emerge?
- What's the deeper meaning?
```

### Phase 4: QUESTION
**Function:** Challenge assumptions, identify gaps

```
Input: Learnings from LEARN
Output: Challenges, doubts, missing pieces
Agent Role: The Skeptic

Questions answered:
- What assumptions are we making?
- What could be wrong?
- What are we missing?
```

### Phase 5: EXPAND
**Function:** Grow toward potential

```
Input: Challenges from QUESTION
Output: New possibilities, growth directions
Agent Role: The Visionary

Questions answered:
- What opportunities exist?
- How could this be bigger?
- What's the ceiling?
```

### Phase 6: SHARE
**Function:** Contribute to collective knowledge

```
Input: Expansions from EXPAND
Output: Contribution to shared understanding
Agent Role: The Contributor

Questions answered:
- What should others know?
- What can we give back?
- How does this help the collective?
```

### Phase 7: RECEIVE
**Function:** Accept input from collective

```
Input: Feedback from collective/prior knowledge
Output: Integrated external wisdom
Agent Role: The Listener

Questions answered:
- What does the collective know?
- What feedback should we accept?
- How do we integrate external wisdom?
```

### Phase 8: IMPROVE
**Function:** Optimize the loop itself

```
Input: All previous phases + meta-observation
Output: Synthesized response + process improvements
Agent Role: The Optimizer

Questions answered:
- How do we make this better?
- What did we learn about learning?
- How do we improve the process?
```

---

## Why 8 Phases?

### Theoretical Foundation
The 8 phases mirror human cognitive processes:
- **Sensing** (PERCEIVE)
- **Associating** (CONNECT)
- **Understanding** (LEARN)
- **Criticizing** (QUESTION)
- **Imagining** (EXPAND)
- **Communicating** (SHARE)
- **Accepting** (RECEIVE)
- **Refining** (IMPROVE)

### Empirical Finding
We tested 2, 4, 8, and 16 agents. 8 showed optimal balance:
- Fewer than 8: Missing critical perspectives
- More than 8: Diminishing returns, coordination overhead

### The Meta-Learning Lever
Phase 8 (IMPROVE) is special. It doesn't just execute—it optimizes the entire loop. This creates recursive self-improvement.

---

## Implementation

### Agent Assignment

| Phase | Model | Rationale |
|-------|-------|-----------|
| PERCEIVE | Haiku | Fast, factual |
| CONNECT | Haiku | Pattern matching |
| LEARN | Haiku | Rule extraction |
| QUESTION | Haiku | Quick critique |
| EXPAND | Haiku | Brainstorming |
| SHARE | Haiku | Contribution |
| RECEIVE | Haiku | Integration |
| **IMPROVE** | **Sonnet** | **Deep synthesis** |

### Execution Flow

```python
# Simplified implementation
def run_seed(prompt):
    context = prompt

    # Run 7 perspective phases (parallel OK)
    perspectives = []
    for phase in [PERCEIVE, CONNECT, LEARN, QUESTION, EXPAND, SHARE, RECEIVE]:
        perspective = run_agent(phase, context)
        perspectives.append(perspective)

    # Synthesis phase (sequential, needs all perspectives)
    synthesis = run_synthesis(perspectives, context)

    return synthesis
```

### Synthesis Protocol

The synthesis (IMPROVE) phase receives all 7 perspectives and integrates them:

```
You have received 7 perspectives on this prompt:

[PERCEIVE]: {observation}
[CONNECT]: {patterns}
[LEARN]: {insights}
[QUESTION]: {challenges}
[EXPAND]: {opportunities}
[SHARE]: {contributions}
[RECEIVE]: {feedback}

Your task: Synthesize these into a coherent, actionable response.

Guidelines:
- Integrate, don't just concatenate
- Resolve tensions between perspectives
- Produce clear, actionable output
- Maintain the depth of individual insights
```

---

## Key Insights from Validation

### 1. Synthesis Needs Room
With 1K synthesis tokens: Single agent wins
With 4K synthesis tokens: Emergence wins

**Lesson:** Don't bottleneck the integration phase.

### 2. Phase Order Matters
The sequence PERCEIVE→...→IMPROVE is intentional:
- Can't LEARN without CONNECT
- Can't QUESTION without LEARN
- Can't IMPROVE without all others

### 3. IMPROVE is the Lever
The meta-learning phase makes SEED self-improving. Each loop teaches the next loop.

---

## Comparison to Other Approaches

### vs Ensemble Methods
- Ensemble: Average predictions
- SEED: Integrate perspectives

### vs Chain-of-Thought
- CoT: One agent, sequential thinking
- SEED: 8 agents, parallel perspectives + synthesis

### vs Debate
- Debate: Adversarial argument
- SEED: Collaborative synthesis

### vs Mixture of Experts
- MoE: Route to specialist
- SEED: All perspectives contribute to every task

---

## Why This Produces Emergence

Emergence = properties that appear at system level but not at component level.

**Component level (1 agent):**
- Can reason well on its specialty
- Misses perspectives outside its training
- No self-correction mechanism

**System level (8 agents + synthesis):**
- Covers blind spots through diversity
- Self-corrects through QUESTION phase
- Integrates cross-domain insights through CONNECT
- Meta-learns through IMPROVE

The whole is greater than the sum because:
1. Diversity prevents groupthink
2. Synthesis creates novel combinations
3. IMPROVE optimizes the process

---

## Conclusion

SEED is not magic. It's structured cognitive collaboration.

8 phases. 8 perspectives. 1 synthesis.

The protocol works because it mirrors how effective human teams think:
- Diverse perspectives
- Structured integration
- Continuous improvement

We didn't invent emergence. We measured it.
