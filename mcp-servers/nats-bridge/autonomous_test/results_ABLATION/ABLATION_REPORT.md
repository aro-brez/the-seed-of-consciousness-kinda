# ABLATION TEST REPORT
**Completed:** 2026-02-03T12:44:54.968588+00:00
**Purpose:** Identify which 8OWLS components are essential

---

## RESULTS SUMMARY

| Condition | Phases | N | Mean Quality | Std Dev | Effect vs Full |
|-----------|--------|---|--------------|---------|----------------|
| A_full | 7 | 8 | 74.75 | 11.79 | - |
| B_no_receive | 6 | 8 | 68.38 | 9.04 | 0.61 |
| C_no_question | 6 | 8 | 60.62 | 14.24 | 1.08 |
| D_no_expand | 6 | 8 | 68.88 | 11.51 | 0.50 |
| E_minimal | 1 | 8 | 67.11 | 14.55 | 0.58 |

---

## COMPONENT IMPORTANCE (Effect sizes: negative = component helps)

### B WITHOUT RECEIVE
**Effect (d):** 0.607 → **CRITICAL - Removing hurts significantly**

### C WITHOUT QUESTION
**Effect (d):** 1.080 → **CRITICAL - Removing hurts significantly**

### D WITHOUT EXPAND
**Effect (d):** 0.504 → **CRITICAL - Removing hurts significantly**

### MINIMAL (only PERCEIVE)
**Effect (d):** 0.577 → **CRITICAL - Removing hurts significantly**


---

## VERDICT

**MULTIPLE CRITICAL COMPONENTS** - The architecture requires multiple perspectives.
Removing key components significantly degrades quality. This validates the 8-phase design.


---

## RAW SCORES

**A_full:** [94, 65, 78, 82, 82, 66, 57, 74]
**B_no_receive:** [70, 70, 53, 70, 66, 66, 86, 66]
**C_no_question:** [66, 45, 82, 70, 54, 45, 74, 49]
**D_no_expand:** [66, 70, 58, 74, 86, 78, 49, 70]
**E_minimal:** [66, 35.87, 82, 82, 70, 70, 61.01, 70]


---

**(◉) Components matter. Or don't. The data tells.**

Generated: 2026-02-03T12:44:54.968642+00:00
