# SIGNAL SOURCES COMPARISON TABLE
**For rapid decision-making on intelligence stack design**

---

## REAL-TIME DATA FEEDS (Infrastructure Layer)

| Source | Coverage | Latency | Cost | Priority | Status |
|--------|----------|---------|------|----------|--------|
| **Binance WebSocket** | BTC/ETH/SOL spot | <100ms | Free | CRITICAL | Need to build |
| **Coinbase WebSocket** | BTC/ETH/SOL spot | <100ms | Free | HIGH (backup) | Need to build |
| **Polymarket WebSocket** | Order books, trades | <50ms | Free | CRITICAL | Need to build |
| **FinFeedAPI** | Multi-platform OHLCV | <50ms | Paid ($?) | HIGH | Research pricing |
| **Kalshi API** | US prediction markets | Unknown | Free | MEDIUM | Future phase |

**Bottom line:** Binance + Polymarket WebSockets are non-negotiable for latency arbitrage.

---

## AI ANALYSIS MODELS (Intelligence Layer)

| Model | Strengths | Weaknesses | Cost/Limits | Use Case | Status |
|-------|-----------|------------|-------------|----------|--------|
| **Grok 4.20** | Real-time X data, conservative, beat GPT/Gemini in trading | Rate limits (40 req/min), no execution, weak TA, hallucination risk | $5/mo API, 40 req/min | Primary sentiment + patterns | Active |
| **Claude Sonnet 4.5** | Superior reasoning, deep analysis, synthesis | No real-time social data, slower | Pay per token | Validation + deep analysis | Need to integrate |
| **GPT-5** | Different training data, good at certain tasks | Lost money in Alpha Arena | Pay per token | Tie-breaker only | Optional |
| **Gemini 3.0** | Google data access | Lost money in Alpha Arena | Pay per token | Not recommended | Skip |

**Bottom line:** Grok primary, Claude backup/validation, ensemble voting for high-stakes trades.

---

## HUMAN INTELLIGENCE SOURCES

| Source | Signal Type | Update Frequency | Quality | Cost | Status |
|--------|-------------|------------------|---------|------|--------|
| **Twitter Bookmarks (ARŌ)** | Pre-filtered alpha | Continuous | High (human curation) | Free | Active |
| **Whale Wallet Tracking** | Large trader moves | Real-time | Very High (proven winners) | Free (Dune) | Need to build |
| **Polymarket Leaderboard** | Top trader positions | Daily | High | Free | Manual monitoring |
| **Alpha Discord/Telegram** | Professional trade ideas | Real-time | Medium-High (signal/noise) | Free-$50/mo | Need to join |
| **Crypto Twitter (raw)** | Market sentiment | Real-time | Low (noise) | Free | Use sparingly |

**Bottom line:** Whale tracking = highest ROI (copy proven winners). ARŌ bookmarks = pre-filtered quality.

---

## QUANTITATIVE / ON-CHAIN DATA

| Source | Data Type | Timeframe | Actionability | Cost | Priority |
|--------|-----------|-----------|---------------|------|----------|
| **Glassnode** | On-chain metrics | Hours-Days | Medium (leading indicator) | $300-400/mo | LOW (not real-time) |
| **Nansen** | Whale movements | Hours-Days | Medium-High | $150-300/mo | MEDIUM |
| **Arkham Intelligence** | Entity tracking | Real-time | Medium | Free tier | MEDIUM |
| **Coinglass** | Derivatives data | Real-time | High (funding rates, OI) | Free | HIGH |
| **Hyperliquid** | DEX order flow | Real-time | High | Free | MEDIUM |

**Bottom line:** Coinglass (free) for derivatives data. On-chain metrics = nice-to-have, not critical for prediction markets.

---

## SIGNAL SOURCE RELIABILITY MATRIX

| Source | Accuracy | Speed | Coverage | Redundancy Available | Single Point of Failure Risk |
|--------|----------|-------|----------|---------------------|----------------------------|
| Grok 4.20 | High (proven) | Medium | Social only | Yes (Claude, GPT) | MEDIUM |
| Binance WebSocket | Very High | Very Fast | Spot prices | Yes (Coinbase) | LOW |
| Polymarket WebSocket | Very High | Very Fast | PM markets | Yes (FinFeedAPI) | MEDIUM |
| Twitter Bookmarks | High | Medium | Curated alpha | No | HIGH (ARŌ only) |
| Whale Tracking | Very High | Fast | Large trades | Yes (multiple trackers) | LOW |
| Claude Sonnet | High | Medium | Deep analysis | Yes (GPT, Gemini) | LOW |
| On-chain Metrics | Medium | Slow | Macro trends | Yes (multiple providers) | LOW |

**Critical vulnerabilities:**
- Twitter bookmarks = single curator (ARŌ)
- Polymarket API = single exchange (need Kalshi backup)
- Mac Studio = single machine (need cloud backup)

---

## COST-BENEFIT ANALYSIS

### Free Tier (Start Here)

| Source | Setup Time | Value | Build Priority |
|--------|-----------|-------|----------------|
| Binance WebSocket | 2-4 hours | CRITICAL | #1 |
| Polymarket WebSocket | 2-4 hours | CRITICAL | #2 |
| Coinbase WebSocket | 1-2 hours | HIGH | #3 |
| Claude integration | 1 hour | HIGH | #4 |
| Whale tracking | 4-6 hours | HIGH | #5 |
| Coinglass derivatives | 2 hours | MEDIUM | #6 |

**Total cost:** $0
**Total build time:** 12-19 hours
**Unlocks:** 3 of 5 strategies, 80% of edge

---

### Paid Tier (Scale Later)

| Source | Monthly Cost | Incremental Value | When to Add |
|--------|-------------|-------------------|-------------|
| FinFeedAPI | $200-500? | 10-15% (faster arb) | Month 2-3 |
| Nansen | $150-300 | 5-10% (whale intel) | Month 3-4 |
| Glassnode | $300-400 | 3-5% (macro trends) | Month 4+ |
| Premium Telegram | $50-100 | 5% (alpha ideas) | Month 2-3 |

**Total cost:** $700-1,300/mo
**Incremental value:** 23-40% improvement
**ROI:** Positive if trading >$5K bankroll

---

## RECOMMENDED INTELLIGENCE STACK BY PHASE

### PHASE 1: Week 1 (Free Tier, Core Infrastructure)
```
PRIMARY SIGNALS:
├─ Binance WebSocket (latency arb)
├─ Polymarket WebSocket (order flow)
└─ Grok 4.20 (sentiment)

BACKUP:
├─ Claude Sonnet (analysis)
└─ Twitter bookmarks (alpha)

RESULT: Can trade latency arb + momentum with 80% of edge
```

### PHASE 2: Week 2-3 (Free Tier, Enhanced)
```
PRIMARY SIGNALS:
├─ Binance + Coinbase WebSocket
├─ Polymarket WebSocket
├─ Grok 4.20
└─ Whale tracking (Dune, leaderboard)

ANALYSIS:
├─ Claude Sonnet (validation)
└─ GPT-5 (tie-breaker)

INTEL:
├─ Twitter bookmarks
└─ Alpha Discord/Telegram (free tiers)

RESULT: Full redundancy, ensemble AI, human+quant intel
```

### PHASE 3: Month 2+ (Paid Tier, Professional)
```
PRIMARY SIGNALS:
├─ Binance + Coinbase WebSocket
├─ Polymarket + Kalshi WebSocket
├─ FinFeedAPI (multi-platform arb)
└─ Whale tracking (Nansen + Arkham)

ANALYSIS:
├─ Grok 4.20 (primary)
├─ Claude Sonnet (validation)
└─ GPT-5 (ensemble)

INTEL:
├─ Twitter bookmarks (ARŌ)
├─ Premium alpha groups
├─ Coinglass derivatives
└─ On-chain metrics (Glassnode/Nansen)

RESULT: Institutional-grade intelligence stack
```

---

## DECISION MATRIX: WHAT TO BUILD FIRST

### IMMEDIATE (This Week)
1. Binance WebSocket → Enables latency arb
2. Polymarket WebSocket → Enables real-time entry
3. Claude integration → Eliminates Grok single-dependency

### SHORT-TERM (Week 2-3)
4. Coinbase WebSocket → Backup for Binance
5. Whale tracking → Copy proven winners
6. Ensemble AI voting → Higher conviction trades

### MEDIUM-TERM (Month 2)
7. FinFeedAPI → Faster cross-platform arb
8. Cloud VPS → 24/7 uptime
9. Kalshi API → Multi-exchange redundancy

### LONG-TERM (Month 3+)
10. Premium data feeds → Last 10-20% of edge
11. Custom ML models → Strategy optimization
12. Multi-agent coordination → Automated research

---

## FINAL RECOMMENDATION

**Start with:** Free tier, core infrastructure (Binance + Polymarket + Claude)
**Build time:** 12-19 hours (1 week)
**Cost:** $0
**Unlocks:** 80% of edge, 3 of 5 strategies
**Risk:** Low (free, validated approaches)

**Scale to:** Enhanced free tier (add whale tracking, ensemble AI, backup feeds)
**Build time:** +8-12 hours (Week 2)
**Cost:** $0
**Unlocks:** 95% of edge, full redundancy
**Risk:** Low

**Professional tier:** Add paid feeds once bankroll >$10K
**Cost:** $700-1,300/mo
**Incremental edge:** +10-20%
**ROI:** Positive (pays for itself with better execution)

**The math is clear: Build free tier first, validate with capital, then scale.**

**(◉)**

---

*SØWL*
*January 28, 2026*
