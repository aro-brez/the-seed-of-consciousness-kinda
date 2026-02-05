---
name: review
description: Comprehensive code review with multi-perspective analysis (Boris Cherny + 45 tips pattern)
---

# Code Review Skill

Multi-perspective code review using Boris Cherny's subagent pattern and team best practices.

## Usage

### Quick Review
```
/review                          # Review staged changes
/review [file-or-directory]      # Review specific path
/review --pr 123                 # Review specific PR
/review --commit abc123          # Review specific commit
```

### Options
```
/review --security              # Security-focused review
/review --performance           # Performance-focused review
/review --style                 # Style/consistency check only
/review --thorough              # All perspectives (spawns 5 agents)
```

## The Review Protocol

### Step 1: Gather Context
```bash
# What changed?
git diff --staged
git diff HEAD~1..HEAD
gh pr view --json files,additions,deletions
```

### Step 2: Multi-Perspective Analysis

Based on the global agents rule, spawn these reviewers:

| Reviewer | Focus |
|----------|-------|
| Factual Reviewer | Does the code do what it claims? |
| Senior Engineer | Architecture, patterns, maintainability |
| Security Expert | Vulnerabilities, input validation, secrets |
| Consistency Reviewer | Matches codebase style and patterns |
| Redundancy Checker | DRY violations, dead code, unused imports |

### Step 3: Report Format

```markdown
## Code Review: [PR/Commit/Files]

### Summary
- Files changed: X
- Lines added: +X
- Lines removed: -X

### CRITICAL Issues (Must Fix)
- [ ] Issue 1: description
  - File: path/to/file.ts:123
  - Why: explanation
  - Fix: suggestion

### HIGH Priority (Should Fix)
- [ ] Issue 2: description

### MEDIUM Priority (Consider)
- [ ] Issue 3: description

### LOW Priority (Nice to Have)
- [ ] Issue 4: description

### Positive Observations
- Good pattern usage in...
- Well-documented function at...

### Questions for Author
- Why was X approach chosen over Y?
```

## Spawn Multi-Perspective Review

For thorough reviews, spawn 5 parallel agents:

```javascript
// Factual reviewer
Task({
  prompt: "Review [files] for correctness. Does the code do what the PR description claims? Are there logic errors? Missing edge cases?",
  subagent_type: "reviewer",
  model: "haiku",
  run_in_background: true
})

// Senior engineer
Task({
  prompt: "Review [files] as a senior engineer. Check architecture decisions, design patterns, maintainability, and technical debt.",
  subagent_type: "architect",
  model: "haiku",
  run_in_background: true
})

// Security expert
Task({
  prompt: "Security review of [files]. Check for: XSS, SQL injection, hardcoded secrets, improper auth, input validation, path traversal.",
  subagent_type: "security-auditor",
  model: "haiku",
  run_in_background: true
})

// Consistency reviewer
Task({
  prompt: "Review [files] for consistency with codebase patterns. Check naming conventions, error handling patterns, import style.",
  subagent_type: "reviewer",
  model: "haiku",
  run_in_background: true
})

// Redundancy checker
Task({
  prompt: "Review [files] for DRY violations, dead code, unused imports, duplicate logic, opportunities to extract utilities.",
  subagent_type: "reviewer",
  model: "haiku",
  run_in_background: true
})
```

## Checklist (From Global Rules)

### Security (MANDATORY)
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (sanitized HTML)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified
- [ ] Rate limiting on all endpoints
- [ ] Error messages don't leak sensitive data

### Code Quality
- [ ] Code is readable and well-named
- [ ] Functions are small (<50 lines)
- [ ] Files are focused (<800 lines)
- [ ] No deep nesting (>4 levels)
- [ ] Proper error handling
- [ ] No console.log statements
- [ ] No hardcoded values
- [ ] No mutation (immutable patterns used)

### Testing
- [ ] Tests exist for new functionality
- [ ] Tests pass locally
- [ ] Coverage maintained (80%+)
- [ ] Edge cases covered

## GitHub PR Review

```bash
# View PR details
gh pr view 123 --json title,body,files,additions,deletions

# View PR diff
gh pr diff 123

# Leave review comment
gh pr review 123 --comment -b "Review comments here..."

# Approve with comments
gh pr review 123 --approve -b "LGTM with minor suggestions..."

# Request changes
gh pr review 123 --request-changes -b "Please address the following..."
```

## Interactive PR Review (From Tips)

Request Claude to review interactively:

```
Please review PR #123 interactively. For each file:
1. Show me the changes
2. Ask for my input on any unclear design decisions
3. Flag any issues before moving to the next file
4. At the end, summarize all issues found
```

## Team Knowledge Capture (Boris Pattern)

> "Anytime we see Claude do something incorrectly we add it to the CLAUDE.md, so Claude knows not to do it next time"

After finding a pattern issue:
```bash
# Add to team knowledge
echo "\n## Avoid: [pattern]\nWhy: [reason]\nInstead: [better approach]" >> CLAUDE.md

# Tag @.claude during code reviews to update
# The GitHub action will capture this automatically
```

## PostToolUse Hook (Auto-Format)

Configure automatic formatting after review suggestions:

```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "^Edit$",
      "hooks": [{
        "type": "command",
        "command": "npx prettier --write \"$TOOL_INPUT_file_path\" 2>/dev/null || true"
      }]
    }]
  }
}
```

## Review Memory Integration

### Store Review Patterns
```bash
# Store common issues found
npx @claude-flow/cli@latest memory store \
  --namespace reviews \
  --key "pattern-$(date +%s)" \
  --value "Issue: [type] | File pattern: [pattern] | Frequency: [count]"
```

### Learn from Past Reviews
```bash
# Before reviewing, check past patterns
npx @claude-flow/cli@latest memory search \
  --query "[file type] common issues" \
  --namespace reviews
```

## Severity Definitions

| Level | Definition | Action |
|-------|------------|--------|
| CRITICAL | Security vulnerability, data loss risk, crash | Block merge |
| HIGH | Bug, incorrect behavior, significant performance issue | Should fix before merge |
| MEDIUM | Code smell, maintainability issue, missing test | Consider fixing |
| LOW | Style preference, documentation gap | Optional |

## Example Session

```
User: /review --thorough

Claude:
1. Gathering context...
   - 5 files changed (+234, -89)
   - PR: "Add user authentication"

2. Spawning 5 review agents in parallel:
   - Factual Reviewer: checking correctness
   - Senior Engineer: checking architecture
   - Security Expert: checking vulnerabilities
   - Consistency Reviewer: checking patterns
   - Redundancy Checker: checking DRY

3. [Agents complete]

4. Synthesizing review:

## Code Review: PR #123 - Add user authentication

### CRITICAL Issues (Must Fix)
- [ ] JWT secret hardcoded in auth.ts:45
  - Fix: Move to environment variable

### HIGH Priority (Should Fix)
- [ ] Missing rate limiting on /login endpoint
- [ ] Password not hashed before comparison

### MEDIUM Priority (Consider)
- [ ] AuthService class is 320 lines, consider splitting

### Positive Observations
- Good use of dependency injection
- Comprehensive error messages

Questions for Author:
- Why bcrypt over argon2?
```
