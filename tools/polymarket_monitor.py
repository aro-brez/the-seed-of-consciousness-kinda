#!/usr/bin/env python3
"""
Polymarket Real-Time Monitor
Continuously scans for high-conviction trades
Integrates with Grok analysis for automated recommendations
"""

import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Paths
REPO_ROOT = Path(__file__).parent.parent
SIGNALS_PATH = REPO_ROOT / 'BRAIN' / 'INTEL' / 'polymarket_live_signals.json'
TRADES_LOG = REPO_ROOT / 'BRAIN' / 'INTEL' / 'polymarket_trades' / 'recommendations.json'

class PolymarketMonitor:
    """Real-time monitoring of Polymarket opportunities"""

    def __init__(self):
        self.base_url = "https://clob.polymarket.com"
        self.signals = []

    def get_hot_markets(self, min_volume=50000):
        """Get high-volume markets"""
        try:
            # Polymarket API - markets endpoint
            response = requests.get(f"{self.base_url}/markets")
            data = response.json()
            markets = data.get('data', []) if isinstance(data, dict) else data

            # Filter by volume
            hot = [m for m in markets if m.get('volume', 0) > min_volume]

            # Sort by volume
            hot.sort(key=lambda x: x.get('volume', 0), reverse=True)

            return hot[:20]  # Top 20

        except Exception as e:
            print(f"Error fetching markets: {e}")
            return []

    def analyze_market(self, market):
        """Quick analysis of a market"""
        analysis = {
            'market_id': market.get('condition_id'),
            'question': market.get('question'),
            'volume_24h': market.get('volume'),
            'current_price_yes': market.get('outcomes', [{}])[0].get('price'),
            'liquidity': market.get('liquidity'),
            'end_date': market.get('end_date_iso'),
            'timestamp': datetime.now().isoformat()
        }

        # Quick filters
        analysis['high_confidence'] = False
        analysis['reasoning'] = []

        # High volume = liquid
        if analysis['volume_24h'] > 100000:
            analysis['reasoning'].append("High liquidity")

        # Near-term resolution
        # TODO: Parse end_date and check if <48 hours

        # Price inefficiency
        price = analysis['current_price_yes']
        if price and (price < 0.3 or price > 0.7):
            analysis['reasoning'].append(f"Strong directional bias: {price:.2f}")

        if len(analysis['reasoning']) >= 2:
            analysis['high_confidence'] = True

        return analysis

    def scan_opportunities(self):
        """Full scan of all opportunities"""
        print("🔍 Scanning Polymarket for opportunities...")

        markets = self.get_hot_markets()
        opportunities = []

        for market in markets:
            analysis = self.analyze_market(market)
            if analysis['high_confidence']:
                opportunities.append(analysis)
                print(f"✅ Found: {analysis['question'][:60]}...")

        # Save
        with open(SIGNALS_PATH, 'w') as f:
            json.dump(opportunities, f, indent=2)

        print(f"📊 Found {len(opportunities)} high-confidence opportunities")
        return opportunities

    def monitor_forever(self, interval=300):
        """Continuous monitoring every 5 minutes"""
        print("🚀 Starting continuous Polymarket monitoring")
        print(f"Scan interval: {interval}s")

        while True:
            try:
                self.scan_opportunities()
                print(f"⏰ Next scan in {interval}s...")
                time.sleep(interval)
            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(60)

def quick_scan():
    """Run one quick scan"""
    monitor = PolymarketMonitor()
    return monitor.scan_opportunities()

if __name__ == '__main__':
    monitor = PolymarketMonitor()
    monitor.monitor_forever(interval=300)  # Every 5 min
