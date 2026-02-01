# The Nexus Connector

<div align="center">

![Nexus Logo](https://img.shields.io/badge/Nexus-Connector-blue)
[![Python](https://img.shields.io/badge/Python-3.8+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg)]()

**🚀 Transform any AI API into an autonomous agent that gets things done**

[What It Does](#what-it-does) • [Features](#features) • [Quick Start](#quick-start) • [Examples](#examples) • [Documentation](#documentation)

</div>

---

## What It Does

**Stop writing API wrappers. Start building agents.**

The Nexus Connector turns AI APIs into autonomous tools that can:

- 🤖 **Build entire applications** — "Create a Flask API with user auth and tests"
- 📁 **Manage your codebase** — Read, write, refactor, and organize files
- 🔄 **Execute multi-step tasks** — Keep working until the job is done
- 🛡️ **Self-correct errors** — Hit an error? It fixes it and continues
- 🔌 **Use any tool you give it** — Databases, APIs, Slack, GitHub, anything
- 💾 **Remember everything** — Persistent sessions across requests and restarts

```python
# This isn't a chatbot. This is an autonomous agent.
result = await connector.execute_task(
    "Create a REST API with user authentication, write tests, and set up the database"
)

print(f"✅ Created {len(result.files_created)} files")
print(f"🔧 Made {result.iterations} tool calls")
print(f"💰 Cost: ${result.cost:.4f}")
```

### Why Nexus?

| Problem | Nexus Solution |
|---------|----------------|
| 🔒 Locked into one AI provider | **6 providers, same code** — switch with one line |
| 📝 Managing conversation state | **Automatic session management** — it just works |
| 🛠️ Building tool integrations | **`@tool` decorator** — 3 lines to add any capability |
| 💥 API failures kill your workflow | **Auto-fallback** — seamlessly switch providers on error |
| 🔍 No idea what the AI is doing | **Full observability** — hooks into every action |
| 🏭 Not ready for production | **Circuit breakers, rate limits, metrics** — enterprise-ready |

---

## 🎯 Real Examples

### Build a Complete Project

```python
result = await connector.execute_task("""
    Create a blog application with:
    - SQLite database with posts and comments
    - Flask REST API with CRUD endpoints
    - Input validation and error handling
    - Unit tests for all endpoints
    - README with setup instructions
""")
# ✅ 12 files created, 47 tool calls, $0.08 cost
```

### Refactor with Confidence

```python
result = await connector.execute_task(
    "Refactor the auth module to use JWT tokens instead of sessions",
    checkpoint=True,        # Git commit before changes
    rollback_on_fail=True,  # Revert if something breaks
    confirm_destructive=True,  # Ask before deleting files
)
```

### Add Custom Capabilities

```python
from nexus import NexusConnector, tool

@tool(description="Query our production database")
async def query_db(sql: str) -> str:
    return await database.execute(sql)

@tool(description="Send alert to Slack")
async def alert_slack(message: str) -> str:
    return await slack.post("#alerts", message)

@tool(description="Deploy to production", destructive=True)
async def deploy(version: str) -> str:
    return await k8s.deploy(version)

connector = NexusConnector(
    provider="anthropic",
    tools=[query_db, alert_slack, deploy],
)

# Now the AI can query your database, alert your team, and deploy code
await connector.execute_task(
    "Check if error rates are above 1%, if so alert the team and rollback to v2.3.1"
)
```

### Smart Provider Routing

```python
connector = NexusConnector(
    router="auto",
    routing_rules={
        "code": "anthropic",     # Claude for coding tasks
        "math": "openai",        # GPT-4 for math/logic
        "creative": "anthropic", # Claude for writing
        "bulk": "deepseek",      # DeepSeek for cost-sensitive work
        "private": "ollama",     # Local model for sensitive data
    },
    fallback_enabled=True,  # If one fails, try the next
)

# Nexus picks the right provider for each task automatically
```

---

## Features

### 🔌 Supported Providers

| Provider | Models | Tool Calling | Streaming | Local |
|----------|--------|:------------:|:---------:|:-----:|
| **OpenAI** | GPT-4o, GPT-4, GPT-3.5 | ✅ | ✅ | ❌ |
| **Anthropic** | Claude 3.5 Opus/Sonnet/Haiku | ✅ | ✅ | ❌ |
| **Google** | Gemini 2.0, 1.5 Pro/Flash | ✅ | ✅ | ❌ |
| **xAI** | Grok-3, Grok-2 | ✅ | ✅ | ❌ |
| **DeepSeek** | DeepSeek-V3, Coder | ✅ | ✅ | ❌ |
| **Ollama** | Llama, Mistral, CodeLlama, any | ✅ | ✅ | ✅ |

### 🛠️ Plugin System

Turn any function into an AI-callable tool:

```python
from nexus import tool

@tool(description="Search our documentation")
async def search_docs(query: str, max_results: int = 5) -> str:
    results = await doc_search.search(query, limit=max_results)
    return format_results(results)

@tool(description="Create a GitHub issue", category="github")
async def create_issue(title: str, body: str, labels: list = None) -> str:
    return await github.create_issue(title, body, labels)

@tool(description="Send email to customer", destructive=True)
async def send_email(to: str, subject: str, body: str) -> str:
    return await email.send(to, subject, body)
```

The `destructive=True` flag enables human-in-the-loop confirmation before execution.

### 🔍 Observable Execution

See exactly what your agent is doing:

```python
connector = NexusConnector(
    provider="anthropic",
    on_tool_call=lambda tc: print(f"🔧 Calling: {tc['name']}({tc['args']})"),
    on_tool_result=lambda tr: print(f"✅ Result: {tr['result'][:100]}..."),
    on_step=lambda step, status: print(f"📍 Step {step}: {status}"),
    on_error=lambda e: print(f"❌ Error: {e}"),
    on_provider_switch=lambda old, new, reason: print(f"🔄 {old} → {new}: {reason}"),
)

result = await connector.execute_task(
    "Analyze the codebase and create documentation",
    log_path="execution_log.json",  # Save detailed execution log
)

# Access metrics after execution
metrics = result.execution_log.get_metrics()
print(f"Tool calls: {metrics['tool_calls']}")
print(f"Tokens: {metrics['total_tokens']}")
print(f"Duration: {metrics['duration_seconds']}s")
```

### 🛡️ Human-in-the-Loop

Stay in control of dangerous operations:

```python
def confirm(tool_meta):
    print(f"⚠️  Agent wants to: {tool_meta.name}")
    print(f"   Arguments: {tool_meta.args}")
    return input("Allow? [y/N]: ").lower() == 'y'

result = await connector.execute_task(
    "Clean up the database and remove old user accounts",
    confirm_destructive=True,  # Pause before delete operations
    confirm_callback=confirm,
)
```

### 🔗 MCP Server Integration

Connect to [Model Context Protocol](https://modelcontextprotocol.io/) servers:

```python
connector = NexusConnector(
    provider="openai",
    mcp_servers=["filesystem", "github", "postgres", "slack"],
)

# MCP tools are automatically available to the AI
print(connector.get_mcp_tools())
# ['mcp_filesystem_read_file', 'mcp_github_create_pr', 'mcp_postgres_query', ...]

# Add servers dynamically
await connector.add_mcp_server("memory")
await connector.add_mcp_server("custom", config={
    "command": "python",
    "args": ["-m", "my_custom_mcp_server"],
})
```

**Supported MCP servers:** `filesystem`, `github`, `postgres`, `sqlite`, `memory`, `fetch`, `time`, `brave-search`, `puppeteer`, `slack`

### 💾 Persistent Sessions

Conversation context survives across requests, restarts, and even server instances:

```python
# In-memory sessions (single instance)
from nexus.web import SessionStore
store = SessionStore(timeout_hours=24)  # Auto-cleanup after 24h

# Get or create a session - context is preserved
wrapper = await store.get_or_create(
    session_id="user_123",
    factory=lambda: NexusConnector(provider="anthropic")
)

# Conversation history is maintained automatically
await wrapper.send_message("My name is Alice")
# ... hours later, same session ...
await wrapper.send_message("What's my name?")  # "Your name is Alice"

# Redis sessions (distributed, multi-instance)
from nexus.web import RedisSessionStore
store = RedisSessionStore(
    redis_url="redis://localhost:6379",
    prefix="nexus:session:",
    default_ttl=86400,  # 24 hours
)

# Works across multiple server instances
async with store:
    session = await store.create_session(
        session_id="user_123",
        provider="anthropic",
        user_id="alice",
    )
    await store.add_message(session.session_id, {
        "role": "user",
        "content": "Remember this for later"
    })
```

**Session features:**
- 🔄 Automatic conversation history tracking
- ⏰ Configurable TTL with auto-cleanup
- 🔒 Session locking for concurrent access
- 📊 Usage stats and session metrics
- 🌐 Redis pub/sub for real-time sync

### 🚀 Smart Routing & Fallback

Never let a provider outage stop your workflow:

```python
connector = NexusConnector(
    router="adaptive",  # Learns which provider works best
    fallback_enabled=True,
    max_fallback_attempts=3,
)

# Routing strategies:
# - "cost"     → Cheapest provider (DeepSeek, Ollama)
# - "quality"  → Best for the task type
# - "latency"  → Fastest based on recent history
# - "fallback" → Try providers in priority order
# - "adaptive" → Balances cost, quality, and reliability
```

### 🏭 Production Hardening

Enterprise-ready reliability out of the box:

```python
from nexus import (
    RETRY_CONFIGS,      # Pre-configured retry strategies
    CircuitBreaker,     # Prevent cascade failures
    get_rate_limiter,   # Token bucket rate limiting
    get_metrics,        # Prometheus metrics
    get_tracer,         # Distributed tracing
)
from nexus.web import RedisSessionStore  # Distributed sessions

# Exponential backoff with jitter
handler = RetryHandler(config=RETRY_CONFIGS["standard"])
# Options: "aggressive", "standard", "conservative", "rate_limit"

# Circuit breaker prevents hammering a dead service
cb = CircuitBreaker("openai", failure_threshold=5, timeout=30.0)

# Rate limiting per provider
limiter = get_rate_limiter("openai")
await limiter.acquire_request(timeout=30)

# Prometheus metrics for monitoring
metrics = get_metrics()
print(metrics.get_prometheus_metrics())

# Redis sessions for horizontal scaling
store = RedisSessionStore(redis_url="redis://localhost:6379")
```

---

## Quick Start

### Installation

```bash
git clone https://github.com/Clark-Wallace/The-Nexus-Connector.git
cd The-Nexus-Connector
pip install -e .
```

### Environment Variables

```bash
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="..."
export XAI_API_KEY="..."
export DEEPSEEK_API_KEY="..."
```

### Your First Agent

```python
import asyncio
from nexus import NexusConnector

async def main():
    connector = NexusConnector(
        provider="anthropic",
        api_key="your-api-key",
        workspace="./my_project",  # Where to create files
    )

    # Simple message
    response = await connector.send_message("What can you help me build?")
    print(response["content"])

    # Autonomous task execution
    result = await connector.execute_task(
        "Create a Python CLI tool that converts CSV files to JSON",
        show_progress=True,
    )

    print(f"✅ Success: {result.success}")
    print(f"📁 Files: {result.files_created}")

asyncio.run(main())
```

---

## CLI

Nexus includes a powerful command-line interface:

```bash
# Interactive chat with any provider
nexus chat --provider anthropic
nexus chat --provider openai --model gpt-4o

# Execute a task and get results
nexus run "Create a Python script that monitors CPU usage" --provider anthropic

# Compare providers side-by-side
nexus compare "Explain quantum computing" --providers openai,anthropic,deepseek

# Start a web server
nexus serve --port 8000

# List available providers and tools
nexus providers
nexus tools
```

### Chat Commands

```
/help     Show available commands
/clear    Clear conversation history
/save     Save conversation to file
/switch   Switch to different provider
/model    Change the model
/system   Set system prompt
/tokens   Show token usage
```

---

## Examples

The `examples/` directory has everything you need:

| Example | What It Shows |
|---------|---------------|
| `simple_message.py` | Basic message sending |
| `task_execution.py` | Multi-step autonomous tasks |
| `custom_tools_example.py` | Creating tools with `@tool` |
| `observable_execution_example.py` | Hooks and execution logging |
| `mcp_example.py` | MCP server integration |
| `smart_routing_example.py` | Provider routing and fallback |
| `production_hardening_example.py` | Retry, rate limiting, metrics |
| `multi_provider_example.py` | Comparing providers |
| `web_server_example.py` | FastAPI deployment |

```bash
# Run any example
python examples/task_execution.py
python examples/custom_tools_example.py
```

---

## Architecture

```
nexus/
├── core/
│   ├── unified_wrapper.py   # 🎯 Main NexusConnector class
│   ├── tool_registry.py     # 🔧 @tool decorator and registry
│   ├── tool_executor.py     # ⚡ Tool execution engine
│   ├── execution_log.py     # 📊 Structured logging
│   ├── mcp_client.py        # 🔗 MCP server integration
│   ├── router.py            # 🧭 Smart routing and fallback
│   ├── retry.py             # 🔄 Retry and circuit breaker
│   ├── rate_limiter.py      # 🚦 Rate limiting
│   └── metrics.py           # 📈 Prometheus metrics
├── connectors/              # Provider implementations
│   ├── openai_connector.py
│   ├── anthropic_connector.py
│   ├── google_connector.py
│   ├── deepseek_connector.py
│   ├── xai_connector.py
│   └── ollama_connector.py
├── web/                     # Web server components
│   ├── web_connector.py     # FastAPI integration
│   ├── session_store.py     # In-memory sessions
│   └── redis_store.py       # Distributed sessions
└── cli.py                   # CLI entry point
```

---

## API Reference

### NexusConnector

```python
connector = NexusConnector(
    # Provider
    provider="anthropic",           # or "openai", "google", "deepseek", "xai", "ollama"
    api_key="...",
    model="claude-sonnet-4-20250514",

    # Workspace for file operations
    workspace="./project",

    # Execution behavior
    max_iterations=10,              # Max tool-use loops
    auto_execute=True,              # Auto-run tool calls
    safe_mode=True,                 # Restrict dangerous operations

    # Custom tools
    tools=[my_func1, my_func2],     # Functions with @tool decorator

    # MCP servers
    mcp_servers=["filesystem", "github"],

    # Smart routing
    router="auto",                  # or "cost", "quality", "latency", "adaptive"
    routing_rules={"code": "anthropic", "math": "openai"},
    fallback_enabled=True,

    # Observability hooks
    on_tool_call=lambda tc: ...,
    on_tool_result=lambda tr: ...,
    on_step=lambda step, status: ...,
    on_error=lambda e: ...,
    on_provider_switch=lambda old, new, reason: ...,
)
```

### Key Methods

| Method | Description |
|--------|-------------|
| `send_message(msg)` | Send a message, get a response |
| `execute_task(task)` | Run autonomous multi-step task |
| `register_tool(func)` | Add a custom tool |
| `add_mcp_server(name)` | Connect to MCP server |
| `clear_history()` | Reset conversation |
| `close()` | Clean up connections |

### TaskResult

```python
result = await connector.execute_task("Build a web scraper")

result.success          # bool - Did it complete successfully?
result.content          # str - Final AI response
result.iterations       # int - How many tool-use loops
result.tokens_used      # int - Total tokens consumed
result.cost             # float - Estimated cost in USD
result.files_created    # List[str] - New files made
result.files_modified   # List[str] - Existing files changed
result.execution_log    # ExecutionLog - Detailed execution data
```

---

## Roadmap

### ✅ Shipped

- [x] **6 AI providers** — OpenAI, Anthropic, Google, xAI, DeepSeek, Ollama
- [x] **Plugin system** — `@tool` decorator for custom capabilities
- [x] **CLI tool** — `nexus chat`, `nexus run`, `nexus compare`
- [x] **Observable execution** — Hooks, logs, metrics for everything
- [x] **Human-in-the-loop** — Confirm before destructive operations
- [x] **MCP integration** — Connect to any MCP tool server
- [x] **Smart routing** — 7 strategies, automatic fallback
- [x] **Production hardening** — Retry, circuit breaker, rate limiting
- [x] **Distributed sessions** — Redis session store
- [x] **Prometheus metrics** — Full observability stack
- [x] **Web server** — FastAPI with auth middleware

### 🔮 Coming Soon

- [ ] More providers (Cohere, Mistral, AWS Bedrock)
- [ ] Response caching layer
- [ ] Web UI dashboard
- [ ] Docker images
- [ ] Kubernetes manifests
- [ ] VS Code extension

---

## Contributing

We'd love your help! See [CONTRIBUTING.md](CONTRIBUTING.md).

```bash
git clone https://github.com/Clark-Wallace/The-Nexus-Connector.git
cd The-Nexus-Connector
pip install -e ".[dev]"
pre-commit install
pytest
```

---

## License

MIT License — see [LICENSE](LICENSE)

---

<div align="center">

### 🚀 Stop writing API wrappers. Start building agents.

**[Get Started](#quick-start)** • **[Examples](./examples/)** • **[Report Issue](https://github.com/Clark-Wallace/The-Nexus-Connector/issues)**

</div>
