#!/usr/bin/env python3
"""
Polymarket WebSocket Client - Real-Time Market Data
Connects to Polymarket CLOB WebSocket for live price updates, order book data, and trade execution.
Streams all data to JSONL for analysis by trading loop.

Built: January 29, 2026
Status: Production-ready with auto-reconnection
"""

import json
import time
import threading
from datetime import datetime
from pathlib import Path
from websocket import WebSocketApp
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/aaronnosbisch/REPOS/seed/logs/polymarket_websocket.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).parent.parent
FEED_FILE = REPO_ROOT / 'BRAIN' / 'INTEL' / 'polymarket_live_feed.jsonl'
STATE_FILE = REPO_ROOT / 'BRAIN' / 'INTEL' / 'polymarket_websocket_state.json'

# Ensure directories exist
FEED_FILE.parent.mkdir(parents=True, exist_ok=True)

# WebSocket endpoints
CLOB_WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
RTDS_WS_URL = "wss://ws-live-data.polymarket.com"


class PolymarketWebSocketClient:
    """
    Production-ready WebSocket client for Polymarket real-time data.

    Features:
    - Auto-reconnection on disconnect
    - Heartbeat/ping to keep connection alive
    - Streams all data to JSONL
    - Tracks connection state
    - Handles errors gracefully
    """

    def __init__(self, asset_ids=None, use_rtds=False):
        """
        Initialize WebSocket client

        Args:
            asset_ids: List of token IDs to subscribe to (None = subscribe to all)
            use_rtds: Use RTDS endpoint instead of CLOB (default: False)
        """
        self.asset_ids = asset_ids or []
        self.use_rtds = use_rtds
        self.url = RTDS_WS_URL if use_rtds else CLOB_WS_URL
        self.ws = None
        self.running = False
        self.ping_thread = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # seconds

        # Stats
        self.messages_received = 0
        self.last_message_time = None
        self.connection_start_time = None

        self.load_state()

    def load_state(self):
        """Load previous state if exists"""
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE) as f:
                    state = json.load(f)
                    logger.info(f"📊 Loaded state: {state.get('messages_received', 0)} messages received")
            except Exception as e:
                logger.warning(f"Could not load state: {e}")

    def save_state(self):
        """Save current state"""
        state = {
            'messages_received': self.messages_received,
            'last_message_time': self.last_message_time,
            'connection_start_time': self.connection_start_time,
            'reconnect_attempts': self.reconnect_attempts,
            'asset_ids': self.asset_ids
        }
        try:
            with open(STATE_FILE, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Could not save state: {e}")

    def write_to_feed(self, data):
        """Write message to JSONL feed"""
        try:
            entry = {
                'timestamp': datetime.now().isoformat(),
                'received_at': time.time(),
                'data': data
            }
            with open(FEED_FILE, 'a') as f:
                f.write(json.dumps(entry) + '\n')

            self.messages_received += 1
            self.last_message_time = datetime.now().isoformat()

            # Save state every 100 messages
            if self.messages_received % 100 == 0:
                self.save_state()
                logger.info(f"📊 {self.messages_received} messages received")

        except Exception as e:
            logger.error(f"Error writing to feed: {e}")

    def on_open(self, ws):
        """Called when WebSocket connection opens"""
        logger.info(f"✅ Connected to Polymarket WebSocket: {self.url}")
        self.connection_start_time = datetime.now().isoformat()
        self.reconnect_attempts = 0

        # Send subscription message
        if not self.use_rtds:
            # CLOB subscription format - try multiple formats

            # First, try the simple "market" command format from docs
            try:
                ws.send("market")
                logger.info("📡 Sent simple 'market' subscription")
            except Exception as e:
                logger.error(f"Error sending simple subscription: {e}")

            # Also try JSON format with specific markets
            if self.asset_ids:
                subscription = {
                    "type": "market",
                    "assets_ids": self.asset_ids
                }
                try:
                    ws.send(json.dumps(subscription))
                    logger.info(f"📡 Also sent JSON subscription for {len(self.asset_ids)} markets")
                except Exception as e:
                    logger.error(f"Error sending JSON subscription: {e}")
            else:
                # If no specific markets, get hot markets automatically
                # Limit to 25 markets to avoid overwhelming the connection
                logger.info("📊 No markets specified, fetching top 25 hot markets...")
                hot_markets = get_hot_markets(limit=25)
                if hot_markets:
                    # Further limit to first 50 asset IDs (25 markets ≈ 50 tokens)
                    self.asset_ids = hot_markets[:50]
                    subscription = {
                        "type": "market",
                        "assets_ids": self.asset_ids
                    }
                    try:
                        ws.send(json.dumps(subscription))
                        logger.info(f"📡 Sent JSON subscription for {len(self.asset_ids)} tokens")
                    except Exception as e:
                        logger.error(f"Error sending JSON subscription: {e}")
        else:
            # RTDS subscription format
            subscription = {
                "type": "subscribe",
                "topic": "activity",  # Can be: activity, comments, rfq, crypto_prices
                "message_type": "*"  # Subscribe to all message types
            }
            ws.send(json.dumps(subscription))
            logger.info("📡 Subscribed to RTDS activity feed")

        # Start heartbeat thread
        self.start_ping_thread()

    def on_message(self, ws, message):
        """Called when message received"""
        try:
            # Handle ping/pong
            if message == "PONG":
                return

            # Parse JSON message
            data = json.loads(message)
            event_type = data.get('event_type', 'unknown')

            # Log interesting events
            if event_type == 'book':
                asset_id = data.get('asset_id', 'unknown')
                bids = len(data.get('bids', []))
                asks = len(data.get('asks', []))
                logger.debug(f"📖 ORDER BOOK: {asset_id} - {bids} bids, {asks} asks")

            elif event_type == 'price_change':
                changes = data.get('price_changes', [])
                for change in changes:
                    asset_id = change.get('asset_id', 'unknown')
                    best_bid = change.get('best_bid')
                    best_ask = change.get('best_ask')
                    logger.info(f"💰 PRICE CHANGE: {asset_id} - Bid: {best_bid} Ask: {best_ask}")

            elif event_type == 'last_trade_price':
                price = data.get('price')
                size = data.get('size')
                side = data.get('side')
                logger.info(f"📈 TRADE: {side} {size} @ {price}")

            # Write all messages to feed
            self.write_to_feed(data)

        except json.JSONDecodeError:
            logger.warning(f"Could not parse message: {message}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")

    def on_error(self, ws, error):
        """Called on WebSocket error"""
        logger.error(f"❌ WebSocket error: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        """Called when WebSocket connection closes"""
        logger.warning(f"⚠️ Connection closed: {close_status_code} - {close_msg}")
        self.save_state()

        # Attempt reconnection if still running
        if self.running and self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            delay = self.reconnect_delay * self.reconnect_attempts
            logger.info(f"🔄 Reconnecting in {delay}s (attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})")
            time.sleep(delay)
            self.connect()
        elif self.running:
            logger.error(f"❌ Max reconnection attempts reached. Stopping.")
            self.running = False

    def start_ping_thread(self):
        """Start background thread to send ping messages"""
        def send_ping():
            ping_interval = 5 if self.use_rtds else 10  # RTDS: 5s, CLOB: 10s
            while self.running and self.ws and hasattr(self.ws, 'sock') and self.ws.sock and self.ws.sock.connected:
                try:
                    time.sleep(ping_interval)
                    self.ws.send("PING")
                    logger.debug(f"🏓 PING sent")
                except Exception as e:
                    logger.error(f"Error sending ping: {e}")
                    break

        self.ping_thread = threading.Thread(target=send_ping, daemon=True)
        self.ping_thread.start()

    def connect(self):
        """Connect to WebSocket and start listening"""
        self.running = True

        logger.info(f"🚀 Starting Polymarket WebSocket client...")
        logger.info(f"   URL: {self.url}")
        logger.info(f"   Markets: {len(self.asset_ids) if self.asset_ids else 'ALL'}")
        logger.info(f"   Feed: {FEED_FILE}")

        self.ws = WebSocketApp(
            self.url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )

        # Run forever (blocking)
        self.ws.run_forever()

    def disconnect(self):
        """Gracefully disconnect"""
        logger.info("🛑 Disconnecting...")
        self.running = False
        if self.ws:
            self.ws.close()
        self.save_state()
        logger.info("✅ Disconnected")


def get_hot_markets(limit=50):
    """
    Get most active markets to subscribe to.
    Uses REST API to find high-volume markets.

    Returns:
        List of asset IDs (token IDs)
    """
    try:
        import requests

        # Polymarket REST API endpoint
        url = "https://clob.polymarket.com/markets"
        params = {
            "limit": limit,
            "closed": "false",  # Only open markets
            "active": "true"    # Only active markets
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # API returns {"data": [...]}
        markets = data.get('data', []) if isinstance(data, dict) else data

        # Extract asset IDs (each market has multiple tokens)
        asset_ids = []
        for market in markets:
            tokens = market.get('tokens', [])
            for token in tokens:
                token_id = token.get('token_id')
                if token_id:
                    asset_ids.append(token_id)

        logger.info(f"📊 Found {len(asset_ids)} asset IDs from {len(markets)} hot markets")
        return asset_ids

    except Exception as e:
        logger.error(f"Error fetching hot markets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        logger.info("Will subscribe to ALL markets instead")
        return []


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Polymarket WebSocket Client')
    parser.add_argument('--rtds', action='store_true', help='Use RTDS endpoint instead of CLOB')
    parser.add_argument('--markets', type=int, default=50, help='Number of hot markets to track (0 = all)')
    parser.add_argument('--asset-ids', type=str, help='Comma-separated list of asset IDs')
    args = parser.parse_args()

    # Determine which markets to subscribe to
    if args.asset_ids:
        asset_ids = args.asset_ids.split(',')
        logger.info(f"Using provided asset IDs: {len(asset_ids)}")
    elif args.markets > 0:
        asset_ids = get_hot_markets(limit=args.markets)
    else:
        asset_ids = []
        logger.info("Subscribing to ALL markets")

    # Create and connect client
    client = PolymarketWebSocketClient(
        asset_ids=asset_ids,
        use_rtds=args.rtds
    )

    try:
        client.connect()
    except KeyboardInterrupt:
        logger.info("\n🛑 Interrupted by user")
        client.disconnect()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        client.disconnect()


if __name__ == '__main__':
    main()
