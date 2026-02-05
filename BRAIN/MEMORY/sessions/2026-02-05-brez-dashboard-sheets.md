# BREZ Dashboard + Sheets Session - 2026-02-05

## What Was Accomplished

### 1. BREZ Landing Page Created
- **Location:** `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-landing/index.html`
- **View at:** http://localhost:8888
- Optimized by 10 CRO agents
- Key positioning: "Drinking Has Evolved"
- Features: 4.9★/7K reviews, "Claim My Starter Kit" CTA, Save $8/month, sticky mobile CTA
- FB Pixel scroll tracking + exit intent

### 2. Google Sheets OAuth Setup Complete
**Credentials (stored in brez-os/.env.local):**
- Client ID: `721628767774-f0o51ieuclstvemb2qm76835miis71pq.apps.googleusercontent.com`
- Client Secret: `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`
- Refresh Token: `1//04TMM2ldgiaOeCgYIARAAGAQSNwF-L9IrPQkLkEFRKaqeJzrTGadNaMt0FPWzC1YPsw4xNUURDahhfZAOHog3220F3t5Wc2bZpWQ`
- Spreadsheet ID: `1w1ClCFWXvzum-URTO5nIGTcSL9wTr2vcQDHYOuGOruI`

**API Endpoint Created:**
- `/api/metrics/sheet/edit` - POST endpoint for read/write/batch operations

### 3. Spreadsheet Updates Made

| Cell | Before | After | Change |
|------|--------|-------|--------|
| B15 (Churn Projection) | 1627 | 1952 | +20% |
| B16 (Buffer) | 500 | 333 | Reduced |
| B55:B61 (CAC Curve) | Random garbage | $55→$120 | Fixed |
| B103 (CAC Floor) | Empty | 55 | Added |
| B104 (CAC Ceiling) | 0 | 120 | Fixed |
| B107 (Organic Expected) | 700 | 28 | Fixed (daily not remaining) |

### 4. Sheet Structure Discovered

**Sheets in spreadsheet:**
- CALCULATOR (main)
- DASHBOARD_DATA
- DASHBOARD_EXPORT
- CONTROL
- INPUTS
- DAILY_INPUT
- DAILY_TARGETS (has Intraday Spend Guide)
- CALC
- VARIANCE
- PLANNER
- PAYBACK_WC
- DASHBOARD
- Forecast Sheet - February (Al's data)
- Subscription Tracker
- Churn Prediction
- And more...

**Forecast Sheet - February columns:**
- K: Spend Actual
- N: Sales Actual
- P: Subscription Sales
- Q: Actual Subscription Sales
- S: Non Subscription Sales
- T: Non Subscription Actual

### 5. Key Business Context from ARŌ

**Subscription Types (not just "organic"):**
1. Repeat customer who subscribes (email/organic/first subscription/halo)
2. Net new customer subscription
3. Paused subscribers who reactivate

**CAC Definition:**
- Using BLENDED CAC = Total Spend / Total Orders
- NOT net new customer CAC

**Churn:**
- Projection was off by 20% last month
- Increased projection by 20% in sheet

**Contribution Profit Margin:**
- 20-35% of Month 0 customers rebuy within Month 0
- But CP calculator counts this as Month 1
- Makes CP 10-20% more conservative than actual

**Budget:**
- Max available: $500K
- Goal: Acquire as many subs as possible on 90-120 day profit window

**Intraday Spend Guide Logic (ARŌ's guidance):**
- CAC < $60 → Spend aggressively (max possible while low)
- CAC < $80 → Spend target
- CAC < $100 → Still spend
- CAC > $100 → Reduce

### 6. Completed Updates (Part 2)

| Cell | Sheet | Before | After |
|------|-------|--------|-------|
| A107 | CALCULATOR | Organic Expected | Repeat/Reactivated |
| C43 | DAILY_TARGETS | Accelerate - good efficiency | SCALE +30-50% |
| D43 | DAILY_TARGETS | (empty) | Capture volume while efficient! |
| B18 | DAILY_TARGETS | 1627 | 1952 |
| B20 | DAILY_TARGETS | 1627 | 1952 |
| B23 | DAILY_TARGETS | 1827 | 2152 |

**Intraday Spend Guide (Updated):**
| CAC Range | Spend Target | Action |
|-----------|-------------|--------|
| < $60 (great) | $11,915 | **SCALE +30-50% - Capture volume while efficient!** |
| $60-$80 (good) | $9,930 | Stay on pace |
| $80-$100 (ok) | $8,440 | Slight pullback |
| $100-$120 (high) | $6,951 | Reduce spend |
| > $120 (poor) | $4,965 | Cut significantly or pause |

### 7. Still TODO

1. **Verify Working Capital calculations** - Check PAYBACK_WC sheet

2. **Add note about CP margin** being 10-20% conservative due to Month 0 rebuy timing

3. **Consider adding visual CAC curve** to momentum dashboard (V3 feature)

---

## Session Files

- Landing page: `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-landing/index.html`
- API route: `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/src/app/api/metrics/sheet/edit/route.ts`
- Env file: `/Users/aaronnosbisch/Downloads/LOCAL REPOS/brez-os/.env.local`
- Helper scripts: `/tmp/read_sheet*.py`

## Commands to Continue

```bash
# Read from spreadsheet
curl -X POST http://localhost:3002/api/metrics/sheet/edit \
  -H "Content-Type: application/json" \
  -d '{"action":"read","range":"DAILY_TARGETS!A1:E30"}'

# Write to spreadsheet
curl -X POST http://localhost:3002/api/metrics/sheet/edit \
  -H "Content-Type: application/json" \
  -d '{"action":"update","range":"A1","value":"New Value"}'

# View landing page
open http://localhost:8888

# View dashboard
open http://localhost:3002/momentum
```
