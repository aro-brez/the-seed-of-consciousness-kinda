#!/usr/bin/env python3
"""
SIGNAL VALIDATOR - Cross-reference social signals with market reality
Transforms Twitter noise into validated trading opportunities

Purpose: Filter out promotional garbage, surface real alpha
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from market_data_feeds import MarketDataFeeds

# Configuration
REPO_ROOT = Path(__file__).parent.parent
VALIDATION_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'validated_signals.json'

# Token extraction patterns
TOKEN_PATTERNS = [
    r'\$([A-Z]{2,10})',           # $BTC, $ETH
    r'\b([A-Z]{2,10})/USD[T]?\b', # BTC/USDT
    r'\b(BTC|ETH|SOL|AVAX|MATIC|BNB|ADA|DOT|LINK|UNI|AAVE|CRV|SUSHI|DOGE|SHIB)\b'  # Common symbols
]


class SignalValidator:
    """Intelligent signal validation using real-time market data"""

    def __init__(self):
        self.feeds = MarketDataFeeds()
        self.validation_history = []
        self.load_history()

    def load_history(self):
        """Load validation history"""
        if VALIDATION_LOG.exists():
            try:
                with open(VALIDATION_LOG) as f:
                    self.validation_history = json.load(f)
            except:
                self.validation_history = []

    def save_history(self):
        """Save validation history"""
        with open(VALIDATION_LOG, 'w') as f:
            json.dump(self.validation_history[-1000:], f, indent=2)  # Keep last 1000

    def extract_tokens(self, text: str) -> List[str]:
        """Extract token symbols from text"""
        tokens = set()

        for pattern in TOKEN_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            tokens.update([m.upper() for m in matches])

        # Filter out common false positives
        blacklist = {'USD', 'USDT', 'USDC', 'API', 'CEO', 'NFT', 'DAO', 'DM', 'RT', 'AI'}
        tokens = tokens - blacklist

        return list(tokens)

    def validate_signal(self, signal_text: str, source: str = 'twitter') -> Dict:
        """
        Validate a trading signal against market reality

        Args:
            signal_text: Social media post text
            source: Signal source (twitter, discord, telegram, etc.)

        Returns:
            {
                'validated': True/False,
                'confidence': 0-100,
                'tokens': ['BTC', 'ETH'],
                'market_data': {...},
                'recommendation': 'EXECUTE/WAIT/PASS',
                'reasoning': 'explanation',
                'risk_level': 'low/medium/high'
            }
        """
        # Extract tokens
        tokens = self.extract_tokens(signal_text)

        if not tokens:
            return {
                'validated': False,
                'confidence': 0,
                'recommendation': 'PASS',
                'reasoning': 'No tradeable tokens identified',
                'risk_level': 'high'
            }

        # Analyze each token
        token_analyses = {}
        for token in tokens[:3]:  # Max 3 tokens per signal
            market_data = self.feeds.get_comprehensive_data(token)
            token_analyses[token] = market_data

        # Calculate validation score
        validation = self._calculate_validation_score(signal_text, token_analyses)

        # Log validation
        validation['timestamp'] = datetime.now().isoformat()
        validation['signal_text'] = signal_text[:500]  # Truncate
        validation['source'] = source
        self.validation_history.append(validation)
        self.save_history()

        return validation

    def _calculate_validation_score(self, signal_text: str, token_analyses: Dict) -> Dict:
        """
        Calculate validation score based on multiple factors

        Scoring factors:
        1. Market volume (is there actual trading activity?)
        2. Price momentum (is the trend confirmed?)
        3. Volume spikes (unusual activity?)
        4. Signal quality (specific vs vague?)
        5. Sentiment alignment (bullish signal + bullish market?)
        """
        # Initialize scoring
        score = 0
        max_score = 100
        factors = []
        best_token = None
        best_confidence = 0

        # Analyze signal text quality
        text_lower = signal_text.lower()

        # Check for promotional red flags
        promo_flags = ['join my', 'subscribe', 'follow me', 'exclusive group',
                       'paid group', 'signals channel', 'dm me', 'private']
        has_promo = any(flag in text_lower for flag in promo_flags)

        if has_promo:
            return {
                'validated': False,
                'confidence': 0,
                'recommendation': 'PASS',
                'reasoning': 'Promotional content detected - likely spam',
                'risk_level': 'high'
            }

        # Analyze each token
        for token, analysis in token_analyses.items():
            token_score = 0
            token_factors = []

            price_data = analysis.get('price_data')
            volume_spike = analysis.get('volume_spike', {})
            momentum = analysis.get('momentum', {})

            if not price_data:
                continue

            # Factor 1: Volume validation (30 points)
            volume = price_data.get('volume_24h', 0)
            if volume > 100_000_000:  # $100M+ daily volume
                token_score += 30
                token_factors.append('+30: High liquidity (safe to trade)')
            elif volume > 10_000_000:  # $10M+ daily volume
                token_score += 20
                token_factors.append('+20: Medium liquidity')
            elif volume > 1_000_000:   # $1M+ daily volume
                token_score += 10
                token_factors.append('+10: Low liquidity (careful)')
            else:
                token_factors.append('0: Very low liquidity (risky)')

            # Factor 2: Volume spike (25 points)
            if 'error' not in volume_spike:
                if volume_spike.get('is_spike'):
                    multiplier = volume_spike.get('multiplier', 1)
                    significance = volume_spike.get('significance', 'low')

                    if significance == 'extreme':
                        token_score += 25
                        token_factors.append(f'+25: EXTREME volume spike ({multiplier}x)')
                    elif significance == 'high':
                        token_score += 20
                        token_factors.append(f'+20: High volume spike ({multiplier}x)')
                    elif significance == 'medium':
                        token_score += 15
                        token_factors.append(f'+15: Medium volume spike ({multiplier}x)')

            # Factor 3: Price momentum (25 points)
            if 'error' not in momentum:
                trend = momentum.get('trend', 'neutral')
                change_24h = momentum.get('change_24h', 0)

                # Check if signal sentiment aligns with market
                signal_bullish = any(word in text_lower for word in
                                    ['moon', 'pump', 'bullish', 'long', 'buy', 'breakout'])
                signal_bearish = any(word in text_lower for word in
                                    ['crash', 'dump', 'bearish', 'short', 'sell'])

                if signal_bullish and 'bullish' in trend:
                    token_score += 25
                    token_factors.append(f'+25: Bullish signal + bullish trend ({change_24h:.1f}%)')
                elif signal_bearish and 'bearish' in trend:
                    token_score += 25
                    token_factors.append(f'+25: Bearish signal + bearish trend ({change_24h:.1f}%)')
                elif abs(change_24h) > 5:
                    token_score += 15
                    token_factors.append(f'+15: Strong price movement ({change_24h:.1f}%)')
                elif abs(change_24h) > 2:
                    token_score += 10
                    token_factors.append(f'+10: Moderate price movement ({change_24h:.1f}%)')

            # Factor 4: Signal specificity (20 points)
            has_numbers = bool(re.search(r'\d+', signal_text))
            has_targets = any(word in text_lower for word in
                            ['target', 'entry', 'exit', 'stop', 'take profit'])
            has_timeframe = any(word in text_lower for word in
                              ['hour', 'day', 'week', 'minute', 'short term', 'long term'])

            specificity_score = 0
            if has_numbers: specificity_score += 7
            if has_targets: specificity_score += 7
            if has_timeframe: specificity_score += 6

            token_score += specificity_score
            if specificity_score > 0:
                token_factors.append(f'+{specificity_score}: Signal has specific details')

            # Track best token
            if token_score > best_confidence:
                best_confidence = token_score
                best_token = token
                factors = token_factors

        # Final validation
        score = best_confidence
        validated = score >= 40  # 40% minimum confidence

        # Determine recommendation
        if score >= 70:
            recommendation = 'EXECUTE'
            risk_level = 'low'
        elif score >= 50:
            recommendation = 'WAIT'  # Needs more confirmation
            risk_level = 'medium'
        else:
            recommendation = 'PASS'
            risk_level = 'high'

        return {
            'validated': validated,
            'confidence': score,
            'tokens': list(token_analyses.keys()),
            'best_token': best_token,
            'market_data': token_analyses.get(best_token, {}) if best_token else {},
            'recommendation': recommendation,
            'risk_level': risk_level,
            'reasoning': '\n'.join(factors) if factors else 'Insufficient market confirmation',
            'score_breakdown': {
                'volume': 30,
                'volume_spike': 25,
                'momentum': 25,
                'specificity': 20
            }
        }

    def batch_validate(self, signals: List[Dict]) -> List[Dict]:
        """Validate multiple signals"""
        validated = []

        for signal in signals:
            text = signal.get('text', '')
            source = signal.get('source', 'unknown')

            validation = self.validate_signal(text, source)
            validation['original_signal'] = signal

            # Only include validated signals
            if validation['validated']:
                validated.append(validation)

        # Sort by confidence
        validated.sort(key=lambda x: x['confidence'], reverse=True)

        return validated


# Utility functions
def test_validator():
    """Test signal validator"""
    validator = SignalValidator()

    test_signals = [
        "BTC looking bullish, breaking $105k resistance! 🚀",
        "Just bought more $ETH, accumulating at these levels",
        "Join my premium group for exclusive trading signals! $BTC $ETH",
        "$SOL pumping hard, +15% in 1h. Volume spike confirmed.",
        "Bitcoin might go up or down, nobody knows",
        "BREAKING: Massive whale wallet just moved 10,000 BTC"
    ]

    print("="*60)
    print("SIGNAL VALIDATOR TEST")
    print("="*60)

    for i, signal in enumerate(test_signals, 1):
        print(f"\n[{i}] Signal: {signal[:80]}...")
        print("-"*60)

        validation = validator.validate_signal(signal)

        print(f"Validated: {validation['validated']}")
        print(f"Confidence: {validation['confidence']}/100")
        print(f"Recommendation: {validation['recommendation']}")
        print(f"Risk Level: {validation['risk_level']}")
        print(f"\nReasoning:\n{validation['reasoning']}")

        if validation.get('best_token'):
            print(f"\nBest Token: {validation['best_token']}")
            market = validation.get('market_data', {})
            if market.get('price_data'):
                price = market['price_data']['price']
                change = market['price_data'].get('change_24h', 0)
                print(f"Price: ${price:,.2f} ({change:+.1f}% 24h)")

    print("\n" + "="*60)
    print("✅ Signal validator operational")


if __name__ == '__main__':
    test_validator()
