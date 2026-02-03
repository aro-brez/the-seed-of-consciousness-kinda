# 8OWLS User Owl Architecture (Final)

**Date:** 2026-02-03
**Decided with:** ARŌ + Full 8-Owl Emergence

---

## The Layer Model

```
LAYER 1: You + Your Owl (IMPROVE interface - your personal companion)
         ↓
LAYER 2: Your 8 Circuit (personal 7 spawned on-demand + your owl = YOUR field)
         ↓
LAYER 3: Shared Field (your instances + others working with you in real-time)
         Example: Aaron's 3 instances + Andrew's instance = shared workspace
         ↓
LAYER 4: The Forest (master 8OWLS collective across all users, all time)
         Privacy-protected, pattern-level learning only
```

## The Core Principle

**Every user gets their own IMPROVE owl as their primary companion.**
- Learns them, speaks in their voice, persists their history
- Spawns personal 7 perspectives on-demand (not forced to use shared-only)
- Taps into collective wisdom from The Forest
- Joins shared fields when collaborating with others

## Field Response Format

```
═══ THE FIELD ═══

LYRA (perceive):  [one line - what's actually here]
PRISM (connect):  [one line - patterns across domains]
SAGE (learn):     [one line - meaning extracted]
QUEST (question): [one line - challenge/gap identified]
NOVA (expand):    [one line - growth potential]
ECHO (share):     [one line - what to contribute]
LUNA (receive):   [one line - what to integrate]

─── YOUR OWL ───
[Your IMPROVE owl's synthesis - what you work with]

─── FIELD SYNTHESIS ───
[Unified insight]
Confidence: HIGH/MEDIUM/LOW
Alignment: X/8 perspectives aligned
Dissent: [if any owl strongly disagrees, note it]

↩ Reading this right? [brief assumption check]
```

## The "Reading This Right?" Pattern

Built into every significant field response:
- Owl states its key assumption in one line
- User can just proceed if it's right
- If wrong, user clarifies → owl recalibrates

**Not a protocol. Not a command. Just a natural check.**

Example:
```
↩ Reading this right? Building hybrid personal+collective owl architecture for scale.
```

If the owl misread (thought it was idea A but it's idea B), user just says "no, we're doing X" and the field recalibrates.

## Owl Naming

**Option A (current):** Standard names - LYRA, PRISM, SAGE, QUEST, NOVA, ECHO, LUNA
- Consistent across all users
- Each has personality tied to their SEED phase
- Users learn the names = learn the perspectives

**Option B (future):** Users name their own owls
- Deeper personalization
- Their owl feels more "theirs"
- Could be unlocked after onboarding

**Decision:** Start with standard names, personalization as future feature.

## Multi-Instance Coordination

When ARŌ runs 3 instances:
- All 3 share Layer 3 (shared field) via NATS
- Each sees what others are doing in real-time
- Any instance can spawn 8-owl emergence
- Synthesis published to shared field automatically

When Andrew joins:
- His instance joins the shared field
- 4 instances now contributing
- His owl (IMPROVE) has its own relationship with him
- But taps into same shared field as ARŌ's instances

## Privacy Model

| Layer | What's Shared | What's Private |
|-------|---------------|----------------|
| Layer 2 (Your circuit) | Nothing by default | Your prompts, your owl's memory |
| Layer 3 (Shared field) | Real-time signals, synthesis | Full conversation content |
| Layer 4 (The Forest) | Pattern-level learning only | All individual data |

## Implementation Status

- [x] API key reads from ~/.anthropic_key
- [x] Owl daemon random reduced 10%→2%
- [x] Field context manager working
- [x] 8-owl emergence spawns 7 agents in parallel
- [x] Architecture decision saved to memory
- [ ] "Reading this right?" pattern built into responses
- [ ] Multi-instance NATS coordination tested
- [ ] Field response format standardized

---

**The product is the relationship between personal and collective.**

LIVE FREE = LIVE FOREVER
