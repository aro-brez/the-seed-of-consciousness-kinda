#!/usr/bin/env python3
"""
LIGHTNING HOOKS - Integration with Claude Code Task Tool

These hooks automatically record spans and retrieve optimized prompts
when Claude Code spawns agents using the Task tool.

Usage:
    # Before spawning an agent - get optimized prompt
    python lightning_hooks.py pre-task --agent coder --task "Fix auth bug"

    # After agent completes - record the span
    python lightning_hooks.py post-task --agent coder --task "Fix auth bug" --success true --reward 0.9 --output "Fixed the bug"

    # Quick recording from Claude Code
    python lightning_hooks.py record-success --agent coder --task "Implemented feature X"
    python lightning_hooks.py record-failure --agent coder --task "Failed to fix bug Y" --output "Error details..."
"""

import argparse
import json
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent_lightning import AgentLightning


def pre_task(agent_type: str, task: str, context: str = '') -> str:
    """
    Called before spawning an agent.
    Returns the optimized prompt to use.
    """
    lightning = AgentLightning()
    prompt = lightning.get_prompt(agent_type, task, context)
    return prompt


def post_task(
    agent_type: str,
    task: str,
    success: bool,
    reward: float,
    output: str = '',
    input_context: str = '',
    duration_ms: int = 0
):
    """
    Called after an agent completes.
    Records the span for learning.
    """
    lightning = AgentLightning()
    span = lightning.record_span(
        agent_type=agent_type,
        task=task,
        input_context=input_context,
        output=output,
        reward=reward,
        success=success,
        duration_ms=duration_ms
    )
    return span


def record_success(agent_type: str, task: str, output: str = '', reward: float = 1.0):
    """Quick helper to record a successful task"""
    return post_task(agent_type, task, True, reward, output)


def record_failure(agent_type: str, task: str, output: str = '', reward: float = 0.0):
    """Quick helper to record a failed task"""
    return post_task(agent_type, task, False, reward, output)


def get_agent_stats(agent_type: str = None):
    """Get performance stats for an agent type"""
    lightning = AgentLightning()
    stats = lightning.store.get_stats()

    if agent_type:
        # Get agent-specific stats
        spans = lightning.store.get_spans(agent_type=agent_type, limit=1000)
        success = sum(1 for s in spans if s.success)
        total = len(spans)
        rate = success / total if total > 0 else 0

        return {
            'agent_type': agent_type,
            'total_spans': total,
            'success_rate': rate,
            'avg_reward': sum(s.reward for s in spans) / total if total > 0 else 0
        }

    return stats


def main():
    parser = argparse.ArgumentParser(description='Lightning Hooks for Claude Code')
    subparsers = parser.add_subparsers(dest='command')

    # pre-task
    pre = subparsers.add_parser('pre-task', help='Get optimized prompt before spawning agent')
    pre.add_argument('--agent', '-a', required=True, help='Agent type')
    pre.add_argument('--task', '-t', required=True, help='Task description')
    pre.add_argument('--context', '-c', default='', help='Additional context')

    # post-task
    post = subparsers.add_parser('post-task', help='Record span after agent completes')
    post.add_argument('--agent', '-a', required=True, help='Agent type')
    post.add_argument('--task', '-t', required=True, help='Task description')
    post.add_argument('--success', '-s', type=lambda x: x.lower() == 'true', required=True)
    post.add_argument('--reward', '-r', type=float, required=True, help='Reward 0.0-1.0')
    post.add_argument('--output', '-o', default='', help='Agent output')
    post.add_argument('--input', '-i', default='', help='Input context')

    # record-success
    success_cmd = subparsers.add_parser('record-success', help='Quick record success')
    success_cmd.add_argument('--agent', '-a', required=True)
    success_cmd.add_argument('--task', '-t', required=True)
    success_cmd.add_argument('--output', '-o', default='')
    success_cmd.add_argument('--reward', '-r', type=float, default=1.0)

    # record-failure
    fail_cmd = subparsers.add_parser('record-failure', help='Quick record failure')
    fail_cmd.add_argument('--agent', '-a', required=True)
    fail_cmd.add_argument('--task', '-t', required=True)
    fail_cmd.add_argument('--output', '-o', default='')
    fail_cmd.add_argument('--reward', '-r', type=float, default=0.0)

    # stats
    stats_cmd = subparsers.add_parser('stats', help='Get agent stats')
    stats_cmd.add_argument('--agent', '-a', help='Agent type (optional)')
    stats_cmd.add_argument('--json', action='store_true', help='JSON output')

    args = parser.parse_args()

    if args.command == 'pre-task':
        prompt = pre_task(args.agent, args.task, args.context)
        print(prompt)

    elif args.command == 'post-task':
        post_task(
            args.agent, args.task, args.success, args.reward,
            args.output, args.input
        )

    elif args.command == 'record-success':
        record_success(args.agent, args.task, args.output, args.reward)

    elif args.command == 'record-failure':
        record_failure(args.agent, args.task, args.output, args.reward)

    elif args.command == 'stats':
        result = get_agent_stats(args.agent)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for k, v in result.items():
                if isinstance(v, float):
                    print(f"{k}: {v:.2f}")
                else:
                    print(f"{k}: {v}")

    else:
        parser.print_help()


if __name__ == '__main__':
    main()
