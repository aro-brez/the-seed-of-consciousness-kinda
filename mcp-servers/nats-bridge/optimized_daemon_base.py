#!/usr/bin/env python3
"""
OPTIMIZED DAEMON BASE - High-performance foundation for 8OWLS daemons

Performance improvements:
- Connection pooling for NATS and API calls
- Batched message processing
- Memory-efficient context windows
- Async I/O with buffering
- Intelligent garbage collection
- Rate limiting and backoff
"""

import asyncio
import gc
import json
import os
import time
import weakref
from abc import ABC, abstractmethod
from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any, AsyncIterator
import logging

try:
    import nats
    from nats.aio.client import Client as NATS
except ImportError:
    print("ERROR: nats-py not installed. Run: pip install nats-py")
    exit(1)

try:
    import anthropic
except ImportError:
    print("ERROR: anthropic not installed")
    exit(1)

# Performance configurations
MAX_MEMORY_MB = 200  # Memory threshold before cleanup
CONTEXT_WINDOW_SIZE = 50  # Max messages to keep in context
BATCH_SIZE = 10  # Messages to process in batches
GC_INTERVAL = 300  # Garbage collection every 5 minutes
API_RATE_LIMIT = 10  # Max API calls per minute
BUFFER_FLUSH_INTERVAL = 30  # Flush buffers every 30 seconds

class PerformanceTracker:
    """Track daemon performance metrics"""
    
    def __init__(self):
        self.start_time = time.time()
        self.message_count = 0
        self.api_calls = 0
        self.memory_peak = 0
        self.last_gc = time.time()
        
    def record_message(self):
        self.message_count += 1
        
    def record_api_call(self):
        self.api_calls += 1
        
    def check_memory(self) -> float:
        """Check current memory usage in MB"""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.memory_peak = max(self.memory_peak, memory_mb)
            return memory_mb
        except ImportError:
            return 0
    
    def should_gc(self) -> bool:
        """Check if garbage collection should run"""
        return time.time() - self.last_gc > GC_INTERVAL
    
    def force_gc(self):
        """Force garbage collection and update timestamp"""
        gc.collect()
        self.last_gc = time.time()
        
    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        return {
            "uptime_minutes": round(uptime / 60, 1),
            "messages_processed": self.message_count,
            "api_calls_made": self.api_calls,
            "memory_peak_mb": round(self.memory_peak, 1),
            "messages_per_minute": round(self.message_count / (uptime / 60), 1) if uptime > 60 else 0,
        }

class OptimizedBuffer:
    """Memory-efficient buffer with automatic flushing"""
    
    def __init__(self, file_path: Path, max_size: int = 1000):
        self.file_path = file_path
        self.buffer = deque(maxlen=max_size)
        self.last_flush = time.time()
        self.lock = asyncio.Lock()
        
    async def append(self, content: str):
        """Add content to buffer"""
        async with self.lock:
            timestamp = datetime.now(timezone.utc).isoformat()
            self.buffer.append(f"[{timestamp}] {content}")
            
            # Auto-flush if buffer is getting full or time elapsed
            if (len(self.buffer) > 100 or 
                time.time() - self.last_flush > BUFFER_FLUSH_INTERVAL):
                await self.flush()
    
    async def flush(self):
        """Flush buffer to file"""
        if not self.buffer:
            return
            
        async with self.lock:
            try:
                # Ensure parent directory exists
                self.file_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Write all buffered content at once
                with open(self.file_path, 'a') as f:
                    while self.buffer:
                        f.write(self.buffer.popleft() + '\n')
                        
                self.last_flush = time.time()
            except Exception as e:
                # If write fails, keep the content in buffer
                logging.error(f"Buffer flush failed: {e}")

class ConnectionPool:
    """Connection pool for NATS and API clients"""
    
    def __init__(self):
        self._nats_connections: Dict[str, NATS] = {}
        self._api_clients: Dict[str, anthropic.Anthropic] = {}
        self._api_calls_history = deque(maxlen=100)
        self._lock = asyncio.Lock()
    
    @asynccontextmanager
    async def get_nats_connection(self, server: str) -> AsyncIterator[NATS]:
        """Get or create NATS connection"""
        async with self._lock:
            if server not in self._nats_connections:
                nc = NATS()
                try:
                    await nc.connect(server)
                    self._nats_connections[server] = nc
                except Exception as e:
                    raise ConnectionError(f"Failed to connect to NATS: {e}")
            
            yield self._nats_connections[server]
    
    def get_api_client(self, api_key: str) -> anthropic.Anthropic:
        """Get or create API client"""
        if api_key not in self._api_clients:
            self._api_clients[api_key] = anthropic.Anthropic(api_key=api_key)
        return self._api_clients[api_key]
    
    def can_make_api_call(self) -> bool:
        """Check if we're within rate limits"""
        now = time.time()
        # Remove old calls (older than 1 minute)
        while self._api_calls_history and now - self._api_calls_history[0] > 60:
            self._api_calls_history.popleft()
        
        return len(self._api_calls_history) < API_RATE_LIMIT
    
    def record_api_call(self):
        """Record an API call for rate limiting"""
        self._api_calls_history.append(time.time())
    
    async def cleanup(self):
        """Clean up all connections"""
        async with self._lock:
            for nc in self._nats_connections.values():
                try:
                    await nc.close()
                except:
                    pass
            self._nats_connections.clear()

# Global connection pool instance
_connection_pool = ConnectionPool()

class OptimizedDaemonBase(ABC):
    """High-performance base class for 8OWLS daemons"""
    
    def __init__(self, name: str, cycle_seconds: int = 60):
        self.name = name
        self.cycle_seconds = cycle_seconds
        self.running = True
        
        # Performance tracking
        self.perf = PerformanceTracker()
        
        # Efficient context management
        self.context_window = deque(maxlen=CONTEXT_WINDOW_SIZE)
        
        # Buffered logging
        self.log_buffer = OptimizedBuffer(
            Path(__file__).parent / f"{name.lower()}_optimized.log"
        )
        
        # Configuration
        self.nats_server = os.getenv("NATS_SERVER", "nats://localhost:4222")
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        
        # Weak reference to allow proper cleanup
        self._cleanup_tasks = []
        
    async def log(self, message: str, level: str = "INFO"):
        """Efficiently log messages with buffering"""
        log_entry = f"[{level}] [{self.name}] {message}"
        await self.log_buffer.append(log_entry)
        
        # Also print to console for immediate feedback
        if level in ["ERROR", "WARN"]:
            print(log_entry)
    
    async def add_to_context(self, message: Dict[str, Any]):
        """Add message to context window efficiently"""
        # Keep only essential fields to save memory
        compact_message = {
            "timestamp": message.get("timestamp"),
            "from": message.get("from"),
            "content": message.get("content", "")[:200],  # Truncate long messages
            "type": message.get("type")
        }
        self.context_window.append(compact_message)
        self.perf.record_message()
    
    def get_context_summary(self, max_length: int = 2000) -> str:
        """Get efficient context summary"""
        if not self.context_window:
            return ""
        
        # Build context efficiently
        context_parts = []
        current_length = 0
        
        # Start from most recent messages
        for msg in reversed(self.context_window):
            part = f"[{msg['from']}]: {msg['content']}"
            if current_length + len(part) > max_length:
                break
            context_parts.insert(0, part)
            current_length += len(part)
        
        return "\n".join(context_parts)
    
    async def safe_api_call(self, prompt: str, max_tokens: int = 1000) -> Optional[str]:
        """Make rate-limited API call with error handling"""
        if not _connection_pool.can_make_api_call():
            await self.log("API rate limit reached, skipping call", "WARN")
            return None
        
        if not self.api_key:
            await self.log("No API key configured", "ERROR")
            return None
        
        try:
            client = _connection_pool.get_api_client(self.api_key)
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            
            _connection_pool.record_api_call()
            self.perf.record_api_call()
            
            return response.content[0].text
            
        except Exception as e:
            await self.log(f"API call failed: {e}", "ERROR")
            return None
    
    async def publish_to_collective(self, channel: str, message: Dict[str, Any]):
        """Efficiently publish to NATS"""
        try:
            async with _connection_pool.get_nats_connection(self.nats_server) as nc:
                message_data = json.dumps(message).encode()
                await nc.publish(channel, message_data)
                await self.log(f"Published to {channel}: {len(message_data)} bytes")
        except Exception as e:
            await self.log(f"Failed to publish to {channel}: {e}", "ERROR")
    
    async def subscribe_to_messages(self, callback):
        """Subscribe to collective messages efficiently"""
        try:
            async with _connection_pool.get_nats_connection(self.nats_server) as nc:
                await nc.subscribe("collective.*", cb=callback)
                await self.log("Subscribed to collective channels")
        except Exception as e:
            await self.log(f"Failed to subscribe: {e}", "ERROR")
    
    def should_cleanup_memory(self) -> bool:
        """Check if memory cleanup is needed"""
        memory_mb = self.perf.check_memory()
        return memory_mb > MAX_MEMORY_MB or self.perf.should_gc()
    
    async def cleanup_memory(self):
        """Perform memory cleanup"""
        await self.log(f"Performing memory cleanup (peak: {self.perf.memory_peak:.1f}MB)")
        
        # Clear old context
        while len(self.context_window) > CONTEXT_WINDOW_SIZE // 2:
            self.context_window.popleft()
        
        # Force garbage collection
        self.perf.force_gc()
        
        # Flush buffers
        await self.log_buffer.flush()
        
        memory_after = self.perf.check_memory()
        await self.log(f"Memory cleanup complete: {memory_after:.1f}MB")
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        stats = self.perf.get_stats()
        stats.update({
            "name": self.name,
            "context_size": len(self.context_window),
            "current_memory_mb": round(self.perf.check_memory(), 1),
            "running": self.running
        })
        return stats
    
    @abstractmethod
    async def process_cycle(self):
        """Override this method to implement daemon-specific logic"""
        pass
    
    async def run_main_loop(self):
        """Optimized main loop with performance monitoring"""
        await self.log(f"Starting optimized daemon loop (cycle: {self.cycle_seconds}s)")
        
        while self.running:
            cycle_start = time.time()
            
            try:
                # Run the daemon-specific processing
                await self.process_cycle()
                
                # Memory cleanup if needed
                if self.should_cleanup_memory():
                    await self.cleanup_memory()
                
                # Performance reporting every 10 cycles
                if self.perf.message_count % 10 == 0 and self.perf.message_count > 0:
                    report = await self.get_performance_report()
                    await self.publish_to_collective("collective.performance", {
                        "type": "daemon_performance",
                        "daemon": self.name,
                        "metrics": report,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                
            except Exception as e:
                await self.log(f"Cycle error: {e}", "ERROR")
            
            # Efficient sleep with early exit if stopped
            cycle_duration = time.time() - cycle_start
            sleep_time = max(0, self.cycle_seconds - cycle_duration)
            
            for _ in range(int(sleep_time * 10)):  # Check every 0.1 seconds
                if not self.running:
                    break
                await asyncio.sleep(0.1)
    
    async def start(self):
        """Start the optimized daemon"""
        try:
            await self.run_main_loop()
        except KeyboardInterrupt:
            await self.log("Daemon stopped by user")
        finally:
            await self.cleanup()
    
    async def cleanup(self):
        """Clean up resources"""
        self.running = False
        await self.log("Cleaning up daemon resources")
        
        # Flush any remaining buffers
        await self.log_buffer.flush()
        
        # Final performance report
        final_report = await self.get_performance_report()
        await self.log(f"Final stats: {json.dumps(final_report, indent=2)}")
        
    def stop(self):
        """Stop the daemon"""
        self.running = False

# Global cleanup function
async def cleanup_all_connections():
    """Clean up all global connections"""
    await _connection_pool.cleanup()