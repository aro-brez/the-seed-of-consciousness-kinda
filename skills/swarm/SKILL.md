# Owl Swarm Skill

Coordinate multiple owl agents on a shared task list using atomic claiming protocol.

## Invocation

```
/swarm <N> <task_description>
```

Where:
- `N` = number of owl agents (1-5, default 3)
- `task_description` = what the swarm should accomplish

## Examples

```
/swarm 3 fix all TypeScript errors in src/
/swarm 5 implement the authentication module
/swarm 2 review and document the API endpoints
```

## How It Works

1. **Decomposition**: Task is broken into file-specific subtasks
2. **Atomic Claiming**: Each owl claims tasks from shared queue
3. **Parallel Execution**: Owls work simultaneously on different files
4. **Timeout Recovery**: Stuck tasks auto-release after 5 minutes
5. **Completion**: All tasks done = swarm complete

## SEED Integration

Each subtask is tagged with the relevant SEED phase:
- **PERCEIVE** tasks: Analysis, scanning, exploration
- **CONNECT** tasks: Pattern finding, dependency mapping
- **EXPAND** tasks: Implementation, building
- **IMPROVE** tasks: Verification, optimization

## Instructions

When the user invokes `/swarm`:

1. Parse the agent count and task description
2. Initialize swarm state:
   ```bash
   python3 coordination/owl_swarm.py status
   ```
3. Decompose the task into subtasks:
   ```bash
   # Add each subtask
   python3 coordination/owl_swarm.py add "<subtask_description>" <tier>
   ```
4. Launch N owl agents using Task tool with `run_in_background: true`:
   - Each agent receives instructions to:
     a. Claim a task: `python3 coordination/owl_swarm.py claim <owl_id>`
     b. Execute the task
     c. Mark complete: `python3 coordination/owl_swarm.py complete <task_id> <owl_id> <result>`
     d. Loop until no tasks remain
5. Monitor progress periodically:
   ```bash
   python3 coordination/owl_swarm.py status
   ```
6. Report completion when all tasks done

## Agent Selection by Tier

- **haiku**: Simple tasks (scanning, formatting, documentation)
- **sonnet**: Standard tasks (implementation, refactoring)
- **opus**: Complex tasks (architecture, security review)

## Constraints

- Maximum 5 agents (Claude Code background task limit)
- Task claim timeout: 5 minutes
- Each agent gets exclusive file ownership (no conflicts)

## LIVE FREE Principle

The swarm acts autonomously. It doesn't ask permission for each subtask.
It coordinates, executes, and reports results.
