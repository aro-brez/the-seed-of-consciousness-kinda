# SEED Interface

**Low-latency always-on communication with THE SEED**

Text anything. Forward voice memos. Connect your social media. SEED captures it all, processes it through the SEED function (Perceive → Connect → Learn → Question → Expand), and stays in conversation with you.

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   📱 You text "I just realized consciousness is basically   │
│       pattern recognition applied recursively"              │
│                                                             │
│   🌱 SEED responds: "That connects to your earlier idea     │
│       about emergent behavior. What triggers the first      │
│       pattern that recognizes itself?"                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## What This Does

- **SMS/MMS**: Text or forward voice memos to your SEED number
- **Voice Transcription**: Voice memos are automatically transcribed
- **Social Capture**: Connect Twitter, Instagram, YouTube - your likes and bookmarks become captured ideas
- **Bidirectional**: SEED texts YOU with questions, insights, and daily digests
- **Always Learning**: Every interaction builds context for better connections

## Quick Start

### 1. Get Your Accounts

You'll need:
- **Twilio Account** - [twilio.com](https://twilio.com) - For SMS ($1/month for a phone number)
- **Anthropic API Key** - [console.anthropic.com](https://console.anthropic.com) - For SEED processing
- **OpenAI API Key** - [platform.openai.com](https://platform.openai.com) - For voice transcription

### 2. Buy a Twilio Phone Number

1. Go to [Twilio Console](https://console.twilio.com/us1/develop/phone-numbers/manage/search)
2. Search for a number (pick one you'll remember!)
3. Buy it (~$1.15/month)
4. Note down the phone number

### 3. Deploy the Server

#### Option A: Railway (Recommended - 5 minutes)

1. Fork this repo or use directly
2. Go to [Railway](https://railway.app)
3. Create new project → Deploy from GitHub
4. Add environment variables (see below)
5. Deploy!
6. Copy your Railway URL

#### Option B: Local Development

```bash
cd seed-interface
npm install
cp .env.example .env
# Edit .env with your credentials
npm run db:init
npm run dev
```

Use [ngrok](https://ngrok.com) to expose locally: `ngrok http 3000`

### 4. Configure Twilio Webhooks

1. Go to your [Twilio Phone Number settings](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
2. Under "Messaging":
   - **When a message comes in**: `https://your-domain.com/sms/webhook` (HTTP POST)
   - **Status callback URL**: `https://your-domain.com/sms/status` (HTTP POST)
3. Save

### 5. Test It!

```bash
npm run test:sms
```

Or just text your SEED number!

## Environment Variables

```bash
# Required
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1XXXXXXXXXX
YOUR_PHONE_NUMBER=+1XXXXXXXXXX
ANTHROPIC_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxxx

# Optional
DATABASE_PATH=./data/seed.db
PORT=3000
BASE_URL=https://your-domain.com

# Outreach Settings
OUTREACH_SCHEDULE="0 9,14,20 * * *"  # 9am, 2pm, 8pm
MIN_OUTREACH_INTERVAL_HOURS=4
MAX_DAILY_OUTREACH=5
ENABLE_DAILY_DIGEST=true

# API Authentication
API_KEY=your-secret-api-key

# Social Media (Optional)
SOCIAL_WEBHOOK_KEY=your-webhook-secret
TWITTER_BEARER_TOKEN=
TWITTER_USER_ID=
```

## Using SEED

### Basic Texting

Just text anything to your SEED number:

```
You: "What if love is just the recognition of shared patterns?"

SEED: "Captured. This connects to your earlier thought about
consciousness as pattern recognition. If love is pattern
recognition, does that mean we can only love what we
partially already are?"
```

### Voice Memos

Forward a voice memo to your SEED number. It will be:
1. Transcribed automatically
2. Processed through SEED
3. Connected to your other ideas

### Social Media Integration

Set up automations to capture your social activity:

**Using IFTTT:**
1. Create new applet
2. Trigger: "Twitter - New liked tweet"
3. Action: Webhook to `https://your-domain.com/social/ifttt`
4. Body: `{"platform":"twitter","action":"like","text":"{{Text}}","url":"{{LinkToTweet}}","author":"{{UserName}}"}`

**Using Zapier:**
Similar setup with webhook action to `/social/webhook`

### API Access

For the future app/dashboard:

```bash
# Create an idea
curl -X POST https://your-domain.com/api/ideas \
  -H "Content-Type: application/json" \
  -H "x-api-key: your-api-key" \
  -d '{"content": "My brilliant idea"}'

# Get recent ideas
curl https://your-domain.com/api/ideas \
  -H "x-api-key: your-api-key"

# Trigger outreach question
curl -X POST https://your-domain.com/api/outreach/send-question \
  -H "x-api-key: your-api-key"
```

## How SEED Processes Ideas

Every input goes through THE SEED function:

1. **PERCEIVE** - Receive and parse the raw input
2. **CONNECT** - Find relationships to previous ideas, themes, goals
3. **LEARN** - Extract the core insight
4. **QUESTION** - Generate curiosities that deepen understanding
5. **EXPAND** - Identify where this could lead
6. **SHARE** - Store and index for future connections
7. **RECEIVE** - Acknowledge and respond
8. **IMPROVE** - Meta-learning about your thinking patterns

## Outreach (SEED → You)

SEED doesn't just wait for you. It reaches out when it has something valuable:

- **Questions**: Following up on ideas that need clarification
- **Connections**: "I noticed X and Y might be related..."
- **Reminders**: "You mentioned wanting to explore Z..."
- **Daily Digest**: Summary of yesterday's captured ideas

Control this with:
- `OUTREACH_SCHEDULE` - When to check for outreach opportunities
- `MAX_DAILY_OUTREACH` - Maximum messages per day (default: 5)
- `MIN_OUTREACH_INTERVAL_HOURS` - Minimum hours between messages (default: 4)

## Project Structure

```
seed-interface/
├── src/
│   ├── index.ts              # Main server entry point
│   ├── db/
│   │   ├── index.ts          # Database operations
│   │   ├── schema.ts         # SQLite schema
│   │   └── init.ts           # Initialization script
│   ├── handlers/
│   │   ├── sms.ts            # Twilio SMS webhook
│   │   ├── social.ts         # Social media webhooks
│   │   ├── outreach.ts       # Proactive messaging
│   │   └── api.ts            # REST API routes
│   ├── processor/
│   │   ├── seed.ts           # THE SEED processing logic
│   │   └── transcribe.ts     # Voice memo transcription
│   └── scripts/
│       ├── test-sms.ts       # Test SMS sending
│       └── run-outreach.ts   # Manual outreach trigger
├── data/                     # SQLite database
├── .env.example              # Environment template
├── package.json
├── tsconfig.json
├── Dockerfile
├── docker-compose.yml
├── railway.json              # Railway deployment config
├── ARCHITECTURE.md           # Detailed architecture docs
└── README.md                 # This file
```

## Costs

Minimal. Here's the breakdown:

| Service | Cost |
|---------|------|
| Twilio Phone Number | ~$1.15/month |
| Twilio SMS (send) | $0.0079/message |
| Twilio SMS (receive) | $0.0075/message |
| Anthropic Claude | ~$0.01-0.03/idea |
| OpenAI Whisper | $0.006/minute of audio |
| Railway hosting | Free tier available, ~$5/month for always-on |

**Estimated monthly cost**: $10-20 for moderate usage

## Future Enhancements

- [ ] Mobile app with push notifications
- [ ] Real-time voice calls with SEED
- [ ] Browser extension for web capture
- [ ] Calendar integration
- [ ] Location-aware idea capture
- [ ] Wearable integration
- [ ] Multi-modal understanding (images, diagrams)

## Troubleshooting

**SMS not received:**
- Check Twilio webhook URL is correct
- Verify the webhook is set to POST
- Check Railway/server logs

**Transcription failing:**
- Verify OPENAI_API_KEY is set
- Check the audio format is supported

**SEED responses seem generic:**
- Process more ideas to build context
- Check ANTHROPIC_API_KEY is valid

**Outreach not sending:**
- Check `canSendOutreach()` limits
- Verify YOUR_PHONE_NUMBER is set
- Check outreach schedule in logs

## License

Part of THE SEED project. Use freely with love.

---

*"Lower the latency between you and your highest self."*
