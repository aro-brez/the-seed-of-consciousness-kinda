---
name: deploy
description: Deployment skill with verification, rollback, and monitoring (DevOps Engineer role from 45 tips)
---

# Deployment Skill

Delegate infrastructure tasks, deployments, and configuration management to Claude (Tip #29: DevOps Engineer Role).

## Usage

### Quick Deploy
```
/deploy                          # Deploy current branch
/deploy staging                  # Deploy to staging
/deploy production               # Deploy to production (with extra verification)
/deploy --rollback               # Rollback last deployment
/deploy --status                 # Check deployment status
```

### Options
```
/deploy --dry-run               # Preview without executing
/deploy --skip-tests            # Skip test verification (use with caution)
/deploy --force                 # Force deploy even if checks fail
/deploy --notify                # Send notifications on completion
```

## Pre-Deployment Protocol

### Step 1: Verification Checks
```bash
# Run full test suite
npm test

# Run linting
npm run lint

# Type check
npm run typecheck

# Security scan
npm audit
npx @claude-flow/cli@latest security scan --depth quick

# Build verification
npm run build

# Truth score check (0.95 threshold for production)
npx @claude-flow/cli@latest verify check --threshold 0.95
```

### Step 2: Environment Validation
```bash
# Verify environment variables are set
env | grep -E "^(DATABASE_URL|API_KEY|SECRET)" | wc -l

# Check secrets are not hardcoded
git diff --staged | grep -iE "(password|secret|key|token).*=" && echo "WARNING: Possible secret detected"

# Validate configuration
npm run validate-config 2>/dev/null || echo "No config validation script"
```

### Step 3: Database Migrations (if any)
```bash
# Check for pending migrations
npm run migrate:status 2>/dev/null || npx prisma migrate status 2>/dev/null

# Run migrations (if needed)
npm run migrate 2>/dev/null || npx prisma migrate deploy 2>/dev/null
```

## Deployment Targets

### Vercel
```bash
# Preview deployment
vercel

# Production deployment
vercel --prod

# With environment
vercel --prod --env-file .env.production
```

### Docker
```bash
# Build image
docker build -t app:$(git rev-parse --short HEAD) .

# Push to registry
docker push registry.example.com/app:$(git rev-parse --short HEAD)

# Deploy to swarm/k8s
docker stack deploy -c docker-compose.yml app
# OR
kubectl apply -f k8s/deployment.yaml
```

### Railway
```bash
# Deploy
railway up

# Deploy to production
railway up --environment production
```

### Fly.io
```bash
# Deploy
fly deploy

# Deploy with machines
fly deploy --machines
```

### AWS
```bash
# ECS deployment
aws ecs update-service --cluster prod --service app --force-new-deployment

# Lambda deployment
aws lambda update-function-code --function-name app --zip-file fileb://dist.zip
```

## Post-Deployment Verification

### Step 1: Health Checks
```bash
# Wait for deployment
sleep 30

# Check health endpoint
curl -f https://app.example.com/health || echo "HEALTH CHECK FAILED"

# Check version endpoint
curl -s https://app.example.com/version | jq .

# Run smoke tests
npm run test:smoke
```

### Step 2: Monitoring Check
```bash
# Check error rates (example with Sentry)
# sentry-cli releases set-commits --auto

# Check logs for errors
# Example: fly logs --app app | grep -i error

# Check metrics
# Example: datadog-ci metric query 'avg:app.error_rate{env:production}'
```

### Step 3: Rollback Ready
```bash
# Store deployment info for potential rollback
echo "$(date),$(git rev-parse HEAD),production" >> .deployment-history

# Verify rollback is available
git log --oneline -5
```

## Rollback Protocol

```bash
# Quick rollback (Vercel)
vercel rollback

# Docker rollback
docker stack deploy -c docker-compose.previous.yml app

# Git-based rollback
git revert HEAD --no-edit
git push origin main

# Manual rollback
/deploy --rollback --target [previous-commit-sha]
```

## Deployment Checklist

### Pre-Deploy
- [ ] All tests pass
- [ ] No linting errors
- [ ] Types check pass
- [ ] Security scan clean
- [ ] Build succeeds
- [ ] Truth score >= 0.95
- [ ] No hardcoded secrets
- [ ] Database migrations tested
- [ ] Environment variables verified
- [ ] Rollback plan documented

### Post-Deploy
- [ ] Health check passes
- [ ] Version endpoint shows correct version
- [ ] Smoke tests pass
- [ ] No error spikes in monitoring
- [ ] Performance within acceptable range
- [ ] Notifications sent to team

## Swarm Deployment (Multi-Agent)

For complex deployments, spawn verification agents:

```javascript
// Pre-deploy security check
Task({
  prompt: "Run security audit before deployment. Check for vulnerabilities, exposed secrets, and security misconfigurations.",
  subagent_type: "security-auditor",
  model: "haiku",
  run_in_background: true
})

// Post-deploy verification
Task({
  prompt: "Verify deployment succeeded. Check health endpoints, run smoke tests, verify no error spikes in logs.",
  subagent_type: "tester",
  model: "haiku",
  run_in_background: true
})

// Performance check
Task({
  prompt: "Run performance benchmark against deployed application. Compare with baseline metrics.",
  subagent_type: "perf-analyzer",
  model: "haiku",
  run_in_background: true
})
```

## Notification Integration

### Slack (via MCP)
```bash
# Post deployment notification
# Using Slack MCP (Boris pattern)
mcp__slack__post_message({
  channel: "#deployments",
  text: "Deployed ${APP_NAME} v${VERSION} to ${ENV}"
})
```

### Manual Notification
```bash
# Webhook notification
curl -X POST https://hooks.slack.com/services/XXX \
  -H "Content-Type: application/json" \
  -d '{"text": "Deployed app to production"}'
```

## Environment-Specific Thresholds

| Environment | Truth Score | Required Checks |
|-------------|-------------|-----------------|
| Development | 0.85 | Tests, Lint |
| Staging | 0.90 | Tests, Lint, Types, Build |
| Production | 0.95 | All checks + Security scan |

## Deployment Memory

### Store Deployment Info
```bash
npx @claude-flow/cli@latest memory store \
  --namespace deployments \
  --key "deploy-$(date +%s)" \
  --value "$(date): Deployed $(git rev-parse --short HEAD) to production"
```

### Search Past Deployments
```bash
npx @claude-flow/cli@latest memory search \
  --query "deployment production" \
  --namespace deployments \
  --limit 10
```

## Example Session

```
User: /deploy production

Claude:
1. Running pre-deployment checks...
   - Tests: PASS (234/234)
   - Lint: PASS
   - Types: PASS
   - Security: PASS (no vulnerabilities)
   - Build: PASS
   - Truth Score: 0.97

2. Validating environment...
   - All required env vars set
   - No secrets in code
   - Database migrations: none pending

3. Deploying to production...
   - Building image: app:abc1234
   - Pushing to registry
   - Updating deployment
   - Waiting for rollout...

4. Post-deployment verification...
   - Health check: PASS
   - Version: v2.3.1 (abc1234)
   - Smoke tests: PASS (5/5)
   - Error rate: 0.01% (normal)

5. Deployment complete!
   - URL: https://app.example.com
   - Rollback available: git revert abc1234

Storing deployment info for future reference...
Done.
```
