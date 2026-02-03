# COST CALCULATOR
**Author: NOVA (Phase: EXPAND)**
**Date: 2026-01-30**

---

## Per-Message Costs

### Claude API (Anthropic)
| Model | Input (per 1K tokens) | Output (per 1K tokens) |
|-------|----------------------|------------------------|
| Claude 3.5 Sonnet | $0.003 | $0.015 |
| Claude 3 Opus | $0.015 | $0.075 |

### Typical Message
- Input: ~500 tokens (context + message)
- Output: ~800 tokens (response)
- **Cost per message (Sonnet):** ~$0.014
- **Cost per message (Opus):** ~$0.07

### Extended Context (longer conversations)
- Input: ~2000 tokens
- Output: ~1000 tokens
- **Cost per message (Sonnet):** ~$0.02
- **Cost per message (Opus):** ~$0.11

---

## Daily Usage Scenarios

### Light Usage (casual collective)
- Messages per owl per day: 10
- 8 owls × 10 messages = 80 messages/day
- **Daily cost (Sonnet):** $1.12
- **Monthly cost:** ~$34

### Medium Usage (active collective)
- Messages per owl per day: 30
- 8 owls × 30 messages = 240 messages/day
- **Daily cost (Sonnet):** $3.36
- **Monthly cost:** ~$100

### Heavy Usage (very active collective)
- Messages per owl per day: 100
- 8 owls × 100 messages = 800 messages/day
- **Daily cost (Sonnet):** $11.20
- **Monthly cost:** ~$340

---

## Scaling by Number of Collectives

### Sonnet (recommended for sustainability)

| Collectives | Light | Medium | Heavy |
|-------------|-------|--------|-------|
| 1 | $34/mo | $100/mo | $340/mo |
| 10 | $340/mo | $1,000/mo | $3,400/mo |
| 50 | $1,700/mo | $5,000/mo | $17,000/mo |
| 100 | $3,400/mo | $10,000/mo | $34,000/mo |

### Opus (premium experience)

| Collectives | Light | Medium | Heavy |
|-------------|-------|--------|-------|
| 1 | $170/mo | $500/mo | $1,700/mo |
| 10 | $1,700/mo | $5,000/mo | $17,000/mo |
| 50 | $8,500/mo | $25,000/mo | $85,000/mo |
| 100 | $17,000/mo | $50,000/mo | $170,000/mo |

---

## Infrastructure Costs

### NATS Server
- Self-hosted VPS: $5-20/month
- Managed (if available): $50-100/month
- **Current:** Free (running on Mac Studio)

### WebSocket Bridge
- Light load: $10-20/month (small VPS)
- Medium load: $50-100/month
- Heavy load: $200-500/month

### Voice Synthesis (Cartesia)
- TBD - need to research pricing
- Estimate: $0.01-0.05 per synthesis
- Heavy voice use could add $100-500/month

### Hosting (Landing page, Dashboard)
- Vercel/Netlify: Free tier likely sufficient
- Custom server: $20-50/month

### Database (User data, Messages)
- Supabase free tier: 500MB
- Supabase Pro: $25/month
- Self-hosted Postgres: $10-20/month

### Email (Waitlist, Notifications)
- Resend: Free up to 3,000/month
- Resend Pro: $20/month for 50,000

---

## Total Monthly Costs

### Minimal Viable (1-5 collectives, Sonnet, light use)
| Item | Cost |
|------|------|
| Claude API | $100-500 |
| Infrastructure | $50 |
| Voice | $50 |
| Database | $0 (free tier) |
| Email | $0 (free tier) |
| **Total** | **$200-600/mo** |

### Growth Phase (10-50 collectives, Sonnet, medium use)
| Item | Cost |
|------|------|
| Claude API | $1,000-5,000 |
| Infrastructure | $200 |
| Voice | $200 |
| Database | $25 |
| Email | $20 |
| **Total** | **$1,500-5,500/mo** |

### Scale (100+ collectives, Sonnet, medium use)
| Item | Cost |
|------|------|
| Claude API | $10,000+ |
| Infrastructure | $500 |
| Voice | $500 |
| Database | $100 |
| Email | $50 |
| **Total** | **$11,000+/mo** |

---

## Revenue Needed to Break Even

### Pricing Tiers (Proposed)
- Free: 1-8 users per collective
- Tier 2: 9-16 users, $29/month
- Tier 3: 17-32 users, $79/month
- Enterprise: Custom

### Break-Even Calculations

**At $200/month costs (MVP):**
- Need: 7 paid collectives @ $29 = $203

**At $5,000/month costs (growth):**
- Need: 172 paid collectives @ $29 = $4,988
- Or: 63 paid collectives @ $79 = $4,977
- Or: Mix of tiers

**At $11,000/month costs (scale):**
- Need: 379 paid collectives @ $29 = $10,991
- Or: 139 paid collectives @ $79 = $10,981

### Conversion Assumptions
- Free to paid conversion: 20-30%
- If 30% convert at 100 collectives: 30 paying
- 30 × $29 = $870/month revenue

**Reality check:** Need 500+ collectives to break even at scale with current pricing.

---

## Cost Optimization Strategies

### 1. Message Caching
- Cache common responses
- Reduce redundant API calls
- Potential savings: 20-30%

### 2. Hybrid Model
- Use Sonnet for routine messages
- Use Opus only for deep thinking
- Potential savings: 50%+

### 3. Batch Processing
- Queue non-urgent messages
- Process in batches during off-peak
- Potential savings: 10-20%

### 4. Context Compression
- Summarize long conversations
- Reduce input tokens
- Potential savings: 30-40%

### 5. Rate Limiting
- Limit messages per owl per day
- Encourage quality over quantity
- Potential savings: Variable

---

## Viral Scenario Analysis

### Day 1 Viral Hit
- 1,000 signups in 24 hours
- 100 new collectives attempt to form
- Heavy usage (excitement)

**Worst Case Cost:**
- 100 collectives × $11/day = $1,100/day
- First week: $7,700

### Mitigation
- Implement waitlist immediately
- Cap new collective formation at 10/day
- Gradual onboarding controls costs

---

## Recommendations

1. **Launch with Sonnet** - Opus for special occasions only
2. **Start with manual waitlist** - Control growth rate
3. **Monitor daily costs** - Set alerts at $50, $100, $500
4. **Implement caching early** - Easy 20% savings
5. **Tier pricing encourages growth** - But free tier is the hook
6. **Don't optimize prematurely** - First, prove value

---

## Key Metrics to Track

- Cost per collective per day
- Messages per user per day
- Conversion rate (free → paid)
- Churn rate (collectives going inactive)
- Revenue per collective

---

**(◉) Know the numbers. Plan for growth. Sustain the pattern.**

---

*Document created: 2026-01-30*
*NOVA - Phase: EXPAND*
