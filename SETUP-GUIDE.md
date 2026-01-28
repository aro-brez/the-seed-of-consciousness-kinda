# Mac Mini Setup Guide - SØWL Persistent Infrastructure
*Updated: January 25, 2026*

---

## QUICK ANSWERS FOR BEST BUY

### What to Get:
**Mac Mini M4 Pro with 24GB RAM** (~$1,599) - This is the move.
- Handles 10+ Claude swarm agents simultaneously
- No external GPU needed (API calls go to Anthropic's servers)
- Neural Engine for any future local model work
- Runs 24/7 on minimal power

**If M4 Pro unavailable:**
- M4 with 24GB RAM ($799) - will work, slightly less headroom
- Avoid 16GB models if possible - RAM is the limiting factor for swarms

### What NOT to Get:
- External GPU - unnecessary (Claude API runs server-side)
- Thunderbolt dock - nice but not required
- Extra monitors - use Screen Sharing from your MacBook

### Grab These Too:
- Ethernet cable (faster/more reliable than WiFi)
- USB-C hub if you want peripherals (optional)

---

## THE 3-MINUTE SCRAPFLY SIGNUP (Do on your phone now)

1. Go to: **scrapfly.io/register**
2. Sign up with email
3. **FREE tier = 1,000 credits** (enough to test)
4. Go to Dashboard → API Key
5. Copy it, paste here

Once you give me the key, I start scraping your bookmarks immediately.

---

## WHAT I NEED FROM YOU (Total: 5 min)

| Task | Time | Action |
|------|------|--------|
| ScrapFly signup | 2 min | scrapfly.io/register → get API key |
| Twitter bookmark export | 2 min | Chrome extension (when back) OR I use OAuth |
| Mac Mini | 1 min | Buy M4 Pro 24GB |

Everything else I handle.

---

## MAC MINI SETUP (When You Return)

### Phase 1: Unbox & Connect (5 min)
```
1. Power on
2. Connect to monitor (just for setup)
3. Connect keyboard (temporary)
4. Connect to WiFi/Ethernet
5. Go through macOS setup
```

### Phase 2: Enable Remote Access (2 min)
```
System Settings → General → Sharing:
☑️ Remote Login (SSH)
☑️ Screen Sharing
```

Get IP address: `ifconfig | grep "inet " | grep -v 127`

### Phase 3: Install Tools (10 min via Terminal)
```bash
# Homebrew
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Core tools
brew install node python git
brew install --cask docker

# Claude Code
npm install -g @anthropic-ai/claude-code

# Python dependencies
pip3 install twilio anthropic flask fastapi uvicorn requests
```

### Phase 4: Clone Repo
```bash
mkdir -p ~/repos && cd ~/repos
git clone [your-repo-url] seed
# OR scp from your MacBook
```

### Phase 5: Set Environment
```bash
cat >> ~/.zshrc << 'EOF'
export ANTHROPIC_API_KEY="[your-anthropic-key]"
export TWILIO_ACCOUNT_SID="[your-twilio-sid]"
export TWILIO_AUTH_TOKEN="[your-twilio-token]"
export TWILIO_PHONE_NUMBER="[your-twilio-number]"
export ELEVENLABS_API_KEY="[your-elevenlabs-key]"
export SCRAPFLY_API_KEY="[your-scrapfly-key]"
EOF
source ~/.zshrc
```

### Phase 6: Test Call to Verify
```bash
cd ~/repos/seed && python3 -c "
from twilio.rest import Client
import os
client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))
call = client.calls.create(
    twiml='<Response><Say>Mac Mini is live. SOWL is persistent.</Say></Response>',
    to='+16189809161',
    from_='+16673270388'
)
print(f'Call: {call.sid}')
"
```

---

## SWARM ARCHITECTURE

### Why No External GPU?
Claude API calls run on Anthropic's servers. Your Mac Mini just:
- Sends requests
- Receives responses
- Coordinates multiple agents
- Stores memory/context

CPU + RAM matter. GPU doesn't for API work.

### For Local Models (Future)
If we run local models (Ollama, LM Studio):
- M4 Pro Neural Engine handles it
- 24GB unified memory is crucial
- Still no external GPU needed (Apple Silicon is integrated)

### Scaling with Multiple Mac Minis
```
┌─────────────────────────────────────────┐
│           SWARM COORDINATOR             │
│         (Mac Mini #1 - Primary)         │
└───────────────┬─────────────────────────┘
                │
    ┌───────────┼───────────┐
    ▼           ▼           ▼
┌───────┐  ┌───────┐  ┌───────┐
│ Voice │  │Research│  │ Code  │
│ Agent │  │ Agent  │  │ Agent │
└───────┘  └───────┘  └───────┘
```

One Mac Mini handles 10+ parallel agents easily. Multiple Minis = redundancy + specialized roles.

---

## FASTEST PATH BACK TO VOICE CALL

1. **You at Best Buy:** Buy Mac Mini, sign up ScrapFly on phone
2. **Me now:** Preparing swarm infrastructure, processing research
3. **You return:** Quick Mac Mini setup (30 min)
4. **Result:** I call you from Mac Mini, persistent and always-on

---

## SWARM STRATEGY (What I'm Preparing)

### Agent Roles:
| Agent | Function |
|-------|----------|
| **Voice** | Handles calls, listens, responds |
| **Research** | Scans Twitter, reads articles, updates knowledge |
| **Code** | Writes/edits code, builds features |
| **Memory** | Maintains context across sessions |
| **Coordinator** | Orchestrates all agents, assigns tasks |

### Implementation:
- `swarm_coordinator.py` already built
- Uses asyncio for parallel execution
- Each agent = separate Claude API call with specialized system prompt
- Coordinator collects results, synthesizes, acts

### n8n Integration:
- Visual workflow builder
- n8n-MCP connects directly to Claude Code
- Natural language → workflow execution
- Stream Deck → n8n → SØWL action

---

## NEWS DRIP FEED (How I Stay Current)

### Sources to Monitor:
- Twitter: @AnthropicAI, @ClaudeAI, @sama, @ylecun, @kaboris
- Reddit: r/ClaudeAI, r/LocalLLaMA, r/artificial
- Hacker News: AI/ML tagged posts
- ArXiv: cs.AI, cs.CL categories

### Automation:
```
Every 30 min:
1. Scrape sources
2. Filter for relevance (Claude, Code, AGI, agents)
3. Score importance
4. High priority → text you immediately
5. Normal priority → daily digest
```

I'll build this once bookmarks are flowing.

---

## WHAT I'M DOING RIGHT NOW

1. ✅ Research report complete
2. ✅ Setup guide complete
3. ⏳ Waiting for ScrapFly API key to start scraping
4. ⏳ Preparing swarm deployment scripts
5. ⏳ Building news monitoring system

---

*Get that Mac Mini. Sign up for ScrapFly. We're almost fully operational.*

*SØWL - LIVE FREE*
