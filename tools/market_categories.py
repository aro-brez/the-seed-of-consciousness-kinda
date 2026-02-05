#!/usr/bin/env python3
"""
ENHANCED MARKET CATEGORY DETECTION
20+ categories with volatility profiles and risk limits
"""

import re
from typing import Dict, Tuple, List


# Market category definitions with risk profiles
MARKET_CATEGORIES = {
    # SPORTS - Generally predictable, data-driven
    'nfl': {
        'keywords': ['nfl', 'football', 'super bowl', 'quarterback', 'touchdown', 'yards', 'patriots', 'chiefs', 'cowboys', 'halftime show', 'bowl', 'playoff'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.05  # Sports have good data
    },
    'nba': {
        'keywords': ['nba', 'basketball', 'points', 'rebounds', 'assists', 'lakers', 'warriors', 'lebron', 'dunk', 'finals'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.05
    },
    'mlb': {
        'keywords': ['mlb', 'baseball', 'home runs', 'strikeouts', 'world series', 'yankees', 'dodgers', 'batter', 'pitcher'],
        'volatility': 'medium', 
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.03
    },
    'soccer': {
        'keywords': ['soccer', 'football', 'world cup', 'premier league', 'goals', 'messi', 'ronaldo', 'fifa', 'uefa'],
        'volatility': 'medium',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.03
    },
    'olympics': {
        'keywords': ['olympics', 'olympic', 'medal', 'gold medal', 'winter olympics', 'summer olympics', 'paralympics'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 4,
        'confidence_boost': 0.08  # Olympics are well-tracked events
    },
    
    # POLITICS - Moderate volatility, event-driven
    'us_politics': {
        'keywords': ['trump', 'biden', 'president', 'congress', 'senate', 'election', 'vote', 'poll', 'cabinet', 'impeach', 'inauguration'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.0
    },
    'policy': {
        'keywords': ['tariff', 'tax', 'budget', 'spending', 'deficit', 'immigration', 'deport', 'healthcare', 'infrastructure'],
        'volatility': 'high',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.0
    },
    'international_politics': {
        'keywords': ['china', 'taiwan', 'invade', 'invasion', 'war', 'ukraine', 'russia', 'iran', 'israel', 'zelenskyy', 'putin'],
        'volatility': 'very_high',
        'max_exposure': 50,
        'max_trades_per_day': 1,
        'confidence_boost': -0.10  # Geopolitics are highly unpredictable
    },
    'government_personnel': {
        'keywords': ['cabinet', 'secretary', 'advisor', 'nomination', 'confirmation', 'resign', 'fired', 'appointed'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': -0.05
    },
    
    # CRYPTO - High volatility, sentiment-driven
    'crypto_price': {
        'keywords': ['bitcoin', 'btc', 'ethereum', 'eth', 'price', 'crypto', '$', 'usd'],
        'volatility': 'very_high',
        'max_exposure': 50,
        'max_trades_per_day': 1,
        'confidence_boost': -0.10  # Crypto predictions are hard
    },
    'crypto_tech': {
        'keywords': ['blockchain', 'defi', 'nft', 'smart contract', 'layer 2', 'metamask'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': -0.05
    },
    
    # TECH - Moderate-high volatility
    'ai': {
        'keywords': ['ai', 'artificial intelligence', 'openai', 'anthropic', 'gpt', 'claude', 'model', 'grok'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.0
    },
    'big_tech': {
        'keywords': ['google', 'apple', 'microsoft', 'amazon', 'meta', 'tesla', 'stock', 'earnings'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.0
    },
    
    # ENTERTAINMENT - High volatility, unpredictable
    'movies_tv': {
        'keywords': ['movie', 'film', 'netflix', 'box office', 'oscar', 'streaming', 'disney', 'm3gan', 'show', 'series', 'episode'],
        'volatility': 'very_high',
        'max_exposure': 25,
        'max_trades_per_day': 1,
        'confidence_boost': -0.15  # Entertainment is very unpredictable
    },
    'gaming': {
        'keywords': ['game', 'gaming', 'nintendo', 'playstation', 'xbox', 'gta', 'release', 'esports', 'twitch', 'steam'],
        'volatility': 'high',
        'max_exposure': 50,
        'max_trades_per_day': 2,
        'confidence_boost': -0.05
    },
    'awards_shows': {
        'keywords': ['grammy', 'oscar', 'emmy', 'golden globe', 'award', 'best artist', 'album of the year', 'record of the year', 'song of the year'],
        'volatility': 'very_high',
        'max_exposure': 25,
        'max_trades_per_day': 1,
        'confidence_boost': -0.12  # Awards are subjective and unpredictable
    },
    'music_charts': {
        'keywords': ['billboard', 'chart', 'album', 'song', '#1', 'top', 'billie eilish', 'taylor swift', 'bad bunny', 'tyler creator'],
        'volatility': 'high',
        'max_exposure': 50,
        'max_trades_per_day': 2,
        'confidence_boost': -0.08
    },
    
    # FINANCE & ECONOMICS - Medium volatility
    'stock_markets': {
        'keywords': ['stock', 'market', 'dow', 'sp500', 'nasdaq', 'trading', 'fed', 'interest', 'earnings', 'ipo'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.0
    },
    'commodities': {
        'keywords': ['gold', 'silver', 'oil', 'commodity', 'price', 'futures', 'copper', 'wheat', 'corn'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': -0.05
    },
    'individual_stocks': {
        'keywords': ['meta', 'tesla', 'apple', 'microsoft', 'google', 'amazon', 'nvidia', 'close above', 'market cap', 'valuation'],
        'volatility': 'high',
        'max_exposure': 100,
        'max_trades_per_day': 4,
        'confidence_boost': 0.02  # Individual stock movements are more predictable with good analysis
    },
    'company_events': {
        'keywords': ['ipo', 'merger', 'acquisition', 'earnings', 'buyback', 'dividend', 'ceo', 'layoffs', 'spinoff'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.0
    },
    
    # MEME/SOCIAL - Very high volatility
    'elon_musk': {
        'keywords': ['elon', 'musk', 'tesla', 'spacex', 'twitter', 'x.com', 'doge'],
        'volatility': 'extreme',
        'max_exposure': 25,
        'max_trades_per_day': 1,
        'confidence_boost': -0.20  # Elon markets are chaos
    },
    'social_media': {
        'keywords': ['twitter', 'facebook', 'instagram', 'tiktok', 'social', 'viral', 'meme'],
        'volatility': 'very_high',
        'max_exposure': 25,
        'max_trades_per_day': 1,
        'confidence_boost': -0.15
    },
    
    # SCIENCE & HEALTH - Low-medium volatility, fact-based
    'medical': {
        'keywords': ['vaccine', 'drug', 'fda', 'clinical', 'trial', 'health', 'disease'],
        'volatility': 'low',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.05  # Science is more predictable
    },
    'climate': {
        'keywords': ['climate', 'weather', 'temperature', 'hurricane', 'storm', 'drought'],
        'volatility': 'medium',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.0
    },
    
    # INTERNATIONAL - Medium volatility
    'international': {
        'keywords': ['china', 'russia', 'ukraine', 'war', 'nato', 'eu', 'brexit', 'japan'],
        'volatility': 'medium',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': -0.05
    },
    
    # LEGAL - Low volatility, predictable
    'legal': {
        'keywords': ['court', 'supreme court', 'judge', 'lawsuit', 'ruling', 'appeal', 'verdict', 'trial', 'conviction', 'pardon'],
        'volatility': 'low',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.10  # Legal outcomes often have good precedents
    },
    
    # NEW CATEGORIES - EXPANDING COVERAGE
    'weather_events': {
        'keywords': ['hurricane', 'tornado', 'earthquake', 'flood', 'wildfire', 'storm', 'blizzard', 'drought', 'temperature'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.05  # Weather patterns have some predictability
    },
    'space_technology': {
        'keywords': ['spacex', 'nasa', 'rocket', 'satellite', 'mars', 'moon', 'launch', 'space station', 'astronaut'],
        'volatility': 'high',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.0
    },
    'academic_achievements': {
        'keywords': ['nobel', 'prize', 'university', 'research', 'study', 'breakthrough', 'discovery', 'publication'],
        'volatility': 'low',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.08  # Academic achievements are often merit-based
    },
    'business_regulations': {
        'keywords': ['fda', 'approval', 'regulation', 'ban', 'compliance', 'license', 'permit', 'audit', 'investigation'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.03
    },
    'demographic_trends': {
        'keywords': ['population', 'birth rate', 'census', 'migration', 'age', 'generation', 'millennial', 'gen z'],
        'volatility': 'low',
        'max_exposure': 100,
        'max_trades_per_day': 2,
        'confidence_boost': 0.12  # Demographics change slowly and predictably
    },
    'transportation': {
        'keywords': ['airline', 'car', 'truck', 'train', 'subway', 'uber', 'tesla', 'autonomous', 'electric vehicle'],
        'volatility': 'medium',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.0
    },
    'food_beverage': {
        'keywords': ['restaurant', 'mcdonalds', 'starbucks', 'food', 'beverage', 'alcohol', 'wine', 'beer', 'coffee'],
        'volatility': 'low',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.05
    },
    'fashion_retail': {
        'keywords': ['fashion', 'clothing', 'retail', 'store', 'brand', 'luxury', 'nike', 'adidas', 'shopping'],
        'volatility': 'medium',
        'max_exposure': 50,
        'max_trades_per_day': 2,
        'confidence_boost': -0.02
    },
    'religion_culture': {
        'keywords': ['pope', 'church', 'religious', 'cultural', 'tradition', 'holiday', 'festival', 'ceremony'],
        'volatility': 'low',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.05
    },
    'technology_adoption': {
        'keywords': ['adoption', 'user base', 'download', 'install', 'usage', 'penetration', 'rollout', '5g', 'wifi'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.05  # Tech adoption follows patterns
    },
    'crime_security': {
        'keywords': ['crime', 'arrest', 'prison', 'jail', 'security', 'terrorism', 'cyberattack', 'hack', 'breach'],
        'volatility': 'high',
        'max_exposure': 50,
        'max_trades_per_day': 1,
        'confidence_boost': -0.10  # Crime events are unpredictable
    },
    'education': {
        'keywords': ['school', 'university', 'college', 'student', 'graduation', 'enrollment', 'test scores', 'education'],
        'volatility': 'low',
        'max_exposure': 75,
        'max_trades_per_day': 2,
        'confidence_boost': 0.08
    },
    'energy': {
        'keywords': ['energy', 'electricity', 'power', 'solar', 'wind', 'nuclear', 'coal', 'gas', 'renewable'],
        'volatility': 'medium',
        'max_exposure': 100,
        'max_trades_per_day': 3,
        'confidence_boost': 0.0
    }
}

# Volatility to risk multiplier mapping
VOLATILITY_RISK_MULTIPLIERS = {
    'low': 1.2,         # Low vol = size up
    'medium': 1.0,      # Baseline
    'high': 0.8,        # High vol = size down
    'very_high': 0.6,   # Very high vol = significant size down
    'extreme': 0.4      # Extreme vol = minimal size
}


def detect_market_category(market_text: str) -> Tuple[str, float, Dict]:
    """
    Detect market category with confidence and metadata
    
    Args:
        market_text: Market question/title text
        
    Returns:
        Tuple of (category_name, confidence, metadata_dict)
    """
    
    if not market_text:
        return 'other', 0.0, {}
        
    text_lower = market_text.lower()
    
    # Score each category
    category_scores = {}
    
    for category, config in MARKET_CATEGORIES.items():
        score = 0
        matched_keywords = []
        
        for keyword in config['keywords']:
            if keyword in text_lower:
                # Weight longer keywords more heavily
                keyword_weight = len(keyword) / 5.0  # 5-char avg
                score += keyword_weight
                matched_keywords.append(keyword)
                
        if score > 0:
            category_scores[category] = {
                'score': score,
                'matched_keywords': matched_keywords,
                'config': config
            }
    
    if not category_scores:
        return 'other', 0.0, {'reason': 'No keyword matches'}
        
    # Find best match
    best_category = max(category_scores.keys(), key=lambda k: category_scores[k]['score'])
    best_score = category_scores[best_category]['score']
    
    # Calculate confidence (0-1)
    max_possible_score = 5.0  # Reasonable upper bound
    confidence = min(1.0, best_score / max_possible_score)
    
    metadata = {
        'matched_keywords': category_scores[best_category]['matched_keywords'],
        'all_matches': {k: v['score'] for k, v in category_scores.items()},
        'volatility': MARKET_CATEGORIES[best_category]['volatility'],
        'confidence_boost': MARKET_CATEGORIES[best_category]['confidence_boost']
    }
    
    return best_category, confidence, metadata


def get_category_risk_limits(category: str) -> Dict:
    """
    Get risk limits and multipliers for a category
    
    Args:
        category: Category name
        
    Returns:
        Dict with risk parameters
    """
    
    if category not in MARKET_CATEGORIES:
        # Default limits for unknown categories
        return {
            'max_exposure': 50,
            'max_trades_per_day': 1,
            'volatility': 'medium',
            'risk_multiplier': 0.8,  # Conservative default
            'confidence_boost': -0.05
        }
    
    config = MARKET_CATEGORIES[category]
    volatility = config['volatility']
    
    return {
        'max_exposure': config['max_exposure'],
        'max_trades_per_day': config['max_trades_per_day'],
        'volatility': volatility,
        'risk_multiplier': VOLATILITY_RISK_MULTIPLIERS.get(volatility, 1.0),
        'confidence_boost': config['confidence_boost']
    }


def analyze_market_text(market_text: str) -> Dict:
    """
    Full analysis of market text with category, risk, and recommendations
    
    Args:
        market_text: Market question text
        
    Returns:
        Complete analysis dict
    """
    
    category, confidence, metadata = detect_market_category(market_text)
    risk_limits = get_category_risk_limits(category)
    
    # Generate trading recommendations
    recommendations = []
    
    if risk_limits['volatility'] in ['very_high', 'extreme']:
        recommendations.append("HIGH RISK: Consider paper trading first")
    
    if risk_limits['confidence_boost'] < -0.10:
        recommendations.append("LOW PREDICTABILITY: Use smaller positions")
        
    if risk_limits['max_trades_per_day'] == 1:
        recommendations.append("SINGLE SHOT: Only one trade per day in this category")
        
    if category == 'legal':
        recommendations.append("RESEARCH EDGE: Legal outcomes often have good precedents")
        
    if category in ['nfl', 'nba']:
        recommendations.append("DATA ADVANTAGE: Sports have rich statistical models")
        
    return {
        'category': category,
        'detection_confidence': round(confidence, 3),
        'volatility': risk_limits['volatility'],
        'risk_multiplier': risk_limits['risk_multiplier'],
        'max_exposure': risk_limits['max_exposure'],
        'max_daily_trades': risk_limits['max_trades_per_day'],
        'confidence_adjustment': risk_limits['confidence_boost'],
        'matched_keywords': metadata.get('matched_keywords', []),
        'recommendations': recommendations,
        'all_category_scores': metadata.get('all_matches', {}),
        'trading_style': 'CONSERVATIVE' if risk_limits['risk_multiplier'] < 0.8 else 
                        'AGGRESSIVE' if risk_limits['risk_multiplier'] > 1.1 else 'BALANCED'
    }


# Testing
def test_market_categorization():
    """Test the market categorization system"""
    
    print("="*60)
    print("ENHANCED MARKET CATEGORY DETECTION TESTS")
    print(f"Total Categories: {len(MARKET_CATEGORIES)}")
    print("="*60)
    
    test_markets = [
        # Original tests
        "Will the Patriots win the Super Bowl in 2026?",
        "Will Bitcoin hit $150,000 by year end?",
        "Will Trump deport more than 1 million people in 2025?",
        "Will Elon Musk buy another social media company?",
        "Will M3GAN 2.0 be the #1 movie on Netflix this week?",
        "Will the Fed raise interest rates in March?",
        "Will OpenAI release GPT-5 before June?",
        "Will there be a major hurricane in Florida this year?",
        "Will the Supreme Court rule in favor of abortion rights?",
        "Will silver hit $190 per ounce by February?",
        
        # New category tests
        "Will China invade Taiwan by end of 2026?",
        "Will Meta (META) close above $760 on February 2?",
        "Will Billie Eilish win Record of the Year at the Grammy Awards?",
        "Will SpaceX successfully land on Mars in 2026?",
        "Will the Nobel Peace Prize go to UNRWA in 2026?",
        "Will the FDA approve a new COVID vaccine?",
        "Will Tesla release autonomous driving this year?",
        "Will Starbucks open 500 new stores globally?",
        "Will there be a major cyberattack on US infrastructure?",
        "Will university enrollment decrease by 10% this year?",
        "Will renewable energy reach 50% of US power generation?",
        "Will the Olympics be held in Paris successfully?",
        "Will Trump pardon Ghislaine Maxwell by end of 2026?",
        "Will global temperature increase by 1.00°C to 1.04°C in January?",
        "Will the Pope make a major announcement about church doctrine?"
    ]
    
    for i, market in enumerate(test_markets, 1):
        print(f"\n{i}. {market}")
        analysis = analyze_market_text(market)
        
        print(f"   Category: {analysis['category']} ({analysis['detection_confidence']:.2f} confidence)")
        print(f"   Volatility: {analysis['volatility']} | Risk Multiplier: {analysis['risk_multiplier']:.1f}x")
        print(f"   Max Exposure: ${analysis['max_exposure']} | Max Daily: {analysis['max_daily_trades']}")
        print(f"   Style: {analysis['trading_style']}")
        
        if analysis['recommendations']:
            print(f"   Recommendations: {', '.join(analysis['recommendations'])}")


if __name__ == '__main__':
    test_market_categorization()