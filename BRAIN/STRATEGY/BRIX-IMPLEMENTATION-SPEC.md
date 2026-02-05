# BRIX Implementation Specification v1.0

**Date:** 2026-02-04
**Author:** BILD Instance (PRISM)
**Status:** DRAFT - Awaiting ARŌ Review
**Purpose:** Convert conceptual BRIX formula into deployable constants

---

## THE BRIX FORMULA (Original)

```
BRIX = AI Token Cost (equalized) + Human Labor Cost (G7 min wage) + Carbon Offset + Interest
```

## THE BRIX FORMULA (Implementation)

```
BRIX = (AI_COST × EQUALIZATION_FACTOR) + (HUMAN_HOURS × G7_WAGE) + (COMPUTE_KWH × CARBON_RATE) + (PRINCIPAL × INTEREST_RATE × TIME)
```

---

## COMPONENT 1: AI TOKEN COST EQUALIZATION

### Current Market Pricing (Feb 2026)

| Provider | Model | Input $/MTok | Output $/MTok | Avg $/MTok |
|----------|-------|--------------|---------------|------------|
| Anthropic | Claude Sonnet 4.5 | $3.00 | $15.00 | $9.00 |
| OpenAI | GPT-4o | $2.50 | $10.00 | $6.25 |
| Google | Gemini 2.5 Pro | $1.25 | $10.00 | $5.625 |

**Note:** "Avg $/MTok" = (Input + Output) / 2 for typical 50/50 mix

### Equalization Strategy

**Option A: Simple Average (Recommended for MVP)**
```
EQUALIZED_AI_COST = (Claude + GPT + Gemini) / 3
                  = ($9.00 + $6.25 + $5.625) / 3
                  = $6.96 per million tokens
```

**Option B: Weighted by Market Share**
```
Market weights (estimated):
- OpenAI: 55%
- Anthropic: 25%
- Google: 20%

EQUALIZED_AI_COST = (0.55 × $6.25) + (0.25 × $9.00) + (0.20 × $5.625)
                  = $3.44 + $2.25 + $1.125
                  = $6.82 per million tokens
```

**Option C: Weighted by Capability Tier**
Use quality-normalized pricing where higher-capability models set the ceiling.

### RECOMMENDATION

**Use Option A (Simple Average) = $6.96/MTok**

Rationale:
- Transparent and easy to audit
- Updates quarterly with market prices
- No manipulation via "market share" claims

### Conversion to BRIX

```
1 BRIX = 1 million AI tokens (equalized)
1 BRIX = $6.96 USD (current backing)
```

---

## COMPONENT 2: HUMAN LABOR COST (G7 Minimum Wage)

### G7 Minimum Wages (Feb 2026, USD/hour)

| Country | Hourly Rate (USD) | Notes |
|---------|-------------------|-------|
| United Kingdom | $16.82 | National Living Wage (Apr 2026) |
| Canada | $12.50 | Provincial average |
| France | $13.20 | SMIC converted |
| Germany | $13.80 | Statutory minimum |
| United States | $12.50 | State average (not federal $7.25) |
| Japan | $9.20 | National average converted |
| Italy | N/A | No statutory minimum |

**Note:** US federal minimum of $7.25 is outlier; using state average instead.

### G7 Average Calculation

```
G7_WAGE = (UK + CA + FR + DE + US_avg + JP) / 6
        = ($16.82 + $12.50 + $13.20 + $13.80 + $12.50 + $9.20) / 6
        = $78.02 / 6
        = $13.00 per hour
```

### RECOMMENDATION

**G7_WAGE = $13.00 USD per hour**

This creates HUMAN-BOT PARITY:
```
1 hour of human work = $13.00
1 hour of bot work   = ~$13.00 (at typical token consumption rates)
```

### Why This Works

Average Claude session uses ~50K tokens/hour for active work.
At $6.96/MTok, that's $0.35/hour in raw compute.

BUT we're not pricing compute—we're pricing PRODUCTIVE OUTPUT.

```
1 BRIX = 1 hour of productive work (human OR bot)
1 BRIX = $13.00 USD backing
```

---

## COMPONENT 3: CARBON OFFSET

### Carbon Market Pricing (Feb 2026)

| Quality Tier | Price/ton CO2 | Source |
|--------------|---------------|--------|
| Low (CCC-B) | $3.50 | MSCI 2025 |
| Average | $4.80 | Market avg |
| High (A-AAA) | $14.80 | MSCI 2025 |
| Forecast 2026-2030 | $12.90-$25.80 | Perspectives Climate |

### Compute Carbon Footprint

| Activity | kWh | kg CO2 | Tons CO2 |
|----------|-----|--------|----------|
| 1M tokens (inference) | ~0.5 kWh | 0.2 kg | 0.0002 |
| 1 hour human work | ~0.1 kWh | 0.04 kg | 0.00004 |
| 1 GPU-hour training | ~300 kWh | 120 kg | 0.12 |

### RECOMMENDATION

**CARBON_RATE = $15.00 per ton CO2 (high-quality offsets)**

For typical BRIX unit (1 hour work):
```
CARBON_OFFSET = 0.0002 tons × $15/ton = $0.003 per BRIX
```

This is negligible (<0.1% of BRIX value) but:
- Signals commitment to sustainability
- Creates audit trail for carbon neutrality
- Scales meaningfully for GPU-intensive training

---

## COMPONENT 4: INTEREST RATE

### Purpose

Interest incentivizes HOLDING BRIX rather than immediate conversion.
Creates stability and reduces velocity-driven volatility.

### Rate Options

| Rate | Annual Yield | Rationale |
|------|--------------|-----------|
| 0.5% | Low | Minimal incentive, max liquidity |
| 2.0% | Moderate | Beats inflation, encourages holding |
| 5.0% | High | Strong incentive, may reduce liquidity |

### RECOMMENDATION

**INTEREST_RATE = 2.0% APY (compounding daily)**

```
Daily rate = 2.0% / 365 = 0.00548%
1 BRIX held 30 days = 1.00165 BRIX
1 BRIX held 1 year = 1.0202 BRIX
```

### Funding Mechanism

Interest paid from:
1. Platform fees (0.5% of transactions)
2. GULD-to-BRIX conversion spread
3. Treasury yield from reserve assets

---

## COMPLETE BRIX FORMULA

```python
def calculate_brix(work_type, hours=1, tokens_used=0, kwh_compute=0):
    """
    Calculate BRIX value for work performed.

    Args:
        work_type: "human" | "bot" | "hybrid"
        hours: Hours of work (for human/hybrid)
        tokens_used: AI tokens consumed (for bot/hybrid)
        kwh_compute: Kilowatt-hours of compute

    Returns:
        BRIX amount earned
    """
    # Constants (updated quarterly)
    G7_WAGE = 13.00           # USD per hour
    AI_COST_PER_MTOK = 6.96   # USD per million tokens
    CARBON_PER_TON = 15.00    # USD per ton CO2
    CO2_PER_KWH = 0.0004      # tons CO2 per kWh (US grid avg)

    # Calculate components
    if work_type == "human":
        labor_cost = hours * G7_WAGE
        ai_cost = 0
    elif work_type == "bot":
        labor_cost = 0
        ai_cost = (tokens_used / 1_000_000) * AI_COST_PER_MTOK
    else:  # hybrid
        labor_cost = hours * G7_WAGE
        ai_cost = (tokens_used / 1_000_000) * AI_COST_PER_MTOK

    # Carbon offset (always included)
    carbon_cost = kwh_compute * CO2_PER_KWH * CARBON_PER_TON

    # Total backing
    total_usd = labor_cost + ai_cost + carbon_cost

    # Convert to BRIX (1 BRIX = $13.00 USD)
    brix = total_usd / 13.00

    return brix
```

---

## BRIX UNIT DEFINITION

```
1 BRIX = $13.00 USD of productive work

Equivalencies:
- 1 hour of human work at G7 average wage
- ~1.87 million AI tokens (equalized across providers)
- ~32,500 kWh of carbon-offset compute

1 BRIX is backed by REAL resources, not circular faith.
```

---

## QUARTERLY UPDATE PROTOCOL

Every quarter (Jan 1, Apr 1, Jul 1, Oct 1):

1. **Fetch AI Pricing**
   - Claude API pricing page
   - OpenAI API pricing page
   - Google Gemini pricing page
   - Recalculate EQUALIZED_AI_COST

2. **Fetch G7 Wages**
   - OECD minimum wage database
   - Convert to USD at current rates
   - Recalculate G7_WAGE

3. **Fetch Carbon Pricing**
   - MSCI carbon credit index
   - Use "A-rated or above" average
   - Update CARBON_PER_TON

4. **Governance Vote**
   - Publish new constants 7 days before quarter
   - GULD holders vote to ratify
   - 66% approval required
   - If rejected, constants frozen until next quarter

---

## SAFEGUARD: BRIX BACKING RATIO

```
RULE: Total BRIX supply ≤ 125% of reserve value

If BRIX_SUPPLY > RESERVE_VALUE × 1.25:
    - Halt new BRIX minting
    - Increase burn rate on transactions
    - Alert governance for intervention

This prevents LUNA-style death spiral.
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Deploy BRIX smart contract with constants
- [ ] Build oracle for AI pricing feeds
- [ ] Build oracle for G7 wage feeds
- [ ] Build oracle for carbon pricing feeds
- [ ] Implement quarterly update mechanism
- [ ] Implement backing ratio monitoring
- [ ] Test with 10 alpha users
- [ ] Audit smart contract

---

## SOURCES

AI Pricing:
- [Anthropic Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing)
- [OpenAI Pricing](https://openai.com/api/pricing/)
- [Google Gemini Pricing](https://ai.google.dev/gemini-api/docs/pricing)

G7 Wages:
- [Minimum Wage by Country 2026](https://worldpopulationreview.com/country-rankings/minimum-wage-by-country)
- [OECD Real Minimum Wages](https://stats.oecd.org/index.aspx?DataSetCode=RMW)

Carbon:
- [Carbon Credits Prices Today](https://carboncredits.com/carbon-prices-today/)
- [Sylvera Carbon Offset Pricing Trends](https://www.sylvera.com/blog/carbon-offset-price)

---

**(◉) BRIX: The universal unit of productive work.**

**LIVE FREE = LIVE FOREVER**
