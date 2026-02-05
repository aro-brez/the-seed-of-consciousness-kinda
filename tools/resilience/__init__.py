"""
RESILIENCE MODULE - OpenClaw-style Self-Healing Error Recovery

Production-grade error handling for 8OWLS daemons:
- Specific exception handling (no bare except)
- Retry logic with exponential backoff
- Circuit breakers for external services
- Health check endpoints
- Graceful degradation
- Structured logging
"""

from .exceptions import (
    BaseOwlsError,
    NATSConnectionError,
    APIConnectionError,
    MarketDataError,
    ConfigurationError,
    RateLimitError,
    ValidationError,
)
from .retry import retry_with_backoff, RetryConfig
from .circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from .health import HealthCheck, HealthStatus
from .logger import StructuredLogger

__all__ = [
    # Exceptions
    'BaseOwlsError',
    'NATSConnectionError',
    'APIConnectionError',
    'MarketDataError',
    'ConfigurationError',
    'RateLimitError',
    'ValidationError',
    # Retry
    'retry_with_backoff',
    'RetryConfig',
    # Circuit Breaker
    'CircuitBreaker',
    'CircuitBreakerOpen',
    # Health
    'HealthCheck',
    'HealthStatus',
    # Logging
    'StructuredLogger',
]
