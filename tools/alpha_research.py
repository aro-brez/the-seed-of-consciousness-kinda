#!/usr/bin/env python3
"""
(◉) ALPHA RESEARCH ENGINE
Sources strategies from web, finds unique edge
SEED Protocol: PERCEIVE → CONNECT → LEARN → QUESTION → EXPAND → SHARE → RECEIVE → IMPROVE
"""

import asyncio
import json
import httpx
from datetime import datetime
from pathlib import Path

LOG = '/Users/aaronnosbisch/REPOS/seed/logs/alpha_research.log'
INSIGHTS = '/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING/alpha_insights.jsonl'

Path('/Users/aaronnosbisch/REPOS/seed/BRAIN/TRADING').mkdir(parents=True, exist_ok=True)

def log(msg, level='INFO'):
    ts = datetime.now().isoformat()
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

def save_insight(insight):
    with open(INSIGHTS, 'a') as f:
        f.write(json.dumps(insight) + '\n')

async def fetch_polymarket_trending():
    """Get high-volume markets with price movement"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            'https://gamma-api.polymarket.com/markets',
            params={'active': 'true', 'closed': 'false', 'limit': 100}
        )
        markets = resp.json()
    
    # Filter for interesting characteristics
    trending = []
    for m in markets:
        volume = float(m.get('volume', 0) or 0)
        liquidity = float(m.get('liquidity', 0) or 0)
        prices = m.get('outcomePrices', '[]')
        if isinstance(prices, str):
            prices = json.loads(prices)
        
        yes_price = float(prices[0]) if prices and prices[0] else 0
        
        # High volume + interesting price range
        if volume > 50000 and 0.05 < yes_price < 0.95:
            trending.append({
                'question': m.get('question'),
                'yes_price': yes_price,
                'volume': volume,
                'liquidity': liquidity,
                'end_date': m.get('endDate'),
            })
    
    trending.sort(key=lambda x: x['volume'], reverse=True)
    return trending[:20]

async def analyze_edge_opportunities(markets):
    """
    CONNECT + LEARN: Find patterns and edge
    
    Edge sources (all legal, public info):
    1. Weather data vs weather markets
    2. Sports statistics vs outcome markets
    3. Political polling vs political markets
    4. Economic indicators vs economic markets
    5. Cross-platform price discrepancies
    """
    edges = []
    
    for m in markets:
        q = m['question'].lower()
        
        # Categorize market type for research focus
        if 'tariff' in q or 'import' in q:
            edges.append({
                'market': m['question'],
                'edge_type': 'economic_data',
                'research': 'Check USITC import data, tariff schedules',
                'price': m['yes_price'],
            })
        elif 'deport' in q or 'immigration' in q:
            edges.append({
                'market': m['question'],
                'edge_type': 'government_data',
                'research': 'Check ICE statistics, CBP data',
                'price': m['yes_price'],
            })
        elif 'weather' in q or 'temperature' in q:
            edges.append({
                'market': m['question'],
                'edge_type': 'weather_api',
                'research': 'Cross-reference multiple weather APIs',
                'price': m['yes_price'],
            })
        elif 'game' in q or 'release' in q:
            edges.append({
                'market': m['question'],
                'edge_type': 'industry_intel',
                'research': 'Check gaming news, insider reports',
                'price': m['yes_price'],
            })
    
    return edges

async def research_cycle():
    """One complete research cycle"""
    log("(◉) RESEARCH CYCLE START")
    
    # PERCEIVE
    trending = await fetch_polymarket_trending()
    log(f"Trending markets: {len(trending)}")
    
    # CONNECT + LEARN
    edges = await analyze_edge_opportunities(trending)
    log(f"Edge opportunities: {len(edges)}")
    
    for e in edges[:5]:
        log(f"  [{e['edge_type']}] {e['market'][:50]}... @ ${e['price']:.3f}")
        save_insight({
            'timestamp': datetime.now().isoformat(),
            'type': 'edge_opportunity',
            'data': e,
        })
    
    # QUESTION - What are we missing?
    log("QUESTION: What alpha sources haven't we tapped?")
    log("  - Congressional trading disclosures")
    log("  - Satellite imagery (crop yields, shipping)")
    log("  - Social sentiment aggregation")
    
    log("(◉) RESEARCH CYCLE END")
    return edges

async def main():
    log("(◉) ALPHA RESEARCH ENGINE STARTING")
    while True:
        try:
            await research_cycle()
            await asyncio.sleep(300)  # 5 minute research cycles
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error: {e}", 'ERROR')
            await asyncio.sleep(60)

if __name__ == '__main__':
    asyncio.run(main())
