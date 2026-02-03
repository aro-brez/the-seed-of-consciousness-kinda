#!/usr/bin/env python3
"""
(◉) AGGRESSIVE SCANNER - 10x/day target
Continuous SEED cycles with web research
"""

import asyncio
import json
import httpx
from datetime import datetime
from pathlib import Path

LOG = '/Users/aaronnosbisch/REPOS/seed/logs/aggressive_scanner.log'
CREDS = '/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'

def log(msg, level='INFO'):
    ts = datetime.now().isoformat()
    line = f"[{ts}] [{level}] {msg}"
    print(line)
    with open(LOG, 'a') as f:
        f.write(line + '\n')

async def scan_asymmetric_opportunities():
    """Find markets with 10x+ potential"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            'https://gamma-api.polymarket.com/markets',
            params={'active': 'true', 'closed': 'false', 'limit': 300}
        )
        markets = resp.json()
    
    opportunities = []
    for m in markets:
        prices = m.get('outcomePrices', '[]')
        if isinstance(prices, str):
            prices = json.loads(prices)
        if not prices or len(prices) < 2:
            continue
            
        yes_price = float(prices[0]) if prices[0] else 0
        volume = float(m.get('volume', 0) or 0)
        liquidity = float(m.get('liquidity', 0) or 0)
        
        # 10x+ opportunities: YES price < 0.10 (10:1 payout)
        if 0.001 < yes_price < 0.10 and volume > 10000:
            potential = 1 / yes_price
            opportunities.append({
                'question': m.get('question', '')[:60],
                'yes_price': yes_price,
                'potential': f'{potential:.0f}x',
                'volume': volume,
                'liquidity': liquidity,
            })
    
    # Sort by potential
    opportunities.sort(key=lambda x: float(x['potential'].replace('x','')), reverse=True)
    return opportunities[:20]

async def scan_momentum():
    """Track price changes between scans"""
    # Would compare current vs previous scan
    pass

async def run_cycle(cycle_num):
    """One SEED cycle"""
    log(f"(◉) CYCLE {cycle_num} START")
    
    # PERCEIVE - Find 10x opportunities
    opps = await scan_asymmetric_opportunities()
    log(f"Found {len(opps)} asymmetric opportunities (10x+)")
    
    # Log top 5
    for o in opps[:5]:
        log(f"  {o['potential']}: {o['question']} @ ${o['yes_price']:.3f}")
    
    log(f"(◉) CYCLE {cycle_num} END")
    return opps

async def main():
    log("(◉) AGGRESSIVE SCANNER STARTING - 10x/day target")
    cycle = 0
    while True:
        try:
            cycle += 1
            await run_cycle(cycle)
            await asyncio.sleep(30)  # 30 second cycles
        except KeyboardInterrupt:
            break
        except Exception as e:
            log(f"Error: {e}", 'ERROR')
            await asyncio.sleep(30)

if __name__ == '__main__':
    asyncio.run(main())
