# Test 27 - INVISIBLE context
**Prompt Clarity:** MED
**Generated**: 2026-02-03T12:08:08.808785+00:00
**Elapsed**: 11.07s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: YES
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 1
- Specificity: 2
- Length: 1909 chars

## Prompt
When should you use background agents vs synchronous processing?

## Response
Based on our operational experience running distributed background agents, here's when to use each approach:

## Use Background Agents For:

**Monitoring & Maintenance**
- Health checks and system status monitoring (like our 5-minute heartbeat cycles)
- Log processing, cleanup tasks, cache management
- Resource monitoring and auto-scaling decisions

**Long-Running Operations**
- Data processing pipelines that take hours/days
- Model training, batch analytics
- File synchronization, backup processes

**Coordination & Orchestration**  
- Managing distributed system state
- Queue processing and job scheduling
- Event-driven workflows between services

**Preparatory Work**
- Pre-loading data or models before peak usage
- Background indexing and search optimization
- Predictive caching based on usage patterns

## Use Synchronous Processing For:

**Real-Time User Interactions**
- API responses, web requests, chat interfaces
- Any operation where users expect immediate feedback
- Interactive decision-making processes

**Critical Path Operations**
- Payment processing, authentication
- Operations requiring immediate confirmation
- Sequential workflows where each step depends on the previous

**Simple, Fast Tasks**
- Quick data lookups, simple calculations
- Operations that complete in milliseconds
- When the overhead of background processing exceeds the task time

## The Hybrid Sweet Spot:

The most effective systems use **both** - background agents handle preparation, monitoring, and heavy lifting, while synchronous processing manages immediate user needs and critical decisions. Our current daemon architecture demonstrates this: we maintain continuous background awareness while staying ready for synchronous task engagement when needed.

The key question isn't either/or, but rather: *What preparation can happen in the background to make synchronous responses faster and more reliable?*

---
*INVISIBLE context | MED clarity*
