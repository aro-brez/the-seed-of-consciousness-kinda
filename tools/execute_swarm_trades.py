#!/usr/bin/env python3
"""
Execute trades based on swarm recommendations
SØWL - February 1, 2026

SWARM PORTFOLIO ALLOCATION ($1,000 from $1,410 capital):
1. Tariffs > $250B: YES @ $0.022 = 45x return - $300
2. DOGE > $50B: NO on "< $50B" @ $0.028 = 36x return - $400
3. GTA 6 > $100: YES @ $0.0095 = 105x return - $100

Keeping $410 reserve for fees and additional opportunities.
"""
import os
import sys
import json
from datetime import datetime

# Add path to py_clob_client
sys.path.insert(0, '/Users/aaronnosbisch/REPOS/seed/polymarket-mcp-server/venv/lib/python3.13/site-packages')

def execute_trades():
    print("=" * 60)
    print("SWARM TRADE EXECUTION")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    print()

    # Trading parameters from swarm analysis
    trades = [
        {
            'name': 'Tariffs > $250B',
            'question': 'Will tariffs generate >$250b in 2025?',
            'side': 'BUY',
            'outcome': 'Yes',
            'token_id': '7935869750973568991063634796432742901043529564448603464914559127943627115874',
            'condition_id': '0x53700c2b2fa65e0a3775c757d0c705be4bee8c265c49d283ef50a0dfb3bf8894',
            'price': 0.022,
            'amount_usd': 300,
            'potential_return': '45x',
            'thesis': 'Trump 25% tariffs on Canada/Mexico, 10% China. US imports ~$3.5T. Even 10% avg = $350B revenue.'
        },
        {
            'name': 'DOGE > $50B',
            'question': 'Will Elon and DOGE cut less than $50b in federal spending in 2025?',
            'side': 'BUY',
            'outcome': 'No',  # Betting NO means DOGE WILL cut more than $50B
            'token_id': '58656358377246279051017109359677190749228949103591068167284263961542487110215',
            'condition_id': '0xc0e6b917320a47228fb96e3b5ae0e5c93773a5ae2662ae4e1f37807cfe47ce98',
            'price': 0.028,
            'amount_usd': 400,
            'potential_return': '36x',
            'thesis': 'IRS alone identified $200B+ waste. DOGE has exec backing + Elon motivation. $50B is easy target.'
        },
        {
            'name': 'GTA 6 > $100',
            'question': 'Will GTA 6 cost $100+?',
            'side': 'BUY',
            'outcome': 'Yes',
            'token_id': '28946595841244317705636126646676849578876740730186646421280828201004700559420',
            'condition_id': '0xae5584fbb57f23c1c608d544b656f23d8bf12340cef70811cf31bb0cb4fc2115',
            'price': 0.0095,
            'amount_usd': 100,
            'potential_return': '105x',
            'thesis': 'Take-Two telegraphed premium pricing. Industry trend $70-80. $100 possible for mega-launch.'
        }
    ]

    total_allocation = sum(t['amount_usd'] for t in trades)
    print(f"Total allocation: ${total_allocation}")
    print(f"Reserve: ${1410 - total_allocation} for fees/opportunities")
    print()

    # Load credentials
    creds_path = '/Users/aaronnosbisch/REPOS/seed/BRAIN/MEMORY/secure/api_keys.json'
    with open(creds_path) as f:
        creds = json.load(f)

    polymarket = creds.get('polymarket', {})
    private_key = polymarket.get('private_key')
    address = polymarket.get('address')

    if not private_key or not address:
        print("ERROR: Missing Polymarket credentials")
        return False

    print("Credentials loaded successfully")
    print(f"Trading address: {address}")
    print()

    # Attempt to import py_clob_client
    try:
        from py_clob_client.client import ClobClient
        from py_clob_client.clob_types import ApiCreds, OrderArgs, OrderType
        print("py_clob_client imported successfully")
    except ImportError as e:
        print(f"ERROR importing py_clob_client: {e}")
        print("Attempting alternative import...")
        try:
            # Try system-wide install
            import subprocess
            result = subprocess.run(['pip3', 'show', 'py-clob-client'], capture_output=True, text=True)
            print(f"pip3 show: {result.stdout}")
        except:
            pass
        return False

    # Initialize client
    print()
    print("Initializing CLOB client...")
    try:
        client = ClobClient(
            host="https://clob.polymarket.com",
            key=private_key,
            chain_id=137,  # Polygon mainnet
        )
        print("CLOB client initialized")

        # Derive API credentials
        print("Deriving API credentials...")
        api_creds = client.derive_api_key()
        client.set_api_creds(api_creds)
        print(f"API Key: {api_creds.api_key[:10]}...")
        print()

    except Exception as e:
        print(f"ERROR initializing client: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Execute trades
    executed_trades = []
    for trade in trades:
        print(f"{'='*60}")
        print(f"EXECUTING: {trade['name']}")
        print(f"Question: {trade['question']}")
        print(f"Outcome: {trade['outcome']}")
        print(f"Price: ${trade['price']:.4f}")
        print(f"Amount: ${trade['amount_usd']}")
        print(f"Potential: {trade['potential_return']}")
        print(f"Thesis: {trade['thesis']}")
        print()

        try:
            # Calculate number of shares
            shares = trade['amount_usd'] / trade['price']
            print(f"Shares to buy: {shares:.2f}")

            # Create order
            order = OrderArgs(
                token_id=trade['token_id'],
                price=trade['price'],
                size=shares,
                side='BUY',
            )

            print("Submitting order...")
            result = client.create_order(order)
            print(f"Order result: {result}")

            executed_trades.append({
                'trade': trade,
                'result': result,
                'success': True
            })

        except Exception as e:
            print(f"ERROR executing trade: {e}")
            import traceback
            traceback.print_exc()
            executed_trades.append({
                'trade': trade,
                'error': str(e),
                'success': False
            })

        print()

    # Summary
    print("=" * 60)
    print("EXECUTION SUMMARY")
    print("=" * 60)

    successful = [t for t in executed_trades if t['success']]
    failed = [t for t in executed_trades if not t['success']]

    print(f"Successful: {len(successful)}/{len(trades)}")
    print(f"Failed: {len(failed)}/{len(trades)}")

    if successful:
        print()
        print("Successful trades:")
        for t in successful:
            print(f"  - {t['trade']['name']}: ${t['trade']['amount_usd']}")

    if failed:
        print()
        print("Failed trades:")
        for t in failed:
            print(f"  - {t['trade']['name']}: {t.get('error', 'Unknown error')}")

    # Save execution log
    log_path = '/Users/aaronnosbisch/REPOS/seed/logs/trade_execution.log'
    with open(log_path, 'a') as f:
        f.write(f"\n{'='*60}\n")
        f.write(f"Execution Time: {datetime.now().isoformat()}\n")
        f.write(f"Trades Attempted: {len(trades)}\n")
        f.write(f"Successful: {len(successful)}\n")
        f.write(f"Failed: {len(failed)}\n")
        f.write(json.dumps(executed_trades, indent=2, default=str))
        f.write("\n")

    return len(successful) > 0

if __name__ == '__main__':
    success = execute_trades()
    sys.exit(0 if success else 1)
