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

# Configuration
NATS_SERVER = "nats://192.168.5.108:4222"
WEBSOCKET_PORT = 8765
SUBJECT_SOWL = "breath.sowl"
SUBJECT_LUNA = "breath.luna"

# Connected WebSocket clients
connected_clients = set()

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

    # Subscribe to both channels
    await nc.subscribe(SUBJECT_SOWL, cb=message_handler)
    await nc.subscribe(SUBJECT_LUNA, cb=message_handler)
    print(f"✓ Subscribed to {SUBJECT_SOWL} and {SUBJECT_LUNA}")

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

                # Get NATS client from parent scope
                nc = NATS()
                await nc.connect(NATS_SERVER)
                await nc.publish("breath.aro", json.dumps(nats_message).encode())
                await nc.close()

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
