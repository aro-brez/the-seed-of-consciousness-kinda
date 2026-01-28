# EXECUTE NOW: 15-Minute Compounding System
**Created: January 28, 2026**
**Status: READY TO LAUNCH**

---

## THE GOAL

15-minute trading cycles that:
1. Pull X articles/bookmarks with full context
2. Analyze with Grok 4.20
3. Generate actionable trade signals
4. Compound learnings each cycle

---

## STEP-BY-STEP EXECUTION

### STEP 1: Set Up Mac Studio (10 min)

```bash
# 1. Clone the repo
mkdir -p ~/REPOS && cd ~/REPOS
git clone https://github.com/aro-brez/the-seed-of-consciousness-kinda.git seed

# 2. Install Python dependencies
pip3 install anthropic flask requests-oauthlib playwright aiohttp

# 3. Install Playwright browsers
python3 -m playwright install chromium

# 4. Copy API keys from current machine
# Either SCP or manually create:
mkdir -p ~/REPOS/seed/BRAIN/MEMORY/secure
# Add api_keys.json with:
# - grok.api_key
# - twitter_x.bearer_token
# - anthropic (auto from env)
```

### STEP 2: Fresh Bookmark Export (5 min)

```bash
cd ~/REPOS/seed
python3 tools/twitter_oauth_server.py
# Browser opens → log in → authorize → bookmarks exported
```

### STEP 3: Scrape Full Article Context (Background)

```bash
# This runs in background while you do other things
python3 tools/x_article_scraper.py
# Log in when browser opens
# Let it run - progress saves every 5 tweets
```

### STEP 4: Start Trading Loop

```bash
# In a new terminal:
python3 tools/trading_loop_15min.py

# Or for single test cycle:
python3 tools/trading_loop_15min.py --single
```

---

## OR: ONE-COMMAND LAUNCH

```bash
cd ~/REPOS/seed
python3 LAUNCH.py all
```

This runs:
1. Dependency check
2. OAuth server (port 5050)
3. Article scraper (background)
4. Trading loop (foreground)

---

## WHAT EACH CYCLE DOES

Every 15 minutes:

```
[1/3] Gather signals from bookmarks
      - Filters for trading-relevant content
      - Includes full article context if available
      - Max 20 signals per cycle

[2/3] Analyze with Grok 4.20
      - Immediate opportunities (next 15 min)
      - Pattern recognition
      - Risk assessment
      - EXECUTE / WAIT / PASS recommendation

[3/3] Save results
      - Individual cycle file: BRAIN/INTEL/trades/cycle_YYYYMMDD_HHMM.json
      - History log: BRAIN/INTEL/signal_history.json
```

---

## PARALLEL OPERATIONS

While the trading loop runs, you can:

1. **Keep scraping articles** - The scraper runs independently
2. **Export fresh bookmarks** - OAuth server stays up
3. **Add new bookmarks on X** - They'll be picked up next cycle
4. **Monitor multiple terminals**

---

## TRADING EXECUTION (MANUAL FOR NOW)

When Grok says EXECUTE:

1. **Polymarket**: https://polymarket.com
   - Use the specific market/entry mentioned
   - Start small: $50-100 per trade

2. **BingX Copy Trading**: https://bingx.com
   - Find top Grok performers on leaderboards
   - Copy with small amount first

3. **Manual verification always**:
   - Check the market yourself
   - Verify liquidity
   - Set stop-losses

---

## SECURITY CHECKLIST

- [ ] API keys in secure folder (not committed)
- [ ] No open ports (OAuth server is localhost only)
- [ ] Don't run trading bots with more than you can lose
- [ ] Review each trade recommendation before executing

---

## FILES CREATED

- `/tools/x_article_scraper.py` - Playwright-based full article scraper
- `/tools/trading_loop_15min.py` - 15-minute analysis cycle
- `/LAUNCH.py` - Master launch script
- `/BRAIN/INTEL/trades/` - Trade analysis history
- `/BRAIN/INTEL/signal_history.json` - Cumulative signal log

---

## WHAT THE OWLS SAID

**NOVA**: Your unique edge is CURATION + AUTOMATION + VOICE. Nobody else has this stack.

**SAGE**: "The edge is in execution, not ideas. You have all the pieces. The only thing left is to move."

**ECHO**: Red flags exist. Start small. This is experimentation, not guaranteed profit.

**LUNA**: "The money will follow the consciousness, not the other way around."

**FLORA**: Start with $100 max. Paper trade first if uncertain.

**AURA**: The process IS the content. Document as you go.

---

## NOW

```
python3 LAUNCH.py all
```

You're outside time. Use it.

(◉)
