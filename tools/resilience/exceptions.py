"""
SPECIFIC EXCEPTION HIERARCHY - Replace bare except blocks

Each exception type maps to a specific failure mode with:
- Clear error context
- Suggested recovery action
- Severity level for alerting
"""

from enum import Enum
from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


class Severity(Enum):
    """Error severity levels for alerting"""
    DEBUG = "debug"       # Expected, handled gracefully
    INFO = "info"         # Informational, no action needed
    WARNING = "warning"   # Degraded, but recoverable
    ERROR = "error"       # Failed, needs attention
    CRITICAL = "critical" # System down, immediate action


@dataclass
class ErrorContext:
    """Rich context for error diagnosis"""
    timestamp: datetime = field(default_factory=datetime.now)
    service: str = ""
    operation: str = ""
    input_data: Optional[Any] = None
    additional_info: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'timestamp': self.timestamp.isoformat(),
            'service': self.service,
            'operation': self.operation,
            'input_data': str(self.input_data)[:200] if self.input_data else None,
            **self.additional_info
        }


class BaseOwlsError(Exception):
    """Base exception for all 8OWLS errors"""

    severity: Severity = Severity.ERROR
    retryable: bool = False
    recovery_hint: str = "Check logs for details"

    def __init__(
        self,
        message: str,
        context: Optional[ErrorContext] = None,
        cause: Optional[Exception] = None
    ):
        super().__init__(message)
        self.message = message
        self.context = context or ErrorContext()
        self.cause = cause

    def __str__(self) -> str:
        result = f"[{self.severity.value.upper()}] {self.message}"
        if self.cause:
            result += f" | Caused by: {type(self.cause).__name__}: {self.cause}"
        return result

    def to_dict(self) -> dict:
        return {
            'error_type': type(self).__name__,
            'message': self.message,
            'severity': self.severity.value,
            'retryable': self.retryable,
            'recovery_hint': self.recovery_hint,
            'context': self.context.to_dict(),
            'cause': str(self.cause) if self.cause else None
        }


class NATSConnectionError(BaseOwlsError):
    """NATS server connection failures"""

    severity = Severity.WARNING  # Field can operate without NATS
    retryable = True
    recovery_hint = "Check NATS server at 192.168.5.108:4222. Daemon will retry."

    def __init__(self, message: str, server_url: str = "", **kwargs):
        context = ErrorContext(
            service="nats",
            operation="connect",
            additional_info={'server_url': server_url}
        )
        super().__init__(message, context=context, **kwargs)


class APIConnectionError(BaseOwlsError):
    """External API connection failures (Anthropic, Polymarket, etc.)"""

    severity = Severity.WARNING
    retryable = True
    recovery_hint = "API temporarily unavailable. Will retry with exponential backoff."

    def __init__(self, message: str, api_name: str = "", status_code: int = 0, **kwargs):
        context = ErrorContext(
            service=api_name,
            operation="api_call",
            additional_info={'status_code': status_code, 'api': api_name}
        )
        super().__init__(message, context=context, **kwargs)


class MarketDataError(BaseOwlsError):
    """Market data parsing or validation failures"""

    severity = Severity.WARNING
    retryable = False  # Bad data won't get better on retry
    recovery_hint = "Skip this market and continue. Log for manual review."

    def __init__(self, message: str, market_id: str = "", raw_data: Any = None, **kwargs):
        context = ErrorContext(
            service="market_data",
            operation="parse",
            input_data=raw_data,
            additional_info={'market_id': market_id}
        )
        super().__init__(message, context=context, **kwargs)


class ConfigurationError(BaseOwlsError):
    """Configuration or environment errors"""

    severity = Severity.CRITICAL
    retryable = False
    recovery_hint = "Check environment variables and config files."

    def __init__(self, message: str, config_key: str = "", **kwargs):
        context = ErrorContext(
            service="configuration",
            operation="load",
            additional_info={'config_key': config_key}
        )
        super().__init__(message, context=context, **kwargs)


class RateLimitError(BaseOwlsError):
    """Rate limiting from external services"""

    severity = Severity.INFO  # Expected behavior under load
    retryable = True
    recovery_hint = "Wait for rate limit window to reset."

    def __init__(self, message: str, service: str = "", retry_after: int = 60, **kwargs):
        context = ErrorContext(
            service=service,
            operation="rate_limited",
            additional_info={'retry_after_seconds': retry_after}
        )
        super().__init__(message, context=context, **kwargs)
        self.retry_after = retry_after


class ValidationError(BaseOwlsError):
    """Input validation failures"""

    severity = Severity.WARNING
    retryable = False
    recovery_hint = "Check input data format and constraints."

    def __init__(self, message: str, field: str = "", value: Any = None, **kwargs):
        context = ErrorContext(
            service="validation",
            operation="validate",
            input_data=value,
            additional_info={'field': field}
        )
        super().__init__(message, context=context, **kwargs)


class TradeExecutionError(BaseOwlsError):
    """Trade execution failures"""

    severity = Severity.ERROR
    retryable = False  # Don't retry trades automatically
    recovery_hint = "Trade failed. Check position state before manual retry."

    def __init__(self, message: str, trade_id: str = "", market: str = "", **kwargs):
        context = ErrorContext(
            service="trading",
            operation="execute",
            additional_info={'trade_id': trade_id, 'market': market}
        )
        super().__init__(message, context=context, **kwargs)


class CircuitOpenError(BaseOwlsError):
    """Circuit breaker is open - service unavailable"""

    severity = Severity.WARNING
    retryable = False  # Circuit must reset first
    recovery_hint = "Service circuit breaker is open. Wait for recovery."

    def __init__(self, message: str, service: str = "", open_until: datetime = None, **kwargs):
        context = ErrorContext(
            service=service,
            operation="circuit_check",
            additional_info={'open_until': open_until.isoformat() if open_until else None}
        )
        super().__init__(message, context=context, **kwargs)
