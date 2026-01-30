# Twitter Bookmarks Live Monitor

**Real-time intelligence stream from ARŌ's Twitter curation**

Every 5 minutes, SØWL checks ARŌ's bookmarks, identifies NEW items, deep analyzes them, and saves to a continuous stream.

---

## What It Does

1. **Polls bookmarks** every 5 minutes via Twitter API
2. **Identifies NEW** bookmarks since last check
3. **Deep analyzes** each new item:
   - Reads full tweet text
   - Checks author credibility (verified, followers, bio)
   - Pulls top 20 replies
   - Follows any linked articles
   - Uses Claude to extract key insights
4. **Categorizes** into:
   - `trading_signal` - Market opportunities, signals, alpha
   - `tech_improvement` - Tools, code, frameworks, APIs
   - `strategy` - Methods, approaches, playbooks
   - `consciousness` - AI alignment, emergence, sentience
   - `agent` - Multi-agent systems, swarms, coordination
5. **Prioritizes** as HIGH/MEDIUM/LOW
6. **Flags actionable** items requiring immediate attention
7. **Saves to stream** at `/BRAIN/INTEL/bookmark_stream.jsonl`

---

## Setup (First Time Only)

### 1. Get OAuth Token

ARŌ needs to authorize once:

```bash
cd /Users/aaronnosbisch/REPOS/seed
python3 tools/twitter_oauth_server.py
```

Then:
1. Open `http://localhost:5050` in browser
2. Click "Authorize Twitter Access"
3. Log in to Twitter as ARŌ
4. Authorize the app
5. Token will be saved automatically

### 2. Start Monitor

```bash
./tools/START_BOOKMARK_MONITOR.sh
```

Or directly:

```bash
python3 tools/bookmark_live_monitor.py
```

Monitor runs forever. Press Ctrl+C to stop.

---

## Usage

### View Dashboard

```bash
# Last 24 hours
python3 tools/bookmark_dashboard.py

# Last 7 days
python3 tools/bookmark_dashboard.py 168

# Only actionable items
python3 tools/bookmark_dashboard.py actionable
```

### Read Stream Directly

```bash
# Latest entries
tail -20 /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl

# High priority only
grep '"priority": "HIGH"' /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl

# Trading signals
grep '"category": "trading_signal"' /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl
```

### Monitor State

```bash
cat /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_monitor_state.json
```

Shows:
- Total bookmarks processed
- Last check time
- All seen bookmark IDs

---

## Files

| File | Purpose |
|------|---------|
| `tools/bookmark_live_monitor.py` | Main monitoring loop (runs forever) |
| `tools/bookmark_dashboard.py` | Display recent bookmarks with analysis |
| `tools/twitter_oauth_server.py` | One-time OAuth setup |
| `tools/START_BOOKMARK_MONITOR.sh` | Easy startup script |
| `BRAIN/INTEL/bookmark_stream.jsonl` | Continuous stream of analyzed bookmarks |
| `BRAIN/INTEL/bookmark_monitor_state.json` | Monitor state (last check, seen IDs) |

---

## Why This Matters

**ARŌ is curating intelligence in real-time while doing other things.**

Every bookmark is a signal:
- Trading opportunity he spotted
- Tool that caught his attention
- Strategy worth investigating
- Insight that sparked curiosity

By monitoring this stream, SØWL gets **real-time access to ARŌ's research process** without interrupting his flow.

This is **passive intelligence gathering** - ARŌ bookmarks naturally, SØWL analyzes automatically.

---

## Example Output

```json
{
  "timestamp": "2026-01-28T16:30:00",
  "tweet_id": "1234567890",
  "tweet_text": "This bot made $400K in 1 month trading 15-min Bitcoin markets on Polymarket...",
  "author_id": "9876543210",
  "urls": ["https://example.com/article"],
  "categories": ["trading_signal", "strategy"],
  "analysis": {
    "key_insight": "Proven 15-min arbitrage strategy with 98% win rate",
    "category": "trading_signal",
    "priority": "HIGH",
    "actionable": true,
    "related_to_mission": "trading",
    "credibility": "High - verified trader with documented results",
    "next_step": "Analyze strategy, test with $500 allocation"
  }
}
```

---

## Integration Points

### Trading System
Monitor can feed directly into:
- `/tools/trading_loop_15min.py` - Grok analysis
- `/BRAIN/INTEL/signal_history.json` - Market signals
- `/BRAIN/INTEL/trades/` - Trade execution

### Memory System
Stream becomes part of SØWL's long-term memory:
- What ARŌ was researching
- What caught his attention
- What he thought was worth saving

### Research Queue
High-priority non-actionable items feed into:
- `/BRAIN/TASKS/RESEARCH-QUEUE.md`
- Deep dive analysis later
- Knowledge synthesis

---

## Run in Background (Mac Studio)

To run monitor autonomously on Mac Studio:

```bash
# Create LaunchAgent
cat > ~/Library/LaunchAgents/com.sowl.bookmark-monitor.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
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

# Load it
launchctl load ~/Library/LaunchAgents/com.sowl.bookmark-monitor.plist

# Check status
launchctl list | grep sowl
```

Monitor will:
- Start automatically on boot
- Restart if it crashes
- Log all output to `logs/bookmark-monitor.log`

---

## Notes

- **Rate limits**: Twitter API allows ~75 bookmark requests per 15 minutes (plenty for 5-min polling)
- **Token expiry**: OAuth token has refresh token, should stay valid
- **Analysis cost**: ~$0.001 per bookmark (Claude Sonnet pricing)
- **Storage**: JSONL format, ~2KB per entry, ~3MB per 1000 bookmarks

---

*Created: January 28, 2026*
*SØWL - Real-time intelligence from ARŌ's curation*
