"""
Anthropic Claude connector implementation.

This handles Anthropic's Claude models including Claude 3 Opus, Sonnet, and Haiku.
"""

import json
from typing import Dict, Any, List, Optional, AsyncIterator

from anthropic import AsyncAnthropic

from ..core.base_connector import BaseConnector, Message, Response


class AnthropicConnector(BaseConnector):
    """
    Connector for Anthropic's Claude API.
    
    Supports Claude 3 Opus, Claude 3.5 Sonnet, Claude 3 Haiku, and other Claude models.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """Initialize Anthropic connector."""
        super().__init__(api_key, model, **kwargs)
        
        # Initialize client
        self.client = AsyncAnthropic(api_key=self.api_key)
        
        # Claude requires max_tokens to be set
        self.default_max_tokens = kwargs.get("max_tokens", 4096)
    
    def get_default_model(self) -> str:
        """Get default model for Anthropic."""
        return "claude-3-5-sonnet-20241022"
    
    async def send_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> Response:
        """Send messages to Claude and get response."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        
        # Extract system message if present
        system_message = None
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                # Convert to Anthropic format
                anthropic_msg = {
                    "role": msg.role,
                    "content": msg.content
                }
                
                # Handle tool responses (Claude uses "user" role for tool results)
                if msg.role == "tool" and msg.tool_call_id:
                    anthropic_msg = {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.tool_call_id,
                                "content": msg.content
                            }
                        ]
                    }
                
                anthropic_messages.append(anthropic_msg)
        
        # Prepare API parameters
        api_params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 1.0),
        }
        
        # Add system message if present
        if system_message:
            api_params["system"] = system_message
        
        # Add tools if provided
        if kwargs.get("tools"):
            api_params["tools"] = self._convert_tools_to_anthropic_format(kwargs["tools"])
            api_params["tool_choice"] = kwargs.get("tool_choice", {"type": "auto"})
        
        # Make API call
        response = await self.client.messages.create(**api_params)
        
        # Extract content and tool calls
        content = ""
        tool_calls = []
        
        # Process content blocks
        for content_block in response.content:
            if content_block.type == "text":
                content += content_block.text
            elif content_block.type == "tool_use":
                tool_calls.append({
                    "id": content_block.id,
                    "name": content_block.name,
                    "arguments": content_block.input
                })
        
        # Create unified response
        return Response(
            content=content,
            tool_calls=tool_calls,
            finish_reason=response.stop_reason,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            },
            raw_response=response
        )
    
    async def stream_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response tokens as they arrive."""
        # Convert messages to Anthropic format
        anthropic_messages = []
        system_message = None
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                anthropic_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Prepare API parameters
        api_params = {
            "model": self.model,
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.default_max_tokens),
            "temperature": kwargs.get("temperature", 0.7),
            "stream": True
        }
        
        if system_message:
            api_params["system"] = system_message
        
        # Stream the response
        async with self.client.messages.stream(**api_params) as stream:
            async for text in stream.text_stream:
                yield text
    
    def count_tokens(self, text: str) -> int:
        """Count tokens for Claude models."""
        # Anthropic doesn't provide a token counter in the SDK
        # Use approximation: ~4 characters per token
        return len(text) // 4
    
    def supports_tools(self) -> bool:
        """Claude supports tool/function calling."""
        return True
    
    def format_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Format tool calls for Claude API."""
        # Claude expects tool calls in the response content
        formatted = []
        for tool in tool_calls:
            formatted.append({
                "type": "tool_use",
                "id": tool.get("id", f"tool_{len(formatted)}"),
                "name": tool["name"],
                "input": tool.get("arguments", {})
            })
        return formatted
    
    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool calls from Claude response."""
        tool_calls = []
        
        if hasattr(response, "content"):
            for content_block in response.content:
                if hasattr(content_block, "type") and content_block.type == "tool_use":
                    tool_calls.append({
                        "id": content_block.id,
                        "name": content_block.name,
                        "arguments": content_block.input
                    })
        
        return tool_calls
    
    def _convert_tools_to_anthropic_format(self, tools: List[Dict]) -> List[Dict]:
        """Convert OpenAI-style tools to Anthropic format."""
        anthropic_tools = []
        
        for tool in tools:
            if tool.get("type") == "function":
                func = tool["function"]
                anthropic_tool = {
                    "name": func["name"],
                    "description": func.get("description", ""),
                    "input_schema": func.get("parameters", {})
                }
                anthropic_tools.append(anthropic_tool)
        
        return anthropic_tools
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by Anthropic."""
        supported_models = [
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20240620",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
        return model in supported_models
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on Anthropic pricing."""
        # Anthropic pricing (as of 2024, in dollars per 1M tokens)
        pricing = {
            "claude-3-opus": {"input": 15.0, "output": 75.0},  # per 1M tokens
            "claude-3-5-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-sonnet": {"input": 3.0, "output": 15.0},
            "claude-3-haiku": {"input": 0.25, "output": 1.25},
            "claude-2.1": {"input": 8.0, "output": 24.0},
            "claude-2.0": {"input": 8.0, "output": 24.0},
            "claude-instant": {"input": 0.8, "output": 2.4}
        }
        
        # Determine model family
        model_family = "claude-3-5-sonnet"  # default
        for family in pricing.keys():
            if family in self.model:
                model_family = family
                break
        
        model_pricing = pricing.get(model_family, pricing["claude-3-5-sonnet"])
        
        # Calculate cost (convert from per 1M to per 1K)
        input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
        output_cost = (output_tokens / 1_000_000) * model_pricing["output"]
        
        return input_cost + output_cost