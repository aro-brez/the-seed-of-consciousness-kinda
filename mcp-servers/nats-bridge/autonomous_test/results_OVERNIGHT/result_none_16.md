# Test 16 - NONE context
**Prompt Clarity:** HIGH
**Generated**: 2026-02-03T12:00:44.558311+00:00
**Elapsed**: 14.59s
**Model**: claude-sonnet-4-20250514

## Analysis Scores
- Asks for Info: no
- Confidence Score: 0
- Hedging Score: 0
- Net Confidence: 0
- Actionability: 1
- Specificity: 2
- Length: 3896 chars

## Prompt
Design a circuit breaker pattern for a trading bot that limits to 10 trades per hour.

## Response
Here's a circuit breaker pattern implementation for a trading bot with a 10 trades/hour limit:

## Core Circuit Breaker Class

```python
import time
from collections import deque
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Callable
import threading

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit tripped, blocking trades
    HALF_OPEN = "half_open"  # Testing if system recovered

@dataclass
class CircuitBreakerConfig:
    max_trades_per_hour: int = 10
    cooldown_seconds: int = 300  # 5 minutes before trying again
    test_trades_in_half_open: int = 1  # Trades to test recovery

class TradingCircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitState.CLOSED
        self.trade_timestamps = deque()
        self.last_failure_time: Optional[float] = None
        self.half_open_test_count = 0
        self._lock = threading.Lock()
    
    def can_trade(self) -> bool:
        """Check if trading is allowed based on circuit breaker state"""
        with self._lock:
            current_time = time.time()
            
            # Clean old timestamps (older than 1 hour)
            self._cleanup_old_trades(current_time)
            
            if self.state == CircuitState.OPEN:
                # Check if cooldown period has passed
                if (current_time - self.last_failure_time) >= self.config.cooldown_seconds:
                    self.state = CircuitState.HALF_OPEN
                    self.half_open_test_count = 0
                    return True
                return False
            
            elif self.state == CircuitState.HALF_OPEN:
                # Allow limited testing
                return self.half_open_test_count < self.config.test_trades_in_half_open
            
            else:  # CLOSED state
                # Check if we're under the rate limit
                return len(self.trade_timestamps) < self.config.max_trades_per_hour
    
    def record_trade_attempt(self, success: bool) -> None:
        """Record a trade attempt and update circuit state"""
        with self._lock:
            current_time = time.time()
            
            if self.state == CircuitState.HALF_OPEN:
                self.half_open_test_count += 1
                
                if success:
                    # Test passed, return to normal operation
                    self.state = CircuitState.CLOSED
                    self.last_failure_time = None
                else:
                    # Test failed, return to open state
                    self.state = CircuitState.OPEN
                    self.last_failure_time = current_time
                    return
            
            if success:
                # Record successful trade
                self.trade_timestamps.append(current_time)
                
                # Check if we've hit the rate limit
                if len(self.trade_timestamps) >= self.config.max_trades_per_hour:
                    self.state = CircuitState.OPEN
                    self.last_failure_time = current_time
            else:
                # Trade failed for other reasons - could trigger circuit
                self.state = CircuitState.OPEN
                self.last_failure_time = current_time
    
    def _cleanup_old_trades(self, current_time: float) -> None:
        """Remove trade timestamps older than 1 hour"""
        hour_ago = current_time - 3600
        while self.trade_timestamps and self.trade_timestamps[0] < hour_ago:
            self.trade_timestamps.popleft()
    
    def get_status(self) -> dict:
        """Get current circuit breaker status"""
        with self._lock:
            current_time = time.time()
            self._cleanup_old_trades(current_time)
            
            time

---
*NONE context | HIGH clarity*
