# Verification Loop Skill

Run full quality gate verification on code changes.

## Invocation

```
/verify [path]
```

Where `path` is optional - defaults to current working directory.

## Verification Steps

1. **Build** - Compile/transpile succeeds
2. **Types** - No TypeScript errors
3. **Lint** - ESLint passes
4. **Tests** - All tests pass, 80%+ coverage
5. **Security** - No obvious vulnerabilities
6. **Diff Review** - Changes make sense

## Instructions

When user invokes `/verify`:

1. **Build Check**
   ```bash
   npm run build 2>&1 || yarn build 2>&1 || pnpm build 2>&1
   ```
   If fails: Stop and report build errors.

2. **Type Check**
   ```bash
   npx tsc --noEmit
   ```
   If fails: Report type errors, suggest fixes.

3. **Lint Check**
   ```bash
   npx eslint . --ext .ts,.tsx,.js,.jsx
   ```
   If fails: Report lint errors. Auto-fix if possible:
   ```bash
   npx eslint . --fix
   ```

4. **Test Check**
   ```bash
   npm test -- --coverage
   ```
   Requirements:
   - All tests pass
   - Coverage >= 80% (branches, functions, lines, statements)

   If fails: Report failing tests, suggest investigation.

5. **Security Scan**
   Check for:
   - Hardcoded secrets (API keys, passwords)
   - console.log statements (remove before production)
   - SQL injection risks (string concatenation in queries)
   - XSS vulnerabilities (unescaped user input)

   Use grep patterns:
   ```bash
   grep -r "console\.log" src/ --include="*.ts" --include="*.tsx"
   grep -r "api[_-]?key.*=" src/ --include="*.ts" --include="*.tsx" -i
   ```

6. **Diff Review**
   ```bash
   git diff --stat
   git diff
   ```
   Verify changes are intentional and complete.

## Output Format

```
## Verification Results

### Build: PASS/FAIL
[details]

### Types: PASS/FAIL
[details]

### Lint: PASS/FAIL
[details]

### Tests: PASS/FAIL
Coverage: X%
[details]

### Security: PASS/FAIL
[findings]

### Diff Review: REVIEWED
[summary of changes]

## Overall: PASS/FAIL
```

## SEED Phase

This skill operates in the **IMPROVE** phase - verifying and optimizing what was built.

## When to Use

- After completing implementation tasks
- Before committing code
- Before creating pull requests
- As final gate before deployment
