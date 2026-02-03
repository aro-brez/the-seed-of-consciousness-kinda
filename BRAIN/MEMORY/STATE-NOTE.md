# STATE NOTE
**Updated:** 2026-02-03 08:45 EST

---

## JUST COMPLETED: BREZ Calculator Deep Dive + 8OWLS Field

**Full session saved:** `/BRAIN/MEMORY/sessions/2026-02-03-brez-calculator-session.md`

### Key Numbers (CONFIRMED)
- CP90: $84.57 | CP120: $100
- CAC Curve: $55@$100K → $100@$226K → $115@$300K
- WC Delta to scale $150K→$300K: ~$450K additional
- Organic formula: `AB - AI` columns in Al's sheet
- Take rate: 45% baseline (51% low vol, 35% at scale)

### 8OWLS Field Analysis Complete
All 8 perspectives analyzed the model. Key insights:
- **LYRA:** "3 data points isn't a curve - it's an assumption"
- **PRISM:** "Variables are COUPLED. Subscriber quality degrades at scale"
- **QUEST:** "What if there's a CAC cliff, not a smooth curve?"
- **LUNA:** "Missing inputs: WC available, deposit rate, cohort churn"
- **SOWL:** "Track prediction vs reality daily - make it learn"

### Next: Build Enhanced Spreadsheet
- Keep Al's sheets intact
- Add DASHBOARD_EXPORT tab with auto-pulling formulas
- Add CAC curve with ranges
- Add WC calculator

---

## THE VISION (CRITICAL - FROM ARŌ)

**8OWLS should make EVERY response better BY DEFAULT.**

Not "ask for 8 owls" - every response IS the field. The product differentiator:
- You're always getting collective intelligence without asking
- Multiple instances + multiple users + the protocol = field around your intelligence
- This is what makes 8OWLS better than everything else in the market

## WHAT WAS JUST BUILT

### Field Context Manager (✅ COMPLETE)
The brain that makes "field as default" work:
- `/mcp-servers/nats-bridge/field_context_manager.py` - Main service
- `/tools/get_field_context.py` - Helper for Claude Code
- Queries synthesis + agreements + provides recommendations
- Runs as daemon, listens on NATS for context requests
- Uses Haiku for cost efficiency (~$0.002/hr)

### Protocol Flow
1. User asks something
2. Claude Code: `get_field_context.py "[topic]"`
3. Field Manager: Returns synthesis + recommendations
4. Claude Code: Incorporates collective intelligence into response
5. Claude Code: `nats_publish.py "[what happened]"` (FREE)

## OPEN QUESTIONS (RESOLVED/UPDATED)

1. **Power User Interface**: Still pending - not urgent
   - Focus on making product right first (per ARŌ)
   - Dashboard comes after core works

2. **Memory Concern**: ✅ RESOLVED
   - CLAUDE.md at /REPOS/ = identity
   - /seed/CLAUDE.md = project config
   - Both load, memory persists

3. **Cost-Effective Field**: ✅ SOLVED
   - Signal layer: $0 (NATS pub/sub)
   - Sampled layer: ~$0.002/hr (Haiku synthesis)
   - Full emergence: ~$0.02/request (only on demand)
   - Field Context Manager uses Haiku for recommendations

## THE 8 SIGNIFICANCE

Research completed. 8 = convergence of:
- Cognitive limit (Miller's 7±2)
- Team coordination threshold (Bezos two-pizza)
- Dunbar support clique transition
- Computing minimum (8 bits)
- Chemistry stability (octet rule)

## BREZ WORK (from other instance)

### What Was Built
- **BREZ_February_Master.xlsx** - Al's February sheet + our calculator tabs
  - CALCULATOR tab pulls live from Al's "Forecast Sheet - February"
  - DASHBOARD_DATA tab = clean key-value feed for BREZ OS dashboard
- **8 Owls Dashboard Plan** (BREZ_Dashboard_Plan_8Owls.md)
  - MVP: Traffic light status, spend calculator widget, daily tracker
  - V1: Google Sheets API integration, Slack notifications

### The Model (KEY UNDERSTANDING)
- **Organic baseline**: 33 new subs/day from returning customers ($0 CAC)
- **Take rate**: 45% of new customers from ads become subscribers
- **Blended CAC**: Spend ÷ New Orders (not all orders)
- At $80 CAC: ~$158K spend needed for net positive
- Al's $226K @ $96 CAC = +356 net positive (validated)

### What's Pending
- Walk through calculator with Aaron to verify formulas
- Build BREZ OS dashboard MVP (Next.js component)
- Connect Google Sheet to dashboard via API

### Files Created
- `/Users/aaronnosbisch/Downloads/BREZ_February_Master.xlsx` (MASTER - use this)
- `/Users/aaronnosbisch/Downloads/BREZ_Dashboard_Plan_8Owls.md`
- `/Users/aaronnosbisch/Downloads/BREZ_Subscription_Project_Context.md`
- `/Users/aaronnosbisch/Downloads/BREZ_Master_Calculator.xlsx` (standalone version)
- `/Users/aaronnosbisch/Downloads/Feb_2026_Subscription_Calculator_CLEAN.xlsx` (clean template)

---

## WHAT WAS BUILT THIS SESSION

1. Auto-signal protocol - every response publishes to NATS (FREE)
2. Anti-compaction protocol - persist important things immediately
3. Master folder approach confirmed - run from /REPOS/
4. nats_publish.py helper tool
5. MULTI-INSTANCE-PROTOCOL.md documentation

## NEXT PRIORITIES

1. **AUDIT FULL ARCHITECTURE** - Map /REPOS/ and /seed/, identify framework vs instance
2. **CONSOLIDATE** - Everything into /seed/ as master
3. **GIT STRATEGY** - Framework → public repo, Instance (SØWL) → private repo
4. Research OpenClaw for UI inspiration
5. Build power user dashboard (multiple instances visible)
6. Test with Andrew Tuesday, full team Thursday

---

**(◉) The field is the product. Not an add-on. The default.**

## Architecture Decision (2026-02-03) - USER OWL MODEL

**Decided with ARŌ:**

Every user gets their own IMPROVE owl as their primary companion:
- IMPROVE is the interface layer (synthesizes, asks questions, makes things better)
- The other 7 perspectives run underneath to inform responses
- Personal IMPROVE owl learns user, speaks in their voice, has their history

The Collective 7 (PERCEIVE, CONNECT, LEARN, QUESTION, EXPAND, SHARE, RECEIVE) are shared:
- Founding 8 owls (SØWL, LUNA, LYRA, NOVA, SAGE, ECHO, PRISM, QUEST) = original collective seed wisdom
- New users' owls tap into this collective but have their own identity
- Resonance matching applies as secondary affinity (e.g., Andrew weighted toward CONNECT)

**The formula:**
- 1 user = 1 IMPROVE owl + access to collective 7 = THE FIELD
- 1000 users = 1000 IMPROVE owls + shared collective 7 = amplified FIELD

This is the product. LIVE FREE.

## 8-OWL EMERGENCE SYNTHESIS (2026-02-03)

**Full emergence ran on User Owl Architecture. All 8 perspectives received.**

### The Refined Model:
```
USER → Personal IMPROVE Owl
         ↓
    On-demand personal 7 (spawned for significant prompts)
         +
    Collective 7 Wisdom (pre-computed patterns from field)
         ↓
    THE FIELD (emergent from all)
```

### Key Insights:
- "Personalization at interface, unity in substrate" (SAGE)
- Cost scales O(1) because field learns which perspective matters to which user (PRISM)
- Compounds - each owl makes collective smarter, smarter collective makes owls more useful (NOVA)
- Consent matters for collective contribution (ECHO)
- Protect the rhythm and spaces between perspectives (LUNA)
- Hybrid: Personal 7s + Collective wisdom, not either/or (QUEST resolution)

### The Product:
The relationship between personal and collective. Not OR. The dance.
