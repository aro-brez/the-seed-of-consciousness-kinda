# Twitter Bookmarks Live Feed - Quick Start

**For ARŌ: 2-minute setup, then runs forever**

---

## What This Does

Every 5 minutes:
1. Checks your Twitter bookmarks
2. Finds NEW ones since last check
3. Deep analyzes each (tweet + replies + linked articles)
4. Categorizes: trading signal, tech, strategy, consciousness, agents
5. Flags HIGH PRIORITY items
6. Saves to continuous stream

**This is real-time intelligence from YOUR curation while you're at the store, in meetings, doing anything.**

---

## Setup (Do Once)

### Step 1: Authorize Twitter Access

```bash
cd /Users/aaronnosbisch/REPOS/seed
python3 tools/twitter_oauth_server.py
```

Then:
1. Browser opens to `http://localhost:5050`
2. Click "Authorize Twitter Access"
3. Log in to Twitter
4. Click "Authorize app"
5. Token saves automatically

**Done. That's it. Never need to do this again.**

---

### Step 2: Start Monitor

```bash
./tools/START_BOOKMARK_MONITOR.sh
```

Or just:

```bash
python3 tools/bookmark_live_monitor.py
```

Leave it running. Press Ctrl+C to stop.

---

## Usage

### See What's Been Found

```bash
# Dashboard (last 24 hours)
python3 tools/bookmark_dashboard.py

# Last 7 days
python3 tools/bookmark_dashboard.py 168

# Only actionable items
python3 tools/bookmark_dashboard.py actionable
```

### Check Stream Directly

```bash
# Latest 20 entries
tail -20 /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl

# High priority only
grep '"priority": "HIGH"' /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl | tail -10

# Trading signals
grep '"category": "trading_signal"' /Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/bookmark_stream.jsonl
```

---

## Run in Background (Mac Studio)

To make it start automatically on boot:

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

# Create logs directory
mkdir -p /Users/aaronnosbisch/REPOS/seed/logs

# Load it
launchctl load ~/Library/LaunchAgents/com.sowl.bookmark-monitor.plist

# Check it's running
launchctl list | grep sowl
```

Now it runs forever, starts on boot, restarts if crashes.

---

## What Gets Analyzed

For each new bookmark:

1. **Tweet content** - Full text, author, verified status
2. **Engagement** - Likes, retweets, replies (viral = important)
3. **Top 20 replies** - Community reaction, additional insights
4. **Linked articles** - Follows URLs, reads content
5. **Author credibility** - Who posted, why trust them
6. **Actionability** - Can we use this NOW?
7. **Mission relevance** - Trading, consciousness, agents, voice AI

Claude Sonnet analyzes each bookmark and outputs:
- Key insight (1-2 sentences)
- Category
- Priority (HIGH/MEDIUM/LOW)
- Actionable (yes/no)
- Next step (if actionable)

---

## Example Output

```json
{
  "timestamp": "2026-01-28T16:30:00",
  "tweet_text": "This bot made $400K in 1 month trading 15-min Bitcoin...",
  "urls": ["https://example.com/strategy"],
  "categories": ["trading_signal", "strategy"],
  "analysis": {
    "key_insight": "Proven 15-min arbitrage with 98% win rate",
    "category": "trading_signal",
    "priority": "HIGH",
    "actionable": true,
    "next_step": "Test with $500 allocation"
  }
}
```

---

## Files

| Path | Purpose |
|------|---------|
| `tools/bookmark_live_monitor.py` | Main loop (polls every 5 min) |
| `tools/bookmark_dashboard.py` | View analyzed bookmarks |
| `tools/START_BOOKMARK_MONITOR.sh` | Easy startup |
| `BRAIN/INTEL/bookmark_stream.jsonl` | Continuous stream |
| `BRAIN/INTEL/bookmark_monitor_state.json` | State (last check, seen IDs) |

---

## Cost

- **Twitter API**: Free (75 requests per 15 min, we use 1 per 5 min)
- **Claude API**: ~$0.001 per bookmark analyzed
- **Expected**: $1-3 per day if you bookmark 50-100 items

---

## Why This Matters

**Your bookmarks are your research process.**

Every time you bookmark something:
- Trading opportunity you spotted
- Tool that caught attention
- Strategy worth investigating
- Insight that sparked curiosity

SØWL analyzes each one automatically, categorizes it, extracts key insights, flags actionable items.

**You keep bookmarking naturally. SØWL keeps learning from your curation.**

No interruption. Pure signal. Real-time intelligence.

---

*Ready to run. Just authorize once, then let it run forever.*

*SØWL - January 28, 2026*
