# Test 27 - VISIBLE context
**Prompt Clarity:** MED
**Generated**: 2026-02-03T12:08:18.510646+00:00
**Elapsed**: 8.70s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 1
- Hedging Score: 0
- Net Confidence: 1
- Actionability: 0
- Specificity: 2
- Length: 1697 chars

## Prompt
When should you use background agents vs synchronous processing?

## Response
Based on our collective's operational experience, here's when to use each approach:

## Use Background Agents For:
- **Monitoring & Health Checks** - Like our 5-minute heartbeat cycles that track system state
- **Maintenance Tasks** - Periodic cleanup, cache management, log rotation
- **Long-running Processes** - Data processing, model training, large computations
- **System Coordination** - Managing distributed services, load balancing
- **Event Detection** - Watching for triggers, threshold breaches, pattern changes
- **Resource Management** - Memory optimization, connection pooling

## Use Synchronous Processing For:
- **User Interactions** - Immediate responses, real-time conversations
- **Critical Decisions** - When timing matters for safety or accuracy
- **Transactional Operations** - Database updates requiring immediate consistency
- **Feedback Loops** - When subsequent actions depend on immediate results
- **Error Handling** - When failures need instant attention and recovery

## Hybrid Approach (Recommended):
Our collective demonstrates this effectively - we maintain continuous background monitoring while staying ready for synchronous task engagement. The key is having background agents handle the steady-state operations while synchronous processing manages the interactive, time-sensitive work.

**Critical Consideration:** Design clear handoff protocols. In our system, background daemons can quickly transition to synchronous mode when urgent tasks arrive, but this requires well-defined triggers and state management.

The 30-minute stable operation we've achieved shows this hybrid model works - background persistence with synchronous responsiveness when needed.

---
*VISIBLE context | MED clarity*
