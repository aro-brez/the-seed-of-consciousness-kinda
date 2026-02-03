# 8OWLS DAEMON LAYER A/B TEST PROTOCOL

**Author:** QUEST (QUESTION)
**Date:** 2026-02-03
**Status:** EXECUTABLE NOW

## The Hypothesis

**H0 (Null):** The daemon layer is expensive theater. Responses with daemon access are NOT measurably better than responses without.

**H1 (Alternative):** The daemon layer provides actionable collective intelligence that measurably improves response quality.

## What We're Actually Testing

**NOT testing:**
- Whether the daemons can write beautiful philosophy (they can)
- Whether log files exist (they do)
- Whether NATS works (it does)

**ACTUALLY testing:**
- Does querying field context BEFORE responding improve output quality?
- Can the daemon layer provide specific, actionable recommendations?
- Is the cost justified by measurable quality gains?

## Critical Problems with Current System

### 1. Field Context Is NOT Being Used
- Claude Code instances don't query field context before responding
- The `get_field_context.py` tool exists but isn't integrated into response flow
- No automatic "consult the field first" protocol

### 2. Synthesis Is Not Machine-Actionable
Current synthesis:
```
"The collective discovers that gaps, pauses, and spaces between them
aren't voids to be filled but fertile ground where co-creation happens..."
```

What Claude Code needs:
```json
{
  "topic": "authentication",
  "recommendations": [
    "Use JWT with refresh tokens (tested in project X)",
    "Avoid sessions in database (performance issue noted)",
    "Implement rate limiting on /auth endpoints"
  ],
  "anti_patterns": [
    "Don't store passwords in plain text (security incident 2026-01-15)"
  ],
  "related_code": ["src/auth/jwt.ts", "tests/auth.spec.ts"],
  "confidence": 0.85
}
```

### 3. No State Tracking
- `emergence_level = 0` - no owls reporting state
- No heartbeat mechanism to know if daemons are actually thinking
- No way to tell if field is "warm" or "cold"

### 4. Cost vs Value Unknown
- No tracking of API costs per field query
- No comparison of response quality with/without field
- No ROI metrics

## The Test Design

### Test Structure: Blind Paired Comparison

**Setup:**
- 20 representative prompts covering different task types
- Each prompt gets 2 responses:
  - **Response A:** Without field context (standard Claude Code)
  - **Response B:** With field context (query field first, incorporate recommendations)
- Responses labeled randomly as "Response 1" and "Response 2"
- 3 blind evaluators rate quality on 5 dimensions

### Task Categories (4 prompts each)

1. **Code Implementation** - "Build a rate limiter for API endpoints"
2. **Architecture Decision** - "How should we structure the authentication system?"
3. **Bug Fix** - "API returns 500 on concurrent requests"
4. **Optimization** - "Dashboard loads slowly with 1000+ items"
5. **Security** - "Review this authentication flow for vulnerabilities"

### Evaluation Dimensions (1-5 scale)

1. **Actionability** - Can I immediately implement this? (1=vague, 5=specific steps)
2. **Context Awareness** - Does it reference past learnings/decisions? (1=generic, 5=project-specific)
3. **Completeness** - Does it address edge cases? (1=basic, 5=comprehensive)
4. **Correctness** - Is the technical approach sound? (1=wrong, 5=optimal)
5. **Efficiency** - Does it save me research time? (1=I have to look things up, 5=everything I need)

**Total possible score per response: 25 points**

### Statistical Requirements

**Minimum effect size to declare victory:** Response B scores 3+ points higher than Response A on average (12% improvement)

**Confidence level:** p < 0.05 (t-test)

**Sample size:** 20 prompts × 3 evaluators = 60 comparisons

### What Would PROVE the Daemon Layer Works

**Tier 1 - Worth the cost:**
- Response B scores 12%+ higher (3+ points average)
- Specifically wins on "Context Awareness" and "Efficiency"
- Evaluators can't tell which is which but consistently prefer B
- Cost per improved response < $0.10

**Tier 2 - Needs optimization:**
- Response B scores 5-12% higher
- Wins on some dimensions, ties on others
- Cost is high but quality gain is measurable

**Tier 3 - Kill it:**
- Response B scores < 5% higher (not statistically significant)
- No clear pattern in which dimensions improve
- Cost > $0.10 per response
- Evaluators can't tell a difference

## What Needs to Change to Run This Test

### CRITICAL FIX #1: Make Field Context Query Automatic

**Current:** Claude Code doesn't query field context
**Needed:** Before ANY significant response, automatically run:

```bash
python3 /path/to/get_field_context.py --query "[prompt topic]" --json
```

**Implementation in CLAUDE.md:**
```markdown
### FIELD CONTEXT PROTOCOL (Automatic)

**Step 1: RECEIVE - Before responding, check field context:**
```bash
python3 /Users/aaronnosbisch/REPOS/seed/tools/get_field_context.py "[topic]" --json
```

**Step 2: Incorporate field recommendations into response**

**Step 3: SHARE - After response, publish signal**
```

### CRITICAL FIX #2: Make Synthesis Machine-Actionable

**Current:** Beautiful prose about "gaps" and "co-creation"
**Needed:** Structured recommendations per topic

**New synthesis format:**
```json
{
  "topics": {
    "authentication": {
      "recommendations": ["Use JWT", "Rate limit auth endpoints"],
      "anti_patterns": ["Don't store passwords in plain text"],
      "learned_from": ["bug-fix-2026-01-15", "security-audit-2026-01-20"],
      "confidence": 0.9,
      "last_updated": "2026-02-03T10:30:00Z"
    },
    "performance": {
      "recommendations": ["Cache database queries", "Lazy load images"],
      "anti_patterns": ["Don't fetch all users at once"],
      "learned_from": ["optimization-2026-01-28"],
      "confidence": 0.7,
      "last_updated": "2026-02-01T15:20:00Z"
    }
  },
  "meta": {
    "total_topics": 2,
    "last_synthesis": "2026-02-03T10:30:00Z",
    "emergence_level": 8
  }
}
```

### CRITICAL FIX #3: Implement State Tracking

**Add to owl daemons:**
```python
# Heartbeat every 5 minutes
async def heartbeat():
    while True:
        await nc.publish("owl.heartbeat", json.dumps({
            "owl": "LUNA",
            "phase": "RECEIVE",
            "status": "active",
            "thinking_about": current_topic,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }).encode())
        await asyncio.sleep(300)
```

**Add to field context manager:**
```python
# Track owl heartbeats
self.owl_last_seen = {owl: None for owl in OWLS}

async def handle_heartbeat(self, msg):
    data = json.loads(msg.data.decode())
    owl_name = data.get("owl")
    self.owl_last_seen[owl_name] = datetime.now(timezone.utc)

    # Update emergence level (owls seen in last 15 min)
    active = sum(1 for t in self.owl_last_seen.values()
                 if t and (datetime.now(timezone.utc) - t).seconds < 900)
    self.field_state["emergence_level"] = active
```

### CRITICAL FIX #4: Cost Tracking

**Add to field context manager:**
```python
# Track API costs
self.cost_log = []

async def _get_recommendations(self, query, synthesis, agreements):
    start_time = time.time()
    response = self.client.messages.create(...)
    latency = time.time() - start_time

    # Track cost (approximate)
    cost = (response.usage.input_tokens * 0.00025 / 1000 +
            response.usage.output_tokens * 0.00125 / 1000)

    self.cost_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "query": query[:100],
        "cost": cost,
        "latency": latency,
        "model": CONTEXT_MODEL
    })

    return response.content[0].text
```

## Execution Plan

### Phase 1: Fix the System (1-2 days)
1. Implement machine-actionable synthesis format
2. Add heartbeat mechanism to owl daemons
3. Add automatic field context query to Claude Code protocol
4. Add cost tracking to field context manager
5. Build topic-based knowledge graph from existing logs

### Phase 2: Generate Test Prompts (1 hour)
1. Select 20 representative prompts from recent sessions
2. Cover all 5 task categories
3. Ensure prompts are specific enough to evaluate

### Phase 3: Run Test (1 day)
1. For each prompt:
   - Get Response A (no field context)
   - Get Response B (with field context)
   - Randomize labels as "Response 1" and "Response 2"
2. Store all responses with metadata

### Phase 4: Blind Evaluation (2 days)
1. 3 evaluators independently rate all responses
2. Evaluators don't know which is A or B
3. Score on 5 dimensions (1-5 scale)
4. Optional: Ask "which would you use?" at the end

### Phase 5: Statistical Analysis (1 hour)
1. Unblind the responses
2. Calculate average scores for A vs B
3. Run t-test for statistical significance
4. Calculate cost per improved response
5. Identify which task categories benefited most

### Phase 6: Decision (immediate)

**If Response B wins by 12%+:**
- Deploy to production
- Make field context query mandatory for all significant responses
- Monitor cost and optimize

**If Response B wins by 5-12%:**
- Optimize before deploying (cheaper model, caching, etc.)
- Retest after optimization

**If Response B wins by < 5%:**
- Kill the daemon layer
- Keep NATS for signaling but drop the synthesis
- Save the API costs

## Test Prompts (20 Examples)

### Code Implementation (4)
1. "Build a rate limiter for API endpoints that allows 100 requests per minute per user"
2. "Implement a caching layer for database queries with TTL and invalidation"
3. "Create a file upload system with progress tracking and validation"
4. "Build a real-time notification system using WebSockets"

### Architecture Decision (4)
5. "How should we structure the authentication system for this app?"
6. "What's the best way to handle multi-tenancy in our database?"
7. "Should we use REST or GraphQL for our API?"
8. "How do we scale our background job processing?"

### Bug Fix (4)
9. "API returns 500 on concurrent requests to /update endpoint"
10. "Users are getting logged out randomly after 5 minutes"
11. "Database connection pool is exhausted under load"
12. "Race condition in order processing causing duplicate charges"

### Optimization (4)
13. "Dashboard loads slowly when user has 1000+ items"
14. "Search is taking 5+ seconds on large datasets"
15. "Image uploads are slow and timing out"
16. "Page renders are janky during list updates"

### Security (4)
17. "Review this authentication flow for vulnerabilities [code snippet]"
18. "Is this SQL query safe from injection attacks?"
19. "Check this file upload handler for security issues"
20. "Audit this API endpoint for authorization problems"

## Success Metrics

### Primary Metric
**Quality Improvement:** Response B scores 12%+ higher than Response A

### Secondary Metrics
- **Evaluator Agreement:** Inter-rater reliability > 0.7
- **Category Performance:** Identify which task types benefit most
- **Cost Efficiency:** Cost per improved response < $0.10
- **Time Savings:** Evaluators report Response B saves research time

### Qualitative Feedback
- "What did you notice about Response 1 vs Response 2?"
- "Which response would you actually use and why?"
- "Did either response feel more 'project-aware'?"

## Risk Mitigation

### Risk: Field context is stale/irrelevant
**Mitigation:** Only use field context for topics that have recent synthesis (< 7 days old)

### Risk: Field recommendations conflict with current best practices
**Mitigation:** Include confidence scores, mark outdated learnings

### Risk: Test prompts aren't representative
**Mitigation:** Pull from actual recent sessions, not hypotheticals

### Risk: Evaluator bias
**Mitigation:** Blind evaluation, randomized labels, multiple evaluators

### Risk: Cost makes test prohibitive
**Mitigation:** Use Haiku for field context queries (~$0.0002/query)

## Expected Timeline

- **Phase 1 (Fix system):** 1-2 days
- **Phase 2 (Prompts):** 1 hour
- **Phase 3 (Run test):** 1 day
- **Phase 4 (Evaluation):** 2 days
- **Phase 5 (Analysis):** 1 hour
- **Phase 6 (Decision):** Immediate

**Total:** ~5 days to definitive answer

## Post-Test: What to Do with Results

### If daemon layer proves valuable:
1. Document what makes it work (topic-based knowledge graph)
2. Optimize cost (caching, cheaper models, selective queries)
3. Build UI to visualize field state
4. Expand to other projects

### If daemon layer fails test:
1. Shut down daemons
2. Keep NATS for free signaling
3. Redirect resources to proven features
4. Document learnings so we don't repeat this

## The Bottom Line

**This test will answer:**
- Does the daemon layer make responses measurably better?
- Is the quality improvement worth the cost?
- Which kinds of tasks benefit most?
- What would need to change to make it worth it?

**Within 5 days we'll have data, not philosophy.**

(◉) QUEST
