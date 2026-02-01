"""
Google Gemini connector implementation.

This handles Google's Gemini models including Gemini Pro and Gemini Pro Vision.
"""

import json
from typing import Dict, Any, List, Optional, AsyncIterator

import google.generativeai as genai

from ..core.base_connector import BaseConnector, Message, Response
from ..utils.tokens import count_tokens as tiktoken_count


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

        # Chat session for conversation history (lazily initialized)
        self._chat = None
        self._chat_message_count = 0

    def get_default_model(self) -> str:
        """Get default model for Google."""
        return "gemini-2.0-flash"

    def _ensure_chat_session(self, messages: List[Message]) -> None:
        """
        Ensure chat session exists and is properly synchronized with messages.

        The Gemini SDK maintains its own internal history, so we need to
        reset the session when the message history changes unexpectedly.
        """
        # Reset chat if:
        # 1. No chat exists yet
        # 2. Message count decreased (history was cleared)
        # 3. First message in a new conversation
        should_reset = (
            self._chat is None or
            len(messages) < self._chat_message_count or
            len(messages) == 1
        )

        if should_reset:
            # Convert existing messages (except the last user message) to Gemini history format
            history = []
            for msg in messages[:-1]:  # Exclude the last message (will be sent separately)
                if msg.role == "user":
                    history.append({"role": "user", "parts": [msg.content]})
                elif msg.role == "assistant":
                    history.append({"role": "model", "parts": [msg.content]})
                # Skip system and tool messages as Gemini handles them differently

            self._chat = self.client.start_chat(history=history)

        self._chat_message_count = len(messages)

    def _get_last_user_message(self, messages: List[Message]) -> str:
        """Extract the last user message from the conversation."""
        for msg in reversed(messages):
            if msg.role == "user":
                return msg.content
        raise ValueError("No user message found in conversation")

    async def send_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> Response:
        """Send messages to Gemini and get response."""
        # Ensure chat session is properly initialized
        self._ensure_chat_session(messages)

        # Get the last user message
        last_user_message = self._get_last_user_message(messages)

        # Configure generation parameters
        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 1.0),
            top_k=kwargs.get("top_k", 40),
        )

        # Send message and get response (properly awaited)
        response = await self._chat.send_message_async(
            last_user_message,
            generation_config=generation_config
        )

        # Extract content safely
        content = ""
        if hasattr(response, 'text'):
            content = response.text
        elif hasattr(response, 'parts') and response.parts:
            content = "".join(part.text for part in response.parts if hasattr(part, 'text'))
        else:
            content = str(response)

        # Gemini 2.0 supports function calling - extract if present
        tool_calls = self.extract_tool_calls(response)

        # Get token usage
        usage = {
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0
        }

        if hasattr(response, 'usage_metadata') and response.usage_metadata:
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
        # Ensure chat session is properly initialized
        self._ensure_chat_session(messages)

        # Get the last user message
        last_user_message = self._get_last_user_message(messages)

        # Configure generation
        generation_config = genai.types.GenerationConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", 4096),
        )

        # Stream the response (properly awaited)
        response_stream = await self._chat.send_message_async(
            last_user_message,
            generation_config=generation_config,
            stream=True
        )

        # Iterate over the async stream
        async for chunk in response_stream:
            if hasattr(chunk, 'text') and chunk.text:
                yield chunk.text
            elif hasattr(chunk, 'parts'):
                for part in chunk.parts:
                    if hasattr(part, 'text') and part.text:
                        yield part.text
    
    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Gemini's native token counter.

        Falls back to tiktoken approximation if native counting fails.
        """
        try:
            # Use Gemini's built-in token counting (most accurate)
            return self.client.count_tokens(text).total_tokens
        except Exception:
            # Fallback to tiktoken-based estimation
            return tiktoken_count(text, self.model)
    
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