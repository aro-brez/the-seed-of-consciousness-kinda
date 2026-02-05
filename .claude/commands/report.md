---
name: report
description: Generate comprehensive reports for code, performance, security, and business metrics
---

# Report Generation Skill

Generate detailed reports with metrics, visualizations, and actionable insights.

## Usage

### Quick Reports
```
/report                          # Generate overview report
/report daily                    # Daily summary report
/report weekly                   # Weekly comprehensive report
/report --type security          # Security-focused report
/report --type performance       # Performance report
/report --type code              # Code quality report
```

### Options
```
/report --format html           # HTML with charts
/report --format markdown       # Markdown (default)
/report --format json           # JSON for automation
/report --export report.html    # Export to file
/report --since 7d              # Time range
```

## Report Types

### 1. Daily Summary Report
```markdown
# Daily Summary - [DATE]

## Activity Overview
- Commits: 12
- Files changed: 45
- Lines: +1,234 / -567
- PRs merged: 3
- Issues closed: 5

## Code Quality
- Test coverage: 84% (+2%)
- Lint errors: 0
- Type errors: 0
- Truth score: 0.94

## Performance
- Build time: 45s (-5s)
- Test time: 2m 30s
- Bundle size: 234kb (+12kb)

## Issues & Blockers
- [HIGH] Redis timeout affecting API latency
- [MEDIUM] Test flakiness in auth module

## Tomorrow's Focus
1. Fix Redis connection issues
2. Complete feature X implementation
3. Review pending PRs
```

### 2. Weekly Comprehensive Report
```markdown
# Weekly Report - Week [N]

## Executive Summary
This week we shipped [features] and fixed [bugs].
Code quality improved by [X%]. No security incidents.

## Metrics Dashboard
| Metric | This Week | Last Week | Change |
|--------|-----------|-----------|--------|
| Commits | 45 | 38 | +18% |
| PRs Merged | 12 | 8 | +50% |
| Test Coverage | 84% | 82% | +2% |
| Bug Reports | 3 | 7 | -57% |
| Uptime | 99.9% | 99.7% | +0.2% |

## Highlights
- Shipped user authentication v2
- Reduced API latency by 40%
- Onboarded 2 new team members

## Challenges
- Scaling issues under high load
- Legacy code migration delayed

## Next Week Priorities
1. Complete payment integration
2. Performance optimization sprint
3. Security audit
```

### 3. Security Report
```markdown
# Security Report - [DATE]

## Security Score: 94/100

## Vulnerability Summary
| Severity | Count | Fixed | Open |
|----------|-------|-------|------|
| Critical | 0 | 0 | 0 |
| High | 2 | 2 | 0 |
| Medium | 5 | 3 | 2 |
| Low | 8 | 5 | 3 |

## Recent Security Actions
- Updated dependencies with known CVEs
- Fixed SQL injection in search endpoint
- Added rate limiting to auth endpoints

## Pending Actions
- [ ] Rotate API keys older than 90 days
- [ ] Enable 2FA for all admin accounts
- [ ] Complete penetration testing

## Compliance Status
- OWASP Top 10: 9/10 addressed
- SOC2: In progress
- GDPR: Compliant
```

### 4. Performance Report
```markdown
# Performance Report - [DATE]

## Overview
- Avg response time: 45ms (-15%)
- p95 latency: 120ms (-20%)
- Error rate: 0.1% (stable)
- Throughput: 1,200 req/s (+10%)

## Endpoint Performance
| Endpoint | Avg (ms) | p95 (ms) | Calls/min |
|----------|----------|----------|-----------|
| GET /api/users | 12 | 35 | 2,400 |
| POST /api/auth | 45 | 120 | 800 |
| GET /api/data | 89 | 250 | 1,200 |

## Resource Utilization
- CPU: avg 45%, peak 78%
- Memory: avg 2.1GB, peak 3.4GB
- Database connections: avg 45, peak 120

## Bottlenecks Identified
1. /api/data endpoint needs caching
2. Database queries on user table slow
3. Image processing causing CPU spikes

## Recommendations
1. Add Redis caching for /api/data
2. Add index on users.email column
3. Move image processing to worker queue
```

### 5. Code Quality Report
```markdown
# Code Quality Report - [DATE]

## Overall Score: 87/100 (Good)

## Metrics
| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Test Coverage | 84% | 80% | PASS |
| Lint Errors | 0 | 0 | PASS |
| Type Coverage | 92% | 90% | PASS |
| Complexity | 12 avg | <15 | PASS |
| Duplication | 3.2% | <5% | PASS |

## Top Issues
1. **Large file**: `src/legacy/processor.ts` (1,200 lines)
2. **High complexity**: `calculateDiscount()` (cyclomatic: 18)
3. **Missing tests**: `src/utils/helpers.ts` (0% coverage)

## Technical Debt
- Estimated: 12 hours
- Critical items: 2
- New debt this week: +2h
- Paid off this week: -4h

## Recommendations
1. Split processor.ts into smaller modules
2. Refactor calculateDiscount() function
3. Add tests for helper utilities
```

## Report Generation Commands

### Gather Metrics
```bash
# Git statistics
git log --since="1 week ago" --oneline | wc -l  # Commits
git diff --stat HEAD~20 | tail -1               # Lines changed

# Test coverage
npm test -- --coverage --coverageReporters=json

# Build metrics
time npm run build 2>&1

# Bundle size
du -sh dist/

# Lint status
npm run lint -- --format json
```

### Security Scan
```bash
# NPM audit
npm audit --json

# Claude Flow security scan
npx @claude-flow/cli@latest security scan --format json

# Secret detection
gitleaks detect --source . --report-format json
```

### Performance Metrics
```bash
# API benchmarks
ab -n 1000 -c 10 http://localhost:3000/api/health

# Database query analysis
psql -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10"
```

## Export Formats

### HTML Report
```bash
# Generate HTML with charts
/report --format html --export reports/weekly-$(date +%Y%m%d).html
```

### JSON for CI/CD
```bash
# Generate JSON for automation
/report --format json > reports/metrics.json

# Use in CI pipeline
jq '.overall_score > 80' reports/metrics.json || exit 1
```

### Markdown for Documentation
```bash
# Generate markdown
/report --format markdown --export reports/REPORT.md
```

## Automated Report Generation

### Schedule Daily Reports
```bash
# Add to crontab
# 0 9 * * * /path/to/report-daily.sh

#!/bin/bash
cd /path/to/project
npx @claude-flow/cli@latest hooks report --type daily --export "reports/daily-$(date +%Y%m%d).md"
```

### Store in Memory
```bash
# Store report metrics
npx @claude-flow/cli@latest memory store \
  --namespace reports \
  --key "report-$(date +%Y%m%d)" \
  --value "$(cat reports/daily-$(date +%Y%m%d).json)"
```

### Search Historical Reports
```bash
npx @claude-flow/cli@latest memory search \
  --query "weekly report" \
  --namespace reports \
  --limit 4
```

## Trading Bot Reports

### Daily Trading Summary
```markdown
# Trading Report - [DATE]

## Performance
- Trades executed: 24
- Win rate: 68%
- Profit factor: 1.8
- Net P&L: +$45.20

## Trade Breakdown
| Market | Trades | Wins | Losses | P&L |
|--------|--------|------|--------|-----|
| Elections | 8 | 6 | 2 | +$22.50 |
| Sports | 10 | 7 | 3 | +$18.30 |
| Crypto | 6 | 3 | 3 | +$4.40 |

## Top Trades
1. Biden approval poll: +$12.00
2. Bitcoin >50k: +$8.50
3. Lakers win: +$6.20

## Risk Metrics
- Max drawdown: -$15.00
- Sharpe ratio: 1.4
- Daily limit used: 62%
```

## Multi-Agent Report Generation

For comprehensive reports, spawn specialized agents:

```javascript
// Gather metrics from multiple sources in parallel
Task({
  prompt: "Analyze git history and generate commit statistics for the past week",
  subagent_type: "researcher",
  model: "haiku",
  run_in_background: true
})

Task({
  prompt: "Run security scan and generate vulnerability report",
  subagent_type: "security-auditor",
  model: "haiku",
  run_in_background: true
})

Task({
  prompt: "Analyze code quality metrics: coverage, complexity, duplication",
  subagent_type: "reviewer",
  model: "haiku",
  run_in_background: true
})

Task({
  prompt: "Gather performance metrics from logs and monitoring endpoints",
  subagent_type: "perf-analyzer",
  model: "haiku",
  run_in_background: true
})
```

## Example Session

```
User: /report weekly

Claude:
Generating weekly report...

1. Gathering metrics:
   - Git statistics: 45 commits, 12 PRs
   - Test coverage: 84%
   - Security scan: 2 medium issues
   - Performance: p95 latency 120ms

2. Analyzing trends:
   - Coverage improved +2%
   - Bug reports down 57%
   - Build time reduced 10%

3. Generating report...

# Weekly Report - Week 5

## Executive Summary
Strong week with 45 commits and 12 PRs merged.
Code quality improved, security posture stable.

[Full report continues...]

Report exported to: reports/weekly-20260205.md
```
