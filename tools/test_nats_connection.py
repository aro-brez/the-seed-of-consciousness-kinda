#!/usr/bin/env python3
"""Quick NATS connection test"""
import asyncio
from nats.aio.client import Client as NATS

async def test():
    nc = NATS()
    try:
        await nc.connect("nats://192.168.5.108:4222")
        print("✅ NATS connection successful!")
        await nc.close()
        return True
    except Exception as e:
        print(f"❌ NATS connection failed: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
