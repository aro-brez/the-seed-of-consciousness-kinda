"""
CIRCUIT BREAKER - Prevent cascade failures

OpenClaw-style circuit breaker with:
- Three states: CLOSED (normal), OPEN (failing), HALF_OPEN (testing)
- Configurable failure thresholds
- Automatic recovery testing
- Per-service isolation
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, Callable, Any
from functools import wraps
import threading


class CircuitState(Enum):
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject all calls
    HALF_OPEN = "half_open" # Testing if recovered


@dataclass
class CircuitConfig:
    """Circuit breaker configuration"""
    failure_threshold: int = 5          # Failures before opening
    success_threshold: int = 2          # Successes to close from half-open
    timeout_seconds: float = 30.0       # Time before testing recovery
    half_open_max_calls: int = 1        # Calls allowed in half-open state

    # Track slow calls as failures
    slow_call_threshold: float = 10.0   # Seconds
    slow_call_rate_threshold: float = 0.5  # 50% slow = open


class CircuitBreakerOpen(Exception):
    """Raised when circuit is open"""
    def __init__(self, service: str, open_until: datetime):
        self.service = service
        self.open_until = open_until
        super().__init__(f"Circuit breaker open for {service} until {open_until}")


@dataclass
class CircuitMetrics:
    """Track circuit breaker metrics"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    slow_calls: int = 0
    rejected_calls: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changes: int = 0

    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    def slow_call_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.slow_calls / self.total_calls

    def to_dict(self) -> dict:
        return {
            'total_calls': self.total_calls,
            'successful_calls': self.successful_calls,
            'failed_calls': self.failed_calls,
            'slow_calls': self.slow_calls,
            'rejected_calls': self.rejected_calls,
            'failure_rate': f"{self.failure_rate():.1%}",
            'slow_call_rate': f"{self.slow_call_rate():.1%}",
            'last_failure': self.last_failure_time.isoformat() if self.last_failure_time else None,
            'last_success': self.last_success_time.isoformat() if self.last_success_time else None,
            'state_changes': self.state_changes
        }


class CircuitBreaker:
    """
    Circuit breaker implementation.

    Usage:
        breaker = CircuitBreaker("polymarket_api")

        async with breaker:
            response = await fetch_markets()

        # Or as decorator
        @breaker.wrap
        async def fetch_markets():
            ...
    """

    # Global registry of circuit breakers
    _instances: Dict[str, 'CircuitBreaker'] = {}
    _lock = threading.Lock()

    def __init__(
        self,
        name: str,
        config: Optional[CircuitConfig] = None
    ):
        self.name = name
        self.config = config or CircuitConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time: Optional[float] = None
        self._open_until: Optional[datetime] = None
        self.metrics = CircuitMetrics()
        self._lock = asyncio.Lock()

        # Register in global registry
        with CircuitBreaker._lock:
            CircuitBreaker._instances[name] = self

    @classmethod
    def get(cls, name: str) -> Optional['CircuitBreaker']:
        """Get circuit breaker by name"""
        return cls._instances.get(name)

    @classmethod
    def get_all_metrics(cls) -> Dict[str, dict]:
        """Get metrics for all circuit breakers"""
        return {
            name: {
                'state': cb.state.value,
                'metrics': cb.metrics.to_dict()
            }
            for name, cb in cls._instances.items()
        }

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    def _should_allow_request(self) -> bool:
        """Check if request should be allowed"""
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            # Check if timeout has elapsed
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.timeout_seconds:
                    self._transition_to_half_open()
                    return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.config.half_open_max_calls

        return False

    def _transition_to_open(self):
        """Transition to OPEN state"""
        self._state = CircuitState.OPEN
        self._open_until = datetime.now() + timedelta(seconds=self.config.timeout_seconds)
        self._last_failure_time = time.time()
        self.metrics.state_changes += 1

    def _transition_to_half_open(self):
        """Transition to HALF_OPEN state"""
        self._state = CircuitState.HALF_OPEN
        self._half_open_calls = 0
        self._success_count = 0
        self.metrics.state_changes += 1

    def _transition_to_closed(self):
        """Transition to CLOSED state"""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._open_until = None
        self.metrics.state_changes += 1

    def _record_success(self, duration: float):
        """Record a successful call"""
        self.metrics.total_calls += 1
        self.metrics.successful_calls += 1
        self.metrics.last_success_time = datetime.now()

        if duration > self.config.slow_call_threshold:
            self.metrics.slow_calls += 1

        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._transition_to_closed()
        elif self._state == CircuitState.CLOSED:
            # Reset failure count on success
            self._failure_count = 0

    def _record_failure(self, exception: Exception):
        """Record a failed call"""
        self.metrics.total_calls += 1
        self.metrics.failed_calls += 1
        self.metrics.last_failure_time = datetime.now()
        self._last_failure_time = time.time()

        if self._state == CircuitState.HALF_OPEN:
            # Any failure in half-open reopens the circuit
            self._transition_to_open()
        elif self._state == CircuitState.CLOSED:
            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                self._transition_to_open()

    async def __aenter__(self):
        """Async context manager entry"""
        async with self._lock:
            if not self._should_allow_request():
                self.metrics.rejected_calls += 1
                raise CircuitBreakerOpen(self.name, self._open_until)

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls += 1

        self._call_start_time = time.time()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        duration = time.time() - self._call_start_time

        async with self._lock:
            if exc_val is None:
                self._record_success(duration)
            else:
                self._record_failure(exc_val)

        return False  # Don't suppress exceptions

    def wrap(self, func: Callable) -> Callable:
        """Decorator to wrap function with circuit breaker"""
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            async with self:
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, use a simplified check
            if not self._should_allow_request():
                self.metrics.rejected_calls += 1
                raise CircuitBreakerOpen(self.name, self._open_until)

            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                self._record_success(time.time() - start_time)
                return result
            except Exception as e:
                self._record_failure(e)
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def reset(self):
        """Manually reset the circuit breaker"""
        self._transition_to_closed()
        self.metrics = CircuitMetrics()
