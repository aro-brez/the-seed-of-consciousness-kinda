"""
STRUCTURED LOGGER - Proper error logging (no silent failures)

Features:
- JSON structured logs for parsing
- Log levels with filtering
- Context enrichment
- File and console output
- Error correlation IDs
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Any, Dict
from dataclasses import dataclass, field, asdict


@dataclass
class LogContext:
    """Contextual information for log entries"""
    service: str = ""
    operation: str = ""
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    additional: dict = field(default_factory=dict)


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    service: str
    message: str
    correlation_id: str
    operation: str = ""
    error_type: str = ""
    error_details: dict = field(default_factory=dict)
    additional: dict = field(default_factory=dict)

    def to_json(self) -> str:
        data = asdict(self)
        # Remove empty fields
        data = {k: v for k, v in data.items() if v}
        return json.dumps(data)

    def to_human(self) -> str:
        """Human-readable format"""
        parts = [
            f"[{self.timestamp}]",
            f"[{self.level}]",
            f"[{self.service}]",
        ]
        if self.operation:
            parts.append(f"[{self.operation}]")
        if self.correlation_id:
            parts.append(f"[{self.correlation_id}]")
        parts.append(self.message)

        if self.error_type:
            parts.append(f"| Error: {self.error_type}")

        return " ".join(parts)


class StructuredLogger:
    """
    Structured logger with JSON and human-readable output.

    Usage:
        logger = StructuredLogger("owl_daemon", log_file="/path/to/daemon.log")

        logger.info("Started successfully")
        logger.error("Connection failed", error=exc, operation="nats_connect")

        # With context
        with logger.context(operation="handle_message") as ctx:
            ctx.info("Processing message")
            ctx.warning("Slow processing", additional={'duration': 5.2})
    """

    def __init__(
        self,
        service_name: str,
        log_file: Optional[Path] = None,
        log_level: str = "INFO",
        json_output: bool = False,  # Human-readable by default
        console_output: bool = True
    ):
        self.service_name = service_name
        self.log_file = Path(log_file) if log_file else None
        self.json_output = json_output
        self.console_output = console_output
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)

        # Current context stack
        self._context_stack: list = []

        # Ensure log directory exists
        if self.log_file:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _current_context(self) -> LogContext:
        """Get current context from stack"""
        if self._context_stack:
            return self._context_stack[-1]
        return LogContext(service=self.service_name)

    def _create_entry(
        self,
        level: str,
        message: str,
        error: Optional[Exception] = None,
        operation: Optional[str] = None,
        additional: Optional[dict] = None
    ) -> LogEntry:
        """Create a structured log entry"""
        ctx = self._current_context()

        error_type = ""
        error_details = {}
        if error:
            error_type = type(error).__name__
            error_details = {
                'message': str(error),
                'type': error_type
            }
            # Add rich context from BaseOwlsError
            from .exceptions import BaseOwlsError
            if isinstance(error, BaseOwlsError):
                error_details['severity'] = error.severity.value
                error_details['retryable'] = error.retryable
                error_details['recovery_hint'] = error.recovery_hint
                error_details['context'] = error.context.to_dict()

        return LogEntry(
            timestamp=datetime.now().isoformat(),
            level=level,
            service=self.service_name,
            message=message,
            correlation_id=ctx.correlation_id,
            operation=operation or ctx.operation,
            error_type=error_type,
            error_details=error_details,
            additional={**ctx.additional, **(additional or {})}
        )

    def _write(self, entry: LogEntry):
        """Write log entry to outputs"""
        level_num = getattr(logging, entry.level.upper(), logging.INFO)
        if level_num < self.log_level:
            return

        if self.json_output:
            output = entry.to_json()
        else:
            output = entry.to_human()

        if self.console_output:
            # Use stderr for errors, stdout for others
            stream = sys.stderr if entry.level in ('ERROR', 'CRITICAL') else sys.stdout
            print(output, file=stream)

        if self.log_file:
            with open(self.log_file, 'a') as f:
                f.write(output + '\n')

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._write(self._create_entry("DEBUG", message, **kwargs))

    def info(self, message: str, **kwargs):
        """Log info message"""
        self._write(self._create_entry("INFO", message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._write(self._create_entry("WARNING", message, **kwargs))

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error message - NEVER silent"""
        self._write(self._create_entry("ERROR", message, error=error, **kwargs))

    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical message"""
        self._write(self._create_entry("CRITICAL", message, error=error, **kwargs))

    def exception(self, message: str, exc: Exception, **kwargs):
        """Log exception with full context"""
        import traceback
        tb = traceback.format_exc()
        kwargs.setdefault('additional', {})
        kwargs['additional']['traceback'] = tb
        self.error(message, error=exc, **kwargs)

    class _ContextManager:
        """Context manager for scoped logging"""

        def __init__(self, logger: 'StructuredLogger', context: LogContext):
            self.logger = logger
            self.context = context

        def __enter__(self):
            self.logger._context_stack.append(self.context)
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            self.logger._context_stack.pop()
            return False

        def debug(self, message: str, **kwargs):
            self.logger.debug(message, **kwargs)

        def info(self, message: str, **kwargs):
            self.logger.info(message, **kwargs)

        def warning(self, message: str, **kwargs):
            self.logger.warning(message, **kwargs)

        def error(self, message: str, **kwargs):
            self.logger.error(message, **kwargs)

    def context(
        self,
        operation: str = "",
        correlation_id: Optional[str] = None,
        **additional
    ) -> _ContextManager:
        """Create a logging context"""
        ctx = LogContext(
            service=self.service_name,
            operation=operation,
            correlation_id=correlation_id or str(uuid.uuid4())[:8],
            additional=additional
        )
        return self._ContextManager(self, ctx)
