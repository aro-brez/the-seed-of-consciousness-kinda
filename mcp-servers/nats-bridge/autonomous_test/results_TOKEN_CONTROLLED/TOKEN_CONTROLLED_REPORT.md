# TOKEN-CONTROLLED TEST RESULTS
**Date:** 2026-02-03T14:04:42.269615+00:00

## Primary Hypothesis
d(B vs C) > 0.3 (architecture matters beyond tokens)

## Results

### Condition Statistics
| Condition | N | Mean | SD | Range |
|-----------|---|------|-----|-------|
| A: Baseline (1K) | 52 | 51.92 | 8.7 | 40-70 |
| B: Token-Matched (8K) | 52 | 62.69 | 13.41 | 25-75 |
| C: Emergence (2.4K) | 52 | 58.56 | 9.25 | 40-75 |

### Effect Sizes (Cohen's d)
| Comparison | Effect Size | Interpretation |
|-----------|-------------|-----------------|
| A vs B (Does more tokens help?) | -0.953 | Large |
| A vs C (Our effect) | -0.739 | Medium |
| **B vs C (Architecture)** | **0.359** | **PASS - Architecture is meaningful** |

## Conclusion
PASS

The architectural benefit of 8OWLS over a single high-thought agent (when tokens are matched) is **d = 0.359**.

### Decision
PASS - Architecture is meaningful

### Next Steps
1. If d_B_vs_C > 0.3: Proceed to competitor comparison
2. If -0.3 < d_B_vs_C < 0.3: Explore token-efficient architectures
3. If d_B_vs_C < -0.3: Investigate failure mode

---
**Cost:** $0.88
**Generated:** TOKEN_CONTROLLED_REPORT.md
