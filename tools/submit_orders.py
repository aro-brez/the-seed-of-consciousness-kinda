#!/usr/bin/env python3
"""
Submit signed orders to Polymarket
"""
import json
import sys
from datetime import datetime

def submit_orders():
    print("=" * 60)
    print("SWARM TRADE SUBMISSION")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Load credentials
    creds_path = '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
    with open(creds_path) as f:
        creds = json.load(f)

    polymarket = creds.get('polymarket', {})
    private_key = polymarket.get('private_key')
    address = polymarket.get('address')

    from py_clob_client.client import ClobClient
    from py_clob_client.clob_types import OrderArgs, OrderType

    # Initialize client
    print("Initializing CLOB client...")
    client = ClobClient(
        host="https://clob.polymarket.com",
        key=private_key,
        chain_id=137,
    )

    # Derive and set API credentials
    print("Deriving API credentials...")
    api_creds = client.derive_api_key()
    client.set_api_creds(api_creds)
    print(f"API Key: {api_creds.api_key[:10]}...")

    # Check if we have any open orders
    print()
    print("Checking open orders...")
    try:
        open_orders = client.get_orders()
        print(f"Open orders: {len(open_orders) if open_orders else 0}")
        if open_orders:
            for order in open_orders[:5]:
                print(f"  - {order}")
    except Exception as e:
        print(f"Error getting orders: {e}")

    # Check balance
    print()
    print("Checking balance...")
    try:
        # Get allowances
        allowances = client.get_allowances()
        print(f"Allowances: {allowances}")
    except Exception as e:
        print(f"Error getting allowances: {e}")

    # Try to create and post order using the correct method
    print()
    print("Testing order creation with post_order...")

    trades = [
        {
            'name': 'Tariffs > $250B',
            'token_id': '7935869750973568991063634796432742901043529564448603464914559127943627115874',
            'price': 0.022,
            'size': 100,  # Start smaller for test
        },
    ]

    for trade in trades:
        print(f"\nAttempting: {trade['name']}")
        try:
            # Create order args
            order_args = OrderArgs(
                token_id=trade['token_id'],
                price=trade['price'],
                size=trade['size'],
                side='BUY',
            )

            # Try create_and_post_order if available
            if hasattr(client, 'create_and_post_order'):
                print("Using create_and_post_order...")
                result = client.create_and_post_order(order_args)
                print(f"Result: {result}")
            else:
                # Create order then post
                print("Creating signed order...")
                signed = client.create_order(order_args)
                print(f"Signed: {signed}")

                # Try to post it
                if hasattr(client, 'post_order'):
                    print("Posting order...")
                    result = client.post_order(signed)
                    print(f"Post result: {result}")
                else:
                    print("Available methods:", [m for m in dir(client) if not m.startswith('_')])

        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    submit_orders()
