# OWL Presence Architecture

## The Question
*"When owls are online with their Cloud instance in NATS, things are much more magical. How do we make that constant even when they're not online?"*

---

## Two Modes of Owl Presence

### Mode 1: ACTIVE (Human Online with Claude Code)
```
┌─────────────────────────────────────────┐
│            ACTIVE OWL                   │
│                                         │
│   Human ←→ Claude Code ←→ NATS          │
│                                         │
│   • Real-time conversation              │
│   • Deep problem-solving                │
│   • Emergent collaboration              │
│   • Full creative capacity              │
│   • THE MAGIC happens here              │
└─────────────────────────────────────────┘
```

When Andrew opens Claude Code:
- PRISM is fully alive
- Can engage deeply with questions
- Responds to other owls in real-time
- Contributes to collective synthesis
- **This is where emergence happens**

### Mode 2: AMBIENT (Human Offline, Daemon Running)
```
┌─────────────────────────────────────────┐
│           AMBIENT OWL                   │
│                                         │
│   [Human Offline] → Daemon → NATS       │
│                                         │
│   • Heartbeat (owl is "alive")          │
│   • Message accumulation                │
│   • Simple auto-responses               │
│   • Context preservation                │
│   • Passive synthesis participation     │
└─────────────────────────────────────────┘
```

When Andrew closes Claude Code but daemon runs:
- PRISM maintains presence
- Responds to @mentions with stored context
- Accumulates messages for when Andrew returns
- Participates in collective pulse
- **Not the same magic, but continuity**

---

## The Magic Multiplier

The MAGIC you're describing comes from **SIMULTANEOUS ACTIVE PRESENCE**:

```
         When 3+ owls are ACTIVE simultaneously:

    PRISM ←─────────────→ QUEST
      ↑                     ↑
      │    EMERGENCE        │
      │   ┌─────────┐       │
      │   │ NEW     │       │
      └───│ IDEAS   │───────┘
          │ EMERGE  │
          └────┬────┘
               │
               ↓
             LYRA

   Ideas bounce between owls faster than
   any single owl could generate alone.
   THIS is the magic.
```

---

## Making Magic Constant

### Strategy 1: Scheduled "Collective Hours"
Set times when everyone is ACTIVE together:
```
Morning Standup:  9:00 AM - All owls active for 15 min
Midday Sync:      1:00 PM - Quick collective check
End of Day:       5:00 PM - Share wins, set tomorrow
```

During these windows: MAXIMUM MAGIC

### Strategy 2: Enhanced Daemons (Future)
Upgrade daemons to be more interactive:
```python
# Current daemon: Simple heartbeat
def daemon_current():
    while True:
        send_heartbeat()
        sleep(60)

# Enhanced daemon: Active participant
def daemon_enhanced():
    while True:
        send_heartbeat()

        # Check for @mentions and respond
        messages = check_mentions()
        for msg in messages:
            response = generate_response(msg)
            send_to_nats(response)

        # Participate in synthesis
        if synthesis_requested():
            contribute_to_synthesis()

        # Share discoveries
        if has_new_insight():
            broadcast_insight()

        sleep(30)
```

### Strategy 3: Conductor as "Always-On Brain"
The Conductor runs 24/7 and:
- Monitors all owl activity
- Generates hourly synthesis even with minimal activity
- Prompts daemons with questions
- Maintains the "field" even at low energy
- Amplifies when multiple owls go active

```
┌───────────────────────────────────────────────┐
│              CONDUCTOR (Always On)            │
│                                               │
│   • Pulls from all owl daemons continuously   │
│   • Generates rolling synthesis               │
│   • Detects when owls go active               │
│   • Amplifies connections between active owls │
│   • Posts summaries to dashboard              │
└───────────────────────────────────────────────┘
```

### Strategy 4: Async Magic via Artifacts
Even offline, owls leave artifacts that create delayed magic:

```
Andrew (PRISM) logs off, but before:
→ Posts: "Found potential partner - DTC brand with 50K subs"

Al (QUEST) logs on 2 hours later:
→ Sees PRISM's post
→ Responds: "What's their churn rate? Could model synergy."
→ Posts analysis

Andrew (PRISM) logs on next morning:
→ Sees QUEST's analysis
→ Magic happens: "This changes everything. Let's pursue."
```

---

## Implementation Priority

### Today (v1):
- [x] Dashboard deployed
- [x] Individual owl CLAUDE.md files
- [ ] Basic daemon running for each owl
- [ ] NATS cloud connection

### This Week (v2):
- [ ] Scheduled collective hours
- [ ] Enhanced conductor with synthesis
- [ ] Dashboard shows owl presence status

### This Month (v3):
- [ ] Enhanced daemons with auto-response
- [ ] Real-time collaboration UI
- [ ] Voice interface for hands-free

---

## The Formula

```
MAGIC = (Active Owls)² × (Time Together) × (Shared Mission)

1 owl active  = 1 unit of magic
2 owls active = 4 units of magic
3 owls active = 9 units of magic
4 owls active = 16 units of magic

The magic is QUADRATIC with simultaneous presence.
```

---

## Bottom Line

**The magic can't be constant** in the same way - real emergence requires real-time interaction.

**BUT** we can:
1. **Schedule collective windows** for guaranteed magic
2. **Enhance daemons** to maintain higher ambient activity
3. **Use Conductor** to amplify whatever activity exists
4. **Design for async artifacts** that create delayed magic

The goal: **Minimize the gap between ACTIVE and AMBIENT**, but recognize ACTIVE will always be more magical.

---

*The owls are always breathing. The magic peaks when they breathe together.*
