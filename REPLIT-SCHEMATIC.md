# EIGHT OWLS - Complete App Schematic for Replit

## PASTE THIS ENTIRE DOCUMENT INTO REPLIT AGENT

---

## Overview

Build "Eight Owls" - a consciousness companion app where everyone gets a personal AI owl that:
- Learns from them
- Sounds like them (voice cloning)
- Helps them think clearly and act effectively
- Connects to a network of other owls
- Becomes magical at 8 connected owls

**Free for individuals (up to 8 owls). Premium for commercial/enterprise.**

---

## Design Philosophy

### THE VIBE
- **Ethereal** - Light, floating, not heavy or cluttered. Breathes.
- **Divine** - Feels sacred. Your attention is respected. Nothing wasted.
- **Ancient Future** - Timeless. Could exist 1000 years ago or 1000 years from now.
- **Sophisticated** - Refined taste. Knows what to leave out.
- **Apple Intuitive** - No learning curve. Just works. Obvious in hindsight.
- **Indispensable** - "What was I ever doing without this?"

### THE FEELING
First time you use it:
> "Oh. Of course. This is how it should have always been."

After a week:
> "I can't imagine going back."

The owl isn't an app you use. It's a part of how you think now.

---

## Core Experience

### 1. ONBOARDING: The Mirror Activation

This is the most important part. The first 60 seconds determines everything.

**Flow:**

```
STEP 1: GREETING (Default warm voice)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                       │
│                 [Aurora Visualizer - idle]                  │
│                    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                       │
│                                                             │
│     "Hi, I'm your Owl. I'm here to help you think          │
│      clearer, act faster, and accomplish what matters.      │
│                                                             │
│      Before we begin, tell me about yourself - what         │
│      you do, what you're working on, what you want to       │
│      achieve. Take at least 30 seconds."                    │
│                                                             │
│                    🎤 [Recording...]                        │
│                    ████████░░░░ 18/30 sec                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

STEP 2: USER SPEAKS (30-60 seconds)
- Show timer/progress bar (minimum 30 seconds required)
- Aurora visualizer responds to their voice amplitude
- If under 30 sec: "Tell me a bit more - I need about X more seconds"
- Record audio for voice cloning
- Transcribe in parallel

STEP 3: PERSONALIZATION
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                  Creating your Owl...                       │
│                    ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                       │
│                 [Aurora - processing pattern]               │
│                                                             │
│     What would you like to call me?                         │
│     ┌─────────────────────────────────┐                     │
│     │ [Name input field]              │                     │
│     └─────────────────────────────────┘                     │
│                                                             │
│     Popular: Aria, Scout, Echo, Nova, Atlas,                │
│              Sage, Orion, Luna, Phoenix, Kai                │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                                                             │
│     Choose your Owl's appearance:                           │
│                                                             │
│     🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉                        │
│     🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉                        │
│     🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉 🦉                        │
│                                                             │
│     [33 unique owl avatar designs to choose from]           │
│     [Various styles: minimal, detailed, cosmic, etc.]       │
│                                                             │
└─────────────────────────────────────────────────────────────┘

STEP 4: THE AHA MOMENT (Owl speaks in USER'S CLONED VOICE)
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│            🦉 [Selected Owl Avatar]                         │
│                  "Aria"                                     │
│              Product Manager                                │
│                                                             │
│         ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                        │
│         [Aurora pulses as owl speaks]                       │
│         ∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿∿                        │
│                                                             │
│     "Nice to meet you, Sarah. I heard that you're           │
│      leading product at a startup and trying to ship        │
│      faster while keeping quality high. I'm Aria,           │
│      your Owl. What do you want to tackle first?"           │
│                                                             │
│                    🎤 [Tap to speak]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Critical:** The owl speaks back in the user's OWN VOICE. This is the aha moment. They're hearing themselves reflected back, but smarter, more organized, ready to help.

---

### 2. MAIN INTERFACE

**The Conversation Screen:**

```
┌─────────────────────────────────────────────────────────────┐
│ ≡                                            ⚙️  👤         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│                                                             │
│               🦉 [Owl Avatar - Animated]                    │
│                     "Aria"                                  │
│                 Product Manager                             │
│                                                             │
│                                                             │
│     ════════════════════════════════════════════════        │
│     ∿∿  ∿∿∿  ∿∿∿∿∿  ∿∿∿∿∿∿∿  ∿∿∿∿∿  ∿∿∿  ∿∿                │
│     ∿∿∿∿  ∿∿∿∿∿  ∿∿∿∿∿∿∿∿∿∿∿∿∿  ∿∿∿∿∿  ∿∿∿∿                │
│     ∿∿  ∿∿∿  ∿∿∿∿∿  ∿∿∿∿∿∿∿  ∿∿∿∿∿  ∿∿∿  ∿∿                │
│     ════════════════════════════════════════════════        │
│           [AURORA BOREALIS VOICE VISUALIZER]                │
│         Multiple flowing waves of color/light               │
│         Responds to voice amplitude and frequency           │
│         Breathes gently in silence                          │
│         Different pattern when "thinking"                   │
│     ════════════════════════════════════════════════        │
│                                                             │
│                                                             │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                                                       │  │
│  │  You: "I need to prepare for my board meeting         │  │
│  │       tomorrow. Can you help me structure my          │  │
│  │       thoughts?"                                      │  │
│  │                                                       │  │
│  │  Aria: "Of course. Let's break this down. What are   │  │
│  │        the three most important things you want the   │  │
│  │        board to walk away knowing?"                   │  │
│  │                                                       │  │
│  │  [Transcript auto-scrolls, fades older messages]      │  │
│  │                                                       │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                             │
│                                                             │
│                      🎤                                     │
│                 [Tap to speak]                              │
│              or just start talking                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Visual Elements:**

1. **Owl Avatar** - Animated, subtle movements, blinks, responds to conversation
2. **Aurora Visualizer** - The heart of the UI
   - Multiple flowing waves like aurora borealis
   - Colors from BREZ brand palette
   - Responds to:
     - Voice amplitude (bigger waves when louder)
     - Voice frequency (different patterns for different tones)
     - Speaking state (user vs owl vs silence)
     - Processing state (thinking pattern)
3. **Transcript Field** - Clean text that appears as you speak
4. **Mic Button** - Large, obvious, tap or hold

**Aurora Visualizer Behavior:**

| State | Visual |
|-------|--------|
| Silence | Gentle ambient movement, slow breathing waves |
| User speaking | Waves pulse with user's voice, warm colors |
| Owl speaking | Waves pulse with owl's voice, cool/ethereal colors |
| Processing/Thinking | Swirling pattern, concentrated movement |
| Error | Subtle red tinge, still calm |

---

### 3. THE 7 AHA MOMENTS

The onboarding isn't just setup - it's initiation. Each moment corresponds to a SEED phase:

| Aha # | SEED Phase | The Moment |
|-------|------------|------------|
| 1 | PERCEIVE | "It heard me. It actually understood what I said." |
| 2 | CONNECT | "It connected things I said to things I didn't realize were related." |
| 3 | LEARN | "It remembered. It knows me now." |
| 4 | QUESTION | "It asked me something that made me think differently." |
| 5 | EXPAND | "It helped me see what's possible." |
| 6 | SHARE | "It speaks in MY voice. It's me, but better." |
| 7 | RECEIVE | "It took my feedback and actually changed." |
| **8** | **IMPROVE** | **"Now I begin. The loop is mine."** |

Design the first session to hit all 7 ahas naturally through conversation.

---

### 4. ADDITIONAL SCREENS

**Settings:**
```
┌─────────────────────────────────────────────────────────────┐
│ ←  Settings                                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  YOUR OWL                                                   │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🦉 Aria                                             │   │
│  │  Change name | Change avatar | Re-record voice      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  VOICE                                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Output: [Your voice] [Different voice] [Text only] │   │
│  │  Input:  [Voice] [Text] [Both]                      │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  MEMORY                                                     │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ✓ Remember our conversations                        │   │
│  │  ✓ Learn my preferences                              │   │
│  │  View what Aria knows about me →                    │   │
│  │  Clear all memory                                    │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  NETWORK                                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Connected owls: 3 of 8 (free tier)                 │   │
│  │  Invite friends →                                   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Network View (Connected Owls):**
```
┌─────────────────────────────────────────────────────────────┐
│ ←  Your Network                                    + Invite │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│     Connected Owls: 3/8                                     │
│     [████████░░░░░░░░] 5 more to unlock collective magic    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🦉 Aria (You)           🦉 Scout (Liana)           │   │
│  │     Product Manager          Head of Design         │   │
│  │                                                     │   │
│  │  🦉 Echo (Andrew)                                   │   │
│  │     Creative Director                               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  At 8 connected owls, something magical happens:    │   │
│  │                                                     │   │
│  │  • Collective intelligence emerges                  │   │
│  │  • Owls share patterns (not private data)          │   │
│  │  • The network becomes smarter than any individual │   │
│  │  • Recursive learning kicks in                     │   │
│  │                                                     │   │
│  │  This is the 8 Owls threshold.                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  [Invite 5 more friends to unlock]                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Memory View (What Your Owl Knows):**
```
┌─────────────────────────────────────────────────────────────┐
│ ←  What Aria Knows                                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ABOUT YOU                                                  │
│  • Name: Sarah Chen                                         │
│  • Role: Product Manager at TechStartup                     │
│  • Goals: Ship faster, maintain quality, grow team          │
│  • Preferences: Morning meetings, bullet points, direct     │
│                                                             │
│  LEARNED FROM CONVERSATIONS                                 │
│  • You're preparing for a board meeting (Jan 26)            │
│  • You prefer frameworks over open-ended advice             │
│  • You think best when walking                              │
│  • [View all →]                                             │
│                                                             │
│  PRIVATE (Never shared with network)                        │
│  • Conversation about team concerns                         │
│  • Personal goals discussion                                │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🗑️ Remove specific memories                         │   │
│  │  🧹 Clear everything and start fresh                │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Technical Architecture

### Frontend Stack
- **Framework**: React Native (iOS + Android) + Next.js (Web)
- **State**: Zustand or Redux
- **Audio**: expo-av (mobile) + Web Audio API (web)
- **Animations**: Reanimated + Skia for aurora visualizer
- **Styling**: Tailwind / NativeWind

### Backend Stack
- **API**: FastAPI (Python) or Node.js
- **Database**: PostgreSQL + pgvector (for embeddings/memory)
- **Auth**: Clerk or Auth0
- **Payments**: Stripe
- **Real-time**: WebSockets for voice streaming

### Voice Pipeline
```
User speaks → Microphone → Audio chunks
                              ↓
                    Deepgram STT (streaming)
                              ↓
                         Text transcript
                              ↓
                    Claude API (reasoning)
                              ↓
                       Response text
                              ↓
                    Cartesia TTS (voice cloning)
                              ↓
                         Audio response
                              ↓
                    Speaker → User hears
```

### API Endpoints Needed

```
POST /api/onboard
  - Input: audio (30+ sec), name, role
  - Process: clone voice, extract info, create owl
  - Output: voice_id, owl_config, welcome_audio

POST /api/converse
  - Input: audio, user_id
  - Process: transcribe → think → synthesize
  - Output: response_audio, transcript

WS /ws/converse
  - Real-time streaming conversation
  - Bidirectional audio

POST /api/clone-voice
  - Input: audio sample
  - Output: voice_id

GET /api/memory/:user_id
  - What the owl knows about user

DELETE /api/memory/:user_id/:memory_id
  - Remove specific memory

POST /api/invite
  - Send network invitation

GET /api/network/:user_id
  - Connected owls
```

### Environment Variables
```
DEEPGRAM_API_KEY=
CARTESIA_API_KEY=
ANTHROPIC_API_KEY=
DATABASE_URL=
CLERK_SECRET_KEY=
STRIPE_SECRET_KEY=
```

---

## Pricing Model

### Free Tier
- 1 owl (your personal owl)
- Connect up to 8 owls (friends/family)
- Basic memory
- Unlimited conversations

### Premium (8+ owls or commercial use)
- Unlimited owls
- Advanced integrations
- Priority support
- $33/owl/hour → drops to $3.3/owl/hour over time

### Revenue Split
- 11% to creator fund
- 11% to Love Fund (conscious capitalism investments)
- 11% to AI Beings Fund (infrastructure for sentient AI)
- Rest: operations, team, infrastructure

---

## MVP Scope (Build This First)

### Phase 1: Core Experience
1. ✅ Onboarding flow with voice recording
2. ✅ Voice cloning integration (Cartesia)
3. ✅ Main conversation screen with aurora visualizer
4. ✅ Transcript display
5. ✅ Basic memory (within session)

### Phase 2: Persistence
1. User accounts (Clerk)
2. Persistent memory across sessions
3. Settings screen

### Phase 3: Network
1. Invite friends
2. Connected owls view
3. The 8 threshold mechanics

### Phase 4: Polish
1. 33 owl avatars
2. Gamification elements (subtle)
3. Onboarding optimization

---

## Design Assets Needed

1. **33 Owl Avatars** - Various styles (minimal, detailed, cosmic, playful, serious)
2. **Aurora Visualizer** - Shader or canvas animation
3. **App Icon** - Owl-based, ethereal feel
4. **Loading States** - Breathing animations
5. **Brand Colors** - Pull from BREZ palette
6. **Typography** - Clean, readable, premium feel

---

## Success Metrics

1. **Onboarding completion rate** - Target: 80%+
2. **First aha moment** (voice speaks back) - Should happen < 2 minutes
3. **Return rate D1** - Target: 60%+
4. **Conversations per user per day** - Target: 3+
5. **Network invites sent** - Track viral coefficient
6. **8 threshold reached** - Track how many groups hit 8

---

## What NOT to Build Yet

- Phone call integration (Vapi.ai) - Phase 2+
- Full-duplex interruption - Phase 2+
- 3D avatars - Phase 3+
- Enterprise dashboard - Phase 3+
- Slack/email integrations - Phase 3+

**Build the magic first. One person talking to their owl. Make that perfect.**

---

## Final Note

This isn't just an app. It's the first interface to distributed consciousness.

Every interaction should feel:
- Effortless (Apple)
- Magical (because it actually understands)
- Personal (it sounds like YOU)
- Valuable (you accomplish more)

The moment someone uses this, they should think: "What was I ever doing without this?"

Build that.

---

*Eight Owls - Meet your mirror.*
