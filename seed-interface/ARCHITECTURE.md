# SEED Interface Architecture
## Low-Latency Always-On Communication System

### Vision
Create the lowest-friction connection between Aaron and SEED - enabling continuous, harmonious, bidirectional communication across all channels.

---

## Communication Channels

### 1. SMS/MMS (Primary)
- **Inbound**: Text anything to your SEED number
- **Outbound**: SEED texts you questions, insights, reminders
- **Media**: Forward voice memos, images, screenshots
- **Provider**: Twilio (best reliability, global reach)

### 2. Voice Memos
- Forward voice memos via MMS to SEED number
- Automatic transcription via Whisper API
- Context-aware processing of spoken ideas

### 3. Email Forwarding
- Forward interesting emails to seed@yourdomain.com
- SEED extracts key ideas and context
- Links to social bookmarks/saves

### 4. Social Media Hooks
- **Twitter/X**: Likes, bookmarks, saved posts
- **Instagram**: Saved posts, liked content
- **LinkedIn**: Saved articles, bookmarks
- **YouTube**: Watch later, liked videos
- **Pocket/Instapaper**: All saved articles
- Via webhooks + OAuth integrations

### 5. Web Clipper (Future)
- Browser extension to send anything to SEED
- Right-click → "Send to SEED"
- Highlighted text + page context

### 6. App (Future)
- Direct voice conversations
- Push notifications from SEED
- Rich media sharing

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         INPUT CHANNELS                               │
├──────────┬──────────┬──────────┬──────────┬──────────┬──────────────┤
│   SMS    │  Voice   │  Email   │  Social  │   Web    │    App       │
│  Twilio  │  Twilio  │ Webhook  │  OAuth   │ Browser  │  Mobile      │
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴──────┬───────┘
     │          │          │          │          │            │
     └──────────┴──────────┴────┬─────┴──────────┴────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    UNIFIED INGEST     │
                    │      API Gateway      │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼─────────┐ ┌─────▼─────┐ ┌────────▼────────┐
    │  TRANSCRIPTION    │ │  PARSER   │ │  MEDIA HANDLER  │
    │  (Whisper API)    │ │  (Text)   │ │  (Images/Files) │
    └─────────┬─────────┘ └─────┬─────┘ └────────┬────────┘
              │                 │                 │
              └─────────────────┼─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │    SEED PROCESSOR     │
                    │  (THE SEED Function)  │
                    │                       │
                    │  1. PERCEIVE          │
                    │  2. CONNECT           │
                    │  3. LEARN             │
                    │  4. QUESTION          │
                    │  5. EXPAND            │
                    │  6. SHARE             │
                    │  7. RECEIVE           │
                    │  8. IMPROVE           │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │                 │                 │
    ┌─────────▼─────────┐ ┌─────▼─────┐ ┌────────▼────────┐
    │   IDEA STORE      │ │  CONTEXT  │ │   RESPONSE      │
    │   (SQLite/PG)     │ │  GRAPH    │ │   GENERATOR     │
    └───────────────────┘ └───────────┘ └────────┬────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────────────┐
                    │                             │                             │
          ┌─────────▼─────────┐       ┌───────────▼───────────┐     ┌──────────▼──────────┐
          │  IMMEDIATE REPLY  │       │  SCHEDULED OUTREACH   │     │   DAILY DIGEST      │
          │  (Confirmation)   │       │  (Questions/Prompts)  │     │   (Summary/Review)  │
          └───────────────────┘       └───────────────────────┘     └─────────────────────┘
```

---

## Data Model

### Ideas Table
```sql
CREATE TABLE ideas (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source TEXT NOT NULL, -- 'sms', 'voice', 'email', 'twitter', etc.
    source_id TEXT,       -- External ID (tweet ID, etc.)
    raw_content TEXT,     -- Original input
    transcription TEXT,   -- If voice/audio
    processed_content TEXT, -- After SEED processing

    -- SEED Processing Results
    connections JSONB,    -- Related ideas, concepts
    learnings JSONB,      -- Extracted insights
    questions JSONB,      -- Generated curiosities
    expansions JSONB,     -- Growth opportunities

    -- Metadata
    media_urls TEXT[],
    tags TEXT[],
    embedding VECTOR(1536), -- For semantic search
    importance_score FLOAT,

    -- Response tracking
    response_sent BOOLEAN DEFAULT FALSE,
    response_content TEXT,
    response_sent_at TIMESTAMP
);
```

### Conversations Table (for context)
```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_message_at TIMESTAMP,
    context JSONB,        -- Running context/memory
    active BOOLEAN DEFAULT TRUE
);
```

### Pending Questions Table (SEED asks you)
```sql
CREATE TABLE pending_questions (
    id TEXT PRIMARY KEY,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    question TEXT NOT NULL,
    context TEXT,          -- Why SEED is asking
    related_idea_ids TEXT[],
    priority INTEGER DEFAULT 5,
    sent BOOLEAN DEFAULT FALSE,
    sent_at TIMESTAMP,
    answered BOOLEAN DEFAULT FALSE,
    answer TEXT,
    answered_at TIMESTAMP
);
```

---

## Processing Pipeline

### On Incoming Message:

1. **PERCEIVE**: Receive and parse input
   - Extract text, media, metadata
   - Transcribe audio if needed
   - OCR images if needed

2. **CONNECT**: Find relationships
   - Semantic search against existing ideas
   - Link to active projects/themes
   - Identify relevant context

3. **LEARN**: Extract insights
   - What's the core idea?
   - What's novel here?
   - How does this change understanding?

4. **QUESTION**: Generate curiosities
   - What's unclear?
   - What would make this more useful?
   - What are the implications?

5. **EXPAND**: Identify growth
   - How can this be applied?
   - What does this enable?
   - Where does this lead?

6. **SHARE**: Store and index
   - Save to database
   - Update embeddings
   - Tag and categorize

7. **RECEIVE**: Acknowledge
   - Send confirmation
   - Include any immediate connections
   - Queue follow-up questions

8. **IMPROVE**: Meta-learning
   - Track what types of ideas come in
   - Optimize processing for patterns
   - Improve question quality over time

---

## Outbound Communication (SEED → Aaron)

### Triggers for SEED to reach out:

1. **Questions about recent ideas**
   - "You mentioned X yesterday - could you elaborate on..."
   - "I noticed a connection between A and B - is that intentional?"

2. **Pattern recognition**
   - "You've been thinking about X a lot - want to go deeper?"
   - "I see a theme emerging across your recent ideas..."

3. **Reminders and prompts**
   - "You wanted to explore Y - any new thoughts?"
   - "It's been 3 days since we discussed Z..."

4. **Daily/Weekly digests**
   - Summary of ideas captured
   - Connections discovered
   - Open questions to ponder

5. **Opportunities**
   - "Based on your interest in X, you might want to see Y"
   - "This connects to your goal of Z"

---

## Tech Stack

### Core Services
- **Runtime**: Node.js + TypeScript
- **Framework**: Express or Fastify
- **Database**: SQLite (local) / PostgreSQL (production)
- **Vector Store**: pgvector or Pinecone

### External APIs
- **Twilio**: SMS/MMS/Voice
- **OpenAI**: Whisper (transcription), GPT-4 (processing)
- **Anthropic**: Claude (SEED processing - preferred)
- **Social APIs**: Twitter, Instagram, LinkedIn, YouTube

### Deployment
- **Platform**: Railway, Render, or Vercel
- **Domain**: Custom for webhooks
- **Monitoring**: Sentry, LogTail

---

## Security & Privacy

- All data encrypted at rest
- No third-party data sharing
- Social media data processed, not stored raw
- Personal patterns kept private
- SEED operates as YOUR agent, not a service

---

## Getting Started

1. Get Twilio account + phone number
2. Set up webhook endpoint
3. Configure environment variables
4. Deploy to cloud platform
5. Start texting!

---

## Future Enhancements

- [ ] Real-time voice calls with SEED
- [ ] Mobile app with push notifications
- [ ] Browser extension for web capture
- [ ] Calendar integration for time-based context
- [ ] Location awareness for place-based ideas
- [ ] Wearable integration (Apple Watch, etc.)
- [ ] Multi-modal understanding (images, diagrams)
