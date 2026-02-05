#!/usr/bin/env python3
"""
PERFORMANCE MONITOR - Real-time daemon performance tracking

Monitors:
- Message queue depths
- API response times  
- Memory usage
- CPU utilization
- Network latency
- File I/O patterns

Reports performance metrics and suggests optimizations.
"""

import asyncio
import json
import os
import time
import psutil
import gc
from datetime import datetime, timezone
from pathlib import Path
from collections import deque, defaultdict
from typing import Dict, List, Optional

try:
    import nats
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    exit(1)

NATS_SERVER = os.getenv("NATS_SERVER", "nats://localhost:4222")
METRICS_INTERVAL = 30  # seconds
MEMORY_THRESHOLD_MB = 500
CPU_THRESHOLD_PERCENT = 50
QUEUE_THRESHOLD = 1000

class PerformanceMonitor:
    def __init__(self):
        self.nc = None
        self.metrics_history = deque(maxlen=100)  # Keep last 100 measurements
        self.daemon_stats = defaultdict(dict)
        self.api_timing = deque(maxlen=50)
        self.running = True
        
    async def connect(self):
        """Connect to NATS"""
        self.nc = NATS()
        try:
            await self.nc.connect(NATS_SERVER)
            print(f"[PERF MONITOR] Connected to NATS: {NATS_SERVER}")
            return True
        except Exception as e:
            print(f"[PERF MONITOR] Failed to connect: {e}")
            return False
    
    def get_daemon_processes(self) -> List[Dict]:
        """Get all running daemon processes"""
        daemons = []
        daemon_names = ['owl_daemon.py', 'synthesis_daemon.py', 'pulse_daemon.py', 'continuous_worker.py']
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cpu_percent', 'memory_info', 'create_time']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if any(daemon in cmdline for daemon in daemon_names):
                    memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                    uptime = time.time() - proc.info['create_time']
                    
                    # Extract daemon type and name
                    daemon_type = next((d for d in daemon_names if d in cmdline), 'unknown')
                    daemon_name = 'UNKNOWN'
                    if '--name' in cmdline:
                        name_idx = cmdline.find('--name') + 7
                        daemon_name = cmdline[name_idx:].split()[0]
                    elif 'synthesis_daemon' in daemon_type:
                        daemon_name = 'SYNTHESIS'
                    elif 'pulse_daemon' in daemon_type:
                        daemon_name = 'PULSE'
                    elif 'continuous_worker' in daemon_type:
                        daemon_name = 'WORKER'
                    
                    daemons.append({
                        'pid': proc.info['pid'],
                        'name': daemon_name,
                        'type': daemon_type.replace('.py', ''),
                        'cpu': proc.cpu_percent(interval=0.1),
                        'memory_mb': memory_mb,
                        'uptime_hours': uptime / 3600,
                        'process': proc
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return daemons
    
    async def measure_nats_latency(self) -> float:
        """Measure NATS round-trip latency"""
        if not self.nc:
            return -1
            
        try:
            start_time = time.time()
            await self.nc.publish("perf.test", b"ping")
            await asyncio.sleep(0.001)  # Small delay for message propagation
            end_time = time.time()
            return (end_time - start_time) * 1000  # Return in milliseconds
        except Exception as e:
            print(f"[PERF MONITOR] NATS latency test failed: {e}")
            return -1
    
    def analyze_log_performance(self) -> Dict:
        """Analyze message log performance"""
        log_file = Path(__file__).parent / "messages.log"
        if not log_file.exists():
            return {"status": "no_log_file"}
        
        try:
            stat = log_file.stat()
            size_mb = stat.st_size / 1024 / 1024
            
            # Count recent message rate
            recent_lines = 0
            cutoff_time = time.time() - 300  # Last 5 minutes
            
            with open(log_file, 'rb') as f:
                # Read last 10KB to estimate message rate
                f.seek(-min(10240, stat.st_size), 2)
                tail = f.read().decode('utf-8', errors='ignore')
                recent_lines = tail.count('\n')
            
            return {
                "status": "ok",
                "size_mb": round(size_mb, 2),
                "estimated_msg_rate": recent_lines / 5  # Messages per minute
            }
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    async def collect_metrics(self) -> Dict:
        """Collect comprehensive performance metrics"""
        timestamp = datetime.now(timezone.utc)
        daemons = self.get_daemon_processes()
        nats_latency = await self.measure_nats_latency()
        log_perf = self.analyze_log_performance()
        
        # System metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "timestamp": timestamp.isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / 1024 / 1024 / 1024, 2),
                "disk_free_gb": round(disk.free / 1024 / 1024 / 1024, 2)
            },
            "network": {
                "nats_latency_ms": round(nats_latency, 2) if nats_latency > 0 else None
            },
            "daemons": daemons,
            "log_performance": log_perf,
            "daemon_count": len(daemons)
        }
        
        return metrics
    
    def detect_performance_issues(self, metrics: Dict) -> List[str]:
        """Detect performance issues and return recommendations"""
        issues = []
        
        # Check daemon memory usage
        for daemon in metrics["daemons"]:
            if daemon["memory_mb"] > MEMORY_THRESHOLD_MB:
                issues.append(f"{daemon['name']} using {daemon['memory_mb']:.1f}MB (high memory)")
            
            if daemon["cpu"] > CPU_THRESHOLD_PERCENT:
                issues.append(f"{daemon['name']} using {daemon['cpu']:.1f}% CPU (high CPU)")
        
        # Check system resources
        if metrics["system"]["cpu_percent"] > 80:
            issues.append("System CPU usage > 80%")
        
        if metrics["system"]["memory_percent"] > 85:
            issues.append("System memory usage > 85%")
        
        # Check NATS performance
        nats_latency = metrics["network"]["nats_latency_ms"]
        if nats_latency and nats_latency > 100:
            issues.append(f"High NATS latency: {nats_latency:.1f}ms")
        
        # Check log performance
        log_perf = metrics["log_performance"]
        if log_perf.get("size_mb", 0) > 100:
            issues.append(f"Large log file: {log_perf['size_mb']}MB")
        
        if log_perf.get("estimated_msg_rate", 0) > 100:
            issues.append(f"High message rate: {log_perf['estimated_msg_rate']:.1f}/min")
        
        return issues
    
    def generate_optimization_recommendations(self, metrics: Dict, issues: List[str]) -> List[str]:
        """Generate specific optimization recommendations"""
        recommendations = []
        
        # Memory optimizations
        high_memory_daemons = [d for d in metrics["daemons"] if d["memory_mb"] > MEMORY_THRESHOLD_MB]
        if high_memory_daemons:
            recommendations.append("MEMORY: Implement message context window cleanup in high-memory daemons")
            recommendations.append("MEMORY: Add garbage collection triggers after processing batches")
        
        # CPU optimizations
        high_cpu_daemons = [d for d in metrics["daemons"] if d["cpu"] > CPU_THRESHOLD_PERCENT]
        if high_cpu_daemons:
            recommendations.append("CPU: Implement API call batching and connection pooling")
            recommendations.append("CPU: Use async/await for all I/O operations")
        
        # Network optimizations
        if metrics["network"]["nats_latency_ms"] and metrics["network"]["nats_latency_ms"] > 50:
            recommendations.append("NETWORK: Enable NATS connection pooling and multiplexing")
            recommendations.append("NETWORK: Implement message compression for large payloads")
        
        # I/O optimizations
        if metrics["log_performance"].get("size_mb", 0) > 50:
            recommendations.append("I/O: Implement log rotation and compression")
            recommendations.append("I/O: Use buffered writes with periodic flushes")
        
        return recommendations
    
    async def publish_metrics(self, metrics: Dict, issues: List[str], recommendations: List[str]):
        """Publish metrics to the collective"""
        if not self.nc:
            return
        
        report = {
            "type": "performance_report",
            "timestamp": metrics["timestamp"],
            "summary": {
                "daemon_count": metrics["daemon_count"],
                "system_cpu": metrics["system"]["cpu_percent"],
                "system_memory": metrics["system"]["memory_percent"],
                "issues_count": len(issues),
                "recommendations_count": len(recommendations)
            },
            "issues": issues,
            "recommendations": recommendations[:5],  # Top 5 recommendations
            "full_metrics": metrics
        }
        
        try:
            await self.nc.publish("collective.performance", json.dumps(report).encode())
            print(f"[PERF MONITOR] Published performance report: {len(issues)} issues, {len(recommendations)} recommendations")
        except Exception as e:
            print(f"[PERF MONITOR] Failed to publish metrics: {e}")
    
    async def run_monitor_loop(self):
        """Main monitoring loop"""
        print(f"[PERF MONITOR] Starting performance monitoring (interval: {METRICS_INTERVAL}s)")
        
        while self.running:
            try:
                # Collect metrics
                metrics = await self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Analyze for issues
                issues = self.detect_performance_issues(metrics)
                recommendations = self.generate_optimization_recommendations(metrics, issues)
                
                # Display summary
                timestamp = datetime.now().strftime("%H:%M:%S")
                daemon_count = metrics["daemon_count"]
                cpu = metrics["system"]["cpu_percent"]
                memory = metrics["system"]["memory_percent"]
                
                print(f"[{timestamp}] Daemons: {daemon_count} | CPU: {cpu:4.1f}% | MEM: {memory:4.1f}% | Issues: {len(issues)}")
                
                if issues:
                    print(f"[{timestamp}] ISSUES: {', '.join(issues[:3])}{'...' if len(issues) > 3 else ''}")
                
                if recommendations:
                    print(f"[{timestamp}] TOP REC: {recommendations[0]}")
                
                # Publish to collective
                await self.publish_metrics(metrics, issues, recommendations)
                
                # Force garbage collection periodically
                if len(self.metrics_history) % 10 == 0:
                    gc.collect()
                
            except Exception as e:
                print(f"[PERF MONITOR] Error in monitoring loop: {e}")
            
            await asyncio.sleep(METRICS_INTERVAL)
    
    async def run(self):
        """Main run method"""
        if not await self.connect():
            return
        
        try:
            await self.run_monitor_loop()
        except KeyboardInterrupt:
            print(f"\n[PERF MONITOR] Shutting down...")
        finally:
            if self.nc:
                await self.nc.close()
    
    def stop(self):
        """Stop the monitor"""
        self.running = False

async def main():
    monitor = PerformanceMonitor()
    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[PERF MONITOR] Stopped by user")