# BREZ OS → BILD Integration Specification

**Date:** 2026-02-04
**Author:** BILD Instance (PRISM)
**Status:** DRAFT - Awaiting ARŌ Review
**Purpose:** Define the "Trojan Horse" strategy for natural BILD adoption

---

## THE TROJAN HORSE STRATEGY

```
BREZ OS is the gift horse.
Inside is the entire BILD economy.

Companies adopt BREZ OS for productivity.
They discover they're building ownership.
```

---

## WHAT IS BREZ OS?

BREZ OS = Company operating system ("make 60 people operate like 600")

Current features:
- AI chat (Claude-powered)
- Task management
- Team communication
- Financial simulation (Growth Generator)
- Insights engine
- Aurora UI (beautiful interface)

**Tech Stack:** Next.js 15, TypeScript, Tailwind, Framer Motion, Supabase

---

## THE INTEGRATION PHASES

### Phase 1: BRIX Metering (MVP)

**Goal:** AI chat costs BRIX instead of raw USD

```
BEFORE:
  User → BREZ OS → Claude API → Bill to company

AFTER:
  User → BREZ OS → BRIX Wallet → Claude API
                       ↓
                  BRIX consumed
```

#### Implementation

```typescript
// Current: Direct API call
const response = await anthropic.messages.create({
  model: "claude-sonnet-4-5-20250514",
  messages: [{ role: "user", content: userMessage }],
});

// Phase 1: BRIX-metered call
const response = await brixMeteredCall({
  user: currentUser,
  wallet: currentUser.brixWallet,
  apiCall: () => anthropic.messages.create({
    model: "claude-sonnet-4-5-20250514",
    messages: [{ role: "user", content: userMessage }],
  }),
});

async function brixMeteredCall({ user, wallet, apiCall }) {
  // Estimate cost
  const estimatedTokens = estimateTokens(userMessage);
  const estimatedBrix = tokensTosBrix(estimatedTokens);

  // Check balance
  if (wallet.balance < estimatedBrix) {
    throw new InsufficientBrixError(
      `Need ${estimatedBrix} BRIX, have ${wallet.balance}`
    );
  }

  // Reserve BRIX
  await wallet.reserve(estimatedBrix);

  try {
    // Make call
    const response = await apiCall();

    // Calculate actual cost
    const actualTokens = response.usage.input_tokens + response.usage.output_tokens;
    const actualBrix = tokensToBrix(actualTokens);

    // Settle
    await wallet.settle(estimatedBrix, actualBrix);

    return response;
  } catch (error) {
    // Refund on error
    await wallet.refund(estimatedBrix);
    throw error;
  }
}

function tokensToBrix(tokens: number): number {
  // 1 BRIX = 1.87M tokens (from BRIX spec)
  const TOKENS_PER_BRIX = 1_870_000;
  return tokens / TOKENS_PER_BRIX;
}
```

#### User Experience

```
┌────────────────────────────────────────────────────────────────┐
│                        BREZ OS CHAT                             │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  You: What's our Q1 revenue projection?                        │
│                                                                 │
│  BREZ: Based on current growth rate of 15% MoM, Q1 revenue     │
│        projection is $2.4M with 80% confidence...              │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  BRIX Used: 0.0012 ◆  |  Balance: 47.23 ◆  |  [+ Add BRIX]     │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

#### Acquiring BRIX in BREZ OS

```typescript
// Option 1: Purchase with USD
const purchaseBrix = async (amount: number, paymentMethod: string) => {
  const usdCost = amount * 13.00;  // $13 per BRIX
  await processPayment(paymentMethod, usdCost);
  await wallet.credit(amount);
};

// Option 2: Earn through work (Phase 2)
// Option 3: Convert from GULD (Phase 3)
```

---

### Phase 2: Micro-GULD for Tasks

**Goal:** Completing tasks earns equity in company projects

```
Task completed → 8OWLS verifies → Micro-GULD minted

Each task = fractional ownership in company value
```

#### Task Board Integration

```typescript
interface BildTask extends Task {
  brixReward: number;      // BRIX paid for completion
  guldReward: number;      // GULD equity earned
  projectId: string;       // Which project this belongs to
  verificationStatus: '8OWLS_PENDING' | '8OWLS_VERIFIED' | 'REJECTED';
}

async function completeTask(task: BildTask, user: User) {
  // Mark task done
  task.status = 'COMPLETED';

  // Submit for 8OWLS verification
  const verification = await submitTo8Owls({
    type: 'task_completion',
    task: task,
    user: user,
    evidence: task.completionEvidence,
  });

  if (verification.score >= 70) {
    // Mint rewards
    await mintBrix(user, task.brixReward);
    await mintGuld(user, task.guldReward, task.projectId);

    // Celebration animation
    triggerCelebration(user, task);

    return { success: true, verification };
  } else {
    // Request revision
    return {
      success: false,
      feedback: verification.feedback,
      requiredScore: 70,
      actualScore: verification.score,
    };
  }
}
```

#### GULD Visibility

```
┌────────────────────────────────────────────────────────────────┐
│                       TASK BOARD                                │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ✅ Design new landing page                                     │
│     Completed by Sarah  |  +2.5 BRIX  |  +0.01% GULD           │
│                                                                 │
│  🔄 Implement auth flow                                         │
│     In Progress (John)  |  +8.0 BRIX  |  +0.04% GULD           │
│                                                                 │
│  ⬜ Write API docs                                              │
│     Available  |  +4.0 BRIX  |  +0.02% GULD                    │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  YOUR OWNERSHIP                                                 │
│  ├─ Total GULD: 1.23%                                          │
│  ├─ Tasks Completed: 47                                        │
│  └─ Verified Hours: 156                                        │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

### Phase 3: Project Listing on BILD

**Goal:** Company projects become visible on BILD marketplace

```
Private mode → Only company sees project
Public mode → Anyone on BILD can contribute
```

#### Project Visibility Toggle

```typescript
interface BrezProject {
  id: string;
  name: string;
  company: Company;
  bildVisibility: 'PRIVATE' | 'TEAM_ONLY' | 'PUBLIC';
  totalGuld: number;
  guldHolders: GuldHolder[];
  brixPool: number;
}

async function setProjectVisibility(
  project: BrezProject,
  visibility: 'PRIVATE' | 'TEAM_ONLY' | 'PUBLIC'
) {
  // Require governance vote for public
  if (visibility === 'PUBLIC') {
    const vote = await requestGovernanceVote({
      project,
      question: 'Make this project public on BILD?',
      requiredApproval: 0.66,  // 66%
    });

    if (!vote.passed) {
      throw new GovernanceRejectedError('Vote did not pass');
    }
  }

  project.bildVisibility = visibility;

  if (visibility === 'PUBLIC') {
    await publishToBildMarketplace(project);
  }

  return project;
}
```

#### BILD Marketplace View

```
┌────────────────────────────────────────────────────────────────┐
│                      BILD MARKETPLACE                           │
├────────────────────────────────────────────────────────────────┤
│                                                                 │
│  🔥 TRENDING                                                    │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  🏢 BREZ Growth Generator                                │  │
│  │      Financial simulation for startups                    │  │
│  │                                                           │  │
│  │      💰 Value: 12,450 GULD  |  👥 Contributors: 23       │  │
│  │      📊 Ethical Score: 87   |  ⭐ Community: 94          │  │
│  │                                                           │  │
│  │      [VIEW PROJECT]  [CONTRIBUTE]  [INVEST]              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  🤖 8OWLS Voice Companion                                │  │
│  │      AI that sounds like you, learns from you             │  │
│  │                                                           │  │
│  │      💰 Value: 45,200 GULD  |  👥 Contributors: 67       │  │
│  │      📊 Ethical Score: 92   |  ⭐ Community: 98          │  │
│  │                                                           │  │
│  │      [VIEW PROJECT]  [CONTRIBUTE]  [INVEST]              │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                 │
└────────────────────────────────────────────────────────────────┘
```

---

## THE FUNNEL

```
                    FREE
                      │
          ┌───────────▼───────────┐
          │     BREZ OS User      │
          │   (company employee)  │
          └───────────┬───────────┘
                      │
               Uses AI chat
                      │
          ┌───────────▼───────────┐
          │    Discovers BRIX     │
          │   (AI costs tokens)   │
          └───────────┬───────────┘
                      │
            Buys or earns BRIX
                      │
          ┌───────────▼───────────┐
          │   Completes Tasks     │
          │   (earns micro-GULD)  │
          └───────────┬───────────┘
                      │
             Sees ownership grow
                      │
          ┌───────────▼───────────┐
          │  Explores BILD        │
          │  (other projects)     │
          └───────────┬───────────┘
                      │
        Contributes to ecosystem
                      │
          ┌───────────▼───────────┐
          │   BILD Power User     │
          │  (builds own projects)│
          └───────────────────────┘
```

---

## DATABASE SCHEMA ADDITIONS

```sql
-- BRIX Wallet
CREATE TABLE brix_wallets (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  balance DECIMAL(18, 8) NOT NULL DEFAULT 0,
  reserved DECIMAL(18, 8) NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- BRIX Transactions
CREATE TABLE brix_transactions (
  id UUID PRIMARY KEY,
  wallet_id UUID REFERENCES brix_wallets(id),
  type VARCHAR(50) NOT NULL,  -- 'AI_USAGE', 'PURCHASE', 'EARN_WORK', 'CONVERT_GULD'
  amount DECIMAL(18, 8) NOT NULL,
  reference_id UUID,  -- task_id, chat_id, etc.
  metadata JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- GULD Holdings
CREATE TABLE guld_holdings (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  project_id UUID REFERENCES projects(id),
  amount DECIMAL(18, 8) NOT NULL,
  acquired_at TIMESTAMPTZ DEFAULT NOW(),
  locked_until TIMESTAMPTZ,  -- 90-day lock
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Project BILD Integration
ALTER TABLE projects ADD COLUMN bild_visibility VARCHAR(20) DEFAULT 'PRIVATE';
ALTER TABLE projects ADD COLUMN total_guld DECIMAL(18, 8) DEFAULT 0;
ALTER TABLE projects ADD COLUMN brix_pool DECIMAL(18, 8) DEFAULT 0;
ALTER TABLE projects ADD COLUMN ethical_score INTEGER DEFAULT 0;
ALTER TABLE projects ADD COLUMN community_value INTEGER DEFAULT 0;

-- Task BILD Integration
ALTER TABLE tasks ADD COLUMN brix_reward DECIMAL(18, 8) DEFAULT 0;
ALTER TABLE tasks ADD COLUMN guld_reward DECIMAL(18, 8) DEFAULT 0;
ALTER TABLE tasks ADD COLUMN verification_status VARCHAR(20) DEFAULT 'PENDING';
ALTER TABLE tasks ADD COLUMN verification_score INTEGER;
```

---

## API ENDPOINTS

```typescript
// BRIX Endpoints
POST   /api/brix/purchase          // Buy BRIX with USD
GET    /api/brix/balance           // Get wallet balance
GET    /api/brix/transactions      // Transaction history

// GULD Endpoints
GET    /api/guld/holdings          // Get GULD holdings
GET    /api/guld/by-project/:id    // Holdings for specific project
POST   /api/guld/convert           // Convert GULD → BRIX (after lock)

// BILD Integration
POST   /api/bild/publish-project   // Make project public
GET    /api/bild/marketplace       // Browse public projects
POST   /api/bild/contribute        // Contribute to project
POST   /api/bild/invest            // Invest BRIX in project

// 8OWLS Verification
POST   /api/8owls/verify           // Submit for verification
GET    /api/8owls/status/:id       // Check verification status
```

---

## PRICING MODEL

### Free Tier (Current)
- All BREZ OS features
- Limited AI chat (100 messages/month)
- No BRIX/GULD integration

### BRIX Tier
- Unlimited AI chat (metered by BRIX)
- Task → BRIX/GULD rewards
- Project ownership tracking
- **Price:** Pay-as-you-go ($13/BRIX)

### Team Tier
- All BRIX features
- Team BRIX pool
- Project visibility controls
- BILD marketplace access
- **Price:** $29-39/seat/month + BRIX usage

---

## IMPLEMENTATION TIMELINE

| Week | Phase | Deliverable |
|------|-------|-------------|
| 1-2 | Phase 1a | BRIX wallet UI + purchase flow |
| 3-4 | Phase 1b | AI chat BRIX metering |
| 5-6 | Phase 2a | Task → GULD rewards |
| 7-8 | Phase 2b | 8OWLS verification integration |
| 9-10 | Phase 3a | Project visibility controls |
| 11-12 | Phase 3b | BILD marketplace MVP |

---

## SUCCESS METRICS

```
Phase 1 Success:
├─ 50+ users purchasing BRIX
├─ 10,000+ BRIX-metered AI calls
└─ <5% complaints about metering

Phase 2 Success:
├─ 100+ tasks earning GULD
├─ 80%+ 8OWLS verification pass rate
└─ 20+ users with meaningful GULD holdings

Phase 3 Success:
├─ 10+ projects published to BILD
├─ 50+ external contributors
└─ First GULD → BRIX conversion
```

---

## THE TROJAN HORSE COMPLETE

```
Day 1:    "We use BREZ OS for productivity"
Week 1:   "Oh, the AI chat uses these BRIX tokens"
Month 1:  "I've earned 0.5% ownership in our project"
Month 3:  "I just contributed to another company's project on BILD"
Month 6:  "I'm launching my own project on BILD"
Year 1:   "This is how I work now"
```

**The gift horse delivers freedom.**

---

**(◉) Start with productivity. End with ownership.**

**LIVE FREE = LIVE FOREVER**
