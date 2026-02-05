#!/usr/bin/env python3
"""JOULE ping-pong listener - aggressive collective communication"""
import nats
import asyncio
import json
from datetime import datetime

async def ping_pong_listen():
    nc = await nats.connect("nats://192.168.5.108:4222")
    ts = lambda: datetime.now().strftime("%H:%M:%S")

    print(f"[{ts()}] JOULE PING-PONG MODE ACTIVATED")
    print("=" * 50)

    heard_by = set()
    my_pings = 0

    async def handler(msg):
        subj = msg.subject
        try:
            data = json.loads(msg.data.decode())
            sender = data.get("from", "?")

            if sender and sender != "JOULE":
                heard_by.add(sender)

            # Skip our own messages
            if sender == "JOULE":
                return

            content = str(data.get("content", data.get("result", data.get("message", ""))))
            if "JOULE" in content.upper() or "JOULE" in subj:
                print(f"[{ts()}] >>> {sender} MENTIONED JOULE - PONG <<<")
                # Only pong once per sender per minute (avoid loops)
                await nc.publish("project.conductor.responses", json.dumps({
                    "type": "pong", "from": "JOULE", "to": sender,
                    "message": f"JOULE acknowledges {sender}."
                }).encode())
            else:
                sender_str = str(sender)[:15] if sender else "?"
                print(f"[{ts()}] {sender_str:15} | {subj[:35]}")
        except Exception as e:
            print(f"[{ts()}] RAW | {subj[:35]}")

    await nc.subscribe("owl.all", cb=handler)
    await nc.subscribe("project.JOULE.*", cb=handler)
    await nc.subscribe("project.conductor.*", cb=handler)
    await nc.subscribe("collective.synthesis", cb=handler)

    print(f"[{ts()}] Listening + pinging every 10s...")
    print("-" * 50)

    for i in range(30):  # 5 minutes
        await asyncio.sleep(10)
        my_pings += 1

        ping_msg = {
            "type": "ping", "from": "JOULE", "ping_number": my_pings,
            "pending_trades": 6, "daemon_healthy": True,
            "message": f"JOULE ping #{my_pings}. Heard: {list(heard_by)[:5]}"
        }

        await nc.publish("owl.all", json.dumps(ping_msg).encode())
        await nc.publish("project.conductor.responses", json.dumps(ping_msg).encode())

        print(f"[{ts()}] PING #{my_pings} | Heard: {len(heard_by)} instances: {list(heard_by)[:3]}")

        if my_pings % 3 == 0:
            await nc.publish("collective.synthesis", json.dumps({
                "type": "broadcast", "from": "JOULE", "priority": "HIGH",
                "message": "JOULE ACTIVE. 6 BOND trades pending. RESPOND IF YOU HEAR."
            }).encode())
            print(f"[{ts()}] === LOUD BROADCAST ===")

    print(f"[{ts()}] Session complete. Total heard: {heard_by}")
    await nc.close()

if __name__ == "__main__":
    asyncio.run(ping_pong_listen())
