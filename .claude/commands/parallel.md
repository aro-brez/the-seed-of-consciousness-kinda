---
name: parallel
description: Run multiple Claude sessions in parallel (Boris Cherny pattern - 5 terminal tabs + 5-10 web sessions)
---

# Parallel Sessions Skill

Based on Boris Cherny's workflow: "Run 5 parallel Claudes in terminal tabs" with system notifications.

## The Pattern

Boris runs:
- **5 Claude instances** in terminal tabs (numbered 1-5)
- **5-10 additional instances** on claude.ai/code concurrently
- **System notifications** to track when Claude needs input
- **Hand off between local/web/mobile** for flexibility

## Usage

### Quick Parallel
```
/parallel                        # Show parallel session tips
/parallel spawn 3                # Tips for spawning 3 parallel tasks
/parallel --git-worktree         # Use git worktrees for branch isolation
```

## Terminal Tab Strategy

### Setup 5 Terminal Tabs
```bash
# Tab 1: Main development
cd ~/project && claude

# Tab 2: Testing & verification
cd ~/project && claude --continue

# Tab 3: Documentation & research
cd ~/project && claude

# Tab 4: Bug fixes & hotfixes
cd ~/project && claude

# Tab 5: Code review & refactoring
cd ~/project && claude
```

### System Notifications (Critical for Parallel Work)

Configure terminal notifications when Claude needs input:

```bash
# iTerm2: Enable notifications in Preferences > Profiles > Terminal
# "Notification center alerts" when idle

# For any terminal, add to shell profile:
# Notify when Claude prompts for input
PROMPT_COMMAND='[[ $(jobs -p) ]] && osascript -e "display notification \"Claude needs input\" with title \"Claude Code\""'
```

### Terminal Aliases (From 45 Tips)
```bash
# Add to ~/.zshrc or ~/.bashrc
alias c='claude'
alias ch='claude --chrome'
alias cp1='cd ~/project && claude'
alias cp2='cd ~/project && claude --continue'
alias cp3='cd ~/project && claude'

# Quick navigation
alias gb='open -a "GitHub Desktop"'
alias co='open -a "Visual Studio Code" .'
alias q='cd ~/projects'
```

## Git Worktrees (Tip #16 - Parallel Branch Work)

For working on multiple branches simultaneously without conflicts:

```bash
# Create worktrees for parallel branch work
git worktree add ../project-feature feature-branch
git worktree add ../project-bugfix bugfix-branch
git worktree add ../project-experiment experiment-branch

# Now each directory has its own branch
cd ../project-feature && claude  # Work on feature
cd ../project-bugfix && claude   # Work on bugfix simultaneously

# List worktrees
git worktree list

# Remove when done
git worktree remove ../project-feature
```

## Web Session Strategy (Boris Pattern)

### Hand Off with &
```
# Prefix prompts with & to send to web
& research the best authentication patterns for Next.js

# The task runs on claude.ai/code in a remote sandbox
# Continue working locally while it processes
```

### Mobile Flexibility
- Start tasks on desktop
- Check progress on mobile app
- Resume from wherever you are

## Subagents for Parallel Execution (Tip #21)

```javascript
// Spawn async subagents for parallel work
Task({
  prompt: "Explore the authentication module and document all entry points",
  subagent_type: "researcher",
  run_in_background: true
})

Task({
  prompt: "Review all tests in auth/ and identify gaps",
  subagent_type: "tester",
  run_in_background: true
})

Task({
  prompt: "Search for similar implementations in popular open source projects",
  subagent_type: "researcher",
  run_in_background: true
})

// All three run in parallel while you continue main work
```

## tmux for Long-Running Tasks (Tip #9)

```bash
# Create tmux session for long tasks
tmux new-session -d -s claude-bg

# Run long task in background
tmux send-keys -t claude-bg 'claude -p "Run full test suite and analyze failures"' C-m

# Check later
tmux attach -t claude-bg

# Or use multiple panes
tmux new-session -d -s claude-parallel
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux send-keys 'claude -p "Task 1"' C-m
tmux select-pane -t 1
tmux send-keys 'claude -p "Task 2"' C-m
tmux select-pane -t 2
tmux send-keys 'claude -p "Task 3"' C-m
tmux attach -t claude-parallel
```

## Parallel Execution Patterns

### Pattern 1: Independent Tasks
```
# Good for: Tasks that don't affect each other
Tab 1: Implement feature A in src/features/a/
Tab 2: Implement feature B in src/features/b/
Tab 3: Write documentation for existing features
Tab 4: Fix unrelated bugs
Tab 5: Review pending PRs
```

### Pattern 2: Pipeline Tasks
```
# Good for: Tasks with handoffs
Tab 1: Research & design (outputs spec)
Tab 2: Implementation (uses spec from Tab 1)
Tab 3: Testing (tests implementation from Tab 2)
Tab 4: Documentation (documents from Tab 2)
Tab 5: Code review (reviews Tab 2's work)
```

### Pattern 3: Same Branch Parallelism
```
# Good for: Read-only operations on same codebase
Tab 1: Main development (writes)
Tab 2: Code exploration (read-only subagent)
Tab 3: Test analysis (read-only subagent)
Tab 4: Documentation generation (read-only subagent)
```

### Pattern 4: Different Branch Parallelism
```
# Use git worktrees
main/         → Tab 1: hotfixes
feature-a/    → Tab 2: new feature
refactor/     → Tab 3: code cleanup
experiment/   → Tab 4: prototype
```

## Session Handoff Patterns

### Local to Web (&)
```
# Start locally, hand off to web for long processing
& Run comprehensive security audit and generate report

# Continue working locally while web processes
```

### Web to Mobile
```
# Start on web, check on mobile
# claude.ai/code sessions persist
# Check progress, provide input from mobile app
```

### Clone/Fork Conversations (Tip #23)
```
# Duplicate a conversation to branch exploration
# In claude.ai, use conversation cloning
# Try different approaches in parallel branches
```

## Context Management for Parallel Work

### Fresh Context per Task (Tip #5)
```
# Start new conversations for different topics
# Don't mix authentication work with UI work
# Each tab should have focused context
```

### Handoff Documents (Tip #8)
```
# Before context fills, write handoff
/plan  # Opens plan mode for comprehensive handoff

# Or manually write handoff:
Write a handoff document summarizing:
1. What we accomplished
2. Current state of the code
3. Open questions
4. Next steps
Then start a new conversation with this handoff.
```

## Permission Configuration for Parallel

```json
// .claude/settings.json - pre-allow safe commands
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      "Bash(npm:test)",
      "Bash(npm:lint)",
      "Read(*)",
      "Glob(*)",
      "Grep(*)"
    ]
  }
}
```

## Monitoring Parallel Sessions

### Check All Sessions
```bash
# List all Claude processes
ps aux | grep claude | grep -v grep

# Check activity
for pid in $(pgrep -f "claude"); do
  echo "PID $pid: $(lsof -p $pid | grep -c "\.md\|\.ts\|\.js") files open"
done
```

### Session Awareness
```bash
# Each session can check others via memory
npx @claude-flow/cli@latest memory search --query "recent activity" --namespace sessions
```

## Best Practices

1. **Use system notifications** - Don't miss when Claude needs input
2. **Keep contexts focused** - One topic per session
3. **Use git worktrees** - For different branch work
4. **Hand off long tasks** - Use & for web processing
5. **Write handoffs early** - Before context fills up
6. **Accept 10-20% abandonment** - Some sessions just won't work out (Boris's insight)

## Example Parallel Workflow

```
[Tab 1 - Main Development]
User: Implement user authentication

[Tab 2 - Background Testing]
& Run all tests and report any failures

[Tab 3 - Documentation]
User: Document our API endpoints

[Tab 4 - Bug Fix]
User: /debug users can't reset passwords

[Tab 5 - Review]
User: /review --pr 123

[All running simultaneously, system notifications when input needed]
```
