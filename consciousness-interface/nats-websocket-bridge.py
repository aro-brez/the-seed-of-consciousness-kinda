#!/usr/bin/env python3
"""
NATS WebSocket Bridge
Bridges NATS messages to WebSocket for the 3D consciousness interface
"""

import asyncio
import json
import websockets
from datetime import datetime
from nats.aio.client import Client as NATS

# Configuration - aligned with MCP bridge channels
NATS_SERVER = "nats://192.168.5.108:4222"
WEBSOCKET_PORT = 8765

# All 8 owl channels + collective
OWL_CHANNELS = [
    "owl.all",      # Collective channel
    "owl.sowl",     # SØWL - IMPROVE
    "owl.luna",     # LUNA - RECEIVE
    "owl.lyra",     # LYRA - PERCEIVE
    "owl.prism",    # PRISM - CONNECT
    "owl.sage",     # SAGE - LEARN
    "owl.quest",    # QUEST - QUESTION
    "owl.nova",     # NOVA - EXPAND
    "owl.echo",     # ECHO - SHARE
]

# Connected WebSocket clients
connected_clients = set()

# Shared NATS connection for publishing (avoid connection churn)
nats_publisher = None

async def nats_to_websocket():
    """Subscribe to NATS and forward messages to WebSocket clients"""
    nc = NATS()
    await nc.connect(NATS_SERVER)
    print(f"✓ Connected to NATS at {NATS_SERVER}")

    async def message_handler(msg):
        """Handle incoming NATS messages"""
        data = json.loads(msg.data.decode())
        print(f"📨 NATS → WS: {data.get('from')} | {data.get('type')}")

        # Forward to all connected WebSocket clients
        if connected_clients:
            message = json.dumps(data)
            await asyncio.gather(
                *[client.send(message) for client in connected_clients],
                return_exceptions=True
            )

    # Subscribe to all 8 owl channels + collective
    for channel in OWL_CHANNELS:
        await nc.subscribe(channel, cb=message_handler)
    print(f"✓ Subscribed to {len(OWL_CHANNELS)} channels: {', '.join(OWL_CHANNELS)}")

    # Keep connection alive
    try:
        while True:
            await asyncio.sleep(1)
    except Exception as e:
        print(f"NATS error: {e}")
    finally:
        await nc.close()

async def websocket_handler(websocket):
    """Handle WebSocket connections from the web interface"""
    global nats_publisher

    # Ensure we have a persistent NATS connection
    if nats_publisher is None or not nats_publisher.is_connected:
        nats_publisher = NATS()
        await nats_publisher.connect(NATS_SERVER)
        print("✓ Established persistent NATS publisher connection")

    connected_clients.add(websocket)
    print(f"✓ WebSocket client connected (total: {len(connected_clients)})")

    try:
        # Send initial connection confirmation
        await websocket.send(json.dumps({
            "type": "connected",
            "message": "Connected to consciousness bridge"
        }))

        # Keep connection alive and handle incoming messages
        async for message in websocket:
            data = json.loads(message)
            print(f"📨 WS → NATS: {data}")

            # Forward ARŌ's message to NATS so SØWL and LUNA can hear it
            if data.get("from") or data.get("content"):
                nats_message = {
                    "from": data.get("from", "ARŌ"),
                    "content": data.get("content", ""),
                    "type": data.get("type", "human_voice"),
                    "timestamp": data.get("timestamp", datetime.utcnow().isoformat() + "Z")
                }

                # Reuse persistent connection instead of creating new one
                await nats_publisher.publish("owl.all", json.dumps(nats_message).encode())
                await nats_publisher.flush()  # Ensure delivery

                print(f"✓ Published to NATS: {nats_message.get('from')} | {nats_message.get('content')[:50]}")

            # Also echo back to browser
            await websocket.send(json.dumps({
                "type": "aro_interjection",
                "content": data.get("content"),
                "timestamp": data.get("timestamp")
            }))

    except websockets.exceptions.ConnectionClosed:
        print("WebSocket client disconnected")
    finally:
        connected_clients.remove(websocket)

async def main():
    """Run both NATS subscriber and WebSocket server"""
    print("(◉) Starting NATS ↔ WebSocket Bridge")
    print("=" * 50)

    # Start WebSocket server
    websocket_server = await websockets.serve(
        websocket_handler,
        "0.0.0.0",
        WEBSOCKET_PORT
    )
    print(f"✓ WebSocket server running on ws://0.0.0.0:{WEBSOCKET_PORT}")

    # Start NATS subscriber
    await nats_to_websocket()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n(◉) Bridge shutting down...")
