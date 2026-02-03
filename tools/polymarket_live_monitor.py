#!/usr/bin/env python3
"""
Polymarket Live Monitor - Real-Time Market Tracking
Polls Polymarket API every 60 seconds for market data and opportunities.
Logs all findings to files for review.

NO TRADES EXECUTED - Monitoring only.
"""

import json
import time
import requests
import sys
from datetime import datetime
from pathlib import Path

# Force output flushing
sys.stdout.reconfigure(line_buffering=True)

# Paths
REPO_ROOT = Path(__file__).parent.parent
INTEL_DIR = REPO_ROOT / 'BRAIN' / 'INTEL'
SIGNALS_FILE = INTEL_DIR / 'polymarket_signals.json'
LOG_FILE = REPO_ROOT / 'logs' / 'polymarket_live_monitor.log'

# Ensure directories exist
INTEL_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log(msg):
    """Log to both stdout and file"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def get_markets():
    """Fetch markets from Gamma API"""
    try:
        response = requests.get(
            'https://gamma-api.polymarket.com/markets',
            params={'limit': 50, 'closed': 'false'},
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        log(f"ERROR fetching markets: {e}")
        return []

def analyze_market(market):
    """Analyze a market for opportunities"""
    try:
        question = market.get('question', 'Unknown')[:70]
        
        # Parse prices
        prices_raw = market.get('outcomePrices', '[]')
        if isinstance(prices_raw, str):
            prices = json.loads(prices_raw)
        else:
            prices = prices_raw or []
        
        yes_price = float(prices[0]) if prices else 0
        no_price = float(prices[1]) if len(prices) > 1 else 1 - yes_price
        
        volume_24h = float(market.get('volume24hr', 0) or 0)
        liquidity = float(market.get('liquidity', 0) or 0)
        
        return {
            'question': question,
            'yes_price': yes_price,
            'no_price': no_price,
            'volume_24h': volume_24h,
            'liquidity': liquidity,
            'id': market.get('id'),
            'slug': market.get('slug')
        }
    except Exception as e:
        return None

def scan_opportunities():
    """Scan for high-value opportunities"""
    log("Scanning Polymarket for opportunities...")
    
    markets = get_markets()
    if not markets:
        log("No markets retrieved")
        return []
    
    log(f"Retrieved {len(markets)} markets")
    
    opportunities = []
    high_volume = []
    
    for market in markets:
        analysis = analyze_market(market)
        if not analysis:
            continue
        
        # Track high volume markets
        if analysis['volume_24h'] > 50000:
            high_volume.append(analysis)
        
        # Identify opportunities based on various criteria
        signals = []
        
        # Strong directional bias with good liquidity
        if 0.1 < analysis['yes_price'] < 0.3 and analysis['liquidity'] > 10000:
            signals.append(f"Low YES ({analysis['yes_price']*100:.1f}%) - potential value")
        elif 0.7 < analysis['yes_price'] < 0.9 and analysis['liquidity'] > 10000:
            signals.append(f"High YES ({analysis['yes_price']*100:.1f}%) - potential value")
        
        # High volume activity
        if analysis['volume_24h'] > 100000:
            signals.append(f"High volume (${analysis['volume_24h']:,.0f})")
        
        if signals:
            analysis['signals'] = signals
            opportunities.append(analysis)
    
    # Log findings
    if high_volume:
        log(f"\n=== HIGH VOLUME MARKETS ({len(high_volume)}) ===")
        for m in sorted(high_volume, key=lambda x: x['volume_24h'], reverse=True)[:10]:
            log(f"  {m['question']}...")
            log(f"    YES: {m['yes_price']*100:.1f}%  |  Vol: ${m['volume_24h']:,.0f}  |  Liq: ${m['liquidity']:,.0f}")
    
    if opportunities:
        log(f"\n=== OPPORTUNITIES ({len(opportunities)}) ===")
        for opp in opportunities[:10]:
            log(f"  {opp['question']}...")
            log(f"    {', '.join(opp['signals'])}")
    
    # Save to file
    output = {
        'timestamp': datetime.now().isoformat(),
        'total_markets': len(markets),
        'high_volume_count': len(high_volume),
        'opportunities_count': len(opportunities),
        'high_volume': high_volume[:20],
        'opportunities': opportunities
    }
    
    with open(SIGNALS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    log(f"Saved signals to {SIGNALS_FILE}")
    return opportunities

def monitor_loop(interval=60):
    """Main monitoring loop"""
    log("=" * 60)
    log("POLYMARKET LIVE MONITOR STARTED")
    log("=" * 60)
    log(f"Scan interval: {interval} seconds")
    log(f"Log file: {LOG_FILE}")
    log(f"Signals file: {SIGNALS_FILE}")
    log("NO TRADES WILL BE EXECUTED - Monitoring only")
    log("=" * 60)
    
    scan_count = 0
    
    while True:
        try:
            scan_count += 1
            log(f"\n--- Scan #{scan_count} ---")
            scan_opportunities()
            log(f"Next scan in {interval}s...")
            time.sleep(interval)
        except KeyboardInterrupt:
            log("\nMonitor stopped by user")
            break
        except Exception as e:
            log(f"ERROR in scan: {e}")
            time.sleep(30)

if __name__ == '__main__':
    monitor_loop(interval=60)
