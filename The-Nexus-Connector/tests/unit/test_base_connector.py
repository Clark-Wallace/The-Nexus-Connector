"""Unit tests for base connector functionality."""

import pytest
from nexus.core.base_connector import AIProvider, Message, Response


class TestAIProvider:
    """Test AIProvider enum."""
    
    def test_provider_values(self):
        """Test provider enum values."""
        assert AIProvider.OPENAI.value == "openai"
        assert AIProvider.ANTHROPIC.value == "anthropic"
        assert AIProvider.GOOGLE.value == "google"
        assert AIProvider.XAI.value == "xai"
        assert AIProvider.DEEPSEEK.value == "deepseek"
        assert AIProvider.OLLAMA.value == "ollama"
    
    def test_display_names(self):
        """Test provider display names."""
        assert AIProvider.OPENAI.display_name == "OpenAI"
        assert AIProvider.ANTHROPIC.display_name == "Anthropic Claude"
        assert AIProvider.GOOGLE.display_name == "Google Gemini"
        assert AIProvider.XAI.display_name == "xAI Grok"
        assert AIProvider.DEEPSEEK.display_name == "DeepSeek"
        assert AIProvider.OLLAMA.display_name == "Ollama (Local)"


class TestMessage:
    """Test Message dataclass."""
    
    def test_message_creation(self):
        """Test creating a message."""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls is None
        assert msg.tool_call_id is None
    
    def test_message_with_tools(self):
        """Test message with tool calls."""
        tool_calls = [{"name": "test_tool", "arguments": "{}"}]
        msg = Message(
            role="assistant",
            content="I'll help with that.",
            tool_calls=tool_calls
        )
        assert msg.tool_calls == tool_calls


class TestResponse:
    """Test Response dataclass."""
    
    def test_response_creation(self):
        """Test creating a response."""
        resp = Response(
            content="Test response",
            tool_calls=[],
            usage={"total_tokens": 10}
        )
        assert resp.content == "Test response"
        assert resp.tool_calls == []
        assert resp.usage["total_tokens"] == 10
        assert resp.finish_reason is None
        assert resp.raw_response is None