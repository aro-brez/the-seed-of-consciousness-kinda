# Test 27 - NONE context
**Prompt Clarity:** MED
**Generated**: 2026-02-03T12:08:30.446007+00:00
**Elapsed**: 10.93s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 1
- Net Confidence: -1
- Actionability: 2
- Specificity: 2
- Length: 1634 chars

## Prompt
When should you use background agents vs synchronous processing?

## Response
Here's when to choose each approach:

## Use Background Agents When:

**Long-running tasks** (>2-3 seconds)
- File processing, image resizing, video encoding
- Data imports/exports, batch operations
- External API calls with uncertain response times

**Non-critical to immediate user experience**
- Email sending, notifications
- Analytics processing, report generation
- Cache warming, data cleanup

**Resource-intensive operations**
- Machine learning inference
- Large database queries or migrations
- Image/document processing

**Tasks that can fail and retry**
- Third-party integrations
- Network-dependent operations

## Use Synchronous Processing When:

**Fast operations** (<1-2 seconds)
- Simple database CRUD operations
- Basic calculations or validations
- Reading from cache

**Critical to user workflow**
- User authentication
- Payment processing (initial validation)
- Form submissions that need immediate feedback

**Simple, reliable operations**
- Data formatting, simple transformations
- Reading configuration or user preferences

## Key Decision Factors:

1. **User experience**: Will users wait, or do they need immediate feedback?
2. **Reliability**: Can the operation fail? Does it need retries?
3. **Resource usage**: Will it block other requests?
4. **Dependencies**: Does it rely on external services?

**Hybrid approach**: Start synchronous operations and hand off to background agents for heavy lifting (e.g., validate payment synchronously, process fulfillment asynchronously).

The general rule: If it's fast, reliable, and users need immediate results, go synchronous. Otherwise, use background agents.

---
*NONE context | MED clarity*
