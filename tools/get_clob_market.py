#!/usr/bin/env python3
"""Get CLOB market details with token IDs for trading"""
import httpx
import json

# Market slugs/questions to search for
SEARCH_TERMS = [
    'DOGE',
    'tariff 250',
    'GTA 6',
    'Jetten',
    'deportation',
]

def search_clob():
    clob_url = 'https://clob.polymarket.com/markets'
    gamma_url = 'https://gamma-api.polymarket.com/markets'

    # First get gamma markets
    gamma_resp = httpx.get(gamma_url, params={'active': 'true', 'closed': 'false', 'limit': 500})
    gamma_markets = gamma_resp.json()

    print('=== CLOB MARKET DETAILS FOR TRADING ===')
    print()

    # Search for our targets
    for term in SEARCH_TERMS:
        matches = [m for m in gamma_markets if term.lower() in m.get('question', '').lower()]
        if matches:
            print(f"=== {term.upper()} ===")
            for m in matches[:2]:
                print(f"Question: {m.get('question')}")
                print(f"ID: {m.get('id')}")

                # Try to get CLOB data
                clob_token_ids = m.get('clob_token_ids')
                if clob_token_ids:
                    print(f"CLOB Token IDs: {clob_token_ids}")

                outcomes_prices = m.get('outcomePrices')
                if outcomes_prices:
                    print(f"Outcome Prices: {outcomes_prices}")

                # Get best bid/ask
                best_bid = m.get('bestBid')
                best_ask = m.get('bestAsk')
                if best_bid:
                    print(f"Best Bid: {best_bid}")
                if best_ask:
                    print(f"Best Ask: {best_ask}")

                # Print all keys to see what's available
                print(f"Available keys: {list(m.keys())[:20]}...")
                print()

    # Also try direct CLOB API
    print('=== DIRECT CLOB API ===')
    try:
        clob_resp = httpx.get(clob_url, params={'next_cursor': ''}, timeout=10)
        if clob_resp.status_code == 200:
            clob_data = clob_resp.json()
            if clob_data:
                print(f"CLOB markets found: {len(clob_data)}")
                if isinstance(clob_data, list) and len(clob_data) > 0:
                    print(f"Sample CLOB market keys: {list(clob_data[0].keys())}")
        else:
            print(f"CLOB API returned: {clob_resp.status_code}")
    except Exception as e:
        print(f"CLOB API error: {e}")

if __name__ == '__main__':
    search_clob()
