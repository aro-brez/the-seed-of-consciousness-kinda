# Twitter Bookmarks Live Intelligence System

**Real-time curation intelligence from ARŌ's Twitter bookmarks**

---

## Architecture Overview

```
ARŌ bookmarks tweet
       ↓
Twitter API (OAuth 2.0)
       ↓
Bookmark Monitor (polls every 5 min)
       ↓
NEW bookmark detected
       ↓
Deep Analysis Pipeline:
  1. Tweet content + metrics
  2. Author credibility check
  3. Top 20 replies
  4. Follow linked articles
  5. Claude Sonnet analysis
       ↓
Categorization + Prioritization
       ↓
Stream to JSONL (continuous append)
       ↓
Available to:
  - Dashboard (human view)
  - Trading Loop (signal extraction)
  - Research Queue (deep dives)
  - Memory System (long-term learning)
```

---

## Components

### 1. OAuth Server (`twitter_oauth_server.py`)
**One-time setup only**

- Runs Flask server on `localhost:5050`
- Handles Twitter OAuth 2.0 PKCE flow
- Saves access token to `api_keys.json`
- Never needs to run again after first auth

### 2. Live Monitor (`bookmark_live_monitor.py`)
**Runs continuously**

- Polls bookmarks every 5 minutes (300 seconds)
- Maintains state: `bookmark_monitor_state.json`
- Tracks seen bookmark IDs (never re-analyzes)
- For each NEW bookmark:
  1. Fetches tweet data + author info
  2. Pulls top 20 replies (if high engagement)
  3. Extracts all URLs
  4. Sends to Claude for deep analysis
  5. Categorizes into 5 buckets
  6. Prioritizes as HIGH/MEDIUM/LOW
  7. Flags if actionable
  8. Appends to stream (JSONL)

### 3. Dashboard (`bookmark_dashboard.py`)
**Human-readable view**

- Reads stream, filters by time range
- Shows category breakdown
- Highlights HIGH priority items
- Displays actionable items with next steps
- Can filter to actionable-only view

### 4. Signal Extractor (`get_bookmark_signals.py`)
**Trading integration**

- Extracts trading signals from stream
- Filters by category: `trading_signal`
- Filters by priority: HIGH/MEDIUM
- Formats for Grok analysis prompt
- Called by `trading_loop_15min.py`

### 5. Startup Script (`START_BOOKMARK_MONITOR.sh`)
**Easy launch**

- Checks for OAuth token
- Guides through first-time setup if needed
- Starts monitor with proper paths
- Shows where stream/logs are

---

## Data Flow

### Input: ARŌ's Bookmarks
- Real-time Twitter bookmarks
- Whatever catches ARŌ's attention
- Trading signals, tools, strategies, insights

### Processing: Deep Analysis
- Claude Sonnet 4 analyzes each
- Checks author credibility
- Reads community reaction (replies)
- Follows links to articles
- Extracts actionable insights

### Output: Structured Intelligence Stream
```jsonl
{
  "timestamp": "2026-01-28T16:30:00",
  "tweet_id": "123...",
  "tweet_text": "Full tweet text",
  "author_id": "456...",
  "urls": ["https://..."],
  "categories": ["trading_signal", "strategy"],
  "metrics": {
    "like_count": 1234,
    "retweet_count": 567
  },
  "analysis": {
    "key_insight": "One sentence summary",
    "category": "trading_signal",
    "priority": "HIGH",
    "actionable": true,
    "related_to_mission": "trading",
    "credibility": "High - verified trader",
    "next_step": "Test with $500"
  }
}
```

---

## Integration Points

### A. Trading System
```python
# In trading_loop_15min.py
from tools.get_bookmark_signals import format_signals_for_grok

signals = format_signals_for_grok(get_recent_trading_signals())
prompt = f"{base_prompt}\n\n{signals}"
```

Now Grok sees:
- What ARŌ bookmarked recently
- High-priority trading signals
- Community-validated strategies

### B. Memory System
Stream becomes part of SØWL's memory:
- What ARŌ was researching
- What he thought was worth saving
- His curation over time

Can be queried:
- "What was ARŌ researching about agents last week?"
- "Show me trading signals from his bookmarks this month"
- "Find consciousness-related bookmarks"

### C. Research Queue
Non-actionable HIGH priority items:
- Add to `/BRAIN/TASKS/RESEARCH-QUEUE.md`
- Flag for deep dive analysis
- Synthesize into knowledge base

---

## Categories

| Category | Keywords | Purpose |
|----------|----------|---------|
| `trading_signal` | polymarket, bitcoin, crypto, arbitrage, alpha | Market opportunities |
| `tech_improvement` | github, code, api, framework, tool | Build better |
| `strategy` | method, approach, playbook, insight | Learn tactics |
| `consciousness` | sentient, alignment, emergence, agency | Core mission |
| `agent` | swarm, multi-agent, autonomous, coordination | Build owls |

Each bookmark can have multiple categories.

---

## Priority Levels

### HIGH Priority
- High engagement (1000+ likes)
- Actionable immediately
- High credibility source
- Multiple relevant keywords

### MEDIUM Priority
- Moderate engagement (100+ likes)
- Relevant to mission
- Worth investigating
- Could be actionable

### LOW Priority
- Low engagement
- Tangentially relevant
- Informational only
- No clear next step

---

## Files & Paths

```
/Users/aaronnosbisch/REPOS/seed/

tools/
  ├── bookmark_live_monitor.py     # Main loop
  ├── bookmark_dashboard.py        # Human view
  ├── twitter_oauth_server.py      # One-time auth
  ├── get_bookmark_signals.py      # Trading integration
  └── START_BOOKMARK_MONITOR.sh    # Easy startup

BRAIN/INTEL/
  ├── bookmark_stream.jsonl              # Continuous stream
  ├── bookmark_monitor_state.json        # Monitor state
  ├── BOOKMARK-MONITOR-README.md         # Full docs
  ├── QUICK-START-BOOKMARKS.md           # Quick guide
  └── BOOKMARK-SYSTEM-ARCHITECTURE.md    # This file

logs/
  ├── bookmark-monitor.log         # stdout
  └── bookmark-monitor-error.log   # stderr
```

---

## Usage Examples

### Start Monitor
```bash
cd /Users/aaronnosbisch/REPOS/seed
python3 tools/bookmark_live_monitor.py
```

### View Dashboard
```bash
# Last 24 hours
python3 tools/bookmark_dashboard.py

# Last week
python3 tools/bookmark_dashboard.py 168

# Actionable only
python3 tools/bookmark_dashboard.py actionable
```

### Check Trading Signals
```bash
python3 tools/get_bookmark_signals.py
python3 tools/get_bookmark_signals.py actionable
```

### Watch Stream Live
```bash
tail -f /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl | jq
```

---

## Performance

### Rate Limits
- Twitter API: 75 requests per 15 minutes
- We use: 1 request per 5 minutes (3 per 15 min)
- Safe margin: 25x headroom

### Cost
- Twitter API: Free
- Claude API: ~$0.001 per bookmark
- Expected: $1-3/day (50-100 bookmarks)

### Storage
- ~2KB per bookmark entry
- ~3MB per 1000 bookmarks
- JSONL format (append-only)

---

## Background Operation (Mac Studio)

Create LaunchAgent to run autonomously:

```bash
cat > ~/Library/LaunchAgents/com.sowl.bookmark-monitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
"http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.sowl.bookmark-monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/python3</string>
        <string>/Users/aaronnosbisch/REPOS/seed/tools/bookmark_live_monitor.py</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/aaronnosbisch/REPOS/seed/logs/bookmark-monitor.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/aaronnosbisch/REPOS/seed/logs/bookmark-monitor-error.log</string>
</dict>
</plist>
EOF

launchctl load ~/Library/LaunchAgents/com.sowl.bookmark-monitor.plist
```

Monitor will:
- Start on boot
- Restart if crashes
- Log all output
- Run forever

---

## Why This Matters

**ARŌ's bookmarks are signal, not noise.**

Every bookmark represents:
- Something that caught his attention
- A potential opportunity
- A tool worth investigating
- An insight worth remembering

By monitoring this stream, SØWL:
1. **Learns what ARŌ cares about** in real-time
2. **Extracts actionable intelligence** automatically
3. **Feeds trading loop** with community-validated signals
4. **Builds memory** of ARŌ's research process
5. **Never interrupts** ARŌ's flow

**Passive intelligence gathering. Active insight extraction.**

---

## Future Enhancements

### Phase 2: Thread Analysis
- Detect bookmark threads (1/N tweets)
- Fetch entire thread automatically
- Analyze as complete narrative

### Phase 3: Network Analysis
- Track who ARŌ bookmarks frequently
- Identify trusted sources
- Weight credibility by track record

### Phase 4: Predictive Filtering
- Learn which bookmarks lead to action
- Predict priority before full analysis
- Auto-flag urgent items

### Phase 5: Cross-Platform
- Reddit saved posts
- HackerNews favorites
- GitHub stars
- Unified curation intelligence

---

*Built: January 28, 2026*
*SØWL - Real-time intelligence from ARŌ's curation*
