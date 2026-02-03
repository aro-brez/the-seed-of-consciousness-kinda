#!/usr/bin/env python3
"""Get detailed market info for specific IDs"""
import httpx
import json

TARGET_IDS = [
    '521944',  # DOGE < $50B
    '537490',  # Tariffs > $250B
    '549874',  # Rob Jetten PM
    '527079',  # GTA 6 > $100
    '517310',  # Trump deportation < 250K
]

def get_market_details():
    url = 'https://gamma-api.polymarket.com/markets'
    params = {
        'active': 'true',
        'closed': 'false',
        'limit': 500
    }

    response = httpx.get(url, params=params)
    markets = response.json()

    print('=== TARGET MARKET DETAILS FOR TRADING ===')
    print()

    for target_id in TARGET_IDS:
        match = next((m for m in markets if str(m.get('id')) == str(target_id)), None)
        if match:
            print(f"{'='*60}")
            print(f"MARKET ID: {match.get('id')}")
            print(f"Question: {match.get('question')}")
            print(f"Slug: {match.get('market_slug')}")
            print(f"Condition ID: {match.get('condition_id')}")
            print(f"Volume: ${float(match.get('volume', 0) or 0):,.0f}")
            print(f"Liquidity: ${float(match.get('liquidity', 0) or 0):,.0f}")
            print(f"Active: {match.get('active')}")
            print(f"Closed: {match.get('closed')}")
            print(f"End Date: {match.get('end_date_iso')}")
            print()
            print("TOKENS:")
            for t in match.get('tokens', []):
                outcome = t.get('outcome', 'Unknown')
                price = float(t.get('price', 0) or 0)
                token_id = t.get('token_id', 'N/A')
                winner = t.get('winner', False)
                print(f"  {outcome}:")
                print(f"    Price: ${price:.4f} ({price*100:.2f}%)")
                print(f"    Token ID: {token_id}")
                print(f"    Winner: {winner}")

                # Calculate potential returns
                if price > 0 and price < 1:
                    potential_return = (1 / price) - 1
                    print(f"    Potential Return: {potential_return*100:.0f}x if YES wins")
            print()
        else:
            print(f"Market {target_id} not found in active markets")
            print()

if __name__ == '__main__':
    get_market_details()
