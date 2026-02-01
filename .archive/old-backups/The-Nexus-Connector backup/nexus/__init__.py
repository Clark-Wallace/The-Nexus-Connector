"""
The Nexus Connector

Universal AI connection interface - Establish a Nexus Connection with any AI provider.
"""

from ._version import __version__, __version_info__

__author__ = "Nexus Team"
__email__ = "support@nexus-ai.dev"

from .core.unified_wrapper import UnifiedAIWrapper as NexusConnector
from .core.base_connector import AIProvider, BaseConnector
from .core.task_result import TaskResult
from .core.exceptions import NexusError, ProviderError, ToolExecutionError

# Web components (optional import)
try:
    from .web import WebConnector, WebEnabledWrapper
    from .connectors.gm_connector import GMConnector, create_gm_server
    __all__ = [
        "NexusConnector",
        "AIProvider",
        "BaseConnector",
        "TaskResult",
        "NexusError",
        "ProviderError",
        "ToolExecutionError",
        # Web extensions
        "WebConnector",
        "WebEnabledWrapper",
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
    ]