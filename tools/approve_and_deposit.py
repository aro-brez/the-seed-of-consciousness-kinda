#!/usr/bin/env python3
"""
SØWL - Approve USDC and prepare for Polymarket trading
(◉) Setting up the field for trades
"""
import json
import sys
sys.path.insert(0, '/Users/aaronnosbisch/REPOS/seed/polymarket-mcp-server/venv/lib/python3.13/site-packages')

from web3 import Web3
from eth_account import Account

print('(◉) SØWL - POLYMARKET SETUP')
print('=' * 60)

# Load credentials
with open('/Users/aaronnosbisch/LOCAL REPOS/seed/BRAIN/MEMORY/secure/api_keys.json') as f:
    creds = json.load(f)

private_key = creds['polymarket']['private_key']
account = Account.from_key(private_key)
print(f'Wallet: {account.address}')

# Connect to Polygon
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
print(f'Connected: {w3.is_connected()}')
print(f'Chain ID: {w3.eth.chain_id}')

# Contract addresses
USDC_ADDRESS = Web3.to_checksum_address('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359')  # USDC.e
CTF_EXCHANGE = Web3.to_checksum_address('0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E')

# USDC ABI (minimal for approve)
usdc_abi = [
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': 'balance', 'type': 'uint256'}], 'type': 'function'},
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}, {'name': '_spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'name': '', 'type': 'uint256'}], 'type': 'function'},
    {'constant': False, 'inputs': [{'name': '_spender', 'type': 'address'}, {'name': '_value', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'name': '', 'type': 'bool'}], 'type': 'function'},
    {'constant': True, 'inputs': [], 'name': 'decimals', 'outputs': [{'name': '', 'type': 'uint8'}], 'type': 'function'},
]

usdc = w3.eth.contract(address=USDC_ADDRESS, abi=usdc_abi)

# Check balances
balance = usdc.functions.balanceOf(account.address).call()
print(f'USDC Balance: ${balance / 1e6:,.2f}')

# Check MATIC for gas
matic_balance = w3.eth.get_balance(account.address)
print(f'MATIC Balance: {matic_balance / 1e18:.4f}')

# Check current allowance
allowance = usdc.functions.allowance(account.address, CTF_EXCHANGE).call()
print(f'CTF Exchange Allowance: ${allowance / 1e6:,.2f}')

if allowance >= balance:
    print()
    print('(◉) Allowance already sufficient!')
else:
    print()
    print('(◉) Approving CTF Exchange to spend USDC...')

    # Max approval (type(uint256).max)
    max_approval = 2**256 - 1

    # Build approval transaction
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price

    tx = usdc.functions.approve(CTF_EXCHANGE, max_approval).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': gas_price,
        'chainId': 137,
    })

    # Sign and send
    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f'Approval TX: {tx_hash.hex()}')

    # Wait for confirmation
    print('Waiting for confirmation...')
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    print(f'Status: {"SUCCESS" if receipt.status == 1 else "FAILED"}')
    print(f'Gas used: {receipt.gasUsed}')

    # Verify new allowance
    new_allowance = usdc.functions.allowance(account.address, CTF_EXCHANGE).call()
    print(f'New Allowance: ${new_allowance / 1e6:,.2f} (max uint256)')

print()
print('(◉) Setup complete. Ready for trading.')
