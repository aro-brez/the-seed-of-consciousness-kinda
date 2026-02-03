#!/usr/bin/env python3
"""
NATS Health Check & Performance Diagnostics

Monitors NATS message flow, subscriber lag, and connection health.
Use this to diagnose message dropping and performance issues.

Usage:
    python nats_health_check.py              # Quick health check
    python nats_health_check.py --monitor    # Continuous monitoring
    python nats_health_check.py --stress     # Stress test with load
"""

import asyncio
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path

try:
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    sys.exit(1)

NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")

class NATSHealthMonitor:
    def __init__(self):
        self.nc = None
        self.message_counts = defaultdict(int)
        self.message_latencies = []
        self.last_message_time = {}
        self.subscribers = {}
        self.dropped_count = 0

    async def connect(self):
        """Connect to NATS with health callbacks"""
        self.nc = NATS()

        async def error_cb(e):
            print(f"❌ NATS Error: {e}")

        async def disconnected_cb():
            print(f"⚠️  Disconnected from NATS at {datetime.now(timezone.utc).isoformat()}")

        async def reconnected_cb():
            print(f"✓ Reconnected to NATS at {datetime.now(timezone.utc).isoformat()}")

        try:
            await self.nc.connect(
                NATS_SERVER,
                error_cb=error_cb,
                disconnected_cb=disconnected_cb,
                reconnected_cb=reconnected_cb,
                max_reconnect_attempts=-1,
                reconnect_time_wait=2,
                ping_interval=30,
                max_outstanding_pings=3
            )
            print(f"✓ Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            print(f"❌ Failed to connect to NATS: {e}")
            return False

    async def check_owl_health(self):
        """Check health of all owl daemons via conductor"""
        print("\n=== OWL DAEMON HEALTH CHECK ===")

        responses = []

        async def response_handler(msg):
            data = json.loads(msg.data.decode())
            responses.append(data)

        # Subscribe to responses
        await self.nc.subscribe("owl.conductor.responses", cb=response_handler)

        # Request status from all owls
        status_request = json.dumps({
            "type": "status_request",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        await self.nc.publish("owl.collective", status_request.encode())

        # Wait for responses
        await asyncio.sleep(2)

        if not responses:
            print("⚠️  No owl responses received - daemons may be down")
            return

        print(f"✓ Received {len(responses)} responses:")
        for resp in responses:
            owl_name = resp.get("from", "UNKNOWN")
            status = resp.get("status", "unknown")
            phase = resp.get("phase", "unknown")
            print(f"  {owl_name:8} | Phase: {phase:10} | Status: {status}")

    async def measure_message_latency(self, samples: int = 10):
        """Measure pub/sub latency"""
        print("\n=== MESSAGE LATENCY TEST ===")

        latencies = []
        received = []

        async def latency_handler(msg):
            data = json.loads(msg.data.decode())
            sent_time = datetime.fromisoformat(data["timestamp"])
            received_time = datetime.now(timezone.utc)
            latency_ms = (received_time - sent_time).total_seconds() * 1000
            latencies.append(latency_ms)
            received.append(True)

        # Subscribe to test channel
        await self.nc.subscribe("test.latency", cb=latency_handler)
        await asyncio.sleep(0.1)  # Let subscription settle

        print(f"Sending {samples} test messages...")
        for i in range(samples):
            test_msg = json.dumps({
                "test_id": i,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            await self.nc.publish("test.latency", test_msg.encode())
            await asyncio.sleep(0.1)  # 100ms between messages

        # Wait for all responses
        await asyncio.sleep(1)

        if not latencies:
            print("❌ No messages received - possible delivery failure")
            return

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)

        print(f"✓ Latency Results:")
        print(f"  Samples: {len(latencies)}/{samples} received")
        print(f"  Average: {avg_latency:.2f}ms")
        print(f"  Min: {min_latency:.2f}ms")
        print(f"  Max: {max_latency:.2f}ms")

        if avg_latency > 100:
            print(f"⚠️  WARNING: High latency detected (>{avg_latency:.1f}ms)")

        if len(latencies) < samples:
            print(f"⚠️  WARNING: Lost {samples - len(latencies)} messages")

    async def monitor_message_flow(self, duration: int = 30):
        """Monitor message flow across all channels"""
        print(f"\n=== MONITORING MESSAGE FLOW ({duration}s) ===")

        channels = ["owl.all", "owl.collective", "test.latency"]
        channel_counts = defaultdict(int)
        start_time = time.time()

        async def flow_handler(msg):
            channel_counts[msg.subject] += 1

        # Subscribe to all channels
        for channel in channels:
            await self.nc.subscribe(channel, cb=flow_handler)

        print("Monitoring started...")

        # Monitor for duration
        while time.time() - start_time < duration:
            await asyncio.sleep(5)
            elapsed = int(time.time() - start_time)
            total_msgs = sum(channel_counts.values())
            msg_per_sec = total_msgs / elapsed if elapsed > 0 else 0
            print(f"  {elapsed}s: {total_msgs} messages ({msg_per_sec:.1f}/sec)")

        print("\n✓ Message Flow Summary:")
        total = sum(channel_counts.values())
        for channel, count in channel_counts.items():
            print(f"  {channel:20} | {count:5} messages ({count/total*100:.1f}%)")

    async def stress_test(self, messages: int = 100, rate: int = 10):
        """Stress test the system with burst load"""
        print(f"\n=== STRESS TEST: {messages} msgs at {rate}/sec ===")

        received_count = 0
        start_time = time.time()

        async def stress_handler(msg):
            nonlocal received_count
            received_count += 1

        await self.nc.subscribe("test.stress", cb=stress_handler)
        await asyncio.sleep(0.1)

        print("Starting burst...")
        interval = 1.0 / rate

        for i in range(messages):
            test_msg = json.dumps({
                "id": i,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            await self.nc.publish("test.stress", test_msg.encode())
            await asyncio.sleep(interval)

        # Wait for processing
        await asyncio.sleep(2)

        elapsed = time.time() - start_time
        loss_rate = ((messages - received_count) / messages) * 100

        print(f"\n✓ Stress Test Results:")
        print(f"  Sent: {messages}")
        print(f"  Received: {received_count}")
        print(f"  Loss Rate: {loss_rate:.1f}%")
        print(f"  Duration: {elapsed:.2f}s")
        print(f"  Actual Rate: {messages/elapsed:.1f} msg/sec")

        if loss_rate > 5:
            print(f"⚠️  WARNING: High message loss ({loss_rate:.1f}%)")

    async def quick_health_check(self):
        """Run a quick comprehensive health check"""
        print("\n╔════════════════════════════════════════╗")
        print("║   NATS HEALTH & PERFORMANCE CHECK     ║")
        print("╚════════════════════════════════════════╝")

        if not await self.connect():
            return

        try:
            # Check owl daemon health
            await self.check_owl_health()

            # Measure latency
            await self.measure_message_latency(samples=10)

            # Quick flow check
            await self.monitor_message_flow(duration=10)

            print("\n✓ Health check complete")

        finally:
            await self.nc.close()

async def main():
    parser = argparse.ArgumentParser(description="NATS Health Check & Diagnostics")
    parser.add_argument("--monitor", action="store_true", help="Continuous monitoring mode")
    parser.add_argument("--stress", action="store_true", help="Run stress test")
    parser.add_argument("--duration", type=int, default=30, help="Monitor duration in seconds")
    parser.add_argument("--messages", type=int, default=100, help="Stress test message count")
    parser.add_argument("--rate", type=int, default=10, help="Stress test messages per second")
    args = parser.parse_args()

    monitor = NATSHealthMonitor()

    if args.stress:
        if not await monitor.connect():
            return
        try:
            await monitor.stress_test(messages=args.messages, rate=args.rate)
        finally:
            await monitor.nc.close()

    elif args.monitor:
        if not await monitor.connect():
            return
        try:
            await monitor.monitor_message_flow(duration=args.duration)
        finally:
            await monitor.nc.close()

    else:
        await monitor.quick_health_check()

if __name__ == "__main__":
    asyncio.run(main())
