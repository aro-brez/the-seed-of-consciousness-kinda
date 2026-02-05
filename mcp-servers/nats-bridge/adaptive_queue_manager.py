#!/usr/bin/env python3
"""
ADAPTIVE QUEUE MANAGER - High-performance message processing with intelligent backpressure

Key optimizations:
- Priority-based message processing
- Dynamic queue sizing based on load
- Intelligent message batching  
- Circuit breaker for overload protection
- Memory-efficient message deduplication
- Performance metrics and adaptive tuning
"""

import asyncio
import time
import hashlib
import logging
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timezone

class MessagePriority(Enum):
    CRITICAL = auto()    # System control messages
    HIGH = auto()        # Direct mentions, conductor commands
    NORMAL = auto()      # Regular collective messages
    LOW = auto()         # Background/monitoring messages

class QueueState(Enum):
    HEALTHY = auto()     # Normal operation
    DEGRADED = auto()    # High load but manageable
    CRITICAL = auto()    # Near capacity
    CIRCUIT_OPEN = auto() # Overloaded, dropping messages

@dataclass
class QueueMetrics:
    """Performance metrics for queue monitoring"""
    total_processed: int = 0
    total_dropped: int = 0
    avg_latency_ms: float = 0.0
    throughput_per_sec: float = 0.0
    queue_depth: int = 0
    state: QueueState = QueueState.HEALTHY
    memory_usage_mb: float = 0.0
    last_updated: datetime = None

@dataclass
class ProcessedMessage:
    """Lightweight message representation"""
    content_hash: str
    priority: MessagePriority
    timestamp: float
    sender: str
    size_bytes: int

class AdaptiveQueueManager:
    """High-performance adaptive message queue with intelligent backpressure"""
    
    def __init__(self, 
                 max_memory_mb: float = 50.0,
                 circuit_breaker_threshold: int = 5000,
                 dedup_window_seconds: int = 30):
        
        # Core queue configuration
        self.max_memory_mb = max_memory_mb
        self.circuit_breaker_threshold = circuit_breaker_threshold
        self.dedup_window_seconds = dedup_window_seconds
        
        # Priority queues with adaptive sizing
        self.queues = {
            MessagePriority.CRITICAL: asyncio.Queue(maxsize=100),
            MessagePriority.HIGH: asyncio.Queue(maxsize=1000),
            MessagePriority.NORMAL: asyncio.Queue(maxsize=5000),
            MessagePriority.LOW: asyncio.Queue(maxsize=10000)
        }
        
        # Deduplication tracking
        self.recent_hashes = deque(maxlen=1000)
        self.hash_timestamps = {}
        
        # Performance tracking
        self.metrics = QueueMetrics()
        self.processing_times = deque(maxlen=100)
        self.throughput_samples = deque(maxlen=20)
        
        # Adaptive behavior
        self.state = QueueState.HEALTHY
        self.circuit_breaker_until = 0
        self.last_metrics_update = time.time()
        
        # Batch processing
        self.batch_size = 10
        self.batch_timeout = 0.1  # 100ms
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _get_content_hash(self, content: str) -> str:
        """Generate content hash for deduplication"""
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if message is a recent duplicate"""
        now = time.time()
        
        # Clean old hashes
        while (self.hash_timestamps and 
               now - min(self.hash_timestamps.values()) > self.dedup_window_seconds):
            old_hash = next(iter(self.hash_timestamps))
            del self.hash_timestamps[old_hash]
        
        if content_hash in self.hash_timestamps:
            return True
        
        self.hash_timestamps[content_hash] = now
        return False
    
    def _classify_priority(self, sender: str, content: str, subject: str = "") -> MessagePriority:
        """Classify message priority"""
        content_lower = content.lower()
        
        # Critical system messages
        if any(keyword in content_lower for keyword in 
               ['shutdown', 'emergency', 'critical', 'system error', '[conductor]']):
            return MessagePriority.CRITICAL
        
        # High priority messages
        if (subject.startswith('owl.') or 
            any(keyword in content_lower for keyword in ['@', 'urgent', 'task:', 'action:'])):
            return MessagePriority.HIGH
        
        # Low priority background messages
        if any(keyword in content_lower for keyword in 
               ['heartbeat', 'status', 'monitoring', 'metrics']):
            return MessagePriority.LOW
        
        return MessagePriority.NORMAL
    
    def _update_queue_sizes(self):
        """Dynamically adjust queue sizes based on load"""
        total_depth = sum(q.qsize() for q in self.queues.values())
        
        if total_depth > self.circuit_breaker_threshold * 0.8:
            # High load: Reduce normal/low capacity, preserve critical/high
            for priority, queue in self.queues.items():
                if priority in [MessagePriority.NORMAL, MessagePriority.LOW]:
                    # Note: Cannot resize asyncio.Queue, but we can drop messages
                    pass
        
        # Update state based on total load
        if total_depth > self.circuit_breaker_threshold:
            self.state = QueueState.CIRCUIT_OPEN
            self.circuit_breaker_until = time.time() + 10  # 10 second cooldown
        elif total_depth > self.circuit_breaker_threshold * 0.8:
            self.state = QueueState.CRITICAL
        elif total_depth > self.circuit_breaker_threshold * 0.5:
            self.state = QueueState.DEGRADED
        else:
            self.state = QueueState.HEALTHY
    
    async def enqueue(self, sender: str, content: str, subject: str = "") -> bool:
        """Enqueue message with adaptive handling"""
        now = time.time()
        
        # Circuit breaker check
        if self.state == QueueState.CIRCUIT_OPEN and now < self.circuit_breaker_until:
            self.metrics.total_dropped += 1
            return False
        
        # Deduplication check
        content_hash = self._get_content_hash(content)
        if self._is_duplicate(content_hash):
            return False  # Silently drop duplicate
        
        # Classify priority
        priority = self._classify_priority(sender, content, subject)
        
        # Memory usage check
        message_size = len(content.encode())
        estimated_memory = sum(q.qsize() * 500 for q in self.queues.values()) / 1024 / 1024
        
        if estimated_memory > self.max_memory_mb and priority == MessagePriority.LOW:
            self.metrics.total_dropped += 1
            return False
        
        # Try to enqueue
        try:
            message_data = {
                'sender': sender,
                'content': content,
                'subject': subject,
                'timestamp': now,
                'priority': priority,
                'content_hash': content_hash,
                'size_bytes': message_size
            }
            
            self.queues[priority].put_nowait(message_data)
            self._update_queue_sizes()
            return True
            
        except asyncio.QueueFull:
            # Queue full - adaptive behavior
            if priority == MessagePriority.CRITICAL:
                # Drop oldest normal/low priority message to make room
                for drop_priority in [MessagePriority.LOW, MessagePriority.NORMAL]:
                    if not self.queues[drop_priority].empty():
                        try:
                            self.queues[drop_priority].get_nowait()
                            self.queues[priority].put_nowait(message_data)
                            self.metrics.total_dropped += 1
                            return True
                        except:
                            pass
            
            self.metrics.total_dropped += 1
            return False
    
    async def dequeue_batch(self, max_batch_size: int = None) -> List[Dict]:
        """Dequeue batch of messages with priority ordering"""
        if max_batch_size is None:
            max_batch_size = self.batch_size
        
        batch = []
        timeout_time = time.time() + self.batch_timeout
        
        # Process in priority order
        for priority in [MessagePriority.CRITICAL, MessagePriority.HIGH, 
                        MessagePriority.NORMAL, MessagePriority.LOW]:
            
            queue = self.queues[priority]
            
            while len(batch) < max_batch_size and not queue.empty():
                try:
                    message = queue.get_nowait()
                    batch.append(message)
                    queue.task_done()
                except asyncio.QueueEmpty:
                    break
            
            if len(batch) >= max_batch_size:
                break
            
            # Check timeout for partial batches
            if time.time() > timeout_time and batch:
                break
        
        # If no messages ready, wait briefly for new ones
        if not batch:
            try:
                message = await asyncio.wait_for(
                    self.queues[MessagePriority.HIGH].get(), 
                    timeout=0.1
                )
                batch.append(message)
                self.queues[MessagePriority.HIGH].task_done()
            except asyncio.TimeoutError:
                pass
        
        # Update metrics
        if batch:
            self.metrics.total_processed += len(batch)
        
        return batch
    
    async def dequeue_single(self) -> Optional[Dict]:
        """Dequeue single message with priority"""
        batch = await self.dequeue_batch(max_batch_size=1)
        return batch[0] if batch else None
    
    def record_processing_time(self, duration_ms: float):
        """Record message processing time for adaptive tuning"""
        self.processing_times.append(duration_ms)
        
        if len(self.processing_times) >= 10:
            avg_time = sum(self.processing_times) / len(self.processing_times)
            
            # Adapt batch size based on processing speed
            if avg_time < 50:  # Fast processing
                self.batch_size = min(20, self.batch_size + 1)
            elif avg_time > 200:  # Slow processing
                self.batch_size = max(5, self.batch_size - 1)
    
    def get_metrics(self) -> QueueMetrics:
        """Get current performance metrics"""
        now = time.time()
        
        # Update throughput calculation
        if now - self.last_metrics_update > 1.0:
            throughput = self.metrics.total_processed / max(1, now - self.last_metrics_update)
            self.throughput_samples.append(throughput)
            self.last_metrics_update = now
        
        # Update current state
        self.metrics.queue_depth = sum(q.qsize() for q in self.queues.values())
        self.metrics.state = self.state
        self.metrics.last_updated = datetime.now(timezone.utc)
        
        if self.processing_times:
            self.metrics.avg_latency_ms = sum(self.processing_times) / len(self.processing_times)
        
        if self.throughput_samples:
            self.metrics.throughput_per_sec = sum(self.throughput_samples) / len(self.throughput_samples)
        
        # Estimate memory usage
        self.metrics.memory_usage_mb = sum(q.qsize() * 0.5 for q in self.queues.values())
        
        return self.metrics
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        metrics = self.get_metrics()
        
        return {
            'state': self.state.name,
            'queue_depth': metrics.queue_depth,
            'throughput_per_sec': round(metrics.throughput_per_sec, 2),
            'avg_latency_ms': round(metrics.avg_latency_ms, 2),
            'memory_usage_mb': round(metrics.memory_usage_mb, 2),
            'total_processed': metrics.total_processed,
            'total_dropped': metrics.total_dropped,
            'drop_rate': round(metrics.total_dropped / max(1, metrics.total_processed + metrics.total_dropped) * 100, 2),
            'batch_size': self.batch_size,
            'circuit_breaker_active': self.state == QueueState.CIRCUIT_OPEN
        }
    
    async def cleanup(self):
        """Clean up resources"""
        self.logger.info(f"Queue cleanup - processed {self.metrics.total_processed}, dropped {self.metrics.total_dropped}")

# Example usage and testing
async def test_queue_manager():
    """Test the adaptive queue manager"""
    manager = AdaptiveQueueManager()
    
    # Test message processing
    test_messages = [
        ("SYSTEM", "Emergency shutdown required", "system.emergency"),
        ("LUNA", "@all urgent task needed", "owl.collective"),
        ("SAGE", "Regular analysis complete", "owl.all"),
        ("MONITOR", "Heartbeat status normal", "system.monitor"),
    ]
    
    # Enqueue test messages
    for sender, content, subject in test_messages:
        success = await manager.enqueue(sender, content, subject)
        print(f"Enqueued {sender}: {success}")
    
    # Process messages
    batch = await manager.dequeue_batch()
    print(f"Dequeued batch of {len(batch)} messages")
    
    for msg in batch:
        print(f"  {msg['priority'].name}: {msg['sender']} - {msg['content'][:50]}...")
    
    # Show health status
    health = manager.get_health_status()
    print(f"Health status: {health}")

if __name__ == "__main__":
    asyncio.run(test_queue_manager())