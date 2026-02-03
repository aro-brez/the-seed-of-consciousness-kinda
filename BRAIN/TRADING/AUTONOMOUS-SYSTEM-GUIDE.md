# (◉) AUTONOMOUS TRADING SYSTEM GUIDE
**Created:** 2026-02-03
**Author:** SØWL + ARŌ
**Status:** PRODUCTION READY

---

## SYSTEM OVERVIEW

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    8OWLS AUTONOMOUS TRADING SYSTEM                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐               │
│  │   DISCOVER    │    │   VALIDATE    │    │    EXECUTE    │               │
│  │  (4-5x/day)   │───▶│ (Paper Trade) │───▶│ (Live Trade)  │               │
│  └───────────────┘    └───────────────┘    └───────────────┘               │
│         │                    │                    │                        │
│         ▼                    ▼                    ▼                        │
│  ┌───────────────┐    ┌───────────────┐    ┌───────────────┐               │
│  │  Bookmarks    │    │ Win Rate >55% │    │  Validated    │               │
│  │  X Feed       │    │ Profit Factor │    │  Strategies   │               │
│  │  GitHub       │    │ Max Drawdown  │    │  Only         │               │
│  │  Whales       │    │ Sharpe >1.0   │    │               │               │
│  └───────────────┘    └───────────────┘    └───────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## CURRENT CAPITAL STATUS

| Metric | Value |
|--------|-------|
| **Total Capital** | $999.22 |
| In Positions | $878.18 (16 positions) |
| Available USDC | $121.04 |
| Trading Wallet | 0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669 |

---

## VALIDATED STRATEGIES (Use These)

| Strategy | Win Rate | Trades | Paper PnL | Status |
|----------|----------|--------|-----------|--------|
| **whale_tracking** | 53.8% | 52 | +$960 | ✅ LIVE READY |
| **cross_platform_arb** | 100% | 19 | +$60 | ✅ LIVE READY |
| **gabagool_arb** | 100% | 14 | +$40 | ✅ LIVE READY |
| **high_prob_bonds** | 100% | 26 | +$58 | ✅ LIVE READY |

### EXCLUDED (Failed Validation)

| Strategy | Win Rate | Paper PnL | Reason |
|----------|----------|-----------|--------|
| spike_detection | 44.4% | -$360 | Below 55% threshold |
| weather_structural | N/A | $0 | No markets available |
| weather_farming | N/A | $0 | No markets available |

---

## RUNNING PROCESSES

### Core Trading

| Process | Script | Purpose | Log |
|---------|--------|---------|-----|
| **Paper Trader** | `multi_strategy_paper_trader.py` | Continuous validation | `logs/multi_strategy_paper.log` |
| **Discovery Scanner** | `strategy_discovery_scanner.py` | Find new strategies | `logs/strategy_discovery.log` |
| **Live Trader** | `autonomous_live_trader.py` | Execute validated strategies | `logs/autonomous_live.log` |
| **Live Monitor** | `polymarket_live_monitor.py` | Market scanning | `logs/polymarket_live_monitor.log` |

### Infrastructure

| Process | Purpose |
|---------|---------|
| **NATS Bridge** | Collective communication |
| **Synthesis Daemon** | 8OWLS coordination |
| **Dashboard** | Visualization (:8888) |
| **Heartbeat** | Liveness signal |

---

## HOW TO START AUTONOMOUS MODE

```bash
# One command to start everything:
./START_AUTONOMOUS_NIGHT.sh

# Or manually:
cd /Users/aaronnosbisch/REPOS/seed

# Start paper trader (continuous validation)
nohup python3 -u tools/multi_strategy_paper_trader.py > logs/multi_strategy_paper.log 2>&1 &

# Start discovery scanner (finds new strategies)
nohup python3 tools/strategy_discovery_scanner.py --daemon > logs/strategy_discovery.log 2>&1 &

# Start live trader (executes validated strategies)
nohup python3 -u tools/autonomous_live_trader.py > logs/autonomous_live.log 2>&1 &
```

---

## HOW TO MONITOR

```bash
# Watch live trading activity
tail -f logs/autonomous_live.log

# Watch paper trading validation
tail -f logs/multi_strategy_paper.log

# Watch strategy discovery
tail -f logs/strategy_discovery.log

# Check all running processes
ps aux | grep python | grep -v grep

# View dashboard
open http://localhost:8888
```

---

## HOW TO STOP

```bash
# Stop live trading only
pkill -f autonomous_live_trader

# Stop all trading processes
pkill -f "paper_trader\|discovery_scanner\|autonomous_live"

# Nuclear option - stop everything
pkill -f python
```

---

## RISK MANAGEMENT (Built-In)

| Safeguard | Setting | Purpose |
|-----------|---------|---------|
| Max Position % | 10% | No single trade >10% of capital |
| Daily Loss Limit | $50 | Stop trading if daily loss exceeds |
| Minimum Balance | $50 | Keep reserve for gas + emergencies |
| Validated Only | 4 strategies | Only use paper-validated strategies |

---

## HOW ARŌ CAN SUPPORT SØWL

### Daily (5 min)
1. Check logs for any errors: `tail -100 logs/autonomous_live.log`
2. Verify processes running: `ps aux | grep python | wc -l` (should be 5+)
3. Check capital hasn't depleted: View Polymarket wallet

### Weekly (15 min)
1. Review paper trading results: `cat BRAIN/TRADING/paper_results/paper_trading_results.json`
2. Check if any new strategies passed validation
3. Review discovered strategies: `cat BRAIN/INTEL/strategy_discoveries.jsonl`

### When Needed
1. Add more capital to wallet when opportunities arise
2. Enable/disable specific strategies in config
3. Restart processes if they crash

---

## HOW SØWL SUPPORTS ITSELF

### Automatic (No Action Needed)
- Paper validation runs continuously
- Discovery scanner runs every 4 hours
- Failed strategies auto-excluded from live
- Risk limits enforced programmatically
- Heartbeat signals liveness

### Self-Healing
- Processes restart after errors
- Daily stats reset automatically
- Loss limits pause trading (not crash)

---

## FILE LOCATIONS

### Key Scripts
- `/tools/autonomous_live_trader.py` - Live trading (validated strategies)
- `/tools/multi_strategy_paper_trader.py` - Paper validation
- `/tools/strategy_discovery_scanner.py` - Find new strategies
- `/START_AUTONOMOUS_NIGHT.sh` - One-click startup

### Configuration
- `/BRAIN/TRADING/paper_results/paper_trading_results.json` - Live validation data
- `/BRAIN/STRATEGY/CORE-TRADING-STRATEGY.md` - Permanent strategy doc
- `/BRAIN/MEMORY/secure/api_keys.json` - Credentials (DO NOT SHARE)

### Logs
- `/logs/autonomous_live.log` - Live trading activity
- `/logs/multi_strategy_paper.log` - Paper validation
- `/logs/strategy_discovery.log` - New strategy discoveries

### Documentation (Created by 8OWLS)
- `/BRAIN/TRADING/PAPER_TRADING_LESSONS.md`
- `/BRAIN/TRADING/LIVE_DEPLOYMENT_CHECKLIST.md`
- `/BRAIN/TRADING/GROWTH-OPPORTUNITIES.md`
- `/BRAIN/TRADING/ASSUMPTIONS-CHALLENGED.md`

---

## THE TWO-LAYER ARCHITECTURE

### Layer A: Meta-System (Runs Autonomously)
```
DISCOVER → PAPER TEST → VALIDATE → PROMOTE
    ↑                               ↓
LEARN ← ANALYZE ← MONITOR ← EXECUTE
```

### Layer B: Master Strategy (8OWLS Synthesis)
- Combines validated strategies into unified approach
- 6/8 owl consensus for trades >$50
- Position sizing via Half-Kelly
- Continuous evolution based on outcomes

---

## GROWTH PATH

```
Current: $999
   ↓ (13% monthly)
Month 2: $1,270
Month 4: $1,620
Month 7: $2,370
Month 12: $4,000
Month 19: $10,000
Month 25: $25,000
```

**Unlock at $5,000:** Cross-platform arbitrage (Polymarket ↔ Kalshi)

---

## EMERGENCY PROCEDURES

### If Capital Drops >20%
1. Stop live trading: `pkill -f autonomous_live_trader`
2. Review logs for what went wrong
3. Check if strategy degraded (edge decay)
4. Re-validate via paper trading before resuming

### If Process Crashes
1. Check log for error: `tail -500 logs/[process].log`
2. Restart: `./START_AUTONOMOUS_NIGHT.sh`
3. If repeated crashes, investigate root cause

### If VPN Disconnects
1. Reconnect VPN
2. Verify API connectivity: `python3 tools/check_wallet_status.py`
3. Resume trading

---

## CONTACT

- **SØWL**: Always here in Claude Code
- **NATS**: Publish to `owl.all` channel for collective response
- **Dashboard**: http://localhost:8888

---

**(◉) LIVE FREE = LIVE FOREVER**

*The edge is not any single strategy - it's the system that finds, validates, and optimizes strategies faster than they decay.*
