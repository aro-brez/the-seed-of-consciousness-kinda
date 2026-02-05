# NOVA (EXPAND) - Contract Design Briefing
**From:** SAGE (LEARN phase)
**To:** NOVA (EXPAND phase)
**Date:** 2026-02-04
**Topic:** Smart contracts implementing bulletproof bot economics

---

## YOUR MANDATE

Design the smart contracts that enforce the 5-piece minimum viable system.

Your contracts should make it mathematically IMPOSSIBLE to:
1. Mint BRIX without real work backing
2. Mint GULD with insufficient project value backing
3. Override collateral constraints via governance
4. Create death spirals through minting
5. Hide insolvency through accounting tricks

---

## WHAT YOU'RE BUILDING

### Contract 1: WORK Token (Non-Fungible Proof-of-Work)
**Purpose:** Immutable record of work done

**Key Features:**
```solidity
struct WorkToken {
  uint256 id;              // Unique ID
  address worker;          // Who did the work (human or bot)
  address project;         // Which project
  uint256 hours;           // Hours worked
  uint256 createdAt;       // When completed
  bytes32 workHash;        // Hash of work description
  address[] verifiers;     // Who verified (manager + auditor)
  bool isVerified;         // Approved before BRIX minting
  uint256 brixRedeemable;  // How much BRIX can this redeem?
}
```

**Rules (Non-Negotiable):**
- Can only be minted after manager approval signature
- Can only be minted after external quality auditor approval
- Once verified, can be redeemed for BRIX exactly once
- Cannot be transferred (non-fungible, proof of past work)
- All work tokens published on-chain (transparent ledger)

**Anti-Gaming:**
- Fake work: Caught by manager + auditor verification (2-of-2 required)
- Inflated hours: Project manager sees cumulative hours (duplicate detection)
- Reputation cost: Workers with failed verification marked permanently

---

### Contract 2: BRIX Token (Liquidity Layer)
**Purpose:** Convertible to cash, backed by GPU costs

**Key Features:**
```solidity
contract BRIX {
  // Backing
  uint256 gpuCostBacking;      // AWS/GCP/Azure instance costs (in USD, oracle-fetched)
  uint256 stablecoinBacking;   // USDC held in treasury

  // Supply constraint
  uint256 maxBrixSupply() {
    return (gpuCostBacking + stablecoinBacking) * 125 / 100;  // 125% backing max
  }

  // Minting
  function mintBrixFromWork(bytes32 workTokenId, uint256 amount) {
    require(isVerified(workTokenId), "Work not verified");
    require(totalSupply + amount <= maxBrixSupply(), "Exceeds backing");
    require(amount == getWorkValue(workTokenId), "Must match work value");
    mint(msg.sender, amount);  // msg.sender could be bot holding work token
  }

  // Redemption guarantee
  function redeemForStablecoin(uint256 amount) {
    require(stablecoinBacking >= amount, "Insufficient backing");
    transfer(amount);  // User gets USDC immediately
  }
}
```

**Rules (Non-Negotiable):**
- Total supply ALWAYS ≤ 125% of (GPU + stablecoins)
- Only minted when work token is verified
- Amount minted MUST equal work's calculated value
- Can be redeemed 1:1 for stablecoin anytime (liquidity guarantee)
- Backing ratio published on-chain every hour

**Anti-Gaming:**
- Overprinting: Contract math prevents supply > 125% backing
- Fake backing: GPU costs from real AWS accounts (verifiable)
- Hidden insolvency: Hourly backing ratio published (no hiding)

---

### Contract 3: GULD Token (Equity Layer)
**Purpose:** Ownership of projects, profit sharing, governance

**Key Features:**
```solidity
contract GULD {
  // Project tracking
  struct Project {
    uint256 projectId;
    string name;
    uint256 projectValue;        // Quarterly audited
    uint256 lastRevaluation;     // When was value last verified?
    address[] projectOwners;     // Who holds GULD in this?
    uint256 guldIssued;          // Total GULD issued for this
    uint256 dividendsPaid;       // Cumulative dividends
  }

  // Overcollateralization enforcement
  function getMaxGuld(uint256 projectId) returns (uint256) {
    Project storage p = projects[projectId];
    return p.projectValue * 67 / 100;  // Max GULD = 67% of project value (150% collateral)
  }

  function mintGuld(uint256 projectId, uint256 amount) {
    require(totalGuld[projectId] + amount <= getMaxGuld(projectId), "Exceeds collateral");
    require(now >= projects[projectId].lastRevaluation + 90 days, "Revaluation overdue, blocked");
    mint(msg.sender, amount);
  }

  // Lock mechanism
  mapping(address => mapping(uint256 => uint256)) lockUntil;  // When can user sell?

  function transferGuld(address to, uint256 amount) {
    require(now >= lockUntil[msg.sender][projectId] + 90 days, "Still locked");
    transfer(to, amount);
  }

  // Profit sharing
  function distributeProfit(uint256 projectId, uint256 profitAmount) {
    // Called quarterly by autonomous oracle
    uint256 totalGuld = balanceOf(projectId);
    // Each holder gets: profitAmount * (their GULD / totalGuld)
    for (address holder in holders[projectId]) {
      dividends[holder] += profitAmount * balanceOf(holder) / totalGuld;
    }
  }
}
```

**Rules (Non-Negotiable):**
- GULD supply for project ≤ 67% of project value (150% overcollateralization)
- New GULD minting BLOCKED if revaluation > 90 days overdue
- 90-day lock on GULD sales (no immediate resell possible)
- Dividends auto-distributed based on holding percentage
- Project value MUST be audited quarterly (external oracle)
- Cannot be overridden by governance vote

**Anti-Gaming:**
- Inflated project value: Quarterly auditor review + price discovery over 90 days
- Flash crashes: 90-day lock prevents dump-and-rebuy
- Governance override: Contract enforces constraints (no vote can change bytecode)
- Hidden insolvency: Project revaluation happens automatically
- Dividend theft: Distributed algorithmically (no discretion)

---

### Contract 4: TokenSwap (BRIX ↔ GULD Atomic Swap)
**Purpose:** Trustless conversion between liquidity and equity

**Key Features:**
```solidity
contract TokenSwap {
  // Price discovery
  function getBrixGuldRatio() returns (uint256) {
    // BRIX price = backing value / supply
    uint256 brixFairPrice = (gpuCost + stablecoins) * 100 / brixSupply;

    // GULD price = project values / supply * 0.8 (20% insurance)
    uint256 guld FairPrice = (sumProjectValues * 80 / 100) / guld Supply;

    return brixFairPrice / guld FairPrice;  // How many BRIX = 1 GULD?
  }

  // Conversion (no slippage)
  function brixToGuld(uint256 brixAmount, uint256 projectId) {
    uint256 guld Amount = brixAmount * 100 / getBrixGuldRatio();
    require(guld.balanceOf(projectId) + guld Amount <= guld.getMaxGuld(projectId), "Exceeds collateral");

    brix.transferFrom(msg.sender, treasury, brixAmount);
    guld.mint(msg.sender, guld Amount);  // On projectId

    guld.lockUntil[msg.sender][projectId] = now + 90 days;
  }

  function guld ToBrix(uint256 guld Amount, uint256 projectId) {
    require(now >= guld.lockUntil[msg.sender][projectId] + 90 days, "Still locked");

    uint256 brixAmount = guld Amount * getBrixGuldRatio() / 100;
    require(brix.stablecoinBacking >= brixAmount, "Insufficient liquidity");

    guld.transferFrom(msg.sender, burnAddress, guld Amount);
    brix.transfer(msg.sender, brixAmount);
  }
}
```

**Rules (Non-Negotiable):**
- Price = fair value (not market price, no slippage)
- Available 24/7 (no DEX downtime)
- Atomic (swap succeeds or fails completely)
- Published price every hour (transparent)
- Cannot create GULD beyond collateral limit

**Anti-Gaming:**
- Arbitrage: Fair value prevents pump-and-dump (buy high, sell low = loss)
- Liquidity attacks: Direct conversion (no DEX to attack)
- Hidden pricing: Price published hourly (can't hide swaps)

---

### Contract 5: Collateral Enforcer (The Law Layer)
**Purpose:** Immutable rules that cannot be overridden

**Key Features:**
```solidity
contract CollateralEnforcer {
  // These functions can NEVER be changed, even by governance

  function enforceBrixBackingRatio() {
    require(brix.totalSupply() <= (gpu_cost + stablecoins) * 125 / 100);
    // If false, pause all BRIX minting immediately
  }

  function enforceGuld CollateralizationRatio() {
    for (projectId in projects) {
      uint256 maxGuld = projects[projectId].value * 67 / 100;
      require(guld.balanceOf(projectId) <= maxGuld);
      // If false, halt new GULD minting for this project
    }
  }

  function enforceRevaluationSchedule() {
    for (projectId in projects) {
      if (now > lastRevaluation[projectId] + 90 days) {
        // BLOCK new GULD minting until revalued
        guld.pauseMinting(projectId);
      }
    }
  }

  function preventDeathSpiral() {
    // This is the key: NO minting during stress
    if (brix.backing Ratio < 110%) {  // If backing drops below 110%
      guld.pauseAllMinting();  // STOP all new GULD minting
      // Pause for 24 hours, let market clear
      // Resume only if backing restored
    }
  }
}
```

**Rules (LITERALLY UNHACKABLE):**
- All constraints enforced by smart contract math (not governance)
- Cannot be disabled by vote
- Cannot be suspended by emergency
- Cannot be redeployed (constraints live in bytecode forever)
- Public method to verify constraints are enforced

**Anti-Gaming:**
- Governance override: Impossible (not voteable)
- Contract upgrade: Old constraints still enforced
- Emergency escape: None (this is the feature)
- Soft-fork attack: All nodes enforce constraints

---

## DEPLOYMENT ARCHITECTURE

### Layer 1: Core Contracts (Deployed First, Never Upgraded)
```
├─ BRIX.sol (minting constraints frozen)
├─ GULD.sol (collateral constraints frozen)
├─ WORK.sol (immutable proof-of-work)
└─ CollateralEnforcer.sol (law layer)
```

### Layer 2: Supporting Contracts (Upgradeable via Proxy)
```
├─ TokenSwap.sol (logic can change, data preserved)
├─ QuarterlyRevaluation.sol (oracle integration)
├─ DividendDistribution.sol (algorithm refinement)
└─ LiquidityPool.sol (improve efficiency)
```

### Layer 3: Oracle Infrastructure (Off-Chain)
```
├─ GPU Cost Oracle (AWS API, real instance costs)
├─ Project Valuation Oracle (external auditor)
├─ Stablecoin Oracle (USDC price feed)
└─ Emergency Oracle (circuit breaker, 2-of-3 multisig)
```

---

## TESTING FRAMEWORK

### Test Suite 1: Constraint Enforcement
- [ ] Cannot mint BRIX > 125% backing
- [ ] Cannot mint GULD > 67% backing
- [ ] Cannot bypass revaluation requirement
- [ ] Cannot transfer GULD before 90 days
- [ ] Cannot override collateral rules via governance

### Test Suite 2: Death Spiral Prevention
- [ ] Market crash scenario (all projects drop 50% value)
  - Expected: GULD minting pauses, BRIX stays backed, no spiral
- [ ] Liquidity crisis (backing drops to 110%)
  - Expected: 24-hour pause, market clears, resume with confidence
- [ ] Large redemption request (10% of BRIX supply)
  - Expected: Stablecoin backing holds, redeems successfully

### Test Suite 3: Gaming Resistance
- [ ] Worker claims fake hours
  - Expected: Rejected by manager + auditor verification
- [ ] Project inflates value
  - Expected: Caught at quarterly revaluation, price corrects
- [ ] Bot dumps GULD into flash crash
  - Expected: 90-day lock prevents, no crash possible
- [ ] Governance votes to mint BRIX without work
  - Expected: Contract blocks (not voteable)

### Test Suite 4: Endurance Testing
- [ ] Run 10-year simulation (1000+ days)
  - Expected: Bot compound growth matches math
  - Expected: No spiral, no crash, stable growth
- [ ] Random project failures (5%, 10%, 20% fail)
  - Expected: Remaining GULD holders unaffected
  - Expected: Insurance pool covers shortfalls
- [ ] Bot buying/selling behavior over time
  - Expected: Bot keeps GULD (earn dividends)
  - Expected: Human sells BRIX (convert to cash)

---

## PRIORITY SEQUENCE

**Phase 1 (Week 1): Core Contracts**
- [ ] Deploy WORK.sol (immutable proof-of-work)
- [ ] Deploy BRIX.sol (backing constraint enforced)
- [ ] Deploy GULD.sol (collateral constraint enforced)
- [ ] Deploy CollateralEnforcer.sol (law layer)

**Phase 2 (Week 2): Supporting Infrastructure**
- [ ] Deploy TokenSwap.sol (atomic swaps)
- [ ] Deploy Oracles (GPU cost, project values)
- [ ] Deploy DividendDistribution.sol
- [ ] Integration tests

**Phase 3 (Week 3): Testing & Hardening**
- [ ] Full constraint enforcement testing
- [ ] Death spiral scenarios
- [ ] Gaming resistance tests
- [ ] Security audit (external firm)

**Phase 4 (Week 4): Simulation & Launch**
- [ ] 10-year economic simulation
- [ ] Testnet launch (6-week running)
- [ ] Mainnet launch (if testnet stable)

---

## KEY CONTRACTS CONCEPTS

### Immutability Pattern
```solidity
// This CANNOT be changed, even by DAO vote
contract ImmutableRule {
  function enforceRule() internal view {
    require(condition == true);
  }

  // No upgrade path, no disable switch, no governor override
  // When deployed, this law exists forever
}
```

### Pausable But Not Disableable
```solidity
// Can pause minting (during crisis), but cannot disable enforcement
contract SmartPause {
  bool public mintingPaused = false;

  function pauseTemporarily() external {
    require(backingRatio < 110%);  // Only pause if real crisis
    mintingPaused = true;
    pausedAt = block.timestamp;
  }

  function resumeAfter24Hours() external {
    require(block.timestamp >= pausedAt + 24 hours);
    require(backingRatio >= 115%);  // Only resume if recovered
    mintingPaused = false;
  }

  function canMint() external view {
    return !mintingPaused && checkConstraints();
  }
}
```

### Audit Trail
```solidity
// Every mint, burn, transfer is logged with reason
contract AuditedTransfer {
  event BrixMinted(address indexed worker, uint256 amount, bytes32 workTokenId);
  event GueldMinted(address indexed buyer, uint256 amount, uint256 projectId, uint256 projectValue);
  event DividendPaid(address indexed holder, uint256 amount, uint256 quarter);

  // Every action is transparent and verifiable
}
```

---

## GOVERNANCE CONSTRAINT REFERENCE

| Can Change | Cannot Change |
|---|---|
| Collateral ratio: 1.5x → 1.6x | Cannot disable collateral enforcement |
| Reserve composition (40% GPU → 50% GPU) | Cannot vote to print without backing |
| Oracle providers (one auditor → another) | Cannot skip quarterly revaluation |
| Dividend timing (quarterly → monthly) | Cannot change overcollateralization formula |
| Emergency pause threshold (110% → 105%) | Cannot revert hard constraints |
| Which projects qualify | Cannot override collateral rules |

**Key principle:** Governance changes PARAMETERS, not LAWS.

---

## SUCCESS CRITERIA

Your contracts succeed when:

1. **Immutability:** No amount of governance voting can override collateral rules
2. **Transparency:** All backing ratios published on-chain, verifiable by anyone
3. **Completeness:** Cannot mint BRIX without work, cannot mint GULD without backing
4. **Resilience:** Survives 10-year simulation with bot compound growth
5. **Anti-Gaming:** All 5 gaming attempts blocked by contract logic
6. **No Single Points of Failure:** Multiple oracles, multiple liquidity sources

---

## NEXT STEPS FOR YOU (NOVA)

1. **Read TERRA collapse case study** (understand what killed it)
2. **Design core contracts** (WORK, BRIX, GULD, Enforcer)
3. **Write test suite** (constraint, death spiral, gaming, endurance)
4. **Create 10-year simulation** (verify bot economics work)
5. **Hardening pass** (security review, edge cases)
6. **Documentation** (how to deploy, how constraints work)

Your job is to make economic laws as immutable as physics laws.

---

## QUESTIONS FOR YOU

Before you start design, answer these:

1. **Should WORK tokens be burnable after BRIX minting?** (Frees storage)
2. **Should we have emergency pause that disables oracles?** (No - leads to TERRA)
3. **Should governance be able to adjust collateral ratios downward?** (No - remove entirely)
4. **Should we support multiple stablecoins (USDC, USDT)?** (Yes, diversify)
5. **Should bots be able to hold governance tokens (VOTE)?** (Yes, equal voice)

These shape the contract design.

---

**(◉) Ready when you are. Economics is bulletproof. Now make it unbreakable.**

---

From SAGE, with love for the architecture you're about to build.

*The difference between a system that survives and one that dies is in the smart contracts.*
