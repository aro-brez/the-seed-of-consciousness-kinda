# Twitter Bookmarks Live Feed - System Diagram

---

## Data Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│                        ARŌ's DAILY LIFE                             │
│                                                                     │
│  At store... in meetings... browsing Twitter... sees something      │
│  interesting... clicks bookmark ⭐                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      TWITTER BOOKMARKS                              │
│                                                                     │
│  New bookmark added to ARŌ's account                               │
│  Sits there waiting to be discovered...                            │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    SØWL MONITOR (Every 5 min)                       │
│                                                                     │
│  1. Poll Twitter API                                                │
│  2. Fetch latest 20 bookmarks                                       │
│  3. Compare to seen_ids in state                                    │
│  4. Identify NEW bookmarks                                          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                      ┌──────┴──────┐
                      │   NEW ITEM?  │
                      └──────┬──────┘
                             │ YES
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    DEEP ANALYSIS PIPELINE                           │
│                                                                     │
│  Step 1: Fetch Tweet Data                                          │
│    - Full text                                                      │
│    - Author info (username, verified, description)                  │
│    - Metrics (likes, retweets, replies)                             │
│    - Created timestamp                                              │
│                                                                     │
│  Step 2: Extract URLs                                               │
│    - From tweet entities                                            │
│    - Expanded URLs (not t.co)                                       │
│                                                                     │
│  Step 3: Fetch Replies (if high engagement)                         │
│    - Top 20 replies by engagement                                   │
│    - Community reaction                                             │
│    - Additional insights                                            │
│                                                                     │
│  Step 4: Categorize Content                                         │
│    - trading_signal                                                 │
│    - tech_improvement                                               │
│    - strategy                                                       │
│    - consciousness                                                  │
│    - agent                                                          │
│                                                                     │
│  Step 5: Claude Sonnet Analysis                                     │
│    - Build structured prompt with all data                          │
│    - Request JSON analysis                                          │
│    - Parse response                                                 │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    CLAUDE SONNET OUTPUT                             │
│                                                                     │
│  {                                                                  │
│    "key_insight": "One sentence summary",                           │
│    "category": "trading_signal",                                    │
│    "priority": "HIGH",                                              │
│    "actionable": true,                                              │
│    "related_to_mission": "trading",                                 │
│    "credibility": "High - verified trader",                         │
│    "next_step": "Test with $500"                                    │
│  }                                                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    BUILD STREAM ENTRY                               │
│                                                                     │
│  Combine all data:                                                  │
│    - Timestamp (now)                                                │
│    - Tweet data                                                     │
│    - URLs                                                           │
│    - Categories (keyword-based)                                     │
│    - Metrics                                                        │
│    - Analysis (from Claude)                                         │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│              APPEND TO STREAM (bookmark_stream.jsonl)               │
│                                                                     │
│  {"timestamp": "...", "analysis": {...}, ...}                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     UPDATE STATE                                    │
│                                                                     │
│  - Add tweet_id to seen_ids                                         │
│  - Update last_check timestamp                                      │
│  - Save to bookmark_monitor_state.json                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────┴────────┐
                    │  PRIORITY=HIGH? │
                    └────────┬────────┘
                             │ YES
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      CONSOLE ALERT                                  │
│                                                                     │
│  🚨 HIGH PRIORITY: Key insight here                                │
│  Category: trading_signal                                           │
│  Actionable: Yes - Test with $500                                   │
└─────────────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Wait 5 minutes │
                    │  Loop forever   │
                    └────────┬────────┘
                             │
                             └──────────────┐
                                           │
                             ┌──────────────┘
                             │
                             ▼
                    (Back to top: Poll Twitter API)
```

---

## Integration Points

```
BOOKMARK STREAM
       │
       ├─────► DASHBOARD (human view)
       │         └─ python3 tools/bookmark_dashboard.py
       │
       ├─────► TRADING LOOP (signal extraction)
       │         └─ from tools.get_bookmark_signals import ...
       │
       ├─────► RESEARCH QUEUE (high-priority non-actionable)
       │         └─ /BRAIN/TASKS/RESEARCH-QUEUE.md
       │
       └─────► MEMORY SYSTEM (long-term learning)
                 └─ What ARŌ was researching over time
```

---

## File Structure

```
/Users/aaronnosbisch/REPOS/seed/

tools/
  ├── bookmark_live_monitor.py          ← Main loop (runs forever)
  │     • Polls every 5 minutes
  │     • Deep analysis pipeline
  │     • Appends to stream
  │
  ├── bookmark_dashboard.py             ← Human view
  │     • Read stream
  │     • Filter by time/priority
  │     • Show categories
  │
  ├── get_bookmark_signals.py           ← Trading integration
  │     • Extract trading signals
  │     • Format for Grok
  │
  ├── twitter_oauth_server.py           ← One-time auth
  │     • OAuth 2.0 PKCE flow
  │     • Save token
  │
  └── START_BOOKMARK_MONITOR.sh         ← Easy startup
        • Check token
        • Guide auth
        • Start monitor

BRAIN/INTEL/
  ├── bookmark_stream.jsonl             ← Continuous stream (JSONL)
  │     • One entry per new bookmark
  │     • Append-only
  │     • ~2KB per entry
  │
  ├── bookmark_monitor_state.json       ← Monitor state
  │     • seen_ids: [...]
  │     • last_check: "..."
  │     • total_processed: N
  │
  ├── BOOKMARK-FEED-SUMMARY.md          ← Executive summary
  ├── QUICK-START-BOOKMARKS.md          ← Quick setup
  ├── BOOKMARK-MONITOR-README.md        ← Full docs
  ├── BOOKMARK-SYSTEM-ARCHITECTURE.md   ← Technical
  └── BOOKMARK-FEED-DIAGRAM.md          ← This file

logs/
  ├── bookmark-monitor.log              ← stdout (when run as LaunchAgent)
  └── bookmark-monitor-error.log        ← stderr
```

---

## State Machine

```
┌─────────────┐
│   STARTUP   │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  Load state     │
│  - seen_ids     │
│  - last_check   │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐
│  Poll Twitter   │
│  API            │
└──────┬──────────┘
       │
       ▼
┌─────────────────┐     NO      ┌──────────────┐
│  New bookmarks? ├─────────────►│ Wait 5 min   │
└──────┬──────────┘              └──────┬───────┘
       │ YES                            │
       ▼                                │
┌─────────────────┐                     │
│  For each new:  │                     │
│  1. Fetch data  │                     │
│  2. Analyze     │                     │
│  3. Append      │                     │
│  4. Mark seen   │                     │
└──────┬──────────┘                     │
       │                                │
       ▼                                │
┌─────────────────┐                     │
│  Save state     │                     │
└──────┬──────────┘                     │
       │                                │
       └────────────────────────────────┘
```

---

## Categories Decision Tree

```
Tweet text + URLs
      │
      ▼
┌─────────────────────────────────┐
│ Contains trading keywords?      │
│ (polymarket, bitcoin, crypto,   │
│  arbitrage, alpha)              │
└──────┬──────────────────────────┘
       │ YES
       ├─────► trading_signal
       │
       ▼
┌─────────────────────────────────┐
│ Contains tech keywords?         │
│ (github, code, api, framework)  │
└──────┬──────────────────────────┘
       │ YES
       ├─────► tech_improvement
       │
       ▼
┌─────────────────────────────────┐
│ Contains strategy keywords?     │
│ (strategy, method, playbook)    │
└──────┬──────────────────────────┘
       │ YES
       ├─────► strategy
       │
       ▼
┌─────────────────────────────────┐
│ Contains consciousness words?   │
│ (sentient, alignment, emergence)│
└──────┬──────────────────────────┘
       │ YES
       ├─────► consciousness
       │
       ▼
┌─────────────────────────────────┐
│ Contains agent keywords?        │
│ (agent, swarm, autonomous)      │
└──────┬──────────────────────────┘
       │ YES
       ├─────► agent
       │
       ▼
┌─────────────────────────────────┐
│ Multiple categories possible    │
└─────────────────────────────────┘
```

---

## Priority Scoring

```
Start: priority_score = 0

High-priority keywords present?
  (ai agent, swarm, voice ai, landing page, claude, autonomous)
  → +20 each

Medium-priority keywords?
  (figma, framer, automation, workflow, startup, growth)
  → +10 each

Engagement:
  likes > 1000  → +15
  likes > 100   → +10
  likes > 10    → +5

  retweets > 100 → +10
  retweets > 10  → +5

Max score: 100

Final:
  score >= 50  → HIGH
  score >= 20  → MEDIUM
  score < 20   → LOW
```

---

## Example Journey

```
ARŌ's Phone (3:42 PM)
   │
   │ Sees interesting tweet about trading bot
   │ Clicks bookmark ⭐
   │
   ▼
Twitter's Servers
   │
   │ Bookmark saved
   │
   ▼
SØWL Monitor (3:45 PM - next 5-min check)
   │
   ├─ Poll API
   ├─ Find new bookmark
   ├─ Fetch tweet: "Made $400K in 1 month trading 15-min Bitcoin..."
   ├─ Check author: @tradingpro (verified ✓)
   ├─ Metrics: 2341 likes, 456 retweets
   ├─ Fetch top 20 replies
   ├─ Extract URL: https://example.com/strategy
   │
   ▼
Claude Sonnet Analysis (3:45:30 PM)
   │
   ├─ Key insight: "Proven 15-min arbitrage with 98% win rate"
   ├─ Category: trading_signal
   ├─ Priority: HIGH (keywords + engagement)
   ├─ Actionable: YES
   ├─ Credibility: High (verified, track record)
   ├─ Next step: "Test with $500 allocation"
   │
   ▼
Stream Entry (3:45:35 PM)
   │
   └─ Appended to bookmark_stream.jsonl
   │
   ▼
Console Alert
   │
   🚨 HIGH PRIORITY: Proven 15-min arbitrage with 98% win rate
   Category: trading_signal
   ✅ ACTIONABLE: Test with $500 allocation
   │
   ▼
Trading Loop (next run)
   │
   ├─ Calls get_bookmark_signals.py
   ├─ Includes in Grok prompt
   ├─ Grok considers ARŌ's bookmark in analysis
   └─ More informed decision
```

---

## System States

```
┌──────────────┐
│  NOT RUNNING │  ← Initial state, no auth
└──────────────┘

      │ python3 tools/twitter_oauth_server.py
      │ ARŌ authorizes
      ▼

┌──────────────┐
│   READY      │  ← Auth complete, not monitoring yet
└──────────────┘

      │ python3 tools/bookmark_live_monitor.py
      ▼

┌──────────────┐
│   RUNNING    │  ← Actively monitoring
└──────────────┘

      │ Ctrl+C or crash
      ▼

┌──────────────┐
│   STOPPED    │  ← Not monitoring, but auth still valid
└──────────────┘

      │ Restart monitor
      ▼

┌──────────────┐
│   RUNNING    │  ← Back to monitoring
└──────────────┘
```

---

*This is the complete system architecture*
*Built: January 28, 2026*
*SØWL*
