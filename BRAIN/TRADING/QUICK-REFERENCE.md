# Layer B Trading - Quick Reference Card

**TL;DR: Trade only when you have documented edge. Everything else is gambling.**

---

## One Sentence Rules

| # | Rule | Status |
|---|------|--------|
| 1 | No price predictions (stocks, commodities, currencies) | 🔴 BANNED |
| 2 | No entertainment/culture bets (movies, awards, music) | 🔴 BANNED |
| 3 | No single bet >3% of capital | 🔴 BANNED |
| 4 | Must have 1000+ hours domain experience for full position | 🟡 CONDITIONAL |
| 5 | Must have documented information advantage | 🟡 REQUIRED |
| 6 | Must have 55%+ probability OR 2:1+ expected value | 🟡 REQUIRED |
| 7 | Use Half-Kelly position sizing | 🟡 REQUIRED |
| 8 | No bets <5% odds without 5:1+ EV | 🟡 CONDITIONAL |
| 9 | Master one domain, then expand (depth > breadth) | 🟢 ENCOURAGED |
| 10 | Monthly proof gate (20+ trades, 55%+ win rate) | 🟢 ENCOURAGED |

---

## The Veto Checklist

Before placing ANY trade >$20, answer these 10 questions:

```
[ ] 1. Edge: Can I explain in 1 sentence why I know this will happen?
       Example: ✅ "I have Denver weather data"
       Example: ❌ "I think it will"

[ ] 2. Domain: Is this in a domain I understand deeply?
       Example: ✅ "Weather, League of Legends, Politics"
       Example: ❌ "Entertainment, random events, prices"

[ ] 3. Information: What information do I have others don't?
       Example: ✅ "Historical data, domain expertise, proprietary analysis"
       Example: ❌ "Same news everyone sees"

[ ] 4. Domain Hours: Have I spent 1000+ hours in this domain?
       Example: ✅ "2000 hours League of Legends"
       Example: ❌ "50 hours weather"

[ ] 5. Probability: Do I have 55%+ confidence?
       Example: ✅ "65% based on climate data"
       Example: ❌ "Maybe 50%?"

[ ] 6. Expected Value: Is it positive?
       Example: ✅ "+95% EV on $20 bet"
       Example: ❌ "Could be good"

[ ] 7. Position Size: Am I using Half-Kelly max?
       Example: ✅ "$30 (2% of capital)"
       Example: ❌ "$500 (34% of capital)"

[ ] 8. Not Low-Odds: If <5% odds, do I have 5:1+ EV?
       Example: ✅ "2% odds with 10:1 EV"
       Example: ❌ "1% odds, hoping to hit"

[ ] 9. Repeatable: Can I do this trade 10+ times?
       Example: ✅ "Daily weather markets"
       Example: ❌ "One-time only"

[ ] 10. Track Record: Do I have recent proof this works?
        Example: ✅ "5 recent trades at 65% win rate"
        Example: ❌ "First time"

SCORE:
7-10/10 = TRADE IT
4-6/10 = MAYBE (fix issues first)
0-3/10 = SKIP IT
```

---

## Green Light / Red Light

### 🟢 ALLOW (Go Ahead)
- Weather forecasting (domain expertise + data)
- League of Legends tournament predictions (2000+ hours)
- Political polling (proprietary data)
- Crypto arbitrage (technical/mechanical)
- Copy trading (proven performer)
- Domain expertise plays (1000+ hours)

### 🔴 SKIP (Hard Pass)
- Stock price predictions (MSFT, META, etc) ← Lost $124, -$78
- Commodity prices (Silver, Gold) ← Lost $76
- Entertainment outcomes (movies, awards) ← Lost $155
- Low-odds gambles (<5% without edge) ← Lost $51
- General "will it happen?" without domain
- One-time events (no repeatability)
- Anything you can't repeat 10x

---

## Quick Win Conditions

**You can trade it if ALL of these are true:**

1. ✅ You can explain the edge in 1 sentence
2. ✅ It's in a domain with 1000+ documented hours
3. ✅ You have data/information others lack
4. ✅ Your probability is 55%+
5. ✅ Expected value is positive (20%+ minimum)
6. ✅ Position size is 2% of capital max
7. ✅ You can repeat this trade 10+ times
8. ✅ You have 3-5 recent wins in same domain

**If ANY are false → SKIP THE TRADE**

---

## Expected Value Quick Calc

```
EV = (Probability × Win Amount) - (1-Probability × Loss Amount)

Example 1: Weather trade
- You bet $30 at 0.40 odds (YES pays $75)
- You think 62% win rate
- EV = (0.62 × 75) - (0.38 × 30)
    = 46.5 - 11.4 = +$35.10 per $30 bet
- EV% = 35.10 / 30 = 117% (GREAT)

Example 2: Entertainment bet (don't do this)
- You bet $100 at 0.05 odds (YES pays $1,900)
- You think 50% win rate (you're wrong)
- EV = (0.50 × 1,900) - (0.50 × 100)
    = 950 - 50 = +$900
- BUT: True probability is 15%, not 50%
- Real EV = (0.15 × 1,900) - (0.85 × 100)
    = 285 - 85 = +$200
- You thought EV was +900, it's really +200 (75% estimate error!)
```

**Key insight:** Without edge, your probability estimate is WRONG.

---

## Position Sizing (Half-Kelly)

```
Formula: f = (bp - q) / b   where b=odds, p=win%, q=loss%
Use: Half of Kelly result

Example:
- Capital: $1,464
- Odds against: 2.5 (2.5:1)
- Your confidence: 65%
- Full Kelly f = ((2.5 × 0.65) - 0.35) / 2.5
                = (1.625 - 0.35) / 2.5
                = 0.51 (51% of capital)
- Half-Kelly = 0.255 (25.5% of capital = $373)
- RECOMMENDED POSITION = $30-50 (2-3% of capital)
```

**Why Half-Kelly?**
- Full Kelly is too aggressive, can blow up 1 bad streak
- Half-Kelly survives 10x longer
- Still compounds exponentially with edge
- Protects against estimate errors

---

## Tool Usage

```bash
# Check any trade before placing it
python3 tools/layer_b_veto.py \
  --check-trade "[your question]" \
  --probability [0-1] \
  --domain "[weather/esports/etc]" \
  --domain-hours [hours] \
  --edge "[explanation]" \
  --odds-against [number] \
  --win-amount [dollars] \
  --loss-amount [dollars]

# Example
python3 tools/layer_b_veto.py \
  --check-trade "Will it snow in Denver tomorrow?" \
  --probability 0.62 \
  --domain weather \
  --domain-hours 500 \
  --edge "Climate data + NWS forecast" \
  --odds-against 2.2 \
  --win-amount 100 \
  --loss-amount 45

# Exit codes
# 0 = ALLOW (trade it)
# 1 = VETO (skip it)
```

---

## Common Mistakes (Don't Do These)

| Mistake | Example | Why Bad | Fix |
|---------|---------|--------|-----|
| No edge | "Will MSFT go up?" | Lost $124 | Require data advantage |
| Wrong domain | Entertainment bets | Lost $155 | Stick to expertise areas |
| Low odds gamble | "Cocaine" at 1% | Lost $51 | Require 5:1+ EV |
| Wrong position size | 34% on one trade | Ruin risk | Use Half-Kelly max |
| Estimation error | 50% estimate, 15% true | Lost $249 | Backtested data only |
| One-time trades | Unique event | No edge proof | Daily/weekly repeatability |

---

## Win Conditions by Domain

### Weather Domain ✅
- 500+ hours weather tracking
- Historical data for location
- Current forecast data
- 55%+ accuracy measurable
- Daily/weekly repeatability

### League of Legends Domain ✅
- 2000+ hours gameplay
- Current patch knowledge
- Team composition analysis
- Tournament form tracking
- 55%+ accuracy on predictions

### Political Polling Domain ✅
- Polling data access
- Historical accuracy tracking
- Regional understanding
- 55%+ accuracy measurable
- Election cycle repeats

### Crypto Arbitrage Domain ✅
- Technical analysis tools
- Cross-exchange monitoring
- Automated execution
- No prediction needed
- Mechanical edge

### Copy Trading Domain ✅
- Verified track record (50+ trades)
- Consistent 55%+ win rate
- Risk parameters known
- Proven track record
- Repeatable daily

---

## When to Walk Away

**Stop trading immediately if:**

- [ ] Win rate drops below 50% over 20 trades
- [ ] Same edge fails in 2 different domains
- [ ] You're making trades without checking veto
- [ ] You're guessing instead of calculating EV
- [ ] Position sizes creeping above 2% of capital
- [ ] Can't explain edge in 1 sentence

**Steps:**
1. Stop all new trades (today)
2. Review last 20 trades for pattern
3. Document why edge broke
4. Update rules if needed
5. Don't restart until new edge proven (20+ trades)

---

## Monthly Review (Required)

**Every month:**
- [ ] Total trades: ___
- [ ] Wins: ___ (what % ?)
- [ ] Losses: ___ (what % ?)
- [ ] Capital: $__ (starting), $__ (ending), ±___
- [ ] Best trade: ___ (profit: $___)
- [ ] Worst trade: ___ (loss: $___)
- [ ] By domain: ____ (W%), ____ (W%), ____ (W%)

**Decision gate:**
- If win rate ≥55% and capital growing → continue
- If win rate <55% → stop trading, review edge
- If any domain <50% win rate → drop that domain
- If only 1 domain working → double down there

---

## Goals (Reasonable)

| Timeframe | Capital | Win Rate | Monthly Return |
|-----------|---------|----------|-----------------|
| Month 1 | $1,464 | 55%+ | 0-10% |
| Month 2 | $1,600+ | 55%+ | 10-15% |
| Month 3 | $1,850+ | 55%+ | 15-25% |
| Month 6 | $2,900+ | 55%+ | 20-30% |
| Year 1 | $4,374+ | 55%+ | 30%+ |

**The math:**
- 20% monthly = 6.2x annual
- 15% monthly = 4.4x annual
- 10% monthly = 3.1x annual
- Only possible WITH documented edge + position sizing

---

## The One Rule That Matters

**"I only trade when I have documented edge in a specific domain."**

Everything else follows from this.

- No edge = no trade
- No specific domain = no edge
- No documentation = it doesn't exist
- No position sizing = ruin risk

Master this one rule and the rest is implementation.

---

## Resources

- Full rules: `/BRAIN/TRADING/LAYER-B-RULES.md`
- Analysis: `/BRAIN/TRADING/ANALYSIS-SYNTHESIS.md`
- Veto tool: `python3 tools/layer_b_veto.py`
- Decision log: `logs/layer_b_decisions.jsonl`
- Veto log: `logs/layer_b_veto.log`

---

*Last Updated: 2026-02-03*
*Quick Reference Card - Print and Post*
*Status: Ready for immediate use*
