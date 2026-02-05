---
name: plan
description: Plan Mode workflow - interview, spec, then execute (Boris Cherny + Thariq pattern)
---

# Plan Mode Skill

Based on Boris Cherny's workflow: "Most sessions start in Plan mode (shift+tab twice)...go back and forth with Claude until I like its plan"

## The Pattern

1. **START IN PLAN MODE** - Don't code immediately
2. **INTERVIEW** - Let Claude ask clarifying questions
3. **ITERATE ON PLAN** - Go back and forth until plan is solid
4. **SWITCH TO EXECUTE** - Auto-accept edits mode
5. **VERIFY** - Give Claude ways to verify its work

## Usage

### Quick Plan
```
/plan                            # Enter planning mode
/plan [feature description]      # Start planning a feature
/plan --interview                # Use AskUserQuestionTool pattern
/plan --spec                     # Generate detailed spec
```

### Options
```
/plan --depth shallow           # Quick planning
/plan --depth deep              # Comprehensive planning
/plan --export                  # Export plan to file
```

## The Interview Pattern (Thariq's Approach)

> "Start with a minimal spec or prompt and ask Claude to interview you using the AskUserQuestionTool, then make a new session to execute the spec"

### Step 1: Initial Prompt
```
I want to build [feature]. Please interview me to understand the requirements fully before we start implementing. Ask me questions one at a time.
```

### Step 2: Claude Interviews
```
Claude: I'd like to understand your requirements better. Let me ask some questions:

1. Who are the primary users of this feature?
   [User answers]

2. What's the expected scale? (users/day, data volume)
   [User answers]

3. Are there existing systems this needs to integrate with?
   [User answers]

4. What's the timeline and priority?
   [User answers]

5. Any specific technology constraints?
   [User answers]
```

### Step 3: Generate Spec
```
Based on our discussion, here's the proposed spec:

## Feature: [Name]

### Overview
[Summary of what we're building]

### Requirements
1. [Requirement 1]
2. [Requirement 2]
3. [Requirement 3]

### Technical Approach
- Architecture: [approach]
- Key components: [list]
- Dependencies: [list]

### Success Criteria
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

### Risks & Mitigations
- Risk 1: [risk] → Mitigation: [mitigation]

Do you approve this spec to proceed with implementation?
```

## Plan Mode Workflow

### Enter Plan Mode
```
Press: Shift+Tab (twice)

# Or start with plan mode explicitly
claude --plan
```

### Iterate on Plan
```
You: Here's what I'm thinking: [initial idea]

Claude: [Proposes plan with phases]

You: I don't like the approach for phase 2, what about [alternative]?

Claude: [Revises plan]

You: Better. What about testing?

Claude: [Adds testing strategy]

You: Looks good. Let's execute.
```

### Switch to Execute
```
# Once plan is approved, switch to auto-accept
Press: Tab (to switch modes)

# Or explicitly
/execute
```

## Planning Templates

### Feature Planning
```markdown
# Feature Plan: [Name]

## 1. Objective
What are we trying to achieve?

## 2. User Stories
- As a [user], I want to [action] so that [benefit]

## 3. Technical Design
### Architecture
[Diagram or description]

### Components
- Component A: [purpose]
- Component B: [purpose]

### Data Model
[Schema or description]

### API Design
[Endpoints or interfaces]

## 4. Implementation Phases

### Phase 1: Foundation
- [ ] Task 1.1
- [ ] Task 1.2
Duration: X days

### Phase 2: Core Features
- [ ] Task 2.1
- [ ] Task 2.2
Duration: X days

### Phase 3: Polish & Testing
- [ ] Task 3.1
- [ ] Task 3.2
Duration: X days

## 5. Testing Strategy
- Unit tests: [approach]
- Integration tests: [approach]
- E2E tests: [approach]

## 6. Success Metrics
- Metric 1: [target]
- Metric 2: [target]

## 7. Risks
| Risk | Impact | Mitigation |
|------|--------|------------|
| Risk 1 | High | Mitigation 1 |
```

### Bug Fix Planning
```markdown
# Bug Fix Plan: [Issue]

## 1. Problem Statement
What's happening vs what should happen?

## 2. Reproduction Steps
1. Step 1
2. Step 2
3. Bug manifests

## 3. Root Cause Analysis
[Analysis of why this is happening]

## 4. Proposed Fix
[Technical approach]

## 5. Verification
- [ ] Test that reproduces bug
- [ ] Test passes after fix
- [ ] No regression in related areas

## 6. Files to Modify
- file1.ts: [change]
- file2.ts: [change]
```

### Refactoring Planning
```markdown
# Refactoring Plan: [Area]

## 1. Current State
[What's wrong with the current code]

## 2. Target State
[What good looks like]

## 3. Approach
[ ] Incremental / [ ] Big bang

## 4. Steps
1. Add tests for existing behavior
2. Refactor step 1
3. Verify tests pass
4. Refactor step 2
5. Verify tests pass
[...]

## 5. Risk Assessment
- Breaking changes: [yes/no]
- Data migration needed: [yes/no]
- Downtime required: [yes/no]
```

## Plans Storage

### Save Plan
```bash
# Plans are auto-saved to ~/.claude/plans/
# Named by timestamp and topic

# Manual export
/plan --export plans/feature-auth.md
```

### Review Past Plans
```bash
# List recent plans
ls -la ~/.claude/plans/

# Search plans
grep -r "authentication" ~/.claude/plans/
```

### Store in Memory
```bash
npx @claude-flow/cli@latest memory store \
  --namespace plans \
  --key "plan-auth-$(date +%s)" \
  --value "$(cat plans/feature-auth.md)"
```

## Swarm Planning

For complex features, spawn planning agents:

```javascript
// Research current patterns
Task({
  prompt: "Research existing authentication patterns in this codebase. Document what's already implemented.",
  subagent_type: "researcher",
  model: "haiku",
  run_in_background: true
})

// Architecture review
Task({
  prompt: "Review proposed authentication architecture. Identify potential issues and suggest improvements.",
  subagent_type: "architect",
  model: "haiku",
  run_in_background: true
})

// Security review
Task({
  prompt: "Review authentication plan from security perspective. Identify vulnerabilities and mitigations.",
  subagent_type: "security-auditor",
  model: "haiku",
  run_in_background: true
})
```

## Plan to Spec to Execute

### Complete Workflow
```
[Session 1: Planning]
1. /plan --interview
2. Answer Claude's questions
3. Iterate on spec
4. Export spec

[Session 2: Execution]
1. Provide spec as context
2. Switch to auto-accept mode
3. Execute phase by phase
4. Verify each phase
```

## Best Practices

1. **Don't skip planning** - Even for "simple" features
2. **Write it down** - Plans catch misunderstandings early
3. **Iterate before executing** - Cheaper to fix plans than code
4. **Break into phases** - Easier to verify and rollback
5. **Include verification** - How will you know it works?
6. **Consider edge cases** - What could go wrong?

## Example Session

```
User: /plan I want to add real-time notifications

Claude: I'll help you plan this feature. Let me ask some questions first.

Q1: What types of notifications do you need?
(a) In-app only (b) Push notifications (c) Email (d) All of the above

User: In-app and push

Claude: Q2: What events should trigger notifications?

User: New messages, mentions, and task assignments

Claude: Q3: What's your current stack? (for real-time: WebSockets, SSE, polling?)

User: We use Next.js, thinking about Socket.io or Pusher

Claude: Based on our discussion, here's the proposed plan:

# Notification System Plan

## Objective
Real-time in-app and push notifications for messages, mentions, and tasks.

## Architecture
- Backend: Socket.io server alongside Next.js API
- Frontend: Socket.io client + Service Worker for push
- Storage: Redis for pub/sub, PostgreSQL for persistence

## Phases

### Phase 1: In-App Notifications (3 days)
- [ ] Socket.io server setup
- [ ] Client connection management
- [ ] Notification UI component
- [ ] Basic notification types

### Phase 2: Push Notifications (2 days)
- [ ] Service Worker registration
- [ ] Push subscription management
- [ ] FCM integration
- [ ] Fallback for unsupported browsers

### Phase 3: Notification Management (2 days)
- [ ] Mark as read/unread
- [ ] Notification preferences
- [ ] Do not disturb mode
- [ ] Notification history

## Verification
- [ ] Unit tests for notification service
- [ ] Integration tests for Socket.io
- [ ] E2E tests for notification flow

Do you approve this plan to proceed?

User: Looks good, let's start with Phase 1

Claude: Switching to execution mode...
[Begins implementation]
```
