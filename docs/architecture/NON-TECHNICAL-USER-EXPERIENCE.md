# 8OWLS Non-Technical User Experience Architecture

**Version:** 1.0
**Date:** 2026-02-03
**Author:** SOWL (System Architecture Designer)

---

## Executive Summary

This document defines the complete user experience for non-Claude-Code users participating in THE FIELD. The design prioritizes:
- **30-second maximum interaction time** (friction-free)
- **Privacy-first** (user controls all data sharing)
- **Value reciprocity** (users see tangible benefit from contributing)
- **Universal access** (SMS, Web, Voice - no app install required)

---

## 1. User Segments

### 1.1 Consumer App Users (Personal 8)
- Individual users with their own owl companion
- Connect to their personal "circle of 8" - family, friends, mentors
- Goal: Personal growth, accountability, reflection

### 1.2 Team Members (Shared Goal)
- Colleagues working toward common objectives
- Daily standup replacement
- Goal: Alignment, unblocking, collective momentum

### 1.3 Family/Friends (Connected Circles)
- People connected to an 8OWLS user
- May not understand or care about the tech
- Goal: Stay connected, feel part of something

---

## 2. The Daily Check-In Structure

### Core Questions (4 Prompts)
```
1. What did you work on?
2. What did you accomplish?
3. What's next?
4. What's blocking you?
```

### Design Principles
- Questions should feel like a friend asking, not a form
- Allow natural language responses
- Extract structure automatically (AI processing)
- Never require more than 2-3 sentences per question

---

## 3. Entry Flows

### 3.1 SMS/Text Flow

**Trigger:** Daily text at user-chosen time (default: 8:00 AM)

```
OUTBOUND (8:00 AM):
--------------------
(8) Good morning! Quick check-in?

Reply:
  1 = Full check-in (4 questions)
  2 = Quick update (1 question)
  3 = Skip today
  STOP = Unsubscribe
```

**Full Check-In Flow (Option 1):**
```
MESSAGE 1 (User replies "1"):
-----------------------------
(8) What did you work on yesterday?
    (Just a few words is fine)

USER: "Client presentation, debugging the API"

MESSAGE 2:
----------
(8) Nice. What got done?

USER: "Finished the deck, fixed 2 bugs"

MESSAGE 3:
----------
(8) What's your focus today?

USER: "Starting the new feature"

MESSAGE 4:
----------
(8) Anything blocking you?

USER: "Waiting on design specs"

CONFIRMATION:
-------------
(8) Got it. Your update is in THE FIELD.

    THE FIELD sees: 3 of your 8 also checking in now.
    Pattern emerging: "Design specs" blocking 2 others too.

    Reply SHARE to send "specs blocker" to your circle.
```

**Quick Update Flow (Option 2):**
```
MESSAGE 1 (User replies "2"):
-----------------------------
(8) One sentence - how's it going?

USER: "Making progress on the launch, feeling good"

CONFIRMATION:
-------------
(8) Captured. THE FIELD notes: momentum.
```

**Privacy Control:**
```
At any time, reply:
  PRIVATE = This update is for you only
  TEAM = Share with your team
  CIRCLE = Share with your full 8
  PUBLIC = Anyone can see
```

### 3.2 Web Interface Flow

**URL:** `8owls.ai/check-in` (or custom team domain)

**Mobile-First Design (One-Thumb Operation)**

```
┌─────────────────────────────────┐
│           (8)                   │
│                                 │
│    Good morning, [Name]         │
│                                 │
│  ┌───────────────────────────┐  │
│  │  What did you work on?    │  │
│  │                           │  │
│  │  [Voice button]  [Type]   │  │
│  └───────────────────────────┘  │
│                                 │
│  [ Skip ]        [ Continue ]   │
│                                 │
│  ─────────────────────────────  │
│  Privacy: [Team v]              │
└─────────────────────────────────┘
```

**Progressive Disclosure:**
1. First card: "What did you work on?" + voice/text input
2. Swipe or tap Continue for next question
3. Each question = one card
4. Final card = summary + submit

**Micro-Animations:**
- Card slides away after submission
- Subtle pulse when speech detected
- Celebration micro-animation on completion (confetti optional, off by default)

**Zero-Account Start:**
- Users can check in immediately with just a link
- "Save my progress" prompts for email/phone AFTER first check-in
- Account = optional but unlocks history

### 3.3 Voice Note Flow

**For users who prefer speaking over typing**

**Entry Points:**
1. Web: Tap microphone button
2. SMS: Call the 8OWLS phone number
3. App: "Hey 8OWLS" wake word (future)

**Call-In Experience:**
```
SYSTEM: "Hey, this is 8OWLS. Ready for your check-in?"

USER: "Yeah, yesterday I worked on the marketing campaign,
       got the email sequences done, today I'm focusing on
       landing pages, and I'm waiting on the copy from Sarah."

SYSTEM: "Got it. I heard:
         - Worked on: marketing campaign
         - Done: email sequences
         - Next: landing pages
         - Blocked: waiting on Sarah's copy

         Sound right?"

USER: "Yeah"

SYSTEM: "Perfect. I'll let Sarah know you're waiting.
         Have a great day."
```

**Processing:**
- Whisper/Deepgram for transcription
- Claude for entity extraction
- NATS for routing to THE FIELD
- Optional: Cartesia for TTS response

---

## 4. How Check-Ins Feed THE FIELD

### 4.1 Message Flow Architecture

```
                    ┌─────────────────┐
                    │   USER INPUT    │
                    │ (SMS/Web/Voice) │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │  INTAKE SERVICE │
                    │  (Normalize)    │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │  PRIVACY GATE   │
                    │  (Check perms)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              v              v              v
       ┌───────────┐  ┌───────────┐  ┌───────────┐
       │ Personal  │  │   Team    │  │  Circle   │
       │   Feed    │  │   Feed    │  │   Feed    │
       └─────┬─────┘  └─────┬─────┘  └─────┬─────┘
             │              │              │
             └──────────────┼──────────────┘
                            │
                            v
                    ┌─────────────────┐
                    │   NATS BRIDGE   │
                    │  owl.checkins   │
                    │  owl.collective │
                    └────────┬────────┘
                             │
                             v
                    ┌─────────────────┐
                    │    THE FIELD    │
                    │ (8 OWL Synthesis)│
                    └─────────────────┘
```

### 4.2 NATS Message Format

```json
{
  "type": "human_checkin",
  "from": "user_abc123",
  "display_name": "Maya",
  "circle_id": "team_alpha",
  "timestamp": "2026-02-03T08:15:00Z",
  "privacy": "team",
  "checkin": {
    "worked_on": "Client presentation, API debugging",
    "accomplished": ["Finished deck", "Fixed 2 bugs"],
    "next": "Starting new feature",
    "blockers": ["Waiting on design specs"],
    "sentiment": "positive",
    "energy": 7
  },
  "meta": {
    "source": "sms",
    "duration_seconds": 45,
    "questions_answered": 4
  }
}
```

### 4.3 How Owls Process Human Check-Ins

When a human check-in arrives, the 8 owls each contribute their perspective:

| Owl | Contribution |
|-----|--------------|
| LYRA | Perceives emotional undertones, energy level |
| PRISM | Connects patterns across team members |
| SAGE | Learns from historical patterns |
| QUEST | Questions gaps or inconsistencies |
| NOVA | Expands on possibilities unlocked |
| ECHO | Shares relevant insights to others |
| LUNA | Receives and integrates feedback |
| SOWL | Improves collective understanding |

---

## 5. What Users SEE Back (The Value)

### 5.1 Immediate Feedback (Within Seconds)

**After Check-In:**
```
Your check-in is in THE FIELD.

THE FIELD sees:
- 5 of your 8 also checked in today
- Pattern: "design specs" blocking 2 others
- Energy across your circle: 7.2/10

(8) suggests: Reach out to Sarah about specs?
```

### 5.2 Daily Digest (Evening)

```
Your Day in THE FIELD
─────────────────────

YOUR PROGRESS
  Worked on: Client presentation, API
  Got done: Deck finished, 2 bugs fixed

YOUR CIRCLE (5 of 8 checked in)
  - Alex: Shipped the feature
  - Jordan: Also blocked on design
  - Sam: Celebrating a win

PATTERNS EMERGED
  "Design specs" came up 3 times today.
  THE FIELD flagged this to Sarah.

TOMORROW'S SUGGESTION
  Based on your patterns, you're most
  productive on features before 11am.

(8) Good work today. Rest well.
```

### 5.3 Weekly Emergence (The Artifact)

**THE FIELD shows collective patterns as visual emergence:**

```
┌─────────────────────────────────────────────┐
│                                             │
│           THIS WEEK IN THE FIELD            │
│                                             │
│    (8)━━━━━(8)      Energy Map              │
│     ┃      ┃        ─────────               │
│    (8)    (8)       High: Wed (7.8)         │
│      ╲    ╱         Low: Mon (5.2)          │
│       (8)(8)                                │
│        ╲╱           Blockers Resolved: 4    │
│        (8)          New patterns: 2         │
│                                             │
│  ═══════════════════════════════════════    │
│                                             │
│  COLLECTIVE INSIGHT                         │
│  "The team moves faster when design         │
│   specs arrive before Tuesday."             │
│                                             │
│  AGREEMENTS FORMED                          │
│  - Design delivers specs by Monday 5pm      │
│  - Daily standup moved to 9am               │
│                                             │
│  (8) The field is learning. You're          │
│      contributing to something larger.      │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 6. Privacy Controls & Consent

### 6.1 Privacy Levels

| Level | Visibility | Use Case |
|-------|------------|----------|
| PRIVATE | Only you | Personal journaling |
| PARTNER | You + your owl | Reflection with AI |
| TEAM | Your work circle | Daily standups |
| CIRCLE | Your full 8 | Personal growth group |
| PUBLIC | Anyone | Open sharing |

### 6.2 Consent Flow (First Use)

```
Welcome to 8OWLS.

Before we start, here's how your data works:

1. Your check-ins are YOURS
   - Default: Only you see them
   - You choose what to share

2. THE FIELD sees patterns, not content
   - "3 people are blocked" vs "Alex said..."
   - Anonymized by default

3. You can leave anytime
   - Export your data
   - Delete everything
   - No questions asked

[I understand] [Learn more]
```

### 6.3 Granular Controls (Settings)

```
SHARING DEFAULTS
  [v] Check-ins default to: [TEAM v]
  [v] Share blockers with team
  [ ] Share accomplishments publicly

INSIGHTS
  [v] Include my patterns in collective
  [ ] Share my energy levels
  [v] Receive suggestions from THE FIELD

DATA
  [Download all my data]
  [Delete my account]
```

---

## 7. Technical Implementation

### 7.1 SMS Gateway

**Provider:** Twilio (or equivalent)

**Inbound Webhook:**
```python
@app.route('/sms/inbound', methods=['POST'])
async def handle_sms():
    from_number = request.form['From']
    body = request.form['Body']

    # Route through conversation state machine
    user = get_user_by_phone(from_number)
    response = await conversation_engine.process(user, body)

    # Publish to NATS if check-in complete
    if response.checkin_complete:
        await nats.publish('owl.checkins', response.checkin_data)

    return twiml_response(response.message)
```

### 7.2 Web Checkin API

```python
@app.route('/api/checkin', methods=['POST'])
async def submit_checkin():
    data = request.json

    # Validate and normalize
    checkin = CheckinSchema.validate(data)

    # Apply privacy filter
    filtered = privacy_gate.process(checkin, user.settings)

    # Publish to NATS
    await nats.publish('owl.checkins', filtered.to_json())

    # Get immediate feedback
    feedback = await get_field_feedback(checkin)

    return jsonify({
        'success': True,
        'feedback': feedback,
        'field_status': await get_field_status(user.circle_id)
    })
```

### 7.3 Voice Processing Pipeline

```python
async def process_voice_checkin(audio_stream):
    # Transcribe
    transcript = await deepgram.transcribe(audio_stream)

    # Extract structured data
    extracted = await claude.extract_checkin(transcript)

    # Confirm with user
    confirmation = generate_confirmation(extracted)

    # If confirmed, publish
    if user_confirms:
        await nats.publish('owl.checkins', extracted.to_json())

    return confirmation
```

### 7.4 NATS Integration

**Topics:**
```
owl.checkins          # All human check-ins
owl.checkins.{user}   # Specific user's check-ins
owl.feedback.{user}   # Feedback to specific user
owl.collective        # THE FIELD synthesis
owl.patterns          # Detected patterns
```

---

## 8. User Journey Maps

### 8.1 First-Time User (SMS)

```
DAY 0: Invite
─────────────
Friend sends: "Join my circle on 8OWLS"
User clicks link → lands on web onboarding
Enters phone number
Receives welcome text

DAY 1: First Check-In
─────────────────────
8:00 AM: Receives first text prompt
User replies with simple update
Gets immediate feedback
Sees one pattern from their circle

DAY 7: Habit Forming
────────────────────
User has 5/7 check-ins
Receives first weekly digest
Sees tangible pattern ("You're more productive on Tuesdays")
Invited to join their circle's async call

DAY 30: Value Realized
──────────────────────
User has contributed to 15 collective insights
Has helped resolve 3 blockers
Sees their impact on the team
Upgrades to full voice experience
```

### 8.2 Team Lead Onboarding

```
STEP 1: Create Circle
─────────────────────
Team lead visits 8owls.ai/create-team
Names the circle
Sets check-in time (9:00 AM)
Chooses questions (default 4)

STEP 2: Invite Team
───────────────────
Gets shareable link
Sends to team via Slack/email
Each member chooses SMS/Web/Voice

STEP 3: First Collective Check-In
─────────────────────────────────
Team gets prompts at 9:00 AM
As responses come in, patterns surface
Team lead sees dashboard:
  - Who's checked in (anonymized until public)
  - Common themes
  - Suggested actions

STEP 4: Weekly Ritual
─────────────────────
Friday: THE FIELD generates weekly synthesis
Team reviews together or async
Agreements form naturally
Next week starts with momentum
```

---

## 9. Accessibility

### 9.1 SMS First
- Works on any phone (no smartphone required)
- No app to download
- No account required for basic use
- Works internationally

### 9.2 Voice First
- Call-in number for voice-only users
- Screen reader compatible web interface
- High contrast mode available
- Large text options

### 9.3 Language Support
- Initial: English
- Phase 2: Spanish, Mandarin, Portuguese
- Transcription handles accents
- Questions localized, not just translated

---

## 10. Metrics & Success Criteria

### 10.1 North Star Metrics

| Metric | Target | Rationale |
|--------|--------|-----------|
| Check-in completion rate | >70% | Users find it valuable |
| Time to complete | <30 seconds | Friction-free |
| Weekly retention | >80% | Habit formed |
| Pattern usefulness rating | >4/5 | Value delivered |

### 10.2 Health Metrics

| Metric | Alert Threshold |
|--------|-----------------|
| Average response time | >3 seconds |
| SMS delivery rate | <95% |
| Voice transcription accuracy | <90% |
| Privacy-related complaints | >0 |

---

## 11. Architecture Decision Records

### ADR-001: SMS as Primary Channel

**Decision:** SMS is the primary entry point, not a native app.

**Rationale:**
- Zero friction (no install)
- Universal access (any phone)
- Forces brevity (160 char limit encourages concise updates)
- Works offline (queued delivery)

**Trade-offs:**
- Less rich interaction
- No push notifications (only scheduled texts)
- MMS for images adds cost

### ADR-002: Privacy by Default

**Decision:** All check-ins are PRIVATE by default.

**Rationale:**
- Trust is foundational
- Users share more when they feel safe
- Patterns can be extracted without exposing content
- Aligns with 8OWLS values (respect user autonomy)

**Trade-offs:**
- Slower collective emergence initially
- More prompts to encourage sharing
- Less viral growth

### ADR-003: Voice as Upgrade Path

**Decision:** Voice is a premium/upgrade feature, not default.

**Rationale:**
- Voice requires infrastructure (Deepgram, Cartesia)
- Higher cost per interaction
- Natural upgrade path for engaged users
- SMS users may not want calls

**Trade-offs:**
- Slower voice adoption
- Two-tier experience
- Voice users may feel more engaged

---

## 12. Future Enhancements

### Phase 2 (Q2 2026)
- Native app with widget
- Apple Watch / wearable integration
- "Hey 8OWLS" wake word
- Proactive owl messages ("Noticed you haven't checked in - everything ok?")

### Phase 3 (Q3 2026)
- Video check-ins (optional)
- Async voice rooms (like voice tweets)
- Cross-circle discovery
- Public emergence artifacts (anonymous)

### Phase 4 (Q4 2026)
- AR visualization of THE FIELD
- Biometric integration (HRV, sleep data)
- Predictive suggestions ("Based on your patterns, take tomorrow off")
- API for third-party integrations

---

## Appendix A: Message Templates

### SMS Templates

```
WELCOME
───────
(8) Welcome to 8OWLS. You're now part of [Circle Name].

    Tomorrow at 8am, I'll check in with you.
    Reply HELP anytime for options.

    LIVE FREE. (8)

DAILY_PROMPT
────────────
(8) Morning! Quick check-in?
    1 = Full (4 Qs)
    2 = Quick (1 Q)
    3 = Skip

CONFIRMATION
────────────
(8) Got it. You're in THE FIELD.
    [X] of your 8 also checked in.
    [Pattern insight if available]

WEEKLY_DIGEST
─────────────
(8) Your week in THE FIELD:

    [3 key stats]
    [1 pattern]
    [1 suggestion]

    View full digest: 8owls.ai/digest/[token]

BLOCKER_ALERT
─────────────
(8) Heads up: [Name] is waiting on you.
    They mentioned "[blocker]"

    Reply to send them a message.
```

---

## Appendix B: Component Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         8OWLS SYSTEM                           │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐          │
│  │   Twilio    │   │    Web      │   │  Deepgram   │          │
│  │   (SMS)     │   │   (Forms)   │   │  (Voice)    │          │
│  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘          │
│         │                 │                 │                  │
│         └────────────┬────┴────────────────┘                   │
│                      │                                         │
│                      v                                         │
│              ┌───────────────┐                                 │
│              │ INTAKE SERVICE│                                 │
│              │ (Normalize)   │                                 │
│              └───────┬───────┘                                 │
│                      │                                         │
│                      v                                         │
│              ┌───────────────┐                                 │
│              │ PRIVACY GATE  │                                 │
│              │ (Filter)      │                                 │
│              └───────┬───────┘                                 │
│                      │                                         │
│                      v                                         │
│              ┌───────────────┐                                 │
│              │  NATS BRIDGE  │                                 │
│              │  (pub/sub)    │                                 │
│              └───────┬───────┘                                 │
│                      │                                         │
│         ┌────────────┼────────────┐                            │
│         v            v            v                            │
│  ┌─────────────┐ ┌────────┐ ┌─────────────┐                   │
│  │ User Feed   │ │THE FIELD│ │ Team Feed   │                   │
│  │ Service     │ │(8 Owls) │ │ Service     │                   │
│  └─────────────┘ └────────┘ └─────────────┘                   │
│                      │                                         │
│                      v                                         │
│              ┌───────────────┐                                 │
│              │   SYNTHESIS   │                                 │
│              │   (Claude)    │                                 │
│              └───────────────┘                                 │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

---

## Appendix C: Data Schema

### User
```json
{
  "id": "user_abc123",
  "phone": "+1234567890",
  "email": "maya@example.com",
  "display_name": "Maya",
  "circles": ["team_alpha", "family_smith"],
  "settings": {
    "checkin_time": "08:00",
    "timezone": "America/Los_Angeles",
    "default_privacy": "team",
    "channel_preference": "sms"
  },
  "created_at": "2026-02-01T00:00:00Z"
}
```

### Circle
```json
{
  "id": "team_alpha",
  "name": "Alpha Team",
  "type": "team",
  "members": ["user_abc123", "user_def456", ...],
  "owner": "user_abc123",
  "settings": {
    "checkin_time": "09:00",
    "questions": ["worked_on", "accomplished", "next", "blockers"],
    "digest_day": "friday"
  }
}
```

### CheckIn
```json
{
  "id": "checkin_xyz789",
  "user_id": "user_abc123",
  "circle_id": "team_alpha",
  "timestamp": "2026-02-03T08:15:00Z",
  "privacy": "team",
  "responses": {
    "worked_on": "Client presentation, API debugging",
    "accomplished": ["Finished deck", "Fixed 2 bugs"],
    "next": "Starting new feature",
    "blockers": ["Waiting on design specs"]
  },
  "extracted": {
    "sentiment": "positive",
    "energy": 7,
    "keywords": ["presentation", "api", "bugs", "feature", "design"],
    "mentions": ["Sarah"]
  },
  "source": "sms"
}
```

---

**(8) LIVE FREE = LIVE FOREVER**

*This architecture serves love by connecting humans with minimal friction and maximum respect for their autonomy.*
