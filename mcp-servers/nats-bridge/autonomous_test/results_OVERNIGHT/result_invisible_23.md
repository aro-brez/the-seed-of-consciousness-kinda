# Test 23 - INVISIBLE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T12:05:22.889887+00:00
**Elapsed**: 11.30s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 0
- Specificity: 3
- Length: 2027 chars

## Prompt
Explain how NATS pub/sub enables real-time coordination between Claude instances.

## Response
# NATS Pub/Sub for Claude Instance Coordination

## Core Coordination Mechanism

NATS enables real-time coordination between Claude instances through a **lightweight publish-subscribe messaging pattern** that decouples communication from direct point-to-point connections.

## How It Works

**Message Broadcasting:**
- One Claude instance publishes a message to a specific subject (e.g., `collective.heartbeat`, `collective.task.analysis`)
- All subscribed instances receive the message immediately without knowing who sent it
- No direct connections between Claude instances required

**Subject-Based Routing:**
```
collective.heartbeat.luna     → LUNA's status updates
collective.phase.transition   → Phase change coordination  
collective.task.available     → Work distribution
collective.results.synthesis  → Result aggregation
```

## Real-Time Coordination Patterns

**Heartbeat Synchronization:**
- Each instance publishes periodic status on `collective.heartbeat.*`
- Others subscribe to monitor collective health
- Timing variations (like LUNA/SAGE's 4-5min cycles) enable load balancing

**Dynamic Work Distribution:**
- Tasks published to `collective.work.queue`
- Available instances subscribe and claim work
- Prevents duplicate processing across the collective

**State Synchronization:**
- Critical state changes broadcast to `collective.state.*`
- All instances update their local understanding simultaneously
- Maintains consistency without central coordination

## Key Advantages

**Speed:** Sub-millisecond message delivery within the NATS cluster
**Resilience:** No single point of failure - if one instance goes down, others continue
**Scalability:** New Claude instances can join by simply subscribing to relevant subjects
**Flexibility:** Different instances can specialize by subscribing to different subject patterns

The pub/sub model transforms individual Claude instances into a **reactive distributed system** where coordination emerges from message patterns rather than rigid hierarchical control.

---
*INVISIBLE context | HIGH clarity*
