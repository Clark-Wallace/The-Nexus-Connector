"""
The main Nexus Connector class.

This establishes and manages Nexus Connections with all AI providers.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

from .base_connector import BaseConnector, AIProvider, Message, Response
from .task_result import TaskResult
from .tool_executor import ToolExecutor
from ..utils.logger import get_logger


class UnifiedAIWrapper:
    """
    The Nexus Connector - Universal AI connection interface.
    
    Establishes and manages Nexus Connections with any AI provider,
    providing a unified interface for seamless AI interactions.
    """
    
    def __init__(
        self,
        provider: Union[AIProvider, str],
        api_key: str,
        model: Optional[str] = None,
        workspace: Optional[Union[str, Path]] = None,
        max_iterations: int = 10,
        auto_execute: bool = True,
        safe_mode: bool = True,
        verbose: bool = False,
        **kwargs
    ):
        """
        Initialize the unified wrapper.
        
        Args:
            provider: AI provider to use (AIProvider enum or string)
            api_key: API key for the provider
            model: Model to use (provider default if None)
            workspace: Working directory for file operations
            max_iterations: Maximum iterations for task execution
            auto_execute: Whether to automatically execute tool calls
            safe_mode: Whether to confirm destructive operations
            verbose: Whether to print detailed logs
            **kwargs: Additional provider-specific parameters
        """
        # Convert string to enum if needed
        if isinstance(provider, str):
            provider = AIProvider(provider.lower())
        
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.max_iterations = max_iterations
        self.auto_execute = auto_execute
        self.verbose = verbose
        
        # Set up workspace
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.workspace.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.logger = get_logger(__name__, verbose=verbose)
        self.connector = self._create_connector(provider, api_key, model, **kwargs)
        self.tool_executor = ToolExecutor(workspace=self.workspace, safe_mode=safe_mode)
        
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
        # Create user message
        user_message = Message(role="user", content=message)
        
        if add_to_history:
            self.conversation_history.append(user_message)
        
        # Prepare messages for API
        messages = self.conversation_history if add_to_history else [user_message]
        
        # Add tools to kwargs if not provided and auto_execute is enabled
        if self.auto_execute and "tools" not in kwargs and self.connector.supports_tools():
            kwargs["tools"] = self._get_tool_definitions()
        
        # Get response from AI
        response = await self.connector.send_message(messages, **kwargs)
        
        # Add assistant response to history
        if add_to_history and response.content:
            assistant_message = Message(
                role="assistant",
                content=response.content,
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
        
        return {
            "content": response.content,
            "tool_calls": response.tool_calls,
            "tool_results": tool_results,
            "usage": response.usage,
            "raw_response": response.raw_response
        }
    
    async def execute_task(
        self,
        task: str,
        show_progress: bool = True,
        **kwargs
    ) -> TaskResult:
        """
        Execute a complex task using the iterative pattern.
        
        This is the key method that implements the successful GPT-4o pattern:
        - Iterative execution with continuation prompts
        - Automatic tool execution and result feeding
        - Completion detection
        - Error recovery
        
        Args:
            task: Task description
            show_progress: Whether to show progress messages
            **kwargs: Additional parameters
            
        Returns:
            TaskResult with execution details
        """
        start_time = time.time()
        result = TaskResult(
            provider=self.provider.value,
            model=self.connector.model,
            session_id=self.session_id
        )
        
        # Clear tool executor history for new task
        self.tool_executor.clear_history()
        
        try:
            if show_progress:
                self.logger.info(f"Starting task execution: {task[:100]}...")
            
            # Main execution loop (the GPT-4o pattern)
            for iteration in range(self.max_iterations):
                result.iterations = iteration + 1
                
                # Prepare message
                if iteration == 0:
                    # Initial task
                    message = task
                else:
                    # Continuation prompt
                    message = "Continue with the task. What's the next step? If the task is complete, please say 'task complete'."
                
                if show_progress and iteration > 0:
                    self.logger.info(f"Iteration {iteration + 1}/{self.max_iterations}")
                
                # Send message
                response = await self.send_message(message)
                
                # Accumulate content
                if response["content"]:
                    if result.content:
                        result.content += f"\n\n--- Iteration {iteration + 1} ---\n\n"
                    result.content += response["content"]
                
                # Update token usage
                if response.get("usage"):
                    result.tokens_used += response["usage"].get("total_tokens", 0)
                
                # Check for task completion
                if response["content"] and self._is_task_complete(response["content"]):
                    if show_progress:
                        self.logger.info("Task completed successfully!")
                    result.success = True
                    break
                
                # Check if we're stuck (no tools called and asking questions)
                if not response["tool_calls"] and response["content"] and "?" in response["content"]:
                    if show_progress:
                        self.logger.warning("AI seems stuck, providing guidance...")
                    
                    # Provide guidance
                    guide_response = await self.send_message(
                        "Please proceed with the task using the available tools. "
                        "If you need to create files, use the create_file tool. "
                        "If you need to execute commands, use the execute_command tool."
                    )
                    
                    if guide_response["content"]:
                        result.content += f"\n\n[Guidance provided]\n{guide_response['content']}"
            
            # Collect execution results
            result.files_created = self.tool_executor.get_created_files()
            result.files_modified = self.tool_executor.get_modified_files()
            
            # If we exhausted iterations without completion
            if not result.success and result.iterations >= self.max_iterations:
                result.error = "Max iterations reached without task completion"
                if show_progress:
                    self.logger.warning(result.error)
            
        except Exception as e:
            result.success = False
            result.error = str(e)
            self.logger.error(f"Task execution failed: {e}")
        
        finally:
            # Calculate final metrics
            result.duration = time.time() - start_time
            result.cost = self.connector.get_cost_estimate(
                result.tokens_used,
                0  # We don't track input/output separately yet
            )
            
            if show_progress:
                self.logger.info(
                    f"Task finished in {result.duration:.2f}s "
                    f"({result.iterations} iterations, {result.tokens_used} tokens)"
                )
        
        return result
    
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
                except:
                    tool_args = {"raw_args": tool_args}
            
            # Execute tool
            self.logger.debug(f"Executing tool: {tool_name} with args: {tool_args}")
            result = await self.tool_executor.execute(tool_name, tool_args)
            
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
        """Get tool definitions in OpenAI format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "create_file",
                    "description": "Create a new file with specified content",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to create"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write to the file"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "write_file",
                    "description": "Write content to a file (overwrites existing)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file"
                            },
                            "content": {
                                "type": "string",
                                "description": "Content to write"
                            }
                        },
                        "required": ["path", "content"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read content from a file",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "path": {
                                "type": "string",
                                "description": "Path to the file to read"
                            }
                        },
                        "required": ["path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory path (default: current directory)"
                            },
                            "pattern": {
                                "type": "string",
                                "description": "File pattern to match (default: *)"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "execute_command",
                    "description": "Execute a shell command",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Command to execute"
                            }
                        },
                        "required": ["command"]
                    }
                }
            }
        ]
    
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