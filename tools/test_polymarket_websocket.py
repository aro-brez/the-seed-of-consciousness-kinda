#!/usr/bin/env python3
"""
Quick test of Polymarket WebSocket connection
Tests connection and receives a few messages
"""

import json
import time
from polymarket_websocket_client import PolymarketWebSocketClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_connection():
    """Test WebSocket connection for 30 seconds"""
    logger.info("🧪 Testing Polymarket WebSocket connection...")
    logger.info("   Will run for 30 seconds to verify data flow")
    logger.info("")

    # Create client that subscribes to all markets
    client = PolymarketWebSocketClient(asset_ids=[])

    # Run in a thread
    import threading
    thread = threading.Thread(target=client.connect, daemon=True)
    thread.start()

    # Wait 30 seconds
    try:
        time.sleep(30)
    except KeyboardInterrupt:
        pass

    # Disconnect
    client.disconnect()

    # Report results
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 TEST RESULTS:")
    logger.info(f"   Messages received: {client.messages_received}")
    logger.info(f"   Connection duration: 30 seconds")
    logger.info(f"   Rate: {client.messages_received / 30:.1f} messages/second")
    logger.info("")

    if client.messages_received > 0:
        logger.info("✅ SUCCESS! WebSocket is receiving data")
        logger.info("")
        logger.info("To start the client permanently, run:")
        logger.info("   ./tools/START_POLYMARKET_WEBSOCKET.sh")
        return True
    else:
        logger.error("❌ FAILED! No messages received")
        logger.error("   Check network connection and API endpoint")
        return False

if __name__ == '__main__':
    success = test_connection()
    exit(0 if success else 1)
