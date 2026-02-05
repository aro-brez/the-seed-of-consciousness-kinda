---
name: verify
description: Verification skill - Give Claude ways to verify its work (Boris Cherny's key insight for 2-3x quality)
---

# Verification Skill

Based on Boris Cherny's key insight: "Give Claude a way to verify its work...2-3x the quality of the final result"

## The Core Principle

> Every task should have a verification method. If Claude can't verify, quality drops significantly.

## Usage

### Quick Verify
```
/verify                          # Verify recent changes
/verify [file]                   # Verify specific file
/verify --all                    # Full verification suite
/verify --browser                # Use Claude Chrome extension
```

### Options
```
/verify --type unit             # Run unit tests only
/verify --type integration      # Run integration tests
/verify --type e2e              # Run E2E tests (Playwright)
/verify --type visual           # Visual regression testing
/verify --type security         # Security verification
```

## Verification Methods by Task Type

### UI/Visual Changes
```bash
# Use Claude Chrome extension
claude --chrome

# Or take screenshot and compare
# Playwright visual comparison
npx playwright test --update-snapshots

# Percy visual testing
npx percy exec -- npm test
```

### API Changes
```bash
# Test endpoint directly
curl -X POST http://localhost:3000/api/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}'

# Run API tests
npm run test:api

# Check OpenAPI spec compliance
npx @stoplight/spectral lint openapi.yaml
```

### Logic/Business Rules
```bash
# Run unit tests for specific module
npm test -- --testPathPattern="auth"

# Run with coverage
npm test -- --coverage --collectCoverageFrom="src/auth/**"

# Property-based testing
npm run test:property
```

### Performance Changes
```bash
# Benchmark before/after
npm run benchmark

# Lighthouse audit
npx lighthouse http://localhost:3000 --output json

# Load testing
npx autocannon -c 100 -d 30 http://localhost:3000/api/health
```

### Security Changes
```bash
# Security scan
npm audit
npx @claude-flow/cli@latest security scan

# OWASP check
npx owasp-dependency-check

# Secret detection
npx gitleaks detect
```

### Database Changes
```bash
# Test migrations up and down
npm run migrate:up && npm run migrate:down && npm run migrate:up

# Verify data integrity
psql -c "SELECT count(*) FROM users WHERE email IS NULL"

# Test queries
npm run test:db
```

## Subagent Verification (Boris Pattern)

Deploy specialized verification subagents:

```javascript
// code-simplifier - cleanup after work
Task({
  prompt: "Review the changes in [files] and simplify any overly complex code while maintaining functionality.",
  subagent_type: "reviewer",
  description: "Code simplification",
  run_in_background: true
})

// verify-app - end-to-end testing
Task({
  prompt: "Run end-to-end verification of [feature]. Test all user flows and edge cases.",
  subagent_type: "tester",
  description: "E2E verification",
  run_in_background: true
})
```

## Stop Hook Verification

For long-running tasks, use Stop hooks for automatic verification:

```json
// .claude/settings.json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "npm test && npm run lint && echo 'Verification passed'",
        "timeout": 60000
      }]
    }]
  }
}
```

## Verification Checklist by Task

### New Feature
- [ ] Unit tests written and passing
- [ ] Integration tests if applicable
- [ ] E2E tests for critical paths
- [ ] Manual testing completed
- [ ] Edge cases covered
- [ ] Error handling verified
- [ ] Performance acceptable
- [ ] Security review passed

### Bug Fix
- [ ] Failing test reproduces bug
- [ ] Test passes after fix
- [ ] No regression in related areas
- [ ] Edge cases tested
- [ ] Fix is minimal (no extra changes)

### Refactoring
- [ ] All existing tests still pass
- [ ] Test coverage maintained or improved
- [ ] No behavior changes (unless intended)
- [ ] Performance not degraded
- [ ] Code complexity reduced

### Performance Optimization
- [ ] Benchmarks show improvement
- [ ] No functionality regression
- [ ] Memory usage acceptable
- [ ] No new bugs introduced
- [ ] Improvement documented

## Claude Chrome Extension Verification

For visual verification:

```bash
# Enable Chrome integration
claude --chrome

# Or use /chrome command
/chrome

# Claude can now:
# - Take screenshots
# - Record interactions as GIFs
# - Verify visual changes
# - Test UI flows
```

## Complete Write-Test Cycles (Tip #9)

Structure autonomous tasks with verification loops:

```bash
# Use tmux for autonomous testing
tmux new-session -d -s test-loop
tmux send-keys 'while true; do npm test; sleep 5; done' C-m

# Or Playwright for web verification
npx playwright test --ui
```

## Verification Pipeline

### Pre-Commit
```bash
# Run before every commit
npm run lint
npm test
npm run typecheck
```

### Pre-Push
```bash
# Run before pushing
npm run lint
npm test
npm run build
npm run test:integration
```

### Pre-Deploy
```bash
# Run before deployment
npm run lint
npm test
npm run build
npm run test:e2e
npx @claude-flow/cli@latest security scan
npx @claude-flow/cli@latest verify check --threshold 0.95
```

## Truth Score Verification

Use Claude Flow's truth scoring system:

```bash
# Check current truth score
npx @claude-flow/cli@latest truth

# Verify specific file
npx @claude-flow/cli@latest verify check --file src/app.ts

# Verify with custom threshold
npx @claude-flow/cli@latest verify check --threshold 0.98

# Watch mode
npx @claude-flow/cli@latest verify watch --directory src/
```

## Verification Memory

### Store Verification Results
```bash
npx @claude-flow/cli@latest memory store \
  --namespace verification \
  --key "verify-$(date +%s)" \
  --value "File: [file] | Tests: PASS | Coverage: 85% | Truth: 0.94"
```

### Track Verification History
```bash
npx @claude-flow/cli@latest memory search \
  --query "[file or feature]" \
  --namespace verification \
  --limit 10
```

## Domain-Specific Verification

| Domain | Verification Methods |
|--------|---------------------|
| Frontend | Jest, Playwright, visual regression, Chrome extension |
| Backend | Jest, Supertest, load testing, API contracts |
| Database | Migration tests, data integrity checks, query analysis |
| Security | SAST, DAST, dependency audit, penetration testing |
| Performance | Benchmarks, profiling, load testing, Lighthouse |
| Infrastructure | Terraform validate, dry-run, staging deploy |

## Example Session

```
User: /verify

Claude:
Running verification suite...

1. Unit Tests
   - 156 tests passed
   - 2 tests skipped
   - Coverage: 84%

2. Integration Tests
   - 24 tests passed
   - API contracts valid

3. Lint & Types
   - No lint errors
   - No type errors

4. Security
   - No vulnerabilities found
   - No secrets in code

5. Truth Score
   - Overall: 0.94
   - Code correctness: 0.97
   - Best practices: 0.92
   - Documentation: 0.88

All verification checks passed.

Recommendations:
- Consider adding tests for edge cases in auth module
- Documentation could be improved for API endpoints
```

## The Verification Mindset

> "If you can't verify it, you can't trust it."

1. **Define verification upfront** - Before writing code, know how you'll verify it
2. **Automate verification** - Manual verification doesn't scale
3. **Layer verification** - Unit → Integration → E2E → Manual
4. **Verify continuously** - Not just at the end
5. **Trust but verify** - Even when confident, run the checks
