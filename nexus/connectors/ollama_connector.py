"""
Ollama Connector - Support for local models via Ollama
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
    
    Ollama allows you to run models like Llama, Mistral, and others
    on your own hardware without sending data to external APIs.
    """
    
    def __init__(
        self, 
        api_key: str = "not-required",  # Ollama doesn't need API keys
        model: Optional[str] = None,
        base_url: str = "http://localhost:11434",
        **kwargs
    ):
        """
        Initialize Ollama connector.
        
        Args:
            api_key: Not used for Ollama, kept for compatibility
            model: Model name (e.g., "llama2", "mistral", "codellama")
            base_url: Ollama server URL (default: http://localhost:11434)
            **kwargs: Additional parameters
        """
        super().__init__(api_key, model, **kwargs)
        self.base_url = base_url.rstrip('/')
        self.model = model or "llama3.2"

        # Initialize token counter (uses tiktoken for approximation)
        self._token_counter = TokenCounter(self.model)

        # Check if Ollama is running
        self._check_ollama_status()
    
    @property
    def provider(self) -> AIProvider:
        """Return the provider type."""
        return AIProvider.OLLAMA
    
    @property
    def default_model(self) -> str:
        """Default model for Ollama."""
        return "llama3.2"

    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        return "llama3.2"

    def format_tool_calls(self, tool_calls: list) -> Any:
        """Ollama doesn't support tool calling — return empty."""
        return []

    def extract_tool_calls(self, response: Any) -> list:
        """Ollama doesn't support tool calling — return empty."""
        return []
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for Ollama models.

        Uses tiktoken with cl100k_base as approximation.
        Note: Actual tokenization varies by model; this is an estimate.
        """
        return self._token_counter.count(text)
    
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
                    logger.warning("No models found. Run 'ollama pull llama2' to download a model")
        except Exception as e:
            logger.warning(f"Ollama not detected at {self.base_url}. Make sure Ollama is running.")
    
    async def send_message(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        stream: bool = False,
        **kwargs
    ) -> Response:
        """
        Send messages to Ollama for completion.
        
        Args:
            messages: List of conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            **kwargs: Additional parameters
            
        Returns:
            Response object with generated content
        """
        # Convert messages to Ollama format
        ollama_messages = []
        system_prompt = ""
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # Build request
        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": stream,
            "options": {
                "temperature": temperature,
            }
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
            
        if max_tokens:
            request_data["options"]["num_predict"] = max_tokens
        
        # Make API call
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=request_data,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"Ollama API error: {response.status} - {error_text}")
                    
                    # Parse response
                    data = await response.json()
                    
                    return Response(
                        content=data["message"]["content"],
                        tool_calls=[],  # Ollama doesn't support tools yet
                        usage={
                            "prompt_tokens": self.count_tokens(
                                "".join(msg.content for msg in messages)
                            ),
                            "completion_tokens": self.count_tokens(
                                data["message"]["content"]
                            ),
                            "total_tokens": self.count_tokens(
                                "".join(msg.content for msg in messages) + 
                                data["message"]["content"]
                            )
                        },
                        raw_response=data
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
        """
        Stream responses from Ollama.
        
        Yields content chunks as they arrive.
        """
        # Convert messages
        ollama_messages = []
        system_prompt = ""
        
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
            else:
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        request_data = {
            "model": self.model,
            "messages": ollama_messages,
            "stream": True
        }
        
        if system_prompt:
            request_data["system"] = system_prompt
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/chat",
                json=request_data
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "message" in data and "content" in data["message"]:
                                yield data["message"]["content"]
                        except json.JSONDecodeError:
                            continue
    
    def supports_tools(self) -> bool:
        """Ollama doesn't support function calling yet."""
        return False
    
    def supports_streaming(self) -> bool:
        """Ollama supports streaming."""
        return True
    
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
                    json={"name": model_name}
                ) as response:
                    return response.status == 200
            except Exception:
                return False


# Helper function for easy setup
def create_ollama_connector(
    model: str = "llama3.2",
    base_url: str = "http://localhost:11434"
) -> OllamaConnector:
    """
    Create an Ollama connector for local model inference.
    
    Example:
        connector = create_ollama_connector(model="mistral")
        response = await connector.send_message([
            Message(role="user", content="Hello!")
        ])
    """
    return OllamaConnector(model=model, base_url=base_url)