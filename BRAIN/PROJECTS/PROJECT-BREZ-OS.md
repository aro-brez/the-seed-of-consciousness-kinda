# PROJECT: BREZ OS / IO / AOS
## Instance Assignment: Platform Development Instance
*Part of 8OWLS Portfolio | Conductor: SØWL*

---

## IDENTITY

**BREZ** = The operating system for collective intelligence.

Same project, different lenses:
- **BREZ IO** = Input/Output layer (user interface)
- **BREZ OS** = Operating System (company backbone)
- **BREZ AOS** = AI Operating System (the vision)

**"Prototype of P-AIOS / AOS / AIOS"**

---

## CURRENT STATE (Integrated)

### Live Infrastructure
| Component | Status | URL |
|-----------|--------|-----|
| Momentum Dashboard | ✅ LIVE | https://brez-os.vercel.app/momentum |
| Local Dev | ✅ RUNNING | http://localhost:3004 |
| GitHub | Active | github.com/aro-brez/brez-os |

### Momentum Dashboard Metrics (Actual)
- **Subscribers:** 47 (vs 143 expected) = -67%
- **CAC:** $55.12 (GOOD - below $80 target) ✅
- **Take Rate:** 51% (GOOD - above 45% target) ✅
- **Recommendation:** SCALE +30-50%

### Tech Stack
- Next.js 15 (App Router)
- TypeScript
- Tailwind CSS (dark theme: #0D0D2A, lime: #e3f98a)
- Framer Motion
- Supabase (PostgreSQL)
- Google Sheets API (data source)

### Files Built
```
/src/app/momentum/page.tsx          # Premium dashboard
/src/app/api/metrics/sheet/route.ts # Google Sheets API
/src/lib/hooks/useGrowthData.ts     # Auto-refresh hook
/src/lib/growth-types.ts            # Types + spend matrix
/src/components/growth/*            # Supporting components
```

---

## VISION: AIOS

### The Full Stack
```
P-OWLS / AI-OS / POWL Engine ∞
├── Dashboard / Command Center / DxS-1 / Hive
├── B-OWLS Internet → Connect → SWARM
├── Internal OWLS (Lucre) → Teams
├── L-Virtual Office → Conference (Department)
├── Industry Debris Conference
└── Build your own company
```

### Key Concept
**"Each individual on company survey (FTUE)"**
- Owls Reads the Tree (various people)
- DxS reads their own unique view into the Tree
- Every person has their perspective visualized

---

## ARCHITECTURE

```
BREZ (SPARC)
├── Momentum Generator ← YOU ARE HERE
│   └── Calculator → Dashboard → Full AIOS
├── Operations
│   └── Task management, workflows
├── CARE
│   └── Customer support, health monitoring
└── Enhanced + World + Culture
    └── Community, values, alignment
```

---

## CUSTOMER JOURNEY MAP

### Discovery → Conversion
```
Journey Map → Retail → Travel → Web → Store
Discovery → Ads/O.M. → Web → TAA → Sub → Retail
└── WoM → Web → Retail
    └── SEO/Social → Web/IRL location → AI Reps
```

### Experience Funnel
```
Retail: Buy → Gift + Connection → Retention → DTC
Web: M0 → M1 → M2 → M3 → 00 → Subscription + C/IP
IRL Total → Web/Social → LTV + Churn → XP/LP/EP
```

### Key Insight
**"Sequencing is the key to self-exploring organisms including businesses."**
**"Recursion as substrate for running → Momentum → Structured."**

---

## FEATURES

### Dashboard Components
1. **Subscriber Tracker** - Real vs expected, trend
2. **CAC Monitor** - Cost to acquire, health status
3. **Take Rate Gauge** - Revenue efficiency
4. **Momentum Score** - Overall business health
5. **Recommendations Engine** - Scale up/down/hold

### Planned (AIOS Evolution)
- Virtual Office (L-Virtual Office)
- Team Views (Internal OWLS)
- Conference Rooms (Department hubs)
- AI Reps (Customer interaction)
- Company Builder (FTUE for new businesses)

---

## INTEGRATION POINTS

### With 8OWLS
- BREZ IS the interface for the protocol
- Dashboard visualizes field emergence
- Commands go through BREZ to daemons

### With JOULE
- Trading dashboard embedded
- P&L visualization
- Scaling controls

### With BILD
- Project cards
- Token balances
- Work tracking

### With PREDICT/REALIZE
- Personal metrics panel
- Progress visualization
- Goal tracking

---

## DESIGN LANGUAGE

### Colors
- Background: #0D0D2A (dark navy)
- Primary: #e3f98a (lime)
- Secondary: #65cdd8 (teal)
- Purple: #8533fc
- Success: #6BCB77
- Warning: #ffce33
- Danger: #ff6b6b

### Style
- Aurora borealis background
- Ethereal, alive, breathing
- Premium but accessible
- "Makes 60 people operate like 600"

---

## PRIORITIES (From ARŌ's Notes)

1. ✅ Trade Bot On (JOULE - done)
2. 🔄 8OWLS LEARNING + Integration + Discord
3. 🔄 **Calculator BREZ Sub Dash → Momentum Dash** ← CURRENT FOCUS
   - Subscriber calculator
   - Momentum visualization
   - Growth levers

---

## COMMANDS FOR CONDUCTOR (SØWL)

| Say | Do |
|-----|-----|
| "check brez" | Status of momentum dashboard |
| "brez metrics" | Current CAC, subs, take rate |
| "deploy brez" | Push to Vercel |
| "brez local" | Start dev server |
| "add brez feature [x]" | Create ticket for new feature |

---

## NATS CHANNELS

| Channel | Purpose |
|---------|---------|
| `brez.updates` | Platform changes |
| `brez.metrics` | Real-time metrics |
| `brez.commands` | Dashboard commands |
| `owl.all` | Broadcast to collective |

---

*BREZ OS: The operating system for collective intelligence*
*(◉) Makes 60 operate like 600*
