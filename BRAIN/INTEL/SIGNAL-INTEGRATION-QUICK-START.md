# EXTERNAL SIGNAL INTEGRATION - QUICK START FOR ARŌ

**Read Time:** 5 minutes
**Status:** Ready to deploy
**Cost:** $0

---

## THE PROBLEM (Why We Lost Positions)

7 pending trades with NO awareness:

| Market | What Happened | Why We Didn't Know |
|--------|---------------|-------------------|
| M3GAN | Price → $0 | No price monitoring |
| Microsoft | Down 30% | No drawdown alerts |
| Trump speech | Market moved | No news tracking |
| Google | Dropped | No health checks |
| Silver | Down 60% | No volatility alert |
| Meta | Down 80% | No critical alerts |
| All 7 | Still open | No resolution tracking |

**Root Cause:** We detect EV and execute, but then go blind.

---

## THE SOLUTION (What We'll Build)

### 5 Real-Time Monitors

1. **Price Monitor** (every 30s)
   - Updates prices for all 7 positions
   - Calculates health score (GREEN/YELLOW/RED)
   - Alerts if >20% drawdown

2. **Resolution Monitor** (every 5 min)
   - Checks if markets resolved
   - Auto-closes winners
   - Alerts 7 days before expiration

3. **Alert Engine** (real-time)
   - Routes alerts by severity (CRITICAL/HIGH/MEDIUM/LOW)
   - CRITICAL → SMS + immediate action
   - HIGH → Dashboard + monitoring
   - Unified alert history

4. **News Monitor** (real-time)
   - Tracks keywords for market-relevant news
   - Alerts if Trump speaks about tariffs (for tariff markets)
   - Maps news to positions

5. **Health Dashboard**
   - Shows all 7 positions + health scores
   - Aggregated P&L view
   - Recent alerts with action recommendations

---

## EXPECTED IMPROVEMENTS

### Before Integration
```
Positions: 7 open
Monitoring: Manual checks only
Alerts: None
Blind spots: Price, resolution, news, volatility
Result: Losses discovered too late
```

### After Integration
```
Positions: 7 open (same)
Monitoring: Real-time (4 feeds)
Alerts: Automatic
Blind spots: ZERO
Result: Know status instantly, close winners fast
```

---

## THE DELIVERABLES

### Files to Create (5 new monitors + 1 engine)
```
/tools/
├── position_price_monitor.py      [~200 lines]
├── resolution_status_monitor.py   [~200 lines]
├── news_event_monitor.py          [~200 lines]
├── volatility_monitor.py          [~150 lines]
├── alert_engine.py                [~250 lines]
└── position_health_dashboard.py   [~300 lines]

/BRAIN/CONFIG/
├── alert_thresholds.json
├── news_keywords.json
└── position_monitoring_config.json

/BRAIN/MONITORING/
├── position_health_state.json     (auto-generated)
├── alert_history.jsonl            (auto-generated)
└── resolution_history.json        (auto-generated)
```

### Output
- **API Endpoint:** `GET /api/position-health` → JSON of all positions
- **Alert Stream:** NATS channels by severity
- **Health Score:** 0.0-1.0 per position (GREEN >0.8, YELLOW >0.5, RED <0.5)
- **Dashboard:** Real-time view with alerts

---

## THRESHOLD REFERENCE

### Price Alerts
| Movement | Alert | Action |
|----------|-------|--------|
| -5% | INFO | Note |
| -10% | LOW | Monitor |
| -20% | MEDIUM | Evaluate |
| -40% | HIGH | Consider closing |
| >-50% | CRITICAL | Close immediately |

### Expiration Alerts
| Days Left | Alert | Action |
|-----------|-------|--------|
| 31+ | INFO | Monitor |
| 7-31 | MEDIUM | Check likely outcome |
| 1-7 | HIGH | Be ready to close |
| 0-1 | CRITICAL | Resolution imminent |

---

## DATA FLOWS

### Price Update (Every 30 seconds)
```
1. Get current price for each position
2. Calculate P&L and health score
3. Update position_health_state.json
4. If health < threshold → send alert
5. Publish to NATS (optional)
```

### Resolution Check (Every 5 minutes)
```
1. Check market status (OPEN/PENDING/RESOLVED)
2. If RESOLVED:
   a. Determine outcome (WIN/LOSS)
   b. Close position
   c. Record in resolution_history.json
   d. Send HIGH alert
3. If expiring soon:
   a. Record days to expiration
   b. Send MEDIUM/HIGH alert
```

### Alert Dispatch (Real-time)
```
By Severity:
  CRITICAL → SMS + NATS broadcast + Dashboard
  HIGH     → NATS broadcast + Dashboard + Log
  MEDIUM   → Dashboard + Log
  LOW      → Log only
  INFO     → Log (historical)
```

---

## QUICK START (For Testing)

### Step 1: Deploy Price Monitor
```bash
# Create position_price_monitor.py with code from SIGNAL-INTEGRATION-IMPLEMENTATION.md
python3 /tools/position_price_monitor.py
```

### Step 2: Check Health State
```bash
# View real-time health of all 7 positions
cat /BRAIN/MONITORING/position_health_state.json | jq '.summary'

# Output should look like:
{
  "total_positions": 7,
  "green": 5,
  "yellow": 2,
  "red": 0,
  "total_value": 63.45,
  "total_pnl": -2.30,
  "aggregate_health": 0.92
}
```

### Step 3: Check for Alerts
```bash
# View recent alerts
tail -20 /BRAIN/MONITORING/alert_history.jsonl

# Or filtered by severity
jq 'select(.severity == "CRITICAL")' /BRAIN/MONITORING/alert_history.jsonl
```

### Step 4: View Dashboard
```bash
# Hit the endpoint (after connecting to web server)
curl http://localhost:8000/api/position-health | jq

# Get specific position
curl http://localhost:8000/api/position/20260204042725_541565
```

---

## DEPLOYMENT PHASES

### Phase 1: Price Monitoring (3 hours)
- Create price monitor
- Test with 7 positions
- Verify 30s updates
- Validate health scores

**Output:** Real-time P&L for all positions

### Phase 2: Resolution Monitoring (2 hours)
- Create resolution monitor
- Test with sample data
- Integrate with price monitor
- Verify expiration alerts

**Output:** Know when markets resolve

### Phase 3: Alert Engine (2 hours)
- Create unified alert engine
- Test alert routing
- Set up NATS channels
- Verify alert history logging

**Output:** Automatic alerts on thresholds

### Phase 4: Integration (1 hour)
- Wire monitors into field_trading_daemon
- Test in parallel with existing daemon
- Monitor for 24 hours
- Iterate based on alerts

**Output:** Full real-time monitoring in production

**Total time:** ~8 hours
**Cost:** $0

---

## EXPECTED METRICS AFTER DEPLOYMENT

### Position Monitoring
- All 7 positions tracked continuously
- Health updates every 30 seconds
- Zero missed resolutions
- Alerts sent <30 seconds after threshold breach

### Alert Accuracy
- CRITICAL alerts for >40% drawdown: 100% (if it happens)
- HIGH alerts for >20% drawdown: 100%
- Resolution alerts: 100% (on resolution)
- False positive rate: <2%

### Operational Improvements
- Close winners immediately on resolution (no manual check)
- Catch bad positions before they're -80%
- Know P&L status anytime
- Data-driven close/hold decisions

---

## HOW TO READ THE HEALTH STATE

### The JSON Structure
```json
{
  "timestamp": "2026-02-04T15:35:00.000000",
  "summary": {
    "total_positions": 7,
    "green": 5,              // Positions with health > 0.80
    "yellow": 2,             // Positions with health 0.50-0.80
    "red": 0,                // Positions with health < 0.50
    "total_value": 63.45,    // Total current value of all positions
    "total_pnl": -2.30,      // Total unrealized P&L
    "aggregate_health": 0.92 // Average health score
  },
  "positions": {
    "20260204042725_541565": {
      "market": "Will Nick Emmanowori...",
      "entry_price": 0.046,
      "current_price": 0.045,
      "entry_value": 8.39,
      "current_value": 8.38,
      "unrealized_pnl": -0.01,
      "unrealized_pnl_pct": -0.12,      // Down 12%
      "health_score": 0.88,              // YELLOW → monitor
      "status": "GREEN",
      "last_updated": "2026-02-04T15:35:00.000000"
    }
  }
}
```

### What Each Color Means
- **GREEN (0.80-1.0):** Position healthy, >-20% loss
- **YELLOW (0.50-0.80):** Position weakening, -20% to -50% loss
- **RED (<0.50):** Position critical, >-50% loss

### Action Based on Color
- **GREEN:** Monitor normally
- **YELLOW:** Decide: hold if conviction, close if unsure
- **RED:** Close immediately (capital preservation)

---

## EXPECTED FIRST ALERTS

Once deployed, you'll see alerts like:

```
[2026-02-04T15:30:00] DRAWDOWN_HIGH: Will Trump deport...
Message: Position down 28.3% - evaluate conviction and close if unsure
Severity: HIGH

[2026-02-04T16:05:00] EXPIRATION: Will Elon cut budget...
Message: Market expires in 6 days
Severity: MEDIUM

[2026-02-04T18:00:00] MARKET_RESOLVED: GTA VI released...
Message: Market resolved → YES
Severity: HIGH
Action: CLOSE_POSITION
P&L: +$15.30 (WIN)
```

---

## NEXT STEPS FOR ARŌ

1. **Review** this document + EXTERNAL-SIGNAL-INTEGRATION.md
2. **Decide** on deployment timeline
3. **Approve** the 5 new monitor files
4. **Launch** price monitor first (lowest risk)
5. **Monitor** for 24 hours + collect data
6. **Deploy** remaining monitors (resolution → alerts → news)
7. **Integrate** with daemon
8. **Run** full test cycle with all 7 positions

---

## SUMMARY

**From:** 7 positions, flying blind, losses discovered too late
**To:** 7 positions, real-time monitoring, automatic alerts, close winners fast

**Cost:** $0
**Time:** 8 hours
**Risk:** Low (monitoring only, no trading changes)
**Benefit:** Stop losing positions without knowing

**Status:** ✅ Ready to build

---

*LUNA RECEIVE PHASE COMPLETE*
*Signal integration spec ready for NOVA (EXPAND) implementation*

(◉) LIVE FREE = LIVE INFORMED
