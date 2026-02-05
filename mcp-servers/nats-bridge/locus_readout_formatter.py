#!/usr/bin/env python3
"""
LOCUS READOUT FORMATTER

Converts Central Locus readout JSON into:
1. Human-readable CLI output
2. Web dashboard format
3. Machine-actionable commands

The same data, three different lenses.
"""

import json
from datetime import datetime
from typing import Dict, Any
from pathlib import Path


class LocusReadoutFormatter:
    """Format Central Locus readout for different audiences"""

    def __init__(self, readout: Dict[str, Any]):
        self.readout = readout

    def to_cli_summary(self) -> str:
        """Generate beautiful CLI-friendly summary"""
        r = self.readout

        # Extract key data
        consensus = r.get("market_consensus", {})
        direction = consensus.get("direction", "?")
        confidence = consensus.get("confidence", 0)
        convergence = consensus.get("convergence_score", 0)
        conv_level = consensus.get("convergence_level", "?")

        strategies = r.get("strategy_alignment", {})
        allocation = r.get("budget_allocation", {})
        allocs = allocation.get("allocations", {})
        ready = r.get("execution_readiness", {})

        # Build output
        output = []
        output.append("")
        output.append("═" * 70)
        output.append("CENTRAL LOCUS READOUT - Epoch {} ({} UTC)".format(
            r.get("epoch", "?"),
            r.get("timestamp", "?")[:10]
        ))
        output.append("═" * 70)
        output.append("")

        # Market consensus
        direction_symbol = {"UP": "↑", "DOWN": "↓", "NEUTRAL": "↔"}[direction]
        output.append(f"🎯 MARKET CONSENSUS")
        output.append(f"   Direction: {direction_symbol} {direction} ({confidence:.0%} confident)")
        output.append(f"   Strength: {consensus.get('strength', 0):.0%} | Convergence: {convergence:.0%} ({conv_level})")
        output.append("")

        # Strategy alignment
        output.append("📊 STRATEGY ALIGNMENT")
        for strat, data in sorted(strategies.items()):
            strat_dir = data.get("direction", "?")
            strat_conf = data.get("confidence", 0)
            strat_acc = data.get("accuracy", 0)
            alignment = data.get("alignment", 0)
            expected = data.get("expected_return", 0)

            dir_sym = {"UP": "→", "DOWN": "←", "NEUTRAL": "↔"}[strat_dir]
            align_bar = "█" * int(alignment * 10) + "░" * (10 - int(alignment * 10))

            output.append(
                f"   {strat:20} {dir_sym}{strat_dir:7} ({strat_conf:.0%}) "
                f"| Aligned: {align_bar} {alignment:.0%} | Expected: +{expected:.1f}%"
            )
        output.append("")

        # Aggregate metrics
        metrics = r.get("aggregate_metrics", {})
        output.append("📈 AGGREGATE METRICS")
        output.append(f"   Mean Confidence: {metrics.get('mean_confidence', 0):.0%} "
                     f"| Std Dev: {metrics.get('confidence_std_dev', 0):.2f}")
        output.append(f"   Mean Accuracy: {metrics.get('mean_accuracy', 0):.0%} "
                     f"| Mean Sharpe: {metrics.get('mean_sharpe', 0):.2f}x")
        output.append(f"   System Uptime: {metrics.get('uptime_pct', 0):.1f}%")
        output.append("")

        # Budget allocation
        total_capital = allocation.get("total_capital", 0)
        output.append("💰 BUDGET ALLOCATION (Total: ${:,.0f})".format(total_capital))
        for strat, alloc_data in sorted(allocs.items()):
            cap = alloc_data.get("capital", 0)
            pct = alloc_data.get("pct", 0)
            conf = alloc_data.get("confidence", 0)
            ret = alloc_data.get("expected_return", 0)
            util = alloc_data.get("utilization", 0)

            bar_len = int(pct * 50)
            bar = "█" * bar_len + "░" * (50 - bar_len)

            output.append(
                f"   {strat:20} {bar} {pct:5.0%} (${cap:>8,.0f}) "
                f"| Conf: {conf:.0%} | Ret: +{ret:.1f}% | Util: {util:.0%}"
            )
        output.append("")

        # Execution readiness
        output.append("⚡ EXECUTION READINESS")
        signals_fresh = "✓" if ready.get("all_signals_fresh") else "✗"
        ready_exec = "READY ✓" if ready.get("ready_for_execution") else "NOT READY ✗"
        output.append(f"   Signals Fresh: {signals_fresh} | Ready: {ready_exec}")
        output.append(f"   Signal Age: {ready.get('min_signal_age_sec', 0):.1f}s - "
                     f"{ready.get('max_signal_age_sec', 0):.1f}s")
        output.append(f"   Execution Confidence: {ready.get('execution_confidence', 0):.0%}")
        output.append("")

        output.append("═" * 70)
        output.append("")

        return "\n".join(output)

    def to_csv_row(self) -> str:
        """Generate CSV row for logging"""
        r = self.readout

        consensus = r.get("market_consensus", {})
        exec_ready = r.get("execution_readiness", {})
        metrics = r.get("aggregate_metrics", {})

        # CSV format: timestamp,epoch,direction,convergence,confidence,ready,uptime
        return "{},{},{},{:.2f},{:.2f},{},{}".format(
            r.get("timestamp", ""),
            r.get("epoch", ""),
            consensus.get("direction", "?"),
            consensus.get("convergence_score", 0),
            consensus.get("confidence", 0),
            int(exec_ready.get("ready_for_execution", False)),
            metrics.get("uptime_pct", 0),
        )

    def to_web_json(self) -> Dict:
        """Convert to web dashboard format"""
        return self.readout  # Already in good format

    def to_machine_command(self) -> Dict:
        """Generate machine-actionable command"""
        r = self.readout
        allocation = r.get("budget_allocation", {})

        return {
            "command": "REALLOCATE_CAPITAL",
            "allocations": {
                strat: data["capital"]
                for strat, data in allocation.get("allocations", {}).items()
            },
            "metadata": {
                "convergence_score": r.get("market_consensus", {}).get("convergence_score"),
                "convergence_level": r.get("market_consensus", {}).get("convergence_level"),
                "epoch": r.get("epoch"),
                "timestamp": r.get("timestamp"),
                "execution_confidence": r.get("execution_readiness", {}).get("execution_confidence"),
                "ready_for_execution": r.get("execution_readiness", {}).get("ready_for_execution"),
            },
        }

    def to_convergence_chart(self, history: list) -> str:
        """ASCII chart of convergence trend"""
        if not history:
            return "No history"

        # Last 50 epochs
        recent = history[-50:] if len(history) > 50 else history
        scores = [r.get("convergence_score", 0) for r in recent]

        # Scale to 0-10
        max_score = max(scores) if scores else 1.0
        scaled = [int((s / max_score) * 10) for s in scores]

        chart = []
        chart.append("Convergence Trend (Last {} epochs)".format(len(recent)))
        chart.append("")

        # Bars
        for i, val in enumerate(scaled):
            bar = "█" * val + "░" * (10 - val)
            score_pct = recent[i].get("convergence_score", 0)
            chart.append(f"  {bar} {score_pct:.0%}")

        return "\n".join(chart)


def format_readout_file(readout_path: str) -> str:
    """Load and format a readout file"""
    with open(readout_path) as f:
        readout = json.load(f)

    formatter = LocusReadoutFormatter(readout)
    return formatter.to_cli_summary()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python locus_readout_formatter.py <readout.json>")
        sys.exit(1)

    readout_file = sys.argv[1]
    print(format_readout_file(readout_file))
