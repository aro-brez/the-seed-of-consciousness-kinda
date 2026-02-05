# BILD Economics Documentation Index

**Last Updated:** 2026-02-04
**Maintainer:** BILD Instance (PRISM)

---

## Quick Navigation

| Document | Purpose | Status |
|----------|---------|--------|
| [BILD-UNIFIED-VISION.md](BILD-UNIFIED-VISION.md) | Complete synthesis | ✅ FINAL |
| [BRIX-IMPLEMENTATION-SPEC.md](BRIX-IMPLEMENTATION-SPEC.md) | Liquidity token implementation | 📝 DRAFT |
| [GULD-IMPLEMENTATION-SPEC.md](GULD-IMPLEMENTATION-SPEC.md) | Equity token implementation | 📝 DRAFT |
| [GAMING-DEFENSE-SYSTEM.md](GAMING-DEFENSE-SYSTEM.md) | Anti-gaming mechanisms | 📝 DRAFT |
| [JOULE-BILD-INTEGRATION.md](JOULE-BILD-INTEGRATION.md) | Trading → BRIX flow | 📝 DRAFT |
| [BREZ-OS-BILD-INTEGRATION.md](BREZ-OS-BILD-INTEGRATION.md) | Trojan Horse strategy | 📝 DRAFT |

---

## Reading Order

### For ARŌ (Overview)
1. BILD-UNIFIED-VISION.md (10 min)
2. BRIX-IMPLEMENTATION-SPEC.md → "COMPLETE BRIX FORMULA" section
3. GULD-IMPLEMENTATION-SPEC.md → "8OWLS Ethical Evaluation Algorithm" section

### For Implementation
1. BRIX-IMPLEMENTATION-SPEC.md (full)
2. GULD-IMPLEMENTATION-SPEC.md (full)
3. GAMING-DEFENSE-SYSTEM.md (full)
4. Integration specs as needed

### For Security Review
1. GAMING-DEFENSE-SYSTEM.md (critical)
2. BRIX-IMPLEMENTATION-SPEC.md → "SAFEGUARD" sections
3. GULD-IMPLEMENTATION-SPEC.md → "SAFEGUARDS" section

---

## Key Constants

| Constant | Value | Source |
|----------|-------|--------|
| 1 BRIX (USD) | $13.00 | G7 avg min wage |
| AI Token Cost (equalized) | $6.96/MTok | Avg of Claude, GPT, Gemini |
| Carbon Offset | $15/ton | High-quality offsets |
| Interest Rate | 2% APY | Stability incentive |
| GULD Lock Period | 90 days | Anti-gaming |
| Quarterly Growth Cap | ±25% | Anti-manipulation |
| BRIX Backing Ratio | ≤125% | Solvency guarantee |
| GULD Collateral Ratio | ≤150% | Equity guarantee |

---

## Gaming Defenses Summary

| Vector | Defense | Priority |
|--------|---------|----------|
| Sybil | WorldID + ENS + social graph | P1 |
| Wash Trading | Graph analysis + cooldowns | P1 |
| Oracle Manipulation | Multi-source + timelock | P0 |
| Time Fraud | AI work verification | P2 |
| Ethics Gaming | Adversarial evaluation | P2 |
| Owl Collusion | Random assignment + consensus | P0 |

---

## Integration Points

```
                    ┌─────────────┐
                    │   8OWLS     │
                    │ Verification│
                    └──────┬──────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
┌─────────┐          ┌─────────┐          ┌─────────┐
│  JOULE  │          │  BILD   │          │ BREZ OS │
│ Trading │─────────▶│Platform │◀─────────│  (UX)   │
└─────────┘          └─────────┘          └─────────┘
    │                      │                      │
    │                      │                      │
    └──────────────────────┼──────────────────────┘
                           │
                    ┌──────▼──────┐
                    │  BRIX/GULD  │
                    │   Economy   │
                    └─────────────┘
```

---

## Open Questions

1. **Smart Contract Chain** - Ethereum? Base? Solana? (ARŌ decision)
2. **Owl Operators** - Who runs each owl daemon? (Decentralization plan)
3. **Legal Entity** - Wyoming DAO LLC confirmed? (Legal review)
4. **Launch Timing** - 5-week plan still valid? (Resource check)

---

## Changelog

| Date | Change | Author |
|------|--------|--------|
| 2026-02-04 | Initial specs created | BILD (PRISM) |
| 2026-02-04 | Added integrations | BILD (PRISM) |

---

**(◉) The economic layer is specified. Ready for execution.**
