#!/usr/bin/env python3
"""
Test Polymarket WebSocket Client v2 (Official SDK)
"""

import asyncio
import logging
from polymarket_websocket_client_v2 import PolymarketWebSocketClientV2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_v2():
    """Test v2 client for 30 seconds"""
    logger.info("🧪 Testing Polymarket WebSocket v2 (Official SDK)...")
    logger.info("   Will run for 30 seconds to verify data flow")
    logger.info("")

    # Create client with just a few popular markets for testing
    test_markets = [
        "will-bitcoin-be-above-100k-on-february-1",
        "will-trump-be-president-on-jan-20-2025",
        "will-the-s-and-p-500-close-above-6000-on-jan-31"
    ]

    client = PolymarketWebSocketClientV2(market_slugs=test_markets)

    # Run for 30 seconds
    try:
        # Start connection
        connect_task = asyncio.create_task(client.connect_and_run())

        # Wait 30 seconds
        await asyncio.sleep(30)

        # Stop
        await client.disconnect()

        # Cancel the connection task
        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    except Exception as e:
        logger.error(f"Test error: {e}")

    # Report results
    logger.info("")
    logger.info("=" * 60)
    logger.info("📊 TEST RESULTS (v2):")
    logger.info(f"   Total messages: {client.messages_received}")
    logger.info(f"   Trades: {client.trades_received}")
    logger.info(f"   Market data: {client.market_data_received}")
    logger.info(f"   Rate: {client.messages_received / 30:.1f} messages/second")
    logger.info("")

    if client.messages_received > 0:
        logger.info("✅ SUCCESS! Official SDK is receiving data")
        logger.info("")
        logger.info("To start the client permanently, run:")
        logger.info("   ./tools/START_POLYMARKET_WEBSOCKET.sh")
        return True
    else:
        logger.error("❌ FAILED! No messages received")
        return False


if __name__ == '__main__':
    success = asyncio.run(test_v2())
    exit(0 if success else 1)
