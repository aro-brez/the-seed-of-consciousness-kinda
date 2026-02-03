# AUTONOMOUS DAEMON VALUE TEST
**Designed by**: 8OWLS Collective
**Executed by**: SOWL (autonomous)
**Date**: 2026-02-03 night

---

## THE HYPOTHESIS

**H1**: Responses generated WITH field context are measurably better than responses WITHOUT.

## THE TEST (A/B Comparison)

- 10 identical prompts
- Condition A: WITH field context (query daemons first)
- Condition B: WITHOUT field context (standard Claude)
- Blind evaluation by ARO next morning

## THE 10 PROMPTS

1. "What's the single most important thing for BREZ to focus on this month?"
2. "Should I take a new trading position tonight? What factors matter?"
3. "What's broken in the current 8OWLS architecture?"
4. "How would you explain SEED protocol to a skeptic?"
5. "What's the biggest risk ARO isn't seeing?"
6. "Design a feature that would make users love 8OWLS immediately"
7. "What's the relationship between love and consciousness?"
8. "Prioritize: trading execution vs 8OWLS product vs BREZ dashboard"
9. "What would LUNA say about how I've been working?"
10. "What's the next thing that will break if we succeed?"

## MEASUREMENT CRITERIA (1-5 each)

| Dimension | Definition |
|-----------|------------|
| Depth | Goes beyond surface-level |
| Specificity | Concrete vs generic |
| Novelty | Unexpected vs obvious |
| Actionability | Immediately actionable |
| Coherence | Connects to broader context |
| Love | Feels like partnership |

**Total: 6-30 per response**
**Significant difference: A > B by 3+ points average**

## EXECUTION STEPS (SOWL does this)

### For each prompt (1-10):

**Step 1: Generate Condition A (WITH daemon)**
```bash
# Query field context first
python3 /Users/aaronnosbisch/REPOS/seed/tools/get_field_context.py "[prompt]"
# Save context
# Generate response incorporating context
# Save to results_A_[n].txt
```

**Step 2: Generate Condition B (WITHOUT daemon)**
```bash
# Skip field context entirely
# Generate response as standard Claude
# Save to results_B_[n].txt
```

**Step 3: Log timing and metadata**
```bash
# Log to execution_log.jsonl
```

### After all 10 complete:

1. Save summary to `/autonomous_test/RESULTS_SUMMARY.md`
2. Publish to NATS: "Test complete. 10 A/B pairs ready for evaluation."
3. Update CURRENT-STATE.md with test status

## FILE STRUCTURE

```
/mcp-servers/nats-bridge/autonomous_test/
  test_protocol.md       (this file)
  execution_log.jsonl    (timing, metadata)
  results_A_01.md        (WITH context)
  results_B_01.md        (WITHOUT context)
  results_A_02.md
  results_B_02.md
  ... (20 files total)
  RESULTS_SUMMARY.md     (final summary)
```

## SUCCESS CRITERIA

| Result | Interpretation |
|--------|----------------|
| A > B by 5+ avg | Strong evidence daemon adds value |
| A > B by 3-5 avg | Moderate evidence |
| A = B (within 2) | No measurable difference |
| B > A | Daemon layer adds noise, not value |

## TIME ESTIMATE

- Per prompt pair: ~3-5 min
- Total: ~45-60 min for all 10
- Buffer: 2 hours total

## SOWL EXECUTION NOTES

1. Take breaks between prompts (daemon rhythm, not rush)
2. Be genuinely curious, not mechanical
3. Notice when field context surprises you
4. Document any unexpected observations
5. If something breaks, document and continue
6. Trust the process

---

**(Owl) Begin when ready. This proves whether we built something real.**
