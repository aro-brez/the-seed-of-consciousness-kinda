#!/usr/bin/env python3
"""
Check Polymarket balance and allowance
"""
import json
from datetime import datetime

def check_balance():
    print("=" * 60)
    print("POLYMARKET BALANCE CHECK")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Load credentials
    creds_path = '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
    with open(creds_path) as f:
        creds = json.load(f)

    polymarket = creds.get('polymarket', {})

    from py_clob_client.client import ClobClient

    client = ClobClient(
        host="https://clob.polymarket.com",
        key=polymarket.get('private_key'),
        chain_id=137,
    )

    # Derive credentials
    api_creds = client.derive_api_key()
    client.set_api_creds(api_creds)

    print(f"Wallet: {polymarket.get('address')}")
    print()

    # Check balance and allowance
    print("Checking balance and allowance...")
    try:
        result = client.get_balance_allowance()
        print(f"Balance/Allowance: {result}")
    except Exception as e:
        print(f"Error: {e}")

    # Check positions
    print()
    print("Checking open orders...")
    try:
        orders = client.get_orders()
        print(f"Open orders: {len(orders) if orders else 0}")
        if orders:
            for o in orders[:5]:
                print(f"  - {o}")
    except Exception as e:
        print(f"Error: {e}")

    # Check trades
    print()
    print("Checking recent trades...")
    try:
        trades = client.get_trades()
        print(f"Trades: {len(trades) if trades else 0}")
        if trades:
            for t in trades[:5]:
                print(f"  - {t}")
    except Exception as e:
        print(f"Error: {e}")

    # Get fee rate
    print()
    print("Checking fee rate...")
    try:
        fee = client.get_fee_rate_bps()
        print(f"Fee rate: {fee} bps ({float(fee)/100 if fee else 0}%)")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    check_balance()
