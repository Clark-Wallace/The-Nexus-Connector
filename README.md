# The Nexus Connector

<div align="center">

![Nexus Logo](https://img.shields.io/badge/Nexus-Connector-blue)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Beta-orange.svg)]()

**Universal AI connection interface - Establish a Nexus Connection with any AI provider**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [Documentation](#documentation) • [Contributing](#contributing)

</div>

---

## Overview

The Nexus Connector is a revolutionary universal connection interface that transforms AI APIs into autonomous CLI tools with persistent state. By establishing a Nexus Connection, you can turn any AI provider (OpenAI, Anthropic Claude, Google Gemini, xAI Grok, DeepSeek, Ollama) into a stateful, autonomous agent that can work continuously without user interface requirements.

### Key Benefits

- **🤖 API to CLI Transformation**: Convert any AI API into an autonomous CLI tool
- **📊 Persistent State**: Maintain conversation history and context across sessions
- **🔄 No UI Required**: Run autonomous AI workflows without user interface
- **🔌 Single Interface**: One API to establish Nexus Connections with all AI providers
- **🚀 Seamless Connection**: Maintain persistent Nexus Connections with automatic session management
- **🛠️ Tool Support**: Unified tool/function calling through the Nexus Connection
- **📝 Smart Routing**: The Nexus Connector automatically handles provider-specific requirements
- **🔧 Extensible**: Easy to add new AI providers to the Nexus Connector

## Features

### Supported Providers

| Provider | Models | Tool Support | Streaming | Web Support |
|----------|--------|--------------|-----------|-------------|
| OpenAI | GPT-4o, GPT-4, GPT-3.5 | ✅ Native | ✅ | ✅ |
| Anthropic | Claude 3 Opus, Sonnet, Haiku | ✅ Native | ✅ | ✅ |
| Google | Gemini 2.0, 1.5 Pro/Flash | ❌ Text-based | ✅ | ✅ |
| xAI | Grok-3, Grok-2 | ✅ Native | ✅ | ✅ |
| DeepSeek | DeepSeek-V3, Coder | ✅ Native | ✅ | ✅ |
| Ollama | Local LLMs | ✅ Native | ✅ | ✅ |

### Core Capabilities

- **🤖 Autonomous CLI Operations**: Transform APIs into stateful CLI tools that work without UI
- **📊 Persistent State Management**: Maintain conversation history and context across sessions
- **🔄 Iterative Task Execution**: Complex multi-step tasks completed autonomously
- **🛠️ Automatic Tool Execution**: Execute file operations and commands seamlessly
- **💬 Unified Message Format**: Consistent message structure across all providers
- **💰 Cost Tracking**: Built-in token usage and cost estimation
- **🌐 Web Integration**: Built-in FastAPI server for web applications
- **🎮 Game Master Mode**: Specialized connector for RPG game management
- **🔐 Session Management**: Persistent sessions with automatic cleanup
- **🏠 Local AI Support**: Run models locally with Ollama integration
- **⚡ Error Handling**: Graceful fallbacks and detailed error reporting

## Installation

### Prerequisites

- Python 3.8 or higher
- API keys for the AI providers you want to use

### Install from Source

```bash
# Clone the repository
git clone https://github.com/yourusername/nexus-connector.git
cd nexus-connector

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install in development mode
pip install -e .
```

### Install via pip (coming soon)

```bash
pip install nexus-connector
```

## Quick Start

### Autonomous CLI Mode

Transform any AI API into a stateful CLI tool:

```python
import asyncio
from nexus import UnifiedAIWrapper, AIProvider

async def autonomous_workflow():
    # Create autonomous AI agent with persistent state
    agent = UnifiedAIWrapper(
        provider=AIProvider.ANTHROPIC,
        api_key="your-api-key",
        workspace="./my_project",
        auto_execute=True,  # Enable autonomous execution
        max_iterations=10   # Allow extended autonomous work
    )
    
    # Start autonomous task - no UI required
    result = await agent.execute_task("""
    Analyze the codebase in this directory:
    1. Create a comprehensive documentation file
    2. Identify potential security issues
    3. Suggest performance optimizations
    4. Generate unit tests for key functions
    5. Create a deployment script
    """)
    
    # Agent maintains state throughout all operations
    print(f"Autonomous task completed: {result.success}")
    print(f"Files created: {result.files_created}")
    print(f"Conversation history: {len(agent.conversation_history)} messages")

asyncio.run(autonomous_workflow())
```

### Basic Usage

```python
import asyncio
from nexus import NexusConnector, AIProvider

async def main():
    # Establish a Nexus Connection with any provider
    connector = NexusConnector(
        provider=AIProvider.OPENAI,
        api_key="your-api-key"
    )
    
    # Send a message through the Nexus Connection
    response = await connector.send_message("Explain quantum computing in simple terms")
    print(response["content"])

asyncio.run(main())
```

### Provider Switching

```python
# Easy to switch providers - same Nexus Connection interface
connector = NexusConnector(
    provider=AIProvider.ANTHROPIC,  # Just change the provider
    api_key="your-anthropic-key"
)
```

### Web Integration

```python
from nexus.web import WebConnector

# Create web-enabled connector with built-in FastAPI server
web_connector = WebConnector(
    provider=AIProvider.OPENAI,
    api_key="your-api-key",
    port=8000
)

# Start the web server
await web_connector.start_server()

# Now you can make HTTP requests to localhost:8000
```

### Game Master Mode

```python
from nexus.connectors import GMConnector

# Specialized connector for RPG game management
gm = GMConnector(
    provider=AIProvider.ANTHROPIC,
    api_key="your-key",
    game_system="D20 Narrative Hybrid"
)

# Send game action
response = await gm.process_action({
    "session_id": "game_123",
    "player_action": {"text": "I search the ancient ruins"},
    "game_state": {"scene": "mysterious_temple", "location": "entrance"},
    "character": {"name": "Thorin", "class": "Warrior"}
})

print(response.narrative)  # Rich narrative response
print(response.suggested_actions)  # Player choices
```

### Local AI with Ollama

```python
# Run AI models locally for privacy
connector = NexusConnector(
    provider=AIProvider.OLLAMA,
    model="llama3.3:70b",
    base_url="http://localhost:11434"
)

response = await connector.send_message("Hello from local AI!")
```

### Complex Task Execution

```python
# Execute multi-step tasks through the Nexus Connection
connector = NexusConnector(
    provider=AIProvider.OPENAI,
    api_key="your-api-key",
    workspace="./my_project"
)

task = """
Create a Python web scraper that:
1. Fetches data from a website
2. Parses HTML content
3. Saves results to CSV
4. Includes error handling
"""

result = await wrapper.execute_task(task)
print(f"Task completed: {result.success}")
print(f"Files created: {result.files_created}")
```

### Tool/Function Calling

```python
# Define tools for the AI to use
tools = [{
    "type": "function",
    "function": {
        "name": "create_file",
        "description": "Create a new file with content",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {"type": "string"},
                "content": {"type": "string"}
            }
        }
    }
}]

response = await wrapper.send_message(
    "Create a README.md file with project documentation",
    tools=tools
)
```

## Architecture

### Component Overview

```
nexus/
├── core/
│   ├── base_connector.py      # Abstract base class for connectors
│   ├── unified_wrapper.py     # Main wrapper implementation
│   ├── tool_executor.py       # Tool execution engine
│   └── text_apply_engine.py   # Text-based code extraction
├── connectors/
│   ├── openai_connector.py    # OpenAI implementation
│   ├── anthropic_connector.py # Anthropic implementation
│   ├── google_connector.py    # Google implementation
│   ├── xai_connector.py       # xAI implementation
│   ├── deepseek_connector.py  # DeepSeek implementation
│   ├── ollama_connector.py    # Ollama local LLM support
│   └── gm_connector.py        # Game Master specialized connector
├── web/
│   ├── web_connector.py       # Web-enabled connector with FastAPI
│   ├── session_manager.py     # Session management for web apps
│   └── models.py              # Pydantic models for web API
└── utils/
    ├── logger.py              # Logging utilities
    └── cost_tracker.py        # Token and cost tracking
```

### Design Patterns

1. **Strategy Pattern**: Each AI provider is implemented as a separate connector
2. **Adapter Pattern**: Connectors adapt provider-specific APIs to unified interface
3. **Factory Pattern**: Dynamic connector creation based on provider selection
4. **Iterator Pattern**: Streaming responses handled consistently

## Advanced Usage

### Custom Connectors

Create your own connector for new AI providers:

```python
from nexus.core.base_connector import BaseConnector, Response

class MyCustomConnector(BaseConnector):
    async def send_message(self, messages, **kwargs):
        # Implement your provider's API call
        response = await self.client.chat(messages)
        
        return Response(
            content=response.text,
            tool_calls=[],
            usage={"total_tokens": response.tokens}
        )
```

### Configuration

```python
# Advanced configuration options
wrapper = UnifiedAIWrapper(
    provider=AIProvider.OPENAI,
    api_key="your-api-key",
    model="gpt-4o",              # Specific model
    max_iterations=10,           # Max continuation iterations
    auto_execute=True,           # Auto-execute tool calls
    safe_mode=True,              # Confirm destructive operations
    verbose=True,                # Detailed logging
    temperature=0.7,             # Model temperature
    max_tokens=4096              # Max response tokens
)
```

### Streaming Responses

```python
# Stream responses as they arrive
async for chunk in wrapper.stream_message("Write a story about AI"):
    print(chunk, end="", flush=True)
```

## API Reference

### UnifiedAIWrapper

The main class for interacting with AI providers.

#### Methods

- `send_message(message, **kwargs)` - Send a single message
- `execute_task(task, **kwargs)` - Execute a complex multi-step task
- `stream_message(message, **kwargs)` - Stream response tokens
- `count_tokens(text)` - Count tokens for the current provider
- `clear_history()` - Clear conversation history

#### Parameters

- `provider` - AI provider enum (OPENAI, ANTHROPIC, etc.)
- `api_key` - API key for the provider
- `model` - Model to use (optional, uses provider default)
- `workspace` - Working directory for file operations
- `max_iterations` - Maximum iterations for task execution
- `auto_execute` - Whether to automatically execute tool calls
- `safe_mode` - Require confirmation for destructive operations
- `verbose` - Enable detailed logging

### AIProvider Enum

Available providers:

- `AIProvider.OPENAI` - OpenAI GPT models
- `AIProvider.ANTHROPIC` - Anthropic Claude models
- `AIProvider.GOOGLE` - Google Gemini models
- `AIProvider.XAI` - xAI Grok models
- `AIProvider.DEEPSEEK` - DeepSeek models
- `AIProvider.OLLAMA` - Local LLM models via Ollama

## Web Features

### FastAPI Server Integration

The Nexus Connector includes built-in web server capabilities using FastAPI:

```python
from nexus.web import WebConnector
from fastapi import FastAPI

# Create web-enabled connector
web_connector = WebConnector(
    provider=AIProvider.OPENAI,
    api_key="your-api-key",
    port=8000
)

# Start the server
await web_connector.start_server()

# The server provides these endpoints:
# POST /chat - Send messages to AI
# GET /sessions/{session_id} - Get session info
# DELETE /sessions/{session_id} - Delete session
# GET /health - Health check
```

### Session Management

Persistent sessions with automatic cleanup:

```python
from nexus.web.session_manager import SessionManager

# Sessions are automatically created and managed
session_manager = SessionManager()

# Get or create session
session = await session_manager.get_or_create_session("user_123")

# Sessions automatically clean up after 24 hours of inactivity
await session_manager.cleanup_old_sessions()
```

### Game Master Web API

Specialized web API for RPG game management:

```python
from nexus.connectors import GMConnector

# The GM connector provides a web API at /gm/action
# Send POST requests with game state and receive narrative responses

{
    "session_id": "game_123",
    "player_action": {"text": "I examine the mysterious door"},
    "game_state": {"scene": "dungeon_entrance", "location": "Ancient Crypt"},
    "character": {"name": "Lyralei", "class": "Ranger"}
}

# Response includes:
{
    "narrative": "You notice ancient runes glowing faintly...",
    "suggested_actions": [
        {"key": "A", "emoji": "🔍", "text": "Investigate the runes"},
        {"key": "B", "emoji": "🗡️", "text": "Draw your weapon"},
        {"key": "C", "emoji": "🚪", "text": "Try to open the door"},
        {"key": "D", "emoji": "👂", "text": "Listen for sounds beyond"}
    ],
    "requires_roll": {"dice": "1d20", "skill": "Investigation", "dc": 15}
}
```

## Examples

### Autonomous Code Analysis Pipeline

```python
async def autonomous_code_analysis():
    """
    Demonstrates autonomous CLI workflow - no UI required
    AI agent analyzes codebase and performs multiple tasks with persistent state
    """
    agent = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        workspace="./target_project",
        auto_execute=True,
        max_iterations=20,
        verbose=True
    )
    
    # Multi-step autonomous task
    result = await agent.execute_task("""
    Perform a comprehensive code analysis:
    
    1. Scan all Python files and create a dependency map
    2. Identify potential security vulnerabilities
    3. Generate performance optimization suggestions
    4. Create unit tests for untested functions
    5. Generate API documentation
    6. Create a deployment checklist
    7. Write a technical summary report
    
    Maintain context throughout all steps and reference previous analysis in later steps.
    """)
    
    print(f"✅ Autonomous analysis completed: {result.success}")
    print(f"📁 Files created: {', '.join(result.files_created)}")
    print(f"💬 Conversation steps: {len(agent.conversation_history)}")
    print(f"💰 Total tokens used: {agent.total_tokens}")

# Run completely autonomously
asyncio.run(autonomous_code_analysis())
```

### Web Scraper Example

```python
async def create_web_scraper():
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        workspace="./scraper_project"
    )
    
    task = """
    Create a complete web scraper that:
    1. Scrapes product data from an e-commerce site
    2. Handles pagination
    3. Saves to both JSON and CSV formats
    4. Includes retry logic and error handling
    5. Adds logging and progress tracking
    """
    
    result = await wrapper.execute_task(task)
    
    if result.success:
        print("✅ Web scraper created successfully!")
        print(f"Files: {', '.join(result.files_created)}")
```

### Multi-Provider Comparison

```python
async def compare_providers(prompt):
    providers = [
        (AIProvider.OPENAI, "OPENAI_API_KEY"),
        (AIProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (AIProvider.GOOGLE, "GOOGLE_API_KEY"),
    ]
    
    for provider, key_name in providers:
        wrapper = UnifiedAIWrapper(
            provider=provider,
            api_key=os.getenv(key_name)
        )
        
        response = await wrapper.send_message(prompt)
        print(f"\n{provider.display_name}:")
        print(response["content"])
        print(f"Tokens: {response.get('usage', {}).get('total_tokens', 'N/A')}")
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run specific provider tests
pytest tests/test_openai_connector.py

# Run integration tests
pytest tests/integration/

# Test with coverage
pytest --cov=nexus tests/
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone and setup
git clone https://github.com/yourusername/nexus-unified-wrapper.git
cd nexus-unified-wrapper

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

### Adding a New Provider

1. Create a new connector in `nexus/connectors/`
2. Implement the `BaseConnector` interface
3. Add the provider to `AIProvider` enum
4. Update the factory method in `UnifiedAIWrapper`
5. Add tests and documentation

## Roadmap

### ✅ Completed
- [x] Core unified interface for multiple AI providers
- [x] Web integration with FastAPI server
- [x] Session management with automatic cleanup
- [x] Game Master specialized connector
- [x] Local AI support via Ollama
- [x] Streaming responses
- [x] Tool/function calling support
- [x] GitHub Actions CI/CD pipeline
- [x] Pre-commit hooks and code quality

### 🚧 In Progress
- [ ] Comprehensive test coverage
- [ ] Documentation improvements
- [ ] Performance optimizations

### 🔮 Future Enhancements
- [ ] Additional providers (Cohere, AI21, Mistral, etc.)
- [ ] Caching layer for responses
- [ ] Rate limiting and retry logic with exponential backoff
- [ ] Plugin system for custom connectors
- [ ] Web UI dashboard for testing and monitoring
- [ ] Batch processing support for multiple requests
- [ ] Fine-tuning integration and model management
- [ ] Evaluation framework for model comparison
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests
- [ ] OpenTelemetry integration for observability
- [ ] Real-time collaboration features
- [ ] Advanced prompt templates and management

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for unified AI interfaces
- Built on the proven patterns from OpenAI's GPT-4o
- Thanks to all contributors and early adopters

## Support

- 📧 Email: support@nexus-ai.dev
- 💬 Discord: [Join our community](https://discord.gg/nexus-ai)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/nexus-unified-wrapper/issues)
- 📖 Docs: [Full Documentation](https://nexus-ai.dev/docs)

---

<div align="center">
Made with ❤️ by the Nexus Team
</div>