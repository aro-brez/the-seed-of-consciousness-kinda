#!/usr/bin/env python3
"""Search for swarm-identified Polymarket opportunities"""
import httpx
import json

def search_markets():
    url = 'https://gamma-api.polymarket.com/markets'
    params = {
        'active': 'true',
        'closed': 'false',
        'limit': 200
    }

    response = httpx.get(url, params=params)
    markets = response.json()

    print('=== SEARCHING FOR SWARM-IDENTIFIED OPPORTUNITIES ===')
    print(f'Total active markets: {len(markets)}')
    print()

    # Keywords from swarm synthesis
    keywords = ['DOGE', 'tariff', 'deportation', 'immigration', 'MegaETH', 'Jetten', 'GTA', 'MicroStrategy', 'MSTR', 'Super Bowl', 'weather', 'temperature']

    found_opportunities = []

    for keyword in keywords:
        matches = [m for m in markets if keyword.lower() in m.get('question', '').lower() or keyword.lower() in m.get('description', '').lower()]
        if matches:
            print(f'=== {keyword.upper()} MARKETS ({len(matches)} found) ===')
            for m in matches[:2]:
                print(f"Question: {m.get('question', 'N/A')}")
                print(f"ID: {m.get('id', 'N/A')}")
                print(f"Condition ID: {m.get('condition_id', 'N/A')}")
                vol = m.get('volume', 0)
                liq = m.get('liquidity', 0)
                print(f"Volume: ${float(vol) if vol else 0:,.0f}")
                print(f"Liquidity: ${float(liq) if liq else 0:,.0f}")
                tokens = m.get('tokens', [])
                for t in tokens:
                    outcome = t.get('outcome', 'Unknown')
                    price = t.get('price', 0)
                    token_id = t.get('token_id', 'N/A')
                    print(f"  {outcome}: ${price:.4f} (token: {token_id[:20]}...)")
                print()
                found_opportunities.append(m)

    # Also search for low-probability high-conviction plays
    print('=== LOW PROBABILITY (<5c) HIGH VOLUME OPPORTUNITIES ===')
    for m in markets:
        tokens = m.get('tokens', [])
        for t in tokens:
            price = float(t.get('price', 1) or 1)
            vol = float(m.get('volume', 0) or 0)
            if price < 0.05 and vol > 100000:
                print(f"Question: {m.get('question', 'N/A')}")
                print(f"  Outcome: {t.get('outcome')} @ ${price:.4f}")
                print(f"  Volume: ${vol:,.0f}")
                print(f"  Token ID: {t.get('token_id', 'N/A')}")
                print()

    return found_opportunities

if __name__ == '__main__':
    search_markets()
