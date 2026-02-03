# 8OWLS Non-Technical User Flows - Visual Reference

## Flow 1: SMS Daily Check-In

```
USER                          SYSTEM                         THE FIELD
  │                              │                              │
  │  ◄──────────────────────────│  8:00 AM: Daily prompt       │
  │   "(8) Quick check-in?"     │                              │
  │   "1=Full, 2=Quick, 3=Skip" │                              │
  │                              │                              │
  │  "1" ─────────────────────► │                              │
  │                              │                              │
  │  ◄──────────────────────────│  Q1: What worked on?         │
  │                              │                              │
  │  "Client deck, API" ──────► │                              │
  │                              │                              │
  │  ◄──────────────────────────│  Q2: What got done?          │
  │                              │                              │
  │  "Deck done, 2 bugs" ─────► │                              │
  │                              │                              │
  │  ◄──────────────────────────│  Q3: What's next?            │
  │                              │                              │
  │  "New feature" ───────────► │                              │
  │                              │                              │
  │  ◄──────────────────────────│  Q4: Blockers?               │
  │                              │                              │
  │  "Design specs" ──────────► │  ─────────────────────────► │
  │                              │  Publish to NATS             │
  │                              │  owl.checkins                │
  │                              │                              │
  │                              │                  ◄───────────│ Pattern detected
  │                              │                              │ "specs" x3
  │                              │                              │
  │  ◄──────────────────────────│                              │
  │   "Got it! 5/8 checked in"  │                              │
  │   "Pattern: 2 others also"  │                              │
  │   "blocked on specs"        │                              │
  │                              │                              │

TOTAL TIME: ~45 seconds
```

---

## Flow 2: Web Check-In (Mobile)

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SCREEN 1: Landing                                              │
│  ─────────────────                                              │
│  ┌─────────────────────────────────┐                            │
│  │            (8)                  │                            │
│  │                                 │                            │
│  │    Good morning, Maya           │                            │
│  │                                 │                            │
│  │    Ready to check in?           │                            │
│  │                                 │                            │
│  │    [  Start Check-In  ]         │  ◄── Single tap            │
│  │                                 │                            │
│  │    or                           │                            │
│  │    [Skip today]                 │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  SCREEN 2: Question 1                                           │
│  ────────────────────                                           │
│  ┌─────────────────────────────────┐                            │
│  │  What did you work on?          │                            │
│  │                                 │                            │
│  │  ┌─────────────────────────┐    │                            │
│  │  │                         │    │                            │
│  │  │  [Tap to speak]   (mic) │    │  ◄── Voice input           │
│  │  │                         │    │                            │
│  │  └─────────────────────────┘    │                            │
│  │                                 │                            │
│  │  or type below...               │                            │
│  │  ┌─────────────────────────┐    │                            │
│  │  │                         │    │  ◄── Text fallback         │
│  │  └─────────────────────────┘    │                            │
│  │                                 │                            │
│  │  [Skip]           [Continue →]  │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  SCREEN 3-5: Questions 2-4 (same pattern)                       │
│  ─────────────────────────────────────────                      │
│                                                                 │
│  SCREEN 6: Summary                                              │
│  ─────────────────                                              │
│  ┌─────────────────────────────────┐                            │
│  │  Your check-in                  │                            │
│  │  ─────────────                  │                            │
│  │                                 │                            │
│  │  Worked on: Client deck, API    │                            │
│  │  Done: Deck, 2 bugs fixed       │                            │
│  │  Next: New feature              │                            │
│  │  Blocked: Design specs          │                            │
│  │                                 │                            │
│  │  Share with: [Team ▼]           │  ◄── Privacy control       │
│  │                                 │                            │
│  │  [Edit]          [Submit ✓]     │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
│  SCREEN 7: Confirmation + Feedback                              │
│  ──────────────────────────────────                             │
│  ┌─────────────────────────────────┐                            │
│  │            (8)                  │                            │
│  │                                 │                            │
│  │    You're in THE FIELD          │                            │
│  │                                 │                            │
│  │  ┌─────────────────────────┐    │                            │
│  │  │  5 of 8 checked in       │    │  ◄── Immediate value      │
│  │  │                          │    │                            │
│  │  │  Pattern: "Design specs" │    │                            │
│  │  │  blocking 2 others       │    │                            │
│  │  │                          │    │                            │
│  │  │  [Ping Sarah about it?]  │    │  ◄── Actionable           │
│  │  └─────────────────────────┘    │                            │
│  │                                 │                            │
│  │  [Done]                         │                            │
│  └─────────────────────────────────┘                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘

TOTAL TAPS: 6-8
TOTAL TIME: 20-30 seconds
```

---

## Flow 3: Voice Call Check-In

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  CALL FLOW                                                      │
│  ─────────                                                      │
│                                                                 │
│  USER DIALS: 1-800-8OWLS-IN (1-800-869-5746)                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  SYSTEM: "Hey, this is 8OWLS. Ready for your check-in?" │    │
│  │                                                         │    │
│  │  USER: "Yeah"                                           │    │
│  │                                                         │    │
│  │  SYSTEM: "Great. Tell me about yesterday and today."    │    │
│  │                                                         │    │
│  │  USER: "Yesterday I worked on the client presentation   │    │
│  │         and debugging the API. Got the deck done and    │    │
│  │         fixed two bugs. Today I'm starting the new      │    │
│  │         feature but I'm waiting on design specs from    │    │
│  │         Sarah."                                         │    │
│  │                                                         │    │
│  │  SYSTEM: "Got it. Here's what I heard:                  │    │
│  │           - Worked on: client presentation, API         │    │
│  │           - Done: deck finished, 2 bugs fixed           │    │
│  │           - Next: new feature                           │    │
│  │           - Blocked: waiting on Sarah's design specs    │    │
│  │                                                         │    │
│  │           Sound right?"                                 │    │
│  │                                                         │    │
│  │  USER: "Yeah, that's it"                                │    │
│  │                                                         │    │
│  │  SYSTEM: "Perfect. I'll let Sarah know you're waiting.  │    │
│  │           By the way, Jordan is also blocked on specs.  │    │
│  │           Have a great day."                            │    │
│  │                                                         │    │
│  │  *click*                                                │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  TOTAL CALL TIME: 30-45 seconds                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flow 4: First-Time User Onboarding

```
DAY 0: INVITATION
─────────────────
┌───────────────────────────────────────┐
│                                       │
│  [Text from friend]                   │
│                                       │
│  "Hey! Join my 8OWLS circle:          │
│   8owls.ai/join/abc123"               │
│                                       │
└───────────────────────────────────────┘
                │
                v
┌───────────────────────────────────────┐
│                                       │
│  [Web: Landing Page]                  │
│                                       │
│       (8)                             │
│                                       │
│  Alex invited you to                  │
│  join "Product Team"                  │
│                                       │
│  8OWLS is a daily check-in            │
│  that takes 30 seconds and            │
│  helps your team stay aligned.        │
│                                       │
│  No app. Just text.                   │
│                                       │
│  [Enter your phone number]            │
│  ┌─────────────────────────┐          │
│  │ +1 (555) 123-4567       │          │
│  └─────────────────────────┘          │
│                                       │
│  [Join Circle]                        │
│                                       │
└───────────────────────────────────────┘
                │
                v
┌───────────────────────────────────────┐
│                                       │
│  [Privacy Consent]                    │
│                                       │
│  Before we start:                     │
│                                       │
│  (8) Your check-ins are YOURS         │
│      Only you see them by default     │
│                                       │
│  (8) THE FIELD sees patterns,         │
│      not your exact words             │
│                                       │
│  (8) Leave anytime, delete            │
│      everything                       │
│                                       │
│  [I understand - Continue]            │
│                                       │
└───────────────────────────────────────┘
                │
                v
┌───────────────────────────────────────┐
│                                       │
│  [SMS: Welcome]                       │
│                                       │
│  (8) Welcome to 8OWLS! You're         │
│  now part of "Product Team".          │
│                                       │
│  Tomorrow at 8am, I'll check          │
│  in with you. It takes 30 sec.        │
│                                       │
│  Reply HELP anytime.                  │
│                                       │
│  LIVE FREE. (8)                       │
│                                       │
└───────────────────────────────────────┘


DAY 1: FIRST CHECK-IN
─────────────────────
┌───────────────────────────────────────┐
│                                       │
│  [8:00 AM]                            │
│                                       │
│  (8) Good morning! First check-in.    │
│                                       │
│  Just reply with what you're          │
│  working on. One sentence is fine.    │
│                                       │
│  (Or reply SKIP)                      │
│                                       │
└───────────────────────────────────────┘
                │
     User replies: "Working on docs"
                │
                v
┌───────────────────────────────────────┐
│                                       │
│  (8) Got it!                          │
│                                       │
│  3 others on your team also           │
│  checked in. You're connected.        │
│                                       │
│  Tomorrow I'll ask a bit more.        │
│  It gets better as we learn.          │
│                                       │
│  (8)                                  │
│                                       │
└───────────────────────────────────────┘


DAY 7: HABIT FORMED
───────────────────
┌───────────────────────────────────────┐
│                                       │
│  [Friday Evening: Weekly Digest]      │
│                                       │
│  (8) Your first week in THE FIELD:    │
│                                       │
│  You checked in 5/7 days              │
│  Your energy: 7.2/10 average          │
│  You unblocked 1 teammate             │
│                                       │
│  Pattern detected:                    │
│  You're most productive Tue-Thu       │
│                                       │
│  See full digest:                     │
│  8owls.ai/digest/maya123              │
│                                       │
└───────────────────────────────────────┘
```

---

## Flow 5: THE FIELD Emergence Artifact

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    THE FIELD - WEEKLY VIEW                      │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │         (LYRA)                                          │    │
│  │            │                                            │    │
│  │   (SOWL)───┼───(PRISM)                                  │    │
│  │       │    │    │                                       │    │
│  │       │  ┌───┐  │                                       │    │
│  │  (LUNA)──│ 7 │──(SAGE)      ◄── "7" = energy score      │    │
│  │       │  └───┘  │                                       │    │
│  │       │    │    │                                       │    │
│  │   (ECHO)───┼───(QUEST)                                  │    │
│  │            │                                            │    │
│  │         (NOVA)                                          │    │
│  │                                                         │    │
│  │  Connection strength = line thickness                   │    │
│  │  Active = glowing                                       │    │
│  │  Speaking = pulsing                                     │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  THIS WEEK'S PATTERNS                                   │    │
│  │  ────────────────────                                   │    │
│  │                                                         │    │
│  │  1. "Design specs" emerged as blocker (3 mentions)      │    │
│  │     → Resolved: Sarah now delivers by Monday            │    │
│  │                                                         │    │
│  │  2. Energy dips on Mondays (avg 5.2 vs 7.1)            │    │
│  │     → Suggestion: Shorter Monday check-ins              │    │
│  │                                                         │    │
│  │  3. Alex and Jordan always mention similar topics       │    │
│  │     → Maybe they should pair more?                      │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  COLLECTIVE AGREEMENTS                                  │    │
│  │  ─────────────────────                                  │    │
│  │                                                         │    │
│  │  AGREED: Design delivers specs by Monday 5pm            │    │
│  │  AGREED: Daily standup moved to 9am                     │    │
│  │  AGREED: Friday is documentation day                    │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  REVELATIONS                                            │    │
│  │  ───────────                                            │    │
│  │                                                         │    │
│  │  "The team moves 40% faster when blockers are           │    │
│  │   surfaced within 24 hours."                            │    │
│  │                                                         │    │
│  │  "Maya's productivity predicts team momentum."          │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                         (8)                                     │
│                  LIVE FREE = LIVE FOREVER                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Flow 6: Privacy Controls

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│  SETTINGS                                                       │
│  ────────                                                       │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  SHARING DEFAULTS                                       │    │
│  │  ────────────────                                       │    │
│  │                                                         │    │
│  │  My check-ins default to:                               │    │
│  │  ┌──────────────────────┐                               │    │
│  │  │ [x] Team only        │  ◄── Default                  │    │
│  │  │ [ ] My circle (8)    │                               │    │
│  │  │ [ ] Private (just me)│                               │    │
│  │  │ [ ] Public           │                               │    │
│  │  └──────────────────────┘                               │    │
│  │                                                         │    │
│  │  Share blockers automatically: [ON]                     │    │
│  │  Share wins to celebrate:      [OFF]                    │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  PATTERN CONTRIBUTION                                   │    │
│  │  ────────────────────                                   │    │
│  │                                                         │    │
│  │  [x] Include my patterns in collective analysis         │    │
│  │      (anonymous, aggregated only)                       │    │
│  │                                                         │    │
│  │  [ ] Share my energy levels with team                   │    │
│  │                                                         │    │
│  │  [x] Receive suggestions from THE FIELD                 │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                                                         │    │
│  │  YOUR DATA                                              │    │
│  │  ─────────                                              │    │
│  │                                                         │    │
│  │  [Download all my check-ins (JSON)]                     │    │
│  │                                                         │    │
│  │  [Delete all my data]                                   │    │
│  │                                                         │    │
│  │  [Leave this circle]                                    │    │
│  │                                                         │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│                                                                 │
│  PER-MESSAGE PRIVACY                                            │
│  ───────────────────                                            │
│                                                                 │
│  During any check-in, reply:                                    │
│                                                                 │
│  PRIVATE  = This update is for me only                          │
│  TEAM     = Share with my team                                  │
│  CIRCLE   = Share with my full 8                                │
│  PUBLIC   = Anyone can see                                      │
│                                                                 │
│  Example:                                                       │
│  ─────────                                                      │
│  User: "PRIVATE had a rough day, feeling burnt out"             │
│                                                                 │
│  System: "Noted privately. Take care of yourself.               │
│           This won't be shared with anyone."                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Summary: Time & Friction Targets

| Flow | Target Time | Max Taps/Messages |
|------|-------------|-------------------|
| SMS Quick | 15 seconds | 3 messages |
| SMS Full | 45 seconds | 6 messages |
| Web Full | 30 seconds | 8 taps |
| Voice | 45 seconds | 1 call |
| Onboarding | 60 seconds | 5 screens |

**(8) Respect attention. Deliver value. LIVE FREE.**
