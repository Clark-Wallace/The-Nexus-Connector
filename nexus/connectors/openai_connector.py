"""
OpenAI connector implementation.

This handles OpenAI's GPT models including GPT-4 and GPT-4o.
"""

import json
from typing import Dict, Any, List, Optional, AsyncIterator

from openai import AsyncOpenAI
import tiktoken

from ..core.base_connector import BaseConnector, Message, Response


class OpenAIConnector(BaseConnector):
    """
    Connector for OpenAI's API.
    
    Supports GPT-3.5, GPT-4, and GPT-4o models with full tool/function support.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """Initialize OpenAI connector."""
        super().__init__(api_key, model, **kwargs)
        
        # Extract OpenAI-specific parameters
        self.base_url = kwargs.get("base_url")
        self.organization = kwargs.get("organization")
        
        # Initialize client
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            organization=self.organization
        )
        
        # Initialize tokenizer
        try:
            self.encoding = tiktoken.encoding_for_model(self.model)
        except:
            self.encoding = tiktoken.get_encoding("cl100k_base")
    
    def get_default_model(self) -> str:
        """Get default model for OpenAI."""
        return "gpt-4o"
    
    async def send_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> Response:
        """Send messages to OpenAI and get response."""
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_msg = {
                "role": msg.role,
                "content": msg.content
            }
            
            # Add tool calls if present
            if msg.tool_calls and msg.role == "assistant":
                openai_msg["tool_calls"] = self.format_tool_calls(msg.tool_calls)
            
            # Add tool call ID for tool responses
            if msg.tool_call_id and msg.role == "tool":
                openai_msg["tool_call_id"] = msg.tool_call_id
                
            openai_messages.append(openai_msg)
        
        # Prepare API parameters
        api_params = {
            "model": self.model,
            "messages": openai_messages,
            "temperature": kwargs.get("temperature", 0.7),
            "max_tokens": kwargs.get("max_tokens", 4096),
            "top_p": kwargs.get("top_p", 1.0),
            "frequency_penalty": kwargs.get("frequency_penalty", 0),
            "presence_penalty": kwargs.get("presence_penalty", 0),
        }
        
        # Add tools if available
        if kwargs.get("tools"):
            api_params["tools"] = kwargs["tools"]
        
        # Make API call
        response = await self.client.chat.completions.create(**api_params)
        
        # Extract response
        choice = response.choices[0]
        message = choice.message
        
        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            tool_calls = self.extract_tool_calls(message)
        
        # Create unified response
        # Handle missing usage data (common with OpenRouter)
        usage_data = {}
        if hasattr(response, 'usage') and response.usage:
            usage_data = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        else:
            # Estimate token counts if usage data is missing
            usage_data = {
                "prompt_tokens": sum(self.count_tokens(msg.content) for msg in messages),
                "completion_tokens": self.count_tokens(message.content or ""),
                "total_tokens": 0
            }
            usage_data["total_tokens"] = usage_data["prompt_tokens"] + usage_data["completion_tokens"]
        
        return Response(
            content=message.content or "",
            tool_calls=tool_calls,
            finish_reason=choice.finish_reason,
            usage=usage_data,
            raw_response=response
        )
    
    async def stream_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response tokens as they arrive."""
        # Convert messages to OpenAI format
        openai_messages = []
        for msg in messages:
            openai_messages.append({
                "role": msg.role,
                "content": msg.content
            })
        
        # Make streaming API call
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4096),
            stream=True
        )
        
        # Stream tokens
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using tiktoken."""
        return len(self.encoding.encode(text))
    
    def supports_tools(self) -> bool:
        """OpenAI supports function/tool calling."""
        return True
    
    def format_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Format tool calls for OpenAI API."""
        formatted = []
        
        for tool in tool_calls:
            formatted_tool = {
                "id": tool.get("id", f"call_{len(formatted)}"),
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "arguments": json.dumps(tool.get("arguments", {}))
                }
            }
            formatted.append(formatted_tool)
        
        return formatted
    
    def extract_tool_calls(self, message: Any) -> List[Dict]:
        """Extract tool calls from OpenAI response."""
        tool_calls = []
        
        if hasattr(message, "tool_calls") and message.tool_calls:
            for tc in message.tool_calls:
                tool_call = {
                    "id": tc.id,
                    "name": tc.function.name,
                    "arguments": json.loads(tc.function.arguments) if tc.function.arguments else {}
                }
                tool_calls.append(tool_call)
        
        return tool_calls
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by OpenAI."""
        supported_models = [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4-turbo-preview",
            "gpt-4o",
            "gpt-4o-mini"
        ]
        return model in supported_models
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on OpenAI pricing."""
        # Pricing as of 2024 (in dollars per 1K tokens)
        pricing = {
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
        }
        
        # Get pricing for model
        model_pricing = pricing.get(self.model, pricing["gpt-4o"])
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost