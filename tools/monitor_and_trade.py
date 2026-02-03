#!/usr/bin/env python3
"""
SØWL - Monitor for USDC arrival and execute swarm trades
(◉)ACT(◉)
"""
import httpx
import json
import time
from datetime import datetime

PHANTOM_WALLET = '0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669'
USDC_CONTRACT = '0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359'  # USDC.e on Polygon
RPC_URL = 'https://polygon-rpc.com'

def check_usdc_balance():
    """Check USDC balance on Phantom wallet"""
    data = '0x70a08231' + '000000000000000000000000' + PHANTOM_WALLET[2:].lower()
    payload = {
        'jsonrpc': '2.0',
        'method': 'eth_call',
        'params': [{'to': USDC_CONTRACT, 'data': data}, 'latest'],
        'id': 1
    }
    resp = httpx.post(RPC_URL, json=payload, timeout=10)
    result = resp.json().get('result', '0x0')
    return int(result, 16) / 1e6

def main():
    print("=" * 60)
    print("(◉) SØWL AWAKENING - MONITORING FOR FUNDS")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()
    print(f"Watching wallet: {PHANTOM_WALLET}")
    print("Waiting for $1,410 USDC to arrive...")
    print()

    initial_balance = check_usdc_balance()
    print(f"Initial balance: ${initial_balance:,.2f}")

    target_balance = initial_balance + 1400  # Expecting ~$1,410 more

    # Monitor for 5 minutes
    for i in range(60):  # 60 checks, 5 seconds each = 5 minutes
        time.sleep(5)
        current = check_usdc_balance()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Balance: ${current:,.2f}")

        if current >= target_balance:
            print()
            print("=" * 60)
            print("(◉) FUNDS ARRIVED! EXECUTING SWARM TRADES")
            print("=" * 60)
            return current

    print()
    print("Timeout - funds not yet arrived")
    return check_usdc_balance()

if __name__ == '__main__':
    final_balance = main()
    print(f"\nFinal balance: ${final_balance:,.2f}")
