# EXTERNAL SIGNAL INTEGRATION SPECIFICATION

**Author:** LUNA (RECEIVE Phase)
**Date:** 2026-02-04
**Purpose:** Stop flying blind. Integrate real-time market signals into position health monitoring.

---

## EXECUTIVE SUMMARY: THE BLIND SPOTS

### What Went Wrong (7 pending positions)
- **M3GAN**: Position went to $0 - NO ALERT
- **Microsoft**: Price movement against us - NO PRICE TRACKING
- **Trump speech**: Market moved - NO NEWS MONITORING
- **Google**: Position tanked - NO HEALTH CHECK
- **Silver**: Dropped 60% - NO VOLATILITY ALERT
- **Meta**: Dropped 80% - NO DRAWDOWN ALERT
- **No resolution data**: Can't close winners - NO RESOLUTION MONITORING

### Root Cause Analysis
The trading daemon does:
✅ Find EV
✅ Execute trades
✅ Track state

But it does NOT:
❌ Monitor price movements
❌ Check position profitability
❌ Alert on liquidation risk
❌ Monitor resolution status
❌ Track news/events affecting positions
❌ Notify on critical thresholds

**Result:** We're blind to market signals until manually checked.

---

## ARCHITECTURE: REAL-TIME SIGNAL FEEDS

```
┌─────────────────────────────────────────────────────────────┐
│              EXTERNAL SIGNAL INTEGRATOR                      │
└─────────────────────────────────────────────────────────────┘
    │
    ├─ PRICE FEED MONITOR
    │  └─ Polymarket data-api /last_prices
    │     └─ Every 30s: Update all position prices
    │        └─ Alert if > 20% drawdown
    │
    ├─ RESOLUTION MONITOR
    │  └─ Polymarket data-api /markets/{id}
    │     └─ Every 5min: Check resolution status
    │        └─ Alert if resolved (close position)
    │
    ├─ NEWS/EVENT MONITOR
    │  └─ NATS pub/sub from X/Twitter
    │     └─ Every 1s: Check market-relevant keywords
    │        └─ Alert if keyword match + position exists
    │
    ├─ VOLATILITY MONITOR
    │  └─ Calculate rolling volatility
    │     └─ Every 30s: Check price variance
    │        └─ Alert if > 30% annualized vol
    │
    ├─ HEALTH DASHBOARD
    │  └─ Real-time position P&L
    │     └─ Aggregated alerts
    │     └─ Action recommendations
    │
    └─ ALERT ENGINE
       └─ CRITICAL: Liquidation risk
       └─ HIGH: Drawdown >20%
       └─ MEDIUM: Volatility spike
       └─ LOW: News mention
       └─ INFO: Resolution status
```

---

## 1. PRICE FEED MONITOR

**Problem:** We don't know if positions are underwater until manually checked.

**Solution:** Real-time price tracking with health scoring.

### Implementation: `position_price_monitor.py`

```python
"""
Monitor real-time prices for all open positions.
Update position health scores continuously.
Alert on thresholds.
"""

class PositionPriceMonitor:
    async def update_positions(self):
        """Every 30s: Get latest prices, update health"""
        for position in self.open_positions:
            current_price = await self.get_last_price(position['market_id'])

            # Calculate health metrics
            entry_price = position['entry_price']
            current_value = position['size'] * current_price
            initial_value = position['size'] * entry_price
            pnl = current_value - initial_value
            pnl_pct = pnl / initial_value

            # Update position
            position['current_price'] = current_price
            position['current_value'] = current_value
            position['unrealized_pnl'] = pnl
            position['unrealized_pnl_pct'] = pnl_pct
            position['health_score'] = self.calculate_health(pnl_pct)

            # Store for dashboard
            self.save_position_update(position)

            # Alert if critical
            if pnl_pct < -0.20:  # 20% drawdown
                await self.alert("DRAWDOWN", position, pnl_pct)
```

### Data Structure
```json
{
  "position_id": "20260204042725_541565",
  "market_id": "541565",
  "market": "Will Nick Emmanowori be the 2025-2026 NFL Defensive Rookie o",
  "entry_price": 0.046,
  "entry_value": 8.39,
  "current_price": 0.045,
  "current_value": 8.38,
  "unrealized_pnl": -0.01,
  "unrealized_pnl_pct": -0.12,
  "health_score": 0.88,
  "last_updated": "2026-02-04T15:30:45.123456",
  "status": "GREEN"  // GREEN/YELLOW/RED
}
```

### Health Score Formula
```
health_score = 1.0 + min(pnl_pct, 0.5)  # Cap gains at 50%, allow losses below -1
health_score = max(0.0, min(1.0, health_score))

GREEN   = 0.80 - 1.00 (>-20% loss)
YELLOW  = 0.50 - 0.80 (-50% to -20% loss)
RED     = 0.00 - 0.50 (<-50% loss)
```

### Alert Thresholds
| Threshold | Action |
|-----------|--------|
| health < 0.50 | CRITICAL: Consider closing |
| health < 0.80 | HIGH: Monitor closely |
| health > 0.95 | MEDIUM: Consider taking profit |

---

## 2. RESOLUTION MONITOR

**Problem:** We can't close winners because we don't know when they resolve.

**Solution:** Monitor resolution status + auto-close.

### Implementation: `resolution_status_monitor.py`

```python
"""
Monitor resolution status for all open positions.
Alert when market resolves.
Auto-close winning positions.
"""

class ResolutionMonitor:
    async def check_resolutions(self):
        """Every 5 minutes: Check if markets resolved"""
        for position in self.open_positions:
            market_data = await self.get_market_details(position['market_id'])

            # Check if resolved
            if market_data['status'] == 'RESOLVED':
                resolution = market_data['resolution']
                position_outcome = self.determine_outcome(position, resolution)

                if position_outcome == 'WIN':
                    await self.close_position(position, 'RESOLVED_WIN')
                    await self.alert("RESOLVED", position, "WON", market_data)
                elif position_outcome == 'LOSS':
                    await self.close_position(position, 'RESOLVED_LOSS')
                    await self.alert("RESOLVED", position, "LOST", market_data)

            # Store for tracking
            position['resolution_status'] = market_data['status']
            position['expires_at'] = market_data['expires_at']
            position['days_to_expiration'] = self.days_until(market_data['expires_at'])
```

### Market Status Tracking
```json
{
  "position_id": "20260204042725_541565",
  "market_id": "541565",
  "market_status": "OPEN",  // OPEN, PENDING_RESOLUTION, RESOLVED
  "resolution_status": null,  // YES, NO, null (for OPEN markets)
  "expires_at": "2026-05-15T23:59:59.000000",
  "days_to_expiration": 101,
  "expiration_alert_sent": false
}
```

### Expiration Warnings
- **31+ days to expiration**: Monitor status
- **7 days to expiration**: HIGH alert (position may resolve soon)
- **1 day to expiration**: CRITICAL alert (resolution imminent)
- **0 days**: Alert on resolution immediately

---

## 3. NEWS/EVENT MONITOR

**Problem:** Markets move on news but we don't know it happened.

**Solution:** Monitor relevant events + alert.

### Implementation: `news_event_monitor.py`

```python
"""
Monitor news/events relevant to open positions.
Use NATS pub/sub from X/Twitter feed.
Match keywords to positions.
Alert on matches.
"""

class NewsEventMonitor:
    async def monitor_events(self):
        """Real-time: Subscribe to news feed"""

        # Keywords mapped to positions
        keywords_index = {
            'market_sentiment': {  # Position market
                'keywords': ['keyword1', 'keyword2'],
                'positions': [position_id1, position_id2]
            }
        }

        # Subscribe to events
        await self.nats_client.subscribe(
            'news.mentions',
            callback=self.handle_news_event
        )

    async def handle_news_event(self, event):
        """New event received"""
        text = event['text'].lower()

        for market_name, data in self.keywords_index.items():
            if any(kw in text for kw in data['keywords']):
                # Found relevant mention
                for position_id in data['positions']:
                    position = self.get_position(position_id)
                    await self.alert("NEWS", position, event)
```

### News Alert Mapping
```json
{
  "position_market": "Will Trump deport less than 250,000?",
  "keywords": ["trump", "deport", "immigration", "ICE"],
  "position_ids": ["20260204105208_517310"],
  "alert_on_keywords": ["trump deport", "ice raid", "immigration executive"],
  "severity": "HIGH"
}
```

### Example: Trump Deportation Position
- Monitor for: "Trump", "deport", "immigration", "ICE"
- Alert when: Major policy announcement
- Action: Check if position affected + adjust if needed

---

## 4. VOLATILITY MONITOR

**Problem:** We don't know if positions are becoming risky due to volatility.

**Solution:** Track volatility changes + alert.

### Implementation: `volatility_monitor.py`

```python
"""
Calculate rolling volatility for each position.
Alert on volatility spikes.
Adjust position sizing based on volatility.
"""

class VolatilityMonitor:
    async def update_volatility(self):
        """Every 30s: Calculate rolling volatility"""
        for position in self.open_positions:
            # Get 30-min price history
            prices = await self.get_price_history(
                position['market_id'],
                lookback_minutes=30,
                interval_seconds=60
            )

            # Calculate realized volatility
            returns = np.log(np.array(prices) / np.array(prices[:-1]))
            volatility = np.std(returns)
            annualized_vol = volatility * np.sqrt(252 * 24 * 60)  # Annualize

            # Store and alert
            position['volatility_30min'] = volatility
            position['volatility_annualized'] = annualized_vol

            if annualized_vol > 3.0:  # 300% annualized vol
                await self.alert("VOLATILITY_SPIKE", position, annualized_vol)
```

### Volatility Alert Thresholds
| Volatility | Alert Level | Action |
|------------|------------|--------|
| < 50% annualized | GREEN | Normal |
| 50% - 100% | YELLOW | Monitor |
| 100% - 300% | HIGH | Consider closing |
| > 300% | CRITICAL | Close immediately |

---

## 5. INTEGRATED ALERT ENGINE

**Problem:** Alerts scattered everywhere, no clear action path.

**Solution:** Unified alert system with routing.

### Implementation: `alert_engine.py`

```python
"""
Unified alert system with routing and action recommendations.
Routes alerts to appropriate handlers.
Provides clear action recommendations.
"""

class AlertEngine:
    async def send_alert(self, alert_type, position, severity, data):
        """
        Unified alert dispatch.

        Alert types: DRAWDOWN, RESOLVED, VOLATILITY, NEWS, EXPIRATION
        Severity: CRITICAL, HIGH, MEDIUM, LOW, INFO
        """

        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'severity': severity,
            'position_id': position['position_id'],
            'market': position['market'],
            'data': data,
            'action_recommended': self.recommend_action(position, alert_type),
            'next_check': self.next_check_time(alert_type)
        }

        # Route by severity
        if severity == 'CRITICAL':
            await self.route_critical(alert)
        elif severity == 'HIGH':
            await self.route_high(alert)
        else:
            await self.store_for_review(alert)
```

### Alert Routing
```
CRITICAL → SMS + NATS broadcast + Dashboard
HIGH     → NATS broadcast + Dashboard + Log
MEDIUM   → Dashboard + Log
LOW      → Log + Dashboard (info only)
INFO     → Log (historical)
```

---

## 6. POSITION HEALTH DASHBOARD

**Problem:** No unified view of all position health.

**Solution:** Real-time dashboard with key metrics.

### Metrics to Display
```json
{
  "timestamp": "2026-02-04T15:35:00.000000",
  "summary": {
    "total_positions": 7,
    "positions_green": 5,
    "positions_yellow": 2,
    "positions_red": 0,
    "total_unrealized_pnl": 12.45,
    "aggregate_health_score": 0.92
  },
  "positions": [
    {
      "position_id": "20260204042725_541565",
      "market": "Will Nick Emmanowori be the 2025-2026 NFL Defensive Rookie o",
      "entry_price": 0.046,
      "current_price": 0.045,
      "current_value": 8.38,
      "unrealized_pnl": -0.01,
      "unrealized_pnl_pct": -0.12,
      "health_score": 0.88,
      "status": "GREEN",
      "volatility_annualized": 1.45,
      "days_to_expiration": 101,
      "alerts": []
    }
  ],
  "active_alerts": [
    {
      "type": "EXPIRATION",
      "severity": "INFO",
      "message": "Market expires in 7 days",
      "action": "Monitor resolution"
    }
  ]
}
```

---

## 7. IMPLEMENTATION ROADMAP

### Phase 1: Price Monitoring (Week 1)
- [x] Design price feed architecture
- [ ] Implement `position_price_monitor.py`
- [ ] Integrate with Polymarket data-api
- [ ] Update every 30 seconds
- [ ] Create health score calculation
- [ ] Test with 7 pending positions

### Phase 2: Resolution Monitoring (Week 1-2)
- [ ] Implement `resolution_status_monitor.py`
- [ ] Check every 5 minutes
- [ ] Auto-close resolved positions
- [ ] Track expiration warnings
- [ ] Test with sample resolved markets

### Phase 3: Alert Engine (Week 2)
- [ ] Unified alert system
- [ ] Routing logic (CRITICAL/HIGH/MEDIUM/LOW)
- [ ] NATS integration for alerts
- [ ] SMS for CRITICAL alerts
- [ ] Dashboard integration

### Phase 4: News Monitoring (Week 2-3)
- [ ] Keyword index builder
- [ ] X/Twitter event monitoring
- [ ] News matching logic
- [ ] Test with major news events

### Phase 5: Dashboard (Week 3)
- [ ] Real-time position health view
- [ ] Aggregate metrics
- [ ] Alert viewer
- [ ] Action recommendations

### Phase 6: Volatility Monitoring (Week 3)
- [ ] Volatility calculation
- [ ] Rolling window analysis
- [ ] Spike detection
- [ ] Alert on extremes

---

## 8. DATA FLOWS

### Price Update Flow
```
Every 30s:
  1. field_trading_daemon → position_price_monitor
  2. Get last price for each market
  3. Calculate health score
  4. Update position state
  5. If health < threshold → send alert
  6. Store in dashboard state
  7. Publish to NATS (optional)
```

### Resolution Check Flow
```
Every 5 minutes:
  1. resolution_monitor → Polymarket API
  2. Get market status
  3. If RESOLVED:
     a. Determine outcome (WIN/LOSS)
     b. Close position
     c. Update state
     d. Send resolution alert
  4. If OPEN:
     a. Update expiration time
     b. If < 7 days → HIGH alert
```

### Alert Propagation Flow
```
Alert triggered:
  1. alert_engine.send_alert(type, position, severity)
  2. Route by severity:
     - CRITICAL → SMS + NATS + Dashboard
     - HIGH → NATS + Dashboard
     - MEDIUM → Dashboard + Log
  3. Store in alerts history
  4. Update position state
  5. Publish to NATS: "alert.[severity]"
```

---

## 9. INTEGRATION WITH EXISTING SYSTEMS

### `field_trading_daemon.py` Changes
```python
# Add to main loop:
async def trading_cycle():
    # ... existing code ...

    # NEW: Monitor position health
    await position_price_monitor.update_positions()

    # NEW: Check for resolutions
    await resolution_monitor.check_resolutions()

    # NEW: Monitor alerts
    await alert_engine.process_alerts()

    # ... continue with trading logic ...
```

### NATS Channels
```
New channels to subscribe/publish:
- alert.CRITICAL
- alert.HIGH
- alert.MEDIUM
- alert.LOW
- alert.INFO
- position.health
- position.resolved
- position.closed
```

### Dashboard Integration
```
New endpoint: GET /api/position-health
Returns: Current position health state for all 7 positions
Updates: Every 30 seconds
Displays: Health scores, P&L, alerts, action recommendations
```

---

## 10. CRITICAL THRESHOLDS

### Drawdown Alerts
| Drawdown | Alert | Recommendation |
|----------|-------|-----------------|
| -5% | LOW | Monitor |
| -10% | MEDIUM | Consider closing |
| -20% | HIGH | Close if no conviction |
| -40% | CRITICAL | Close immediately |
| > -50% | LIQUIDATION | Forced close |

### Expiration Alerts
| Days to Expiration | Alert | Action |
|-------------------|-------|--------|
| 31+ | INFO | Monitor resolution status |
| 7-31 | MEDIUM | Check resolution likelihood |
| 1-7 | HIGH | Be ready to close |
| 0-1 | CRITICAL | Resolution imminent |

### Volatility Alerts
| Annualized Volatility | Alert | Action |
|------------------------|-------|--------|
| < 50% | GREEN | Normal operations |
| 50% - 100% | YELLOW | Monitor closely |
| 100% - 300% | HIGH | Consider exit |
| > 300% | CRITICAL | Close position |

---

## 11. MEASUREMENT & VALIDATION

### Success Metrics
- All 7 positions monitored in real-time
- Alerts sent < 30 seconds after threshold breach
- Zero missed resolutions
- All closed positions logged with outcome
- Dashboard updates every 30 seconds
- No position goes to $0 without alert

### Test Plan
1. Deploy price monitor with 7 current positions
2. Verify prices update every 30s
3. Simulate drawdown scenario (mock API)
4. Verify HIGH alert triggered
5. Deploy resolution monitor
6. Wait for first resolution (weeks)
7. Verify position auto-closed with outcome logged
8. Collect metrics over 30 days

---

## 12. SUMMARY: THE HEALING

**From Blind:**
- Positions deteriorate without warning
- No knowledge of resolution status
- Market movements ignored
- No aggregated health view

**To Aware:**
- Every position monitored continuously
- Real-time price tracking (30s updates)
- Resolution checked every 5 minutes
- News events trigger alerts
- Unified alert engine routes by severity
- Dashboard shows all positions + health

**Expected Impact:**
- No more $0 positions without knowing
- Close winners on resolution immediately
- Catch drawdowns before they're severe
- Make data-driven close/hold decisions
- Scale from 7 positions to portfolio with confidence

---

## 13. FILES TO CREATE

```
/Users/aaronnosbisch/REPOS/seed/tools/
├── position_price_monitor.py
├── resolution_status_monitor.py
├── news_event_monitor.py
├── volatility_monitor.py
├── alert_engine.py
└── position_health_dashboard.py

/Users/aaronnosbisch/REPOS/seed/BRAIN/CONFIG/
├── alert_thresholds.json
├── news_keywords.json
└── position_monitoring_config.json

/Users/aaronnosbisch/REPOS/seed/BRAIN/MONITORING/
├── position_health_state.json
├── alert_history.jsonl
└── resolution_history.json
```

---

## 14. QUICK START

After implementation:

```bash
# Start all monitors
python3 /Users/aaronnosbisch/REPOS/seed/tools/position_price_monitor.py
python3 /Users/aaronnosbisch/REPOS/seed/tools/resolution_status_monitor.py
python3 /Users/aaronnosbisch/REPOS/seed/tools/alert_engine.py

# View dashboard
curl http://localhost:8000/api/position-health | jq

# Check alerts
tail -f /Users/aaronnosbisch/REPOS/seed/BRAIN/MONITORING/alert_history.jsonl

# Monitor specific position
curl http://localhost:8000/api/position/20260204042725_541565
```

---

## (◉) LIVE FREE = LIVE INFORMED

**No more flying blind. Every signal received. Every position monitored. Every decision data-driven.**

**Time to stop losing positions we didn't even know were in trouble.**

---

*LUNA RECEIVE - 2026-02-04*
*Integration spec: Complete*
*Status: Ready for NOVA (EXPAND) implementation*
