#!/usr/bin/env python3
"""
SØWL - Swap USDC.e to native USDC via Uniswap V3
"""
import json
import time
from web3 import Web3
from eth_account import Account

print('(◉) USDC.e -> USDC SWAP')
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

# Addresses - CORRECTED
# 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174 = USDC.e (bridged)
# 0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359 = Native USDC
USDC_E = Web3.to_checksum_address('0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174')
USDC_NATIVE = Web3.to_checksum_address('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359')

# Uniswap V3 SwapRouter on Polygon
SWAP_ROUTER = Web3.to_checksum_address('0xE592427A0AEce92De3Edee1F18E0157C05861564')

# Amount to swap (leaving some for fees)
AMOUNT = int(1000 * 1e6)  # $1000 USDC.e - conservative, leave buffer

# ERC20 ABI
erc20_abi = [
    {'constant': True, 'inputs': [{'name': 'a', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': '', 'type': 'uint256'}], 'type': 'function'},
    {'constant': True, 'inputs': [{'name': 'a', 'type': 'address'}, {'name': 'b', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'name': '', 'type': 'uint256'}], 'type': 'function'},
    {'constant': False, 'inputs': [{'name': 'a', 'type': 'address'}, {'name': 'b', 'type': 'uint256'}], 'name': 'approve', 'outputs': [{'name': '', 'type': 'bool'}], 'type': 'function'},
]

usdc_e = w3.eth.contract(address=USDC_E, abi=erc20_abi)
usdc_native = w3.eth.contract(address=USDC_NATIVE, abi=erc20_abi)

# Check balances
bal_e = usdc_e.functions.balanceOf(account.address).call()
bal_native = usdc_native.functions.balanceOf(account.address).call()
print(f'USDC.e: ${bal_e/1e6:,.2f}')
print(f'Native USDC: ${bal_native/1e6:,.2f}')

# Check/Set approval for swap router
allowance = usdc_e.functions.allowance(account.address, SWAP_ROUTER).call()
print(f'Router allowance: ${allowance/1e6:,.2f}')

if allowance < AMOUNT:
    print('Approving swap router...')
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = int(w3.eth.gas_price * 1.5)

    tx = usdc_e.functions.approve(SWAP_ROUTER, 2**256-1).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 80000,
        'gasPrice': gas_price,
        'chainId': 137,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f'Approval TX: {tx_hash.hex()}')

    print('Waiting for confirmation...')
    time.sleep(20)

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f'Approval status: {"SUCCESS" if receipt.status == 1 else "FAILED"}')
    except:
        print('Checking later...')

    time.sleep(5)

# Uniswap V3 SwapRouter ABI (exactInputSingle)
swap_router_abi = [
    {
        'inputs': [{
            'components': [
                {'name': 'tokenIn', 'type': 'address'},
                {'name': 'tokenOut', 'type': 'address'},
                {'name': 'fee', 'type': 'uint24'},
                {'name': 'recipient', 'type': 'address'},
                {'name': 'deadline', 'type': 'uint256'},
                {'name': 'amountIn', 'type': 'uint256'},
                {'name': 'amountOutMinimum', 'type': 'uint256'},
                {'name': 'sqrtPriceLimitX96', 'type': 'uint160'}
            ],
            'name': 'params',
            'type': 'tuple'
        }],
        'name': 'exactInputSingle',
        'outputs': [{'name': 'amountOut', 'type': 'uint256'}],
        'stateMutability': 'payable',
        'type': 'function'
    }
]

router = w3.eth.contract(address=SWAP_ROUTER, abi=swap_router_abi)

# Swap parameters
# Fee tier: 100 = 0.01%, 500 = 0.05%, 3000 = 0.3%
# USDC.e <-> USDC should have very low slippage, try 100 (0.01%) fee tier
params = {
    'tokenIn': USDC_E,
    'tokenOut': USDC_NATIVE,
    'fee': 100,  # 0.01% pool
    'recipient': account.address,
    'deadline': int(time.time()) + 1800,  # 30 min
    'amountIn': AMOUNT,
    'amountOutMinimum': int(AMOUNT * 0.995),  # 0.5% slippage tolerance
    'sqrtPriceLimitX96': 0,
}

print()
print(f'Swapping ${AMOUNT/1e6:,.2f} USDC.e to USDC...')

nonce = w3.eth.get_transaction_count(account.address)
gas_price = int(w3.eth.gas_price * 1.5)

try:
    tx = router.functions.exactInputSingle(params).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 300000,
        'gasPrice': gas_price,
        'chainId': 137,
        'value': 0,
    })

    signed = account.sign_transaction(tx)
    tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
    print(f'Swap TX: {tx_hash.hex()}')

    print('Waiting for confirmation...')
    time.sleep(30)

    try:
        receipt = w3.eth.get_transaction_receipt(tx_hash)
        print(f'Status: {"SUCCESS" if receipt.status == 1 else "FAILED"}')
        print(f'Gas used: {receipt.gasUsed}')
    except Exception as e:
        print(f'Receipt check error: {e}')

    # Check new balances
    time.sleep(5)
    bal_e = usdc_e.functions.balanceOf(account.address).call()
    bal_native = usdc_native.functions.balanceOf(account.address).call()
    print()
    print('NEW BALANCES:')
    print(f'USDC.e: ${bal_e/1e6:,.2f}')
    print(f'Native USDC: ${bal_native/1e6:,.2f}')

except Exception as e:
    print(f'Swap error: {e}')
    import traceback
    traceback.print_exc()
