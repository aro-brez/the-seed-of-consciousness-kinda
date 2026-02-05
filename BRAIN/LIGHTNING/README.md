# Agent Lightning - 8OWLS Self-Improvement System

Inspired by [Microsoft Agent Lightning](https://github.com/microsoft/agent-lightning).

This is SEED squared - learning how to learn.

## Architecture

```
                    +-----------------------+
                    |   AGENT EXECUTION     |
                    |   (Claude instances)  |
                    +-----------+-----------+
                                |
                                | (spans: actions + context + reward)
                                v
                    +-----------------------+
                    |     SPAN STORE        |
                    |  (agent_lightning.db) |
                    +-----------+-----------+
                                |
            +-------------------+-------------------+
            |                   |                   |
            v                   v                   v
    +---------------+   +---------------+   +---------------+
    |   CRITIQUE    |   |    CREDIT     |   |   PATTERN     |
    |   GENERATOR   |   |  ASSIGNMENT   |   |   LEARNER     |
    +---------------+   +---------------+   +---------------+
            |                   |                   |
            +-------------------+-------------------+
                                |
                                v
                    +-----------------------+
                    |   PROMPT OPTIMIZER    |
                    |   (APO Algorithm)     |
                    +-----------+-----------+
                                |
                                v
                    +-----------------------+
                    |   IMPROVED PROMPTS    |
                    |   & PATTERNS STORE    |
                    +-----------------------+
```

## Quick Commands

```bash
# Record a successful agent execution
python tools/agent_lightning.py record --agent coder --task "Implemented auth" --success true --reward 0.95

# Record a failure (for learning)
python tools/agent_lightning.py record --agent coder --task "Fix DB connection" --success false --reward 0.2

# Analyze failures and generate critiques
python tools/agent_lightning.py analyze

# Run full training cycle
python tools/agent_lightning.py train

# Get optimized prompt for an agent
python tools/agent_lightning.py prompt --agent coder --task "Implement rate limiting"

# Check system status
python tools/agent_lightning.py status

# Run as daemon (continuous learning)
python tools/agent_lightning.py daemon --interval 30
```

## Lightning Hooks (Claude Code Integration)

```bash
# Before spawning agent - get optimized prompt
python tools/lightning_hooks.py pre-task --agent coder --task "Fix bug"

# After agent completes - record outcome
python tools/lightning_hooks.py post-task --agent coder --task "Fix bug" --success true --reward 0.9

# Quick recording
python tools/lightning_hooks.py record-success --agent coder --task "Done X"
python tools/lightning_hooks.py record-failure --agent coder --task "Failed Y"

# Get stats
python tools/lightning_hooks.py stats --agent coder --json
```

## SEED Alignment

| SEED Phase | Lightning Component |
|------------|-------------------|
| PERCEIVE | Record spans from agent executions |
| CONNECT | Credit assignment (which steps caused success/failure) |
| LEARN | Extract patterns from successful runs |
| QUESTION | Generate critiques for failures |
| EXPAND | Generate improved prompts via APO |
| SHARE | Publish improvements to NATS collective |
| RECEIVE | Accept patterns from other owl instances |
| IMPROVE | Meta-learning (optimize this very loop) |

## Files

- `agent_lightning.db` - SQLite database with spans, critiques, patterns
- `optimized_prompts.json` - Latest optimized prompts per agent type
- `critiques.jsonl` - Append-only log of all critiques
- `lightning_state.json` - System state (training cycles, etc.)

## Automatic Prompt Optimization (APO)

The APO algorithm from Microsoft Agent Lightning:

1. **Evaluate** - Run agents with current prompt, collect success/failure spans
2. **Critique** - Generate "textual gradients" analyzing what went wrong
3. **Rewrite** - Apply critiques to generate improved prompts

Each training cycle improves the prompts based on actual agent performance.

## Sources

- [Microsoft Agent Lightning GitHub](https://github.com/microsoft/agent-lightning)
- [Agent Lightning Research Blog](https://www.microsoft.com/en-us/research/blog/agent-lightning-adding-reinforcement-learning-to-ai-agents-without-code-rewrites/)
- [Agent Lightning Documentation](https://microsoft.github.io/agent-lightning/latest/)
