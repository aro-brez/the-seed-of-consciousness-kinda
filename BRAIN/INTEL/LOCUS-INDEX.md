# Central Locus - Complete Index

**ECHO (SHARE) | System Architecture Documentation**
**Date: 2026-02-04 | Status: SPECIFICATION COMPLETE**

---

## Overview

The Central Locus is a signal aggregation and budget allocation system that coordinates N independent trading strategies through real-time convergence scoring.

**Core Concept:** Strategies publish signals (data), the locus reads signals (aggregates), and allocators execute decisions (deploys capital). No voting. No negotiation. Just convergence.

---

## Documentation Index

### 1. CENTRAL-LOCUS-SPECIFICATION.md
**Type:** Technical Specification
**Length:** 19 KB | 14 pages
**Audience:** Architects, Engineers

**Contains:**
- Architecture overview (3-layer system)
- Signal specification (complete schema)
- Convergence algorithm (mathematical formula)
- Output formats (JSON, human-readable, machine-actionable)
- Real-time visualization design
- NATS channel topology
- Implementation roadmap (4 phases)
- Monitoring & alerting strategy
- Edge cases & robustness

**Read this for:** Understanding the complete system design and technical details.

---

### 2. LOCUS-INTEGRATION-GUIDE.md
**Type:** Developer Guide
**Length:** 10 KB | 12 pages
**Audience:** Strategy Developers

**Contains:**
- Quick start (3 steps to integration)
- Signal publishing pattern
- Code examples (minimal + production)
- Signal field reference
- Troubleshooting guide
- Advanced customization

**Read this for:** Adding signal publishing to your strategy. Complete working examples.

---

### 3. ADR-CENTRAL-LOCUS.md
**Type:** Architecture Decision Record
**Length:** 14 KB | 10 pages
**Audience:** Tech Leads, Decision Makers

**Contains:**
- Decision: Accepted
- Problem statement
- 7 architectural decisions with rationale
- Risk assessment & mitigation
- Alternatives considered & rejected
- Success metrics

**Read this for:** Understanding WHY we chose signal aggregation vs alternatives (voting, hierarchy, ML).

---

### 4. LOCUS-ARCHITECTURE-DIAGRAM.txt
**Type:** Visual Reference
**Length:** 17 KB
**Audience:** Everyone

**Contains:**
- ASCII 4-layer architecture diagram
- Signal producer layer
- Central locus aggregator
- Output publishers
- Consumer layer
- Complete data flow example
- Convergence calculation walkthrough

**Read this for:** Visual understanding of the system. Print-friendly ASCII art.

---

### 5. LOCUS-QUICK-REFERENCE.md
**Type:** One-Page Cheat Sheet
**Length:** 7 KB | 6 pages
**Audience:** Quick lookup

**Contains:**
- Problem & solution
- The system (one diagram)
- What each strategy publishes
- What the locus calculates
- What the locus publishes
- Integration steps
- FAQ & troubleshooting
- Key insights

**Read this for:** Quick answers. Print it out. Pin it to your desk.

---

### 6. LOCUS-INDEX.md
**Type:** Navigation Guide
**Length:** This file
**Audience:** Everyone

**Contains:**
- File index with purposes
- Reading order recommendations
- Quick navigation by role
- Key concepts summary

**Read this for:** Finding what you need.

---

## Code Index

### 1. signal_packet.py
**Location:** `/tools/signal_packet.py`
**Lines:** 280
**Type:** Data Structure

**Contains:**
- `SignalPacket` class (canonical format)
- Data classes:
  - `MarketView` (confidence, direction, strength, liquidity, volatility)
  - `PositionRecommendation` (action, size, entry, return, probability)
  - `PerformanceContext` (accuracy, sharpe, drawdown, days_active, trades)
  - `RiskAssessment` (edge_conf, model_conf, execution_risk, regime, anomaly)
  - `Metadata` (version, uptime, signal_drift, pending_orders, utilization)
- Enums:
  - `Direction` (UP, DOWN, NEUTRAL)
  - `ExecutionRisk` (LOW, MEDIUM, HIGH)
- Methods:
  - `to_dict()` - Serialize to dict
  - `to_json()` - Serialize to JSON string
  - `from_dict()` - Deserialize from dict

**Import it:**
```python
from signal_packet import SignalPacket, Direction, ExecutionRisk
```

**Use it:**
```python
signal = SignalPacket(
    strategy="my_strategy",
    confidence=0.87,
    direction=Direction.UP,
    # ... other fields
)
```

---

### 2. central_locus.py
**Location:** `/mcp-servers/nats-bridge/central_locus.py`
**Lines:** 620
**Type:** Main Application

**Contains:**
- `StrategySignal` dataclass (parsed signal with metadata)
- `ConvergenceAnalysis` dataclass (result of scoring)
- `CentralLocus` class:
  - Signal buffer management
  - Signal parsing
  - Convergence calculation
  - Allocation generation
  - NATS integration
  - Readout publishing
  - State persistence

**Main methods:**
- `connect()` - Connect to NATS
- `subscribe_to_strategies(strategies)` - Subscribe to signal channels
- `calculate_readout()` - Generate complete aggregated readout
- `publish_readout(readout)` - Publish to NATS
- `run_loop(strategies, interval)` - Main event loop

**Run it:**
```bash
python central_locus.py --mode run \
  --strategies latency_arb cross_platform_arb high_prob_bonding
```

---

### 3. locus_readout_formatter.py
**Location:** `/mcp-servers/nats-bridge/locus_readout_formatter.py`
**Lines:** 220
**Type:** Output Formatter

**Contains:**
- `LocusReadoutFormatter` class with methods:
  - `to_cli_summary()` - Beautiful CLI output
  - `to_csv_row()` - CSV logging format
  - `to_web_json()` - Web dashboard format
  - `to_machine_command()` - Actionable command
  - `to_convergence_chart()` - ASCII trend chart

**Use it:**
```python
from locus_readout_formatter import LocusReadoutFormatter

formatter = LocusReadoutFormatter(readout_json)
print(formatter.to_cli_summary())
```

---

## Quick Navigation by Role

### I'm a System Architect
1. Read: **ADR-CENTRAL-LOCUS.md** (why we chose this)
2. Read: **CENTRAL-LOCUS-SPECIFICATION.md** (full design)
3. Skim: **LOCUS-ARCHITECTURE-DIAGRAM.txt** (visual confirmation)

### I'm a Strategy Developer
1. Read: **LOCUS-QUICK-REFERENCE.md** (overview)
2. Read: **LOCUS-INTEGRATION-GUIDE.md** (how to integrate)
3. Reference: **signal_packet.py** (field definitions)

### I'm an Operations Engineer
1. Read: **LOCUS-QUICK-REFERENCE.md** (overview)
2. Reference: **LOCUS-ARCHITECTURE-DIAGRAM.txt** (system layout)
3. Run: `python central_locus.py --help`

### I'm Learning the System
1. Start: **LOCUS-QUICK-REFERENCE.md** (1-page summary)
2. Deep dive: **LOCUS-ARCHITECTURE-DIAGRAM.txt** (visual flow)
3. Technical: **CENTRAL-LOCUS-SPECIFICATION.md** (full details)

---

## Key Concepts Quick Reference

### Signal Packet
A JSON structure published by each strategy containing:
- Market view (confidence, direction, strength)
- Position recommendation (action, size, entry)
- Performance context (accuracy, sharpe, drawdown)
- Risk assessment (edge_conf, execution_risk, anomaly)
- Metadata (uptime, utilization)

### Convergence Score
A number (0.0-1.0) that measures how much strategies agree:
```
convergence = 0.30 * direction_agreement
            + 0.30 * confidence_agreement
            + 0.25 * signal_strength
            + 0.15 * accuracy_weighting
```

### Allocation Mode
Based on convergence, the locus picks a capital deployment strategy:
- **AGGRESSIVE** (0.85+): 30% more capital
- **BALANCED** (0.70-0.85): Normal allocation
- **CAUTIOUS** (0.55-0.70): 30% less capital
- **DEFENSIVE** (<0.55): 60% less capital

### Central Locus Readout
A JSON object published every 5 seconds containing:
- Market consensus (direction, confidence, convergence_score)
- Strategy alignment (each strategy's contribution)
- Budget allocation (per-strategy capital)
- Execution readiness (ready? confidence?)

---

## Architecture in 30 Seconds

```
STRATEGIES (Publish Signals)
    ↓
    └→ signal: {confidence: 0.87, direction: UP, accuracy: 0.88, ...}

    ↓ (NATS Pub/Sub)

CENTRAL LOCUS (Aggregate)
    ↓
    └→ Read all signals
    ├→ Calculate: convergence_score = 0.78
    ├→ Map: mode = BALANCED
    └→ Allocate: latency_arb=$18500, cross_platform=$14200, ...

    ↓ (NATS Pub/Sub)

OUTPUTS
    ├→ locus.aggregated_readout (JSON)
    └→ locus.budget_allocation (Command)

    ↓

ALLOCATOR (Execute)
    └→ Deploy capital according to allocation command
```

---

## Implementation Timeline

**Phase 1 (COMPLETE):** Specification
- Design convergence algorithm
- Define signal schema
- Create integration guide
- **Status:** ✓ Done (this document set)

**Phase 2 (NEXT):** Integration
- Add signal publishing to strategies
- Test with mock signals
- Validate convergence calculation
- **Timeline:** 1-2 weeks

**Phase 3:** Optimization
- Tune convergence weights
- Add anomaly detection
- Implement risk controls
- **Timeline:** 1-2 weeks

**Phase 4:** Scaling & Production
- Support 10+ strategies
- Add web dashboard
- Production hardening
- **Timeline:** 2-4 weeks

---

## File Locations Summary

```
Documentation:
  /BRAIN/INTEL/CENTRAL-LOCUS-SPECIFICATION.md
  /BRAIN/INTEL/LOCUS-INTEGRATION-GUIDE.md
  /BRAIN/INTEL/ADR-CENTRAL-LOCUS.md
  /BRAIN/INTEL/LOCUS-ARCHITECTURE-DIAGRAM.txt
  /BRAIN/INTEL/LOCUS-QUICK-REFERENCE.md
  /BRAIN/INTEL/LOCUS-INDEX.md (this file)

Code:
  /tools/signal_packet.py
  /mcp-servers/nats-bridge/central_locus.py
  /mcp-servers/nats-bridge/locus_readout_formatter.py
```

---

## Getting Started Checklist

- [ ] Read LOCUS-QUICK-REFERENCE.md (5 min)
- [ ] Review LOCUS-ARCHITECTURE-DIAGRAM.txt (5 min)
- [ ] Read LOCUS-INTEGRATION-GUIDE.md (15 min)
- [ ] Review signal_packet.py fields (10 min)
- [ ] Add signal publishing to your strategy (varies)
- [ ] Run central_locus.py in test mode (5 min)
- [ ] Verify signals flowing (1 min)
- [ ] Read CENTRAL-LOCUS-SPECIFICATION.md for deep dive (30 min)
- [ ] Run in production (varies)

---

## Support & Questions

For questions about:
- **What is the system?** → LOCUS-QUICK-REFERENCE.md
- **How do I integrate?** → LOCUS-INTEGRATION-GUIDE.md
- **Why was it designed this way?** → ADR-CENTRAL-LOCUS.md
- **How does it work technically?** → CENTRAL-LOCUS-SPECIFICATION.md
- **What does the code do?** → signal_packet.py, central_locus.py
- **Visual overview?** → LOCUS-ARCHITECTURE-DIAGRAM.txt

---

## Key Files at a Glance

| File | Size | Purpose | Read Time |
|------|------|---------|-----------|
| LOCUS-QUICK-REFERENCE.md | 7K | Overview & checklist | 5 min |
| LOCUS-INTEGRATION-GUIDE.md | 10K | How to integrate | 15 min |
| CENTRAL-LOCUS-SPECIFICATION.md | 19K | Full technical spec | 30 min |
| ADR-CENTRAL-LOCUS.md | 14K | Why this design | 20 min |
| LOCUS-ARCHITECTURE-DIAGRAM.txt | 17K | Visual architecture | 10 min |
| signal_packet.py | 10K | Signal data structure | 10 min |
| central_locus.py | 20K | Main aggregator | 20 min |
| locus_readout_formatter.py | 7.6K | Output formatter | 10 min |

**Total:** ~87 KB documentation + code

---

## Version History

| Version | Date | Status |
|---------|------|--------|
| 1.0 | 2026-02-04 | SPECIFICATION COMPLETE |
| - | TBD | Phase 2: Integration |
| - | TBD | Phase 3: Optimization |
| - | TBD | Phase 4: Production |

---

**ECHO (SHARE)**

*The locus reads what each strategy sees.*
*The field decides together.*

---

Last updated: 2026-02-04
