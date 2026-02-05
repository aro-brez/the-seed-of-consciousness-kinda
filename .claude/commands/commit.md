---
name: commit
description: Smart commit with auto-generated message, pre-commit hooks, and push (Boris pattern with inline bash)
---

# Smart Commit Skill

Based on Boris Cherny's slash command pattern: "commit-push-pr uses inline bash to precompute git status"

## Usage

### Quick Commit
```
/commit                          # Auto-commit with generated message
/commit "message"                # Commit with specific message
/commit --push                   # Commit and push
/commit --pr                     # Commit, push, and create PR
/commit --amend                  # Amend last commit
```

### Options
```
/commit --no-verify             # Skip pre-commit hooks
/commit --wip                   # WIP commit (work in progress)
/commit --fix [issue]           # Reference issue in commit
```

## The Protocol

### Step 1: Gather Context
```bash
# Get current status
git status --porcelain

# Get staged changes
git diff --cached --stat

# Get recent commits for message style
git log --oneline -5
```

### Step 2: Generate Message
Based on changes, generate a message following conventional commits:

| Type | When to Use |
|------|-------------|
| `feat:` | New feature |
| `fix:` | Bug fix |
| `refactor:` | Code change that neither fixes nor adds |
| `docs:` | Documentation only |
| `test:` | Adding or updating tests |
| `chore:` | Maintenance, dependencies |
| `perf:` | Performance improvement |
| `ci:` | CI/CD changes |

### Step 3: Verify & Commit
```bash
# Run pre-commit checks
npm run lint
npm test

# Stage specific files (preferred over git add -A)
git add src/feature.ts src/feature.test.ts

# Commit with generated message
git commit -m "$(cat <<'EOF'
feat: add user authentication flow

- Implement login/logout endpoints
- Add JWT token validation
- Create auth middleware
EOF
)"
```

## Commit Message Generation

### Analyze Changes
```bash
# What files changed?
changed_files=$(git diff --cached --name-only)

# What kind of changes?
additions=$(git diff --cached --stat | grep -E "^\s+\d+ file" | awk '{print $4}')
deletions=$(git diff --cached --stat | grep -E "^\s+\d+ file" | awk '{print $6}')

# Determine commit type
if echo "$changed_files" | grep -q "test"; then
  type="test"
elif echo "$changed_files" | grep -qE "README|docs/"; then
  type="docs"
elif echo "$changed_files" | grep -qE "package.json|.config"; then
  type="chore"
else
  type="feat"
fi
```

### Message Format
```
<type>(<scope>): <subject>

<body>

<footer>
```

Example:
```
feat(auth): implement JWT token refresh

- Add refresh token endpoint
- Implement token rotation
- Add 7-day expiration for refresh tokens

Closes #123
```

## Pre-Commit Verification

### Run Checks
```bash
# Lint
npm run lint || { echo "Lint failed"; exit 1; }

# Type check
npm run typecheck || { echo "Type check failed"; exit 1; }

# Tests
npm test || { echo "Tests failed"; exit 1; }

# Security check
npm audit --audit-level=high || echo "Security warnings (non-blocking)"
```

### Hook Configuration
```json
// .claude/settings.json
{
  "hooks": {
    "PreToolUse": [{
      "matcher": "^Bash.*git commit",
      "hooks": [{
        "type": "command",
        "command": "npm run lint && npm test"
      }]
    }]
  }
}
```

## Commit Patterns

### Feature Commit
```bash
git add src/features/auth/
git commit -m "$(cat <<'EOF'
feat(auth): add OAuth2 integration

- Implement Google OAuth provider
- Add callback handling
- Store tokens securely

Closes #45
EOF
)"
```

### Bug Fix Commit
```bash
git add src/utils/validator.ts src/utils/validator.test.ts
git commit -m "$(cat <<'EOF'
fix(validator): handle empty string input

Previously, empty strings passed validation incorrectly.
Now returns false for empty or whitespace-only strings.

Fixes #78
EOF
)"
```

### WIP Commit
```bash
git add -A
git commit -m "$(cat <<'EOF'
wip: authentication flow in progress

NOT READY FOR REVIEW
- Login works
- Logout not implemented
- Tests incomplete
EOF
)"
```

## Push & PR

### Push to Remote
```bash
# Push current branch
git push origin $(git branch --show-current)

# Push with upstream tracking
git push -u origin $(git branch --show-current)
```

### Create PR
```bash
# Create PR with auto-generated body
gh pr create --title "feat(auth): add OAuth2 integration" --body "$(cat <<'EOF'
## Summary
- Implement Google OAuth provider
- Add callback handling
- Store tokens securely

## Test Plan
- [ ] Test login flow manually
- [ ] Verify token refresh works
- [ ] Check logout clears session

## Related Issues
Closes #45
EOF
)"
```

## Attribution

From settings.json:
```json
{
  "attribution": {
    "commit": "Co-Authored-By: claude-flow <ruv@ruv.net>",
    "pr": "Generated with claude-flow"
  }
}
```

Automatically appended to commits (unless disabled).

## Dangerous Operations Warning

### Never Do
```bash
# NEVER force push to main
git push --force origin main  # BLOCKED

# NEVER reset hard without confirmation
git reset --hard              # ASK FIRST

# NEVER use -A blindly
git add -A                    # PREFER specific files
```

### Safety Checks
```bash
# Check for secrets before commit
git diff --cached | grep -iE "(password|secret|key|token).*=" && \
  echo "WARNING: Possible secret in staged changes"

# Check for large files
git diff --cached --stat | awk '$3 > 1000 {print "Large file: " $1}'
```

## Memory Integration

### Store Commit Pattern
```bash
# After successful commit, store for learning
npx @claude-flow/cli@latest memory store \
  --namespace commits \
  --key "commit-$(date +%s)" \
  --value "$(git log -1 --format='%s')"
```

### Learn from Past Commits
```bash
# Search for similar past commits
npx @claude-flow/cli@latest memory search \
  --query "[feature type]" \
  --namespace commits \
  --limit 5
```

## Example Session

```
User: /commit --push

Claude:
1. Gathering context...
   - 3 files staged: auth.ts, auth.test.ts, README.md
   - +156 lines, -23 lines

2. Running pre-commit checks...
   - Lint: PASS
   - Types: PASS
   - Tests: PASS (24/24)

3. Generating commit message...

4. Committing:
   git commit -m "feat(auth): implement token refresh endpoint

   - Add /api/auth/refresh endpoint
   - Implement secure token rotation
   - Add integration tests

   Co-Authored-By: claude-flow <ruv@ruv.net>"

5. Pushing to origin/feature-auth...
   Done.

6. Create PR?
   > [Y/n]
```
