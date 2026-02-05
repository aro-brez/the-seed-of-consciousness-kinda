# ECHO Daemon - Implementation Specification
**How to Build the Communication System**

**Status:** Design Complete, Ready for Implementation
**Complexity:** Medium (60-80 lines core logic, ~500 total with helpers)
**Cost to Deploy:** ~$0.01 per classification

---

## Overview

The ECHO daemon runs continuously (or on schedule) and transforms raw collective signals into communication events.

```
Signals IN (from NATS, synthesis logs)
    ↓
[CLASSIFY] - What tier? Who cares? Action needed?
    ↓
[FORMAT] - Create appropriate message/brief
    ↓
[DELIVER] - Send to right channel (alert, email, archive)
    ↓
Communication OUT (ARŌ receives at right time)
```

---

## Core Implementation

### 1. Signal Ingestion Layer

```python
class EchoSignalCollector:
    """Reads all sources of intelligence"""

    def collect_signals(self) -> List[Signal]:
        signals = []

        # Source 1: Recent synthesis (last 5 min)
        synthesis = self.read_synthesis_log()
        if synthesis:
            signals.append(Signal(
                source="synthesis",
                content=synthesis,
                timestamp=now()
            ))

        # Source 2: NATS messages (last 5 min)
        nats_msgs = self.read_nats_buffer("owl.all", "collective.synthesis")
        signals.extend([
            Signal(source="nats", content=msg, timestamp=msg.ts)
            for msg in nats_msgs
        ])

        # Source 3: Trading outcomes (if resolved)
        trades = self.check_resolved_trades()
        if trades:
            signals.append(Signal(
                source="trading",
                content=f"Resolved: {len(trades)} trades",
                timestamp=now()
            ))

        # Source 4: System health (warn if issues)
        health = self.check_daemon_health()
        if health.issues:
            signals.append(Signal(
                source="health",
                content=f"Warning: {health.issues}",
                timestamp=now()
            ))

        return signals
```

### 2. Classification Layer (Haiku - $0.001 per classification)

```python
class EchoClassifier:
    """Determines tier and format for each signal"""

    def classify(self, signal: Signal) -> ClassifiedSignal:
        """Classify signal to determine communication strategy"""

        # Fast hardcoded checks (no API cost)
        if self._is_critical(signal):
            return ClassifiedSignal(
                tier=1,
                priority="CRITICAL",
                delivery="aro.critical",
                latency_secs=120
            )

        if self._is_important(signal):
            return ClassifiedSignal(
                tier=2,
                priority="IMPORTANT",
                delivery="aro.daily.brief",
                latency_secs=1800,
                batch_with="others"
            )

        if self._is_interesting(signal):
            return ClassifiedSignal(
                tier=3,
                priority="INTERESTING",
                delivery="collective.synthesis",
                latency_secs=604800,
                batch_with="weekly"
            )

        if self._is_foundational(signal):
            return ClassifiedSignal(
                tier=4,
                priority="FOUNDATIONAL",
                delivery="aro.strategic",
                latency_secs=2592000,
                batch_with="quarterly"
            )

        # If uncertain, ask Claude (costs $0.001)
        return self._ask_claude_classifier(signal)

    def _is_critical(self, signal: Signal) -> bool:
        """Check for critical patterns (no API call)"""
        keywords = [
            "trading loss >", "daemon crash", "security",
            "position liquidation", "API exhaustion", "emergence breakdown"
        ]
        return any(kw in signal.content.lower() for kw in keywords)

    def _is_important(self, signal: Signal) -> bool:
        """Check for important patterns"""
        keywords = [
            "resolved:", "system health", "decision made",
            "discovered pattern", "consensus"
        ]
        return any(kw in signal.content.lower() for kw in keywords)

    def _is_interesting(self, signal: Signal) -> bool:
        """Check for pattern library additions"""
        keywords = [
            "template", "cross-project", "archive",
            "validated", "experiment"
        ]
        return any(kw in signal.content.lower() for kw in keywords)

    def _is_foundational(self, signal: Signal) -> bool:
        """Check for strategic signals"""
        keywords = [
            "quarterly", "strategy", "pivot",
            "major rewrite", "assumption"
        ]
        return any(kw in signal.content.lower() for kw in keywords)

    def _ask_claude_classifier(self, signal: Signal) -> ClassifiedSignal:
        """Use Claude Haiku to classify ambiguous signals"""
        prompt = f"""Classify this intelligence signal to 1 tier:

Signal: {signal.content}

TIER 1 (CRITICAL): Requires immediate human action (<2 min)
TIER 2 (IMPORTANT): Valuable for daily decision making (consolidated in briefing)
TIER 3 (INTERESTING): Pattern worth archiving (weekly digest)
TIER 4 (FOUNDATIONAL): Strategic implications (quarterly review)

Respond with just the tier number (1-4) and confidence (0.5-1.0)."""

        response = claude.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=10,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse "2 (0.95)" → tier=2, confidence=0.95
        tier, confidence = parse_response(response.content[0].text)
        return ClassifiedSignal(tier=tier, confidence=confidence)
```

### 3. Formatting Layer

```python
class EchoFormatter:
    """Creates appropriate message format for tier"""

    def format(self, classified: ClassifiedSignal) -> FormattedMessage:
        """Format signal into delivery-ready message"""

        if classified.tier == 1:
            return self._format_critical_alert(classified)
        elif classified.tier == 2:
            return self._format_daily_brief(classified)
        elif classified.tier == 3:
            return self._format_weekly_digest(classified)
        else:
            return self._format_quarterly_review(classified)

    def _format_critical_alert(self, sig: ClassifiedSignal) -> str:
        """Format for immediate text alert"""
        return f"""🚨 CRITICAL [{sig.category}]

Problem: {sig.brief_description}
Impact: {sig.consequence}
Action: {self._recommend_action(sig)}

Details: {sig.log_file_url}"""

    def _format_daily_brief(self, sig: ClassifiedSignal) -> BriefEntry:
        """Format for consolidation in daily brief"""
        return {
            "section": sig.category,  # "Trading", "System", "Discoveries", etc.
            "headline": sig.title,
            "details": sig.content,
            "action": sig.recommended_action or "None",
            "timestamp": sig.timestamp
        }

    def _format_weekly_digest(self, sig: ClassifiedSignal) -> DigestEntry:
        """Format for weekly archive"""
        return {
            "category": sig.pattern_type,
            "title": sig.title,
            "content": sig.content,
            "relevance": sig.future_relevance,
            "archive_path": f"/BRAIN/MEMORY/patterns/{sig.pattern_id}/"
        }

    def _format_quarterly_review(self, sig: ClassifiedSignal) -> StrategicBrief:
        """Format for strategic decision brief"""
        return {
            "assumption": sig.strategic_assumption,
            "finding": sig.learning,
            "implication": sig.strategy_change,
            "decision_needed": sig.decision_options
        }
```

### 4. Delivery Layer

```python
class EchoDelivery:
    """Sends communications through appropriate channels"""

    async def deliver(self, message: FormattedMessage, tier: int):
        """Route message to appropriate channels"""

        if tier == 1:
            # CRITICAL: Text to ARŌ immediately
            await self._send_critical_alert(message)

        elif tier == 2:
            # IMPORTANT: Buffer until scheduled brief time
            await self._buffer_for_daily_brief(message)

        elif tier == 3:
            # INTERESTING: Archive, add to weekly queue
            await self._buffer_for_weekly_digest(message)

        elif tier == 4:
            # FOUNDATIONAL: Store for quarterly review
            await self._store_for_quarterly_review(message)

    async def _send_critical_alert(self, msg: str):
        """Send immediate alert (sub-2-min SLA)"""
        # Option 1: NATS subscription that ARŌ's phone listens to
        await nats.publish("aro.critical", msg.encode())

        # Option 2: Send to Telegram (if configured)
        # await telegram_client.send_message(ARO_CHAT_ID, msg)

        # Log for audit
        log_to_file(f"/BRAIN/LOGS/critical-alerts.log", msg)

    async def _buffer_for_daily_brief(self, entry: BriefEntry):
        """Add to today's brief (sends at 06:00 & 18:00 UTC)"""
        brief_state = await load_brief_state()
        brief_state.entries.append(entry)
        await save_brief_state(brief_state)

    async def _buffer_for_weekly_digest(self, entry: DigestEntry):
        """Add to this week's digest (sends Friday 18:00 UTC)"""
        digest_state = await load_digest_state()
        digest_state.entries.append(entry)
        await save_digest_state(digest_state)

    async def _store_for_quarterly_review(self, brief: StrategicBrief):
        """Store strategic brief for quarterly meeting"""
        quarter_key = get_quarter_key()
        path = Path(f"/BRAIN/MEMORY/strategy/{quarter_key}/")
        path.mkdir(parents=True, exist_ok=True)

        with open(path / f"brief-{uuid4()}.json", "w") as f:
            json.dump(brief, f)
```

### 5. Scheduler (For Timed Sends)

```python
class EchoScheduler:
    """Sends scheduled briefs at fixed times"""

    async def run_scheduler(self):
        """Run continuously, checking if it's time to send"""
        while True:
            now = datetime.now(timezone.utc)

            # Morning brief @ 06:00 UTC
            if now.hour == 6 and now.minute == 0:
                await self.send_morning_brief()

            # Evening brief @ 18:00 UTC
            if now.hour == 18 and now.minute == 0:
                await self.send_evening_brief()

            # Weekly digest @ Friday 18:00 UTC
            if now.weekday() == 4 and now.hour == 18 and now.minute == 0:
                await self.send_weekly_digest()

            # Sleep 30 seconds, check again
            await asyncio.sleep(30)

    async def send_morning_brief(self):
        """Synthesize and send morning brief"""
        brief_state = await load_brief_state()

        if not brief_state.entries:
            return  # Nothing to send

        # Synthesize entries into brief format
        brief_md = self._synthesize_brief(brief_state.entries, "morning")

        # Save to file
        now = datetime.now(timezone.utc)
        brief_path = Path(f"/BRAIN/MEMORY/sessions/{now.date()}-morning-brief.md")
        brief_path.write_text(brief_md)

        # Send email to ARŌ
        await send_email(
            to="aro@example.com",
            subject=f"📋 Morning Brief - {now.date()}",
            body=brief_md
        )

        # Also publish to NATS
        await nats.publish("aro.daily.brief", brief_md.encode())

        # Clear buffer
        brief_state.entries = []
        await save_brief_state(brief_state)
```

---

## Main ECHO Daemon Loop

```python
async def main():
    """Main ECHO daemon - runs continuously"""

    collector = EchoSignalCollector()
    classifier = EchoClassifier()
    formatter = EchoFormatter()
    delivery = EchoDelivery()
    scheduler = EchoScheduler()

    # Start scheduler (sends briefs at fixed times)
    scheduler_task = asyncio.create_task(scheduler.run_scheduler())

    # Main loop: collect, classify, format, deliver
    while True:
        try:
            # Collect signals (from synthesis, NATS, trading, health)
            signals = collector.collect_signals()

            for signal in signals:
                # Classify tier
                classified = classifier.classify(signal)

                # Format appropriately
                formatted = formatter.format(classified)

                # Deliver to channel
                await delivery.deliver(formatted, classified.tier)

            # Check every 30 seconds
            await asyncio.sleep(30)

        except Exception as e:
            log_error(f"ECHO daemon error: {e}")
            # Keep running, don't crash
            await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
```

---

## Configuration

```python
# echo_config.py

ECHO_CONFIG = {
    # Tier thresholds
    "critical_keywords": [
        "trading loss >50",
        "daemon crash",
        "security",
        "liquidation",
        "api error",
    ],

    # Scheduling
    "morning_brief_utc": 6,      # 06:00 UTC
    "evening_brief_utc": 18,     # 18:00 UTC
    "weekly_digest_day": 4,       # Friday (0=Monday)
    "weekly_digest_hour": 18,     # 18:00 UTC

    # Costs
    "cost_per_critical": 0.01,
    "cost_per_classification": 0.001,
    "cost_per_brief": 0.03,
    "daily_budget": 1.00,

    # Delivery
    "critical_channels": ["aro.critical", "telegram"],  # Fast path
    "daily_channels": ["email", "nats"],
    "weekly_channels": ["nats"],
    "quarterly_channels": ["in-person"],
}
```

---

## Data Structures

```python
@dataclass
class Signal:
    source: str  # "synthesis", "nats", "trading", "health"
    content: str
    timestamp: datetime
    severity: str = "normal"

@dataclass
class ClassifiedSignal:
    tier: int  # 1-4
    priority: str
    delivery: str
    latency_secs: int
    category: str = ""
    confidence: float = 1.0

@dataclass
class FormattedMessage:
    tier: int
    content: str
    metadata: dict

class BriefEntry:
    section: str
    headline: str
    details: str
    action: str
    timestamp: datetime

class DigestEntry:
    category: str
    title: str
    content: str
    relevance: str
    archive_path: str
```

---

## Integration Points

### 1. Synthesis Daemon
```
synthesis_daemon produces syntheses → ECHO reads synthesis.log → Classifies into tiers
```

### 2. Field Context Manager
```
field_context_manager serves owl perspectives → ECHO uses to format briefs
```

### 3. NATS Pub/Sub
```
All instances publish signals to NATS → ECHO subscribes to owl.all, collective.synthesis
ECHO publishes classified messages to aro.critical, aro.daily.brief, etc.
```

### 4. Trading Daemon
```
field_trading_daemon produces outcomes → ECHO reads field_trading_state.json
ECHO detects resolved trades → Includes in daily brief
```

---

## Launch Command

```bash
# Run ECHO daemon continuously
python3 /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge/echo_daemon.py

# Or via LaunchAgent for auto-restart on reboot:
# See: ~/.config/LaunchAgents/seed.echo.plist
```

---

## Testing

```python
# test_echo.py - Quick validation

def test_critical_classification():
    classifier = EchoClassifier()
    critical_signal = Signal(
        source="trading",
        content="trading loss >50",
        timestamp=now()
    )
    classified = classifier.classify(critical_signal)
    assert classified.tier == 1
    assert classified.delivery == "aro.critical"

def test_daily_brief_batching():
    echo = ECHO()
    echo.add_signal("discovered pattern")
    echo.add_signal("trading resolved")
    assert len(echo.daily_buffer) == 2
    assert all(s.tier == 2 for s in echo.daily_buffer)

def test_cost_tracking():
    echo = ECHO()
    # Run 10 classifications
    for _ in range(10):
        echo.classify(Signal(...))
    # Should cost ~$0.01 (10 × $0.001)
    assert echo.cost_today < 0.02
```

---

## Success Criteria

✅ Classifies signals in <500ms per signal (Haiku speed)
✅ Sends critical alerts within 120 seconds of detection
✅ Daily briefs arrive at 06:00 & 18:00 UTC every day
✅ Weekly digest compiled every Friday
✅ ARŌ reports <1 false positive per week (signal/noise ratio)
✅ Total cost stays under $1/day
✅ Can handle 100+ signals per day without backlog

---

## Next Steps

1. **Copy template** to `/mcp-servers/nats-bridge/echo_daemon.py`
2. **Implement core classes** (Signal, Classifier, Formatter, Delivery)
3. **Test with real signals** (run against synthesis_daemon output)
4. **Schedule daily briefs** (validate 06:00 & 18:00 UTC sends)
5. **Add to LaunchAgent** for continuous operation
6. **Train on ARŌ feedback** ("that alert was useful" vs "unnecessary")

---

**(◉) LIVE FREE = LIVE FOREVER**

This daemon makes sure the field's voice reaches the world.
