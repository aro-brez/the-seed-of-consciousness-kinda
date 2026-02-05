---
name: debug
description: Test-First Auto-Debug - Write failing test, then fix bug (Boris Cherny pattern)
---

# Test-First Auto-Debug

Based on Boris Cherny's workflow: "Write test first, then fix bug"

## The Protocol

1. **WRITE THE TEST FIRST** - Before touching any code
2. **RUN THE TEST** - Confirm it fails (reproduces the bug)
3. **FIX THE BUG** - Minimal changes only
4. **RUN THE TEST** - Confirm it passes
5. **VERIFY** - Give Claude a way to verify its work (2-3x quality improvement)

## Usage

### Quick Debug (Single Command)
```
/debug [description of bug]
```

### Example Prompts
```
/debug users can't login after password reset
/debug memory leak in the dashboard component
/debug API returns 500 on large file uploads
```

## Workflow Steps

### Step 1: Reproduce & Write Test
```javascript
// FIRST: Write a test that fails
describe('Bug: [description]', () => {
  it('should [expected behavior]', async () => {
    // Arrange - setup that triggers the bug
    const input = createBugTriggeringInput();

    // Act - the action that causes the bug
    const result = await buggyFunction(input);

    // Assert - what SHOULD happen
    expect(result).toEqual(expectedOutput);
  });
});
```

### Step 2: Run Test (Must Fail)
```bash
# Run the specific test
npm test -- --testPathPattern="[test-file]" --testNamePattern="Bug:"

# Verify it FAILS - this proves we've reproduced the bug
# If test passes, we haven't reproduced it correctly
```

### Step 3: Fix Minimally
- **ONLY** change what's necessary to make the test pass
- Don't refactor during bug fixes
- Don't add features during bug fixes
- Keep the diff as small as possible

### Step 4: Verify Fix
```bash
# Run the test again - must PASS now
npm test -- --testPathPattern="[test-file]" --testNamePattern="Bug:"

# Run full test suite to check for regressions
npm test
```

### Step 5: Additional Verification
- **Browser check**: If UI bug, use Claude Chrome extension to verify
- **API check**: Run curl/httpie to test endpoint
- **Logs check**: Grep logs for error patterns
- **Performance check**: Verify no performance regression

## Verification Methods (Boris's Key Insight)

> "Give Claude a way to verify its work...2-3x the quality of the final result"

| Bug Type | Verification Method |
|----------|---------------------|
| UI/Visual | Claude Chrome extension, screenshot comparison |
| API | curl commands, Postman collection |
| Logic | Unit tests with edge cases |
| Performance | Benchmark before/after |
| Security | Security scan, penetration test |
| Memory Leak | Heap snapshot comparison |
| Integration | E2E test suite (Playwright) |

## Auto-Debug Pipeline

```bash
# The full pipeline in one command
npm test -- --testPathPattern="$BUG_TEST" --testNamePattern="Bug:" && \
  echo "Test passes - bug not reproduced correctly" || \
  (echo "Bug reproduced. Attempting fix..." && \
   # Apply fix here && \
   npm test -- --testPathPattern="$BUG_TEST" --testNamePattern="Bug:" && \
   echo "Bug fixed and verified!" || \
   echo "Fix failed - test still failing")
```

## Integration with Claude Flow

### Store Bug Pattern
```bash
# After fixing, store the pattern for future learning
npx @claude-flow/cli@latest memory store \
  --namespace bugs \
  --key "bug-$(date +%s)" \
  --value "Bug: [description] | Root cause: [cause] | Fix: [fix approach]"
```

### Search Past Bugs
```bash
# Before debugging, check if similar bug was fixed before
npx @claude-flow/cli@latest memory search \
  --query "[bug description]" \
  --namespace bugs \
  --limit 5
```

## Subagent Verification (Boris's Pattern)

For complex bugs, spawn verification subagents:

```javascript
// After fix is applied, spawn verifier
Task({
  prompt: "Verify the bug fix for [description]. Run tests, check for regressions, validate the fix in browser if applicable.",
  subagent_type: "tester",
  description: "Bug fix verification",
  run_in_background: true
})
```

## Stop Hook Verification

For long-running debug sessions, use Stop hooks:

```json
// .claude/settings.json
{
  "hooks": {
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": "npm test && echo 'All tests pass - safe to stop'"
      }]
    }]
  }
}
```

## Best Practices

1. **Never skip the failing test** - It's your proof the bug exists
2. **One bug = one test = one fix** - Don't bundle changes
3. **Keep the test forever** - It prevents regression
4. **Document the root cause** - In the test comment or PR description
5. **Verify in multiple ways** - Test + manual check + logs

## Example Session

```
User: /debug login fails after password reset

Claude:
1. Let me search for similar past bugs...
   [searches memory for "login" + "password reset"]

2. Writing a failing test:
   [creates test that reproduces the bug]

3. Running test to confirm it fails:
   [test fails - bug reproduced]

4. Analyzing root cause:
   [traces code path, identifies issue]

5. Applying minimal fix:
   [edits the specific file]

6. Verifying fix:
   [runs test - passes]
   [runs full suite - no regressions]

7. Storing pattern for future:
   [stores bug pattern in memory]

Bug fixed and verified.
```
