"""
Metrics & Tracing - Production observability.

Provides metrics collection, Prometheus export, and OpenTelemetry tracing
for monitoring Nexus in production environments.
"""

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import logging


logger = logging.getLogger(__name__)


# ============================================================================
# Metrics Collection
# ============================================================================

class MetricType(Enum):
    """Types of metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class MetricValue:
    """A single metric value with labels."""
    name: str
    type: MetricType
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    help_text: str = ""


class MetricsCollector:
    """
    Collects and stores metrics.

    Thread-safe metrics collection with support for counters, gauges,
    histograms, and summaries.
    """

    def __init__(self, prefix: str = "nexus"):
        """
        Initialize metrics collector.

        Args:
            prefix: Prefix for all metric names
        """
        self.prefix = prefix
        self._counters: Dict[str, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._gauges: Dict[str, Dict[str, float]] = defaultdict(dict)
        self._histograms: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self._help_texts: Dict[str, str] = {}
        self._lock = asyncio.Lock()

    def _make_name(self, name: str) -> str:
        """Create full metric name with prefix."""
        return f"{self.prefix}_{name}"

    def _labels_key(self, labels: Dict[str, str]) -> str:
        """Create a hashable key from labels."""
        return ",".join(f"{k}={v}" for k, v in sorted(labels.items()))

    async def inc_counter(
        self,
        name: str,
        value: float = 1,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """
        Increment a counter.

        Args:
            name: Metric name
            value: Value to add
            labels: Optional labels
            help_text: Help text for the metric
        """
        full_name = self._make_name(name)
        labels = labels or {}
        key = self._labels_key(labels)

        async with self._lock:
            self._counters[full_name][key] += value
            if help_text:
                self._help_texts[full_name] = help_text

    async def set_gauge(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """
        Set a gauge value.

        Args:
            name: Metric name
            value: Value to set
            labels: Optional labels
            help_text: Help text for the metric
        """
        full_name = self._make_name(name)
        labels = labels or {}
        key = self._labels_key(labels)

        async with self._lock:
            self._gauges[full_name][key] = value
            if help_text:
                self._help_texts[full_name] = help_text

    async def observe_histogram(
        self,
        name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None,
        help_text: str = ""
    ) -> None:
        """
        Record a histogram observation.

        Args:
            name: Metric name
            value: Value to observe
            labels: Optional labels
            help_text: Help text for the metric
        """
        full_name = self._make_name(name)
        labels = labels or {}
        key = self._labels_key(labels)

        async with self._lock:
            self._histograms[full_name][key].append(value)
            # Keep last 1000 observations per label set
            if len(self._histograms[full_name][key]) > 1000:
                self._histograms[full_name][key] = self._histograms[full_name][key][-1000:]
            if help_text:
                self._help_texts[full_name] = help_text

    @asynccontextmanager
    async def timer(
        self,
        name: str,
        labels: Optional[Dict[str, str]] = None
    ):
        """
        Context manager to time operations.

        Usage:
            async with metrics.timer("request_duration", {"provider": "openai"}):
                await make_request()
        """
        start = time.monotonic()
        try:
            yield
        finally:
            duration = time.monotonic() - start
            await self.observe_histogram(name, duration, labels)

    async def get_all_metrics(self) -> List[MetricValue]:
        """Get all collected metrics."""
        metrics = []

        async with self._lock:
            # Counters
            for name, label_values in self._counters.items():
                for label_key, value in label_values.items():
                    labels = dict(item.split("=") for item in label_key.split(",") if item)
                    metrics.append(MetricValue(
                        name=name,
                        type=MetricType.COUNTER,
                        value=value,
                        labels=labels,
                        help_text=self._help_texts.get(name, ""),
                    ))

            # Gauges
            for name, label_values in self._gauges.items():
                for label_key, value in label_values.items():
                    labels = dict(item.split("=") for item in label_key.split(",") if item)
                    metrics.append(MetricValue(
                        name=name,
                        type=MetricType.GAUGE,
                        value=value,
                        labels=labels,
                        help_text=self._help_texts.get(name, ""),
                    ))

            # Histograms (emit count, sum, and buckets)
            for name, label_values in self._histograms.items():
                for label_key, values in label_values.items():
                    if not values:
                        continue
                    labels = dict(item.split("=") for item in label_key.split(",") if item)

                    # Count
                    metrics.append(MetricValue(
                        name=f"{name}_count",
                        type=MetricType.COUNTER,
                        value=len(values),
                        labels=labels,
                    ))

                    # Sum
                    metrics.append(MetricValue(
                        name=f"{name}_sum",
                        type=MetricType.COUNTER,
                        value=sum(values),
                        labels=labels,
                    ))

                    # Quantiles
                    sorted_values = sorted(values)
                    for q in [0.5, 0.9, 0.95, 0.99]:
                        idx = int(len(sorted_values) * q)
                        metrics.append(MetricValue(
                            name=name,
                            type=MetricType.SUMMARY,
                            value=sorted_values[min(idx, len(sorted_values) - 1)],
                            labels={**labels, "quantile": str(q)},
                        ))

        return metrics

    def to_prometheus(self) -> str:
        """
        Export metrics in Prometheus text format.

        Returns:
            Prometheus-formatted metrics string
        """
        lines = []
        metrics = asyncio.get_event_loop().run_until_complete(self.get_all_metrics())

        # Group by name for proper formatting
        by_name: Dict[str, List[MetricValue]] = defaultdict(list)
        for m in metrics:
            by_name[m.name].append(m)

        for name, metric_list in sorted(by_name.items()):
            # Help text
            if metric_list[0].help_text:
                lines.append(f"# HELP {name} {metric_list[0].help_text}")

            # Type
            type_name = metric_list[0].type.value
            if type_name == "summary":
                type_name = "summary"
            lines.append(f"# TYPE {name} {type_name}")

            # Values
            for m in metric_list:
                label_str = ""
                if m.labels:
                    label_parts = [f'{k}="{v}"' for k, v in sorted(m.labels.items())]
                    label_str = "{" + ",".join(label_parts) + "}"
                lines.append(f"{name}{label_str} {m.value}")

            lines.append("")

        return "\n".join(lines)


# ============================================================================
# Nexus-specific Metrics
# ============================================================================

class NexusMetrics:
    """
    Pre-defined metrics for Nexus operations.

    Provides convenience methods for recording common metrics.
    """

    def __init__(self, collector: Optional[MetricsCollector] = None):
        self.collector = collector or MetricsCollector()

    async def record_request(
        self,
        provider: str,
        model: str,
        success: bool,
        duration_seconds: float,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cost: float = 0.0,
    ) -> None:
        """Record an AI provider request."""
        labels = {"provider": provider, "model": model}
        status = "success" if success else "error"

        # Request count
        await self.collector.inc_counter(
            "requests_total",
            labels={**labels, "status": status},
            help_text="Total number of requests"
        )

        # Duration
        await self.collector.observe_histogram(
            "request_duration_seconds",
            duration_seconds,
            labels=labels,
            help_text="Request duration in seconds"
        )

        # Tokens
        if input_tokens:
            await self.collector.inc_counter(
                "tokens_total",
                input_tokens,
                labels={**labels, "type": "input"},
                help_text="Total tokens processed"
            )
        if output_tokens:
            await self.collector.inc_counter(
                "tokens_total",
                output_tokens,
                labels={**labels, "type": "output"},
                help_text="Total tokens processed"
            )

        # Cost
        if cost > 0:
            await self.collector.inc_counter(
                "cost_total",
                cost,
                labels=labels,
                help_text="Total cost in USD"
            )

    async def record_tool_call(
        self,
        tool_name: str,
        success: bool,
        duration_seconds: float,
    ) -> None:
        """Record a tool execution."""
        status = "success" if success else "error"

        await self.collector.inc_counter(
            "tool_calls_total",
            labels={"tool": tool_name, "status": status},
            help_text="Total tool calls"
        )

        await self.collector.observe_histogram(
            "tool_duration_seconds",
            duration_seconds,
            labels={"tool": tool_name},
            help_text="Tool execution duration"
        )

    async def record_task_execution(
        self,
        provider: str,
        success: bool,
        iterations: int,
        duration_seconds: float,
    ) -> None:
        """Record a task execution."""
        status = "success" if success else "error"

        await self.collector.inc_counter(
            "tasks_total",
            labels={"provider": provider, "status": status},
            help_text="Total tasks executed"
        )

        await self.collector.observe_histogram(
            "task_duration_seconds",
            duration_seconds,
            labels={"provider": provider},
            help_text="Task execution duration"
        )

        await self.collector.observe_histogram(
            "task_iterations",
            iterations,
            labels={"provider": provider},
            help_text="Iterations per task"
        )

    async def set_active_sessions(self, count: int) -> None:
        """Set the number of active sessions."""
        await self.collector.set_gauge(
            "active_sessions",
            count,
            help_text="Number of active sessions"
        )

    async def record_rate_limit(self, provider: str) -> None:
        """Record a rate limit hit."""
        await self.collector.inc_counter(
            "rate_limits_total",
            labels={"provider": provider},
            help_text="Rate limit hits"
        )

    async def record_circuit_breaker(
        self,
        provider: str,
        state: str
    ) -> None:
        """Record circuit breaker state change."""
        await self.collector.inc_counter(
            "circuit_breaker_state_changes_total",
            labels={"provider": provider, "state": state},
            help_text="Circuit breaker state changes"
        )

    async def record_fallback(
        self,
        from_provider: str,
        to_provider: str,
    ) -> None:
        """Record a provider fallback."""
        await self.collector.inc_counter(
            "fallbacks_total",
            labels={"from": from_provider, "to": to_provider},
            help_text="Provider fallbacks"
        )

    def get_prometheus_metrics(self) -> str:
        """Get metrics in Prometheus format."""
        return self.collector.to_prometheus()


# ============================================================================
# OpenTelemetry Tracing (Optional)
# ============================================================================

class Span:
    """Simple span for tracing (compatible with OpenTelemetry)."""

    def __init__(
        self,
        name: str,
        parent: Optional["Span"] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.parent = parent
        self.attributes = attributes or {}
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "OK"
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a span attribute."""
        self.attributes[key] = value

    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
        """Add an event to the span."""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {},
        })

    def set_status(self, status: str, description: str = "") -> None:
        """Set span status."""
        self.status = status
        if description:
            self.attributes["status_description"] = description

    def end(self) -> None:
        """End the span."""
        self.end_time = time.time()

    @property
    def duration(self) -> float:
        """Get span duration in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> Dict[str, Any]:
        """Convert span to dictionary."""
        return {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_seconds": self.duration,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
        }


class Tracer:
    """
    Simple tracer for distributed tracing.

    Can be extended to integrate with OpenTelemetry, Jaeger, etc.
    """

    def __init__(
        self,
        service_name: str = "nexus",
        exporter: Optional[Callable[[Span], None]] = None
    ):
        """
        Initialize tracer.

        Args:
            service_name: Name of the service
            exporter: Optional function to export spans
        """
        self.service_name = service_name
        self.exporter = exporter
        self._current_span: Optional[Span] = None

    @asynccontextmanager
    async def start_span(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None
    ):
        """
        Start a new span.

        Usage:
            async with tracer.start_span("my_operation", {"key": "value"}):
                await do_work()
        """
        span = Span(
            name=name,
            parent=self._current_span,
            attributes=attributes,
        )
        span.set_attribute("service.name", self.service_name)

        previous_span = self._current_span
        self._current_span = span

        try:
            yield span
            span.set_status("OK")
        except Exception as e:
            span.set_status("ERROR", str(e))
            span.add_event("exception", {"type": type(e).__name__, "message": str(e)})
            raise
        finally:
            span.end()
            self._current_span = previous_span

            if self.exporter:
                try:
                    self.exporter(span)
                except Exception as e:
                    logger.warning(f"Failed to export span: {e}")

    def get_current_span(self) -> Optional[Span]:
        """Get the current active span."""
        return self._current_span


# ============================================================================
# FastAPI Integration
# ============================================================================

def create_metrics_endpoint(metrics: NexusMetrics):
    """
    Create a FastAPI endpoint for Prometheus metrics.

    Usage:
        from fastapi import FastAPI
        app = FastAPI()
        metrics = NexusMetrics()
        app.get("/metrics")(create_metrics_endpoint(metrics))
    """
    async def metrics_endpoint():
        from fastapi.responses import PlainTextResponse
        return PlainTextResponse(
            content=metrics.get_prometheus_metrics(),
            media_type="text/plain"
        )

    return metrics_endpoint


# ============================================================================
# Global instances
# ============================================================================

_global_metrics: Optional[NexusMetrics] = None
_global_tracer: Optional[Tracer] = None


def get_metrics() -> NexusMetrics:
    """Get global metrics instance."""
    global _global_metrics
    if _global_metrics is None:
        _global_metrics = NexusMetrics()
    return _global_metrics


def get_tracer(service_name: str = "nexus") -> Tracer:
    """Get global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer(service_name)
    return _global_tracer
