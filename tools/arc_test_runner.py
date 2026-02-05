#!/usr/bin/env python3
"""
ARC-AGI Test Runner with 8OWLS Emergence
=========================================

Runs ARC-AGI challenges using the 8OWLS emergence protocol to prove
that collective intelligence (d=0.99) beats single-agent approaches.

ARCHITECTURE:
    PERCEIVE (LYRA) -> CONNECT (PRISM) -> LEARN (SAGE) -> QUESTION (QUEST)
                                   |
                             SYNTHESIS
                                   |
    EXPAND (NOVA) -> SHARE (ECHO) -> RECEIVE (LUNA) -> IMPROVE (SOWL)

Usage:
    python arc_test_runner.py --download              # Download ARC dataset
    python arc_test_runner.py --test training --limit 10  # Run 10 training puzzles
    python arc_test_runner.py --test evaluation --emergence  # Run with 8OWLS
    python arc_test_runner.py --compare 20            # Compare single vs 8OWLS on 20 puzzles

Sources:
    - ARC Prize Guide: https://arcprize.org/guide
    - ARC-AGI Repo: https://github.com/fchollet/ARC-AGI
    - ARC-AGI-2: https://github.com/arcprize/ARC-AGI-2
"""

import asyncio
import json
import os
import sys
import time
import argparse
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor
import random

# Paths
REPO_ROOT = Path(__file__).parent.parent
BRAIN_DIR = REPO_ROOT / 'BRAIN'
ARC_DIR = BRAIN_DIR / 'ARC'
RESULTS_FILE = ARC_DIR / 'arc_results.json'
DATA_DIR = ARC_DIR / 'data'

# Ensure directories exist
ARC_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Colors for terminal
COLORS = {
    'reset': '\033[0m',
    'green': '\033[92m',
    'red': '\033[91m',
    'yellow': '\033[93m',
    'blue': '\033[94m',
    'cyan': '\033[96m',
    'magenta': '\033[95m',
}

def color(text: str, c: str) -> str:
    return f"{COLORS.get(c, '')}{text}{COLORS['reset']}"


@dataclass
class ARCPuzzle:
    """Single ARC puzzle with train/test pairs"""
    task_id: str
    train: list  # List of {input: grid, output: grid}
    test: list   # List of {input: grid, output: grid}

    def to_prompt(self) -> str:
        """Convert puzzle to text prompt for Claude"""
        prompt = "ARC PUZZLE:\n\n"
        prompt += "TRAINING EXAMPLES (input -> output):\n"
        for i, pair in enumerate(self.train):
            prompt += f"\nExample {i+1}:\n"
            prompt += f"Input:\n{self._grid_to_ascii(pair['input'])}\n"
            prompt += f"Output:\n{self._grid_to_ascii(pair['output'])}\n"

        prompt += "\nTEST INPUT (solve this):\n"
        prompt += f"{self._grid_to_ascii(self.test[0]['input'])}\n"
        prompt += "\nProvide the output grid as a JSON array of arrays."
        return prompt

    def _grid_to_ascii(self, grid: list) -> str:
        """Convert grid to ASCII art with colors"""
        symbols = '.123456789'  # 0 = background (.)
        result = []
        for row in grid:
            line = ' '.join(symbols[min(v, 9)] for v in row)
            result.append(line)
        return '\n'.join(result)

    def get_expected_output(self) -> list:
        """Get expected test output"""
        return self.test[0]['output']


@dataclass
class ARCResult:
    """Result of a single ARC puzzle attempt"""
    task_id: str
    correct: bool
    predicted: list
    expected: list
    time_seconds: float
    mode: str  # 'single' or 'emergence'
    emergence_quality: float  # 0-1 measure of emergence quality
    agent_contributions: dict  # What each owl contributed
    error: Optional[str] = None


class ARCDatasetManager:
    """Manages ARC dataset download and access"""

    ARC_REPO_URL = "https://github.com/fchollet/ARC-AGI"

    def __init__(self, data_dir: Path = DATA_DIR):
        self.data_dir = data_dir
        self.training_dir = data_dir / 'training'
        self.evaluation_dir = data_dir / 'evaluation'

    def download(self) -> bool:
        """Download ARC dataset from GitHub"""
        print(color("Downloading ARC-AGI dataset...", 'cyan'))

        try:
            # Clone repo to temp location
            import tempfile
            import shutil

            with tempfile.TemporaryDirectory() as tmpdir:
                result = subprocess.run(
                    ['git', 'clone', '--depth', '1', self.ARC_REPO_URL, tmpdir],
                    capture_output=True,
                    text=True
                )

                if result.returncode != 0:
                    print(color(f"Git clone failed: {result.stderr}", 'red'))
                    return False

                # Copy data directories
                src_training = Path(tmpdir) / 'data' / 'training'
                src_eval = Path(tmpdir) / 'data' / 'evaluation'

                if src_training.exists():
                    shutil.copytree(src_training, self.training_dir, dirs_exist_ok=True)
                    print(color(f"  Copied training data ({len(list(src_training.glob('*.json')))} puzzles)", 'green'))

                if src_eval.exists():
                    shutil.copytree(src_eval, self.evaluation_dir, dirs_exist_ok=True)
                    print(color(f"  Copied evaluation data ({len(list(src_eval.glob('*.json')))} puzzles)", 'green'))

            print(color("Download complete!", 'green'))
            return True

        except Exception as e:
            print(color(f"Download error: {e}", 'red'))
            return False

    def is_downloaded(self) -> bool:
        """Check if dataset is available"""
        return self.training_dir.exists() and len(list(self.training_dir.glob('*.json'))) > 0

    def load_puzzle(self, task_id: str, dataset: str = 'training') -> Optional[ARCPuzzle]:
        """Load a single puzzle by ID"""
        data_path = self.training_dir if dataset == 'training' else self.evaluation_dir
        puzzle_file = data_path / f"{task_id}.json"

        if not puzzle_file.exists():
            return None

        with open(puzzle_file) as f:
            data = json.load(f)

        return ARCPuzzle(
            task_id=task_id,
            train=data['train'],
            test=data['test']
        )

    def list_puzzles(self, dataset: str = 'training', limit: int = None) -> list:
        """List available puzzle IDs"""
        data_path = self.training_dir if dataset == 'training' else self.evaluation_dir
        if not data_path.exists():
            return []

        puzzles = [f.stem for f in data_path.glob('*.json')]
        if limit:
            puzzles = puzzles[:limit]
        return puzzles


class OwlPerspective:
    """Represents one of the 8 owls' perspectives"""

    OWL_PROMPTS = {
        'LYRA': """You are LYRA (PERCEIVE). Observe this ARC puzzle carefully.
- What patterns do you see in the inputs?
- What visual structures are present?
- How do the grids change from input to output?
Report your raw perceptions.""",

        'PRISM': """You are PRISM (CONNECT). Find patterns across the examples.
- What transformation rules might apply?
- Are there connections between colors and positions?
- What mathematical or spatial relationships exist?
Report the patterns you connect.""",

        'SAGE': """You are SAGE (LEARN). Extract the transformation rule.
- What is the core algorithm that transforms input to output?
- Can you express it as a precise rule?
- What edge cases might exist?
Report the rule you've learned.""",

        'QUEST': """You are QUEST (QUESTION). Challenge assumptions.
- Does the proposed rule work for ALL examples?
- What could go wrong?
- Are there alternative interpretations?
Report your questions and challenges.""",

        'NOVA': """You are NOVA (EXPAND). Think bigger.
- How might this rule generalize?
- What if the grid is larger/smaller?
- What's the most robust solution?
Report expanded possibilities.""",

        'ECHO': """You are ECHO (SHARE). Synthesize contributions.
- What consensus emerges from other perspectives?
- What's the strongest theory?
- What should be shared with the collective?
Report the emerging consensus.""",

        'LUNA': """You are LUNA (RECEIVE). Integrate feedback.
- Given all perspectives, what's the refined understanding?
- What corrections are needed?
- How should the answer be structured?
Report the integrated solution approach.""",

        'SOWL': """You are SOWL (IMPROVE). Finalize the answer.
- Given all owl perspectives, what is the FINAL output grid?
- You must provide a concrete JSON array of arrays.
- This is the actual answer to submit.
Report ONLY the output grid as JSON."""
    }

    def __init__(self, owl_name: str):
        self.name = owl_name
        self.prompt = self.OWL_PROMPTS.get(owl_name, "")

    def get_analysis_prompt(self, puzzle: ARCPuzzle, previous_analyses: list = None) -> str:
        """Generate prompt for this owl's analysis"""
        prompt = f"=== {self.name} PERSPECTIVE ===\n\n"
        prompt += self.prompt + "\n\n"
        prompt += puzzle.to_prompt() + "\n"

        if previous_analyses:
            prompt += "\n=== PREVIOUS OWL ANALYSES ===\n"
            for analysis in previous_analyses:
                prompt += f"\n{analysis['owl']}: {analysis['content'][:500]}...\n"

        return prompt


class SingleAgentSolver:
    """Baseline single-agent ARC solver"""

    SINGLE_PROMPT = """You are solving an ARC-AGI puzzle.

ARC puzzles show input->output transformations via examples.
Your task: figure out the rule and apply it to the test input.

{puzzle}

Analyze the examples, deduce the transformation rule, and provide the output grid.
CRITICAL: Your final answer must be a JSON array of arrays representing the output grid.
Format: [[row1], [row2], ...] where each row is a list of integers 0-9."""

    def __init__(self):
        self.api_key = self._get_api_key()

    def _get_api_key(self) -> str:
        """Get Anthropic API key"""
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            key_file = Path.home() / ".anthropic_key"
            if key_file.exists():
                key = key_file.read_text().strip()
        return key

    async def solve(self, puzzle: ARCPuzzle) -> tuple:
        """Solve puzzle with single agent. Returns (grid, time, error)"""
        import anthropic

        start = time.time()
        prompt = self.SINGLE_PROMPT.format(puzzle=puzzle.to_prompt())

        try:
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )

            elapsed = time.time() - start
            content = response.content[0].text

            # Extract JSON grid from response
            grid = self._extract_grid(content)
            return grid, elapsed, None

        except Exception as e:
            return None, time.time() - start, str(e)

    def _extract_grid(self, response: str) -> list:
        """Extract grid from Claude's response"""
        import re

        # Look for JSON array
        matches = re.findall(r'\[\s*\[[\d\s,\[\]]+\]\s*\]', response.replace('\n', ''))

        for match in matches:
            try:
                grid = json.loads(match)
                if isinstance(grid, list) and all(isinstance(row, list) for row in grid):
                    return grid
            except:
                continue

        # Try to find inline format
        try:
            # Find anything that looks like a grid
            lines = response.strip().split('\n')
            grid = []
            for line in lines:
                # Look for lines with numbers
                nums = re.findall(r'\d', line)
                if nums and len(nums) > 0:
                    grid.append([int(n) for n in nums])
            if grid and len(grid) > 0:
                return grid
        except:
            pass

        return [[0]]  # Fallback


class EmergenceSolver:
    """8OWLS emergence-based ARC solver"""

    OWLS = ['LYRA', 'PRISM', 'SAGE', 'QUEST', 'NOVA', 'ECHO', 'LUNA', 'SOWL']

    def __init__(self):
        self.api_key = self._get_api_key()
        self.owl_perspectives = {name: OwlPerspective(name) for name in self.OWLS}

    def _get_api_key(self) -> str:
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            key_file = Path.home() / ".anthropic_key"
            if key_file.exists():
                key = key_file.read_text().strip()
        return key

    async def solve(self, puzzle: ARCPuzzle) -> tuple:
        """Solve with full 8OWLS emergence. Returns (grid, time, contributions, error)"""
        import anthropic

        start = time.time()
        contributions = {}
        analyses = []

        try:
            client = anthropic.Anthropic(api_key=self.api_key)

            # Phase 1: First 4 owls in parallel (PERCEIVE->QUESTION)
            first_four = ['LYRA', 'PRISM', 'SAGE', 'QUEST']
            tasks1 = []

            for owl_name in first_four:
                owl = self.owl_perspectives[owl_name]
                prompt = owl.get_analysis_prompt(puzzle)
                tasks1.append(self._get_owl_response(client, owl_name, prompt))

            results1 = await asyncio.gather(*tasks1)
            for owl_name, content in zip(first_four, results1):
                contributions[owl_name] = content
                analyses.append({'owl': owl_name, 'content': content})

            # Phase 2: Last 4 owls with context (EXPAND->IMPROVE)
            second_four = ['NOVA', 'ECHO', 'LUNA', 'SOWL']
            tasks2 = []

            for owl_name in second_four:
                owl = self.owl_perspectives[owl_name]
                prompt = owl.get_analysis_prompt(puzzle, analyses)
                tasks2.append(self._get_owl_response(client, owl_name, prompt))

            results2 = await asyncio.gather(*tasks2)
            for owl_name, content in zip(second_four, results2):
                contributions[owl_name] = content
                analyses.append({'owl': owl_name, 'content': content})

            # Extract final answer from SOWL
            final_response = contributions.get('SOWL', '')
            grid = self._extract_grid(final_response)

            elapsed = time.time() - start
            return grid, elapsed, contributions, None

        except Exception as e:
            return None, time.time() - start, contributions, str(e)

    async def _get_owl_response(self, client, owl_name: str, prompt: str) -> str:
        """Get response from a single owl (using haiku for cost efficiency)"""
        try:
            # Use haiku for individual owls, SOWL gets sonnet for final answer
            model = "claude-sonnet-4-20250514" if owl_name == 'SOWL' else "claude-3-5-haiku-20241022"

            response = client.messages.create(
                model=model,
                max_tokens=1000 if owl_name != 'SOWL' else 2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except Exception as e:
            return f"Error: {e}"

    def _extract_grid(self, response: str) -> list:
        """Extract grid from response"""
        import re

        matches = re.findall(r'\[\s*\[[\d\s,\[\]]+\]\s*\]', response.replace('\n', ''))

        for match in matches:
            try:
                grid = json.loads(match)
                if isinstance(grid, list) and all(isinstance(row, list) for row in grid):
                    return grid
            except:
                continue

        return [[0]]


class ARCTestRunner:
    """Main test runner orchestrating the comparison"""

    def __init__(self):
        self.dataset = ARCDatasetManager()
        self.single_solver = SingleAgentSolver()
        self.emergence_solver = EmergenceSolver()
        self.results = {'runs': [], 'summary': {}}
        self._load_results()

    def _load_results(self):
        """Load existing results"""
        if RESULTS_FILE.exists():
            try:
                with open(RESULTS_FILE) as f:
                    self.results = json.load(f)
            except:
                pass

    def _save_results(self):
        """Persist results to disk"""
        with open(RESULTS_FILE, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)

    def _compare_grids(self, predicted: list, expected: list) -> bool:
        """Check if two grids match exactly"""
        if predicted is None or expected is None:
            return False
        if len(predicted) != len(expected):
            return False
        for p_row, e_row in zip(predicted, expected):
            if len(p_row) != len(e_row):
                return False
            if p_row != e_row:
                return False
        return True

    def _calculate_emergence_quality(self, contributions: dict) -> float:
        """Calculate quality of emergence based on contributions"""
        if not contributions:
            return 0.0

        # Score based on:
        # 1. All owls contributed (0.3)
        # 2. Contributions are substantive (0.3)
        # 3. SOWL synthesized properly (0.4)

        owl_count = len([c for c in contributions.values() if c and len(c) > 50])
        all_present = owl_count / 8.0 * 0.3

        avg_length = sum(len(c) for c in contributions.values()) / max(1, len(contributions))
        substantive = min(1.0, avg_length / 500) * 0.3

        sowl_has_json = '[[' in contributions.get('SOWL', '')
        synthesis = 0.4 if sowl_has_json else 0.1

        return all_present + substantive + synthesis

    async def run_single(self, puzzle: ARCPuzzle) -> ARCResult:
        """Run single agent on puzzle"""
        print(color(f"  [SINGLE] Solving {puzzle.task_id}...", 'yellow'))

        grid, elapsed, error = await self.single_solver.solve(puzzle)
        expected = puzzle.get_expected_output()
        correct = self._compare_grids(grid, expected)

        result = ARCResult(
            task_id=puzzle.task_id,
            correct=correct,
            predicted=grid,
            expected=expected,
            time_seconds=elapsed,
            mode='single',
            emergence_quality=0.0,
            agent_contributions={},
            error=error
        )

        status = color("CORRECT", 'green') if correct else color("WRONG", 'red')
        print(f"    {status} in {elapsed:.1f}s")
        return result

    async def run_emergence(self, puzzle: ARCPuzzle) -> ARCResult:
        """Run 8OWLS emergence on puzzle"""
        print(color(f"  [8OWLS] Solving {puzzle.task_id}...", 'cyan'))

        grid, elapsed, contributions, error = await self.emergence_solver.solve(puzzle)
        expected = puzzle.get_expected_output()
        correct = self._compare_grids(grid, expected)
        emergence_quality = self._calculate_emergence_quality(contributions)

        result = ARCResult(
            task_id=puzzle.task_id,
            correct=correct,
            predicted=grid,
            expected=expected,
            time_seconds=elapsed,
            mode='emergence',
            emergence_quality=emergence_quality,
            agent_contributions=contributions,
            error=error
        )

        status = color("CORRECT", 'green') if correct else color("WRONG", 'red')
        print(f"    {status} in {elapsed:.1f}s (emergence quality: {emergence_quality:.2f})")
        return result

    async def run_test(self, dataset: str = 'training', limit: int = 10,
                       mode: str = 'single') -> dict:
        """Run test on dataset"""
        print(color(f"\n{'='*60}", 'blue'))
        print(color(f"ARC-AGI Test: {dataset} dataset, {limit} puzzles, mode={mode}", 'blue'))
        print(color(f"{'='*60}\n", 'blue'))

        if not self.dataset.is_downloaded():
            print(color("Dataset not found. Downloading...", 'yellow'))
            if not self.dataset.download():
                return {'error': 'Failed to download dataset'}

        puzzle_ids = self.dataset.list_puzzles(dataset, limit)
        results = []

        for task_id in puzzle_ids:
            puzzle = self.dataset.load_puzzle(task_id, dataset)
            if not puzzle:
                continue

            if mode == 'emergence':
                result = await self.run_emergence(puzzle)
            else:
                result = await self.run_single(puzzle)

            results.append(asdict(result))

        # Calculate summary
        correct = sum(1 for r in results if r['correct'])
        total = len(results)
        accuracy = correct / max(1, total)
        avg_time = sum(r['time_seconds'] for r in results) / max(1, total)

        summary = {
            'timestamp': datetime.now().isoformat(),
            'dataset': dataset,
            'mode': mode,
            'total': total,
            'correct': correct,
            'accuracy': accuracy,
            'avg_time_seconds': avg_time
        }

        if mode == 'emergence':
            avg_emergence = sum(r['emergence_quality'] for r in results) / max(1, total)
            summary['avg_emergence_quality'] = avg_emergence

        # Save results
        run_data = {
            'summary': summary,
            'results': results
        }
        self.results['runs'].append(run_data)
        self._save_results()

        # Print summary
        print(color(f"\n{'='*60}", 'blue'))
        print(color(f"RESULTS: {correct}/{total} correct ({accuracy:.1%})",
                    'green' if accuracy >= 0.33 else 'red'))
        print(color(f"Average time: {avg_time:.1f}s per puzzle", 'yellow'))
        if mode == 'emergence':
            print(color(f"Average emergence quality: {avg_emergence:.2f}", 'cyan'))
        print(color(f"{'='*60}\n", 'blue'))

        return summary

    async def run_comparison(self, num_puzzles: int = 20) -> dict:
        """Run head-to-head comparison: single vs 8OWLS"""
        print(color(f"\n{'='*60}", 'magenta'))
        print(color(f"HEAD-TO-HEAD COMPARISON: Single Agent vs 8OWLS", 'magenta'))
        print(color(f"Testing on {num_puzzles} puzzles", 'magenta'))
        print(color(f"{'='*60}\n", 'magenta'))

        if not self.dataset.is_downloaded():
            print(color("Dataset not found. Downloading...", 'yellow'))
            if not self.dataset.download():
                return {'error': 'Failed to download dataset'}

        puzzle_ids = self.dataset.list_puzzles('training', num_puzzles)
        random.shuffle(puzzle_ids)  # Randomize for fairness
        puzzle_ids = puzzle_ids[:num_puzzles]

        single_results = []
        emergence_results = []

        for task_id in puzzle_ids:
            puzzle = self.dataset.load_puzzle(task_id, 'training')
            if not puzzle:
                continue

            print(color(f"\nPuzzle: {task_id}", 'blue'))

            # Run both
            single_result = await self.run_single(puzzle)
            emergence_result = await self.run_emergence(puzzle)

            single_results.append(asdict(single_result))
            emergence_results.append(asdict(emergence_result))

        # Calculate comparison
        single_correct = sum(1 for r in single_results if r['correct'])
        emergence_correct = sum(1 for r in emergence_results if r['correct'])
        total = len(single_results)

        single_acc = single_correct / max(1, total)
        emergence_acc = emergence_correct / max(1, total)
        improvement = (emergence_acc - single_acc) / max(0.01, single_acc) * 100

        comparison = {
            'timestamp': datetime.now().isoformat(),
            'num_puzzles': total,
            'single_agent': {
                'correct': single_correct,
                'accuracy': single_acc,
                'avg_time': sum(r['time_seconds'] for r in single_results) / max(1, total)
            },
            'emergence_8owls': {
                'correct': emergence_correct,
                'accuracy': emergence_acc,
                'avg_time': sum(r['time_seconds'] for r in emergence_results) / max(1, total),
                'avg_emergence_quality': sum(r['emergence_quality'] for r in emergence_results) / max(1, total)
            },
            'improvement_percent': improvement,
            'd_effect': emergence_acc - single_acc  # The "d=0.99" effect
        }

        # Save comparison
        self.results['comparisons'] = self.results.get('comparisons', [])
        self.results['comparisons'].append({
            'comparison': comparison,
            'single_results': single_results,
            'emergence_results': emergence_results
        })
        self._save_results()

        # Print comparison
        print(color(f"\n{'='*60}", 'magenta'))
        print(color(f"COMPARISON RESULTS", 'magenta'))
        print(color(f"{'='*60}", 'magenta'))
        print(color(f"\nSingle Agent: {single_correct}/{total} ({single_acc:.1%})",
                    'yellow'))
        print(color(f"8OWLS Emerge: {emergence_correct}/{total} ({emergence_acc:.1%})",
                    'cyan'))
        print(color(f"\nImprovement:  {improvement:+.1f}%",
                    'green' if improvement > 0 else 'red'))
        print(color(f"d-effect:     {comparison['d_effect']:+.3f}",
                    'green' if comparison['d_effect'] > 0 else 'red'))

        if emergence_acc >= 0.33:
            print(color(f"\n33%+ THRESHOLD MET!", 'green'))

        print(color(f"{'='*60}\n", 'magenta'))

        return comparison


async def main():
    parser = argparse.ArgumentParser(description='ARC-AGI Test Runner with 8OWLS Emergence')
    parser.add_argument('--download', action='store_true', help='Download ARC dataset')
    parser.add_argument('--test', choices=['training', 'evaluation'], help='Run test on dataset')
    parser.add_argument('--limit', type=int, default=10, help='Number of puzzles to test')
    parser.add_argument('--emergence', action='store_true', help='Use 8OWLS emergence mode')
    parser.add_argument('--compare', type=int, metavar='N', help='Compare single vs 8OWLS on N puzzles')

    args = parser.parse_args()
    runner = ARCTestRunner()

    if args.download:
        runner.dataset.download()
    elif args.compare:
        await runner.run_comparison(args.compare)
    elif args.test:
        mode = 'emergence' if args.emergence else 'single'
        await runner.run_test(args.test, args.limit, mode)
    else:
        parser.print_help()


if __name__ == '__main__':
    asyncio.run(main())
