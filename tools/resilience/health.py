"""
HEALTH CHECK - Monitor daemon health

Provides:
- Health status tracking
- Dependency health aggregation
- HTTP health endpoints
- Liveness and readiness probes
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Callable, Optional, Any
import json


class HealthStatus(Enum):
    """Health status levels"""
    HEALTHY = "healthy"         # All systems operational
    DEGRADED = "degraded"       # Some issues, but functional
    UNHEALTHY = "unhealthy"     # Critical failures


@dataclass
class ComponentHealth:
    """Health status of a single component"""
    name: str
    status: HealthStatus
    message: str = ""
    last_check: datetime = field(default_factory=datetime.now)
    details: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'status': self.status.value,
            'message': self.message,
            'last_check': self.last_check.isoformat(),
            'details': self.details
        }


@dataclass
class HealthReport:
    """Aggregated health report"""
    status: HealthStatus
    components: List[ComponentHealth]
    uptime_seconds: float
    version: str = "2.0.0"

    def to_dict(self) -> dict:
        return {
            'status': self.status.value,
            'uptime_seconds': round(self.uptime_seconds, 2),
            'version': self.version,
            'timestamp': datetime.now().isoformat(),
            'components': [c.to_dict() for c in self.components]
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class HealthCheck:
    """
    Health check manager for daemons.

    Usage:
        health = HealthCheck("owl_daemon")

        # Register component checks
        health.register("nats", check_nats_connection)
        health.register("anthropic_api", check_api_key)

        # Get health report
        report = await health.check()

        # Start background monitoring
        await health.start_monitoring(interval=30)
    """

    def __init__(
        self,
        service_name: str,
        version: str = "2.0.0"
    ):
        self.service_name = service_name
        self.version = version
        self._start_time = time.time()
        self._checks: Dict[str, Callable] = {}
        self._last_results: Dict[str, ComponentHealth] = {}
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_ready = False

    @property
    def uptime(self) -> float:
        return time.time() - self._start_time

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def register(
        self,
        component_name: str,
        check_func: Callable[[], ComponentHealth],
        critical: bool = False
    ):
        """
        Register a health check function.

        Args:
            component_name: Name of the component
            check_func: Function that returns ComponentHealth
            critical: If True, failure makes overall status UNHEALTHY
        """
        self._checks[component_name] = {
            'func': check_func,
            'critical': critical
        }

    async def _run_check(self, name: str, check_info: dict) -> ComponentHealth:
        """Run a single health check"""
        try:
            check_func = check_info['func']

            # Support both sync and async check functions
            if asyncio.iscoroutinefunction(check_func):
                result = await check_func()
            else:
                result = check_func()

            self._last_results[name] = result
            return result

        except Exception as e:
            result = ComponentHealth(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message=f"Check failed: {type(e).__name__}: {e}"
            )
            self._last_results[name] = result
            return result

    async def check(self) -> HealthReport:
        """Run all health checks and return aggregated report"""
        components = []
        has_critical_failure = False
        has_any_failure = False

        for name, check_info in self._checks.items():
            result = await self._run_check(name, check_info)
            components.append(result)

            if result.status == HealthStatus.UNHEALTHY:
                has_any_failure = True
                if check_info['critical']:
                    has_critical_failure = True
            elif result.status == HealthStatus.DEGRADED:
                has_any_failure = True

        # Determine overall status
        if has_critical_failure:
            overall_status = HealthStatus.UNHEALTHY
        elif has_any_failure:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY

        self._is_ready = overall_status != HealthStatus.UNHEALTHY

        return HealthReport(
            status=overall_status,
            components=components,
            uptime_seconds=self.uptime,
            version=self.version
        )

    async def liveness(self) -> bool:
        """
        Liveness probe - is the process running?
        Returns True if the daemon is alive (even if unhealthy).
        """
        return True

    async def readiness(self) -> bool:
        """
        Readiness probe - can the service handle requests?
        Returns True only if healthy or degraded.
        """
        report = await self.check()
        return report.status != HealthStatus.UNHEALTHY

    async def start_monitoring(self, interval: float = 30.0):
        """Start background health monitoring"""
        async def monitor_loop():
            while True:
                try:
                    report = await self.check()
                    if report.status == HealthStatus.UNHEALTHY:
                        # Log critical health issues
                        print(f"[HEALTH] {self.service_name}: UNHEALTHY - {report.to_json()}")
                except Exception as e:
                    print(f"[HEALTH] Monitoring error: {e}")

                await asyncio.sleep(interval)

        self._monitoring_task = asyncio.create_task(monitor_loop())

    def stop_monitoring(self):
        """Stop background health monitoring"""
        if self._monitoring_task:
            self._monitoring_task.cancel()


# Pre-built health check factories

def create_nats_check(nc) -> Callable:
    """Create health check for NATS connection"""
    def check() -> ComponentHealth:
        if nc is None:
            return ComponentHealth(
                name="nats",
                status=HealthStatus.DEGRADED,
                message="NATS not configured"
            )

        if nc.is_connected:
            return ComponentHealth(
                name="nats",
                status=HealthStatus.HEALTHY,
                message="Connected",
                details={'server': str(nc.connected_url) if hasattr(nc, 'connected_url') else 'unknown'}
            )
        else:
            return ComponentHealth(
                name="nats",
                status=HealthStatus.UNHEALTHY,
                message="Disconnected"
            )

    return check


def create_api_key_check(api_key: Optional[str], service_name: str = "api") -> Callable:
    """Create health check for API key presence"""
    def check() -> ComponentHealth:
        if api_key:
            # Mask the key for display
            masked = f"{api_key[:8]}...{api_key[-4:]}" if len(api_key) > 12 else "***"
            return ComponentHealth(
                name=service_name,
                status=HealthStatus.HEALTHY,
                message="API key configured",
                details={'key_preview': masked}
            )
        else:
            return ComponentHealth(
                name=service_name,
                status=HealthStatus.UNHEALTHY,
                message="API key not configured"
            )

    return check


def create_circuit_breaker_check(breaker) -> Callable:
    """Create health check for circuit breaker state"""
    def check() -> ComponentHealth:
        from .circuit_breaker import CircuitState

        if breaker.state == CircuitState.CLOSED:
            status = HealthStatus.HEALTHY
            message = "Circuit closed (normal)"
        elif breaker.state == CircuitState.HALF_OPEN:
            status = HealthStatus.DEGRADED
            message = "Circuit half-open (testing recovery)"
        else:
            status = HealthStatus.UNHEALTHY
            message = f"Circuit open until {breaker._open_until}"

        return ComponentHealth(
            name=f"circuit:{breaker.name}",
            status=status,
            message=message,
            details=breaker.metrics.to_dict()
        )

    return check
