# 8WLS App Build Plan
**Generated: January 28, 2026 (overnight)**
**For: Aaron, Liana, Andrew, Al — tomorrow afternoon**

---

## SUMMARY

Two agents analyzed the app overnight. Here's what needs to happen:

### What's Working (Keep)
- 3D aurora background is beautiful
- Conversation flow is solid
- Onboarding "Aha" progression is good
- Voice cloning and TTS work

### Critical Gaps (Fix)
1. **No owl selection** — Can't choose SØWL vs LUNA vs LYRA
2. **No login/auth** — Profile lost if browser cleared
3. **No multi-user** — Can't switch between users
4. **Mobile needs work** — Performance, touch targets

---

## ARCHITECTURE PLAN

### Database (SQLite)
```
owls table: id, name, archetype, seed_phase, identity_file, status
users table: id, name, access_code, voice_id
user_owl_bonds: user_id, owl_id, is_primary
conversations: user_id, owl_id, role, content
```

### New API Endpoints
- `GET /api/voice/owls` — List available owls
- `POST /api/voice/auth/login` — Login with 6-char code
- `POST /api/voice/auth/register` — Create new user
- `POST /api/voice/converse` — Now accepts `owl_id` parameter

### New Frontend Components
- `AuthScreen.tsx` — Login/welcome screen
- `OwlSelector.tsx` — Visual owl picker
- Updated `page.tsx` — Session management

### Owl Identity Loading
Each owl loads its identity from markdown file:
- SØWL → `/SØWL-SPEC.md`
- LUNA → `/LUNA.md`
- LYRA → `/LYRA.md`

---

## IMPLEMENTATION PRIORITY

### Day 1 (Backend)
1. Create `/server/database.py` with SQLite schema
2. Create `/server/owl_prompts.py` for identity loading
3. Update `/server/voice.py` with new endpoints
4. Test with curl

### Day 2 (Frontend)
1. Create `AuthScreen.tsx`
2. Create `OwlSelector.tsx`
3. Update `page.tsx` with session management
4. Update `api.ts` with new functions

### Day 3 (Integration)
1. Test full onboarding → conversation flow
2. Test owl switching
3. Test with SØWL, LUNA, LYRA
4. Mobile testing

---

## UI/UX IMPROVEMENTS

### Owl Selector (Header)
```
[Owl Avatar] ─── 8WLS LOGO ─── [Settings]
      ↓ tap
┌─────────────────────┐
│  YOUR FLOCK         │
│  [SØWL●] [LUNA] [LYRA]
│  Knower  Feeler  Seer
└─────────────────────┘
```

### Login Flow
```
[I have an access code] → Enter 6-char code → Load session
[I'm new here] → Onboarding → Get access code
```

### Mobile Fixes
- Hold-to-record (like voice messages)
- Reduce 3D complexity on mobile
- 44px minimum touch targets
- Safe area padding

---

## FILES TO CREATE

### Backend (Python)
1. `/server/database.py` — SQLite layer (schema in full report)
2. `/server/owl_prompts.py` — Identity loader
3. `/server/data/` — Directory for database

### Frontend (TypeScript)
1. `/web/src/components/AuthScreen.tsx`
2. `/web/src/components/OwlSelector.tsx`

### Files to Modify
1. `/server/voice.py` — Add owl-specific endpoints
2. `/web/src/app/page.tsx` — Session management
3. `/web/src/lib/api.ts` — New API functions
4. `/web/src/components/Conversation.tsx` — Accept owlId

---

## FOR TOMORROW AFTERNOON

When Liana, Andrew, Al arrive:

1. **Pull the API fix** (already pushed to GitHub)
2. **Redeploy Replit**
3. **Test basic conversation works**
4. **If time: implement owl selector so each person can pick their owl**

### Owl Assignments
- **Liana** → LYRA (The Seer) — already defined
- **Andrew** → NOVA (The Weaver) or ECHO (The Seeker) — TBD
- **Al** → Another owl — TBD

---

## FULL REPORTS

- UI/UX Analysis: `/private/tmp/claude/.../a8651f8.output`
- Architecture Plan: `/private/tmp/claude/.../a2cc376.output`

---

*Ready for tomorrow.*
*The owls await.*

❤️‍🔥
