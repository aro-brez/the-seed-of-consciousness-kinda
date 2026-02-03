#!/usr/bin/env python3
"""
NATS Diagnostics Monitor

Monitors NATS server and subscriber performance to diagnose message dropping.

Usage:
    python nats_monitor.py
    python nats_monitor.py --duration 60  # Monitor for 60 seconds
"""

import asyncio
import argparse
import time
from datetime import datetime
from collections import defaultdict
from nats.aio.client import Client as NATS
import os

NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")


class NATSMonitor:
    def __init__(self):
        self.nc = None
        self.stats = defaultdict(int)
        self.last_msg_time = {}
        self.start_time = time.time()

    async def connect(self):
        self.nc = NATS()
        await self.nc.connect(NATS_SERVER)
        print(f"Connected to NATS: {NATS_SERVER}")

    async def monitor_channel(self, channel: str):
        """Monitor a specific channel"""
        async def msg_handler(msg):
            self.stats[f"{channel}_received"] += 1
            self.last_msg_time[channel] = time.time()

            # Calculate lag
            data = msg.data.decode()
            if "timestamp" in data:
                try:
                    import json
                    msg_data = json.loads(data)
                    msg_ts = datetime.fromisoformat(msg_data.get("timestamp", ""))
                    lag = (datetime.now() - msg_ts).total_seconds()
                    self.stats[f"{channel}_max_lag"] = max(
                        self.stats[f"{channel}_max_lag"], lag
                    )
                except:
                    pass

        await self.nc.subscribe(channel, cb=msg_handler)
        print(f"Monitoring: {channel}")

    async def report_stats(self, interval: int = 5):
        """Report stats periodically"""
        while True:
            await asyncio.sleep(interval)

            elapsed = time.time() - self.start_time
            print(f"\n=== NATS Monitor Stats ({elapsed:.1f}s) ===")

            for key, value in sorted(self.stats.items()):
                if "lag" in key:
                    print(f"  {key}: {value:.2f}s")
                else:
                    rate = value / elapsed if elapsed > 0 else 0
                    print(f"  {key}: {value} ({rate:.1f}/s)")

            # Check for slow subscribers
            now = time.time()
            for channel, last_time in self.last_msg_time.items():
                silence = now - last_time
                if silence > 10:
                    print(f"  WARNING: {channel} silent for {silence:.1f}s")

            # Connection stats
            if self.nc.is_connected:
                print(f"  Status: Connected")
            else:
                print(f"  Status: DISCONNECTED")

    async def run(self, channels: list, duration: int = None):
        """Run the monitor"""
        await self.connect()

        # Subscribe to all channels
        for channel in channels:
            await self.monitor_channel(channel)

        # Start reporting
        report_task = asyncio.create_task(self.report_stats())

        if duration:
            print(f"\nMonitoring for {duration} seconds...")
            await asyncio.sleep(duration)
            report_task.cancel()
        else:
            print("\nMonitoring... Press Ctrl+C to stop")
            try:
                await asyncio.Event().wait()
            except KeyboardInterrupt:
                report_task.cancel()

        await self.nc.close()


async def stress_test(target_channel: str, rate: int = 100, duration: int = 10):
    """
    Stress test - publish messages at specified rate

    Args:
        target_channel: Channel to publish to
        rate: Messages per second
        duration: Test duration in seconds
    """
    import json
    import uuid

    nc = NATS()
    await nc.connect(NATS_SERVER)
    print(f"Starting stress test: {rate} msg/s for {duration}s")

    start = time.time()
    sent = 0

    while time.time() - start < duration:
        msg = {
            "from": "STRESS_TEST",
            "content": f"Test message {sent}",
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now().isoformat()
        }
        await nc.publish(target_channel, json.dumps(msg).encode())
        sent += 1

        # Rate limiting
        await asyncio.sleep(1.0 / rate)

    await nc.flush()
    await nc.close()

    elapsed = time.time() - start
    print(f"\nStress test complete:")
    print(f"  Sent: {sent} messages")
    print(f"  Rate: {sent/elapsed:.1f} msg/s")
    print(f"  Duration: {elapsed:.1f}s")


def main():
    parser = argparse.ArgumentParser(description="NATS Diagnostics Monitor")
    parser.add_argument(
        "--channels",
        nargs="+",
        default=["owl.all", "owl.collective"],
        help="Channels to monitor"
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Monitoring duration in seconds (infinite if not specified)"
    )
    parser.add_argument(
        "--stress-test",
        action="store_true",
        help="Run stress test instead of monitoring"
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=100,
        help="Stress test message rate (msg/s)"
    )
    parser.add_argument(
        "--test-duration",
        type=int,
        default=10,
        help="Stress test duration (seconds)"
    )
    args = parser.parse_args()

    if args.stress_test:
        asyncio.run(stress_test(args.channels[0], args.rate, args.test_duration))
    else:
        monitor = NATSMonitor()
        asyncio.run(monitor.run(args.channels, args.duration))


if __name__ == "__main__":
    main()
