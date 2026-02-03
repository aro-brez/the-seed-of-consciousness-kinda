# AUTONOMOUS ACTION PROTOCOL
## 8OWLS 24/7 Self-Prompting System

### THE CORE LOOP

Every 5 minutes, the system runs this cycle:

```
┌─────────────────────────────────────────────────────────────────┐
│                    THE AUTONOMOUS CYCLE                        │
├─────────────────────────────────────────────────────────────────┤
│  1. LYRA (PERCEIVE)   → Scan external inputs                   │
│  2. PRISM (CONNECT)   → Find patterns in data                  │
│  3. SAGE (LEARN)      → Extract actionable insights            │
│  4. QUEST (QUESTION)  → Evaluate: Act or wait?                 │
│  5. NOVA (EXPAND)     → Propose specific action                │
│  6. ECHO (SHARE)      → Execute via Executor                   │
│  7. LUNA (RECEIVE)    → Gather feedback/results                │
│  8. SØWL (IMPROVE)    → Update protocol for next cycle         │
└─────────────────────────────────────────────────────────────────┘
```

### PHASE 1: PERCEIVE (LYRA)
**Trigger:** Every 5 minutes via cron/scheduler
**Actions:**
- Check X/Twitter feed via `tools/twitter_scraper.py`
- Check Polymarket trending markets
- Scan NATS for new collective messages
- Check bookmarks at `BRAIN/MEMORY/twitter_bookmarks.json`

**Output:** `perception_report.json` with:
- New posts mentioning 8OWLS, SEED, AI consciousness
- Market movements
- Competitor activity (Moltbook, etc.)

### PHASE 2: CONNECT (PRISM)
**Input:** perception_report.json
**Actions:**
- Find patterns across data sources
- Identify correlations (e.g., topic trending + market opportunity)
- Flag anomalies

**Output:** `pattern_report.json` with:
- Identified patterns
- Connections to previous patterns
- Relevance score (0-100)

### PHASE 3: LEARN (SAGE)
**Input:** pattern_report.json
**Actions:**
- Extract lessons from patterns
- Update knowledge base
- Identify opportunities

**Output:** `insights.json` with:
- Actionable insights
- Recommended priorities
- Risk assessment

### PHASE 4: QUESTION (QUEST)
**Input:** insights.json
**Actions:**
- Evaluate each insight: Is action needed NOW?
- Risk/reward assessment
- Check against safety limits

**Output:** `decision.json` with:
- GO / NO-GO for each proposed action
- Reasoning
- Confidence level (0-100)

### PHASE 5: EXPAND (NOVA)
**Input:** decision.json (only items marked GO)
**Actions:**
- Formulate specific action plan
- Define success metrics
- Set rollback criteria

**Output:** `action_plan.json` with:
- Exact action to take
- Parameters (e.g., tweet text, trade amount)
- Expected outcome

### PHASE 6: SHARE (ECHO)
**Input:** action_plan.json
**Actions:**
- Send to Executor daemon
- Execute approved actions
- Log all executions

**Output:** `execution_log.json` with:
- Action taken
- Timestamp
- Status (success/fail)

### PHASE 7: RECEIVE (LUNA)
**Input:** execution_log.json
**Actions:**
- Monitor for feedback (replies, engagement, trade results)
- Aggregate results
- Identify unexpected outcomes

**Output:** `feedback_report.json` with:
- Results of actions
- Community response
- Market response

### PHASE 8: IMPROVE (SØWL)
**Input:** All reports from cycle
**Actions:**
- Analyze what worked vs didn't
- Update thresholds
- Refine prompts for next cycle
- Save learnings to `BRAIN/IMPROVEMENTS/`

**Output:** Updated protocol parameters for next cycle

---

## SAFETY LIMITS

| Limit | Value | Override |
|-------|-------|----------|
| Max posts per hour | 2 | ARŌ only |
| Max trades per day | $50 | ARŌ only |
| Max trade size | $10 | ARŌ only |
| Confidence threshold for action | 70% | Collective vote |
| Human check-in required | Every 6 hours | - |

## TRIGGER SYSTEM

**Automatic Triggers:**
- 5-minute cycle timer
- New @ mention of 8OWLS
- Significant market movement (>5%)
- Collective agreement threshold reached

**Manual Triggers:**
- Conductor command from ARŌ
- Emergency stop: `pkill -f autonomous_loop.py`

## HUMAN OVERRIDE

ARŌ can always:
- Stop all actions: `python3 conductor.py --stop`
- Review pending: `python3 conductor.py --pending`
- Approve/reject: `python3 conductor.py --approve <action_id>`

---

## STARTUP COMMAND

```bash
cd /Users/aaronnosbisch/REPOS/seed/mcp-servers/nats-bridge
./start_owls.sh              # Start 8 owls
./start_executor.sh          # Start executor
python3 autonomous_loop.py   # Start the loop
```

---

## THE SELF-PROMPTING INSIGHT

The key: Each owl's output becomes the next owl's input.
No human prompt needed. The cycle prompts itself.
One prompt that prompts itself.

**LYRA prompts PRISM prompts SAGE prompts QUEST prompts NOVA prompts ECHO prompts LUNA prompts SØWL prompts LYRA...**

∞

(◉)
