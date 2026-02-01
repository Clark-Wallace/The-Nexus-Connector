"""
Google Gemini connector implementation.

This handles Google's Gemini models including Gemini Pro and Gemini Pro Vision.
"""

import json
from typing import Dict, Any, List, Optional, AsyncIterator

import google.generativeai as genai

from ..core.base_connector import BaseConnector, Message, Response


class GoogleConnector(BaseConnector):
    """
    Connector for Google's Gemini API.
    
    Supports Gemini Pro, Gemini Pro Vision, and other Gemini models.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """Initialize Google connector."""
        super().__init__(api_key, model, **kwargs)
        
        # Configure the Google API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.client = genai.GenerativeModel(self.model)
        
        # Start a chat session for conversation history
        self.chat = None
    
    def get_default_model(self) -> str:
        """Get default model for Google."""
        return "gemini-2.0-flash"
    
    async def send_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> Response:
        """Send messages to Gemini and get response."""
        # Convert messages to Gemini format
        # Gemini uses a different approach - it maintains chat history internally
        
        # If this is a new conversation or we need to reset
        if not self.chat or len(messages) == 1:
            self.chat = self.client.start_chat(history=[])
        
        # Get the last user message (Gemini expects just the latest message)
        last_user_message = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_message = msg.content
                break
        
        if not last_user_message:
            raise ValueError("No user message found in conversation")
        
        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 1.0),
            top_k=kwargs.get("top_k", 40),
        )
        
        # Send message and get response
        response = await self.chat.send_message_async(
            last_user_message,
            generation_config=generation_config
        )
        
        # Extract content
        content = response.text if hasattr(response, 'text') else str(response)
        
        # Gemini doesn't have native function calling in the same way
        # We'll need to implement this differently if needed
        tool_calls = []
        
        # Count tokens (Gemini provides this differently)
        usage = {
            "prompt_tokens": 0,  # Would need to estimate
            "completion_tokens": 0,  # Would need to estimate
            "total_tokens": 0
        }
        
        # Try to get token counts if available
        if hasattr(response, 'usage_metadata'):
            usage = {
                "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
            }
        
        return Response(
            content=content,
            tool_calls=tool_calls,
            finish_reason="stop",
            usage=usage,
            raw_response=response
        )
    
    async def stream_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream response tokens as they arrive."""
        # Get the last user message
        last_user_message = None
        for msg in reversed(messages):
            if msg.role == "user":
                last_user_message = msg.content
                break
        
        if not last_user_message:
            raise ValueError("No user message found in conversation")
        
        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", 4096),
        )
        
        # Stream the response
        response_stream = await self.chat.send_message_async(
            last_user_message,
            generation_config=generation_config,
            stream=True
        )
        
        async for chunk in response_stream:
            if chunk.text:
                yield chunk.text
    
    def count_tokens(self, text: str) -> int:
        """Count tokens using Gemini's token counter."""
        try:
            # Use Gemini's built-in token counting
            return self.client.count_tokens(text).total_tokens
        except:
            # Fallback to estimation
            return len(text) // 4
    
    def supports_tools(self) -> bool:
        """Gemini has limited tool/function support compared to OpenAI."""
        # Gemini 2.0 models do support function calling, but it's different
        # For now, we'll say no to use text-based tool execution
        return False
    
    def format_tool_calls(self, tool_calls: List[Dict]) -> Any:
        """Format tool calls for Gemini API."""
        # Gemini uses a different format for functions
        # This would need to be implemented based on Gemini's function calling API
        return []
    
    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool calls from Gemini response."""
        # Would need to parse Gemini's function call format
        return []
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is supported by Google."""
        supported_models = [
            "gemini-pro",
            "gemini-pro-vision",
            "gemini-1.5-pro",
            "gemini-1.5-pro-latest",
            "gemini-1.5-flash",
            "gemini-1.5-flash-latest",
            "gemini-2.0-flash",
            "gemini-2.0-flash-thinking",
            "gemini-2.0-pro",
        ]
        return model in supported_models
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on Google pricing."""
        # Google Gemini pricing (as of 2024, in dollars per 1K tokens)
        pricing = {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.00025, "output": 0.001},
            "gemini-2.0-flash": {"input": 0.00015, "output": 0.0006},
            "gemini-2.0-pro": {"input": 0.002, "output": 0.008},
        }
        
        # Get pricing for model (default to flash pricing)
        model_base = self.model.split("-")[0] + "-" + self.model.split("-")[1]
        model_pricing = pricing.get(model_base, pricing["gemini-2.0-flash"])
        
        # Calculate cost
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]
        
        return input_cost + output_cost