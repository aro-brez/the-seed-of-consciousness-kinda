"""
RETRY WITH EXPONENTIAL BACKOFF

OpenClaw-style retry logic with:
- Configurable retry counts and delays
- Exponential backoff with jitter
- Specific exception filtering
- Timeout support
"""

import asyncio
import random
from dataclasses import dataclass, field
from typing import Type, Tuple, Callable, Any, Optional, Union
from functools import wraps

from .exceptions import BaseOwlsError, RateLimitError


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    initial_delay: float = 1.0       # seconds
    max_delay: float = 60.0          # seconds
    exponential_base: float = 2.0
    jitter: bool = True              # Add randomness to prevent thundering herd
    jitter_factor: float = 0.25

    # Exceptions that should trigger retry
    retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            ConnectionError,
            TimeoutError,
            asyncio.TimeoutError,
        )
    )

    # Exceptions that should NOT retry (even if otherwise retryable)
    non_retryable_exceptions: Tuple[Type[Exception], ...] = field(
        default_factory=lambda: (
            KeyboardInterrupt,
            SystemExit,
            MemoryError,
        )
    )


def calculate_delay(
    attempt: int,
    config: RetryConfig,
    rate_limit_delay: Optional[float] = None
) -> float:
    """Calculate delay before next retry"""
    if rate_limit_delay is not None:
        return rate_limit_delay

    # Exponential backoff
    delay = config.initial_delay * (config.exponential_base ** attempt)
    delay = min(delay, config.max_delay)

    # Add jitter
    if config.jitter:
        jitter_range = delay * config.jitter_factor
        delay = delay + random.uniform(-jitter_range, jitter_range)

    return max(0, delay)


def should_retry(
    exception: Exception,
    config: RetryConfig,
    attempt: int
) -> bool:
    """Determine if we should retry based on exception type"""
    # Never retry non-retryable exceptions
    if isinstance(exception, config.non_retryable_exceptions):
        return False

    # Check if max attempts exceeded
    if attempt >= config.max_attempts:
        return False

    # Check BaseOwlsError retryable flag
    if isinstance(exception, BaseOwlsError):
        return exception.retryable

    # Check configured retryable exceptions
    return isinstance(exception, config.retryable_exceptions)


def retry_with_backoff(
    config: Optional[RetryConfig] = None,
    on_retry: Optional[Callable[[Exception, int, float], None]] = None,
    on_failure: Optional[Callable[[Exception, int], None]] = None,
):
    """
    Decorator for retry with exponential backoff.

    Usage:
        @retry_with_backoff()
        async def fetch_data():
            ...

        @retry_with_backoff(RetryConfig(max_attempts=5))
        async def critical_operation():
            ...
    """
    if config is None:
        config = RetryConfig()

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if not should_retry(e, config, attempt + 1):
                        if on_failure:
                            on_failure(e, attempt + 1)
                        raise

                    # Calculate delay (special handling for rate limits)
                    rate_limit_delay = None
                    if isinstance(e, RateLimitError):
                        rate_limit_delay = float(e.retry_after)

                    delay = calculate_delay(attempt, config, rate_limit_delay)

                    # Callback before retry
                    if on_retry:
                        on_retry(e, attempt + 1, delay)

                    await asyncio.sleep(delay)

            # All retries exhausted
            if on_failure:
                on_failure(last_exception, config.max_attempts)
            raise last_exception

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            import time
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except Exception as e:
                    last_exception = e

                    if not should_retry(e, config, attempt + 1):
                        if on_failure:
                            on_failure(e, attempt + 1)
                        raise

                    delay = calculate_delay(attempt, config)

                    if on_retry:
                        on_retry(e, attempt + 1, delay)

                    time.sleep(delay)

            if on_failure:
                on_failure(last_exception, config.max_attempts)
            raise last_exception

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


class RetryContext:
    """Context manager for retry blocks"""

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        logger: Optional[Any] = None
    ):
        self.config = config or RetryConfig()
        self.logger = logger
        self.attempt = 0
        self.last_exception = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_val is None:
            return False

        self.last_exception = exc_val
        self.attempt += 1

        if should_retry(exc_val, self.config, self.attempt):
            delay = calculate_delay(self.attempt - 1, self.config)

            if self.logger:
                self.logger.warning(
                    f"Retry {self.attempt}/{self.config.max_attempts} after {delay:.1f}s: {exc_val}"
                )

            await asyncio.sleep(delay)
            return True  # Suppress exception, will retry

        return False  # Re-raise exception
