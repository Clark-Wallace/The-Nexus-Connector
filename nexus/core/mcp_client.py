"""
MCP (Model Context Protocol) Client for Nexus.

Provides integration with MCP servers, allowing Nexus to use tools
from any MCP-compatible server (filesystem, github, postgres, etc.)

MCP Spec: https://modelcontextprotocol.io/
"""

import asyncio
import json
import os
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import logging

from .tool_registry import ToolRegistry, ToolMetadata, ToolParameter


logger = logging.getLogger(__name__)


class MCPTransport(Enum):
    """MCP transport types."""
    STDIO = "stdio"
    SSE = "sse"
    HTTP = "http"


class MCPServerState(Enum):
    """MCP server connection states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server."""
    name: str
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    transport: MCPTransport = MCPTransport.STDIO
    url: Optional[str] = None  # For HTTP/SSE transport
    timeout: float = 30.0
    auto_restart: bool = True
    max_retries: int = 3

    @classmethod
    def from_dict(cls, name: str, config: Dict[str, Any]) -> "MCPServerConfig":
        """Create config from dictionary (e.g., from JSON config file)."""
        return cls(
            name=name,
            command=config.get("command", ""),
            args=config.get("args", []),
            env=config.get("env", {}),
            transport=MCPTransport(config.get("transport", "stdio")),
            url=config.get("url"),
            timeout=config.get("timeout", 30.0),
            auto_restart=config.get("auto_restart", True),
            max_retries=config.get("max_retries", 3),
        )


@dataclass
class MCPTool:
    """Represents a tool discovered from an MCP server."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    server_name: str

    def to_tool_metadata(self, execute_fn: Callable) -> ToolMetadata:
        """Convert to Nexus ToolMetadata for registry integration."""
        # Extract parameters from input_schema
        parameters = []
        properties = self.input_schema.get("properties", {})
        required = self.input_schema.get("required", [])

        for param_name, param_info in properties.items():
            parameters.append(ToolParameter(
                name=param_name,
                type=param_info.get("type", "string"),
                description=param_info.get("description", ""),
                required=param_name in required,
                default=param_info.get("default"),
                enum=param_info.get("enum"),
            ))

        return ToolMetadata(
            name=f"mcp_{self.server_name}_{self.name}",
            description=f"[MCP:{self.server_name}] {self.description}",
            function=execute_fn,
            parameters=parameters,
            category=f"mcp:{self.server_name}",
            is_async=True,
        )


@dataclass
class MCPResource:
    """Represents a resource from an MCP server."""
    uri: str
    name: str
    description: Optional[str] = None
    mime_type: Optional[str] = None


class MCPConnection:
    """
    Manages connection to a single MCP server.

    Handles:
    - Process lifecycle (start/stop/restart)
    - JSON-RPC communication
    - Tool discovery and execution
    - Resource listing and reading
    """

    def __init__(self, config: MCPServerConfig):
        self.config = config
        self.state = MCPServerState.DISCONNECTED
        self.process: Optional[asyncio.subprocess.Process] = None
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self._request_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._read_task: Optional[asyncio.Task] = None
        self._retry_count = 0

    async def connect(self) -> bool:
        """Start the MCP server and establish connection."""
        if self.state == MCPServerState.CONNECTED:
            return True

        self.state = MCPServerState.CONNECTING
        logger.info(f"Connecting to MCP server: {self.config.name}")

        try:
            if self.config.transport == MCPTransport.STDIO:
                await self._connect_stdio()
            elif self.config.transport in (MCPTransport.SSE, MCPTransport.HTTP):
                await self._connect_http()
            else:
                raise ValueError(f"Unsupported transport: {self.config.transport}")

            # Initialize connection with MCP handshake
            await self._initialize()

            # Discover tools
            await self._discover_tools()

            # Discover resources
            await self._discover_resources()

            self.state = MCPServerState.CONNECTED
            self._retry_count = 0
            logger.info(f"Connected to MCP server: {self.config.name} ({len(self.tools)} tools)")
            return True

        except Exception as e:
            self.state = MCPServerState.ERROR
            logger.error(f"Failed to connect to MCP server {self.config.name}: {e}")
            return False

    async def _connect_stdio(self) -> None:
        """Connect via stdio transport (subprocess)."""
        # Merge environment
        env = os.environ.copy()
        env.update(self.config.env)

        # Start the MCP server process
        self.process = await asyncio.create_subprocess_exec(
            self.config.command,
            *self.config.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        # Start reading responses
        self._read_task = asyncio.create_task(self._read_responses())

    async def _connect_http(self) -> None:
        """Connect via HTTP/SSE transport."""
        # HTTP/SSE implementation would go here
        # For now, we focus on stdio which is most common
        raise NotImplementedError("HTTP/SSE transport not yet implemented")

    async def _read_responses(self) -> None:
        """Read and dispatch responses from the MCP server."""
        if not self.process or not self.process.stdout:
            return

        try:
            while True:
                line = await self.process.stdout.readline()
                if not line:
                    break

                try:
                    message = json.loads(line.decode().strip())
                    await self._handle_message(message)
                except json.JSONDecodeError:
                    continue

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error reading from MCP server {self.config.name}: {e}")
            self.state = MCPServerState.ERROR

    async def _handle_message(self, message: Dict[str, Any]) -> None:
        """Handle an incoming JSON-RPC message."""
        # Response to a request
        if "id" in message and message["id"] in self._pending_requests:
            future = self._pending_requests.pop(message["id"])
            if "error" in message:
                future.set_exception(MCPError(message["error"]))
            else:
                future.set_result(message.get("result"))

        # Notification from server
        elif "method" in message and "id" not in message:
            await self._handle_notification(message)

    async def _handle_notification(self, message: Dict[str, Any]) -> None:
        """Handle a notification from the MCP server."""
        method = message.get("method")
        params = message.get("params", {})

        if method == "notifications/tools/list_changed":
            # Tools have changed, rediscover
            await self._discover_tools()
        elif method == "notifications/resources/list_changed":
            # Resources have changed, rediscover
            await self._discover_resources()

    async def _send_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Send a JSON-RPC request and wait for response."""
        if not self.process or not self.process.stdin:
            raise MCPError({"code": -1, "message": "Not connected"})

        self._request_id += 1
        request_id = self._request_id

        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params

        # Create future for response
        future: asyncio.Future = asyncio.get_event_loop().create_future()
        self._pending_requests[request_id] = future

        # Send request
        request_line = json.dumps(request) + "\n"
        self.process.stdin.write(request_line.encode())
        await self.process.stdin.drain()

        # Wait for response with timeout
        try:
            return await asyncio.wait_for(future, timeout=self.config.timeout)
        except asyncio.TimeoutError:
            self._pending_requests.pop(request_id, None)
            raise MCPError({"code": -2, "message": f"Request timed out: {method}"})

    async def _initialize(self) -> None:
        """Perform MCP initialization handshake."""
        result = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "roots": {"listChanged": True},
                "sampling": {},
            },
            "clientInfo": {
                "name": "nexus",
                "version": "1.0.0",
            }
        })

        # Send initialized notification
        if self.process and self.process.stdin:
            notification = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
            }
            self.process.stdin.write((json.dumps(notification) + "\n").encode())
            await self.process.stdin.drain()

        logger.debug(f"MCP server {self.config.name} initialized: {result}")

    async def _discover_tools(self) -> None:
        """Discover available tools from the server."""
        try:
            result = await self._send_request("tools/list")
            self.tools.clear()

            for tool_data in result.get("tools", []):
                tool = MCPTool(
                    name=tool_data["name"],
                    description=tool_data.get("description", ""),
                    input_schema=tool_data.get("inputSchema", {}),
                    server_name=self.config.name,
                )
                self.tools[tool.name] = tool

            logger.debug(f"Discovered {len(self.tools)} tools from {self.config.name}")

        except Exception as e:
            logger.warning(f"Failed to discover tools from {self.config.name}: {e}")

    async def _discover_resources(self) -> None:
        """Discover available resources from the server."""
        try:
            result = await self._send_request("resources/list")
            self.resources.clear()

            for resource_data in result.get("resources", []):
                resource = MCPResource(
                    uri=resource_data["uri"],
                    name=resource_data.get("name", resource_data["uri"]),
                    description=resource_data.get("description"),
                    mime_type=resource_data.get("mimeType"),
                )
                self.resources[resource.uri] = resource

            logger.debug(f"Discovered {len(self.resources)} resources from {self.config.name}")

        except Exception as e:
            logger.warning(f"Failed to discover resources from {self.config.name}: {e}")

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Call a tool on the MCP server."""
        if self.state != MCPServerState.CONNECTED:
            raise MCPError({"code": -1, "message": "Not connected"})

        result = await self._send_request("tools/call", {
            "name": name,
            "arguments": arguments,
        })

        # MCP returns content as array of content blocks
        content = result.get("content", [])
        if content and len(content) == 1:
            # Single text result
            if content[0].get("type") == "text":
                return content[0].get("text", "")

        return content

    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the MCP server."""
        if self.state != MCPServerState.CONNECTED:
            raise MCPError({"code": -1, "message": "Not connected"})

        result = await self._send_request("resources/read", {"uri": uri})
        return result.get("contents", [])

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass

        if self.process:
            self.process.terminate()
            try:
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                self.process.kill()

        self.state = MCPServerState.DISCONNECTED
        self.tools.clear()
        self.resources.clear()
        logger.info(f"Disconnected from MCP server: {self.config.name}")

    async def health_check(self) -> bool:
        """Check if the server is healthy."""
        if self.state != MCPServerState.CONNECTED:
            return False

        try:
            await self._send_request("ping")
            return True
        except Exception:
            return False


class MCPError(Exception):
    """MCP protocol error."""

    def __init__(self, error: Dict[str, Any]):
        self.code = error.get("code", -1)
        self.message = error.get("message", "Unknown error")
        self.data = error.get("data")
        super().__init__(f"MCP Error {self.code}: {self.message}")


class MCPManager:
    """
    Manages multiple MCP server connections.

    Provides:
    - Server lifecycle management (start/stop/restart)
    - Tool aggregation across all servers
    - Registry integration
    - Health monitoring
    """

    # Well-known MCP servers with default configurations
    KNOWN_SERVERS: Dict[str, Dict[str, Any]] = {
        "filesystem": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem"],
        },
        "github": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {"GITHUB_PERSONAL_ACCESS_TOKEN": ""},
        },
        "postgres": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-postgres"],
        },
        "sqlite": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-sqlite"],
        },
        "brave-search": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-brave-search"],
            "env": {"BRAVE_API_KEY": ""},
        },
        "puppeteer": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-puppeteer"],
        },
        "slack": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-slack"],
            "env": {"SLACK_BOT_TOKEN": "", "SLACK_TEAM_ID": ""},
        },
        "memory": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-memory"],
        },
        "fetch": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-fetch"],
        },
        "time": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-time"],
        },
    }

    def __init__(self, registry: Optional[ToolRegistry] = None):
        """
        Initialize the MCP manager.

        Args:
            registry: Optional ToolRegistry to register MCP tools into
        """
        self.registry = registry
        self._connections: Dict[str, MCPConnection] = {}
        self._health_task: Optional[asyncio.Task] = None

    async def add_server(
        self,
        name: str,
        config: Optional[Union[MCPServerConfig, Dict[str, Any]]] = None,
        **kwargs
    ) -> bool:
        """
        Add and connect to an MCP server.

        Args:
            name: Server name (can be a well-known server name like "filesystem")
            config: Server configuration (optional for well-known servers)
            **kwargs: Additional config overrides

        Returns:
            True if successfully connected
        """
        # Build configuration
        if isinstance(config, MCPServerConfig):
            server_config = config
        elif config is not None:
            server_config = MCPServerConfig.from_dict(name, config)
        elif name in self.KNOWN_SERVERS:
            # Use well-known server config
            base_config = self.KNOWN_SERVERS[name].copy()
            base_config.update(kwargs)
            server_config = MCPServerConfig.from_dict(name, base_config)
        else:
            raise ValueError(
                f"Unknown server '{name}'. Provide config or use a known server: "
                f"{list(self.KNOWN_SERVERS.keys())}"
            )

        # Create connection
        connection = MCPConnection(server_config)

        # Connect
        if await connection.connect():
            self._connections[name] = connection

            # Register tools with the registry
            if self.registry:
                self._register_mcp_tools(connection)

            return True

        return False

    def _register_mcp_tools(self, connection: MCPConnection) -> None:
        """Register MCP tools with the Nexus tool registry."""
        if not self.registry:
            return

        for tool in connection.tools.values():
            # Create execution function for this tool
            async def execute_mcp_tool(
                _conn=connection,
                _tool_name=tool.name,
                **kwargs
            ) -> str:
                result = await _conn.call_tool(_tool_name, kwargs)
                if isinstance(result, str):
                    return result
                return json.dumps(result)

            # Convert to ToolMetadata and register
            metadata = tool.to_tool_metadata(execute_mcp_tool)
            self.registry._tools[metadata.name] = metadata

            # Add to category
            category = metadata.category
            if category not in self.registry._categories:
                self.registry._categories[category] = []
            self.registry._categories[category].append(metadata.name)

        logger.info(
            f"Registered {len(connection.tools)} tools from MCP server "
            f"'{connection.config.name}' to registry"
        )

    async def remove_server(self, name: str) -> bool:
        """
        Remove and disconnect from an MCP server.

        Args:
            name: Server name

        Returns:
            True if server was found and removed
        """
        if name not in self._connections:
            return False

        connection = self._connections.pop(name)

        # Unregister tools from registry
        if self.registry:
            for tool in connection.tools.values():
                tool_name = f"mcp_{connection.config.name}_{tool.name}"
                self.registry.unregister(tool_name)

        await connection.disconnect()
        return True

    async def connect_all(self, servers: List[str]) -> Dict[str, bool]:
        """
        Connect to multiple MCP servers.

        Args:
            servers: List of server names

        Returns:
            Dict mapping server name to connection success
        """
        results = {}
        for server in servers:
            results[server] = await self.add_server(server)
        return results

    async def disconnect_all(self) -> None:
        """Disconnect from all MCP servers."""
        for name in list(self._connections.keys()):
            await self.remove_server(name)

    def get_connection(self, name: str) -> Optional[MCPConnection]:
        """Get a specific server connection."""
        return self._connections.get(name)

    def get_all_tools(self) -> List[MCPTool]:
        """Get all tools from all connected servers."""
        tools = []
        for connection in self._connections.values():
            tools.extend(connection.tools.values())
        return tools

    def get_server_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all servers."""
        return {
            name: {
                "state": conn.state.value,
                "tools_count": len(conn.tools),
                "resources_count": len(conn.resources),
            }
            for name, conn in self._connections.items()
        }

    async def start_health_monitoring(self, interval: float = 30.0) -> None:
        """Start periodic health checks for all servers."""
        async def monitor():
            while True:
                await asyncio.sleep(interval)
                for name, connection in self._connections.items():
                    if not await connection.health_check():
                        logger.warning(f"MCP server {name} health check failed")
                        if connection.config.auto_restart:
                            logger.info(f"Attempting to reconnect to {name}")
                            await connection.connect()

        self._health_task = asyncio.create_task(monitor())

    async def stop_health_monitoring(self) -> None:
        """Stop health monitoring."""
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass

    @classmethod
    def list_known_servers(cls) -> List[str]:
        """List all well-known MCP server names."""
        return list(cls.KNOWN_SERVERS.keys())

    async def __aenter__(self) -> "MCPManager":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.disconnect_all()
