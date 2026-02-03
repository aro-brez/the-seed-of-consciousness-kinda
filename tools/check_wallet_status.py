#!/usr/bin/env python3
"""
Check wallet status on Polymarket
"""
import json
import httpx
from datetime import datetime

def check_wallet():
    print("=" * 60)
    print("WALLET STATUS CHECK")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Load credentials
    creds_path = '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
    with open(creds_path) as f:
        creds = json.load(f)

    polymarket = creds.get('polymarket', {})
    address = polymarket.get('address')

    print(f"Wallet Address: {address}")
    print()

    # Check CLOB client methods
    from py_clob_client.client import ClobClient

    client = ClobClient(
        host="https://clob.polymarket.com",
        key=polymarket.get('private_key'),
        chain_id=137,
    )

    # Derive credentials
    api_creds = client.derive_api_key()
    client.set_api_creds(api_creds)

    print("Available ClobClient methods:")
    methods = [m for m in dir(client) if not m.startswith('_') and callable(getattr(client, m))]
    for m in sorted(methods):
        print(f"  - {m}")

    print()

    # Try to get balance
    print("Checking balance methods...")
    if hasattr(client, 'get_balance'):
        try:
            balance = client.get_balance()
            print(f"Balance: {balance}")
        except Exception as e:
            print(f"get_balance error: {e}")

    if hasattr(client, 'get_allowances'):
        try:
            allowances = client.get_allowances()
            print(f"Allowances: {allowances}")
        except Exception as e:
            print(f"get_allowances error: {e}")

    # Check on-chain balance using Polygon API
    print()
    print("Checking on-chain USDC balance (Polygon)...")

    # USDC contract on Polygon
    usdc_address = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"

    # Use Polygonscan API (free tier)
    polygon_api = f"https://api.polygonscan.com/api?module=account&action=tokenbalance&contractaddress={usdc_address}&address={address}&tag=latest"

    try:
        resp = httpx.get(polygon_api)
        data = resp.json()
        if data.get('status') == '1':
            balance_raw = int(data.get('result', 0))
            balance_usdc = balance_raw / 1e6  # USDC has 6 decimals
            print(f"On-chain USDC balance: ${balance_usdc:,.2f}")
        else:
            print(f"Polygonscan API error: {data}")
    except Exception as e:
        print(f"Polygonscan error: {e}")

    # Check MATIC balance for gas
    print()
    print("Checking MATIC balance (for gas)...")
    matic_api = f"https://api.polygonscan.com/api?module=account&action=balance&address={address}&tag=latest"

    try:
        resp = httpx.get(matic_api)
        data = resp.json()
        if data.get('status') == '1':
            balance_raw = int(data.get('result', 0))
            balance_matic = balance_raw / 1e18  # MATIC has 18 decimals
            print(f"MATIC balance: {balance_matic:.4f} MATIC")
        else:
            print(f"Polygonscan API error: {data}")
    except Exception as e:
        print(f"Polygonscan error: {e}")

    # Summary
    print()
    print("=" * 60)
    print("DIAGNOSIS")
    print("=" * 60)
    print()
    print("To trade on Polymarket, you need:")
    print("1. USDC in your Polygon wallet")
    print("2. MATIC for gas fees")
    print("3. USDC deposited to Polymarket exchange")
    print("4. Allowance set for CLOB contract")
    print()
    print("If you have USDC but see 'not enough balance/allowance':")
    print("- You may need to deposit USDC via Polymarket's deposit function")
    print("- Or approve the CTF Exchange contract to spend USDC")
    print()
    print("CTF Exchange address: 0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E")

if __name__ == '__main__':
    check_wallet()
