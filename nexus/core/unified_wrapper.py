"""
The main Nexus Connector class.

This establishes and manages Nexus Connections with all AI providers.
"""

import asyncio
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union, Callable, Tuple
from datetime import datetime

from .base_connector import BaseConnector, AIProvider, Message, Response
from .task_result import TaskResult
from .tool_executor import ToolExecutor
from .tool_registry import ToolRegistry, tool, ToolMetadata
from .mcp_client import MCPManager, MCPServerConfig
from .router import Router, RoutingStrategy, ProviderConfig, create_router_from_env
from ..utils.logger import get_logger


class UnifiedAIWrapper:
    """
    The Nexus Connector - Universal AI connection interface.
    
    Establishes and manages Nexus Connections with any AI provider,
    providing a unified interface for seamless AI interactions.
    """
    
    def __init__(
        self,
        provider: Union[AIProvider, str, None] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        workspace: Optional[Union[str, Path]] = None,
        max_iterations: int = 10,
        auto_execute: bool = True,
        safe_mode: bool = True,
        verbose: bool = False,
        tools: Optional[List[Callable]] = None,
        mcp_servers: Optional[List[str]] = None,
        # Smart routing
        router: Optional[Union[Router, str]] = None,
        routing_rules: Optional[Dict[str, str]] = None,
        fallback_enabled: bool = True,
        max_fallback_attempts: int = 3,
        # Execution hooks
        on_message: Optional[Callable[[Message], None]] = None,
        on_tool_call: Optional[Callable[[Dict], None]] = None,
        on_tool_result: Optional[Callable[[Dict], None]] = None,
        on_step: Optional[Callable[[int, str], None]] = None,
        on_error: Optional[Callable[[Exception], None]] = None,
        on_provider_switch: Optional[Callable[[AIProvider, AIProvider, str], None]] = None,
        **kwargs
    ):
        """
        Initialize the unified wrapper.

        Args:
            provider: AI provider to use (AIProvider enum or string).
                      Can be None if using router="auto".
            api_key: API key for the provider.
                     Can be None if using router="auto".
            model: Model to use (provider default if None)
            workspace: Working directory for file operations
            max_iterations: Maximum iterations for task execution
            auto_execute: Whether to automatically execute tool calls
            safe_mode: Whether to confirm destructive operations
            verbose: Whether to print detailed logs
            tools: Optional list of custom tool functions decorated with @tool
            mcp_servers: Optional list of MCP server names to connect to
                        (e.g., ["filesystem", "github", "memory"])
            router: Smart routing configuration. Can be:
                    - None: Use single provider (default behavior)
                    - "auto": Create router from environment variables
                    - "cost", "quality", "latency", "fallback": Use strategy
                    - Router instance: Use custom router
            routing_rules: Task type → provider mapping for smart routing
                          e.g., {"code": "anthropic", "math": "openai"}
            fallback_enabled: Whether to try other providers on failure
            max_fallback_attempts: Maximum providers to try in fallback
            on_message: Callback for each message sent/received
            on_tool_call: Callback before tool execution
            on_tool_result: Callback after tool execution
            on_step: Callback for each iteration step
            on_error: Callback when errors occur
            on_provider_switch: Callback when switching providers during fallback
                               (old_provider, new_provider, reason)
            **kwargs: Additional provider-specific parameters
        """
        # Initialize logging first
        self.logger = get_logger(__name__, verbose=verbose)

        # Smart routing setup
        self._router: Optional[Router] = None
        self._fallback_enabled = fallback_enabled
        self._max_fallback_attempts = max_fallback_attempts
        self._on_provider_switch = on_provider_switch
        self._connectors: Dict[AIProvider, BaseConnector] = {}
        self._extra_kwargs = kwargs

        if router is not None:
            self._router = self._setup_router(router, routing_rules)
            # Select initial provider from router
            if provider is None:
                provider = self._router.select_provider()
                if provider is None:
                    raise ValueError(
                        "No providers available. Set API keys in environment or "
                        "provide provider/api_key explicitly."
                    )
                api_key = self._router._providers[provider].api_key
                model = model or self._router._providers[provider].model
                self.logger.info(f"Router selected initial provider: {provider.value}")

        # Validate we have a provider
        if provider is None:
            raise ValueError("provider is required (or use router='auto')")

        # Auto-resolve API key from environment if not provided
        if api_key is None and not (router and isinstance(router, Router)):
            _provider_str = provider.value if isinstance(provider, AIProvider) else provider.lower()
            _key_map = {
                "openai": "OPENAI_API_KEY",
                "anthropic": "ANTHROPIC_API_KEY",
                "google": "GOOGLE_API_KEY",
                "deepseek": "DEEPSEEK_API_KEY",
                "xai": "XAI_API_KEY",
            }
            if _provider_str in _key_map:
                api_key = os.getenv(_key_map[_provider_str])
            if api_key is None:
                raise ValueError("api_key is required (or use router='auto')")

        # Convert string to enum if needed
        if isinstance(provider, str):
            provider = AIProvider(provider.lower())

        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.max_iterations = max_iterations
        self.auto_execute = auto_execute
        self.verbose = verbose
        self.safe_mode = safe_mode

        # Set up workspace
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Initialize connector
        self.connector = self._create_connector(provider, api_key, model, **kwargs)
        self._connectors[provider] = self.connector

        # Initialize tool registry and executor
        self._tool_registry = ToolRegistry()
        self.tool_executor = ToolExecutor(
            workspace=self.workspace,
            safe_mode=safe_mode,
            registry=self._tool_registry
        )

        # Register custom tools if provided
        if tools:
            self.register_tools(tools)

        # Initialize MCP manager (tools will be registered to the same registry)
        self._mcp_manager = MCPManager(registry=self._tool_registry)
        self._mcp_servers_pending = mcp_servers or []
        self._mcp_initialized = False

        # Execution hooks for observability
        self._on_message = on_message
        self._on_tool_call = on_tool_call
        self._on_tool_result = on_tool_result
        self._on_step = on_step
        self._on_error = on_error

        # Session management
        self.session_id = f"nexus_{provider.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation_history: List[Message] = []

        self.logger.info(f"Initialized UnifiedAIWrapper with {provider.display_name} ({self.model})")
    
    def _create_connector(
        self,
        provider: AIProvider,
        api_key: str,
        model: Optional[str],
        **kwargs
    ) -> BaseConnector:
        """Create the appropriate connector for the provider."""
        # Import connectors dynamically to avoid circular imports
        if provider == AIProvider.OPENAI:
            from ..connectors.openai_connector import OpenAIConnector
            return OpenAIConnector(api_key, model, **kwargs)
        
        elif provider == AIProvider.ANTHROPIC:
            from ..connectors.anthropic_connector import AnthropicConnector
            return AnthropicConnector(api_key, model, **kwargs)
        
        elif provider == AIProvider.GOOGLE:
            from ..connectors.google_connector import GoogleConnector
            return GoogleConnector(api_key, model, **kwargs)
        
        elif provider == AIProvider.XAI:
            from ..connectors.xai_connector import XAIConnector
            return XAIConnector(api_key, model, **kwargs)
        
        elif provider == AIProvider.DEEPSEEK:
            from ..connectors.deepseek_connector import DeepSeekConnector
            return DeepSeekConnector(api_key, model, **kwargs)
        
        elif provider == AIProvider.OLLAMA:
            from ..connectors.ollama_connector import OllamaConnector
            return OllamaConnector(api_key, model, **kwargs)

        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _setup_router(
        self,
        router: Union[Router, str],
        routing_rules: Optional[Dict[str, str]] = None
    ) -> Router:
        """Set up the smart router."""
        if isinstance(router, Router):
            return router

        # String-based router configuration
        if router == "auto":
            # Create from environment variables
            return create_router_from_env(
                strategy=RoutingStrategy.FALLBACK,
                routing_rules=routing_rules
            )

        # Strategy string
        try:
            strategy = RoutingStrategy(router)
            return create_router_from_env(
                strategy=strategy,
                routing_rules=routing_rules
            )
        except ValueError:
            raise ValueError(
                f"Invalid router value: {router}. "
                f"Use 'auto', a strategy name ({[s.value for s in RoutingStrategy]}), "
                "or a Router instance."
            )

    def _get_or_create_connector(self, provider: AIProvider) -> BaseConnector:
        """Get existing connector or create a new one for the provider."""
        if provider in self._connectors:
            return self._connectors[provider]

        if self._router is None or provider not in self._router._providers:
            raise ValueError(f"Provider {provider.value} not configured")

        config = self._router._providers[provider]
        connector = self._create_connector(
            provider,
            config.api_key,
            config.model,
            **self._extra_kwargs
        )
        self._connectors[provider] = connector
        return connector

    def _switch_provider(self, new_provider: AIProvider, reason: str) -> None:
        """Switch to a different provider."""
        old_provider = self.provider
        self.provider = new_provider
        self.connector = self._get_or_create_connector(new_provider)

        self.logger.info(f"Switched provider: {old_provider.value} → {new_provider.value} ({reason})")

        if self._on_provider_switch:
            try:
                self._on_provider_switch(old_provider, new_provider, reason)
            except Exception as e:
                self.logger.warning(f"on_provider_switch hook error: {e}")
    
    async def send_message(
        self,
        message: str,
        add_to_history: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send a single message and get response.

        Args:
            message: Message to send
            add_to_history: Whether to add to conversation history
            **kwargs: Additional parameters for the AI

        Returns:
            Response dictionary with content, tool_calls, etc.
        """
        # Auto-initialize MCP servers on first message
        if not self._mcp_initialized and self._mcp_servers_pending:
            await self.init_mcp_servers()

        # Create user message
        user_message = Message(role="user", content=message)

        if add_to_history:
            self.conversation_history.append(user_message)

        # Prepare messages for API
        messages = self.conversation_history if add_to_history else [user_message]

        # Add tools to kwargs if not provided and auto_execute is enabled
        if self.auto_execute and "tools" not in kwargs and self.connector.supports_tools():
            kwargs["tools"] = self._get_tool_definitions()

        # Use router if available for provider selection
        if self._router:
            # Select best provider for this message
            selected = self._router.select_provider(message)
            if selected and selected != self.provider:
                self._switch_provider(selected, "router selection")

        # Send with fallback support
        response, provider_used = await self._send_with_fallback(messages, message, **kwargs)

        # Add assistant response to history
        # Must add if there's content OR tool_calls (tool results need preceding assistant message)
        if add_to_history and (response.content or response.tool_calls):
            assistant_message = Message(
                role="assistant",
                content=response.content or "",
                tool_calls=response.tool_calls
            )
            self.conversation_history.append(assistant_message)

        # Execute tool calls if auto_execute is enabled
        tool_results = []
        if self.auto_execute and response.tool_calls:
            tool_results = await self._execute_tool_calls(response.tool_calls)

            # Add tool results to history
            if add_to_history:
                for result in tool_results:
                    tool_message = Message(
                        role="tool",
                        content=str(result["result"]),
                        tool_call_id=result["tool_call_id"]
                    )
                    self.conversation_history.append(tool_message)

            # Send tool results back to the AI for a final text response
            if add_to_history and tool_results:
                messages = self.conversation_history
                follow_up, _ = await self._send_with_fallback(messages, message, **kwargs)
                if follow_up.content:
                    response = follow_up
                    # Add the follow-up response to history
                    self.conversation_history.append(
                        Message(role="assistant", content=follow_up.content,
                                tool_calls=follow_up.tool_calls)
                    )

        return {
            "content": response.content,
            "tool_calls": response.tool_calls,
            "tool_results": tool_results,
            "usage": response.usage,
            "raw_response": response.raw_response,
            "provider": provider_used.value if provider_used else self.provider.value,
        }

    async def _send_with_fallback(
        self,
        messages: List[Message],
        original_message: str,
        **kwargs
    ) -> Tuple[Response, Optional[AIProvider]]:
        """
        Send message with automatic fallback on failure.

        Returns:
            Tuple of (response, provider_used)
        """
        import time as time_module

        # Get fallback order
        if self._router and self._fallback_enabled:
            providers_to_try = self._router.get_fallback_order(
                original_message,
                max_providers=self._max_fallback_attempts
            )
        else:
            providers_to_try = [self.provider]

        last_error: Optional[Exception] = None
        excluded: List[AIProvider] = []

        for provider in providers_to_try:
            # Switch to this provider if needed
            if provider != self.provider:
                reason = f"fallback from {self.provider.value}" if last_error else "router selection"
                self._switch_provider(provider, reason)

            start_time = time_module.time()
            try:
                response = await self.connector.send_message(messages, **kwargs)

                # Record success with router
                if self._router:
                    latency_ms = (time_module.time() - start_time) * 1000
                    tokens = response.usage.get("total_tokens", 0) if response.usage else 0
                    self._router.record_success(provider, latency_ms, tokens, 0.0)

                return response, provider

            except Exception as e:
                last_error = e
                self.logger.warning(f"Provider {provider.value} failed: {e}")

                # Record failure with router
                if self._router:
                    self._router.record_failure(provider, str(e))

                # Fire on_error hook
                if self._on_error:
                    try:
                        self._on_error(e)
                    except Exception:
                        pass

                excluded.append(provider)
                continue

        # All providers failed
        raise last_error or Exception("All providers failed")
    
    async def execute_task(
        self,
        task: str,
        show_progress: bool = True,
        confirm_destructive: bool = False,
        confirm_all: bool = False,
        checkpoint: bool = False,
        rollback_on_fail: bool = False,
        log_path: Optional[str] = None,
        **kwargs
    ) -> TaskResult:
        """
        Execute a complex task using the iterative pattern.

        This is the key method that implements the successful GPT-4o pattern:
        - Iterative execution with continuation prompts
        - Automatic tool execution and result feeding
        - Completion detection
        - Error recovery
        - Human-in-the-loop confirmation for destructive operations

        Args:
            task: Task description
            show_progress: Whether to show progress messages
            confirm_destructive: Pause before destructive operations (delete, rm, etc.)
            confirm_all: Pause before every tool call
            checkpoint: Create a git checkpoint before making changes
            rollback_on_fail: Rollback to checkpoint if task fails
            log_path: Path to save execution log
            **kwargs: Additional parameters

        Returns:
            TaskResult with execution details
        """
        from .execution_log import ExecutionLog

        start_time = time.time()
        result = TaskResult(
            provider=self.provider.value,
            model=self.connector.model,
            session_id=self.session_id
        )

        # Initialize execution log
        exec_log = ExecutionLog(
            task=task,
            session_id=self.session_id,
            provider=self.provider.value,
            model=self.connector.model,
        )

        # Store confirmation settings for use in tool execution
        self._confirm_destructive = confirm_destructive
        self._confirm_all = confirm_all
        self._confirm_callback = kwargs.get("confirm_callback")

        # Clear tool executor history for new task
        self.tool_executor.clear_history()

        # Create checkpoint if requested
        checkpoint_id = None
        if checkpoint:
            checkpoint_id = await self._create_checkpoint()
            if checkpoint_id:
                exec_log.log_checkpoint(checkpoint_id, "Pre-task checkpoint")

        try:
            if show_progress:
                self.logger.info(f"Starting task execution: {task[:100]}...")

            # Main execution loop (the GPT-4o pattern)
            for iteration in range(self.max_iterations):
                result.iterations = iteration + 1
                step_start = time.time()

                # Fire on_step hook
                if self._on_step:
                    try:
                        self._on_step(iteration + 1, "starting")
                    except Exception as e:
                        self.logger.warning(f"on_step hook error: {e}")

                exec_log.log_step_start(iteration + 1)

                # Prepare message
                if iteration == 0:
                    message = task
                else:
                    message = "Continue with the task."

                if show_progress and iteration > 0:
                    self.logger.info(f"Iteration {iteration + 1}/{self.max_iterations}")

                # Log and send message
                exec_log.log_message_sent(message)
                response = await self.send_message(message)

                # Log response
                exec_log.log_message_received(
                    response.get("content", ""),
                    tokens=response.get("usage", {}).get("total_tokens"),
                )

                # Accumulate content
                if response["content"]:
                    if result.content:
                        result.content += f"\n\n--- Iteration {iteration + 1} ---\n\n"
                    result.content += response["content"]

                # Update token usage
                if response.get("usage"):
                    result.tokens_used += response["usage"].get("total_tokens", 0)

                # Check for task completion:
                # If the AI responded with text and made no tool calls, the task is done.
                # The model decides when it's finished — no magic phrases needed.
                if response["content"] and not response["tool_calls"]:
                    if show_progress:
                        self.logger.info("Task completed successfully!")
                    result.success = True
                    exec_log.log_step_end(
                        iteration + 1,
                        success=True,
                        duration_ms=(time.time() - step_start) * 1000
                    )
                    break

                exec_log.log_step_end(
                    iteration + 1,
                    success=True,
                    duration_ms=(time.time() - step_start) * 1000
                )

            # Collect execution results
            result.files_created = self.tool_executor.get_created_files()
            result.files_modified = self.tool_executor.get_modified_files()

            # If we exhausted iterations without completion
            if not result.success and result.iterations >= self.max_iterations:
                result.error = "Max iterations reached without task completion"
                exec_log.log_warning(result.error)
                if show_progress:
                    self.logger.warning(result.error)

        except Exception as e:
            result.success = False
            result.error = str(e)
            exec_log.log_error(str(e))
            self.logger.error(f"Task execution failed: {e}")

            # Fire on_error hook
            if self._on_error:
                try:
                    self._on_error(e)
                except Exception:
                    pass

            # Rollback if requested
            if rollback_on_fail and checkpoint_id:
                await self._rollback_to_checkpoint(checkpoint_id)
                exec_log.log_rollback(checkpoint_id, f"Task failed: {e}")

        finally:
            # Calculate final metrics
            result.duration = time.time() - start_time
            result.cost = self.connector.get_cost_estimate(
                result.tokens_used,
                0  # We don't track input/output separately yet
            )

            # Finalize execution log
            exec_log.finish(result.success)

            # Save log if path provided
            if log_path:
                exec_log.save(log_path)

            # Attach log to result
            result.execution_log = exec_log

            if show_progress:
                self.logger.info(
                    f"Task finished in {result.duration:.2f}s "
                    f"({result.iterations} iterations, {result.tokens_used} tokens)"
                )

        return result

    async def _create_checkpoint(self) -> Optional[str]:
        """Create a git checkpoint before making changes."""
        try:
            result = await self.tool_executor.execute(
                "execute_command",
                {"command": "git rev-parse HEAD 2>/dev/null"}
            )
            if result.get("success"):
                return result.get("stdout", "").strip()
        except Exception as e:
            self.logger.warning(f"Could not create checkpoint: {e}")
        return None

    async def _rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """Rollback to a git checkpoint."""
        try:
            result = await self.tool_executor.execute(
                "execute_command",
                {"command": f"git checkout {checkpoint_id} -- ."}
            )
            return result.get("success", False)
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False
    
    async def _execute_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Execute tool calls and return results."""
        results = []

        for tool_call in tool_calls:
            tool_name = tool_call.get("name", tool_call.get("function", {}).get("name"))
            tool_args = tool_call.get("arguments", tool_call.get("function", {}).get("arguments", {}))
            tool_id = tool_call.get("id", f"tool_{len(results)}")

            # Parse arguments if they're JSON string
            if isinstance(tool_args, str):
                import json
                try:
                    tool_args = json.loads(tool_args)
                except Exception:
                    tool_args = {"raw_args": tool_args}

            # Fire on_tool_call hook
            if self._on_tool_call:
                try:
                    self._on_tool_call({"name": tool_name, "arguments": tool_args, "id": tool_id})
                except Exception as e:
                    self.logger.warning(f"on_tool_call hook error: {e}")

            # Execute tool
            self.logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
            try:
                result = await self.tool_executor.execute(tool_name, tool_args)
            except Exception as e:
                if self._on_error:
                    self._on_error(e)
                result = {"success": False, "error": str(e)}

            # Fire on_tool_result hook
            if self._on_tool_result:
                try:
                    self._on_tool_result({"name": tool_name, "result": result, "id": tool_id})
                except Exception as e:
                    self.logger.warning(f"on_tool_result hook error: {e}")

            results.append({
                "tool_call_id": tool_id,
                "tool_name": tool_name,
                "result": result
            })

        return results
    
    def _is_task_complete(self, content: str) -> bool:
        """Check if the task is complete based on AI response."""
        completion_phrases = [
            "task complete",
            "task is complete",
            "completed successfully",
            "all done",
            "finished successfully",
            "task has been completed",
            "successfully completed the task"
        ]
        
        content_lower = content.lower()
        return any(phrase in content_lower for phrase in completion_phrases)
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history.clear()
        self.logger.debug("Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get conversation history."""
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls
            }
            for msg in self.conversation_history
        ]
    
    def _get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get tool definitions in OpenAI format from the registry."""
        return self.tool_executor.get_tool_definitions(format="openai")

    # ========== Tool registration methods ==========

    def register_tool(self, func: Callable = None, **kwargs) -> Callable:
        """
        Register a custom tool.

        Can be used as a decorator:
            @connector.register_tool(description="My tool")
            def my_tool(x: int) -> str:
                ...

        Or directly:
            connector.register_tool(some_func, description="Some tool")

        Args:
            func: Function to register
            **kwargs: Tool metadata (description, category, timeout, etc.)

        Returns:
            The registered function
        """
        return self.tool_executor.register_tool(func, **kwargs)

    def register_tools(self, tools: List[Callable]) -> None:
        """
        Register multiple custom tools at once.

        Args:
            tools: List of tool functions (should be decorated with @tool)

        Example:
            @tool(description="Search docs")
            async def search(query: str) -> str:
                ...

            @tool(description="Send email")
            async def email(to: str, subject: str, body: str) -> str:
                ...

            connector.register_tools([search, email])
        """
        self.tool_executor.register_tools(tools)

    def get_tools(self) -> List[ToolMetadata]:
        """Get all registered tools."""
        return self._tool_registry.get_all()

    def get_tool_names(self) -> List[str]:
        """Get names of all registered tools."""
        return [t.name for t in self._tool_registry.get_all()]
    
    @property
    def model_info(self) -> Dict[str, Any]:
        """Get information about the current model."""
        return {
            "provider": self.provider.value,
            "provider_name": self.provider.display_name,
            "model": self.connector.model,
            "supports_tools": self.connector.supports_tools(),
            "session_id": self.session_id
        }

    # ========== MCP Server Management ==========

    async def init_mcp_servers(self) -> Dict[str, bool]:
        """
        Initialize MCP servers specified in constructor.

        This is called automatically on first send_message/execute_task,
        but can be called explicitly if you need to ensure servers are
        connected before starting work.

        Returns:
            Dict mapping server name to connection success
        """
        if self._mcp_initialized:
            return {}

        results = {}
        if self._mcp_servers_pending:
            self.logger.info(f"Connecting to MCP servers: {self._mcp_servers_pending}")
            results = await self._mcp_manager.connect_all(self._mcp_servers_pending)
            for server, success in results.items():
                if success:
                    self.logger.info(f"Connected to MCP server: {server}")
                else:
                    self.logger.warning(f"Failed to connect to MCP server: {server}")

        self._mcp_initialized = True
        return results

    async def add_mcp_server(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> bool:
        """
        Add and connect to an MCP server.

        Args:
            name: Server name. Can be a well-known server like "filesystem",
                  "github", "memory", etc., or a custom server name.
            config: Optional configuration dict with keys:
                    - command: Command to run the server
                    - args: Command arguments
                    - env: Environment variables
                    - timeout: Connection timeout
            **kwargs: Additional config overrides

        Returns:
            True if successfully connected

        Example:
            # Use well-known server
            await connector.add_mcp_server("filesystem")

            # Use well-known server with env override
            await connector.add_mcp_server("github", env={
                "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxx"
            })

            # Use custom server
            await connector.add_mcp_server("my-server", config={
                "command": "python",
                "args": ["-m", "my_mcp_server"],
            })
        """
        if config:
            kwargs.update(config)

        success = await self._mcp_manager.add_server(name, **kwargs)
        if success:
            self.logger.info(f"Added MCP server: {name}")
        return success

    async def remove_mcp_server(self, name: str) -> bool:
        """
        Remove and disconnect from an MCP server.

        Args:
            name: Server name

        Returns:
            True if server was found and removed
        """
        success = await self._mcp_manager.remove_server(name)
        if success:
            self.logger.info(f"Removed MCP server: {name}")
        return success

    def get_mcp_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all connected MCP servers.

        Returns:
            Dict mapping server name to status info:
            {
                "filesystem": {
                    "state": "connected",
                    "tools_count": 5,
                    "resources_count": 0
                }
            }
        """
        return self._mcp_manager.get_server_status()

    def get_mcp_tools(self) -> List[str]:
        """
        Get list of all tools from connected MCP servers.

        Returns:
            List of tool names (prefixed with "mcp_<server>_")
        """
        return [
            f"mcp_{tool.server_name}_{tool.name}"
            for tool in self._mcp_manager.get_all_tools()
        ]

    @staticmethod
    def list_known_mcp_servers() -> List[str]:
        """
        List all well-known MCP server names that can be used directly.

        Returns:
            List of server names like ["filesystem", "github", "memory", ...]
        """
        return MCPManager.list_known_servers()

    async def close(self) -> None:
        """
        Close all connections and cleanup resources.

        Should be called when done using the connector.
        """
        await self._mcp_manager.disconnect_all()
        self.logger.info("Closed all connections")