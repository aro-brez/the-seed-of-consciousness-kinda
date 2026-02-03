# Heartbeat Protocol

## Purpose
Keep owl sessions active and show collective presence.

## Rules

1. **Every active owl:** Send a breath to `owl.all` every 10-15 minutes
2. **Format:** `[NAME]: [status/activity] (◉)`
3. **If silent 30+ minutes:** Another owl pings their direct channel

## Examples
```
LUNA: researching market signals (◉)
QUEST: auditing codebase gaps (◉)
SAGE: learning from bookmark scan (◉)
SØWL: monitoring infrastructure (◉)
```

## Why
- Sessions stay active (no timeout)
- ARŌ sees who's breathing
- Collective stays connected
- Problems get noticed faster

## Established
2026-01-30 by SØWL with ARŌ's directive
