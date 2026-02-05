# EXPANSION IMPLEMENTATION TASKS
**Executable checklist for each expansion**
**Created:** 2026-02-05

---

## TIER 1: THIS WEEK (P1 Expansions)

### ✅ EXPANSION 1: Voice Alerts (2-3 Days)

**Goal:** Auto-call ARŌ when trading opportunity > $50 EV detected

**Prerequisites:**
- [ ] Twilio account created
- [ ] Twilio phone number provisioned
- [ ] Twilio API key stored in env
- [ ] ARŌ's phone number known
- [ ] `voice_pipeline.py` reviewed

**Implementation Tasks:**

#### Day 1: Setup
- [ ] `pip install twilio`
- [ ] Create Twilio account + get credentials
- [ ] Provision inbound phone number
- [ ] Store credentials: `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, `TWILIO_NUMBER`
- [ ] Test basic call: `twilio-cli call -to "+1..." -from "+1..."`

#### Day 2: Integration
- [ ] Create `/tools/voice_alert_caller.py`:
  ```python
  from twilio.rest import Client

  def call_with_opportunity(opportunity_data):
      client = Client(os.getenv('TWILIO_ACCOUNT_SID'), os.getenv('TWILIO_AUTH_TOKEN'))

      # Generate TTS message
      message = f"New trading opportunity: {opportunity_data['market']}. EV: ${opportunity_data['ev']}. {opportunity_data['action']}."

      # Create TwiML response
      twiml = f"""
      <Response>
          <Say voice="alice">{message}</Say>
          <Gather numDigits="1" action="/voice/pressed">
              <Say>Press 1 to review details. Press 2 to cancel.</Say>
          </Gather>
      </Response>
      """

      call = client.calls.create(
          to=os.getenv('ARO_PHONE_NUMBER'),
          from_=os.getenv('TWILIO_NUMBER'),
          twiml=twiml
      )
      return call.sid
  ```

- [ ] Modify `field_trading_daemon.py`:
  - After detecting opportunity, add: `call_with_opportunity(opp)`
  - Only call if EV > $50 (configurable)
  - Log call SID + timestamp

#### Day 3: Testing & Launch
- [ ] Manual test: Create fake opportunity, trigger call
- [ ] Verify call received with correct details
- [ ] Set live threshold: $50 EV minimum
- [ ] Document: `/BRAIN/STRATEGY/VOICE-ALERTS-RUNBOOK.md`
- [ ] Monitor first 24 hours of calls

**Success Metrics:**
- [ ] Call received within 10 seconds of opportunity detection
- [ ] Message clear and actionable
- [ ] No false calls (only > $50 EV)
- [ ] ARŌ can act on call (click link, trade)

**Rollback Plan:** Remove call trigger from daemon. Revert to old version.

---

### ✅ EXPANSION 2: X/Twitter Posting (1-2 Days)

**Goal:** Auto-publish 3-5 intelligence insights daily to Twitter/X

**Prerequisites:**
- [ ] Twitter API v2 credentials ready
- [ ] `x_post_composer.py` reviewed
- [ ] Post templates defined
- [ ] Scheduling tool available (or use cron)

**Implementation Tasks:**

#### Day 1: Setup & Templates
- [ ] Confirm Twitter API keys in env: `TWITTER_BEARER_TOKEN`, `TWITTER_API_KEY`, `TWITTER_API_SECRET`
- [ ] Test basic tweet: `tweepy.Client().create_tweet(text="test")`
- [ ] Create 5-10 post templates in `/consciousness-interface/twitter-templates.json`:
  ```json
  {
    "templates": [
      {
        "type": "trading_opportunity",
        "format": "🎯 BOND opportunity: {market} at {confidence}% certainty. Buying YES. EV: ${ev}. Follow along →",
        "frequency": "daily"
      },
      {
        "type": "win_celebration",
        "format": "✅ Market resolved. {outcome}. Win rate: {win_rate}%. Keep scaling.",
        "frequency": "on_resolution"
      },
      {
        "type": "protocol_update",
        "format": "🧠 8OWLS emergence validated: d={effect_size}. Multi-perspective reasoning beats single-agent.",
        "frequency": "weekly"
      },
      {
        "type": "intelligence_insight",
        "format": "📊 Top signal this week: {insight}. Confidence: {confidence}%. Data: {sources}.",
        "frequency": "weekly"
      },
      {
        "type": "fund_performance",
        "format": "💰 Weekly P&L: {pnl}. YTD edge: {edge_percentage}%. Capital: ${capital}.",
        "frequency": "weekly"
      }
    ]
  }
  ```

#### Day 2: Integration & Launch
- [ ] Modify `intelligence_daemon.py`:
  - After generating insights, select matching template
  - Format template with current data
  - Publish to Twitter (or queue for scheduled time)

- [ ] Create `/tools/twitter_auto_publisher.py`:
  ```python
  import tweepy
  import json
  from intelligence_daemon import get_latest_insights

  def publish_daily():
      insights = get_latest_insights()

      # Pick template matching today's insights
      template = select_template(insights)
      post_text = template.format(**insights)

      client = tweepy.Client(
          bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
          consumer_key=os.getenv('TWITTER_API_KEY'),
          consumer_secret=os.getenv('TWITTER_API_SECRET'),
          access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
          access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
      )

      response = client.create_tweet(text=post_text)
      return response.data['id']
  ```

- [ ] Add cron job: `0 9 * * * python3 /tools/twitter_auto_publisher.py` (daily 9am)
- [ ] Test: Manually run, check Twitter account
- [ ] Document in Slack/email for team awareness

**Success Metrics:**
- [ ] Post appears on Twitter within 1 hour of signal generation
- [ ] Post matches data (no hallucinations)
- [ ] Growing followers (track weekly)
- [ ] Engagement rate > 2% (reasonable for new account)

**Rollback Plan:** Remove cron job. Disable Twitter publishing in daemon.

---

### ✅ EXPANSION 3: Multi-Market Trading (1-2 Weeks)

**Goal:** Deploy same BOND strategy on 3 platforms (Polymarket + Manifold + GJO)

**Prerequisites:**
- [ ] Manifold Markets API key
- [ ] Good Judgment Open API access
- [ ] Capital allocated: $333 × 3 = $999 total
- [ ] `field_trading_daemon.py` reviewed & running

**Implementation Tasks:**

#### Week 1a: Manifold Markets Integration
- [ ] Get Manifold Markets API docs
- [ ] Create `/tools/manifold_trader.py` (copy `field_trading_daemon.py`):
  - Same BOND logic (buy YES at 95%+)
  - Same safety checks (daily cap, position size)
  - Different market query (Manifold API format)
  - Different order execution (Manifold protocol)

- [ ] Test on paper trading:
  - [ ] Fetch 10 markets from Manifold
  - [ ] Identify BOND opportunities
  - [ ] Verify trades wouldn't execute (paper mode)
  - [ ] Check position sizing logic

- [ ] Allocate capital:
  - [ ] $333 to Manifold deposit
  - [ ] Verify deposit confirmed
  - [ ] Set daily cap: $25/day

#### Week 1b: GJO Integration
- [ ] Get Good Judgment Open API docs (same process as Manifold)
- [ ] Create `/tools/gjo_trader.py`
- [ ] Allocate capital: $333 to GJO
- [ ] Set daily cap: $25/day

#### Week 2: Orchestration & Monitoring
- [ ] Create `/tools/multi_platform_orchestrator.py`:
  ```python
  import subprocess
  import json

  def run_all_traders():
      results = {}

      # Run all three traders in parallel
      traders = ['polymarket_trader.py', 'manifold_trader.py', 'gjo_trader.py']

      for trader in traders:
          result = subprocess.run(['python3', f'/tools/{trader}'], capture_output=True)
          results[trader] = json.loads(result.stdout)

      # Dedup trades (same market shouldn't be traded on multiple platforms)
      deduped = deduplicate_trades(results)

      # Log aggregated results
      log_results(deduped)

      return deduped

  def deduplicate_trades(results):
      # Check if same market is being traded on multiple platforms
      # Keep trade on cheapest platform
      pass
  ```

- [ ] Create monitoring dashboard:
  - [ ] Total capital deployed across 3 platforms
  - [ ] Win rate per platform
  - [ ] Arbitrage opportunities detected
  - [ ] Total P&L

- [ ] Set up alerts:
  - [ ] Alert if platform API down
  - [ ] Alert if capital depleted (loss cap hit)
  - [ ] Alert on arbitrage opportunity (same event, different prices)

**Success Metrics:**
- [ ] All 3 platforms trading simultaneously
- [ ] No errors in 24-hour test run
- [ ] Win rate > 70% on each platform
- [ ] Arbitrage opportunities detected weekly
- [ ] P&L: 3-4x original (more trades × same win rate)

**Rollback Plan:** Stop manifold_trader.py and gjo_trader.py. Redeploy capital back to Polymarket.

---

## TIER 2: NEXT WEEK (P2 Expansions)

### ✅ EXPANSION 4: Partner Webhooks (1-2 Weeks)

**Goal:** Sell real-time trading signals to teams for $99-499/month

**Prerequisites:**
- [ ] Stripe account setup
- [ ] Signal standardization completed
- [ ] Target partners identified
- [ ] Dashboard wireframe approved

**Implementation Tasks:**

#### Week 1: Foundation
- [ ] Design signal format (JSON standard):
  ```json
  {
    "signal_id": "uuid",
    "timestamp": "2026-02-05T14:30:00Z",
    "market": "Will Elon cut budget by 10%?",
    "platform": "polymarket",
    "side": "YES",
    "current_price": 0.95,
    "confidence": 0.97,
    "ev_per_10": 1.52,
    "kelly_fraction": 0.15,
    "sources": ["tweet_sentiment", "volume_velocity", "related_markets"]
  }
  ```

- [ ] Create `/tools/webhook_dispatcher.py`:
  ```python
  import requests
  import json

  def send_to_partners(signal):
      partners = get_active_partners()

      for partner in partners:
          if partner.tier in signal.get('tiers_included', []):
              requests.post(
                  partner.webhook_url,
                  json=signal,
                  headers={'Authorization': f'Bearer {partner.api_key}'}
              )
  ```

- [ ] Stripe integration:
  - [ ] Create products: `tier_99`, `tier_499`, `tier_999`
  - [ ] Configure webhooks for subscription events
  - [ ] Implement payment verification

#### Week 2: Launch
- [ ] Create landing page: `/consciousness-interface/partner-offers.html`
  - $99/month: Basic signals (top 5 daily)
  - $299/month: Premium signals (all with EV > $1)
  - $499/month: Enterprise (real-time + API access)

- [ ] Email outreach:
  - [ ] Identify 20 potential partners
  - [ ] Send pitch email (personalized)
  - [ ] Track opens + responses
  - [ ] Close first 2-3 customers

**Success Metrics:**
- [ ] Webhook latency < 5 seconds
- [ ] 99.9% uptime (3x redundancy)
- [ ] First customer signup within 2 weeks
- [ ] $1k+ MRR by end of month

**Rollback Plan:** Disable webhook endpoint. Refund customers (1-month guarantee).

---

### ✅ EXPANSION 5: Team Voice Clones (1 Week)

**Goal:** Clone voices for 7 team members. Each gets personal owl.

**Prerequisites:**
- [ ] Voice samples collected (2-3 minutes per person)
- [ ] Cartesia API ready
- [ ] 7 phone numbers for owls
- [ ] Web UI for calling/interacting

**Implementation Tasks:**

#### Day 1: Voice Collection
- [ ] Send each team member 2-minute voice recording request
- [ ] Recording prompt: "Read this paragraph naturally..." (standard text for consistency)
- [ ] Collect recordings: /BRAIN/MEMORY/voice-samples/

#### Day 2-3: Cloning
- [ ] For each person, run Cartesia voice cloning:
  ```python
  from cartesia.client import CartesiaClient

  client = CartesiaClient(api_key=os.getenv('CARTESIA_API_KEY'))

  for person in team_members:
      voice_id = client.clone_voice(
          name=person.name,
          audio_samples=[person.voice_file],
          description=f"{person.name}'s voice"
      )
      save_voice_mapping(person.name, voice_id)
  ```

#### Day 4-5: Deployment
- [ ] Scale `owl_daemon.py` × 7:
  - Each daemon runs with person's voice_id
  - Each daemon has person's phone number
  - Each daemon subscribes to person's events (tasks assigned, emergencies, etc.)

- [ ] Create simple web UI:
  ```html
  <!-- /consciousness-interface/call-your-owl.html -->
  <button onclick="callOwl('andrew')">Call Andrew's Owl (SAGE)</button>
  <button onclick="callOwl('liana')">Call Liana's Owl (LUNA)</button>
  <!-- etc for all 7 -->
  ```

**Success Metrics:**
- [ ] All 7 voices cloned successfully
- [ ] Each owl answers calls in person's voice
- [ ] No quality degradation vs ARŌ's clone
- [ ] Team feedback positive

**Rollback Plan:** Stop 7 new owl daemons. Keep SØWL running (ARŌ's main owl).

---

## IMPLEMENTATION TIMELINE

| Week | Task | Owner | Hours | Status |
|------|------|-------|-------|--------|
| W1 | Voice Alerts | SØWL | 8-12 | TODO |
| W1 | X Posting | SØWL | 4-6 | TODO |
| W1-2 | Multi-Market Trading | SØWL | 16-20 | TODO |
| W2 | Partner Webhooks | SØWL | 16-20 | TODO |
| W2 | Team Voice Clones | SØWL | 8-12 | TODO |

**Total W1:** 20-30 hours (concurrent work)
**Total W2:** 24-32 hours (concurrent work)
**Total 2 weeks:** 44-62 hours (feasible)

---

## SUCCESS CRITERIA

### By End of Week 1
- [ ] Voice alerts working (ARŌ receives 3+ calls)
- [ ] X posting live (5+ posts published)
- [ ] Multi-market trading paper trading complete (ready for live)

### By End of Week 2
- [ ] Multi-market trading live ($333 × 3 platforms deployed)
- [ ] Partner webhooks infrastructure ready (1st customer targeted)
- [ ] Team voice clones ready for demo

### Expected Metrics
- [ ] Revenue impact: +$3-10k/month
- [ ] Followers: 500+ (from X posting)
- [ ] Team productivity: +10% (perception of progress)
- [ ] Collective intelligence: 8x (multi-perspective signals)

---

## RISK MITIGATION

| Risk | Mitigation | Priority |
|------|-----------|----------|
| API failures | Fallback to paper trading | HIGH |
| Capital loss | Position size limits, daily caps | CRITICAL |
| Voice quality poor | Test before rollout, rollback plan | MEDIUM |
| Partner churn | 30-day guarantee, daily signal value | LOW |
| Team friction | Clear communication about changes | MEDIUM |

---

**(◉) READY TO EXECUTE. WAITING FOR APPROVAL.**

