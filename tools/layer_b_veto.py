#!/usr/bin/env python3
"""
Layer B Veto Algorithm - Trade Decision Gate

Prevents bad trades by enforcing edge-based rules.
No trade passes without documented edge and positive expected value.

Usage:
    python3 layer_b_veto.py --check-trade "[question]" --probability 0.55 --odds-against 1.82
"""

import json
import sys
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from pathlib import Path

# Constants
REPO_ROOT = Path(__file__).parent.parent
VETO_LOG = REPO_ROOT / 'logs' / 'layer_b_veto.log'
VETO_LOG.parent.mkdir(parents=True, exist_ok=True)


class VerdictType(Enum):
    ALLOW = "ALLOW"
    VETO = "VETO"
    CONDITIONAL = "CONDITIONAL"


@dataclass
class CheckResult:
    question: str
    verdict: VerdictType
    score: float
    reason: str
    rules_passed: list
    rules_failed: list
    estimated_ev: float = 0
    position_size: float = 0
    recommendation: str = ""


class LayerBVeto:
    """Trade decision gate enforcing edge-based rules"""

    def __init__(self):
        self.min_edge_confidence = 0.55
        self.min_domain_hours = 1000
        self.max_position_pct = 0.03  # 3% per trade
        self.min_ev_threshold = 0.20  # 20% expected value

    def log(self, msg: str):
        """Log decision to file and stdout"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        line = f"[{timestamp}] {msg}"
        print(line)
        with open(VETO_LOG, 'a') as f:
            f.write(line + '\n')

    def check_trade(
        self,
        question: str,
        probability: float = None,
        domain: str = None,
        domain_hours: int = 0,
        has_edge_rationale: bool = False,
        edge_description: str = "",
        odds_against: float = None,
        win_amount: float = None,
        loss_amount: float = None,
        capital: float = 1464
    ) -> CheckResult:
        """
        Comprehensive trade veto check

        Args:
            question: The trade proposition
            probability: Your estimated win probability (0-1)
            domain: Domain of the bet (e.g., "weather", "league-of-legends")
            domain_hours: Hours of experience in domain
            has_edge_rationale: Whether you have an edge explanation
            edge_description: Explanation of the edge
            odds_against: Market odds against (e.g., 2.5 means 2.5:1 against)
            win_amount: Dollar amount won if right
            loss_amount: Dollar amount lost if wrong
            capital: Total available capital

        Returns:
            CheckResult with verdict and scoring
        """

        rules_passed = []
        rules_failed = []
        score = 0
        estimated_ev = 0

        # Rule 1: Edge existence test
        rule1_pass = has_edge_rationale and edge_description and len(edge_description) > 5
        if rule1_pass:
            rules_passed.append("Rule 1: Has documented edge rationale")
            score += 20
        else:
            rules_failed.append("Rule 1: No edge documented (must answer 'Why do I know this?')")

        # Rule 2: Domain specificity test
        allowed_domains = [
            "weather",
            "league-of-legends",
            "esports",
            "political-polling",
            "crypto-arbitrage",
            "copy-trading",
            "technical-analysis",
            "scientific-data"
        ]
        banned_domains = [
            "entertainment",
            "movies",
            "awards",
            "music",
            "general-culture"
        ]

        rule2_pass = domain and domain in allowed_domains
        if rule2_pass:
            rules_passed.append(f"Rule 2: Valid domain ({domain})")
            score += 15
        elif domain and domain in banned_domains:
            rules_failed.append(f"Rule 2: BANNED domain ({domain})")
        else:
            rules_failed.append("Rule 2: Domain not specified or too generic")

        # Rule 3: Information asymmetry test
        rule3_pass = bool(edge_description and (
            "data" in edge_description.lower() or
            "hours" in edge_description.lower() or
            "experience" in edge_description.lower() or
            "proprietary" in edge_description.lower()
        ))
        if rule3_pass:
            rules_passed.append("Rule 3: Has information advantage identified")
            score += 15
        else:
            rules_failed.append("Rule 3: No documented information advantage")

        # Rule 4: Minimum domain expertise
        rule4_pass = domain_hours >= self.min_domain_hours
        if rule4_pass:
            rules_passed.append(f"Rule 4: Sufficient domain expertise ({domain_hours} hours)")
            score += 15
        elif domain_hours > 0:
            rules_failed.append(f"Rule 4: Insufficient domain hours ({domain_hours}/{self.min_domain_hours})")
        else:
            rules_failed.append("Rule 4: No domain expertise documented")

        # Rule 5: Probability threshold
        rule5_pass = probability and probability >= self.min_edge_confidence
        if rule5_pass:
            rules_passed.append(f"Rule 5: Sufficient confidence ({probability*100:.1f}%)")
            score += 10
        elif probability:
            rules_failed.append(f"Rule 5: Low probability ({probability*100:.1f}% < {self.min_edge_confidence*100:.0f}%)")
        else:
            rules_failed.append("Rule 5: Probability not estimated")

        # Rule 6: Expected Value calculation
        if probability and win_amount and loss_amount:
            ev = (probability * win_amount) - ((1 - probability) * loss_amount)
            ev_pct = ev / loss_amount if loss_amount > 0 else 0
            estimated_ev = ev_pct

            rule6_pass = estimated_ev >= self.min_ev_threshold
            if rule6_pass:
                rules_passed.append(f"Rule 6: Positive EV ({estimated_ev*100:.1f}%)")
                score += 10
            else:
                rules_failed.append(f"Rule 6: Insufficient EV ({estimated_ev*100:.1f}% < {self.min_ev_threshold*100:.0f}%)")
        else:
            rules_failed.append("Rule 6: Cannot calculate EV (need probability + amounts)")

        # Rule 7: Position sizing (Kelly Criterion)
        position_size = 0
        if probability and odds_against:
            # Kelly: f = (bp - q) / b
            b = odds_against
            p = probability
            q = 1 - probability
            kelly_f = ((b * p) - q) / b
            half_kelly = kelly_f / 2
            position_size = half_kelly * capital
            position_pct = position_size / capital

            rule7_pass = position_pct <= self.max_position_pct
            if rule7_pass:
                rules_passed.append(f"Rule 7: Safe position size ({position_pct*100:.2f}%)")
                score += 10
            else:
                rules_failed.append(f"Rule 7: Position too large ({position_pct*100:.2f}% > {self.max_position_pct*100:.1f}%)")

        # Rule 8: No extreme odds without massive edge
        rule8_pass = True
        if probability and probability < 0.05:  # <5% odds
            if estimated_ev < 1.0:  # Need 100%+ EV for low odds
                rule8_pass = False
                rules_failed.append("Rule 8: Too-low odds without 100%+ EV")
            else:
                rules_passed.append("Rule 8: Low odds justified by EV")
                score += 5
        else:
            rules_passed.append("Rule 8: Not extreme long odds")
            score += 5

        # Rule 9: No banned categories
        banned_patterns = [
            "price will",
            "stock will",
            "cost will",
            "movie",
            "film",
            "award",
            "cocaine",
            "will it snow"  # Generic weather - need specificity
        ]

        rule9_pass = not any(pattern in question.lower() for pattern in banned_patterns)
        if rule9_pass:
            rules_passed.append("Rule 9: Not in banned category")
            score += 5
        else:
            rules_failed.append("Rule 9: Matches banned pattern (likely no edge)")

        # Rule 10: Repeatability
        rule10_pass = domain and domain in ["weather", "league-of-legends", "esports", "copy-trading", "crypto-arbitrage"]
        if rule10_pass:
            rules_passed.append("Rule 10: Domain allows repeated execution")
            score += 5
        else:
            rules_failed.append("Rule 10: One-time opportunity (no repeatability)")

        # Final verdict
        if score >= 70:
            verdict = VerdictType.ALLOW
            recommendation = f"ALLOW - Position size: ${position_size:.2f} ({position_size/capital*100:.2f}% of capital)"
        elif score >= 50:
            verdict = VerdictType.CONDITIONAL
            recommendation = f"CONDITIONAL - Fix {len(rules_failed)} issues before trading"
        else:
            verdict = VerdictType.VETO
            recommendation = f"VETO - Too many rule violations ({len(rules_failed)}/{10} rules)"

        result = CheckResult(
            question=question,
            verdict=verdict,
            score=score,
            reason=recommendation,
            rules_passed=rules_passed,
            rules_failed=rules_failed,
            estimated_ev=estimated_ev,
            position_size=position_size,
            recommendation=recommendation
        )

        return result

    def format_result(self, result: CheckResult) -> str:
        """Format result for human reading"""
        output = []
        output.append("")
        output.append("=" * 70)
        output.append(f"TRADE VETO CHECK: {result.question[:60]}")
        output.append("=" * 70)
        output.append("")

        # Score
        output.append(f"VERDICT: {result.verdict.value} (Score: {result.score}/100)")
        output.append(f"Recommendation: {result.recommendation}")
        output.append("")

        # Passed rules
        if result.rules_passed:
            output.append("✅ PASSED:")
            for rule in result.rules_passed:
                output.append(f"  {rule}")
            output.append("")

        # Failed rules
        if result.rules_failed:
            output.append("❌ FAILED:")
            for rule in result.rules_failed:
                output.append(f"  {rule}")
            output.append("")

        # EV and position
        if result.estimated_ev != 0:
            output.append(f"Expected Value: {result.estimated_ev*100:.1f}%")
        if result.position_size > 0:
            output.append(f"Recommended Position: ${result.position_size:.2f}")
        output.append("")
        output.append("=" * 70)

        return "\n".join(output)

    def save_decision(self, result: CheckResult, capital: float):
        """Save decision to log"""
        decision_log = {
            "timestamp": datetime.now().isoformat(),
            "question": result.question,
            "verdict": result.verdict.value,
            "score": result.score,
            "capital": capital,
            "estimated_position": result.position_size,
            "estimated_ev": result.estimated_ev,
            "rules_passed": len(result.rules_passed),
            "rules_failed": len(result.rules_failed)
        }

        log_file = REPO_ROOT / 'logs' / 'layer_b_decisions.jsonl'
        log_file.parent.mkdir(parents=True, exist_ok=True)

        with open(log_file, 'a') as f:
            f.write(json.dumps(decision_log) + '\n')


def main():
    """CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Layer B Veto - Trade Decision Gate"
    )
    parser.add_argument("--check-trade", type=str, help="Trade question to evaluate")
    parser.add_argument("--probability", type=float, help="Win probability (0-1)")
    parser.add_argument("--domain", type=str, help="Domain (weather, league-of-legends, etc)")
    parser.add_argument("--domain-hours", type=int, default=0, help="Hours of domain expertise")
    parser.add_argument("--edge", type=str, help="Edge description")
    parser.add_argument("--odds-against", type=float, help="Market odds against (e.g., 2.5)")
    parser.add_argument("--win-amount", type=float, help="Dollar amount if correct")
    parser.add_argument("--loss-amount", type=float, help="Dollar amount if wrong")
    parser.add_argument("--capital", type=float, default=1464, help="Total capital available")

    args = parser.parse_args()

    if not args.check_trade:
        print("Usage: python3 layer_b_veto.py --check-trade '[question]' --probability 0.55 [other options]")
        sys.exit(1)

    veto = LayerBVeto()
    result = veto.check_trade(
        question=args.check_trade,
        probability=args.probability,
        domain=args.domain,
        domain_hours=args.domain_hours,
        has_edge_rationale=bool(args.edge),
        edge_description=args.edge or "",
        odds_against=args.odds_against,
        win_amount=args.win_amount,
        loss_amount=args.loss_amount,
        capital=args.capital
    )

    output = veto.format_result(result)
    print(output)

    veto.save_decision(result, args.capital)
    veto.log(f"Trade check: {args.check_trade[:50]} → {result.verdict.value}")

    # Exit code based on verdict
    sys.exit(0 if result.verdict == VerdictType.ALLOW else 1)


if __name__ == "__main__":
    main()
