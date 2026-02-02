"""
Google Gemini connector implementation.

This handles Google's Gemini models using the new google-genai SDK.
"""

from typing import Dict, Any, List, Optional, AsyncIterator

from google import genai
from google.genai import types

from ..core.base_connector import BaseConnector, Message, Response
from ..utils.tokens import count_tokens as tiktoken_count


class GoogleConnector(BaseConnector):
    """
    Connector for Google's Gemini API.

    Supports Gemini Pro, Gemini Flash, and other Gemini models.
    Uses the new google-genai SDK.
    """

    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """Initialize Google connector."""
        super().__init__(api_key, model, **kwargs)

        # Create the client
        self.client = genai.Client(api_key=self.api_key)

        # Chat session for conversation history (lazily initialized)
        self._chat = None
        self._chat_message_count = 0

    def get_default_model(self) -> str:
        """Get default model for Google."""
        return "gemini-2.0-flash"

    def _convert_messages_to_contents(self, messages: List[Message]) -> List[types.Content]:
        """Convert our Message format to Gemini Content format."""
        contents = []
        for msg in messages:
            if msg.role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=msg.content)]
                ))
            elif msg.role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part(text=msg.content)]
                ))
            elif msg.role == "system":
                # Gemini handles system prompts differently - prepend to first user message
                # or use system_instruction parameter
                pass
        return contents

    def _get_system_instruction(self, messages: List[Message]) -> Optional[str]:
        """Extract system instruction from messages."""
        for msg in messages:
            if msg.role == "system":
                return msg.content
        return None

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
        # Convert messages to Gemini format
        contents = self._convert_messages_to_contents(messages)
        system_instruction = self._get_system_instruction(messages)

        # Configure generation parameters
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", 4096),
            top_p=kwargs.get("top_p", 1.0),
            top_k=kwargs.get("top_k", 40),
        )

        if system_instruction:
            config.system_instruction = system_instruction

        # Send message using async client
        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=contents,
            config=config,
        )

        # Extract content safely
        content = ""
        if response.text:
            content = response.text
        elif response.candidates and response.candidates[0].content.parts:
            content = "".join(
                part.text for part in response.candidates[0].content.parts
                if hasattr(part, 'text') and part.text
            )

        # Extract tool calls if present
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
        # Convert messages to Gemini format
        contents = self._convert_messages_to_contents(messages)
        system_instruction = self._get_system_instruction(messages)

        # Configure generation
        config = types.GenerateContentConfig(
            temperature=kwargs.get("temperature", 0.7),
            max_output_tokens=kwargs.get("max_tokens", 4096),
        )

        if system_instruction:
            config.system_instruction = system_instruction

        # Stream the response
        async for chunk in self.client.aio.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=config,
        ):
            if chunk.text:
                yield chunk.text
            elif chunk.candidates and chunk.candidates[0].content.parts:
                for part in chunk.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        yield part.text

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using tiktoken approximation.

        The new SDK's token counting is sync-only, so we use tiktoken.
        """
        return tiktoken_count(text, self.model)

    def supports_tools(self) -> bool:
        """Gemini 2.0 supports function calling."""
        # Enable for 2.0 models
        return "2.0" in self.model or "1.5" in self.model

    def format_tool_calls(self, tool_calls: List[Dict]) -> List[types.Tool]:
        """Format tool calls for Gemini API."""
        if not tool_calls:
            return []

        function_declarations = []
        for tool in tool_calls:
            func = tool.get("function", {})
            function_declarations.append(types.FunctionDeclaration(
                name=func.get("name", tool.get("name", "")),
                description=func.get("description", ""),
                parameters=func.get("parameters", {}),
            ))

        return [types.Tool(function_declarations=function_declarations)]

    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool calls from Gemini response."""
        tool_calls = []

        if not hasattr(response, 'candidates') or not response.candidates:
            return tool_calls

        candidate = response.candidates[0]
        if not hasattr(candidate, 'content') or not candidate.content.parts:
            return tool_calls

        for part in candidate.content.parts:
            if hasattr(part, 'function_call') and part.function_call:
                fc = part.function_call
                tool_calls.append({
                    "id": f"call_{len(tool_calls)}",
                    "type": "function",
                    "function": {
                        "name": fc.name,
                        "arguments": dict(fc.args) if fc.args else {},
                    }
                })

        return tool_calls

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
            "gemini-2.0-flash-exp",
            "gemini-2.0-flash-thinking",
            "gemini-2.0-flash-thinking-exp",
            "gemini-2.0-pro",
            "gemini-2.0-pro-exp",
        ]
        return model in supported_models

    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost based on Google pricing."""
        # Google Gemini pricing (as of 2025, in dollars per 1K tokens)
        pricing = {
            "gemini-pro": {"input": 0.0005, "output": 0.0015},
            "gemini-1.5-pro": {"input": 0.00125, "output": 0.005},
            "gemini-1.5-flash": {"input": 0.00025, "output": 0.001},
            "gemini-2.0-flash": {"input": 0.00015, "output": 0.0006},
            "gemini-2.0-pro": {"input": 0.002, "output": 0.008},
        }

        # Get pricing for model (default to flash pricing)
        for key in pricing:
            if key in self.model:
                model_pricing = pricing[key]
                break
        else:
            model_pricing = pricing["gemini-2.0-flash"]

        # Calculate cost
        input_cost = (input_tokens / 1000) * model_pricing["input"]
        output_cost = (output_tokens / 1000) * model_pricing["output"]

        return input_cost + output_cost
