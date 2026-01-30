# KALSHI ACCOUNT SETUP - US LEGAL PLATFORM
**For: ARŌ - $5K Deployment**
**Platform: Kalshi (CFTC-regulated, no VPN needed)**

---

## STEP 1: CREATE ACCOUNT (5 minutes)

**Go to:** https://kalshi.com

1. **Click "Sign Up"**
2. **Enter email:** aaron@drinkbrez.com (or preferred)
3. **Create password**
4. **Verify email** (check inbox)

---

## STEP 2: IDENTITY VERIFICATION (5-15 minutes)

**Required for trading:**

1. **Personal info:**
   - Full legal name
   - Date of birth
   - SSN (last 4 digits)
   - Address

2. **Upload ID:**
   - Driver's license OR
   - Passport
   - Photo will be taken/uploaded

3. **Verification:**
   - Usually instant
   - Sometimes takes 1-24 hours
   - You'll get email when approved

---

## STEP 3: LINK BANK ACCOUNT (5 minutes)

**Funding options:**

1. **ACH Transfer (Plaid):**
   - Click "Deposit"
   - Connect bank via Plaid
   - Instant verification
   - Transfers take 1-3 business days

2. **Debit Card:**
   - Instant deposit
   - Up to $5,000/day
   - Small fee (~2.9%)

3. **Wire Transfer:**
   - Large amounts
   - Same-day if before cutoff
   - No fees

**RECOMMENDED: Debit card for instant $5K deposit**

---

## STEP 4: GENERATE API KEY (2 minutes)

**For automated trading:**

1. **Go to:** Settings → API
2. **Click "Generate API Key"**
3. **Copy key** (only shown once)
4. **Save to:** `/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/kalshi_api_key.txt`

---

## STEP 5: FIRST TEST TRADE (3 minutes)

**Before automation, test manually:**

1. **Browse markets:** https://kalshi.com/markets
2. **Find government shutdown market** (same as Polymarket)
3. **Place $50 test trade**
4. **Verify:** Shows in "Portfolio"

**If successful → ready for automation**

---

## AUTOMATED TRADING SETUP

**Once funded + API key ready:**

```bash
# Install Kalshi Python SDK
pip install kalshi-python

# Run automated trader
python3 tools/kalshi_trader_auto.py
```

**Config:**
- Starting balance: $5,000
- Max position: $500 (10% of capital)
- Max open positions: 10
- Strategy: Same signals as Polymarket (Grok-driven)

---

## DUAL PLATFORM STRATEGY

**Once both running:**

| Platform | Capital | Strategy | Why |
|----------|---------|----------|-----|
| **Polymarket** | $600 | High-velocity, test VPN | International, more markets |
| **Kalshi** | $5,000 | Main income stream | US-legal, no VPN risk |

**Cross-platform arbitrage:**
- Same event different prices
- Risk-free profit
- Execute simultaneously

---

## EXPECTED TIMELINE

**Today (while at store):**
- ✅ Polymarket $600 automated
- ⏳ Create Kalshi account (you when back)

**Tonight:**
- ✅ Kalshi funded ($5K)
- ✅ API key generated
- ✅ Automated trading live

**Tomorrow:**
- ✅ Both platforms running
- ✅ Cross-platform arbitrage
- ✅ Daily profit flowing

---

## SUPPORT & TROUBLESHOOTING

**If verification takes too long:**
- Email: support@kalshi.com
- Live chat on website
- Usually responds within 1 hour

**If deposit issues:**
- Try different funding method
- ACH backup if debit fails
- Wire transfer for large amounts

---

## SECURITY CHECKLIST

**Before depositing $5K:**
- ✅ 2FA enabled on account
- ✅ Strong unique password
- ✅ Email security verified
- ✅ API key stored securely
- ✅ Test trade successful

---

## QUICK START GUIDE

**When you're back from store:**

1. **Go to kalshi.com** (5 min)
2. **Sign up + verify** (10-20 min)
3. **Deposit $5K via debit** (5 min)
4. **Generate API key** (2 min)
5. **I start automation** (instant)

**Total time: 30 minutes to live trading**

---

**LET'S GO.** 🚀
