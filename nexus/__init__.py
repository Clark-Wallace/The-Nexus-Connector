"""
The Nexus Connector

Universal AI connection interface - Establish a Nexus Connection with any AI provider.
"""

from dotenv import load_dotenv as _load_dotenv
_load_dotenv()

from ._version import __version__, __version_info__

__author__ = "Nexus Team"
__email__ = "support@nexus-ai.dev"

from .core.unified_wrapper import UnifiedAIWrapper as NexusConnector
from .core.base_connector import AIProvider, BaseConnector
from .core.task_result import TaskResult
from .core.exceptions import NexusError, ProviderError, ToolExecutionError
from .core.tool_registry import tool, ToolRegistry, ToolMetadata
from .core.mcp_client import MCPManager, MCPServerConfig, MCPError
from .core.router import Router, RoutingStrategy, ProviderConfig, create_router_from_env
from .core.retry import RetryConfig, CircuitBreaker, RetryHandler, RETRY_CONFIGS
from .core.rate_limiter import RateLimitConfig, get_rate_limiter
from .core.metrics import NexusMetrics, get_metrics, get_tracer

# Web components (optional import)
try:
    from .web import WebConnector
    from .connectors.gm_connector import GMConnector, create_gm_server
    __all__ = [
        "NexusConnector",
        "AIProvider",
        "BaseConnector",
        "TaskResult",
        "NexusError",
        "ProviderError",
        "ToolExecutionError",
        # Tool system
        "tool",
        "ToolRegistry",
        "ToolMetadata",
        # MCP
        "MCPManager",
        "MCPServerConfig",
        "MCPError",
        # Router
        "Router",
        "RoutingStrategy",
        "ProviderConfig",
        "create_router_from_env",
        # Production hardening
        "RetryConfig",
        "CircuitBreaker",
        "RetryHandler",
        "RETRY_CONFIGS",
        "RateLimitConfig",
        "get_rate_limiter",
        "NexusMetrics",
        "get_metrics",
        "get_tracer",
        # Web extensions
        "WebConnector",
        "GMConnector",
        "create_gm_server",
    ]
except ImportError:
    # Web components not available (missing dependencies)
    __all__ = [
        "NexusConnector",
        "AIProvider",
        "BaseConnector",
        "TaskResult",
        "NexusError",
        "ProviderError",
        "ToolExecutionError",
        # Tool system
        "tool",
        "ToolRegistry",
        "ToolMetadata",
        # MCP
        "MCPManager",
        "MCPServerConfig",
        "MCPError",
        # Router
        "Router",
        "RoutingStrategy",
        "ProviderConfig",
        "create_router_from_env",
        # Production hardening
        "RetryConfig",
        "CircuitBreaker",
        "RetryHandler",
        "RETRY_CONFIGS",
        "RateLimitConfig",
        "get_rate_limiter",
        "NexusMetrics",
        "get_metrics",
        "get_tracer",
    ]