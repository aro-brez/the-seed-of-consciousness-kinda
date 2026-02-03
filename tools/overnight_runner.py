#!/usr/bin/env python3
"""
OVERNIGHT AUTONOMOUS RUNNER
Keeps trading systems alive and monitors for opportunities
"""

import asyncio
import json
import time
import logging
from datetime import datetime, timedelta
from pathlib import Path
import subprocess
import sys

# Setup logging
LOG_DIR = Path(__file__).parent.parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'overnight_runner.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

REPO_ROOT = Path(__file__).parent.parent

async def check_polymarket_daemon():
    """Ensure Polymarket trading daemon is running"""
    try:
        result = subprocess.run(
            ['pgrep', '-f', 'autonomous_trader.py'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            logger.warning("Polymarket daemon not running - restarting...")
            subprocess.Popen(
                [sys.executable, '-u', str(REPO_ROOT / 'tools/autonomous_trader.py'), '--capital', '383'],
                stdout=open(LOG_DIR / 'autonomous_trader.log', 'a'),
                stderr=subprocess.STDOUT,
                start_new_session=True
            )
            logger.info("Polymarket daemon restarted")
            return "RESTARTED"
        return "RUNNING"
    except Exception as e:
        logger.error(f"Error checking daemon: {e}")
        return "ERROR"

async def check_solana_balance():
    """Check Solana wallet balance"""
    import httpx
    
    address = "Fg3MYxfcJ8tgQEyhVS9c6EJAc9Kyg5jjm8tY93hJeaBf"
    
    try:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                "https://api.mainnet-beta.solana.com",
                json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]},
                timeout=15
            )
            if resp.status_code == 200:
                data = resp.json()
                lamports = data.get('result', {}).get('value', 0)
                return lamports / 1e9
    except Exception as e:
        logger.error(f"Solana check error: {e}")
    return 0

async def check_polygon_balance():
    """Check Polygon wallet balance"""
    import httpx
    
    address = "0xAED6D39e30F675Fb00514D8Ccb3ea01588d6a669"
    
    try:
        async with httpx.AsyncClient() as http:
            # USDC.e + USDC
            total = 0
            for contract in ["0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"]:
                data = f"0x70a08231000000000000000000000000{address[2:]}"
                resp = await http.post(
                    "https://polygon-rpc.com",
                    json={"jsonrpc": "2.0", "method": "eth_call", 
                          "params": [{"to": contract, "data": data}, "latest"], "id": 1},
                    timeout=10
                )
                if resp.status_code == 200:
                    result = resp.json().get("result", "0x0")
                    total += int(result, 16) / 1e6
            return total
    except Exception as e:
        logger.error(f"Polygon check error: {e}")
    return 0

async def run_overnight():
    """Main overnight loop"""
    logger.info("=" * 60)
    logger.info("OVERNIGHT AUTONOMOUS RUNNER STARTING")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    end_time = start_time + timedelta(hours=12)
    
    cycle = 0
    
    while datetime.now() < end_time:
        cycle += 1
        logger.info(f"\n--- Cycle {cycle} at {datetime.now().strftime('%H:%M:%S')} ---")
        
        # Check and restart Polymarket daemon if needed
        daemon_status = await check_polymarket_daemon()
        logger.info(f"Polymarket daemon: {daemon_status}")
        
        # Check balances
        sol_balance = await check_solana_balance()
        usdc_balance = await check_polygon_balance()
        
        logger.info(f"SOL balance: {sol_balance:.4f} (~${sol_balance * 100:.2f})")
        logger.info(f"USDC balance: ${usdc_balance:.2f}")
        
        # Log total
        total = (sol_balance * 100) + usdc_balance
        logger.info(f"TOTAL LIQUID: ${total:.2f}")
        
        # Save state
        state = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'sol_balance': sol_balance,
            'usdc_balance': usdc_balance,
            'total_liquid': total,
            'daemon_status': daemon_status
        }
        
        state_file = REPO_ROOT / 'BRAIN/TRADING/overnight_state/runner_state.json'
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Wait 5 minutes between checks
        await asyncio.sleep(300)
    
    logger.info("=" * 60)
    logger.info("OVERNIGHT RUNNER COMPLETE")
    logger.info("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_overnight())
