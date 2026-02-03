#!/usr/bin/env python3
"""Get all trading parameters for swarm opportunities"""
import httpx
import json

def get_trading_params():
    gamma_url = 'https://gamma-api.polymarket.com/markets'

    gamma_resp = httpx.get(gamma_url, params={'active': 'true', 'closed': 'false', 'limit': 500})
    markets = gamma_resp.json()

    # Target markets from swarm synthesis
    targets = {
        'DOGE < $50B': 'DOGE cut less than $50',
        'DOGE $50-100B': 'DOGE cut between $50',
        'Tariffs > $250B': 'tariff',
        'GTA 6 > $100': 'GTA 6 cost',
        'Jetten PM': 'Jetten',
        'Deportation < 250K': 'deport less than 250',
    }

    print('=== TRADING PARAMETERS FOR SWARM OPPORTUNITIES ===')
    print()

    for name, search in targets.items():
        matches = [m for m in markets if search.lower() in m.get('question', '').lower()]
        if matches:
            m = matches[0]
            print(f"=== {name} ===")
            print(f"Question: {m.get('question')}")
            print(f"Condition ID: {m.get('conditionId')}")
            print(f"Slug: {m.get('slug')}")

            outcomes = m.get('outcomes', [])
            prices = m.get('outcomePrices', [])
            tokens = m.get('clobTokenIds', [])

            print(f"Outcomes: {outcomes}")
            print(f"Prices: {prices}")
            print(f"CLOB Token IDs: {tokens}")
            print(f"Best Bid: {m.get('bestBid')}")
            print(f"Best Ask: {m.get('bestAsk')}")
            print(f"Liquidity: ${float(m.get('liquidity', 0) or 0):,.0f}")
            print(f"Volume: ${float(m.get('volume', 0) or 0):,.0f}")
            print()

            # Calculate implied probabilities and potential returns
            if prices and isinstance(prices, list):
                for i, outcome in enumerate(outcomes):
                    if i < len(prices):
                        price_str = prices[i]
                        try:
                            price = float(price_str)
                            if price > 0:
                                implied_prob = price * 100
                                potential_return = (1 / price) - 1
                                print(f"  {outcome}:")
                                print(f"    Price: ${price:.4f}")
                                print(f"    Implied: {implied_prob:.1f}%")
                                print(f"    Return if wins: {potential_return:.0f}x")
                                if i < len(tokens):
                                    print(f"    Token ID: {tokens[i]}")
                        except (ValueError, TypeError):
                            print(f"  {outcome}: price parsing error")
            print()

if __name__ == '__main__':
    get_trading_params()
