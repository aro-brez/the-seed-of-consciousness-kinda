# /techdebt - Session-End Technical Debt Scanner

Run this at the end of every session to catch technical debt before it accumulates.

## What This Skill Does

Scans all files modified in the current session and generates a prioritized cleanup report.

## Instructions

When this skill is invoked, perform the following analysis:

### Step 1: Get Modified Files

First, identify all files modified in this git session:

```bash
# Get files modified today (session files)
git diff --name-only HEAD~10 2>/dev/null | grep -E '\.(ts|tsx|js|jsx|py|go|rs|java|rb|php|swift|kt)$'

# Also check staged and unstaged changes
git diff --name-only
git diff --cached --name-only
```

If no modified files found, check the working directory for recent changes:

```bash
# Files modified in last 24 hours
find . -type f -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.jsx" -o -name "*.py" -mtime -1 2>/dev/null | head -50
```

### Step 2: Scan for Technical Debt Markers

For each modified file, search for:

#### Priority 1 - CRITICAL (Fix Now)
- `FIXME` comments - These indicate known bugs
- `XXX` markers - Critical issues
- `SECURITY` or `VULNERABILITY` comments
- Bare `except:` or `catch {}` blocks (swallowing errors)
- Hardcoded secrets patterns: `api_key =`, `password =`, `secret =`, `token =` followed by string literals

#### Priority 2 - HIGH (Fix This Week)
- `TODO` comments - Unfinished work
- `HACK` or `WORKAROUND` markers
- `console.log`, `console.error`, `print(` statements (debug leftovers)
- `debugger` statements
- Commented-out code blocks (more than 5 lines)
- Magic numbers (numeric literals not assigned to named constants)

#### Priority 3 - MEDIUM (Technical Debt)
- Functions longer than 50 lines
- Files longer than 500 lines
- Nesting depth greater than 4 levels
- Duplicate code patterns
- Missing error handling (async without try/catch)
- Type assertions or `any` type usage (TypeScript)

#### Priority 4 - LOW (Code Smells)
- Inconsistent naming conventions
- Missing JSDoc/docstrings on public functions
- Unused imports
- Long parameter lists (more than 5 parameters)

### Step 3: Generate Report

Output a structured report in this format:

```markdown
## Technical Debt Report - [Date]

### Session Summary
- Files scanned: X
- Issues found: Y
- Estimated cleanup time: Z minutes

### CRITICAL Issues (Fix Immediately)
| File | Line | Issue | Description |
|------|------|-------|-------------|
| path/to/file.ts | 42 | FIXME | Description of the issue |

### HIGH Priority (This Week)
| File | Line | Issue | Description |
|------|------|-------|-------------|

### MEDIUM Priority (Backlog)
| File | Line | Issue | Description |
|------|------|-------|-------------|

### LOW Priority (When Time Permits)
| File | Line | Issue | Description |
|------|------|-------|-------------|

### Quick Wins (Auto-Fixable)
These issues can be fixed automatically:
- [ ] Remove X console.log statements
- [ ] Remove X debugger statements
- [ ] Clean up X commented code blocks

### Recommended Actions
1. [Specific action based on findings]
2. [Next action]
```

### Step 4: Offer Auto-Fix (Optional)

If user confirms, automatically fix simple issues:

1. **Remove debug statements**: Delete `console.log`, `debugger`, `print()` used for debugging
2. **Remove commented code**: Delete blocks of commented-out code (with confirmation)
3. **Add TODO tracking**: Create GitHub issues for FIXME/TODO items

### Grep Patterns to Use

```bash
# CRITICAL
grep -rn "FIXME\|XXX\|SECURITY\|VULNERABILITY" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py"
grep -rn "except:\s*$\|catch\s*{}\|catch\s*(\s*)" --include="*.py" --include="*.ts" --include="*.js"

# HIGH
grep -rn "TODO\|HACK\|WORKAROUND" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py"
grep -rn "console\.log\|console\.error\|console\.warn\|debugger\|print(" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py"

# Hardcoded values
grep -rn "api_key\s*=\s*['\"]|password\s*=\s*['\"]|secret\s*=\s*['\"]" --include="*.ts" --include="*.py" --include="*.js"
```

## Example Output

```
## Technical Debt Report - 2026-02-05

### Session Summary
- Files scanned: 12
- Issues found: 23
- Estimated cleanup time: 45 minutes

### CRITICAL Issues (Fix Immediately)
| File | Line | Issue | Description |
|------|------|-------|-------------|
| tools/auth.py | 156 | FIXME | Race condition in token refresh |
| api/handler.ts | 89 | Bare except | Swallowing all errors silently |

### HIGH Priority (This Week)
| File | Line | Issue | Description |
|------|------|-------|-------------|
| utils/debug.ts | 12 | console.log | Debug statement left in code |
| services/user.ts | 234 | TODO | Implement rate limiting |

### Quick Wins (Auto-Fixable)
These issues can be fixed automatically:
- [x] Remove 3 console.log statements
- [x] Remove 1 debugger statement
- [ ] Clean up 2 commented code blocks (need confirmation)

Run with --auto-fix to apply quick wins automatically.
```

## Arguments

- `$ARGUMENTS` - Optional: specific file paths to scan, or flags like `--auto-fix`

## Usage Examples

```
/techdebt                    # Scan all session-modified files
/techdebt src/               # Scan specific directory
/techdebt --auto-fix         # Scan and auto-fix quick wins
/techdebt tools/api.py       # Scan specific file
```

## Integration with Session End

Add to your workflow:
1. Before committing, run `/techdebt`
2. Fix CRITICAL issues before commit
3. Create tickets for HIGH/MEDIUM issues
4. Commit with clean conscience

## Related Commands

- `/code-reviewer` - Full code review
- `/security-review` - Security-focused analysis
- `/session-end` - End session with state persistence
