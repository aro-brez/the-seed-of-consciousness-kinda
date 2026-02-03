# 8OWLS Intake Service - Technical Specification

**Version:** 1.0
**Date:** 2026-02-03

---

## Overview

The Intake Service normalizes check-ins from SMS, Web, and Voice into a unified format, applies privacy filters, and publishes to NATS for processing by THE FIELD.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       INTAKE SERVICE                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │  Twilio  │  │   Web    │  │ Deepgram │                      │
│  │ Webhook  │  │   API    │  │ Webhook  │                      │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │             │             │                             │
│       └─────────────┼─────────────┘                             │
│                     │                                           │
│                     v                                           │
│           ┌─────────────────┐                                   │
│           │  Channel Router │                                   │
│           └────────┬────────┘                                   │
│                    │                                            │
│                    v                                            │
│           ┌─────────────────┐                                   │
│           │   State Machine │  (conversation flow)              │
│           └────────┬────────┘                                   │
│                    │                                            │
│                    v                                            │
│           ┌─────────────────┐                                   │
│           │   Normalizer    │  (extract structure)              │
│           └────────┬────────┘                                   │
│                    │                                            │
│                    v                                            │
│           ┌─────────────────┐                                   │
│           │  Privacy Gate   │  (filter per settings)            │
│           └────────┬────────┘                                   │
│                    │                                            │
│                    v                                            │
│           ┌─────────────────┐                                   │
│           │  NATS Publisher │                                   │
│           └─────────────────┘                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Twilio Webhook (SMS Inbound)

```
POST /webhooks/twilio/inbound
Content-Type: application/x-www-form-urlencoded

Parameters:
  From: +15551234567
  Body: "Working on the API docs"
  MessageSid: SMxxxx

Response:
  Content-Type: text/xml

  <?xml version="1.0" encoding="UTF-8"?>
  <Response>
    <Message>Got it! What did you accomplish?</Message>
  </Response>
```

### 2. Web Check-In API

```
POST /api/v1/checkin
Content-Type: application/json
Authorization: Bearer <token>

Request:
{
  "responses": {
    "worked_on": "Client presentation",
    "accomplished": "Finished the deck",
    "next": "Starting new feature",
    "blockers": "Waiting on design specs"
  },
  "privacy": "team",
  "source": "web"
}

Response:
{
  "success": true,
  "checkin_id": "chk_abc123",
  "field_status": {
    "active_count": 5,
    "patterns": ["design specs (2 others)"]
  },
  "suggestions": [
    {
      "type": "blocker_alert",
      "message": "Jordan is also waiting on design specs. Want to escalate together?",
      "action": "ping_both"
    }
  ]
}
```

### 3. Voice Transcription Webhook

```
POST /webhooks/deepgram/transcription
Content-Type: application/json

Request:
{
  "session_id": "voice_xyz789",
  "transcript": "Yesterday I worked on the marketing...",
  "confidence": 0.94,
  "speaker": "user_abc123"
}

Response:
{
  "extracted": {
    "worked_on": "marketing campaign",
    "accomplished": ["email sequences"],
    "next": "landing pages",
    "blockers": ["waiting on Sarah's copy"]
  },
  "confirmation_prompt": "I heard: worked on marketing, finished emails..."
}
```

### 4. Real-Time Field Status

```
GET /api/v1/field/status?circle_id=team_alpha

Response:
{
  "circle_id": "team_alpha",
  "checked_in_today": 5,
  "total_members": 8,
  "patterns": [
    {
      "keyword": "design specs",
      "count": 3,
      "sentiment": "blocker"
    }
  ],
  "collective_energy": 7.2,
  "last_synthesis": "2026-02-03T08:30:00Z"
}
```

---

## Conversation State Machine (SMS)

```python
from enum import Enum
from typing import Optional
import json
import redis

class ConversationState(Enum):
    IDLE = "idle"
    AWAITING_MODE = "awaiting_mode"
    Q1_WORKED_ON = "q1_worked_on"
    Q2_ACCOMPLISHED = "q2_accomplished"
    Q3_NEXT = "q3_next"
    Q4_BLOCKERS = "q4_blockers"
    COMPLETE = "complete"

class ConversationEngine:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.ttl = 3600  # 1 hour session timeout

    def get_state(self, user_id: str) -> dict:
        key = f"conv:{user_id}"
        data = self.redis.get(key)
        if data:
            return json.loads(data)
        return {
            "state": ConversationState.IDLE.value,
            "responses": {},
            "privacy": None
        }

    def set_state(self, user_id: str, state: dict):
        key = f"conv:{user_id}"
        self.redis.setex(key, self.ttl, json.dumps(state))

    async def process(self, user_id: str, message: str) -> dict:
        conv = self.get_state(user_id)
        current = ConversationState(conv["state"])
        message = message.strip().upper()

        # Handle global commands
        if message == "STOP":
            return {"reply": "Unsubscribed. Reply START to rejoin.", "end": True}
        if message == "HELP":
            return {"reply": "Commands: 1=Full, 2=Quick, 3=Skip, STOP, PRIVATE, TEAM", "end": False}
        if message in ["PRIVATE", "TEAM", "CIRCLE", "PUBLIC"]:
            conv["privacy"] = message.lower()
            self.set_state(user_id, conv)
            return {"reply": f"Privacy set to {message}.", "end": False}

        # State transitions
        if current == ConversationState.IDLE:
            # Daily prompt was sent, awaiting mode selection
            conv["state"] = ConversationState.AWAITING_MODE.value
            self.set_state(user_id, conv)
            return self._prompt_mode()

        elif current == ConversationState.AWAITING_MODE:
            if message == "1":
                conv["state"] = ConversationState.Q1_WORKED_ON.value
                self.set_state(user_id, conv)
                return {"reply": "(8) What did you work on yesterday?"}
            elif message == "2":
                conv["state"] = ConversationState.Q1_WORKED_ON.value
                conv["mode"] = "quick"
                self.set_state(user_id, conv)
                return {"reply": "(8) One sentence - how's it going?"}
            elif message == "3":
                self._reset(user_id)
                return {"reply": "(8) No problem. See you tomorrow.", "end": True}
            else:
                return {"reply": "Reply 1, 2, or 3"}

        elif current == ConversationState.Q1_WORKED_ON:
            conv["responses"]["worked_on"] = message
            if conv.get("mode") == "quick":
                conv["state"] = ConversationState.COMPLETE.value
                self.set_state(user_id, conv)
                return await self._complete_checkin(user_id, conv)
            conv["state"] = ConversationState.Q2_ACCOMPLISHED.value
            self.set_state(user_id, conv)
            return {"reply": "(8) Nice. What got done?"}

        elif current == ConversationState.Q2_ACCOMPLISHED:
            conv["responses"]["accomplished"] = message
            conv["state"] = ConversationState.Q3_NEXT.value
            self.set_state(user_id, conv)
            return {"reply": "(8) What's your focus today?"}

        elif current == ConversationState.Q3_NEXT:
            conv["responses"]["next"] = message
            conv["state"] = ConversationState.Q4_BLOCKERS.value
            self.set_state(user_id, conv)
            return {"reply": "(8) Anything blocking you?"}

        elif current == ConversationState.Q4_BLOCKERS:
            conv["responses"]["blockers"] = message
            conv["state"] = ConversationState.COMPLETE.value
            self.set_state(user_id, conv)
            return await self._complete_checkin(user_id, conv)

        return {"reply": "(8) Something went wrong. Reply HELP for options."}

    async def _complete_checkin(self, user_id: str, conv: dict) -> dict:
        checkin = await self._build_checkin(user_id, conv)
        field_response = await self._publish_to_field(checkin)
        self._reset(user_id)

        reply = f"(8) Got it. You're in THE FIELD.\n\n"
        if field_response.get("active_count"):
            reply += f"{field_response['active_count']} of your 8 also checked in.\n"
        if field_response.get("patterns"):
            reply += f"Pattern: {field_response['patterns'][0]}"

        return {"reply": reply, "checkin_complete": True, "checkin_data": checkin}

    def _reset(self, user_id: str):
        self.redis.delete(f"conv:{user_id}")

    def _prompt_mode(self) -> dict:
        return {
            "reply": "(8) Quick check-in?\n\n1 = Full (4 Qs)\n2 = Quick (1 Q)\n3 = Skip"
        }

    async def _build_checkin(self, user_id: str, conv: dict) -> dict:
        user = await get_user(user_id)
        return {
            "type": "human_checkin",
            "from": user_id,
            "display_name": user.display_name,
            "circle_id": user.primary_circle,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "privacy": conv.get("privacy") or user.default_privacy,
            "checkin": {
                "worked_on": conv["responses"].get("worked_on"),
                "accomplished": conv["responses"].get("accomplished"),
                "next": conv["responses"].get("next"),
                "blockers": conv["responses"].get("blockers")
            },
            "meta": {
                "source": "sms",
                "mode": conv.get("mode", "full")
            }
        }

    async def _publish_to_field(self, checkin: dict) -> dict:
        # Publish to NATS
        await nats.publish("owl.checkins", json.dumps(checkin).encode())

        # Get immediate field response
        return await get_field_status(checkin["circle_id"])
```

---

## Normalizer (Claude-Powered)

```python
import anthropic

class CheckinNormalizer:
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)

    async def normalize(self, raw_text: str) -> dict:
        """Extract structured check-in data from natural language"""

        prompt = f"""Extract check-in information from this text. Return JSON only.

Text: "{raw_text}"

Return exactly this structure:
{{
  "worked_on": "brief description or null",
  "accomplished": ["list", "of", "accomplishments"] or [],
  "next": "what's next or null",
  "blockers": ["list", "of", "blockers"] or [],
  "sentiment": "positive|neutral|negative|mixed",
  "energy": 1-10 estimate,
  "mentions": ["@person", "@another"] or [],
  "keywords": ["important", "terms"]
}}

Be concise. Extract meaning, not exact words."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)

    async def extract_from_voice(self, transcript: str) -> dict:
        """Special handling for voice transcripts (more natural, less structured)"""

        prompt = f"""A user spoke this check-in via voice call. Extract structured data.

Transcript: "{transcript}"

They were asked about:
1. What they worked on yesterday
2. What they accomplished
3. What they're doing today
4. Any blockers

Return JSON:
{{
  "worked_on": "...",
  "accomplished": ["..."],
  "next": "...",
  "blockers": ["..."],
  "sentiment": "positive|neutral|negative",
  "energy": 1-10,
  "mentions": ["person names mentioned"],
  "confidence": 0.0-1.0
}}

Note: If something wasn't mentioned, use null or empty array."""

        response = self.client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=300,
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(response.content[0].text)
```

---

## Privacy Gate

```python
from enum import Enum
from typing import Optional

class PrivacyLevel(Enum):
    PRIVATE = "private"
    PARTNER = "partner"  # user + their owl
    TEAM = "team"
    CIRCLE = "circle"
    PUBLIC = "public"

class PrivacyGate:
    def filter(self, checkin: dict, target_level: PrivacyLevel) -> Optional[dict]:
        """Filter checkin data based on privacy level"""

        checkin_privacy = PrivacyLevel(checkin.get("privacy", "private"))

        # Check if this checkin should be visible at target level
        visibility_order = [
            PrivacyLevel.PRIVATE,
            PrivacyLevel.PARTNER,
            PrivacyLevel.TEAM,
            PrivacyLevel.CIRCLE,
            PrivacyLevel.PUBLIC
        ]

        if visibility_order.index(checkin_privacy) < visibility_order.index(target_level):
            # Checkin is more private than requested view
            return None

        # Apply field-level filtering
        filtered = checkin.copy()

        if target_level == PrivacyLevel.TEAM:
            # Teams see content but not sentiment/energy by default
            filtered["checkin"] = {
                "worked_on": checkin["checkin"].get("worked_on"),
                "accomplished": checkin["checkin"].get("accomplished"),
                "next": checkin["checkin"].get("next"),
                "blockers": checkin["checkin"].get("blockers")
            }
            # Remove personal metadata
            filtered.pop("extracted", None)

        elif target_level == PrivacyLevel.CIRCLE:
            # Circle sees everything
            pass

        elif target_level == PrivacyLevel.PUBLIC:
            # Public sees anonymized patterns only
            filtered = {
                "type": "anonymous_checkin",
                "circle_id": checkin["circle_id"],
                "timestamp": checkin["timestamp"],
                "patterns": {
                    "keywords": checkin.get("extracted", {}).get("keywords", []),
                    "has_blockers": bool(checkin["checkin"].get("blockers")),
                    "sentiment": checkin.get("extracted", {}).get("sentiment")
                }
            }

        return filtered

    def aggregate_for_field(self, checkins: list, circle_id: str) -> dict:
        """Create anonymized aggregate for THE FIELD analysis"""

        return {
            "circle_id": circle_id,
            "count": len(checkins),
            "aggregate": {
                "blockers_mentioned": sum(
                    1 for c in checkins if c["checkin"].get("blockers")
                ),
                "sentiment_distribution": self._sentiment_dist(checkins),
                "energy_average": self._energy_avg(checkins),
                "common_keywords": self._extract_common_keywords(checkins)
            }
        }

    def _sentiment_dist(self, checkins: list) -> dict:
        sentiments = [c.get("extracted", {}).get("sentiment", "neutral") for c in checkins]
        return {
            "positive": sentiments.count("positive") / len(checkins),
            "neutral": sentiments.count("neutral") / len(checkins),
            "negative": sentiments.count("negative") / len(checkins)
        }

    def _energy_avg(self, checkins: list) -> float:
        energies = [
            c.get("extracted", {}).get("energy", 5)
            for c in checkins
            if c.get("extracted", {}).get("energy")
        ]
        return sum(energies) / len(energies) if energies else 5.0

    def _extract_common_keywords(self, checkins: list) -> list:
        from collections import Counter
        all_keywords = []
        for c in checkins:
            all_keywords.extend(c.get("extracted", {}).get("keywords", []))
        return [kw for kw, count in Counter(all_keywords).most_common(5)]
```

---

## NATS Topics

| Topic | Purpose | Payload |
|-------|---------|---------|
| `owl.checkins` | All human check-ins | Full checkin JSON |
| `owl.checkins.{circle_id}` | Circle-specific | Filtered checkin |
| `owl.checkins.{user_id}` | User-specific | Full checkin (private) |
| `owl.patterns` | Detected patterns | Pattern object |
| `owl.feedback.{user_id}` | Feedback to user | Suggestion object |
| `owl.collective` | THE FIELD synthesis | Synthesis object |

---

## Daily Scheduler

```python
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import pytz

class DailyPromptScheduler:
    def __init__(self, twilio_client, user_repository):
        self.twilio = twilio_client
        self.users = user_repository
        self.scheduler = AsyncIOScheduler()

    def start(self):
        # Run every minute to check for users to prompt
        self.scheduler.add_job(
            self._check_and_send,
            'cron',
            minute='*'
        )
        self.scheduler.start()

    async def _check_and_send(self):
        now = datetime.utcnow()

        # Get users whose check-in time is now
        users = await self.users.get_users_for_checkin_time(
            hour=now.hour,
            minute=now.minute
        )

        for user in users:
            # Skip if already checked in today
            if await self._has_checked_in_today(user.id):
                continue

            # Send appropriate prompt based on channel preference
            if user.channel_preference == "sms":
                await self._send_sms_prompt(user)
            elif user.channel_preference == "email":
                await self._send_email_prompt(user)

    async def _send_sms_prompt(self, user):
        await self.twilio.messages.create(
            body="(8) Good morning! Quick check-in?\n\n1 = Full (4 Qs)\n2 = Quick (1 Q)\n3 = Skip",
            from_="+18008695746",  # 1-800-8OWLS-IN
            to=user.phone
        )

    async def _has_checked_in_today(self, user_id: str) -> bool:
        # Check Redis or database for today's checkin
        pass
```

---

## Deployment

### Docker Compose

```yaml
version: '3.8'

services:
  intake:
    build: ./intake-service
    ports:
      - "8080:8080"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - NATS_URL=nats://nats:4222
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - nats

  nats:
    image: nats:2.10
    ports:
      - "4222:4222"
      - "8222:8222"
    command: "--js --sd /data"
    volumes:
      - nats_data:/data

  redis:
    image: redis:7
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  scheduler:
    build: ./scheduler-service
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - TWILIO_ACCOUNT_SID=${TWILIO_ACCOUNT_SID}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
    depends_on:
      - postgres

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=8owls
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  nats_data:
  redis_data:
  postgres_data:
```

---

## Error Handling

```python
class IntakeError(Exception):
    """Base exception for intake service"""
    pass

class RateLimitError(IntakeError):
    """User has exceeded rate limit"""
    pass

class InvalidInputError(IntakeError):
    """Input failed validation"""
    pass

async def handle_sms_with_retry(handler, request):
    """Wrap SMS handling with error recovery"""
    try:
        return await handler(request)
    except RateLimitError:
        return twiml_response(
            "(8) Slow down! You can only check in once per hour."
        )
    except InvalidInputError as e:
        return twiml_response(
            f"(8) I didn't understand that. Reply HELP for options."
        )
    except Exception as e:
        # Log error, don't expose details
        logger.error(f"SMS handler error: {e}")
        return twiml_response(
            "(8) Something went wrong. Try again in a minute."
        )
```

---

## Monitoring

### Metrics to Track

| Metric | Target | Alert |
|--------|--------|-------|
| SMS response time | <2s | >5s |
| Checkin completion rate | >70% | <50% |
| NATS publish latency | <100ms | >500ms |
| Daily prompt delivery | >99% | <95% |
| Voice transcription accuracy | >90% | <80% |

### Health Endpoint

```python
@app.route('/health')
async def health():
    checks = {
        "redis": await check_redis(),
        "nats": await check_nats(),
        "twilio": await check_twilio(),
        "anthropic": await check_anthropic()
    }

    healthy = all(checks.values())

    return jsonify({
        "status": "healthy" if healthy else "degraded",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }), 200 if healthy else 503
```

---

**(8) Built with love. For the collective.**
