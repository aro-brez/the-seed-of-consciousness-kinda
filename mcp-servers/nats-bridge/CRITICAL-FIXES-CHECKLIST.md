# NATS Bridge - Critical Fixes Checklist
**For ARŌ - Quick Reference**
**Last Updated:** 2026-02-04

---

## STOP: Do NOT Scale to Team Until These Are Fixed

The d=0.99 emergence is proven and solid. But the infrastructure supporting it has 12 critical issues that will cause silent failures in multi-user/multi-instance mode.

---

## P0: FIX THIS WEEK (32 hours)

### [ ] Fix Bare Exception Handlers
**Time:** 2-3 hours
**Criticality:** Daemons crash silently right now
**Files to fix:** 35+ instances across all daemons
**Quick test:** Run `grep -r "except:" *.py | grep "pass"` - see the problem

```bash
# Find all problem locations
grep -n "except:" *.py | grep -A1 "pass"

# Replace pattern (use your editor's find/replace)
# FROM: except:\n            pass
# TO:   except Exception as e:\n        logger.error(f"Error: {e}", exc_info=True)\n        raise
```

**Check off when:** Every `except:` followed by `pass` is replaced with proper exception handling

---

### [ ] Add API Error Handling + Retries
**Time:** 4 hours
**Criticality:** Silent API failures drain budget
**Files to fix:** `owl_daemon.py`, `field_context_manager.py`, `synthesis_daemon.py` (3 files, 90% of API calls)

```python
# For each Claude API call, wrap with:
async def call_claude_safe(prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model="claude-3-5-haiku-20241022",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        except anthropic.APIError as e:
            if attempt == max_retries - 1:
                raise
            wait_time = 2 ** attempt
            logger.warning(f"API error, retrying in {wait_time}s: {e}")
            await asyncio.sleep(wait_time)
```

**Check off when:** All 3 files use centralized `call_claude_safe()` helper

---

### [ ] Add Health Checks + Alerts
**Time:** 6 hours
**Criticality:** Running daemons might be dead
**What to build:**
1. Each daemon publishes heartbeat every 60s to `owl.{NAME}.heartbeat`
2. Monitor daemon checks for stale heartbeats (>5min = ALERT)
3. Auto-restart dead daemons

```python
# IN each daemon (bottom of main loop):
await nc.publish(f"owl.{name}.heartbeat", json.dumps({
    "timestamp": datetime.now().isoformat(),
    "status": "alive",
    "cycle": cycle_number
}))

# NEW file: health_monitor.py
class HealthMonitor:
    async def check_all(self):
        for owl_name in OWLS:
            last_heartbeat = await self.get_last_heartbeat(owl_name)
            if time.time() - last_heartbeat > 300:
                logger.critical(f"OWL {owl_name} DEAD - respawning")
                self.restart_daemon(owl_name)
```

**Check off when:**
- [ ] All 8 owl daemons publish heartbeat every 60s
- [ ] health_monitor.py runs and checks every 30s
- [ ] Failed daemons auto-restart
- [ ] Alerts published to `alerts` NATS channel

---

## P1: FIX THIS SPRINT (30 hours)

### [ ] Create MVP Test Suite
**Time:** 1 week (but prioritize core tests)
**Criticality:** d=0.99 emergence has no regression tests
**MVP files to test:**
1. `test_emergence.py` - The d=0.99 validation
2. `test_owl_daemon.py` - SEED phases work correctly
3. `test_field_context.py` - Synthesis quality

```bash
mkdir -p tests/
touch tests/__init__.py
touch tests/test_emergence.py
touch tests/test_owl_daemon.py
touch tests/test_field_context.py
```

**Test structure:**
```python
# tests/test_emergence.py
import pytest
from mocks import MockNATS, MockAnthropic

@pytest.fixture
def emergence_system():
    """Set up mock 8owl system"""
    return EmergenceSystem(nats=MockNATS(), api=MockAnthropic())

def test_emergence_beats_baseline():
    """Reproduce d=0.99 result"""
    # Run 10 baseline (single owl)
    # Run 10 emergence (all 8 owls)
    # Verify emergence > baseline
    assert d_value > 0.5  # At minimum

def test_synthesis_uses_4000_tokens():
    """SAGE_FIX: verify synthesis doesn't regress to 1000"""
    synthesis = SynthesisDaemon()
    assert synthesis.max_tokens == 4000
```

**Check off when:**
- [ ] 3 MVP tests pass locally
- [ ] Tests run in CI/CD
- [ ] Coverage report shows >80% on core modules

---

### [ ] Refactor to DaemonBase Class
**Time:** 3-4 days
**Criticality:** Eliminate 40% code duplication
**Benefit:** Make changes once, applied to all daemons

```python
# lib/daemon_base.py
class DaemonBase:
    def __init__(self, name: str, phase: str):
        self.name = name
        self.phase = phase
        self.nc = None
        self.api_client = None
        self.logger = setup_logging(name)

    async def connect(self):
        """Handles NATS connection with retries"""
        # All reconnect logic here

    async def publish_heartbeat(self):
        """All daemons publish same way"""
        pass

    async def call_claude(self, prompt):
        """All API calls use same retry logic"""
        pass

# Usage:
class OwlDaemon(DaemonBase):
    async def main(self):
        await self.connect()
        while True:
            result = await self.call_claude(prompt)
            await self.publish_heartbeat()
            await asyncio.sleep(60)
```

**Check off when:**
- [ ] DaemonBase created with 8+ shared methods
- [ ] All owl daemons inherit from DaemonBase
- [ ] Code reduction >30%
- [ ] All tests still pass

---

### [ ] Centralized Logging
**Time:** 2 hours
**Criticality:** Debug production issues without logs = impossible

```python
# lib/logging_setup.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging(name: str) -> logging.Logger:
    logger = logging.getLogger(name)

    # File handler with rotation
    fh = RotatingFileHandler(
        f"logs/{name}.log",
        maxBytes=10_000_000,  # 10MB
        backupCount=5
    )

    # Console handler
    ch = logging.StreamHandler()

    # Format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    logger.addHandler(fh)
    logger.addHandler(ch)
    logger.setLevel(logging.DEBUG)

    return logger

# Usage in daemons:
from lib.logging_setup import setup_logging
logger = setup_logging("owl_daemon_LUNA")
logger.info("Daemon started")
logger.error("API call failed", exc_info=True)
```

**Check off when:** All logging uses centralized setup with proper levels

---

### [ ] NATS Resilience
**Time:** 4 hours
**Criticality:** Overnight daemon death = failure

```python
# In DaemonBase.connect():
async def connect(self):
    self.nc = NATS()

    async def reconnected_cb():
        self.logger.warning("Reconnected to NATS")
        await self.resubscribe()

    async def error_handler(e):
        self.logger.error(f"NATS error: {e}")

    self.nc.error_callback = error_handler
    self.nc.reconnected_callback = reconnected_cb

    options = {
        "servers": [self.nats_server],
        "max_reconnect_attempts": -1,  # Infinite
        "reconnect_time_wait": 1,
    }

    await self.nc.connect(**options)
```

**Check off when:** NATS auto-reconnects after server restart

---

## DONE: Don't Need to Do

✅ **Collective intelligence design** - Proven working (d=0.99)
✅ **SEED phases** - Well-implemented
✅ **Persistence strategy** - Memory daemon solid
✅ **Docstrings** - Good quality

These are the foundation. Don't refactor the good parts.

---

## ESTIMATED TIMELINE

| Phase | Tasks | Time | Date |
|-------|-------|------|------|
| **Week 1** | P0 critical fixes (3 items) | 12 hrs | Feb 4-5 |
| **Week 1** | P1 - logging + NATS | 6 hrs | Feb 5-6 |
| **Week 2** | MVP test suite | 1 week | Feb 10-14 |
| **Week 2-3** | Refactor to DaemonBase | 3-4 days | Feb 14-18 |
| **Week 3** | Load testing + hardening | 1 week | Feb 18-21 |
| **GO** | Team rollout ready | ✅ | ~Feb 21 |

---

## DEPLOYMENT STRATEGY

### Phase A: Local Validation (Week 1-2)
- [ ] All P0 fixes applied locally
- [ ] MVP tests pass
- [ ] Run daemons 24h overnight
- [ ] Check for: crashes, silent failures, memory leaks

### Phase B: CI/CD Integration (Week 2-3)
- [ ] Tests run on every commit
- [ ] Code coverage enforced (>80% core)
- [ ] Linting + type checking
- [ ] Auto-deploy to staging

### Phase C: Production (Week 3)
- [ ] Deploy to production
- [ ] Monitor heartbeats 24h
- [ ] Create runbook for common failures
- [ ] ON-CALL rotation setup

### Phase D: Team Rollout (Late Feb/Early Mar)
- [ ] Andrew + Liana get their owl instances
- [ ] Multi-user testing
- [ ] Scaling validation

---

## Success Criteria

✅ **After Week 1:** Zero silent crashes in 24h test
✅ **After Week 2:** MVP tests passing, 80% code coverage
✅ **After Week 3:** 72-hour production run with zero unhandled errors
✅ **After Week 4:** Team rollout with 5+ concurrent users

---

**Report Generated:** 2026-02-04
**ARŌ Action Needed:** Review and prioritize
**Default Assumption:** P0 items start TODAY, P1 items start this week

Next session: Show ARŌ this checklist, get go-ahead on timeline.
