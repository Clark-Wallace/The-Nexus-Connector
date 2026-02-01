# The Nexus Connector

<div align="center">

![Nexus Logo](https://img.shields.io/badge/Nexus-Connector-blue)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg)]()

**The Agentic AI Toolkit - Build AI agents that work with any provider**

[Features](#features) • [Installation](#installation) • [Quick Start](#quick-start) • [CLI](#cli) • [Documentation](#documentation)

</div>

---

## Overview

The Nexus Connector is a production-ready toolkit for building AI agents. Unlike simple API wrappers, Nexus provides everything you need for agentic applications: a plugin system for custom tools, smart routing across providers, automatic fallback, full observability, and enterprise-grade reliability features.

**What makes Nexus different:**
- **Agentic-first**: Built for AI agents that use tools, not just chat
- **Provider-agnostic**: Same code works with OpenAI, Anthropic, Google, and more
- **Observable**: See exactly what your agent is doing with hooks and logs
- **Production-ready**: Retry logic, circuit breakers, rate limiting, metrics

### Key Benefits

| Feature | Description |
|---------|-------------|
| **Plugin System** | Create custom tools with `@tool` decorator |
| **Smart Routing** | Route tasks by type (code → Claude, math → GPT-4) |
| **Automatic Fallback** | Failed provider? Automatically try the next one |
| **Full Observability** | Hooks for every tool call, execution logs, metrics |
| **Human-in-the-Loop** | Pause before destructive operations |
| **MCP Support** | Connect to any MCP tool server |
| **CLI Included** | `nexus chat` and `nexus run` out of the box |
| **Production Hardening** | Retry, circuit breaker, rate limiting |

## Features

### Supported Providers

| Provider | Models | Tool Support | Streaming |
|----------|--------|--------------|-----------|
| OpenAI | GPT-4o, GPT-4, GPT-3.5 | ✅ Native | ✅ |
| Anthropic | Claude 3.5/3 Opus, Sonnet, Haiku | ✅ Native | ✅ |
| Google | Gemini 2.0, 1.5 Pro/Flash | ✅ | ✅ |
| xAI | Grok-3, Grok-2 | ✅ Native | ✅ |
| DeepSeek | DeepSeek-V3, Coder | ✅ Native | ✅ |
| Ollama | Any local LLM | ✅ Native | ✅ |

### Plugin System

Create custom tools with the `@tool` decorator:

```python
from nexus import NexusConnector, tool

@tool(description="Search our documentation")
async def search_docs(query: str, max_results: int = 5) -> str:
    results = await my_search_engine.search(query, limit=max_results)
    return format_results(results)

@tool(description="Send a Slack message", destructive=True)
async def send_slack(channel: str, message: str) -> str:
    return await slack.post_message(channel, message)

# Tools are automatically available to the AI
connector = NexusConnector(
    provider="openai",
    api_key=api_key,
    tools=[search_docs, send_slack],
)
```

### Smart Routing

Route tasks to the best provider automatically:

```python
# Auto-configure from environment variables
connector = NexusConnector(router="auto")

# Or define routing rules
connector = NexusConnector(
    router="auto",
    routing_rules={
        "code": "anthropic",    # Claude for code
        "math": "openai",       # GPT-4 for math
        "creative": "anthropic", # Claude for writing
        "bulk": "deepseek",     # DeepSeek for cost
    }
)

# Routing strategies
connector = NexusConnector(router="cost")      # Cheapest provider
connector = NexusConnector(router="quality")   # Best for task type
connector = NexusConnector(router="latency")   # Fastest provider
connector = NexusConnector(router="adaptive")  # Balances all factors
```

### Observable Execution

See exactly what your agent is doing:

```python
connector = NexusConnector(
    provider="openai",
    api_key=api_key,
    # Hooks for full visibility
    on_tool_call=lambda tc: print(f"Calling: {tc['name']}"),
    on_tool_result=lambda tr: print(f"Result: {tr['result']}"),
    on_step=lambda step, status: print(f"Step {step}: {status}"),
    on_error=lambda e: logger.error(f"Error: {e}"),
    on_provider_switch=lambda old, new, reason: print(f"Switched: {old} → {new}"),
)

# Execute with detailed logging
result = await connector.execute_task(
    "Refactor the auth module",
    log_path="execution_log.json",  # Save detailed log
)

# Access execution metrics
print(result.execution_log.get_metrics())
```

### Human-in-the-Loop

Control when to pause for confirmation:

```python
def confirm_callback(tool_metadata):
    print(f"Tool: {tool_metadata.name}")
    print(f"Destructive: {tool_metadata.is_destructive}")
    return input("Proceed? [y/N]: ").lower() == 'y'

result = await connector.execute_task(
    "Clean up old log files",
    confirm_destructive=True,  # Pause before delete/rm operations
    confirm_callback=confirm_callback,
)

# Or confirm before every tool call
result = await connector.execute_task(
    "Refactor codebase",
    confirm_all=True,
)

# Git checkpoint for safety
result = await connector.execute_task(
    "Major refactoring",
    checkpoint=True,        # Git commit before changes
    rollback_on_fail=True,  # Revert if task fails
)
```

### MCP Support

Connect to MCP (Model Context Protocol) servers:

```python
# Connect to well-known MCP servers
connector = NexusConnector(
    provider="openai",
    api_key=api_key,
    mcp_servers=["filesystem", "github", "memory"],
)

# MCP tools available alongside custom tools
print(connector.get_mcp_tools())
# ['mcp_filesystem_read_file', 'mcp_filesystem_write_file', ...]

# Add servers dynamically
await connector.add_mcp_server("postgres")
await connector.add_mcp_server("custom", config={
    "command": "python",
    "args": ["-m", "my_mcp_server"],
})
```

Supported MCP servers: `filesystem`, `github`, `postgres`, `sqlite`, `memory`, `fetch`, `time`, `brave-search`, `puppeteer`, `slack`

### Production Hardening

Enterprise-ready reliability:

```python
from nexus import RETRY_CONFIGS, get_rate_limiter, get_metrics

# Pre-configured retry strategies
# "aggressive", "standard", "conservative", "rate_limit"
handler = RetryHandler(config=RETRY_CONFIGS["standard"])

# Rate limiting per provider
limiter = get_rate_limiter("openai")
await limiter.acquire_request(timeout=30)

# Prometheus metrics
metrics = get_metrics()
await metrics.record_request(
    provider="openai",
    success=True,
    duration_seconds=1.5,
    input_tokens=100,
    output_tokens=500,
)
print(metrics.get_prometheus_metrics())

# Circuit breaker
from nexus import CircuitBreaker
cb = CircuitBreaker("openai", config=CircuitBreakerConfig(
    failure_threshold=5,
    timeout=30.0,
))

# Redis distributed sessions
from nexus.web import RedisSessionStore
store = RedisSessionStore(redis_url="redis://localhost:6379")
```

## Installation

```bash
# Clone the repository
git clone https://github.com/Clark-Wallace/The-Nexus-Connector.git
cd The-Nexus-Connector

# Install in development mode
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt
```

### Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export XAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."
```

## CLI

Nexus includes a powerful command-line interface:

```bash
# Interactive chat
nexus chat --provider openai
nexus chat --provider anthropic --model claude-sonnet-4-20250514

# One-shot task execution
nexus run "Create a Python function to sort a list" --provider openai

# Compare providers
nexus compare "Explain recursion" --providers openai,anthropic,deepseek

# Start web server
nexus serve --port 8000

# List providers and tools
nexus providers
nexus tools
```

### Interactive Chat Commands

```
/help     - Show available commands
/clear    - Clear conversation history
/save     - Save conversation to file
/switch   - Switch provider
/model    - Change model
/system   - Set system prompt
/tokens   - Show token usage
```

## Quick Start

### Basic Usage

```python
import asyncio
from nexus import NexusConnector

async def main():
    connector = NexusConnector(
        provider="openai",
        api_key="your-api-key"
    )

    response = await connector.send_message("Hello!")
    print(response["content"])

asyncio.run(main())
```

### With Custom Tools

```python
from nexus import NexusConnector, tool

@tool(description="Get weather for a city")
async def get_weather(city: str) -> str:
    return f"Weather in {city}: 72°F, Sunny"

async def main():
    connector = NexusConnector(
        provider="openai",
        api_key="your-api-key",
        tools=[get_weather],
    )

    response = await connector.send_message(
        "What's the weather in San Francisco?"
    )
    print(response["content"])
```

### With Smart Routing

```python
from nexus import NexusConnector

async def main():
    # Auto-configure from environment, with fallback
    connector = NexusConnector(
        router="auto",
        routing_rules={"code": "anthropic", "math": "openai"},
        fallback_enabled=True,
    )

    # Router selects best provider for each task
    response = await connector.send_message(
        "Write a Python function to calculate fibonacci"
    )
    print(f"Provider used: {response['provider']}")
```

### Task Execution

```python
from nexus import NexusConnector

async def main():
    connector = NexusConnector(
        provider="anthropic",
        api_key="your-api-key",
        workspace="./my_project",
    )

    result = await connector.execute_task(
        "Create a REST API with Flask that has CRUD endpoints for users",
        show_progress=True,
        confirm_destructive=True,
    )

    print(f"Success: {result.success}")
    print(f"Files created: {result.files_created}")
    print(f"Iterations: {result.iterations}")
    print(f"Tokens used: {result.tokens_used}")
```

## Architecture

```
nexus/
├── core/
│   ├── unified_wrapper.py   # Main NexusConnector class
│   ├── tool_registry.py     # @tool decorator and registry
│   ├── tool_executor.py     # Tool execution engine
│   ├── execution_log.py     # Structured execution logging
│   ├── mcp_client.py        # MCP server integration
│   ├── router.py            # Smart routing and fallback
│   ├── retry.py             # Retry logic and circuit breaker
│   ├── rate_limiter.py      # Rate limiting
│   └── metrics.py           # Prometheus metrics and tracing
├── connectors/
│   ├── openai_connector.py
│   ├── anthropic_connector.py
│   ├── google_connector.py
│   ├── deepseek_connector.py
│   ├── xai_connector.py
│   └── ollama_connector.py
├── web/
│   ├── web_connector.py     # FastAPI integration
│   ├── session_store.py     # In-memory sessions
│   └── redis_store.py       # Distributed sessions
├── cli.py                   # CLI entry point
└── utils/
    ├── logger.py
    └── tokens.py            # Token counting
```

## Examples

The `examples/` directory contains comprehensive examples:

| Example | Description |
|---------|-------------|
| `simple_message.py` | Basic message sending |
| `multi_provider_example.py` | Compare providers |
| `custom_tools_example.py` | `@tool` decorator usage |
| `observable_execution_example.py` | Hooks and logging |
| `mcp_example.py` | MCP server integration |
| `smart_routing_example.py` | Routing and fallback |
| `production_hardening_example.py` | Retry, rate limiting, metrics |
| `task_execution.py` | Multi-step task execution |
| `web_server_example.py` | FastAPI deployment |

Run any example:
```bash
python examples/custom_tools_example.py
```

## API Reference

### NexusConnector

```python
connector = NexusConnector(
    # Provider configuration
    provider="openai",              # or AIProvider.OPENAI
    api_key="...",
    model="gpt-4o",

    # Workspace
    workspace="./project",

    # Execution settings
    max_iterations=10,
    auto_execute=True,
    safe_mode=True,
    verbose=False,

    # Custom tools
    tools=[my_tool1, my_tool2],

    # MCP servers
    mcp_servers=["filesystem", "github"],

    # Smart routing
    router="auto",                   # or Router instance
    routing_rules={"code": "anthropic"},
    fallback_enabled=True,
    max_fallback_attempts=3,

    # Observability hooks
    on_message=lambda msg: ...,
    on_tool_call=lambda tc: ...,
    on_tool_result=lambda tr: ...,
    on_step=lambda step, status: ...,
    on_error=lambda e: ...,
    on_provider_switch=lambda old, new, reason: ...,
)
```

### Methods

| Method | Description |
|--------|-------------|
| `send_message(msg)` | Send message and get response |
| `execute_task(task)` | Execute multi-step task |
| `register_tool(func)` | Register a custom tool |
| `register_tools([...])` | Register multiple tools |
| `get_tools()` | Get all registered tools |
| `add_mcp_server(name)` | Add MCP server |
| `remove_mcp_server(name)` | Remove MCP server |
| `get_mcp_status()` | Get MCP server status |
| `clear_history()` | Clear conversation |
| `close()` | Close all connections |

### TaskResult

```python
result = await connector.execute_task("...")

result.success          # bool
result.content          # str - AI responses
result.iterations       # int - loop iterations
result.tokens_used      # int - total tokens
result.duration         # float - seconds
result.cost             # float - estimated cost
result.files_created    # List[str]
result.files_modified   # List[str]
result.execution_log    # ExecutionLog object
```

## Roadmap

### ✅ Completed

- [x] Core unified interface (6 providers)
- [x] Plugin system (`@tool` decorator)
- [x] CLI tool (`nexus chat`, `nexus run`)
- [x] Observable execution (hooks, logs)
- [x] Human-in-the-loop confirmation
- [x] MCP server integration
- [x] Smart routing (7 strategies)
- [x] Automatic fallback
- [x] Retry with exponential backoff
- [x] Circuit breaker pattern
- [x] Rate limiting
- [x] Prometheus metrics
- [x] Distributed tracing
- [x] Redis session store
- [x] Web server with auth

### 🔮 Future

- [ ] Additional providers (Cohere, Mistral)
- [ ] Response caching
- [ ] Web UI dashboard
- [ ] Docker images
- [ ] Kubernetes manifests

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
# Development setup
git clone https://github.com/Clark-Wallace/The-Nexus-Connector.git
cd The-Nexus-Connector
pip install -e ".[dev]"
pre-commit install

# Run tests
pytest
pytest --cov=nexus
```

## License

MIT License - see [LICENSE](LICENSE)

## Support

- **Issues**: [GitHub Issues](https://github.com/Clark-Wallace/The-Nexus-Connector/issues)
- **Docs**: [examples/](./examples/)

---

<div align="center">

**Build AI agents, not API integrations.**

</div>
