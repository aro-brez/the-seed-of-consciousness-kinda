#!/usr/bin/env python3
"""
Test RTDS (Real-Time Data Streaming) endpoint
This may be more active than the CLOB market channel
"""

import json
import time
from polymarket_websocket_client import PolymarketWebSocketClient
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_rtds():
    """Test RTDS WebSocket connection for 30 seconds"""
    logger.info("🧪 Testing Polymarket RTDS connection...")
    logger.info("   Will run for 30 seconds to verify data flow")
    logger.info("")

    # Create client using RTDS endpoint
    client = PolymarketWebSocketClient(use_rtds=True)

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
    logger.info("📊 TEST RESULTS (RTDS):")
    logger.info(f"   Messages received: {client.messages_received}")
    logger.info(f"   Connection duration: 30 seconds")
    logger.info(f"   Rate: {client.messages_received / 30:.1f} messages/second")
    logger.info("")

    if client.messages_received > 0:
        logger.info("✅ SUCCESS! RTDS WebSocket is receiving data")
        return True
    else:
        logger.error("❌ FAILED! No messages received from RTDS")
        return False

if __name__ == '__main__':
    success = test_rtds()
    exit(0 if success else 1)
