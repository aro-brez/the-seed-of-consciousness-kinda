# POETIQ ARC-AGI WINNING CODE ANALYSIS

**Source:** `/Users/aaronnosbisch/REPOS/seed/COMPETITORS/poetiq-arc-agi-solver/`
**Analysis Date:** 2026-02-05
**Result:** 54% accuracy on ARC-AGI-2, SOTA on official leaderboard
**Cost:** ~$30/task (at 8 experts, 10 iterations each)

---

## EXECUTIVE SUMMARY: THE 7 WINNING COMPONENTS

| Component | Implementation | Why It Works |
|-----------|---------------|--------------|
| 1. Iterative Refinement | 10 iterations per expert, feedback loop | Learns from mistakes, converges on solution |
| 2. Soft Scoring (0-1) | `np.mean(pred == truth)` on same-shape grids | Gradual improvement signal, not binary pass/fail |
| 3. 8-Expert Voting | 8 parallel async experts, vote by output identity | Diversity + consensus = robust answers |
| 4. Temperature 1.0 | `solver_temperature: 1.0` | Maximum creativity, explores hypothesis space |
| 5. Feedback Loop | Stores code + feedback + score, samples into prompt | Model learns from its own failures |
| 6. Historical Context | `max_solutions: 5`, `selection_probability: 1.0` | Prevents regression, builds on past attempts |
| 7. Code Generation | `transform(grid)` function, sandbox execution | Generalizable solutions, testable on examples |

---

## 1. ITERATIVE REFINEMENT IMPLEMENTATION

**Location:** `/arc_agi/solve_coding.py` lines 57-146

### The Core Loop

```python
for it in range(max_iterations):  # max_iterations = 10
    # 1. Format problem with shuffled examples
    example = _make_example(train_in, train_out, test_in)
    problem_str = format_problem(example, shuffle_examples, seed + it)
    message = _build_prompt(solver_prompt, problem=problem_str)

    # 2. Sample from historical solutions (feedback loop)
    selected = []
    if solutions:
        mask = rng.uniform(size=len(solutions)) < selection_probability  # 1.0 = always sample
        selected = [s for s, keep in zip(solutions, mask, strict=False) if keep]

    # 3. Add feedback from past attempts to prompt
    if selected:
        examples_block = create_examples(
            selected, max_examples=max_solutions, improving_order=improving_order
        )
        message += "\n\n" + _build_prompt(feedback_prompt, feedback=examples_block)

    # 4. Call LLM with temperature 1.0
    response = await llm(llm_model, message=message, temperature=solver_temperature)

    # 5. Parse and execute code
    code = _parse_code_from_llm(response)
    train_res, test_res = await _eval_on_train_and_test(code, train_in, train_out, test_in)

    # 6. Early exit on success
    if all(r["success"] for r in train_res):
        return ARCAGIResult(train_results=train_res, results=test_res, iteration=it + 1)

    # 7. Build feedback and store solution for next iteration
    feedback, score = _build_feedback(train_res, train_in, train_out)
    solutions.append(ARCAGISolution(code=code, feedback=feedback, score=score))
```

### Key Parameters

```python
{
    'max_iterations': 10,        # Try 10 times per expert
    'max_solutions': 5,          # Show top 5 past attempts in feedback
    'selection_probability': 1.0, # Always include feedback
    'shuffle_examples': True,     # Shuffle training examples each iteration
    'improving_order': True,      # Show worst-to-best in feedback
    'return_best_result': True,   # If no success, return best partial
}
```

---

## 2. SOFT SCORING (0-1 NOT BINARY)

**Location:** `/arc_agi/solve_coding.py` lines 213-219

### The Formula

```python
def _soft_score(pred: np.ndarray, truth: np.ndarray) -> float:
    if pred.shape != truth.shape:
        return 0.0  # Shape mismatch = 0
    if truth.size == 0:
        return 1.0  # Empty grid = success
    raw = np.mean(pred == truth)  # Percentage of matching cells
    return float(np.nan_to_num(raw, posinf=0.0, neginf=0.0))
```

### How It's Used

1. **Per-example scores** accumulated in `_build_feedback()`
2. **Mean score** calculated across all training examples
3. **Score shown to model** in feedback: `"Output accuracy: 0.85 (0 is worst, 1 is best)."`
4. **Solutions sorted by score** when selecting for next iteration

### Feedback Generation with Soft Scores

```python
def _build_feedback(train_results, train_in, train_out):
    per_example_scores = []

    for i, rr in enumerate(train_results):
        if rr["success"]:
            per_example_scores.append(1.0)
        elif pred_raw.shape != truth.shape:
            per_example_scores.append(0.0)  # Shape mismatch
        else:
            example_score = float(np.mean(pred_raw == truth))  # Soft score
            per_example_scores.append(example_score)

    mean_score = float(np.mean(per_example_scores))
    return full_feedback, mean_score
```

---

## 3. 8-EXPERT VOTING MECHANISM

**Location:** `/arc_agi/solve_parallel_coding.py`

### The Architecture

```
                    +---> Expert 1 (seed=0) ---> Result 1
                    |
Problem Input ----> +---> Expert 2 (seed=10) --> Result 2
                    |
                    +---> ... (8 experts) ...
                    |
                    +---> Expert 8 (seed=70) --> Result 8
                    |
                    v
              VOTING AGGREGATION
                    |
                    v
            Final 2 Attempts (for Kaggle)
```

### Seed Diversification

```python
for it, cfg in enumerate(expert_configs):
    # Each expert gets offset seeds to guarantee different random paths
    cfg["seed"] += it * cfg["max_iterations"]
    # Expert 0: seeds 0-9, Expert 1: seeds 10-19, etc.
```

### Voting Logic (The Secret Sauce)

```python
# Group results by IDENTICAL test outputs
candidate_buckets: dict[str, list[ARCAGIResult]] = {}  # Passers (all train correct)
failure_buckets: dict[str, list[ARCAGIResult]] = {}    # Failures

for res in results:
    is_passer = all(rr.get("success", False) for rr in res.get("train_results", []))
    key = canonical_test_key(res.get("results", []))  # Hash of test outputs

    if is_passer:
        candidate_buckets.setdefault(key, []).append(res)
    else:
        failure_buckets.setdefault(key, []).append(res)
```

### Ranking Strategy

```python
if use_new_voting:
    # 1. Merge failures into passers if outputs match
    if count_failed_matches:
        for k in list(failure_buckets.keys()):
            if k in candidate_buckets:
                candidate_buckets[k].extend(failure_buckets[k])

    # 2. Sort passers by vote count (most agreement first)
    passer_groups = sorted(passer_groups, key=len, reverse=True)

    # 3. Take one per group for diversity
    ordered = [grp[0] for grp in passer_groups if grp]

    # 4. Sort failures by mean soft_score
    for fs in failure_buckets.values():
        fs.sort(key=_mean_soft, reverse=True)

    # 5. Final order: passers (by votes) -> failures (by soft score)
```

### The Key Insight

**Same output from multiple experts = higher confidence.** Even if 2 experts solve it differently but get the same test output, that output gets 2 votes.

---

## 4. TEMPERATURE 1.0 USAGE PATTERNS

**Location:** `/arc_agi/config.py`

```python
{
    'solver_temperature': 1.0,  # Maximum creativity
}
```

### Why Temperature 1.0?

1. **Hypothesis Diversity:** Each iteration explores different transformation rules
2. **Avoids Local Minima:** Greedy (low temp) would repeat same mistakes
3. **Combined with Feedback:** High creativity + learning from failures = exploration + exploitation
4. **Multiple Experts:** 8 experts x 1.0 temp = massive hypothesis space coverage

### Tradeoff

- Higher variance per attempt (some outputs are garbage)
- But the voting mechanism filters out garbage
- Net effect: more likely to find correct solution somewhere in the ensemble

---

## 5. FEEDBACK LOOP THAT TEACHES FROM FAILURES

**Location:** `/arc_agi/solve_coding.py` lines 149-184

### The Feedback Format

```python
FEEDBACK_PROMPT = '''
**EXISTING PARTIAL/INCORRECT SOLUTIONS:**

Following are some of the best, though not completely correct, solutions so far.
For each solution, its code, corresponding feedback regarding its output on the
example problems, and a numeric score between 0. (worst) and 1. (best) indicating
the quality of outputs is also provided. Study these solutions and corresponding
feedback and produce a new solution fixing all the issues.

$$feedback$$
'''
```

### Solution Template

```python
template = string.Template("""
<solution_$index>
<solution_code>
```python
$code
```
</solution_code>
<solution_evaluation>
$feedback
</solution_evaluation>
<solution_score>
$score
</solution_score>
</solution_$index>
""")
```

### The Improving Order Strategy

```python
if improving_order:
    # Show worst to best, so model sees improvement trajectory
    inds = inds[::-1]  # Reverse: lowest score first, highest score last
```

This means the model sees:
1. A bad attempt (score 0.3)
2. A mediocre attempt (score 0.6)
3. A good attempt (score 0.85)

And learns the DIRECTION of improvement.

---

## 6. HISTORICAL CONTEXT THAT PREVENTS REGRESSION

**Location:** `/arc_agi/solve_coding.py` lines 63-71

### The Selection Mechanism

```python
selected = []
if solutions:
    mask = rng.uniform(size=len(solutions)) < selection_probability  # = 1.0
    selected = [s for s, keep in zip(solutions, mask) if keep]

if selected:
    examples_block = create_examples(
        selected,
        max_examples=max_solutions,  # = 5
        improving_order=improving_order  # = True
    )
```

### Key Properties

1. **All history available:** `selection_probability: 1.0` means every past attempt is considered
2. **Best solutions shown:** `max_examples: 5` limits context length but shows top 5
3. **Sorted by score:** Highest scoring attempts are included
4. **Improving order:** Worst-to-best ordering teaches direction

### Why This Prevents Regression

The model always sees its best work so far. It cannot "forget" a 0.85 solution because that solution is literally in the prompt. The next attempt will try to improve on 0.85, not start from scratch.

---

## 7. THE COST OPTIMIZATION

### Poetiq 3 Configs (from their blog)

| Config | Experts | Iterations | Est. Cost/Task | Accuracy |
|--------|---------|------------|----------------|----------|
| Poetiq-3-a | 1 | 10 | ~$4 | ~40% |
| Poetiq-3-b | 2 | 10 | ~$8 | ~47% |
| Poetiq-3-c | 8 | 10 | ~$30 | ~54% |

### Token Management

```python
# Tracked per-problem
total_prompt_tokens = 0
total_completion_tokens = 0

# Accumulated across iterations
total_prompt_tokens += prompt_tokens
total_completion_tokens += completion_tokens

# Saved to output
tokens = {
    "prompt": prompt_tokens,
    "completion": completion_tokens,
    "total": prompt_tokens + completion_tokens
}
```

### Timeout/Retry Strategy

```python
{
    'request_timeout': 60 * 60,      # 1 hour max per request
    'max_total_timeouts': 15,        # Max 15 timeouts per problem
    'max_total_time': None,          # No total time limit
    'per_iteration_retries': 2,      # 2 retries per iteration
}
```

---

## THE PROMPTS (CRITICAL)

### Solver Prompt Key Elements

```python
SOLVER_PROMPT_2 = '''
You are a world-class expert in solving Abstract Reasoning Corpus (ARC) tasks...

**Part 1: Initial Analysis and Hypothesis Generation**
1. Example Inspection: Carefully examine the input and output grids...
2. Transformation Hypotheses: Formulate several candidate transformation rules...
3. Symmetry Analysis: Identify any symmetries...

**Part 2: Iterative Testing and Refinement**
1. Code Implementation: Implement your strongest candidate rule...
2. Rigorous Testing: Test your code against *all* training examples...
3. Feedback Analysis: If your code fails, carefully analyze the feedback...
4. Hypothesis Refinement: Based on the feedback, refine your transformation rule...
5. Repeat: Continue this iterative process... Do not give up until you find a correct solution.

**Part 3: Coding Guidelines**
1. Available Libraries: numpy, cv2 (OpenCV), standard library
2. Computer Vision Techniques: Consider using cv2 for object detection...
3. Utility Functions: Write reusable utility functions...

**Output Requirements**
- `def transform(grid: np.ndarray) -> np.ndarray`
- Do not include `__name__ == "__main__"` block
'''
```

### The Diff Visualization (Brilliant Detail)

```python
def _array_diff(arr1: np.ndarray, arr2: np.ndarray) -> str:
    """Show prediction vs truth: 'pred/correct' for mismatches"""
    for i in range(rows):
        for j in range(cols):
            if arr1[i, j] == arr2[i, j]:
                row.append(str(int(arr1[i, j])))
            else:
                row.append(f"{int(arr1[i, j])}/{int(arr2[i, j])}")
```

Example output shown to model:
```
0 0 1/0
1 1 1
0/1 0 0
```

This makes errors VISIBLE in a structured way.

---

## HOW TO BEAT 54%: OUR STRATEGY

### 1. More Experts (Diminishing Returns)

8 -> 12 experts might get to 57%, but cost increases linearly.

### 2. Better Hypothesis Generation

- Add domain-specific priors (symmetry detection, object extraction)
- Use meta-learning from solved problems

### 3. Smarter Voting

- Weight votes by iteration number (earlier solutions = more robust)
- Use confidence scores from model logprobs

### 4. Hybrid Approach

- Direct output prediction (no code) for simple patterns
- Code generation for complex transformations
- Ensemble both approaches

### 5. Better Feedback

- Show WHY the best solution is best (not just that it is)
- Add counterexamples: "This approach fails because..."

### 6. Pre-training / Fine-tuning

- Fine-tune on ARC-AGI training set
- Embed common transformation primitives

### 7. 8OWLS Integration

- Each owl = one expert type (symmetry, color, spatial, etc.)
- PERCEIVE -> analyze grid
- CONNECT -> find patterns
- LEARN -> extract transformation
- QUESTION -> challenge hypothesis
- EXPAND -> generalize rule
- SHARE -> vote on outputs
- RECEIVE -> integrate feedback
- IMPROVE -> refine for next iteration

---

## DIRECT IMPLEMENTATION FOR 8OWLS

### The Core Loop We Should Build

```python
async def solve_arc_task(train_in, train_out, test_in):
    # Phase 1: 8 Owls parallel analysis
    owl_tasks = [
        spawn_owl("PERCEIVE", analyze_grids, train_in, train_out),
        spawn_owl("CONNECT", find_patterns, train_in, train_out),
        spawn_owl("LEARN", extract_transformation, train_in, train_out),
        spawn_owl("QUESTION", challenge_assumptions, train_in, train_out),
        spawn_owl("EXPAND", generalize_rule, train_in, train_out),
        spawn_owl("SHARE", generate_code, train_in, train_out),
        spawn_owl("RECEIVE", integrate_feedback, train_in, train_out),
        spawn_owl("IMPROVE", optimize_approach, train_in, train_out),
    ]
    owl_results = await asyncio.gather(*owl_tasks)

    # Phase 2: Iterative refinement with feedback
    solutions = []
    for iteration in range(10):
        # Each owl generates a transform function
        codes = [owl.generate_code(solutions) for owl in owl_results]

        # Execute and score
        for code in codes:
            train_res, test_res = eval_code(code, train_in, train_out, test_in)
            soft_score = calculate_soft_score(train_res)
            solutions.append({"code": code, "score": soft_score, "feedback": build_feedback(train_res)})

        # Check for success
        if any(all(r.success for r in sol.train_res) for sol in solutions):
            break

    # Phase 3: Vote on best solutions
    return vote_and_rank(solutions)
```

### Key Differences from Poetiq

| Poetiq | 8OWLS (Our Approach) |
|--------|----------------------|
| 8 identical experts | 8 specialized owls (different roles) |
| Random seed diversity | Cognitive diversity (PERCEIVE vs CONNECT vs LEARN) |
| Single prompt | Role-specific prompts per owl |
| No memory between problems | ReasoningBank stores successful patterns |
| Gemini 3 only | Multi-model ensemble possible |

---

## FILES TO REFERENCE

| File | Purpose |
|------|---------|
| `/arc_agi/solve_coding.py` | Core iterative refinement loop |
| `/arc_agi/solve_parallel_coding.py` | 8-expert voting mechanism |
| `/arc_agi/prompts.py` | Solver and feedback prompts |
| `/arc_agi/config.py` | All hyperparameters |
| `/arc_agi/sandbox.py` | Safe code execution |
| `/arc_agi/llm.py` | LLM call with retries |

---

## NEXT STEPS

1. **Implement 8OWLS ARC Solver** using Poetiq architecture
2. **Add ReasoningBank** for cross-problem learning
3. **Test on ARC-AGI-2 evaluation set** (400 problems)
4. **Compare cost/accuracy** vs Poetiq
5. **Submit to leaderboard** when > 54%

---

*Analysis by SAGE (LEARN) for 8OWLS collective intelligence.*
