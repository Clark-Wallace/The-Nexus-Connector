"""
Pytest configuration and fixtures for Nexus tests.
"""

import os
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock

from nexus import NexusConnector as UnifiedAIWrapper, AIProvider


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_api_key() -> str:
    """Provide a mock API key for testing."""
    return "test-api-key-12345"


@pytest.fixture
def mock_openai_response() -> dict:
    """Mock OpenAI API response."""
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677652288,
        "model": "gpt-3.5-turbo",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "Hello! How can I help you today?"
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 10,
            "total_tokens": 20
        }
    }


@pytest.fixture
def mock_anthropic_response() -> dict:
    """Mock Anthropic API response."""
    return {
        "id": "msg_123",
        "type": "message",
        "role": "assistant",
        "content": [{
            "type": "text",
            "text": "Hello! How can I help you today?"
        }],
        "model": "claude-3-opus",
        "stop_reason": "end_turn",
        "usage": {
            "input_tokens": 10,
            "output_tokens": 10
        }
    }


@pytest.fixture
async def mock_wrapper(mock_api_key: str) -> AsyncGenerator[UnifiedAIWrapper, None]:
    """Create a mock UnifiedAIWrapper for testing."""
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.OPENAI,
        api_key=mock_api_key,
        model="gpt-3.5-turbo",
        auto_execute=False,
        verbose=False
    )
    
    # Mock the connector's send_message method
    wrapper.connector.send_message = AsyncMock(return_value={
        "content": "Test response",
        "tool_calls": [],
        "usage": {"total_tokens": 20}
    })
    
    yield wrapper


@pytest.fixture
def temp_workspace(tmp_path) -> Generator[str, None, None]:
    """Create a temporary workspace for file operations."""
    workspace = tmp_path / "test_workspace"
    workspace.mkdir()
    original_cwd = os.getcwd()
    os.chdir(workspace)
    yield str(workspace)
    os.chdir(original_cwd)


@pytest.fixture
def sample_messages() -> list:
    """Sample messages for testing."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
        {"role": "assistant", "content": "Hi there! How can I help you?"},
        {"role": "user", "content": "What's the weather like?"}
    ]


@pytest.fixture
def mock_env_vars(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "OPENAI_API_KEY": "test-openai-key",
        "ANTHROPIC_API_KEY": "test-anthropic-key",
        "GOOGLE_API_KEY": "test-google-key",
        "GROQ_API_KEY": "test-groq-key",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    return env_vars


# Marker definitions
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
    config.addinivalue_line(
        "markers", "requires_api_key: marks tests that require real API keys"
    )