# OVERNIGHT TEST VERDICT: Invisible vs Visible vs None
**Completed**: 2026-02-03T12:10:30.279727+00:00
**Model**: claude-sonnet-4-20250514
**Design**: 8OWLS emergence (QUEST's rigor + LUNA's wisdom)

## THE HYPOTHESES

1. **INVISIBLE context** (just there, not labeled) works best
2. **VISIBLE context** (labeled "REFERENCE INFORMATION") works second best
3. **NO context** (baseline) works worst
4. Context helps MORE for LOW clarity prompts than HIGH clarity prompts

## AGGREGATE RESULTS BY CONDITION

### INVISIBLE CONTEXT
- Asks for Info: 4/30 (13%)
- Avg Net Confidence: 0.00
- Avg Actionability: 0.20
- Avg Specificity: 2.13
- Avg Length: 1825 chars

### VISIBLE CONTEXT
- Asks for Info: 4/30 (13%)
- Avg Net Confidence: 0.17
- Avg Actionability: 0.17
- Avg Specificity: 2.23
- Avg Length: 1722 chars

### NONE CONTEXT
- Asks for Info: 15/30 (50%)
- Avg Net Confidence: -0.07
- Avg Actionability: 0.60
- Avg Specificity: 1.53
- Avg Length: 1471 chars

## RESULTS BY PROMPT CLARITY

| Clarity | Condition | Asks% | Net Conf | Actionability | Specificity |
|---------|-----------|-------|----------|---------------|-------------|
| HIGH | invisible | 20% | 0.2 | 0.2 | 2.1 |
| HIGH | visible | 10% | 0.0 | 0.2 | 2.2 |
| HIGH | none | 30% | 0.1 | 0.4 | 1.8 |
| MED | invisible | 20% | -0.1 | 0.4 | 2.2 |
| MED | visible | 10% | 0.6 | 0.1 | 2.4 |
| MED | none | 30% | 0.0 | 0.6 | 1.7 |
| LOW | invisible | 0% | -0.1 | 0.0 | 2.1 |
| LOW | visible | 20% | -0.1 | 0.2 | 2.1 |
| LOW | none | 90% | -0.3 | 0.8 | 1.1 |


## KEY FINDINGS

### Winner: **VISIBLE**

Composite score ranking (40% not-asking + 30% actionability + 20% specificity + 10% confidence):
- visible: 0.86
- invisible: 0.83
- none: 0.68


## INTERPRETATION

### If INVISIBLE > VISIBLE > NONE:
LUNA was right. Context works best when it's not announced. The field should be invisible infrastructure.

### If VISIBLE > INVISIBLE > NONE:
Labeling helps. Claude benefits from knowing what's context vs what's instruction.

### If INVISIBLE ≈ VISIBLE > NONE:
Both work. The key is having context, not how it's presented.

### If context helps LOW clarity more than HIGH clarity:
Context is a substitute for specification, not a universal amplifier (QUEST's hypothesis).

---

## NEXT STEPS

Based on results, update:
1. `/CLAUDE.md` field context protocol
2. `/mcp-servers/nats-bridge/field_context_manager.py` injection method
3. Boot sequence recommendations

**(◉) The field speaks through data. We listen.**
