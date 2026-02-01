"""
Base connector interface for AI providers.

This defines the contract that all AI connectors must implement.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass


class AIProvider(Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    XAI = "xai"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
    
    @property
    def display_name(self) -> str:
        """Human-friendly display name."""
        names = {
            "openai": "OpenAI",
            "anthropic": "Anthropic Claude",
            "google": "Google Gemini",
            "xai": "xAI Grok",
            "deepseek": "DeepSeek",
            "ollama": "Ollama (Local)"
        }
        return names.get(self.value, self.value.title())


@dataclass
class Message:
    """Unified message format."""
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None


@dataclass
class Response:
    """Unified response format."""
    content: str
    tool_calls: List[Dict]
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None


class BaseConnector(ABC):
    """
    Abstract base class for AI provider connectors.
    
    Each AI provider must implement this interface to work with Nexus.
    """
    
    def __init__(self, api_key: str, model: Optional[str] = None, **kwargs):
        """
        Initialize connector.
        
        Args:
            api_key: API key for the provider
            model: Model to use (provider-specific default if None)
            **kwargs: Additional provider-specific parameters
        """
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.kwargs = kwargs
    
    @abstractmethod
    def get_default_model(self) -> str:
        """Get the default model for this provider."""
        pass
    
    @abstractmethod
    async def send_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> Response:
        """
        Send messages to the AI and get a response.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters (temperature, max_tokens, etc.)
            
        Returns:
            Unified Response object
        """
        pass
    
    @abstractmethod
    async def stream_message(
        self,
        messages: List[Message],
        **kwargs
    ) -> AsyncIterator[str]:
        """
        Stream response tokens as they arrive.
        
        Args:
            messages: List of messages in the conversation
            **kwargs: Additional parameters
            
        Yields:
            Response tokens as they arrive
        """
        pass
    
    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text for this provider.
        
        Args:
            text: Text to count tokens for
            
        Returns:
            Number of tokens
        """
        pass
    
    @abstractmethod
    def supports_tools(self) -> bool:
        """Check if this provider supports tool/function calling."""
        pass
    
    @abstractmethod
    def format_tool_calls(self, tool_calls: List[Dict]) -> Any:
        """
        Format tool calls for this provider's API.
        
        Args:
            tool_calls: List of tool calls in Nexus format
            
        Returns:
            Tool calls in provider-specific format
        """
        pass
    
    @abstractmethod
    def extract_tool_calls(self, response: Any) -> List[Dict]:
        """
        Extract tool calls from provider's response.
        
        Args:
            response: Raw response from provider
            
        Returns:
            List of tool calls in Nexus format
        """
        pass
    
    def validate_model(self, model: str) -> bool:
        """
        Validate if model is supported by this provider.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is supported
        """
        return True  # Override in subclasses for validation
    
    def get_cost_estimate(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for token usage.
        
        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            
        Returns:
            Estimated cost in dollars
        """
        return 0.0  # Override in subclasses with actual pricing