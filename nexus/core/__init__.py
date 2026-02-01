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
]