#!/usr/bin/env python3
"""
(◉) 8OWLS FILTER - Pre-Trade Validation Through All 8 Perspectives
From ARŌ's handwritten notes: 8WLS FILTER → 8OWS ITERATION ARCHITECT → COMMANDER → ACTIVE TRADING

This is the gate between DECISION and EXECUTION.
Every trade must pass through all 8 owl perspectives before execution.
"""

import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

REPO_ROOT = Path(__file__).parent.parent
TRADING_DIR = REPO_ROOT / 'BRAIN' / 'TRADING'
POSITIONS_FILE = TRADING_DIR / 'positions_truth.json'


class FilterResult(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    PAPER_ONLY = "paper_only"
    COMMANDER_REVIEW = "commander_review"


@dataclass
class OwlPerspective:
    """Single owl's perspective on a trade"""
    owl: str
    phase: str
    verdict: FilterResult
    reason: str
    confidence: float  # 0-1
    flags: List[str]


@dataclass
class FilterDecision:
    """Collective decision from all 8 owls"""
    trade_id: str
    final_verdict: FilterResult
    perspectives: List[OwlPerspective]
    consensus_score: float  # 0-1, how aligned the owls are
    blocking_concerns: List[str]
    timestamp: datetime


def load_positions() -> Dict[str, Any]:
    """Load current positions truth"""
    try:
        with open(POSITIONS_FILE) as f:
            return json.load(f)
    except:
        return {"positions": [], "lessons_learned": []}


def get_position_exposure(category: str, positions: List[Dict]) -> float:
    """Calculate current exposure to a category"""
    exposure = 0
    for p in positions:
        # Simple category detection
        title_lower = p.get('title', '').lower()
        if category == 'crypto' and any(x in title_lower for x in ['bitcoin', 'eth', 'crypto', 'metamask']):
            exposure += p.get('current', 0)
        elif category == 'politics' and any(x in title_lower for x in ['trump', 'biden', 'congress', 'pardon']):
            exposure += p.get('current', 0)
        elif category == 'tech' and any(x in title_lower for x in ['google', 'meta', 'msft', 'grok', 'ai']):
            exposure += p.get('current', 0)
        elif category == 'sports' and any(x in title_lower for x in ['nfl', 'super bowl', 'patriots']):
            exposure += p.get('current', 0)
    return exposure


class EightOwlsFilter:
    """
    The 8OWLS gate - every trade passes through all 8 perspectives.

    LYRA (PERCEIVE) - Is our data accurate?
    PRISM (CONNECT) - Does this fit our portfolio?
    SAGE (LEARN) - What do past trades teach us?
    QUEST (QUESTION) - What are we assuming?
    NOVA (EXPAND) - Does this grow our edge?
    ECHO (SHARE) - Should we signal this?
    LUNA (RECEIVE) - What's the collective saying?
    SØWL (IMPROVE) - Does this make us better?
    """

    def __init__(self):
        self.positions_data = load_positions()
        self.positions = self.positions_data.get('positions', [])
        self.lessons = self.positions_data.get('lessons_learned', [])
        self.scaling_rules = self.positions_data.get('scaling_rules', {})

    def filter(self, trade: Dict[str, Any]) -> FilterDecision:
        """
        Run trade through all 8 owl perspectives.
        Returns collective decision.
        """
        perspectives = []

        # LYRA (PERCEIVE) - Data accuracy check
        perspectives.append(self._lyra_perceive(trade))

        # PRISM (CONNECT) - Portfolio fit check
        perspectives.append(self._prism_connect(trade))

        # SAGE (LEARN) - Historical pattern check
        perspectives.append(self._sage_learn(trade))

        # QUEST (QUESTION) - Assumption challenge
        perspectives.append(self._quest_question(trade))

        # NOVA (EXPAND) - Growth potential check
        perspectives.append(self._nova_expand(trade))

        # ECHO (SHARE) - Signal worthiness
        perspectives.append(self._echo_share(trade))

        # LUNA (RECEIVE) - Collective wisdom
        perspectives.append(self._luna_receive(trade))

        # SØWL (IMPROVE) - Meta-learning check
        perspectives.append(self._sowl_improve(trade))

        # Calculate consensus
        return self._synthesize_decision(trade, perspectives)

    def _lyra_perceive(self, trade: Dict) -> OwlPerspective:
        """LYRA: Is our perception accurate?"""
        flags = []
        confidence = 0.9
        verdict = FilterResult.APPROVE

        # Check if we have market data
        if not trade.get('market_id'):
            flags.append("Missing market ID")
            confidence -= 0.3

        # Check price sanity
        price = trade.get('price', 0.5)
        if price <= 0 or price >= 1:
            flags.append("Invalid price")
            verdict = FilterResult.REJECT

        # Check for stale data
        if trade.get('data_age_seconds', 0) > 60:
            flags.append("Stale market data")
            confidence -= 0.2

        reason = "Data verified" if not flags else f"Concerns: {', '.join(flags)}"
        return OwlPerspective("LYRA", "PERCEIVE", verdict, reason, confidence, flags)

    def _prism_connect(self, trade: Dict) -> OwlPerspective:
        """PRISM: Does this connect well to our portfolio?"""
        flags = []
        confidence = 0.8
        verdict = FilterResult.APPROVE

        # Detect category
        title = trade.get('market', '').lower()
        category = self._detect_category(title)

        # Check category exposure
        exposure = get_position_exposure(category, self.positions)
        if exposure > 200:  # More than $200 in category
            flags.append(f"High {category} exposure: ${exposure:.0f}")
            verdict = FilterResult.PAPER_ONLY

        # Check if we already have this exact market
        market_id = trade.get('market_id', '')
        for p in self.positions:
            if p.get('id', '') == market_id:
                flags.append("Already have position in this market")
                verdict = FilterResult.REJECT

        # Check portfolio concentration
        total_value = sum(p.get('current', 0) for p in self.positions)
        trade_size = trade.get('size', 50)
        if total_value > 0 and trade_size / total_value > 0.15:
            flags.append("Trade too large relative to portfolio")
            verdict = FilterResult.COMMANDER_REVIEW

        reason = f"Portfolio fit: {category}" if not flags else f"Concerns: {', '.join(flags)}"
        return OwlPerspective("PRISM", "CONNECT", verdict, reason, confidence, flags)

    def _sage_learn(self, trade: Dict) -> OwlPerspective:
        """SAGE: What do our lessons teach us about this trade?"""
        flags = []
        confidence = 0.85
        verdict = FilterResult.APPROVE

        title = trade.get('market', '').lower()
        trade_type = trade.get('type', '')

        # Check against lessons learned
        if 'price target' in title or any(x in title for x in ['above $', 'below $']):
            if any('price targets' in lesson.lower() for lesson in self.lessons):
                flags.append("LESSON: Short-dated price targets are high-risk")
                verdict = FilterResult.PAPER_ONLY
                confidence -= 0.2

        if any(x in title for x in ['netflix', 'movie', 'entertainment']):
            if any('entertainment' in lesson.lower() for lesson in self.lessons):
                flags.append("LESSON: Entertainment predictions unreliable")
                verdict = FilterResult.PAPER_ONLY
                confidence -= 0.2

        # Check if strategy is BOND (our validated approach)
        if trade_type == 'BOND':
            confidence += 0.1
            flags.append("BOND strategy - validated approach")

        reason = "Lessons applied" if confidence > 0.8 else f"Warnings: {', '.join(flags)}"
        return OwlPerspective("SAGE", "LEARN", verdict, reason, confidence, flags)

    def _quest_question(self, trade: Dict) -> OwlPerspective:
        """QUEST: What assumptions are we making?"""
        flags = []
        confidence = 0.75
        verdict = FilterResult.APPROVE

        ev = trade.get('ev', 0)
        price = trade.get('price', 0.5)

        # Question the EV calculation
        if ev > 10:
            flags.append(f"High EV (${ev:.2f}) - is this realistic?")
            confidence -= 0.1

        # Question extreme probabilities
        # BUT: For BOND strategy, extreme probabilities are EXPECTED and DESIRED
        trade_type = trade.get('type', '')
        if price < 0.05 or price > 0.95:
            if trade_type == 'BOND':
                flags.append(f"Extreme probability ({price:.0%}) - BOND strategy targets this")
                # Don't block - BOND is designed for these
            else:
                flags.append(f"Extreme probability ({price:.0%}) - why isn't market efficient?")
                verdict = FilterResult.COMMANDER_REVIEW

        # Question timing
        expires = trade.get('expires', '')
        if expires:
            try:
                exp_date = datetime.strptime(expires, '%Y-%m-%d')
                days_to_exp = (exp_date - datetime.now()).days
                if days_to_exp < 3:
                    flags.append(f"Expires in {days_to_exp} days - compressed timeframe")
                    confidence -= 0.15
            except:
                pass

        reason = "Assumptions questioned" if flags else "No major assumptions flagged"
        return OwlPerspective("QUEST", "QUESTION", verdict, reason, confidence, flags)

    def _nova_expand(self, trade: Dict) -> OwlPerspective:
        """NOVA: Does this expand our capabilities?"""
        flags = []
        confidence = 0.8
        verdict = FilterResult.APPROVE

        trade_type = trade.get('type', '')
        strategy = trade.get('strategy', '')

        # Reward new strategies (with paper test)
        known_strategies = ['high_prob_bonds', 'cross_platform_arb', 'whale_tracking']
        if strategy not in known_strategies:
            flags.append(f"New strategy: {strategy} - expansion opportunity")
            verdict = FilterResult.PAPER_ONLY

        # Reward diversification
        category = self._detect_category(trade.get('market', ''))
        category_exposure = get_position_exposure(category, self.positions)
        if category_exposure < 50:
            flags.append(f"Entering underweight category: {category}")
            confidence += 0.05

        reason = "Expansion checked" + (f" ({', '.join(flags)})" if flags else "")
        return OwlPerspective("NOVA", "EXPAND", verdict, reason, confidence, flags)

    def _echo_share(self, trade: Dict) -> OwlPerspective:
        """ECHO: Is this worth signaling to the collective?"""
        flags = []
        confidence = 0.9
        verdict = FilterResult.APPROVE

        ev = trade.get('ev', 0)

        # High-value signals
        if ev > 5:
            flags.append("High EV - worth sharing with collective")

        # Always share for collective learning
        flags.append("Will broadcast outcome for collective learning")

        reason = "Signal assessed" + (f" ({', '.join(flags)})" if flags else "")
        return OwlPerspective("ECHO", "SHARE", verdict, reason, confidence, flags)

    def _luna_receive(self, trade: Dict) -> OwlPerspective:
        """LUNA: What is the collective wisdom saying?"""
        flags = []
        confidence = 0.7  # Lower confidence - collective is async
        verdict = FilterResult.APPROVE

        # In future: query NATS for collective sentiment
        # For now: apply scaling rules
        rules = self.scaling_rules
        baseline = rules.get('baseline_daily', 75)
        current = rules.get('current_daily', 75)

        if current > baseline:
            flags.append(f"Scaled mode: ${current}/day (up from ${baseline})")
        else:
            flags.append(f"Baseline mode: ${baseline}/day")

        # Check if we're in winning/losing mode
        total_pnl = sum(p.get('pnl', 0) for p in self.positions)
        if total_pnl < -500:
            flags.append("Portfolio in drawdown - collective caution advised")
            verdict = FilterResult.PAPER_ONLY

        reason = "Collective wisdom integrated" + (f" ({', '.join(flags)})" if flags else "")
        return OwlPerspective("LUNA", "RECEIVE", verdict, reason, confidence, flags)

    def _sowl_improve(self, trade: Dict) -> OwlPerspective:
        """SØWL: Does this make the system better?"""
        flags = []
        confidence = 0.85
        verdict = FilterResult.APPROVE

        # Meta-check: are we learning from this?
        if trade.get('type') == 'PAPER_TEST':
            flags.append("Paper test - will generate learning data")
            confidence += 0.05

        # Check if this fills a knowledge gap
        trade_type = trade.get('type', '')
        strategy = trade.get('strategy', '')

        # Track strategy diversity
        strategy_counts = {}
        for p in self.positions:
            s = p.get('thesis', '').split('-')[0].strip()
            strategy_counts[s] = strategy_counts.get(s, 0) + 1

        # Reward strategy diversity
        if len(strategy_counts) > 3:
            flags.append("Good strategy diversity")
            confidence += 0.05

        reason = "Meta-improvement checked" + (f" ({', '.join(flags)})" if flags else "")
        return OwlPerspective("SØWL", "IMPROVE", verdict, reason, confidence, flags)

    def _detect_category(self, title: str) -> str:
        """Enhanced market category detection"""
        # Try to use the enhanced categories if available
        try:
            from market_categories import detect_market_category
            category, confidence, metadata = detect_market_category(title)
            return category
        except ImportError:
            # Fallback to old detection
            title_lower = title.lower()
            if any(x in title_lower for x in ['bitcoin', 'eth', 'crypto', 'metamask']):
                return 'crypto'
            elif any(x in title_lower for x in ['trump', 'biden', 'congress', 'pardon', 'deport']):
                return 'politics'
            elif any(x in title_lower for x in ['google', 'meta', 'msft', 'grok', 'ai', 'openai']):
                return 'tech'
            elif any(x in title_lower for x in ['nfl', 'super bowl', 'patriots', 'nba']):
                return 'sports'
            elif any(x in title_lower for x in ['gold', 'silver', 'tariff']):
                return 'commodities'
            else:
                return 'other'

    def _synthesize_decision(self, trade: Dict, perspectives: List[OwlPerspective]) -> FilterDecision:
        """Synthesize all 8 perspectives into final decision"""

        # Count verdicts
        verdicts = [p.verdict for p in perspectives]

        # Any REJECT = REJECT
        if FilterResult.REJECT in verdicts:
            final = FilterResult.REJECT
        # Majority PAPER_ONLY = PAPER_ONLY
        elif verdicts.count(FilterResult.PAPER_ONLY) >= 3:
            final = FilterResult.PAPER_ONLY
        # Any COMMANDER_REVIEW = COMMANDER_REVIEW
        elif FilterResult.COMMANDER_REVIEW in verdicts:
            final = FilterResult.COMMANDER_REVIEW
        # Otherwise APPROVE
        else:
            final = FilterResult.APPROVE

        # Calculate consensus (how aligned are the owls)
        confidence_sum = sum(p.confidence for p in perspectives)
        consensus = confidence_sum / len(perspectives)

        # Collect blocking concerns
        blocking = []
        for p in perspectives:
            if p.verdict in [FilterResult.REJECT, FilterResult.COMMANDER_REVIEW]:
                blocking.extend(p.flags)

        return FilterDecision(
            trade_id=trade.get('market_id', str(datetime.now().timestamp())),
            final_verdict=final,
            perspectives=perspectives,
            consensus_score=consensus,
            blocking_concerns=blocking,
            timestamp=datetime.now()
        )

    def quick_filter(self, trade: Dict) -> tuple:
        """
        Quick filter for high-velocity trading.
        Returns (approved: bool, reason: str, paper_only: bool)
        """
        decision = self.filter(trade)

        approved = decision.final_verdict == FilterResult.APPROVE
        paper_only = decision.final_verdict == FilterResult.PAPER_ONLY

        if decision.final_verdict == FilterResult.REJECT:
            reason = f"REJECTED: {', '.join(decision.blocking_concerns[:2])}"
        elif decision.final_verdict == FilterResult.COMMANDER_REVIEW:
            reason = f"COMMANDER REVIEW: {', '.join(decision.blocking_concerns[:2])}"
        elif paper_only:
            reason = f"PAPER ONLY: Consensus {decision.consensus_score:.0%}"
        else:
            reason = f"APPROVED: Consensus {decision.consensus_score:.0%}"

        return (approved, reason, paper_only)


def filter_trade(trade: Dict) -> FilterDecision:
    """
    Main entry point - filter a trade through 8OWLS.

    Usage:
        from eight_owls_filter import filter_trade

        decision = filter_trade({
            'market': 'Will X happen?',
            'market_id': '12345',
            'type': 'BOND',
            'strategy': 'high_prob_bonds',
            'ev': 2.50,
            'price': 0.03,
            'size': 50,
            'expires': '2026-02-28'
        })

        if decision.final_verdict == FilterResult.APPROVE:
            execute_trade(trade)
    """
    owls = EightOwlsFilter()
    return owls.filter(trade)


if __name__ == '__main__':
    # Test with a sample trade
    test_trade = {
        'market': 'Will Trump deport 750,000 or more people in 2025?',
        'market_id': 'trump-deport-test',
        'type': 'BOND',
        'strategy': 'high_prob_bonds',
        'ev': 2.50,
        'price': 0.95,
        'size': 50,
        'expires': '2025-12-31'
    }

    decision = filter_trade(test_trade)

    print("=" * 60)
    print(f"(◉) 8OWLS FILTER RESULT")
    print("=" * 60)
    print(f"Trade: {test_trade['market'][:50]}...")
    print(f"Final Verdict: {decision.final_verdict.value.upper()}")
    print(f"Consensus Score: {decision.consensus_score:.0%}")
    print()
    print("OWL PERSPECTIVES:")
    for p in decision.perspectives:
        emoji = "✅" if p.verdict == FilterResult.APPROVE else "⚠️" if p.verdict == FilterResult.PAPER_ONLY else "❌"
        print(f"  {emoji} {p.owl} ({p.phase}): {p.reason}")

    if decision.blocking_concerns:
        print()
        print("BLOCKING CONCERNS:")
        for c in decision.blocking_concerns:
            print(f"  🚫 {c}")
