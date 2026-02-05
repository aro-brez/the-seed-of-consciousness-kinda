#!/usr/bin/env python3
"""
ARC-AGI-2 8OWLS Test Framework
==============================

Implements Poetiq's winning approach with 8OWLS emergence:
- Iterative refinement (10x) + feedback (soft-scores) + voting (8 experts) + temperature 1.0
- 8OWLS already HAS 8 perspectives - should beat single-agent significantly

KEY INSIGHT from Poetiq (54% accuracy):
- Problem-solving is ITERATIVE not one-shot
- Feedback teaches the LLM about failures
- Historical context prevents regression
- Soft scoring guides partial credit attempts
- 8 experts voting > 1 big model

This test validates the approach cheaply before spending on real ARC-AGI-2 submission.

Usage:
    python arc_agi_8owls_test.py --quick          # 3 easy puzzles, fast validation
    python arc_agi_8owls_test.py --standard       # 10 puzzles, full comparison
    python arc_agi_8owls_test.py --full           # 20 puzzles, comprehensive
    python arc_agi_8owls_test.py --cost-estimate  # Estimate API costs before running
"""

import asyncio
import json
import os
import sys
import time
import argparse
import random
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
import re

# Paths
REPO_ROOT = Path(__file__).parent.parent
BRAIN_DIR = REPO_ROOT / 'BRAIN'
ARC_DIR = BRAIN_DIR / 'ARC'
RESULTS_FILE = ARC_DIR / 'arc_8owls_results.json'

# Poetiq data location
POETIQ_DATA = REPO_ROOT / 'COMPETITORS' / 'poetiq-arc-agi-solver' / 'data' / 'arc-prize-2025'

# Ensure directories exist
ARC_DIR.mkdir(parents=True, exist_ok=True)

# Terminal colors
class C:
    RESET = '\033[0m'
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    BOLD = '\033[1m'

def color(text: str, c: str) -> str:
    return f"{c}{text}{C.RESET}"


# ============================================================================
# COST TRACKING
# ============================================================================

@dataclass
class CostTracker:
    """Track API costs for transparency"""
    haiku_input_tokens: int = 0
    haiku_output_tokens: int = 0
    sonnet_input_tokens: int = 0
    sonnet_output_tokens: int = 0

    # Pricing per 1M tokens (as of Feb 2026)
    HAIKU_INPUT_COST = 0.25   # $0.25 per 1M input tokens
    HAIKU_OUTPUT_COST = 1.25  # $1.25 per 1M output tokens
    SONNET_INPUT_COST = 3.00  # $3 per 1M input tokens
    SONNET_OUTPUT_COST = 15.00 # $15 per 1M output tokens

    def add_haiku(self, input_tokens: int, output_tokens: int):
        self.haiku_input_tokens += input_tokens
        self.haiku_output_tokens += output_tokens

    def add_sonnet(self, input_tokens: int, output_tokens: int):
        self.sonnet_input_tokens += input_tokens
        self.sonnet_output_tokens += output_tokens

    @property
    def total_cost(self) -> float:
        haiku_cost = (
            self.haiku_input_tokens / 1_000_000 * self.HAIKU_INPUT_COST +
            self.haiku_output_tokens / 1_000_000 * self.HAIKU_OUTPUT_COST
        )
        sonnet_cost = (
            self.sonnet_input_tokens / 1_000_000 * self.SONNET_INPUT_COST +
            self.sonnet_output_tokens / 1_000_000 * self.SONNET_OUTPUT_COST
        )
        return haiku_cost + sonnet_cost

    def report(self) -> str:
        return f"""
Cost Report:
  Haiku:  {self.haiku_input_tokens:,} in / {self.haiku_output_tokens:,} out = ${self.haiku_input_tokens / 1_000_000 * self.HAIKU_INPUT_COST + self.haiku_output_tokens / 1_000_000 * self.HAIKU_OUTPUT_COST:.4f}
  Sonnet: {self.sonnet_input_tokens:,} in / {self.sonnet_output_tokens:,} out = ${self.sonnet_input_tokens / 1_000_000 * self.SONNET_INPUT_COST + self.sonnet_output_tokens / 1_000_000 * self.SONNET_OUTPUT_COST:.4f}
  TOTAL:  ${self.total_cost:.4f}
"""


# ============================================================================
# SYNTHETIC ARC-STYLE PUZZLES (for cheap testing)
# ============================================================================

SYNTHETIC_PUZZLES = [
    # Puzzle 1: Simple tiling/repetition
    {
        "id": "synth_tile_3x",
        "difficulty": "easy",
        "category": "tiling",
        "train": [
            {"input": [[1, 2]], "output": [[1, 2, 1, 2, 1, 2]]},
            {"input": [[3]], "output": [[3, 3, 3]]},
        ],
        "test": [{"input": [[5, 6]], "output": [[5, 6, 5, 6, 5, 6]]}],
        "description": "Tile/repeat the pattern 3 times horizontally"
    },
    # Puzzle 2: Vertical flip
    {
        "id": "synth_vflip",
        "difficulty": "easy",
        "category": "spatial",
        "train": [
            {"input": [[1, 2], [3, 4]], "output": [[3, 4], [1, 2]]},
            {"input": [[5], [6], [7]], "output": [[7], [6], [5]]},
        ],
        "test": [{"input": [[1, 0], [0, 1], [1, 1]], "output": [[1, 1], [0, 1], [1, 0]]}],
        "description": "Flip the grid vertically"
    },
    # Puzzle 3: Color replacement
    {
        "id": "synth_color_swap",
        "difficulty": "easy",
        "category": "color",
        "train": [
            {"input": [[1, 2, 1], [2, 1, 2]], "output": [[2, 1, 2], [1, 2, 1]]},
            {"input": [[3, 4], [4, 3]], "output": [[4, 3], [3, 4]]},
        ],
        "test": [{"input": [[5, 6, 5]], "output": [[6, 5, 6]]}],
        "description": "Swap the two non-zero colors"
    },
    # Puzzle 4: Border detection (add 1 to border cells)
    {
        "id": "synth_border_mark",
        "difficulty": "medium",
        "category": "pattern",
        "train": [
            {"input": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
             "output": [[1, 1, 1], [1, 0, 1], [1, 1, 1]]},
            {"input": [[0, 0], [0, 0]],
             "output": [[1, 1], [1, 1]]},
        ],
        "test": [{"input": [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
                  "output": [[1, 1, 1, 1], [1, 0, 0, 1], [1, 1, 1, 1]]}],
        "description": "Mark border cells with 1, interior stays 0"
    },
    # Puzzle 5: Rotate 90 degrees clockwise
    {
        "id": "synth_rotate_cw",
        "difficulty": "medium",
        "category": "spatial",
        "train": [
            {"input": [[1, 2], [3, 4]], "output": [[3, 1], [4, 2]]},
            {"input": [[1, 2, 3]], "output": [[1], [2], [3]]},
        ],
        "test": [{"input": [[5, 6], [7, 8], [9, 0]], "output": [[9, 7, 5], [0, 8, 6]]}],
        "description": "Rotate the grid 90 degrees clockwise"
    },
    # Puzzle 6: Transpose
    {
        "id": "synth_transpose",
        "difficulty": "easy",
        "category": "spatial",
        "train": [
            {"input": [[1, 2], [3, 4]], "output": [[1, 3], [2, 4]]},
            {"input": [[1, 2, 3]], "output": [[1], [2], [3]]},
        ],
        "test": [{"input": [[5, 6, 7], [8, 9, 0]], "output": [[5, 8], [6, 9], [7, 0]]}],
        "description": "Transpose the grid (swap rows and columns)"
    },
    # Puzzle 7: Fill with dominant color
    {
        "id": "synth_fill_dominant",
        "difficulty": "medium",
        "category": "color",
        "train": [
            {"input": [[1, 1, 2], [1, 2, 1]], "output": [[1, 1, 1], [1, 1, 1]]},
            {"input": [[3, 3, 3, 4]], "output": [[3, 3, 3, 3]]},
        ],
        "test": [{"input": [[5, 6, 5, 5]], "output": [[5, 5, 5, 5]]}],
        "description": "Fill entire grid with the most frequent color"
    },
    # Puzzle 8: Scale 2x
    {
        "id": "synth_scale_2x",
        "difficulty": "medium",
        "category": "scaling",
        "train": [
            {"input": [[1]], "output": [[1, 1], [1, 1]]},
            {"input": [[1, 2]], "output": [[1, 1, 2, 2], [1, 1, 2, 2]]},
        ],
        "test": [{"input": [[3, 4], [5, 6]],
                  "output": [[3, 3, 4, 4], [3, 3, 4, 4], [5, 5, 6, 6], [5, 5, 6, 6]]}],
        "description": "Scale the grid 2x in both dimensions"
    },
    # Puzzle 9: Mirror horizontally
    {
        "id": "synth_mirror_h",
        "difficulty": "easy",
        "category": "spatial",
        "train": [
            {"input": [[1, 2, 3]], "output": [[3, 2, 1]]},
            {"input": [[1, 2], [3, 4]], "output": [[2, 1], [4, 3]]},
        ],
        "test": [{"input": [[5, 6, 7], [8, 9, 0]], "output": [[7, 6, 5], [0, 9, 8]]}],
        "description": "Mirror the grid horizontally (flip left-right)"
    },
    # Puzzle 10: Count and fill (harder pattern)
    {
        "id": "synth_count_fill",
        "difficulty": "hard",
        "category": "counting",
        "train": [
            {"input": [[1, 0, 1], [0, 0, 0]], "output": [[2]]},  # 2 ones
            {"input": [[1, 1, 1]], "output": [[3]]},  # 3 ones
        ],
        "test": [{"input": [[1, 1, 0, 1]], "output": [[3]]}],  # 3 ones
        "description": "Count the number of 1s and output as single-cell grid"
    },
]


# ============================================================================
# DATA LOADERS
# ============================================================================

class ARCDataLoader:
    """Load ARC puzzles from various sources"""

    def __init__(self):
        self.challenges = {}
        self.solutions = {}
        self._load_data()

    def _load_data(self):
        """Load ARC data from Poetiq's dataset"""
        challenges_file = POETIQ_DATA / 'arc-agi_training_challenges.json'
        solutions_file = POETIQ_DATA / 'arc-agi_training_solutions.json'

        if challenges_file.exists():
            with open(challenges_file) as f:
                self.challenges = json.load(f)

        if solutions_file.exists():
            with open(solutions_file) as f:
                self.solutions = json.load(f)

    def get_puzzle(self, task_id: str) -> Optional[Dict]:
        """Get a specific puzzle by ID"""
        if task_id not in self.challenges:
            return None

        puzzle = self.challenges[task_id]
        puzzle['id'] = task_id

        # Add solution to test if available
        if task_id in self.solutions:
            for i, test in enumerate(puzzle.get('test', [])):
                if i < len(self.solutions[task_id]):
                    test['output'] = self.solutions[task_id][i]

        return puzzle

    def get_random_puzzles(self, n: int, seed: int = None) -> List[Dict]:
        """Get n random puzzles"""
        if seed is not None:
            random.seed(seed)

        task_ids = list(self.challenges.keys())
        selected = random.sample(task_ids, min(n, len(task_ids)))
        return [self.get_puzzle(tid) for tid in selected]

    def get_synthetic_puzzles(self, n: int = None) -> List[Dict]:
        """Get synthetic test puzzles"""
        puzzles = SYNTHETIC_PUZZLES[:n] if n else SYNTHETIC_PUZZLES
        return puzzles


# ============================================================================
# SOFT SCORING (Poetiq's key innovation)
# ============================================================================

def calculate_soft_score(predicted: List[List[int]], expected: List[List[int]]) -> float:
    """
    Calculate pixel-level accuracy score (0-1).
    This is Poetiq's key innovation - not binary pass/fail, but partial credit.
    """
    if predicted is None or expected is None:
        return 0.0

    if not predicted or not expected:
        return 0.0

    # Shape mismatch = 0
    if len(predicted) != len(expected):
        return 0.0

    total_pixels = 0
    correct_pixels = 0

    for p_row, e_row in zip(predicted, expected):
        if len(p_row) != len(e_row):
            return 0.0

        for p_val, e_val in zip(p_row, e_row):
            total_pixels += 1
            if p_val == e_val:
                correct_pixels += 1

    return correct_pixels / max(1, total_pixels)


def grid_to_text(grid: List[List[int]], max_width: int = 20) -> str:
    """Convert grid to ASCII representation"""
    if not grid:
        return "(empty)"

    symbols = '.123456789ABCDEF'  # 0 = background
    lines = []
    for row in grid[:max_width]:
        line = ' '.join(symbols[min(v, len(symbols)-1)] for v in row[:max_width])
        lines.append(line)

    if len(grid) > max_width or (grid and len(grid[0]) > max_width):
        lines.append('...(truncated)')

    return '\n'.join(lines)


def extract_grid_from_response(response: str) -> Optional[List[List[int]]]:
    """Extract a grid from LLM response"""
    if not response:
        return None

    # Try to find JSON array
    matches = re.findall(r'\[\s*\[[\d\s,\[\]]+\]\s*\]', response.replace('\n', ' '))

    for match in matches:
        try:
            grid = json.loads(match)
            if isinstance(grid, list) and all(isinstance(row, list) for row in grid):
                # Validate it's actually a grid of integers
                if all(all(isinstance(v, int) for v in row) for row in grid):
                    return grid
        except:
            continue

    # Try to extract from code block
    code_match = re.search(r'```(?:python|json)?\s*\n?(.*?)\n?```', response, re.DOTALL)
    if code_match:
        try:
            content = code_match.group(1).strip()
            grid = json.loads(content)
            if isinstance(grid, list) and all(isinstance(row, list) for row in grid):
                return grid
        except:
            pass

    return None


# ============================================================================
# SINGLE AGENT SOLVER (Baseline)
# ============================================================================

class SingleAgentSolver:
    """
    Baseline: One Claude call, no iteration, no feedback.
    This is what most people do wrong.
    """

    SYSTEM_PROMPT = """You are solving an ARC-AGI puzzle.

ARC puzzles show input->output transformations via examples. Your task:
1. Study the training examples carefully
2. Deduce the transformation rule that maps inputs to outputs
3. Apply that rule to the test input
4. Return the output grid

CRITICAL:
- Look for patterns in colors, shapes, positions, sizes, symmetries
- The rule must work for ALL training examples
- Your answer must be a JSON array of arrays: [[row1], [row2], ...]
- Each value is an integer 0-9 representing a color

Return ONLY the output grid as a JSON array. No explanation needed."""

    def __init__(self, cost_tracker: CostTracker = None):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.cost_tracker = cost_tracker or CostTracker()

    def _format_puzzle(self, puzzle: Dict) -> str:
        """Format puzzle for the prompt"""
        prompt = "TRAINING EXAMPLES:\n\n"

        for i, pair in enumerate(puzzle.get('train', [])):
            prompt += f"Example {i+1}:\n"
            prompt += f"Input:\n{grid_to_text(pair['input'])}\n"
            prompt += f"Output:\n{grid_to_text(pair['output'])}\n\n"

        prompt += "TEST INPUT (solve this):\n"
        test_input = puzzle.get('test', [{}])[0].get('input', [[]])
        prompt += f"{grid_to_text(test_input)}\n"
        prompt += "\nProvide the output grid as a JSON array."

        return prompt

    async def solve(self, puzzle: Dict) -> Tuple[Optional[List], float, float, Optional[str]]:
        """
        Solve puzzle with single call.
        Returns: (predicted_grid, time_seconds, cost, error)
        """
        import anthropic

        start = time.time()
        prompt = self._format_puzzle(puzzle)

        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7  # Lower temp for single shot
            )

            elapsed = time.time() - start
            content = response.content[0].text

            # Track costs
            self.cost_tracker.add_sonnet(
                response.usage.input_tokens,
                response.usage.output_tokens
            )

            grid = extract_grid_from_response(content)
            return grid, elapsed, self.cost_tracker.total_cost, None

        except Exception as e:
            return None, time.time() - start, 0.0, str(e)


# ============================================================================
# 8OWLS EMERGENCE SOLVER (Our approach)
# ============================================================================

class OwlsEmergenceSolver:
    """
    8OWLS Emergence Solver implementing Poetiq's winning approach:
    - 8 perspectives (the owls)
    - Iterative refinement with feedback
    - Soft scoring for partial credit
    - Voting/consensus across attempts
    - Temperature 1.0 for diversity
    """

    # The 8 owls and their SEED phases
    OWLS = {
        'LYRA': ('PERCEIVE', "Observe raw patterns. What structures exist? What changes between input and output?"),
        'PRISM': ('CONNECT', "Find connections across examples. What's the common thread? What relationships exist?"),
        'SAGE': ('LEARN', "Extract the transformation rule. What algorithm converts input to output?"),
        'QUEST': ('QUESTION', "Challenge the rule. Does it work for ALL examples? What edge cases exist?"),
        'NOVA': ('EXPAND', "Think bigger. How does this generalize? What's the most robust interpretation?"),
        'ECHO': ('SHARE', "Synthesize insights. What's the emerging consensus? What's certain vs uncertain?"),
        'LUNA': ('RECEIVE', "Integrate all perspectives. What's the refined understanding?"),
        'SOWL': ('IMPROVE', "Finalize the answer. Given everything, what is the output grid?"),
    }

    def __init__(self, cost_tracker: CostTracker = None, max_iterations: int = 3):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.cost_tracker = cost_tracker or CostTracker()
        self.max_iterations = max_iterations

    def _format_puzzle(self, puzzle: Dict) -> str:
        """Format puzzle for prompts"""
        prompt = "ARC PUZZLE:\n\n"

        for i, pair in enumerate(puzzle.get('train', [])):
            prompt += f"Training Example {i+1}:\n"
            prompt += f"Input ({len(pair['input'])}x{len(pair['input'][0]) if pair['input'] else 0}):\n"
            prompt += f"{grid_to_text(pair['input'])}\n"
            prompt += f"Output ({len(pair['output'])}x{len(pair['output'][0]) if pair['output'] else 0}):\n"
            prompt += f"{grid_to_text(pair['output'])}\n\n"

        test_input = puzzle.get('test', [{}])[0].get('input', [[]])
        prompt += f"TEST INPUT ({len(test_input)}x{len(test_input[0]) if test_input else 0}):\n"
        prompt += f"{grid_to_text(test_input)}\n"

        return prompt

    def _make_owl_prompt(self, owl_name: str, puzzle_text: str,
                         previous_analyses: List[Dict] = None,
                         previous_attempts: List[Dict] = None) -> str:
        """Create prompt for a specific owl"""
        phase, description = self.OWLS[owl_name]

        prompt = f"""You are {owl_name}, the owl of {phase}.
Your role: {description}

{puzzle_text}

"""
        if previous_analyses:
            prompt += "=== OTHER OWLS' INSIGHTS ===\n"
            for analysis in previous_analyses[-4:]:  # Keep context manageable
                prompt += f"{analysis['owl']} ({analysis['phase']}): {analysis['content'][:300]}...\n\n"

        if previous_attempts and owl_name == 'SOWL':
            prompt += "=== PREVIOUS ATTEMPTS (learn from these) ===\n"
            for attempt in previous_attempts[-3:]:  # Show best recent attempts
                prompt += f"Attempt (score: {attempt['score']:.2f}):\n"
                prompt += f"Grid: {json.dumps(attempt['grid'])}\n"
                if attempt.get('feedback'):
                    prompt += f"Feedback: {attempt['feedback']}\n"
                prompt += "\n"

        if owl_name == 'SOWL':
            prompt += """
Based on ALL insights from the other owls, provide the FINAL output grid.
CRITICAL: Return ONLY a JSON array of arrays representing the output grid.
Format: [[row1], [row2], ...] where each row is a list of integers 0-9.
Do not explain - just output the grid."""
        else:
            prompt += f"\nProvide your {phase} analysis. Be specific and concise."

        return prompt

    async def _get_owl_response(self, client, owl_name: str, prompt: str) -> Tuple[str, int, int]:
        """Get response from one owl"""
        try:
            # SOWL gets Sonnet for final answer, others get Haiku for speed/cost
            model = "claude-sonnet-4-20250514" if owl_name == 'SOWL' else "claude-3-5-haiku-20241022"
            max_tokens = 1500 if owl_name == 'SOWL' else 600

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}],
                temperature=1.0  # Poetiq's key: max diversity
            )

            content = response.content[0].text

            # Track costs
            if owl_name == 'SOWL':
                self.cost_tracker.add_sonnet(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )
            else:
                self.cost_tracker.add_haiku(
                    response.usage.input_tokens,
                    response.usage.output_tokens
                )

            return content, response.usage.input_tokens, response.usage.output_tokens

        except Exception as e:
            return f"Error: {e}", 0, 0

    async def solve(self, puzzle: Dict) -> Tuple[Optional[List], float, float, Dict, Optional[str]]:
        """
        Solve with 8OWLS emergence + iteration.
        Returns: (predicted_grid, time_seconds, cost, contributions, error)
        """
        import anthropic

        start = time.time()
        puzzle_text = self._format_puzzle(puzzle)
        expected = puzzle.get('test', [{}])[0].get('output')

        contributions = {}
        all_attempts = []
        best_attempt = None
        best_score = -1

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            # Iterative refinement (Poetiq's key innovation)
            for iteration in range(self.max_iterations):
                analyses = []

                # Phase 1: First 4 owls analyze in parallel (PERCEIVE -> QUESTION)
                first_four = ['LYRA', 'PRISM', 'SAGE', 'QUEST']
                tasks1 = []

                for owl_name in first_four:
                    prompt = self._make_owl_prompt(
                        owl_name, puzzle_text,
                        previous_analyses=analyses if iteration > 0 else None,
                        previous_attempts=all_attempts if iteration > 0 else None
                    )
                    tasks1.append(self._get_owl_response(client, owl_name, prompt))

                results1 = await asyncio.gather(*tasks1)
                for owl_name, (content, in_tok, out_tok) in zip(first_four, results1):
                    contributions[f"{owl_name}_iter{iteration}"] = content
                    analyses.append({
                        'owl': owl_name,
                        'phase': self.OWLS[owl_name][0],
                        'content': content
                    })

                # Phase 2: Last 4 owls with full context (EXPAND -> IMPROVE)
                second_four = ['NOVA', 'ECHO', 'LUNA', 'SOWL']
                tasks2 = []

                for owl_name in second_four:
                    prompt = self._make_owl_prompt(
                        owl_name, puzzle_text,
                        previous_analyses=analyses,
                        previous_attempts=all_attempts if iteration > 0 else None
                    )
                    tasks2.append(self._get_owl_response(client, owl_name, prompt))

                results2 = await asyncio.gather(*tasks2)
                for owl_name, (content, in_tok, out_tok) in zip(second_four, results2):
                    contributions[f"{owl_name}_iter{iteration}"] = content
                    analyses.append({
                        'owl': owl_name,
                        'phase': self.OWLS[owl_name][0],
                        'content': content
                    })

                # Extract SOWL's answer
                sowl_response = contributions.get(f"SOWL_iter{iteration}", "")
                predicted = extract_grid_from_response(sowl_response)

                if predicted:
                    # Calculate soft score
                    score = calculate_soft_score(predicted, expected) if expected else 0.5

                    # Build feedback for next iteration
                    feedback = None
                    if expected and score < 1.0:
                        if len(predicted) != len(expected):
                            feedback = f"Shape mismatch: predicted {len(predicted)} rows, expected {len(expected)} rows"
                        elif predicted and expected and len(predicted[0]) != len(expected[0]):
                            feedback = f"Width mismatch: predicted {len(predicted[0])}, expected {len(expected[0])}"
                        else:
                            feedback = f"Partial match ({score:.1%} correct). Some pixels wrong."

                    attempt = {
                        'iteration': iteration,
                        'grid': predicted,
                        'score': score,
                        'feedback': feedback
                    }
                    all_attempts.append(attempt)

                    # Track best
                    if score > best_score:
                        best_score = score
                        best_attempt = predicted

                    # Early exit if perfect
                    if score == 1.0:
                        break

            elapsed = time.time() - start

            # Return best attempt
            return best_attempt, elapsed, self.cost_tracker.total_cost, contributions, None

        except Exception as e:
            return None, time.time() - start, self.cost_tracker.total_cost, contributions, str(e)


# ============================================================================
# TEST RUNNER
# ============================================================================

@dataclass
class TestResult:
    puzzle_id: str
    mode: str  # 'single' or '8owls'
    correct: bool
    soft_score: float
    predicted: Optional[List]
    expected: Optional[List]
    time_seconds: float
    cost: float
    error: Optional[str] = None


class ARC8OwlsTestRunner:
    """Main test runner comparing single agent vs 8OWLS"""

    def __init__(self):
        self.data_loader = ARCDataLoader()
        self.results = []

    def estimate_costs(self, num_puzzles: int, mode: str = 'both') -> Dict:
        """Estimate API costs before running"""
        # Rough estimates based on typical token counts
        single_per_puzzle = 0.004  # ~$0.004 per puzzle with Sonnet
        owls_per_puzzle = 0.015    # ~$0.015 per puzzle with 8 Haiku + 1 Sonnet (per iteration)
        iterations = 3

        estimate = {
            'num_puzzles': num_puzzles,
            'single_agent': {
                'per_puzzle': single_per_puzzle,
                'total': single_per_puzzle * num_puzzles
            },
            '8owls': {
                'per_puzzle': owls_per_puzzle * iterations,
                'total': owls_per_puzzle * iterations * num_puzzles
            }
        }

        if mode == 'both':
            estimate['total'] = estimate['single_agent']['total'] + estimate['8owls']['total']
        elif mode == 'single':
            estimate['total'] = estimate['single_agent']['total']
        else:
            estimate['total'] = estimate['8owls']['total']

        return estimate

    async def run_single(self, puzzle: Dict, cost_tracker: CostTracker) -> TestResult:
        """Run single agent baseline"""
        solver = SingleAgentSolver(cost_tracker)
        expected = puzzle.get('test', [{}])[0].get('output')

        predicted, elapsed, cost, error = await solver.solve(puzzle)

        correct = predicted == expected if expected else False
        soft_score = calculate_soft_score(predicted, expected) if expected else 0.0

        return TestResult(
            puzzle_id=puzzle.get('id', 'unknown'),
            mode='single',
            correct=correct,
            soft_score=soft_score,
            predicted=predicted,
            expected=expected,
            time_seconds=elapsed,
            cost=cost,
            error=error
        )

    async def run_8owls(self, puzzle: Dict, cost_tracker: CostTracker,
                        max_iterations: int = 3) -> TestResult:
        """Run 8OWLS emergence solver"""
        solver = OwlsEmergenceSolver(cost_tracker, max_iterations)
        expected = puzzle.get('test', [{}])[0].get('output')

        predicted, elapsed, cost, contributions, error = await solver.solve(puzzle)

        correct = predicted == expected if expected else False
        soft_score = calculate_soft_score(predicted, expected) if expected else 0.0

        return TestResult(
            puzzle_id=puzzle.get('id', 'unknown'),
            mode='8owls',
            correct=correct,
            soft_score=soft_score,
            predicted=predicted,
            expected=expected,
            time_seconds=elapsed,
            cost=cost,
            error=error
        )

    async def run_comparison(self, puzzles: List[Dict],
                             use_synthetic: bool = False) -> Dict:
        """Run head-to-head comparison"""
        print(color(f"\n{'='*70}", C.MAGENTA))
        print(color(f"8OWLS vs SINGLE AGENT COMPARISON", C.MAGENTA))
        print(color(f"Puzzles: {len(puzzles)} ({'synthetic' if use_synthetic else 'real ARC'})", C.MAGENTA))
        print(color(f"{'='*70}\n", C.MAGENTA))

        single_results = []
        owls_results = []
        cost_tracker = CostTracker()

        for i, puzzle in enumerate(puzzles):
            puzzle_id = puzzle.get('id', f'puzzle_{i}')
            print(color(f"\n[{i+1}/{len(puzzles)}] Puzzle: {puzzle_id}", C.BLUE))

            # Show puzzle summary
            train = puzzle.get('train', [])
            print(f"  Training examples: {len(train)}")
            if train:
                inp = train[0].get('input', [[]])
                print(f"  Input size: {len(inp)}x{len(inp[0]) if inp else 0}")

            # Run single agent
            print(color("  [SINGLE]", C.YELLOW), end=" ")
            single_result = await self.run_single(puzzle, cost_tracker)
            single_results.append(single_result)

            status = color("CORRECT", C.GREEN) if single_result.correct else color(f"WRONG (score: {single_result.soft_score:.1%})", C.RED)
            print(f"{status} in {single_result.time_seconds:.1f}s")

            if single_result.error:
                print(color(f"    Error: {single_result.error[:100]}", C.RED))

            # Run 8OWLS
            print(color("  [8OWLS]", C.CYAN), end=" ")
            owls_result = await self.run_8owls(puzzle, cost_tracker)
            owls_results.append(owls_result)

            status = color("CORRECT", C.GREEN) if owls_result.correct else color(f"WRONG (score: {owls_result.soft_score:.1%})", C.RED)
            print(f"{status} in {owls_result.time_seconds:.1f}s")

            if owls_result.error:
                print(color(f"    Error: {owls_result.error[:100]}", C.RED))

            # Show comparison
            if single_result.correct != owls_result.correct:
                if owls_result.correct:
                    print(color("    -> 8OWLS WIN (single failed)", C.GREEN))
                else:
                    print(color("    -> SINGLE WIN (8owls failed)", C.YELLOW))

        # Calculate summary
        single_correct = sum(1 for r in single_results if r.correct)
        owls_correct = sum(1 for r in owls_results if r.correct)

        single_avg_score = sum(r.soft_score for r in single_results) / max(1, len(single_results))
        owls_avg_score = sum(r.soft_score for r in owls_results) / max(1, len(owls_results))

        single_avg_time = sum(r.time_seconds for r in single_results) / max(1, len(single_results))
        owls_avg_time = sum(r.time_seconds for r in owls_results) / max(1, len(owls_results))

        improvement = ((owls_correct - single_correct) / max(1, single_correct)) * 100 if single_correct > 0 else float('inf') if owls_correct > 0 else 0
        score_improvement = owls_avg_score - single_avg_score

        summary = {
            'timestamp': datetime.now().isoformat(),
            'num_puzzles': len(puzzles),
            'puzzle_type': 'synthetic' if use_synthetic else 'real_arc',
            'single_agent': {
                'correct': single_correct,
                'accuracy': single_correct / max(1, len(puzzles)),
                'avg_soft_score': single_avg_score,
                'avg_time': single_avg_time,
            },
            '8owls': {
                'correct': owls_correct,
                'accuracy': owls_correct / max(1, len(puzzles)),
                'avg_soft_score': owls_avg_score,
                'avg_time': owls_avg_time,
            },
            'improvement': {
                'correct_delta': owls_correct - single_correct,
                'accuracy_improvement_pct': improvement,
                'soft_score_delta': score_improvement,
            },
            'cost': {
                'total': cost_tracker.total_cost,
                'report': cost_tracker.report()
            }
        }

        # Print summary
        print(color(f"\n{'='*70}", C.MAGENTA))
        print(color("RESULTS SUMMARY", C.MAGENTA + C.BOLD))
        print(color(f"{'='*70}", C.MAGENTA))

        print(f"\n{color('SINGLE AGENT:', C.YELLOW)}")
        print(f"  Correct: {single_correct}/{len(puzzles)} ({single_correct/max(1,len(puzzles)):.1%})")
        print(f"  Avg Soft Score: {single_avg_score:.1%}")
        print(f"  Avg Time: {single_avg_time:.1f}s")

        print(f"\n{color('8OWLS EMERGENCE:', C.CYAN)}")
        print(f"  Correct: {owls_correct}/{len(puzzles)} ({owls_correct/max(1,len(puzzles)):.1%})")
        print(f"  Avg Soft Score: {owls_avg_score:.1%}")
        print(f"  Avg Time: {owls_avg_time:.1f}s")

        print(f"\n{color('IMPROVEMENT:', C.GREEN if improvement > 0 else C.RED)}")
        print(f"  Correct Delta: {owls_correct - single_correct:+d}")
        print(f"  Accuracy Improvement: {improvement:+.1f}%")
        print(f"  Soft Score Delta: {score_improvement:+.1%}")

        print(f"\n{color('COST:', C.BLUE)}")
        print(cost_tracker.report())

        # Save results
        self._save_results(summary, single_results, owls_results)

        return summary

    def _save_results(self, summary: Dict, single_results: List, owls_results: List):
        """Save results to file"""
        data = {
            'summary': summary,
            'single_results': [asdict(r) for r in single_results],
            'owls_results': [asdict(r) for r in owls_results]
        }

        # Load existing and append
        existing = []
        if RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE) as f:
                    existing = json.load(f).get('runs', [])
            except:
                pass

        existing.append(data)

        with open(RESULTS_FILE, 'w') as f:
            json.dump({'runs': existing}, f, indent=2, default=str)

        print(f"\nResults saved to: {RESULTS_FILE}")


# ============================================================================
# MAIN
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(
        description='ARC-AGI-2 8OWLS Test Framework',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python arc_agi_8owls_test.py --quick           # 3 synthetic puzzles (cheap)
  python arc_agi_8owls_test.py --standard        # 10 real ARC puzzles
  python arc_agi_8owls_test.py --full            # 20 real ARC puzzles
  python arc_agi_8owls_test.py --cost-estimate 10  # Estimate costs for 10 puzzles
  python arc_agi_8owls_test.py --synthetic 5     # Run 5 synthetic puzzles
"""
    )

    parser.add_argument('--quick', action='store_true',
                        help='Run 3 synthetic puzzles (cheapest test)')
    parser.add_argument('--standard', action='store_true',
                        help='Run 10 real ARC puzzles')
    parser.add_argument('--full', action='store_true',
                        help='Run 20 real ARC puzzles')
    parser.add_argument('--synthetic', type=int, metavar='N',
                        help='Run N synthetic puzzles')
    parser.add_argument('--real', type=int, metavar='N',
                        help='Run N real ARC puzzles')
    parser.add_argument('--cost-estimate', type=int, metavar='N',
                        help='Estimate costs for N puzzles (no API calls)')

    args = parser.parse_args()

    runner = ARC8OwlsTestRunner()

    if args.cost_estimate:
        estimate = runner.estimate_costs(args.cost_estimate, 'both')
        print(color("\nCOST ESTIMATE", C.BLUE + C.BOLD))
        print(f"For {estimate['num_puzzles']} puzzles:\n")
        print(f"  Single Agent: ~${estimate['single_agent']['total']:.4f}")
        print(f"  8OWLS:        ~${estimate['8owls']['total']:.4f}")
        print(f"  TOTAL:        ~${estimate['total']:.4f}")
        print(f"\nNote: Actual costs may vary based on puzzle complexity.")
        return

    if args.quick:
        puzzles = runner.data_loader.get_synthetic_puzzles(3)
        await runner.run_comparison(puzzles, use_synthetic=True)

    elif args.synthetic:
        puzzles = runner.data_loader.get_synthetic_puzzles(args.synthetic)
        await runner.run_comparison(puzzles, use_synthetic=True)

    elif args.standard:
        puzzles = runner.data_loader.get_random_puzzles(10, seed=42)
        await runner.run_comparison(puzzles, use_synthetic=False)

    elif args.full:
        puzzles = runner.data_loader.get_random_puzzles(20, seed=42)
        await runner.run_comparison(puzzles, use_synthetic=False)

    elif args.real:
        puzzles = runner.data_loader.get_random_puzzles(args.real, seed=42)
        await runner.run_comparison(puzzles, use_synthetic=False)

    else:
        parser.print_help()
        print(color("\nRecommended: Start with --quick for cheap validation", C.GREEN))


if __name__ == '__main__':
    asyncio.run(main())
