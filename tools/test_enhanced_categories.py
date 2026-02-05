#!/usr/bin/env python3
"""
Test the enhanced market categories with real market data from the system
"""

import json
from pathlib import Path
from market_categories import analyze_market_text

# Load real market data
REPO_ROOT = Path(__file__).parent.parent
fast_markets_file = REPO_ROOT / 'fast_markets.json'
trade_targets_file = REPO_ROOT / 'trade_targets.json'

def test_with_real_data():
    print("="*80)
    print("ENHANCED MARKET CATEGORIZATION - REAL DATA TEST")
    print("="*80)
    
    # Test with fast_markets.json
    try:
        with open(fast_markets_file, 'r') as f:
            fast_markets = json.load(f)
        
        print("\nFAST MARKETS DATA:")
        print("-" * 50)
        for i, market in enumerate(fast_markets[:5], 1):  # Test first 5
            question = market.get('q', 'Unknown')
            analysis = analyze_market_text(question)
            
            print(f"{i}. {question}")
            print(f"   → {analysis['category']} ({analysis['detection_confidence']:.2f}) | {analysis['trading_style']}")
            print(f"   → Max: ${analysis['max_exposure']} | Daily: {analysis['max_daily_trades']} | Vol: {analysis['volatility']}")
            if analysis['recommendations']:
                print(f"   → {analysis['recommendations'][0]}")
            print()
    
    except Exception as e:
        print(f"Error loading fast markets: {e}")
    
    # Test with trade_targets.json
    try:
        with open(trade_targets_file, 'r') as f:
            trade_targets = json.load(f)
        
        print("\nTRADE TARGETS DATA:")
        print("-" * 50)
        for i, target in enumerate(trade_targets[:5], 1):  # Test first 5
            question = target.get('question', 'Unknown')
            analysis = analyze_market_text(question)
            
            print(f"{i}. {question}")
            print(f"   → {analysis['category']} ({analysis['detection_confidence']:.2f}) | {analysis['trading_style']}")
            print(f"   → Max: ${analysis['max_exposure']} | Daily: {analysis['max_daily_trades']} | Vol: {analysis['volatility']}")
            if analysis['recommendations']:
                print(f"   → {analysis['recommendations'][0]}")
            print()
    
    except Exception as e:
        print(f"Error loading trade targets: {e}")

def category_coverage_analysis():
    """Analyze coverage across different categories"""
    print("\nCATEGORY COVERAGE ANALYSIS:")
    print("-" * 50)
    
    # Combine all real market data
    all_questions = []
    
    try:
        with open(fast_markets_file, 'r') as f:
            fast_markets = json.load(f)
            all_questions.extend([m.get('q', '') for m in fast_markets])
    except:
        pass
        
    try:
        with open(trade_targets_file, 'r') as f:
            trade_targets = json.load(f)
            all_questions.extend([t.get('question', '') for t in trade_targets])
    except:
        pass
    
    # Categorize all questions
    category_counts = {}
    for question in all_questions:
        if question:
            analysis = analyze_market_text(question)
            category = analysis['category']
            confidence = analysis['detection_confidence']
            if category not in category_counts:
                category_counts[category] = []
            category_counts[category].append((question[:60] + "...", confidence))
    
    # Show coverage
    print(f"Total Questions Analyzed: {len(all_questions)}")
    print(f"Categories Detected: {len(category_counts)}")
    print()
    
    for category, items in sorted(category_counts.items(), key=lambda x: len(x[1]), reverse=True):
        avg_confidence = sum(conf for _, conf in items) / len(items)
        print(f"{category:20s}: {len(items):2d} markets (avg conf: {avg_confidence:.2f})")
        # Show top example
        best_example = max(items, key=lambda x: x[1])
        print(f"   Best: {best_example[0]} ({best_example[1]:.2f})")
        print()

if __name__ == '__main__':
    test_with_real_data()
    category_coverage_analysis()