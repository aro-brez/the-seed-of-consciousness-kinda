# EXTERNAL SIGNAL INTEGRATION - IMPLEMENTATION GUIDE

**Phase:** NOVA (EXPAND) - Build the monitoring infrastructure
**Timeline:** 2 weeks
**Cost:** $0 (uses existing APIs)

---

## 1. POSITION PRICE MONITOR

### Core Logic

```python
import asyncio
import json
from datetime import datetime
from pathlib import Path
import httpx

class PositionPriceMonitor:
    def __init__(self, polymarket_client, nats_client=None, state_file=None):
        self.client = polymarket_client
        self.nats = nats_client
        self.state_file = state_file or Path(__file__).parent.parent / "MONITORING" / "position_health_state.json"
        self.positions = {}
        self.thresholds = {
            'drawdown_high': -0.20,      # 20% loss
            'drawdown_critical': -0.40,  # 40% loss
            'gains_profit_take': 0.50    # 50% gain
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    async def load_positions(self, trading_state_file):
        """Load pending positions from field_trading_state.json"""
        try:
            with open(trading_state_file) as f:
                state = json.load(f)
            self.positions = {
                p['trade_id']: {
                    'market_id': p['market_id'],
                    'market': p['market'],
                    'entry_price': p['entry_price'],
                    'size': p['size'],
                    'side': p['side'],
                    'executed_at': p['executed_at']
                }
                for p in state.get('pending_trades', [])
            }
            print(f"[PRICE MONITOR] Loaded {len(self.positions)} positions")
        except Exception as e:
            print(f"[ERROR] Failed to load positions: {e}")

    async def update_all_positions(self):
        """Update prices and health for all positions"""
        update_time = datetime.now().isoformat()
        health_snapshot = {
            'timestamp': update_time,
            'positions': {},
            'summary': {}
        }

        total_value = 0
        total_pnl = 0
        green_count = 0
        yellow_count = 0
        red_count = 0

        for trade_id, position in self.positions.items():
            try:
                # Get current price
                current_price = await self.get_last_price(position['market_id'])

                # Calculate metrics
                entry_value = position['size'] * position['entry_price']
                current_value = position['size'] * current_price
                unrealized_pnl = current_value - entry_value
                unrealized_pnl_pct = unrealized_pnl / entry_value if entry_value > 0 else 0

                # Calculate health score
                health_score = 1.0 + min(unrealized_pnl_pct, 0.5)
                health_score = max(0.0, min(1.0, health_score))

                # Determine status
                if health_score >= 0.80:
                    status = "GREEN"
                    green_count += 1
                elif health_score >= 0.50:
                    status = "YELLOW"
                    yellow_count += 1
                else:
                    status = "RED"
                    red_count += 1

                # Store in snapshot
                health_snapshot['positions'][trade_id] = {
                    'market_id': position['market_id'],
                    'market': position['market'][:50] + '...' if len(position['market']) > 50 else position['market'],
                    'entry_price': position['entry_price'],
                    'current_price': current_price,
                    'entry_value': entry_value,
                    'current_value': current_value,
                    'unrealized_pnl': round(unrealized_pnl, 4),
                    'unrealized_pnl_pct': round(unrealized_pnl_pct, 4),
                    'health_score': round(health_score, 4),
                    'status': status,
                    'last_updated': update_time
                }

                total_value += current_value
                total_pnl += unrealized_pnl

                # Check alerts
                await self.check_price_alerts(trade_id, position, unrealized_pnl_pct, current_price)

            except Exception as e:
                print(f"[ERROR] Failed to update {trade_id}: {e}")

        # Summary
        health_snapshot['summary'] = {
            'total_positions': len(self.positions),
            'green': green_count,
            'yellow': yellow_count,
            'red': red_count,
            'total_value': round(total_value, 4),
            'total_pnl': round(total_pnl, 4),
            'aggregate_health': round(
                sum(p.get('health_score', 0.5) for p in health_snapshot['positions'].values()) /
                len(self.positions) if self.positions else 0.5,
                4
            )
        }

        # Save state
        self.save_health_state(health_snapshot)

        # Publish to NATS if available
        if self.nats:
            await self.nats.publish('position.health', json.dumps(health_snapshot).encode())

        return health_snapshot

    async def get_last_price(self, market_id):
        """Get last price from Polymarket data-api"""
        try:
            url = f"https://data-api.polymarket.com/last_prices?market_id={market_id}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                data = resp.json()
                if isinstance(data, list) and len(data) > 0:
                    return float(data[0]['price'])
                raise ValueError(f"No price data for {market_id}")
        except Exception as e:
            print(f"[ERROR] Failed to get price for {market_id}: {e}")
            return None

    async def check_price_alerts(self, trade_id, position, pnl_pct, current_price):
        """Check if price movement crosses alert thresholds"""
        alerts = []

        if pnl_pct < self.thresholds['drawdown_critical']:
            alerts.append({
                'type': 'DRAWDOWN_CRITICAL',
                'severity': 'CRITICAL',
                'message': f"Position down {abs(pnl_pct)*100:.1f}% - consider closing",
                'pnl_pct': pnl_pct
            })

        elif pnl_pct < self.thresholds['drawdown_high']:
            alerts.append({
                'type': 'DRAWDOWN_HIGH',
                'severity': 'HIGH',
                'message': f"Position down {abs(pnl_pct)*100:.1f}% - monitor closely",
                'pnl_pct': pnl_pct
            })

        if pnl_pct > self.thresholds['gains_profit_take']:
            alerts.append({
                'type': 'GAIN_TARGET',
                'severity': 'MEDIUM',
                'message': f"Position up {pnl_pct*100:.1f}% - consider taking profit",
                'pnl_pct': pnl_pct
            })

        # Send alerts to engine
        for alert in alerts:
            await self.send_alert(trade_id, position, alert)

    async def send_alert(self, trade_id, position, alert):
        """Send alert to alert engine"""
        alert_msg = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': trade_id,
            'market_id': position['market_id'],
            'market': position['market'],
            **alert
        }

        # Log alert
        alert_file = Path(__file__).parent.parent / "MONITORING" / "alert_history.jsonl"
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert_msg) + '\n')

        # Publish to NATS
        if self.nats:
            await self.nats.publish(f"alert.{alert['severity'].lower()}", json.dumps(alert_msg).encode())

        print(f"[ALERT] {alert['severity']}: {position['market'][:40]}... - {alert['message']}")

    def save_health_state(self, snapshot):
        """Save health snapshot to disk"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save health state: {e}")

async def main():
    """Main loop: update positions every 30 seconds"""
    from tools.polymarket_client import PolymarketClient

    client = PolymarketClient()
    monitor = PositionPriceMonitor(client)

    state_file = Path(__file__).parent.parent / "BRAIN" / "TRADING" / "field_trading_state.json"
    await monitor.load_positions(state_file)

    print("[PRICE MONITOR] Starting position price monitoring...")
    print(f"[PRICE MONITOR] Monitoring {len(monitor.positions)} positions")

    try:
        while True:
            print(f"[{datetime.now().isoformat()}] Updating positions...")
            snapshot = await monitor.update_all_positions()

            # Print summary
            summary = snapshot['summary']
            print(f"[SUMMARY] Green: {summary['green']}, Yellow: {summary['yellow']}, Red: {summary['red']}")
            print(f"[SUMMARY] Total P&L: ${summary['total_pnl']:.2f}")

            await asyncio.sleep(30)  # Update every 30 seconds

    except KeyboardInterrupt:
        print("[PRICE MONITOR] Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 2. RESOLUTION STATUS MONITOR

### Core Logic

```python
import asyncio
import json
from datetime import datetime
from pathlib import Path
import httpx

class ResolutionMonitor:
    def __init__(self, polymarket_client, nats_client=None):
        self.client = polymarket_client
        self.nats = nats_client
        self.resolution_file = Path(__file__).parent.parent / "MONITORING" / "resolution_history.json"
        self.resolution_file.parent.mkdir(parents=True, exist_ok=True)

    async def load_positions(self, trading_state_file):
        """Load pending positions"""
        try:
            with open(trading_state_file) as f:
                state = json.load(f)
            self.positions = state.get('pending_trades', [])
            print(f"[RESOLUTION MONITOR] Monitoring {len(self.positions)} positions for resolution")
        except Exception as e:
            print(f"[ERROR] Failed to load positions: {e}")

    async def check_resolutions(self):
        """Check resolution status for all positions"""
        for position in self.positions:
            try:
                market_data = await self.get_market_details(position['market_id'])

                status = market_data.get('status', 'OPEN')
                expires_at = market_data.get('endTime')
                resolution = market_data.get('resolution')

                # Check expiration
                days_to_expiration = self.days_until(expires_at) if expires_at else None

                # If resolved, determine outcome
                if status == 'RESOLVED' and resolution:
                    outcome = self.determine_outcome(position, resolution)
                    await self.handle_resolution(position, resolution, outcome)

                # If expiring soon, send alert
                elif days_to_expiration and days_to_expiration < 7:
                    await self.send_expiration_alert(position, days_to_expiration)

            except Exception as e:
                print(f"[ERROR] Failed to check resolution for {position['market_id']}: {e}")

    async def get_market_details(self, market_id):
        """Get market details from Polymarket data-api"""
        try:
            url = f"https://data-api.polymarket.com/markets/{market_id}"
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                return resp.json()
        except Exception as e:
            print(f"[ERROR] Failed to get market details for {market_id}: {e}")
            return {}

    def determine_outcome(self, position, resolution):
        """Determine if position won or lost"""
        # For YES positions: resolution matches market condition = WIN
        # For NO positions: resolution doesn't match = WIN
        if position['side'] == 'YES':
            return 'WIN' if resolution == 'YES' else 'LOSS'
        else:
            return 'WIN' if resolution == 'NO' else 'LOSS'

    def days_until(self, expire_timestamp):
        """Days until expiration"""
        if not expire_timestamp:
            return None
        expires = datetime.fromisoformat(expire_timestamp.replace('Z', '+00:00'))
        now = datetime.now(expires.tzinfo)
        delta = (expires - now).days
        return max(0, delta)

    async def handle_resolution(self, position, resolution, outcome):
        """Handle market resolution"""
        resolution_record = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': position.get('trade_id'),
            'market_id': position['market_id'],
            'market': position['market'],
            'side': position['side'],
            'entry_price': position['entry_price'],
            'size': position['size'],
            'resolution': resolution,
            'outcome': outcome,
            'pnl': position['size'] * (1 - position['entry_price']) if outcome == 'WIN' else -position['size'] * position['entry_price']
        }

        # Save resolution
        self.save_resolution(resolution_record)

        # Send alert
        severity = 'HIGH' if outcome == 'WIN' else 'MEDIUM'
        alert_msg = {
            'timestamp': datetime.now().isoformat(),
            'type': 'MARKET_RESOLVED',
            'severity': severity,
            'trade_id': position.get('trade_id'),
            'market_id': position['market_id'],
            'market': position['market'],
            'resolution': resolution,
            'outcome': outcome,
            'action': 'CLOSE_POSITION'
        }

        if self.nats:
            await self.nats.publish(f"alert.{severity.lower()}", json.dumps(alert_msg).encode())
            await self.nats.publish("position.resolved", json.dumps(alert_msg).encode())

        print(f"[RESOLUTION] Market resolved: {position['market'][:40]}... → {outcome}")

    async def send_expiration_alert(self, position, days_remaining):
        """Alert if market expiring soon"""
        severity = 'HIGH' if days_remaining < 2 else 'MEDIUM'
        alert_msg = {
            'timestamp': datetime.now().isoformat(),
            'type': 'MARKET_EXPIRING',
            'severity': severity,
            'trade_id': position.get('trade_id'),
            'market_id': position['market_id'],
            'market': position['market'],
            'days_remaining': days_remaining,
            'action': 'MONITOR_RESOLUTION'
        }

        if self.nats:
            await self.nats.publish(f"alert.{severity.lower()}", json.dumps(alert_msg).encode())

        # Save alert
        alert_file = Path(__file__).parent.parent / "MONITORING" / "alert_history.jsonl"
        with open(alert_file, 'a') as f:
            f.write(json.dumps(alert_msg) + '\n')

        print(f"[EXPIRATION] {position['market'][:40]}... expires in {days_remaining} days")

    def save_resolution(self, record):
        """Save resolution to history"""
        history = []
        if self.resolution_file.exists():
            try:
                with open(self.resolution_file) as f:
                    history = json.load(f)
            except:
                history = []

        history.append(record)

        with open(self.resolution_file, 'w') as f:
            json.dump(history, f, indent=2)

async def main():
    """Main loop: check resolutions every 5 minutes"""
    from tools.polymarket_client import PolymarketClient

    client = PolymarketClient()
    monitor = ResolutionMonitor(client)

    state_file = Path(__file__).parent.parent / "BRAIN" / "TRADING" / "field_trading_state.json"
    await monitor.load_positions(state_file)

    print("[RESOLUTION MONITOR] Starting resolution monitoring...")

    try:
        while True:
            print(f"[{datetime.now().isoformat()}] Checking resolutions...")
            await monitor.check_resolutions()
            await asyncio.sleep(300)  # Check every 5 minutes

    except KeyboardInterrupt:
        print("[RESOLUTION MONITOR] Shutting down...")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 3. ALERT ENGINE

### Core Logic

```python
import asyncio
import json
from datetime import datetime
from pathlib import Path
from enum import Enum

class AlertSeverity(Enum):
    CRITICAL = "CRITICAL"  # Action required immediately
    HIGH = "HIGH"           # Action required soon
    MEDIUM = "MEDIUM"       # Monitor closely
    LOW = "LOW"             # Informational
    INFO = "INFO"           # Historical

class AlertEngine:
    def __init__(self, nats_client=None):
        self.nats = nats_client
        self.alert_history_file = Path(__file__).parent.parent / "MONITORING" / "alert_history.jsonl"
        self.alert_history_file.parent.mkdir(parents=True, exist_ok=True)
        self.alert_handlers = {
            'CRITICAL': self.handle_critical,
            'HIGH': self.handle_high,
            'MEDIUM': self.handle_medium,
            'LOW': self.handle_low,
            'INFO': self.handle_info
        }

    def get_action_recommendation(self, alert_type, position, severity):
        """Generate action recommendation based on alert type"""
        recommendations = {
            'DRAWDOWN_CRITICAL': {
                'action': 'CLOSE_POSITION',
                'reason': 'Position down >40% - close immediately'
            },
            'DRAWDOWN_HIGH': {
                'action': 'MONITOR_OR_CLOSE',
                'reason': 'Position down 20-40% - evaluate conviction and close if unsure'
            },
            'VOLATILITY_SPIKE': {
                'action': 'MONITOR_CLOSELY',
                'reason': 'High volatility detected - be ready to close if worsens'
            },
            'MARKET_EXPIRING': {
                'action': 'MONITOR_RESOLUTION',
                'reason': 'Market expiring soon - watch for resolution signal'
            },
            'MARKET_RESOLVED': {
                'action': 'CLOSE_POSITION',
                'reason': 'Market resolved - close and record outcome'
            },
            'NEWS_MENTION': {
                'action': 'MONITOR_CLOSELY',
                'reason': 'Market-relevant news detected - evaluate impact'
            }
        }
        return recommendations.get(alert_type, {})

    async def process_alert(self, alert_type, position, severity, data):
        """Main alert processing entry point"""
        alert = {
            'timestamp': datetime.now().isoformat(),
            'type': alert_type,
            'severity': severity,
            'trade_id': position.get('trade_id'),
            'market_id': position.get('market_id'),
            'market': position.get('market'),
            'data': data,
            'action_recommended': self.get_action_recommendation(alert_type, position, severity)
        }

        # Route by severity
        handler = self.alert_handlers.get(severity, self.handle_info)
        await handler(alert)

        # Log all alerts
        self.log_alert(alert)

    async def handle_critical(self, alert):
        """Handle CRITICAL alerts - immediate action required"""
        print(f"\n{'='*60}")
        print(f"🚨 CRITICAL ALERT 🚨")
        print(f"{'='*60}")
        print(f"Market: {alert['market']}")
        print(f"Action: {alert['action_recommended'].get('action')}")
        print(f"Reason: {alert['action_recommended'].get('reason')}")
        print(f"Data: {alert['data']}")
        print(f"{'='*60}\n")

        # Publish to NATS
        if self.nats:
            await self.nats.publish(
                "alert.CRITICAL",
                json.dumps(alert).encode()
            )

        # SMS would go here (requires setup)
        # await self.send_sms(alert)

    async def handle_high(self, alert):
        """Handle HIGH alerts - action required soon"""
        print(f"\n{'─'*60}")
        print(f"⚠️  HIGH ALERT")
        print(f"{'─'*60}")
        print(f"Market: {alert['market']}")
        print(f"Action: {alert['action_recommended'].get('action')}")
        print(f"{'─'*60}\n")

        if self.nats:
            await self.nats.publish(
                "alert.HIGH",
                json.dumps(alert).encode()
            )

    async def handle_medium(self, alert):
        """Handle MEDIUM alerts - monitor closely"""
        if self.nats:
            await self.nats.publish(
                "alert.MEDIUM",
                json.dumps(alert).encode()
            )

    async def handle_low(self, alert):
        """Handle LOW alerts - informational"""
        if self.nats:
            await self.nats.publish(
                "alert.LOW",
                json.dumps(alert).encode()
            )

    async def handle_info(self, alert):
        """Handle INFO alerts - historical logging"""
        # Just log, no special handling
        pass

    def log_alert(self, alert):
        """Log alert to history"""
        try:
            with open(self.alert_history_file, 'a') as f:
                f.write(json.dumps(alert) + '\n')
        except Exception as e:
            print(f"[ERROR] Failed to log alert: {e}")

    def get_recent_alerts(self, limit=20, severity=None):
        """Get recent alerts from history"""
        alerts = []
        try:
            with open(self.alert_history_file, 'r') as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    try:
                        alert = json.loads(line)
                        if severity is None or alert['severity'] == severity:
                            alerts.append(alert)
                    except:
                        pass
        except:
            pass
        return alerts

async def main():
    """Test alert engine"""
    engine = AlertEngine()

    # Test alert
    test_position = {
        'trade_id': '20260204042725_541565',
        'market_id': '541565',
        'market': 'Will Nick Emmanowori be the 2025-2026 NFL Defensive Rookie o'
    }

    # Send test critical alert
    await engine.process_alert(
        'DRAWDOWN_CRITICAL',
        test_position,
        'CRITICAL',
        {'pnl_pct': -0.45}
    )

    # Show recent alerts
    alerts = engine.get_recent_alerts(limit=5)
    print(f"\nRecent alerts: {len(alerts)}")

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 4. INTEGRATION WITH FIELD TRADING DAEMON

### Modifications to `field_trading_daemon.py`

```python
# Add to imports
from position_price_monitor import PositionPriceMonitor
from resolution_status_monitor import ResolutionMonitor
from alert_engine import AlertEngine

# Add to initialization
async def initialize_monitors():
    """Initialize all monitoring systems"""
    price_monitor = PositionPriceMonitor(
        polymarket_client=POLYMARKET_CLIENT,
        nats_client=NATS_CLIENT
    )
    resolution_monitor = ResolutionMonitor(
        polymarket_client=POLYMARKET_CLIENT,
        nats_client=NATS_CLIENT
    )
    alert_engine = AlertEngine(nats_client=NATS_CLIENT)

    # Load positions
    await price_monitor.load_positions(TRADING_STATE_FILE)
    await resolution_monitor.load_positions(TRADING_STATE_FILE)

    return price_monitor, resolution_monitor, alert_engine

# Add to main trading loop
async def trading_cycle():
    """Updated trading cycle with monitoring"""

    # ... existing PERCEIVE logic ...

    # NEW: Monitor position health
    health_snapshot = await price_monitor.update_all_positions()

    # NEW: Check for resolutions
    await resolution_monitor.check_resolutions()

    # NEW: Process any alerts from monitors
    for alert in get_pending_alerts(alert_engine):
        await alert_engine.process_alert(
            alert['type'],
            alert['position'],
            alert['severity'],
            alert['data']
        )

    # ... existing DECIDE logic ...

    # ... existing EXECUTE logic ...

    # Publish health to NATS
    if NATS_CLIENT:
        await NATS_CLIENT.publish(
            'position.health',
            json.dumps(health_snapshot).encode()
        )
```

---

## 5. FILE STRUCTURE

```
/BRAIN/
├── MONITORING/                    (NEW)
│   ├── position_health_state.json
│   ├── alert_history.jsonl
│   └── resolution_history.json
├── CONFIG/                        (NEW)
│   ├── alert_thresholds.json
│   ├── news_keywords.json
│   └── position_monitoring_config.json
└── INTEL/
    ├── EXTERNAL-SIGNAL-INTEGRATION.md
    └── SIGNAL-INTEGRATION-IMPLEMENTATION.md

/tools/
├── position_price_monitor.py      (NEW)
├── resolution_status_monitor.py   (NEW)
├── news_event_monitor.py          (NEW)
├── volatility_monitor.py          (NEW)
├── alert_engine.py                (NEW)
└── position_health_dashboard.py   (NEW)
```

---

## 6. DEPLOYMENT CHECKLIST

- [ ] Create all new monitor files
- [ ] Test price monitor with 7 positions
- [ ] Verify prices update every 30s
- [ ] Test resolution monitor with mock data
- [ ] Test alert engine with test alerts
- [ ] Integrate monitors with field_trading_daemon
- [ ] Deploy and monitor for 24 hours
- [ ] Collect metrics on alert accuracy
- [ ] Iterate based on feedback

---

## Summary

This implementation adds real-time monitoring without changing the trading logic. It runs in parallel, collecting signals, checking thresholds, and alerting when action is needed.

**Key files to create:**
1. `position_price_monitor.py` - Real-time price tracking
2. `resolution_status_monitor.py` - Resolution checking
3. `alert_engine.py` - Unified alert routing
4. Integrate with existing daemon

**Result:** No more blind positions. Every signal received.

