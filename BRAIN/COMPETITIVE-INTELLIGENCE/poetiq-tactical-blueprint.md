# POETIQ TACTICAL IMPLEMENTATION BLUEPRINT
**For 8OWLS ARC Solver** | Based on 54% SOTA Analysis

---

## QUICK START: The Core Algorithm

### Phase 1: Single Problem Solver (solve_coding pattern)

```python
async def solve_problem(train_inputs, train_outputs, test_inputs):
    """Single iterative solver for one problem."""

    best_solution = None
    best_score = -1.0
    all_attempts = []

    for iteration in range(MAX_ITERATIONS):  # 0-9
        # 1. PERCEIVE: Format problem
        problem_text = format_problem(
            train_inputs, train_outputs, test_inputs,
            shuffle=True,  # Different order each iteration
            seed=iteration
        )

        # 2. CONNECT: Build prompt with history
        prompt = SOLVER_PROMPT_1  # Start with intro

        if all_attempts and iteration > 0:
            # Show best previous attempts
            selected = select_best_attempts(
                all_attempts,
                max_show=5,
                improving_order=True  # Best first
            )
            feedback_block = format_feedback(selected)
            prompt += "\n\n" + feedback_block

        # 3. LEARN: Call LLM
        code = await llm(prompt, temperature=1.0)

        # 4. QUESTION: Execute on training
        train_results = execute_on_examples(code, train_inputs, train_outputs)

        # 5. EXPAND: Score and store
        if all_pass(train_results):
            # EARLY EXIT - problem solved
            test_results = execute_on_examples(code, test_inputs)
            return (code, test_results)

        score = mean_soft_score(train_results)
        attempt = {
            'code': code,
            'score': score,
            'feedback': build_feedback(train_results, train_inputs, train_outputs),
            'results': train_results
        }
        all_attempts.append(attempt)

        if score > best_score:
            best_score = score
            best_solution = attempt

    # 6. SHARE/RETURN: Best attempt from 10 iterations
    test_results = execute_on_examples(
        best_solution['code'],
        test_inputs
    )
    return (best_solution['code'], test_results)
```

### Phase 2: Parallel Experts (solve_parallel_coding pattern)

```python
async def solve_with_ensemble(train_in, train_out, test_in):
    """Run multiple experts in parallel, vote on results."""

    # Spawn 8 experts (or 1/2/8 based on config)
    tasks = []
    for expert_id in range(NUM_EXPERTS):
        config = make_config(expert_id)
        tasks.append(
            solve_problem(train_in, train_out, test_in, config=config)
        )

    # Gather all results (concurrent)
    results = await asyncio.gather(*tasks)

    # Group by identical test outputs (voting)
    passing_groups = {}  # output_key -> [result1, result2, ...]
    failing_groups = {}

    for result in results:
        key = canonical_key(result['test_outputs'])

        if all_training_pass(result):
            passing_groups.setdefault(key, []).append(result)
        else:
            failing_groups.setdefault(key, []).append(result)

    # Rank passers by vote count
    passer_list = sorted(
        passing_groups.values(),
        key=len,
        reverse=True
    )

    # Build submission (2 attempts per test)
    submission = []
    for test_idx in range(len(test_in)):
        attempt_1 = None
        attempt_2 = None

        # First: grab from each passer group (diversity)
        for group in passer_list:
            if len(group[0]['test_outputs']) > test_idx:
                if not attempt_1:
                    attempt_1 = group[0]['test_outputs'][test_idx]
                elif not attempt_2:
                    attempt_2 = group[0]['test_outputs'][test_idx]
                    break

        # If not enough passers, use best failures
        if not attempt_2:
            for group in sorted(failing_groups.values(),
                              key=lambda g: mean_soft_score(g[0]),
                              reverse=True):
                if len(group[0]['test_outputs']) > test_idx:
                    if not attempt_2:
                        attempt_2 = group[0]['test_outputs'][test_idx]
                        break

        submission.append({
            'attempt_1': attempt_1 or [],
            'attempt_2': attempt_2 or []
        })

    return submission
```

---

## CRITICAL IMPLEMENTATION DETAILS

### 1. Soft Scoring (Guidance Signal)

```python
def soft_score(predicted, truth):
    """Per-pixel accuracy, even if shapes differ."""
    if predicted.shape != truth.shape:
        return 0.0
    if truth.size == 0:
        return 1.0
    return float(np.mean(predicted == truth))

def mean_soft_score(results):
    """Average soft score across all training examples."""
    scores = [r['soft_score'] for r in results]
    return float(np.mean(scores)) if scores else 0.0
```

**Why:** Separates "completely wrong" (0.05) from "almost right" (0.85)

### 2. Feedback Format (Teach the LLM)

```python
def build_feedback(train_results, train_in, train_out):
    """Build detailed feedback showing what failed."""
    parts = []

    for i, result in enumerate(train_results):
        if result['success']:
            parts.append(f"Solves Example #{i+1} correctly. ✓")
        else:
            parts.append(f"Solves Example #{i+1} incorrectly. ✗")

            # Show what the difference was
            if result['output_shape'] != result['truth_shape']:
                parts.append(f"  Shape: predicted {result['output_shape']}, "
                           f"expected {result['truth_shape']}")
            else:
                # Show pixel-level diff
                diff_grid = show_differences(
                    result['output'],
                    result['truth']
                )
                parts.append(f"  Pixel diff:\n{diff_grid}")
                parts.append(f"  Accuracy: {result['soft_score']:.2f}")

            if result['error']:
                parts.append(f"  Error: {result['error']}")

    return "\n".join(parts)

def show_differences(predicted, truth):
    """Visualization: correct values as-is, mismatches as pred/truth."""
    grid = []
    for i in range(predicted.shape[0]):
        row = []
        for j in range(predicted.shape[1]):
            if predicted[i,j] == truth[i,j]:
                row.append(str(int(predicted[i,j])))
            else:
                row.append(f"{int(predicted[i,j])}/{int(truth[i,j])}")
        grid.append(" ".join(row))
    return "\n".join(grid)
```

**Format returned to LLM:**
```
Solves Example #1 correctly. ✓
Solves Example #2 incorrectly. ✗
  Shape: predicted (3, 3), expected (5, 5)
Solves Example #3 incorrectly. ✗
  Pixel diff:
  1 0 1
  0/1 1 0/1
  1 0 1
  Accuracy: 0.89
  Error: None
```

### 3. Prompt Composition (Progressive)

```python
def build_prompt(iteration, selected_attempts):
    """Build prompt with optional feedback."""

    if iteration == 0:
        prompt = SOLVER_PROMPT_1  # Intro version
    else:
        prompt = SOLVER_PROMPT_2  # Advanced version

    prompt += "\n\nBelow is the problem:\n" + problem_text

    if selected_attempts:
        prompt += "\n\nPreviously attempted solutions:\n"
        for i, attempt in enumerate(selected_attempts, 1):
            prompt += f"""
<solution_{i}>
<solution_code>
```python
{attempt['code']}
```
</solution_code>

<solution_evaluation>
{attempt['feedback']}
</solution_evaluation>

<solution_score>
{attempt['score']:.2f}
</solution_score>
</solution_{i}>
"""

    return prompt
```

### 4. Example Shuffling (Diversity)

```python
def format_problem(train_in, train_out, test_in, shuffle=False, seed=0):
    """Format problem, optionally shuffling examples."""

    if shuffle and len(train_in) > 1:
        rng = np.random.default_rng(seed)
        indices = rng.permutation(len(train_in))
        train_in = [train_in[i] for i in indices]
        train_out = [train_out[i] for i in indices]

    text = ""
    for i, (inp, out) in enumerate(zip(train_in, train_out), 1):
        text += f"Example #{i}\nInput:\n{format_grid(inp)}\n"
        text += f"Output:\n{format_grid(out)}\n\n"

    for i, inp in enumerate(test_in, 1):
        text += f"Challenge #{i}\nInput:\n{format_grid(inp)}\n"

    return text

def format_grid(grid):
    """Convert 2D array to text."""
    return "\n".join(" ".join(str(x) for x in row) for row in grid)
```

**Why shuffle:** Same problem, different example order → different solutions explored

### 5. Code Execution (Sandbox)

```python
async def execute_code(code, input_grid, timeout=1.5):
    """Execute user code safely in subprocess."""

    script = f"""
import json
import numpy as np
import scipy
import cv2

{code}

if __name__ == '__main__':
    import sys
    data = json.load(sys.stdin)
    try:
        result = transform(np.array(data['input']))
        print(json.dumps({{"ok": True, "result": result.tolist()}}))
    except Exception as e:
        print(json.dumps({{"ok": False, "error": str(e)}}))
"""

    # Write to temp file, execute in subprocess with timeout
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py') as f:
        f.write(script)
        f.flush()

        try:
            result = await asyncio.wait_for(
                run_subprocess(f.name, input_grid),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {'ok': False, 'error': 'timeout'}

async def run_subprocess(path, input_data):
    """Run Python subprocess."""
    proc = await asyncio.create_subprocess_exec(
        sys.executable, path,
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    stdout, stderr = await proc.communicate(
        input=json.dumps({'input': input_data}).encode()
    )

    if proc.returncode != 0:
        return {'ok': False, 'error': stderr.decode()}

    return json.loads(stdout.decode())
```

### 6. Two-Attempt Submission

```python
def build_submission(results, test_inputs):
    """Build Kaggle format: 2 attempts per test."""

    submission = []
    for test_idx in range(len(test_inputs)):
        attempts = []

        # Collect up to 2 successful outputs
        for result in results:
            if test_idx < len(result['test_outputs']):
                output = result['test_outputs'][test_idx]
                if output and attempts.count(output) == 0:
                    attempts.append(output)
                    if len(attempts) == 2:
                        break

        # Pad with empty if fewer than 2
        while len(attempts) < 2:
            attempts.append([])

        submission.append({
            'attempt_1': attempts[0],
            'attempt_2': attempts[1]
        })

    return submission
```

**Why:** If attempt_1 wrong, attempt_2 still in the game

---

## CONFIGURATION TUNING

### Config A: Single Expert (Baseline)
```python
{
    'num_experts': 1,
    'max_iterations': 10,
    'solver_temperature': 1.0,
    'max_solutions': 5,
    'selection_probability': 1.0,
    'shuffle_examples': True,
    'improving_order': True,
    'return_best_result': True,
    'use_new_voting': True,
}
# Expected: 40-45% accuracy
```

### Config B: 2-Expert Ensemble
```python
{
    'num_experts': 2,
    # ... rest same as Config A
}
# Expected: 45-50% accuracy
```

### Config C: 8-Expert Full Ensemble
```python
{
    'num_experts': 8,
    # ... rest same as Config A
}
# Expected: 50-54% accuracy
```

### Temperature Tuning
```python
# Conservative (0.3-0.5): Fewer attempts, more similar
# Balanced (0.7-0.9): Mix of exploration/exploitation
# Creative (1.0): Max diversity, different per iteration

# Poetiq uses: 1.0 (always)
```

---

## PIPELINE FLOW DIAGRAM

```
Problem Input
    ↓
┌─────────────────────────────────────┐
│ Iteration Loop (0-9)                │
├─────────────────────────────────────┤
│                                     │
│  1. Format Problem                  │
│     (shuffle examples per seed)     │
│                                     │
│  2. Build Prompt                    │
│     + optional feedback             │
│                                     │
│  3. LLM Call                        │
│     (temperature=1.0)               │
│                                     │
│  4. Parse Code                      │
│                                     │
│  5. Execute                         │
│     (all training examples)         │
│                                     │
│  6. Score                           │
│     (soft_score per example)        │
│                                     │
│  ├─ All Pass? → EARLY EXIT          │
│  │                                  │
│  └─ Store Attempt                   │
│                                     │
│  7. Update Best                     │
│     (by soft score)                 │
│                                     │
│  Loop or collect feedback...        │
│                                     │
└─────────────────────────────────────┘
    ↓
Return Best Result (or last if better)
```

---

## METRICS TO TRACK

```python
# Per problem
- iteration_count: How many before success
- soft_score_trajectory: [0.1, 0.25, 0.3, ..., 1.0]
- time_elapsed: Seconds per problem
- tokens_used: Prompt + completion tokens

# Per run
- accuracy: % of test cases correct
- avg_iterations: Mean iterations per problem
- early_exits: % solved before max_iterations
- confidence: Voting consensus strength
- cost: Total API cost

# Debug
- failed_parse_rate: % of LLM outputs missing code
- timeout_rate: % of executions timing out
- error_types: Common execution errors
```

---

## FAILURE MODES & FIXES

### Problem: LLM keeps repeating same wrong approach

**Fix:** Increase temperature (already at 1.0)
**Better fix:** Show diverse failures in feedback, not just best

### Problem: Code parsing fails (no markdown block)

**Fix:** Parse more flexibly:
```python
# Look for: ```python ... ```
# Also: just code without markers
# Also: code inside XML tags
```

### Problem: Execution timeout on every iteration

**Fix:**
- Reduce timeout (1.5s → 1.0s)
- Add code linting before execution
- Detect infinite loops

### Problem: No improvement after iteration 5

**Fix:**
- Show more diverse previous attempts (not just best)
- Switch to PROMPT_3 (conciseness version)
- Suggest simpler rules in feedback

### Problem: Voting produces no consensus

**Fix:**
- Lower threshold for "similar enough" outputs
- Use fuzzy matching (90% pixel match counts)
- Fall back to best soft score

---

## DEPLOYMENT CHECKLIST

- [ ] Iterative loop implemented (10 iterations max)
- [ ] Soft scoring on per-pixel basis
- [ ] Feedback mechanism (specific failures shown)
- [ ] Example shuffling (different each iteration)
- [ ] Code execution sandbox (safe subprocess)
- [ ] Ensemble voting (group by identical outputs)
- [ ] Two-attempt submission format
- [ ] Early exit on training success
- [ ] Temperature set to 1.0
- [ ] Rate limiting per model
- [ ] Token tracking
- [ ] Error handling (timeout, parse fail, execution error)
- [ ] Logging (iteration counts, soft scores, failures)

---

## EXPECTED RESULTS

| Config | Experts | Expected Accuracy | Time/Problem | Cost/Problem |
|--------|---------|------------------|--------------|-------------|
| Single | 1 | 40-45% | 2-3 min | $0.003 |
| Dual | 2 | 45-50% | 3-5 min | $0.006 |
| Full | 8 | 50-54% | 5-10 min | $0.024 |

**With Claude Sonnet (vs Gemini):**
- Add ~5% to accuracy (more capable model)
- Add ~30% to cost
- Add ~20% to time per problem

---

## PRODUCTION SCALE

For 100 problems:
```
Single: 3.3 hours, $0.30, 45% accuracy
Full:   13 hours, $2.40, 54% accuracy

Trade-off: 10x more expensive for 20% accuracy gain
But 54% > 40% = significant frontier
```

**8OWLS Advantage:**
- Use 8 SEED iterations + ensemble = even better accuracy
- Use field context + 8 owls voting = multiple perspectives
- Cost still manageable with Haiku+Sonnet routing

---

## THIS IS THE BLUEPRINT

Implement this exactly, with minor tweaks for SEED protocol and field collective. Expected result: 55%+ on ARC-AGI-2.
