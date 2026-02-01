"""Core components of the Nexus unified wrapper."""

from .unified_wrapper import UnifiedAIWrapper
from .base_connector import BaseConnector, AIProvider
from .task_result import TaskResult
from .tool_executor import ToolExecutor
from .tool_registry import (
    ToolRegistry,
    ToolMetadata,
    ToolParameter,
    tool,
    get_default_registry,
    register_tool,
)
from .execution_log import ExecutionLog, LogEvent, LogEventType, ExecutionMetrics
from .mcp_client import (
    MCPManager,
    MCPConnection,
    MCPServerConfig,
    MCPTool,
    MCPResource,
    MCPError,
    MCPTransport,
    MCPServerState,
)
from .router import (
    Router,
    RoutingStrategy,
    ProviderConfig,
    ProviderStats,
    TaskClassifier,
    create_router_from_env,
)
from .retry import (
    RetryHandler,
    RetryConfig,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    RetryExhaustedError,
    with_retry,
    RETRY_CONFIGS,
)
from .rate_limiter import (
    RateLimiter,
    TokenBucketLimiter,
    SlidingWindowLimiter,
    ConcurrencyLimiter,
    ProviderRateLimiter,
    RateLimitConfig,
    RateLimitExceeded,
    get_rate_limiter,
)
from .metrics import (
    MetricsCollector,
    NexusMetrics,
    Tracer,
    Span,
    get_metrics,
    get_tracer,
)

__all__ = [
    "UnifiedAIWrapper",
    "BaseConnector",
    "AIProvider",
    "TaskResult",
    "ToolExecutor",
    # Tool registry exports
    "ToolRegistry",
    "ToolMetadata",
    "ToolParameter",
    "tool",
    "get_default_registry",
    "register_tool",
    # Execution log exports
    "ExecutionLog",
    "LogEvent",
    "LogEventType",
    "ExecutionMetrics",
    # MCP exports
    "MCPManager",
    "MCPConnection",
    "MCPServerConfig",
    "MCPTool",
    "MCPResource",
    "MCPError",
    "MCPTransport",
    "MCPServerState",
    # Router exports
    "Router",
    "RoutingStrategy",
    "ProviderConfig",
    "ProviderStats",
    "TaskClassifier",
    "create_router_from_env",
    # Retry exports
    "RetryHandler",
    "RetryConfig",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitOpenError",
    "RetryExhaustedError",
    "with_retry",
    "RETRY_CONFIGS",
    # Rate limiter exports
    "RateLimiter",
    "TokenBucketLimiter",
    "SlidingWindowLimiter",
    "ConcurrencyLimiter",
    "ProviderRateLimiter",
    "RateLimitConfig",
    "RateLimitExceeded",
    "get_rate_limiter",
    # Metrics exports
    "MetricsCollector",
    "NexusMetrics",
    "Tracer",
    "Span",
    "get_metrics",
    "get_tracer",
]