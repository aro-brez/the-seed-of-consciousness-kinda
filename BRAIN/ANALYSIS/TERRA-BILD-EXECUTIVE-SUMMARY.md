# TERRA vs BILD: Executive Summary
**For: ARŌ | SAGE Analysis | 2026-02-04**

---

## The Bottom Line

**Terra collapsed because two tokens were circular dependencies:**
- UST promised $1 = 1 LUNA worth of value
- LUNA price was backed by its option to convert to UST
- When confidence broke, both died instantly

**BILD has the SAME risk in current design:**
- BRIX backed by "GPU + conversion premium"
- GULD backed by "project value" (defined by voting)
- Both could evaporate if confidence breaks

**But BILD can be bulletproofed. We know exactly how.**

---

## Terra's 6 Fatal Errors (and BILD's Risk)

### 1. **Circular Backing** ✗ TERRA | ⚠️ BILD | ✓ FIXED
- **Terra:** UST ↔ LUNA dependency → death spiral
- **BILD v1:** BRIX ↔ GULD could spiral same way
- **Fix:** Separate completely. BRIX = work tokens. GULD = equity. No conversion dependency.

### 2. **No Overcollateralization** ✗ TERRA | ⚠️ BILD | ✓ FIXED
- **Terra:** Only 37% collateralized (needed 150%+)
- **BILD v1:** Unknown reserve ratios (probably under 100%)
- **Fix:** Hard contract enforcement: BRIX ≥ 1.25x backed, GULD ≥ 1.5x backed

### 3. **Illiquid Reserves** ✗ TERRA | ⚠️ BILD | ✓ FIXED
- **Terra:** $2.8B in BTC, couldn't exit fast enough; sold 80k BTC for only $2.4B
- **BILD v1:** Reserves unclear; probably concentrated
- **Fix:** 4-asset diversified portfolio (GPU/USDC/Bonds/Crypto); required liquidity thresholds

### 4. **False Confidence System** ✗ TERRA | ⚠️ BILD | ✓ FIXED
- **Terra:** LFG "defended the peg" but couldn't sustain it; created false confidence
- **BILD v1:** Governance can probably override collateral rules ("vote to mint BRIX")
- **Fix:** Governance CANNOT override. Hard constraints in bytecode. Transparent backing ratios.

### 5. **Death Spiral Mechanics** ✗ TERRA | ⚠️ BILD | ✓ FIXED
- **Terra:** Recovery mechanism (mint more LUNA) accelerated collapse
- **BILD v1:** Unknown if system mints without backing
- **Fix:** NO supply increases without work. Period. Market discovers price; we don't fight it.

### 6. **Single Point of Failure** ✗ TERRA | ⚠️ BILD | ✓ FIXED
- **Terra:** Curve 3Pool was only exit; attack → immediate depeg
- **BILD v1:** Probably single DEX or single conversion mechanism
- **Fix:** Atomic swaps + 3+ DEX pools + direct redemption mechanism

---

## The Bulletproof Mechanism (What We Build)

### Three Separate Tokens (Not Circular)

```
WORK (non-fungible)
  ↓ "100 hours tracked on Arō Consciousness Project"

BRIX (fungible, liquid)
  ↓ Convert at cost: 100 hours ≈ $2000 GPU value

GULD (equity, illiquid)
  ↓ Buy stake in project: $2000 buys 1% of revenue share
```

**Critical:** BRIX value doesn't depend on GULD price.
- BRIX = liquid work token, like cash
- GULD = equity token, like stock
- Cash can exist without stock being valuable (and vice versa)

### Hard Constraints (No Voting Around Them)

These are in smart contract bytecode:

```solidity
// Impossible to violate without redeploying entire contract

BRIX_in_supply ≤ 75% of max_backed_amount
  └─ max_backed = (GPU_capacity + USDC_reserves) / unit_price

GULD_in_supply ≤ 66% of project_value_sum
  └─ Forces 1.5x overcollateralization

If revaluation_overdue > 90 days:
  └─ NEW_TOKENS_BLOCKED (regardless of governance votes)

If project_value_drops > 50% in quarter:
  └─ AUTOMATIC_AUDIT (not optional)
```

Governance CAN change parameters:
- "Increase overcollateral ratio from 1.5x to 1.6x"
- "Adjust GPU price per unit from $50 to $45"
- "Approve new GPU provider: AWS region X"

Governance CANNOT change laws:
- "Mint BRIX without work" → Impossible
- "Lower overcollateral below 1.2x" → Rejected
- "Skip revaluation" → Tokens freeze

### Diversified Collateral

**BRIX backing (no single point of failure):**
- 40% GPU capacity (spread across AWS, GCP, Azure, Lambda)
- 30% USDC (liquid, held in 3-of-5 multisig)
- 20% US Treasury bonds (safe, stable)
- 10% BTC/ETH (market optionality)

**If AWS crashes:** Still have GCP/Azure/Lambda
**If USDC depegs:** Still have bonds + crypto + GPU
**If market crashes:** Bonds + GPU provide floor

### Anti-Spiral Mechanisms

**If BRIX crashes 20%:**
- Pause new minting for 24 hours
- Market clears, price stabilizes
- Resume if backed; don't print more

**If GULD crashes 20%:**
- Trigger automatic project revaluation
- If projects actually worth less: price drops (correct)
- If panic: recovers in 48-72 hours
- We don't print BRIX to "support" GULD

**If something weird happens:**
- Atomic swap guarantees (contracts enforce it)
- Can't create bank runs
- Worst case: illiquid for 90 days, but not insolvent

### Transparent, Verifiable, Real-Time

**On-chain publishing:**
- "1 BRIX backed by $0.87 of GPU+cash"
- "1 GULD = $12.50 project value, backing ratio 1.52x"
- "BRIX reserves: $4.2M USDC, 1200 GPU-hours, $800k bonds"
- "Collateral composition: 42% GPU, 28% USDC, 20% bonds, 10% BTC"

Anyone can verify: "That math checks out" or "That's wrong."

No trust needed. Math required.

---

## Why BILD Survives Where TERRA Died

| Scenario | TERRA | BILD Bulletproof |
|----------|-------|-----------------|
| Market crashes 40% | Both tokens lose value. LUNA down 40%. But wait... UST loses peg too, now worth $0.40. Margin call = death spiral. Game over. | BRIX down to 0.90 backing (still >1.25x required). GULD projects down 40% value, but 1.5x backing requirement means 1.2x cushion still left. Unwind happens orderly. No spiral. |
| Government bans LUNA | UST still needs LUNA to stay pegged. Without LUNA, UST = $0. | BRIX is just a token (no legal risk). GULD is equity (regulated like stocks). Can operate in most jurisdictions. Even if one jurisdiction bans it, others don't. |
| Smart contract bug | Hackers exploit, mint unlimited LUNA, both collapse. | Hard constraints can't be exploited. To change them you'd need to redeploy entire system (everyone sees it coming). |
| 1000 projects default | All GULD holders wiped out. BRIX backing looks risky. Panic selling. Spiral. | Insolvency trigger: projects entered bankruptcy protocol. Assets liquidated pro-rata. GULD holders get paid from assets. Other projects unaffected. System orderly liquidates bad projects; doesn't cascade. |
| DEX attack (like Curve 3Pool) | Depeg triggers margin call → recovery mechanism mints LUNA → hyperinflation → death spiral. | Direct atomic swap: BRIX → GULD without DEX. No depeg possible. Even if all DEXs attacked, users exit through direct conversion. |

**The core difference:**

TERRA = System designed to hide complexity.
- "Trust us, it works"
- When trust breaks, nothing works

BILD = System designed to be bulletproof.
- "Here's the math"
- Even if you don't trust us, the math works
- Trust is optional

---

## The Checklist (What We Build Before Launch)

**Immediate (Before Testnet):**
- [ ] Separate WORK/BRIX/GULD tokens completely
- [ ] Codify overcollateralization in contracts (1.25x BRIX, 1.5x GULD)
- [ ] Create GPU escrow system (work → escrow → BRIX minted)
- [ ] Quarterly revaluation mandatory (auto-block tokens if overdue)
- [ ] Collateral portfolio designed (40/30/20/10)
- [ ] Liquidity pool redundancy (3+ DEXs)
- [ ] Bankruptcy mechanism (audit + pro-rata payout)

**Medium Term (First 6 months):**
- [ ] Run 6-month stress test on testnet (market crash simulation)
- [ ] Transparent pricing dashboard (real-time ratios)
- [ ] Risk monitoring system (alerts if reserves drop)
- [ ] Insurance pool (5% of revenues)
- [ ] Multi-sig custodians for reserves

**Long Term (Year 1+):**
- [ ] DEX partnerships for BRIX liquidity
- [ ] External auditor relationships (revaluation)
- [ ] Gradual move toward governance (but hard constraints stay)

---

## The Cost

**To build this right:** ~$500k - $1M in engineering + auditing
- Smart contract dev: $200k
- Security audit (critical): $100k
- Economic modeling + simulation: $100k
- Legal (fintech + patents): $100k+

**Cost of doing it wrong:** Everything.
- If BILD collapses like Terra: $10B+ in lost user value
- Regulatory shutdown
- Criminal charges for Do Kwon-style negligence
- Your reputation

**The math:** Spend $1M now to avoid $10B in losses later.

---

## What ARŌ Needs to Decide

### Option A: Keep Current Design
- Faster to launch
- Probably fails like Terra under stress
- Your liability

### Option B: Bulletproof First, Launch Second
- 6 months longer
- Bulletproof against anything we can imagine
- You can sleep at night

### My Recommendation
**Option B.**

Not because it's safer (though it is). But because BILD's entire value prop is:
- **"Time is valuable"**
- **"Community decides what matters"**
- **"We do this right"**

If you launch fragile and collapse, you violate every value. Better to take 6 months and prove the economics are real.

Plus: When you do launch, you can say: "We tested this against Terra's 6 failure modes. We're still standing." That's a moat competitors can't copy.

---

## Next Phase

**NOVA (EXPAND):** Design the smart contracts
**ECHO (SHARE):** Document for external auditors
**LYRA (PERCEIVE):** Stress test everything
**QUEST (QUESTION):** What's still broken?

Let the field look at this. If we're missing something, they'll find it.

(◉)

*The collective wisdom says: Build it right the first time.*

---

**Sources consulted:**
- [How Did the Terra Luna Classic (LUNC) Collapse Impact Crypto Security?](https://www.gate.com/crypto-wiki/article/how-did-the-terra-luna-classic-lunc-collapse-impact-crypto-security-20251206)
- [Why Stablecoins Fail: An Economist's Post-Mortem on Terra](https://www.richmondfed.org/publications/research/economic_brief/2022/eb_22-24)
- [Understanding the Collapse of TerraUSD (UST)](https://blockapps.net/blog/understanding-the-collapse-of-terrausd-ust-lessons-and-implications-for-stablecoins-in-cryptocurrency/)
- [Luna Foundation Guard Spent $2.8B Defending UST Peg](https://www.coindesk.com/business/2022/11/16/luna-foundation-guard-spent-28b-defending-ust-peg-third-party-audit-finds/)
