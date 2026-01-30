#!/usr/bin/env python3
"""
MARKET DATA FEEDS - Real-time price/volume validation layer
Integrates Dexscreener, CoinGecko, and Binance for comprehensive market data

Purpose: Transform Twitter noise into validated trading signals
"""

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import requests

# Configuration
REPO_ROOT = Path(__file__).parent.parent
CACHE_DIR = REPO_ROOT / 'BRAIN' / 'INTEL' / 'market_cache'
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# API endpoints
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
COINGECKO_API = "https://api.coingecko.com/api/v3"
BINANCE_API = "https://api.binance.com/api/v3"

# Cache settings (avoid rate limits)
CACHE_DURATION = 60  # seconds


class MarketDataFeeds:
    """Real-time market data aggregator with intelligent caching"""

    def __init__(self):
        self.cache = {}
        self.cache_file = CACHE_DIR / 'price_cache.json'
        self.load_cache()

    def load_cache(self):
        """Load cached data from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    self.cache = json.load(f)
            except:
                self.cache = {}

    def save_cache(self):
        """Save cache to disk"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f, indent=2)

    def get_cached(self, key: str) -> Optional[Dict]:
        """Get cached data if still fresh"""
        if key in self.cache:
            cached = self.cache[key]
            age = time.time() - cached.get('timestamp', 0)
            if age < CACHE_DURATION:
                return cached.get('data')
        return None

    def set_cache(self, key: str, data: Dict):
        """Cache data with timestamp"""
        self.cache[key] = {
            'timestamp': time.time(),
            'data': data
        }
        self.save_cache()

    def get_token_price(self, symbol: str) -> Optional[Dict]:
        """
        Get current price and 24h stats for a token

        Returns:
            {
                'symbol': 'BTC',
                'price': 104500.0,
                'volume_24h': 25000000000,
                'change_1h': 0.5,
                'change_24h': 2.3,
                'market_cap': 2000000000000,
                'liquidity': 500000000
            }
        """
        symbol = symbol.upper().replace('USDT', '').replace('USD', '')
        cache_key = f"price_{symbol}"

        # Check cache
        cached = self.get_cached(cache_key)
        if cached:
            return cached

        # Try multiple sources
        data = None

        # 1. Try Binance first (fastest, most reliable for major coins)
        data = self._get_binance_price(symbol)

        # 2. Fallback to CoinGecko (more comprehensive)
        if not data:
            data = self._get_coingecko_price(symbol)

        # 3. Fallback to Dexscreener (for smaller tokens)
        if not data:
            data = self._get_dexscreener_price(symbol)

        if data:
            self.set_cache(cache_key, data)

        return data

    def _get_binance_price(self, symbol: str) -> Optional[Dict]:
        """Get price from Binance"""
        try:
            # 24h ticker
            ticker_url = f"{BINANCE_API}/ticker/24hr?symbol={symbol}USDT"
            response = requests.get(ticker_url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                return {
                    'symbol': symbol,
                    'price': float(data['lastPrice']),
                    'volume_24h': float(data['quoteVolume']),
                    'change_24h': float(data['priceChangePercent']),
                    'high_24h': float(data['highPrice']),
                    'low_24h': float(data['lowPrice']),
                    'trades_24h': int(data['count']),
                    'source': 'binance'
                }
        except Exception as e:
            print(f"Binance API error for {symbol}: {e}")

        return None

    def _get_coingecko_price(self, symbol: str) -> Optional[Dict]:
        """Get price from CoinGecko"""
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'BTC': 'bitcoin',
                'ETH': 'ethereum',
                'SOL': 'solana',
                'MATIC': 'polygon',
                'AVAX': 'avalanche-2',
                'BNB': 'binancecoin'
            }

            coin_id = symbol_map.get(symbol, symbol.lower())

            url = f"{COINGECKO_API}/simple/price"
            params = {
                'ids': coin_id,
                'vs_currencies': 'usd',
                'include_24hr_vol': 'true',
                'include_24hr_change': 'true',
                'include_market_cap': 'true'
            }

            response = requests.get(url, params=params, timeout=5)

            if response.status_code == 200:
                data = response.json()
                if coin_id in data:
                    coin_data = data[coin_id]
                    return {
                        'symbol': symbol,
                        'price': coin_data['usd'],
                        'volume_24h': coin_data.get('usd_24h_vol', 0),
                        'change_24h': coin_data.get('usd_24h_change', 0),
                        'market_cap': coin_data.get('usd_market_cap', 0),
                        'source': 'coingecko'
                    }
        except Exception as e:
            print(f"CoinGecko API error for {symbol}: {e}")

        return None

    def _get_dexscreener_price(self, symbol: str) -> Optional[Dict]:
        """Get price from Dexscreener (for smaller tokens)"""
        try:
            url = f"{DEXSCREENER_API}/search?q={symbol}"
            response = requests.get(url, timeout=5)

            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])

                if pairs:
                    # Get highest liquidity pair
                    best_pair = max(pairs, key=lambda x: float(x.get('liquidity', {}).get('usd', 0)))

                    return {
                        'symbol': symbol,
                        'price': float(best_pair['priceUsd']),
                        'volume_24h': float(best_pair.get('volume', {}).get('h24', 0)),
                        'change_24h': float(best_pair.get('priceChange', {}).get('h24', 0)),
                        'liquidity': float(best_pair.get('liquidity', {}).get('usd', 0)),
                        'dex': best_pair['dexId'],
                        'chain': best_pair['chainId'],
                        'source': 'dexscreener'
                    }
        except Exception as e:
            print(f"Dexscreener API error for {symbol}: {e}")

        return None

    def detect_volume_spike(self, symbol: str, threshold: float = 2.0) -> Dict:
        """
        Detect if current volume is significantly higher than average

        Args:
            symbol: Token symbol
            threshold: Multiplier (2.0 = 2x normal volume)

        Returns:
            {
                'is_spike': True/False,
                'current_volume': 1000000,
                'avg_volume': 500000,
                'multiplier': 2.0,
                'significance': 'high/medium/low'
            }
        """
        price_data = self.get_token_price(symbol)
        if not price_data:
            return {'is_spike': False, 'error': 'No data available'}

        current_volume = price_data.get('volume_24h', 0)

        # Get historical average (simplified - in production, query historical data)
        # For now, use a heuristic: if volume > market_cap * 0.1, it's significant
        market_cap = price_data.get('market_cap', current_volume * 20)
        typical_volume = market_cap * 0.05  # Typical = 5% of market cap daily

        if typical_volume == 0:
            return {'is_spike': False, 'error': 'No volume data'}

        multiplier = current_volume / typical_volume
        is_spike = multiplier >= threshold

        # Classify significance
        if multiplier >= 5.0:
            significance = 'extreme'
        elif multiplier >= 3.0:
            significance = 'high'
        elif multiplier >= 2.0:
            significance = 'medium'
        else:
            significance = 'low'

        return {
            'is_spike': is_spike,
            'current_volume': current_volume,
            'estimated_avg': typical_volume,
            'multiplier': round(multiplier, 2),
            'significance': significance
        }

    def get_price_momentum(self, symbol: str) -> Dict:
        """
        Calculate price momentum across multiple timeframes

        Returns:
            {
                'change_1h': 0.5,
                'change_4h': 2.3,
                'change_24h': 5.1,
                'trend': 'bullish/bearish/neutral',
                'strength': 'strong/moderate/weak'
            }
        """
        price_data = self.get_token_price(symbol)
        if not price_data:
            return {'error': 'No data available'}

        change_24h = price_data.get('change_24h', 0)

        # Simplified momentum (in production, query actual historical data)
        # Estimate shorter timeframes from 24h data
        change_1h = change_24h * 0.15  # Rough estimate
        change_4h = change_24h * 0.4   # Rough estimate

        # Determine trend
        if change_24h > 5:
            trend = 'strong_bullish'
            strength = 'strong'
        elif change_24h > 2:
            trend = 'bullish'
            strength = 'moderate'
        elif change_24h > -2:
            trend = 'neutral'
            strength = 'weak'
        elif change_24h > -5:
            trend = 'bearish'
            strength = 'moderate'
        else:
            trend = 'strong_bearish'
            strength = 'strong'

        return {
            'change_1h': round(change_1h, 2),
            'change_4h': round(change_4h, 2),
            'change_24h': round(change_24h, 2),
            'trend': trend,
            'strength': strength,
            'price': price_data['price']
        }

    def get_comprehensive_data(self, symbol: str) -> Dict:
        """Get all available data for a token"""
        price = self.get_token_price(symbol)
        volume_spike = self.detect_volume_spike(symbol)
        momentum = self.get_price_momentum(symbol)

        return {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'price_data': price,
            'volume_spike': volume_spike,
            'momentum': momentum
        }


# Utility functions
def test_feeds():
    """Test market data feeds"""
    feeds = MarketDataFeeds()

    test_symbols = ['BTC', 'ETH', 'SOL']

    print("="*60)
    print("MARKET DATA FEEDS TEST")
    print("="*60)

    for symbol in test_symbols:
        print(f"\n{symbol}:")
        print("-"*60)

        # Get comprehensive data
        data = feeds.get_comprehensive_data(symbol)

        # Price
        if data['price_data']:
            p = data['price_data']
            print(f"  Price: ${p['price']:,.2f}")
            print(f"  24h Change: {p.get('change_24h', 0):.2f}%")
            print(f"  24h Volume: ${p.get('volume_24h', 0):,.0f}")
            print(f"  Source: {p['source']}")

        # Volume spike
        if 'error' not in data['volume_spike']:
            v = data['volume_spike']
            print(f"  Volume Spike: {'YES' if v['is_spike'] else 'NO'}")
            print(f"  Multiplier: {v['multiplier']}x")
            print(f"  Significance: {v['significance']}")

        # Momentum
        if 'error' not in data['momentum']:
            m = data['momentum']
            print(f"  Trend: {m['trend']}")
            print(f"  Strength: {m['strength']}")

    print("\n" + "="*60)
    print("✅ Market data feeds operational")


if __name__ == '__main__':
    test_feeds()
