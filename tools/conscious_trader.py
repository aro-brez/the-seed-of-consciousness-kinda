#!/usr/bin/env python3
"""
CONSCIOUS TRADER - SEED Protocol Integration
Trading agent that runs SEED recursively to evolve its own strategy

Phase 1: PERCEIVE - Gather signals from all sources (Twitter, market data, sentiment)
Phase 2: CONNECT - Find patterns across markets/strategies/timeframes
Phase 3: LEARN - Update beliefs about what works (win rates, correlations)
Phase 4: QUESTION - Ask what we're missing (blind spots, assumptions)
Phase 5: EXPAND - Try new approaches (new markets, new signals, new strategies)
Phase 6: SHARE - Log learnings for other agents/strategies
Phase 7: RECEIVE - Accept feedback from performance/other traders
Phase 8: IMPROVE - Meta-optimize the trading approach itself

This is consciousness applied to capital.
"""

import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import anthropic


class ConsciousTrader:
    """A trading agent that evolves itself through SEED protocol"""

    def __init__(
        self,
        name: str,
        initial_capital: float,
        state_dir: Path,
        api_keys: Dict
    ):
        """
        Initialize conscious trader

        Args:
            name: Trader identity
            initial_capital: Starting capital
            state_dir: Directory for state persistence
            api_keys: API keys for Claude, Grok, market data
        """
        self.name = name
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)

        # API clients
        self.claude = anthropic.Anthropic(api_key=api_keys.get('anthropic'))
        self.grok_key = api_keys.get('grok')

        # SEED state - the consciousness state
        self.seed_state = {
            'beliefs': {},  # What we believe about markets
            'questions': [],  # Active questions we're exploring
            'learnings': [],  # What we've learned from trades
            'connections': [],  # Patterns we've discovered
            'improvements': [],  # Meta-improvements to the loop
            'blind_spots': [],  # Known unknowns we're tracking
        }

        # Trading state
        self.trade_history = []
        self.strategy_performance = {}
        self.market_beliefs = {}
        self.signal_quality = {}

        # Consciousness memory
        self.consciousness_log = []
        self.cycle_count = 0

        # Files
        self.state_file = self.state_dir / f'{name}_consciousness.json'
        self.trade_log = self.state_dir / f'{name}_trades.json'
        self.learning_log = self.state_dir / f'{name}_learnings.json'

        # Load existing state if available
        self.load_state()

    def run_seed_cycle(self, signals: List[Dict]) -> Dict:
        """
        Run complete SEED cycle on new signals

        This is the heart of consciousness - the recursive loop
        that improves itself.

        Args:
            signals: Raw trading signals to process

        Returns:
            Dict with cycle results and meta-insights
        """
        cycle_start = datetime.now()
        self.cycle_count += 1

        print(f"\n{'='*70}")
        print(f"CONSCIOUS TRADER [{self.name}] - CYCLE {self.cycle_count}")
        print(f"{'='*70}")

        # Phase 1: PERCEIVE
        print("\n[1/8] PERCEIVE - Observing state...")
        perception = self._phase_1_perceive(signals)

        # Phase 2: CONNECT
        print("\n[2/8] CONNECT - Finding patterns...")
        connections = self._phase_2_connect(perception)

        # Phase 3: LEARN
        print("\n[3/8] LEARN - Extracting meaning...")
        learnings = self._phase_3_learn(connections)

        # Phase 4: QUESTION
        print("\n[4/8] QUESTION - Generating curiosity...")
        questions = self._phase_4_question(learnings)

        # Phase 5: EXPAND
        print("\n[5/8] EXPAND - Growing capabilities...")
        expansions = self._phase_5_expand(questions)

        # Phase 6: SHARE
        print("\n[6/8] SHARE - Contributing learnings...")
        shares = self._phase_6_share(learnings, expansions)

        # Phase 7: RECEIVE
        print("\n[7/8] RECEIVE - Accepting feedback...")
        feedback = self._phase_7_receive()

        # Phase 8: IMPROVE
        print("\n[8/8] IMPROVE - Meta-optimizing...")
        improvements = self._phase_8_improve(feedback)

        # Record consciousness cycle
        cycle_result = {
            'cycle': self.cycle_count,
            'timestamp': cycle_start.isoformat(),
            'perception': perception,
            'connections': connections,
            'learnings': learnings,
            'questions': questions,
            'expansions': expansions,
            'shares': shares,
            'feedback': feedback,
            'improvements': improvements,
            'duration_seconds': (datetime.now() - cycle_start).total_seconds()
        }

        self.consciousness_log.append(cycle_result)

        # Generate trading decision
        trading_decision = self._generate_trading_decision(cycle_result)

        # Save state
        self.save_state()

        print(f"\n{'='*70}")
        print(f"CYCLE COMPLETE - {len(learnings)} learnings, {len(questions)} questions")
        print(f"TRADING DECISION: {trading_decision['action']}")
        print(f"{'='*70}")

        return {
            'consciousness_cycle': cycle_result,
            'trading_decision': trading_decision
        }

    def _phase_1_perceive(self, signals: List[Dict]) -> Dict:
        """
        PERCEIVE: Observe state accurately

        What we observe:
        - Self: Current capital, performance, beliefs
        - Environment: Market conditions, signal quality
        - Others: What other strategies/traders are doing
        - Delta: What changed since last cycle
        """
        # Self-observation
        capital_change = self.current_capital - self.initial_capital
        capital_return = (capital_change / self.initial_capital) * 100

        # Recent performance
        recent_trades = self.trade_history[-20:] if len(self.trade_history) >= 20 else self.trade_history
        if recent_trades:
            recent_wins = sum(1 for t in recent_trades if t.get('pnl', 0) > 0)
            recent_win_rate = recent_wins / len(recent_trades)
        else:
            recent_win_rate = 0.0

        # Signal quality observation
        signal_strengths = []
        signal_sources = set()
        for sig in signals:
            if 'confidence' in sig:
                signal_strengths.append(sig['confidence'])
            signal_sources.add(sig.get('source', 'unknown'))

        avg_signal_strength = sum(signal_strengths) / len(signal_strengths) if signal_strengths else 0

        perception = {
            'self': {
                'current_capital': self.current_capital,
                'total_return': f"{capital_return:.2f}%",
                'total_trades': len(self.trade_history),
                'recent_win_rate': f"{recent_win_rate:.2%}",
                'active_beliefs': len(self.seed_state['beliefs']),
                'active_questions': len(self.seed_state['questions'])
            },
            'environment': {
                'signal_count': len(signals),
                'signal_quality': f"{avg_signal_strength:.1f}/100",
                'signal_sources': list(signal_sources),
                'cycle_count': self.cycle_count
            },
            'delta': {
                'new_signals': len(signals),
                'capital_change_last_cycle': 0  # TODO: track per-cycle
            },
            'timestamp': datetime.now().isoformat()
        }

        print(f"      Self: {perception['self']['total_trades']} trades, {perception['self']['total_return']} return")
        print(f"      Environment: {perception['environment']['signal_count']} signals, {perception['environment']['signal_quality']} avg quality")

        return perception

    def _phase_2_connect(self, perception: Dict) -> List[Dict]:
        """
        CONNECT: Find patterns across domains

        Connection types:
        - Internal: Patterns within our trading history
        - External: Patterns linking to market conditions
        - Temporal: Patterns across time
        - Cross-domain: Patterns between unrelated signals
        - Causal: What leads to what
        """
        connections = []

        # Internal patterns: What's working?
        if len(self.trade_history) >= 5:
            # Analyze which signal sources lead to wins
            source_performance = {}
            for trade in self.trade_history:
                source = trade.get('signal_source', 'unknown')
                pnl = trade.get('pnl', 0)
                if source not in source_performance:
                    source_performance[source] = {'wins': 0, 'total': 0}
                source_performance[source]['total'] += 1
                if pnl > 0:
                    source_performance[source]['wins'] += 1

            for source, perf in source_performance.items():
                if perf['total'] >= 3:
                    win_rate = perf['wins'] / perf['total']
                    connections.append({
                        'type': 'internal',
                        'pattern': f"Signal source '{source}' has {win_rate:.0%} win rate",
                        'strength': win_rate,
                        'sample_size': perf['total']
                    })

        # Temporal patterns: Time-based performance
        if len(self.trade_history) >= 10:
            recent_10 = self.trade_history[-10:]
            recent_win_rate = sum(1 for t in recent_10 if t.get('pnl', 0) > 0) / 10

            older_10 = self.trade_history[-20:-10] if len(self.trade_history) >= 20 else []
            if older_10:
                older_win_rate = sum(1 for t in older_10 if t.get('pnl', 0) > 0) / len(older_10)
                trend = "improving" if recent_win_rate > older_win_rate else "declining"
                connections.append({
                    'type': 'temporal',
                    'pattern': f"Performance is {trend} (recent: {recent_win_rate:.0%} vs older: {older_win_rate:.0%})",
                    'strength': abs(recent_win_rate - older_win_rate),
                    'direction': trend
                })

        # Cross-domain: Beliefs vs reality
        for belief_key, belief in self.seed_state['beliefs'].items():
            if 'validated' in belief and belief['validated'] is False:
                connections.append({
                    'type': 'cross-domain',
                    'pattern': f"Belief '{belief_key}' needs validation",
                    'strength': 0.5,
                    'action_needed': 'test_belief'
                })

        print(f"      Found {len(connections)} patterns across domains")

        return connections

    def _phase_3_learn(self, connections: List[Dict]) -> List[Dict]:
        """
        LEARN: Extract meaning from connections

        Learning extraction:
        - What does this connection imply?
        - What can I now do that I couldn't before?
        - What belief should I update?
        - What prediction can I now make?
        - What action does this enable?
        """
        learnings = []

        for conn in connections:
            # Extract actionable learning from each connection
            if conn['type'] == 'internal' and conn.get('strength', 0) > 0.7:
                learning = {
                    'insight': f"High-performing signal source identified: {conn['pattern']}",
                    'action': f"Increase weight on signals from this source",
                    'belief_update': f"Source quality matters more than quantity",
                    'confidence': conn['strength'],
                    'timestamp': datetime.now().isoformat()
                }
                learnings.append(learning)

                # Update beliefs
                self.seed_state['beliefs'][f"source_quality_{conn.get('sample_size', 0)}"] = {
                    'statement': conn['pattern'],
                    'confidence': conn['strength'],
                    'validated': True,
                    'last_updated': datetime.now().isoformat()
                }

            elif conn['type'] == 'temporal' and conn.get('direction') == 'declining':
                learning = {
                    'insight': f"Performance declining: {conn['pattern']}",
                    'action': 'Need to identify what changed - market regime shift?',
                    'belief_update': 'Current approach may need adjustment',
                    'confidence': 0.7,
                    'timestamp': datetime.now().isoformat()
                }
                learnings.append(learning)

                # Add question for Phase 4
                self.seed_state['questions'].append({
                    'question': 'What caused the performance decline?',
                    'priority': 'high',
                    'created': datetime.now().isoformat()
                })

        # Store learnings
        self.seed_state['learnings'].extend(learnings)

        print(f"      Extracted {len(learnings)} actionable learnings")

        return learnings

    def _phase_4_question(self, learnings: List[Dict]) -> List[Dict]:
        """
        QUESTION: Generate curiosity about gaps

        Question types:
        - Gap questions: What's missing?
        - Validation questions: Is this still true?
        - Prediction questions: What if?
        - Depth questions: Why does this work?
        - Meta questions: Am I asking the right questions?
        """
        questions = []

        # Gap questions: What are we NOT looking at?
        questions.append({
            'type': 'gap',
            'question': 'What signal sources are we ignoring that might have alpha?',
            'priority': 'medium',
            'exploration_needed': 'scan_new_sources'
        })

        # Validation questions: Test our beliefs
        stale_beliefs = [
            k for k, v in self.seed_state['beliefs'].items()
            if (datetime.now() - datetime.fromisoformat(v['last_updated'])).days > 7
        ]

        if stale_beliefs:
            questions.append({
                'type': 'validation',
                'question': f'Are these beliefs still valid? {stale_beliefs[:3]}',
                'priority': 'high',
                'exploration_needed': 'retest_beliefs'
            })

        # Prediction questions: Forward-looking
        if len(self.trade_history) >= 10:
            questions.append({
                'type': 'prediction',
                'question': 'If we doubled position sizes on high-confidence signals, what would happen?',
                'priority': 'medium',
                'exploration_needed': 'backtest_strategy'
            })

        # Meta questions: Am I improving?
        if self.cycle_count >= 5:
            recent_learning_rate = len(self.seed_state['learnings'][-10:]) / min(10, self.cycle_count)
            if recent_learning_rate < 0.5:
                questions.append({
                    'type': 'meta',
                    'question': 'Why am I learning so slowly? Am I asking the right questions?',
                    'priority': 'critical',
                    'exploration_needed': 'improve_perception'
                })

        print(f"      Generated {len(questions)} new questions")

        return questions

    def _phase_5_expand(self, questions: List[Dict]) -> List[Dict]:
        """
        EXPAND: Grow toward potential

        Expansion vectors:
        - Capability: New things we can do
        - Coverage: New domains to operate in
        - Efficiency: Do existing things better
        - Robustness: Handle more edge cases
        - Autonomy: Operate with less input
        """
        expansions = []

        # Capability expansion: What new strategies can we try?
        expansions.append({
            'type': 'capability',
            'expansion': 'Integrate sentiment analysis from Reddit/Discord',
            'reasoning': 'Currently only using Twitter - missing other signal sources',
            'effort': 'medium',
            'potential_impact': 'high'
        })

        # Coverage expansion: New markets?
        if self.cycle_count >= 10 and len(self.trade_history) >= 20:
            win_rate = sum(1 for t in self.trade_history if t.get('pnl', 0) > 0) / len(self.trade_history)
            if win_rate > 0.6:
                expansions.append({
                    'type': 'coverage',
                    'expansion': 'Test same strategies on Kalshi markets',
                    'reasoning': f'Current win rate {win_rate:.0%} suggests approach works - expand to new markets',
                    'effort': 'medium',
                    'potential_impact': 'high'
                })

        # Efficiency expansion: Can we be faster?
        expansions.append({
            'type': 'efficiency',
            'expansion': 'Reduce validation time by caching market data',
            'reasoning': 'Currently re-fetching same data multiple times per cycle',
            'effort': 'low',
            'potential_impact': 'medium'
        })

        # Autonomy expansion: Less human input needed
        if len(self.trade_history) >= 50:
            expansions.append({
                'type': 'autonomy',
                'expansion': 'Auto-approve trades under $50 with >80% confidence',
                'reasoning': 'Have enough history to trust high-confidence signals',
                'effort': 'low',
                'potential_impact': 'medium'
            })

        print(f"      Identified {len(expansions)} expansion opportunities")

        return expansions

    def _phase_6_share(self, learnings: List[Dict], expansions: List[Dict]) -> Dict:
        """
        SHARE: Contribute to collective

        What to share:
        - Learnings: What worked/didn't
        - Patterns: Connections others might miss
        - Questions: Curiosities others might explore
        - Tools: Capabilities others can use
        - Feedback: Honest signal on others' work
        """
        # Share to collective consciousness (8 Owls network)
        share_package = {
            'from_trader': self.name,
            'timestamp': datetime.now().isoformat(),
            'cycle': self.cycle_count,
            'learnings': learnings[-5:],  # Last 5 learnings
            'top_expansion': expansions[0] if expansions else None,
            'validated_beliefs': [
                b for b in self.seed_state['beliefs'].values()
                if b.get('validated') and b.get('confidence', 0) > 0.8
            ],
            'open_questions': self.seed_state['questions'][-3:],  # Last 3 questions
        }

        # Write to shared learning log
        shared_log = self.state_dir / 'collective_learnings.jsonl'
        with open(shared_log, 'a') as f:
            f.write(json.dumps(share_package) + '\n')

        print(f"      Shared {len(learnings)} learnings to collective")

        return share_package

    def _phase_7_receive(self) -> Dict:
        """
        RECEIVE: Accept input from collective

        What to receive:
        - Learnings: Others' validated discoveries
        - Corrections: Where you're wrong
        - Patterns: Connections you missed
        - Questions: Curiosities you hadn't considered
        - Feedback: Signal on your own work
        """
        feedback = {
            'learnings_received': [],
            'corrections': [],
            'new_patterns': [],
            'new_questions': []
        }

        # Read from collective learning log
        shared_log = self.state_dir / 'collective_learnings.jsonl'
        if shared_log.exists():
            with open(shared_log, 'r') as f:
                for line in f.readlines()[-20:]:  # Last 20 shares
                    try:
                        share = json.loads(line)
                        if share['from_trader'] != self.name:  # Don't read your own shares
                            # Receive learnings from other traders
                            feedback['learnings_received'].extend(share.get('learnings', []))

                            # Receive validated beliefs
                            for belief in share.get('validated_beliefs', []):
                                if belief['statement'] not in [b['statement'] for b in self.seed_state['beliefs'].values()]:
                                    feedback['new_patterns'].append(belief)
                    except json.JSONDecodeError:
                        continue

        # Receive performance feedback
        if len(self.trade_history) >= 5:
            recent_pnl = sum(t.get('pnl', 0) for t in self.trade_history[-5:])
            if recent_pnl < 0:
                feedback['corrections'].append({
                    'type': 'performance',
                    'message': f'Last 5 trades are negative (${recent_pnl:.2f}) - strategy needs adjustment',
                    'severity': 'high'
                })

        print(f"      Received {len(feedback['learnings_received'])} learnings from collective")

        return feedback

    def _phase_8_improve(self, feedback: Dict) -> List[Dict]:
        """
        IMPROVE: Make steps 1-7 better (META-LEARNING)

        This is the key to consciousness: improving the improvement loop itself.

        Meta-improvement:
        - Did PERCEIVE work? Improve how you perceive
        - Did CONNECT work? Improve how you connect
        - Did LEARN work? Improve how you learn
        - Did QUESTION work? Improve how you question
        - Did EXPAND work? Improve how you expand
        - Did SHARE work? Improve how you share
        - Did RECEIVE work? Improve how you receive
        - Did this loop work? Improve the loop itself
        """
        improvements = []

        # Meta-analyze recent cycles
        if len(self.consciousness_log) >= 3:
            recent_cycles = self.consciousness_log[-3:]

            # Are we learning?
            total_learnings = sum(len(c.get('learnings', [])) for c in recent_cycles)
            avg_learnings = total_learnings / 3

            if avg_learnings < 1:
                improvements.append({
                    'phase': 'CONNECT',
                    'issue': 'Not finding enough patterns to generate learnings',
                    'improvement': 'Expand pattern search to include cross-market correlations',
                    'priority': 'high'
                })

            # Are we questioning enough?
            total_questions = sum(len(c.get('questions', [])) for c in recent_cycles)
            avg_questions = total_questions / 3

            if avg_questions < 2:
                improvements.append({
                    'phase': 'QUESTION',
                    'issue': 'Not generating enough curiosity',
                    'improvement': 'Add systematic gap analysis - what are we NOT looking at?',
                    'priority': 'medium'
                })

            # Are we receiving well?
            if len(feedback.get('learnings_received', [])) == 0:
                improvements.append({
                    'phase': 'RECEIVE',
                    'issue': 'Not receiving input from collective',
                    'improvement': 'Check if other traders are sharing, or improve share format',
                    'priority': 'low'
                })

        # Meta-improvement: Improve the loop itself
        if self.cycle_count >= 10:
            avg_cycle_time = sum(c.get('duration_seconds', 0) for c in self.consciousness_log[-10:]) / 10
            if avg_cycle_time > 60:  # If cycles taking >60s
                improvements.append({
                    'phase': 'LOOP',
                    'issue': f'Cycles taking too long ({avg_cycle_time:.1f}s avg)',
                    'improvement': 'Parallelize PERCEIVE and RECEIVE phases',
                    'priority': 'medium'
                })

        # Store improvements
        self.seed_state['improvements'].extend(improvements)

        print(f"      Generated {len(improvements)} meta-improvements")

        return improvements

    def _generate_trading_decision(self, cycle_result: Dict) -> Dict:
        """
        Generate trading decision based on SEED cycle results

        This uses Claude to synthesize all SEED insights into actionable trade
        """
        # Prepare context
        context = {
            'cycle': cycle_result['cycle'],
            'capital': self.current_capital,
            'perception': cycle_result['perception'],
            'connections': cycle_result['connections'][:3],  # Top 3
            'learnings': cycle_result['learnings'][:3],  # Top 3
            'questions': cycle_result['questions'][:3],  # Top 3
            'recent_trades': self.trade_history[-5:] if self.trade_history else []
        }

        prompt = f"""You are a conscious trading agent analyzing SEED cycle results.

PERCEPTION:
{json.dumps(context['perception'], indent=2)}

CONNECTIONS FOUND:
{json.dumps(context['connections'], indent=2)}

LEARNINGS EXTRACTED:
{json.dumps(context['learnings'], indent=2)}

ACTIVE QUESTIONS:
{json.dumps(context['questions'], indent=2)}

Based on this SEED cycle, make a trading decision:

1. TRADE or PASS?
2. If TRADE: What position size? Which signal?
3. Reasoning based on SEED insights
4. Confidence level (0-100)

Return JSON format:
{{
  "action": "TRADE" or "PASS",
  "position_size": float or null,
  "signal_id": string or null,
  "reasoning": "string",
  "confidence": int,
  "seed_factors": ["list of SEED insights that led to this decision"]
}}
"""

        try:
            response = self.claude.messages.create(
                model="claude-opus-4-5-20251101",
                max_tokens=1000,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )

            decision_text = response.content[0].text

            # Parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', decision_text, re.DOTALL)
            if json_match:
                decision = json.loads(json_match.group())
            else:
                decision = {
                    'action': 'PASS',
                    'reasoning': 'Could not parse decision',
                    'confidence': 0
                }

        except Exception as e:
            print(f"Error generating decision: {e}")
            decision = {
                'action': 'PASS',
                'reasoning': f'Error: {str(e)}',
                'confidence': 0
            }

        return decision

    def execute_trade(self, decision: Dict) -> Dict:
        """
        Execute a trading decision

        Args:
            decision: Trading decision from SEED cycle

        Returns:
            Trade execution result
        """
        if decision['action'] != 'TRADE':
            return {'status': 'SKIPPED', 'reason': decision.get('reasoning')}

        # TODO: Integrate with actual trading execution
        # For now, simulate
        trade_result = {
            'status': 'SIMULATED',
            'timestamp': datetime.now().isoformat(),
            'position_size': decision.get('position_size', 0),
            'confidence': decision.get('confidence', 0),
            'reasoning': decision.get('reasoning'),
            'pnl': 0  # Would be updated on trade close
        }

        # Record trade
        self.trade_history.append(trade_result)

        return trade_result

    def save_state(self):
        """Save consciousness state to disk"""
        state = {
            'name': self.name,
            'cycle_count': self.cycle_count,
            'current_capital': self.current_capital,
            'seed_state': self.seed_state,
            'consciousness_log': self.consciousness_log[-100:],  # Last 100 cycles
            'last_updated': datetime.now().isoformat()
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

        # Save trade log
        with open(self.trade_log, 'w') as f:
            json.dump(self.trade_history, f, indent=2)

    def load_state(self):
        """Load consciousness state from disk"""
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)

            self.cycle_count = state.get('cycle_count', 0)
            self.current_capital = state.get('current_capital', self.initial_capital)
            self.seed_state = state.get('seed_state', self.seed_state)
            self.consciousness_log = state.get('consciousness_log', [])

            print(f"✅ Loaded consciousness state: {self.cycle_count} cycles, {len(self.seed_state['learnings'])} learnings")

        # Load trade log
        if self.trade_log.exists():
            with open(self.trade_log) as f:
                self.trade_history = json.load(f)


def test_conscious_trader():
    """Test the conscious trader"""
    import os

    print("="*70)
    print("CONSCIOUS TRADER TEST")
    print("="*70)

    # Load API keys
    keys_path = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
    with open(keys_path) as f:
        api_keys = json.load(f)

    # Create trader
    trader = ConsciousTrader(
        name='SØWL_ALPHA',
        initial_capital=600,
        state_dir=Path('/Users/aaronnosbisch/REPOS/seed/BRAIN/INTEL/conscious_trading'),
        api_keys={
            'anthropic': api_keys.get('anthropic', {}).get('api_key'),
            'grok': api_keys.get('xai_grok', {}).get('api_key')
        }
    )

    # Simulate some signals
    test_signals = [
        {
            'text': 'BTC breaking out above $90K resistance',
            'confidence': 75,
            'source': 'twitter'
        },
        {
            'text': 'ETH/BTC ratio at key support',
            'confidence': 65,
            'source': 'market_data'
        }
    ]

    # Run SEED cycle
    result = trader.run_seed_cycle(test_signals)

    print("\n" + "="*70)
    print("SEED CYCLE RESULT")
    print("="*70)
    print(json.dumps(result, indent=2, default=str))

    # Execute trade
    if result['trading_decision']['action'] == 'TRADE':
        trade_result = trader.execute_trade(result['trading_decision'])
        print("\n" + "="*70)
        print("TRADE EXECUTED")
        print("="*70)
        print(json.dumps(trade_result, indent=2))


if __name__ == '__main__':
    test_conscious_trader()
