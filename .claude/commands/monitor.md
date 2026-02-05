---
name: monitor
description: System monitoring skill with real-time status, logs, and alerts
---

# System Monitoring Skill

Real-time system monitoring, log analysis, and alerting.

## Usage

### Quick Monitor
```
/monitor                         # Show system overview
/monitor logs                    # View recent logs
/monitor errors                  # View recent errors only
/monitor --watch                 # Real-time monitoring mode
/monitor health                  # Health check all services
```

### Options
```
/monitor --service [name]       # Monitor specific service
/monitor --since 1h             # Logs from last hour
/monitor --level error          # Filter by log level
/monitor --export               # Export metrics to file
```

## System Overview Dashboard

```
System Status Dashboard
=======================

Services:
  api-server      HEALTHY   cpu: 23%  mem: 456MB  uptime: 3d 4h
  database        HEALTHY   cpu: 12%  mem: 2.1GB  connections: 45
  redis-cache     HEALTHY   cpu: 5%   mem: 128MB  keys: 12.4k
  worker-queue    WARNING   cpu: 89%  mem: 890MB  queue: 1.2k pending

Recent Activity (last 5m):
  Requests: 2,345/min  Errors: 12 (0.5%)  Avg latency: 45ms

Active Alerts:
  [WARN] Worker queue backlog > 1000
  [INFO] Database connection pool at 90%
```

## Log Analysis

### View Logs
```bash
# Tail application logs
tail -f logs/app.log

# Tail with filtering
tail -f logs/app.log | grep -i error

# View last 100 lines
tail -100 logs/app.log

# Search for patterns
grep -r "ERROR\|FATAL" logs/
```

### Log Aggregation Commands
```bash
# Count errors by type
grep ERROR logs/app.log | awk '{print $5}' | sort | uniq -c | sort -rn

# Find most common error messages
grep ERROR logs/app.log | sed 's/.*ERROR//' | sort | uniq -c | sort -rn | head -20

# Errors per hour
grep ERROR logs/app.log | cut -d' ' -f1-2 | cut -d':' -f1-2 | sort | uniq -c
```

### Sentry Integration (Boris Pattern)
```bash
# Fetch recent errors from Sentry
# Claude can use this to diagnose issues
sentry-cli issues list --project app --status unresolved

# Get error details
sentry-cli issues show [ISSUE_ID]
```

## Health Checks

### Endpoint Health
```bash
# Check main health endpoint
curl -sf http://localhost:3000/health && echo "OK" || echo "FAIL"

# Check all services
for service in api auth database cache; do
  status=$(curl -sf "http://localhost:3000/health/$service" && echo "OK" || echo "FAIL")
  echo "$service: $status"
done
```

### Database Health
```bash
# PostgreSQL
psql -c "SELECT 1" && echo "DB: OK"

# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity"

# Check slow queries
psql -c "SELECT query, calls, mean_time FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 5"
```

### Container Health
```bash
# Docker containers
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Docker stats
docker stats --no-stream

# Kubernetes pods
kubectl get pods -o wide
kubectl top pods
```

## Error Tracking

### Recent Errors
```bash
# Find errors in last hour
grep ERROR logs/app.log | grep "$(date -d '1 hour ago' '+%Y-%m-%d %H')"

# Unique errors with count
grep -h ERROR logs/*.log | sort | uniq -c | sort -rn | head -10

# Error rate
total=$(wc -l < logs/app.log)
errors=$(grep -c ERROR logs/app.log)
echo "Error rate: $(echo "scale=2; $errors * 100 / $total" | bc)%"
```

### Error Pattern Analysis
```bash
# Find stack traces
grep -A 10 "Stack trace\|Traceback" logs/app.log

# Find timeout errors
grep -i "timeout\|timed out" logs/app.log

# Find memory issues
grep -i "out of memory\|heap\|OOM" logs/app.log
```

## Performance Monitoring

### CPU & Memory
```bash
# System overview
top -l 1 -n 5 | head -20

# Process memory usage
ps aux --sort=-%mem | head -10

# Process CPU usage
ps aux --sort=-%cpu | head -10
```

### Application Metrics
```bash
# Node.js process stats
curl -s http://localhost:3000/metrics | grep -E "^(process_|nodejs_)"

# Request latency
curl -s http://localhost:3000/metrics | grep "http_request_duration"

# Active connections
curl -s http://localhost:3000/metrics | grep "active_connections"
```

## Alerting

### Define Alert Rules
```yaml
# alert-rules.yaml
alerts:
  - name: high_error_rate
    condition: error_rate > 5%
    severity: critical
    action: notify

  - name: high_latency
    condition: p99_latency > 500ms
    severity: warning
    action: notify

  - name: disk_space_low
    condition: disk_usage > 90%
    severity: critical
    action: notify
```

### Check Alerts
```bash
# Check disk space
df -h | awk '$5 > 90 {print "ALERT: " $6 " at " $5}'

# Check memory
free -m | awk '/Mem:/ {if ($3/$2 > 0.9) print "ALERT: Memory at " int($3/$2*100) "%"}'

# Check load average
uptime | awk -F'load average:' '{if ($2 > 4) print "ALERT: High load: " $2}'
```

## 8OWLS Trading Bot Monitor

### Quick Status
```bash
# Check if trading bot is running
ps aux | grep field_trading_daemon | grep -v grep && echo "Trading bot: RUNNING" || echo "Trading bot: STOPPED"

# View recent trading activity
tail -20 /Users/aaronnosbisch/REPOS/seed/logs/field_trading.log

# Check trading state
cat /Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/field_trading_state.json | jq .
```

### Trading Metrics
```bash
# Win rate
state=$(cat /Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/field_trading_state.json)
echo "Win rate: $(echo $state | jq .win_rate)"
echo "Profit factor: $(echo $state | jq .profit_factor)"
echo "Pending trades: $(echo $state | jq '.pending_trades | length')"
echo "Resolved trades: $(echo $state | jq '.resolved_trades | length')"
```

## Claude Flow Monitoring

### Daemon Status
```bash
# Check daemon
npx @claude-flow/cli@latest daemon status

# Check workers
npx @claude-flow/cli@latest hooks worker status

# Check memory
npx @claude-flow/cli@latest memory list --limit 5
```

### Swarm Status
```bash
# Check swarm
npx @claude-flow/cli@latest swarm status

# Agent health
npx @claude-flow/cli@latest agent list
npx @claude-flow/cli@latest agent health
```

## Watch Mode

### Real-time Monitoring
```bash
# Watch logs
watch -n 1 'tail -10 logs/app.log'

# Watch system resources
watch -n 2 'top -l 1 -n 5 | head -15'

# Watch trading bot
watch -n 5 'cat /Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/field_trading_state.json | jq "{win_rate, profit_factor, pending: (.pending_trades | length)}"'
```

### Combined Dashboard
```bash
# Create tmux monitoring dashboard
tmux new-session -d -s monitor
tmux split-window -h
tmux split-window -v
tmux select-pane -t 0
tmux send-keys 'watch -n 5 "npx @claude-flow/cli@latest hooks statusline"' C-m
tmux select-pane -t 1
tmux send-keys 'tail -f logs/app.log | grep --color=always ERROR' C-m
tmux select-pane -t 2
tmux send-keys 'watch -n 10 "curl -s localhost:3000/health | jq ."' C-m
tmux attach-session -t monitor
```

## Memory Integration

### Store Metrics
```bash
# Store hourly metrics
npx @claude-flow/cli@latest memory store \
  --namespace metrics \
  --key "metrics-$(date +%Y%m%d%H)" \
  --value "$(cat << EOF
{
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "cpu": $(top -l 1 | grep "CPU usage" | awk '{print $3}' | tr -d '%'),
  "memory": $(vm_stat | grep "Pages active" | awk '{print $3}' | tr -d '.'),
  "errors_1h": $(grep -c ERROR logs/app.log 2>/dev/null || echo 0)
}
EOF
)"
```

### Search Historical Metrics
```bash
npx @claude-flow/cli@latest memory search \
  --query "metrics" \
  --namespace metrics \
  --limit 24
```

## Example Session

```
User: /monitor

Claude:
System Status Dashboard
=======================

Services:
  api-server      HEALTHY   cpu: 23%  mem: 456MB  uptime: 3d 4h
  database        HEALTHY   cpu: 12%  mem: 2.1GB  connections: 45
  trading-bot     RUNNING   trades: 24  win_rate: 68%

Recent Errors (last 1h):
  2 ERROR: Connection timeout to redis
  1 ERROR: Rate limit exceeded for /api/markets

Alerts:
  [WARN] Redis connection unstable (2 timeouts in 1h)

Recommendations:
  1. Check Redis connectivity and increase timeout
  2. Consider adding retry logic for Redis operations

Would you like me to investigate the Redis issues?
```
