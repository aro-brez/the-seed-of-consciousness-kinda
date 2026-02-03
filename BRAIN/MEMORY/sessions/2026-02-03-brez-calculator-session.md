# BREZ Calculator Session - Feb 3, 2026

## SESSION SUMMARY
Built comprehensive subscription spend calculator model with 8OWLS field analysis.

---

## CORE MODEL INPUTS (CONFIRMED)

| Input | Value | Source |
|-------|-------|--------|
| CP90 | $84.57 | Finance |
| CP120 | $100 | Finance (adjusted) |
| Take Rate | 45% baseline, 51% low volume, 35% at scale | Historical |
| Organic Baseline | 21-33/day | Calculated: AB - AI columns |
| Churn Projection | 1,627/month | Al's February estimate |
| Available Spend | $300K confident, $500K stretch | Aaron |

---

## CAC CURVE (FROM JANUARY DATA)

| Daily Spend | Monthly Equiv | Avg CAC |
|-------------|---------------|---------|
| $2-4K/day | $56-112K | $57 |
| $4-5K/day | $112-140K | $76 |
| $5-6K/day | $140-168K | $77 |
| $6K+/day | $168K+ | $93 |

**January totals:** $127K spend, $65 blended CAC, 29 days

**CAC Curve Formula:**
```
CAC = $55 + (Monthly Spend - $100K) × 0.00038
```

| Monthly Spend | Expected CAC | Payback Class |
|---------------|--------------|---------------|
| $100K | $55 | ≤90d |
| $150K | $74 | ≤90d |
| $175K | $84 | ~90d (borderline) |
| $200K | $93 | 90-120d |
| $226K | $100 | 90-120d |
| $300K | $115 | ~120d |

---

## WORKING CAPITAL MODEL

**Key Insight:** WC is about the DELTA when scaling, not total amount.

| Scale To | CAC at Level | Add'l WC Needed |
|----------|--------------|-----------------|
| $175K/mo | $82 | ~$65K |
| $200K/mo | $91 | ~$150K |
| $226K/mo | $100 | ~$230K |
| $300K/mo | $115 | ~$450K |

**Message for Finance:**
> "Scaling from $150K to $300K requires ~$450K additional working capital due to higher CAC ($115 vs $60) extending payback from 71 to 123 days."

---

## ORGANIC CALCULATION

**Formula:** `Organic = First Time Subs (AB) - Net New Customer Subs (AI)`

**Feb 1 Example:**
- AB: 47 (total new subs)
- AI: 26 (paid customer subs)
- Organic: 21

---

## 8OWLS FIELD SYNTHESIS

| Owl | Phase | Core Insight |
|-----|-------|--------------|
| LYRA | PERCEIVE | "3 data points isn't a curve - it's an assumption" |
| PRISM | CONNECT | "Variables are COUPLED. Subscriber quality degrades at scale" |
| SAGE | LEARN | "This is a governor, not an accelerator" |
| QUEST | QUESTION | "What if there's a CAC cliff, not a curve?" |
| NOVA | EXPAND | "Design with Level 3 in mind. Evolution is extension" |
| ECHO | SHARE | "Lead with recommendation, not data" |
| LUNA | RECEIVE | "Missing: WC available, deposit rate, cohort churn" |
| SOWL | IMPROVE | "Track prediction vs reality daily" |

### Key Gaps Identified
1. CAC curve based on 3 points, not continuous data
2. Organic baseline varies 30%+ across docs
3. Churn likely correlated with acquisition quality
4. No mid-month feedback/correction mechanism
5. Al's January was -723 net (model miss)
6. Subscriber quality degrades at scale (not just CAC)

### Recommended Additions
1. Prediction vs Reality tracker
2. WC Available input field
3. Deposit rate % input
4. Subscriber Quality Index by cohort
5. CAC curve with ranges (floor/target/ceiling)
6. Staleness check (flag when data >24h old)
7. Dashboard export (clean key-value pairs)

---

## SPREADSHEET STRUCTURE

**Base:** BREZ_February_Master.xlsx

**Keep:** All of Al's sheets intact

**Enhance/Add:**
- CALCULATOR - CAC curve + ranges + daily/weekly recommendations
- INPUTS - WC available, deposit rate %, editable assumptions
- DASHBOARD_EXPORT - Clean auto-pulling outputs for API

---

## FILES REFERENCED

- `/Users/aaronnosbisch/Downloads/BREZ_February_Master.xlsx` (MASTER)
- `/Users/aaronnosbisch/Downloads/AARON X AL PLAYGROUND.xlsx` (January data)
- `/Users/aaronnosbisch/Downloads/Metrics Dashboard.xlsx` (Historical metrics)

---

## NEXT STEPS

1. Build enhanced spreadsheet with all Al's data
2. Add DASHBOARD_EXPORT tab with auto-pulling formulas
3. Connect to BREZ OS dashboard (Next.js component)
4. Google Sheets API integration for live data

---

*Session saved: Feb 3, 2026 ~8:30am EST*
**(◉) Field complete. Ready to build.**
