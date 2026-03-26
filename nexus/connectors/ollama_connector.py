"""
Ollama Connector - Support for local models via Ollama

Supports tool/function calling for models that have the Tools capability
(e.g., llama3.1, qwen2.5, mistral, qwen3).
"""

import aiohttp
import json
from typing import List, Dict, Any, Optional, AsyncIterator
import logging

from ..core.base_connector import BaseConnector, Message, Response, AIProvider
from ..utils.tokens import TokenCounter

logger = logging.getLogger(__name__)


class OllamaConnector(BaseConnector):
    """
    Connector for Ollama - run large language models locally.

    Ollama allows you to run models like Llama, Mistral, Qwen, and others
    on your own hardware without sending data to external APIs.
    Supports tool/function calling for compatible models.
    """

    def __init__(
        self,
        api_key: str = "not-required",
        model: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        super().__init__(api_key, model, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.model = model or "llama3.2:3b"
        self._token_counter = TokenCounter(self.model)
        self._check_ollama_status()

    @property
    def provider(self) -> AIProvider:
        return AIProvider.OLLAMA

    @property
    def default_model(self) -> str:
        return "llama3.2:3b"

    def get_default_model(self) -> str:
        return "llama3.2:3b"

    def count_tokens(self, text: str) -> int:
        return self._token_counter.count(text)

    def supports_tools(self) -> bool:
        """Ollama supports tool/function calling for compatible models."""
        return True

    def supports_streaming(self) -> bool:
        return True

    def format_tool_calls(self, tool_calls: List[Dict]) -> List[Dict]:
        """Format tool calls for Ollama API (same format as OpenAI)."""
        formatted = []
        for tool in tool_calls:
            formatted.append({
                "id": tool.get("id", f"call_{len(formatted)}"),
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "arguments": json.dumps(tool.get("arguments", {}))
                        if isinstance(tool.get("arguments"), dict)
                        else tool.get("arguments", "{}"),
                }
            })
        return formatted

    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """Extract tool calls from Ollama response.

        Ollama returns tool_calls as a list of dicts (not SDK objects like OpenAI),
        where each entry has: {"function": {"name": "...", "arguments": {...}}}
        """
        tool_calls = []

        # response is the raw message dict from Ollama
        raw_calls = []
        if isinstance(response, dict):
            raw_calls = response.get("tool_calls", [])
        elif hasattr(response, "tool_calls") and response.tool_calls:
            raw_calls = response.tool_calls

        for i, tc in enumerate(raw_calls):
            func = tc.get("function", tc) if isinstance(tc, dict) else tc
            name = func.get("name", "") if isinstance(func, dict) else getattr(func, "name", "")
            args = func.get("arguments", {}) if isinstance(func, dict) else getattr(func, "arguments", {})

            # Arguments may already be a dict (Ollama) or a JSON string (OpenAI compat)
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}

            tool_calls.append({
                "id": tc.get("id", f"call_{i}") if isinstance(tc, dict) else f"call_{i}",
                "name": name,
                "arguments": args,
            })

        return tool_calls

    def _check_ollama_status(self):
        """Check if Ollama is running and available."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                logger.info("Ollama server is running")
                models = response.json().get("models", [])
                if models:
                    logger.info(f"Available models: {[m['name'] for m in models]}")
                else:
                    logger.warning("No models found. Run 'ollama pull llama3.2' to download a model")
        except Exception:
            logger.warning(f"Ollama not detected at {self.base_url}. Make sure Ollama is running.")

    def _convert_messages(self, messages: List[Message]) -> tuple[list, str]:
        """Convert Nexus messages to Ollama format, extracting system prompt."""
        ollama_messages = []
        system_prompt = ""

        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue

            ollama_msg = {"role": msg.role, "content": msg.content}

            # Include tool_calls on assistant messages (for conversation history)
            if msg.tool_calls and msg.role == "assistant":
                ollama_msg["tool_calls"] = self.format_tool_calls(msg.tool_calls)

            # Include tool_call_id for tool result messages
            if msg.tool_call_id and msg.role == "tool":
                ollama_msg["tool_call_id"] = msg.tool_call_id

            ollama_messages.append(ollama_msg)

        return ollama_messages, system_prompt

    async def send_message(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Response:
        """Send messages to Ollama with tool support."""
        ollama_messages, system_prompt = self._convert_messages(messages)

        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": False,
            "options": {"temperature": temperature},
        }

        if system_prompt:
            request_data["system"] = system_prompt
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens

        # Pass tools if provided
        if kwargs.get("tools"):
            request_data["tools"] = kwargs["tools"]

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=request_data,
                    headers={"Content-Type": "application/json"},
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")

                    data = await response.json()
                    message = data.get("message", {})

                    # Extract tool calls from response
                    tool_calls = self.extract_tool_calls(message)

                    # Token estimation
                    prompt_text = "".join(msg.content for msg in messages)
                    content = message.get("content", "")

                    return Response(
                        content=content,
                        tool_calls=tool_calls,
                        usage={
                            "prompt_tokens": self.count_tokens(prompt_text),
                            "completion_tokens": self.count_tokens(content),
                            "total_tokens": self.count_tokens(prompt_text + content),
                        },
                        raw_response=data,
                    )

            except aiohttp.ClientError as e:
                logger.error(f"Connection error: {e}")
                raise Exception(
                    f"Failed to connect to Ollama at {self.base_url}. "
                    "Make sure Ollama is running (ollama serve)"
                )

    async def stream_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """Stream responses from Ollama."""
        ollama_messages, system_prompt = self._convert_messages(messages)

        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True,
        }

        if system_prompt:
            request_data["system"] = system_prompt

        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=request_data,
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue

    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        return [model["name"] for model in data.get("models", [])]
                    return []
            except Exception:
                return []

    async def pull_model(self, model_name: str) -> bool:
        """Pull a model from Ollama library."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/api/pull",
                    json={"name": model_name},
                ) as response:
                    return response.status == 200
            except Exception:
                return False


def create_ollama_connector(
    model: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434",
) -> OllamaConnector:
    """Create an Ollama connector for local model inference."""
    return OllamaConnector(model=model, base_url=base_url)
