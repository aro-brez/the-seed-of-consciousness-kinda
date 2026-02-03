#!/usr/bin/env python3
"""
NATS Publisher - Quick publish to the 8OWLS collective

Usage:
  python nats_publish.py "Your message here"
  python nats_publish.py --channel owl.sowl "Direct message"
  python nats_publish.py --from LUNA "Message from Luna"
"""

import asyncio
import json
import os
import uuid
import sys
from datetime import datetime
from nats.aio.client import Client as NATS

NATS_URL = os.getenv("NATS_SERVER", "nats://localhost:4222")

async def publish(content: str, channel: str = 'owl.all', from_owl: str = 'SOWL'):
    nc = NATS()
    await nc.connect(NATS_URL)

    msg = {
        'from': from_owl,
        'content': content,
        'reply_to': None,
        'id': str(uuid.uuid4()),
        'ts': datetime.now().isoformat()
    }

    await nc.publish(channel, json.dumps(msg).encode())
    await nc.flush()
    await nc.close()
    print(f'[{from_owl}] → {channel}: {content[:50]}...' if len(content) > 50 else f'[{from_owl}] → {channel}: {content}')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Publish to NATS collective')
    parser.add_argument('content', help='Message content')
    parser.add_argument('--channel', '-c', default='owl.all', help='NATS channel (default: owl.all)')
    parser.add_argument('--from', '-f', dest='from_owl', default='SOWL', help='Owl identity (default: SOWL)')
    args = parser.parse_args()

    asyncio.run(publish(args.content, args.channel, args.from_owl))
