# Nexus Examples

This directory contains example scripts demonstrating various features and use cases of the Nexus Unified AI Wrapper.

## Basic Examples

### 1. Simple Message (`simple_message.py`)
Basic example of sending a message to different AI providers.

```bash
python examples/simple_message.py
```

### 2. Provider Comparison (`multi_provider_example.py`)
Compare responses from multiple AI providers for the same prompt.

```bash
python examples/multi_provider_example.py
```

### 3. Ollama Local AI (`ollama_example.py`)
Run AI models locally with Ollama - no internet required.

```bash
python examples/ollama_example.py
```

### 4. Web Server Mode (`web_server_example.py`)
Deploy Nexus as a web service with FastAPI.

```bash
python examples/web_server_example.py
```

## Advanced Examples

### 5. Task Execution (`task_execution.py`)
Execute complex multi-step tasks with automatic continuation.

```bash
python examples/task_execution.py
```

### 6. Custom Tools (`custom_tools_example.py`) ✨ NEW
Create custom tools using the `@tool` decorator and register them with NexusConnector.

```bash
python examples/custom_tools_example.py
```

Features demonstrated:
- `@tool` decorator for creating custom tools
- Async and sync tool support
- Tool categories and metadata
- Observability hooks (`on_tool_call`, `on_tool_result`)

### 7. Observable Execution (`observable_execution_example.py`)
Full visibility into task execution with hooks, logging, and human-in-the-loop.

```bash
python examples/observable_execution_example.py
```

Features demonstrated:
- Execution hooks for real-time monitoring
- ExecutionLog for detailed tracking
- Human-in-the-loop confirmation
- Checkpoint and rollback support

### 8. MCP Server Integration (`mcp_example.py`) ✨ NEW
Connect to MCP (Model Context Protocol) servers to give your AI agent access to external tools.

```bash
python examples/mcp_example.py
```

Features demonstrated:
- Connect to well-known MCP servers (filesystem, github, memory, etc.)
- Dynamically add/remove MCP servers
- Use MCP tools alongside custom `@tool` functions
- Configure custom MCP servers

Supported MCP servers:
- `filesystem` - Read/write files, list directories
- `github` - Search repos, create issues, make PRs
- `postgres` / `sqlite` - Database queries
- `memory` - Key-value storage
- `fetch` - HTTP requests
- `time` - Time/timezone operations
- `brave-search` - Web search
- `puppeteer` - Browser automation
- `slack` - Slack messaging

### 9. Smart Routing (`smart_routing_example.py`) ✨ NEW
Intelligent provider selection with automatic fallback.

```bash
python examples/smart_routing_example.py
```

Features demonstrated:
- Auto-routing from environment variables (`router="auto"`)
- Task-based routing (code → Claude, math → GPT-4)
- Routing strategies: cost, quality, latency, adaptive
- Automatic fallback when providers fail
- Provider statistics and monitoring

Routing strategies:
- `cost` - Cheapest provider (DeepSeek, Ollama)
- `quality` - Best for task type
- `latency` - Fastest based on history
- `fallback` - Priority order with retry
- `adaptive` - Balances all factors

### 10. Production Hardening (`production_hardening_example.py`) ✨ NEW
Enterprise-ready reliability features for production deployments.

```bash
python examples/production_hardening_example.py
```

Features demonstrated:
- Retry with exponential backoff and jitter
- Circuit breaker pattern
- Rate limiting (requests + tokens)
- Prometheus metrics collection
- Distributed tracing
- Redis distributed sessions

Pre-configured retry strategies:
- `aggressive` - 5 retries, fast recovery
- `standard` - 3 retries, balanced
- `conservative` - 2 retries, cautious
- `rate_limit` - 5 retries, long delays for rate limits

## CLI Development Tools

### 🚀 QwenDevr - The Ultimate Qwen CLI
**Moved to dedicated folder: [`/QwenDevr/`](../QwenDevr/)**

**Claude Code-inspired development assistant powered by Qwen3-235B (FREE!) via OpenRouter**

✨ **NEW: Now uses FREE Qwen3-235B model with 235B parameters!**

QwenDevr has been moved to its own dedicated folder with complete setup:

```bash
# Navigate to QwenDevr
cd QwenDevr/

# Run setup script
./setup.sh

# Or install manually
pip install -r qwen_devr_requirements.txt
export OPENROUTER_API_KEY="your-key-here"

# Start using QwenDevr (now defaults to FREE Qwen3-235B!)
python qwen_devr_cli.py --interactive
python qwen.py --interactive        # Short launcher
python qwen_devr_demo.py            # Demo (no API key needed)
```

**Key Features:**
- 🆓 **Completely FREE** - Qwen3-235B is free on OpenRouter
- 🚀 **235B Parameters** - 3x larger than previous generation
- 🎯 **Claude Code-like Interface** - Familiar development commands
- 🔄 **Model Switching** - Switch between qwen3-235b, qwen2.5-72b, qwen2.5-coder
- 📁 **Project Management** - Create web, api, cli, lib, data, game, mobile projects

**See [`QwenDevr/README.md`](../QwenDevr/README.md) for complete documentation.**

## Development Examples

### 6. Code Generation (`code_generation.py`)
Generate complete applications with file creation and organization.

```bash
python examples/code_generation.py
```

### 7. Tool Usage (`tool_usage.py`)
Demonstrate custom tool definition and execution.

```bash
python examples/tool_usage.py
```

## Real-World Applications

### 8. Web Scraper (`web_scraper_builder.py`)
Build a complete web scraping application.

```bash
python examples/web_scraper_builder.py
```

### 9. API Client Generator (`api_client_generator.py`)
Generate API client libraries from specifications.

```bash
python examples/api_client_generator.py
```

### 10. Test Suite Creator (`test_suite_creator.py`)
Automatically generate comprehensive test suites.

```bash
python examples/test_suite_creator.py
```

### 11. Documentation Generator (`doc_generator.py`)
Generate project documentation from code.

```bash
python examples/doc_generator.py
```

## Configuration Examples

### 12. Custom Connector (`custom_connector.py`)
Implement a custom AI provider connector.

```bash
python examples/custom_connector.py
```

### 13. Middleware Usage (`middleware_example.py`)
Add custom processing to requests and responses.

```bash
python examples/middleware_example.py
```

## Running the Examples

1. **Set up environment variables:**
   ```bash
   export OPENAI_API_KEY="your-key"
   export ANTHROPIC_API_KEY="your-key"
   export GOOGLE_API_KEY="your-key"
   export XAI_API_KEY="your-key"
   export DEEPSEEK_API_KEY="your-key"
   export OPENROUTER_API_KEY="your-key"  # For QwenDevr
   ```

2. **Install Nexus:**
   ```bash
   pip install -e .
   ```

3. **Run any example:**
   ```bash
   python examples/<example_name>.py
   ```

## Creating Your Own Examples

When creating new examples:

1. Import necessary modules
2. Load API keys from environment
3. Create UnifiedAIWrapper instance
4. Demonstrate specific features
5. Include error handling
6. Add helpful comments

Example template:

```python
#!/usr/bin/env python3
"""
Example: [Brief description]

This example demonstrates [what it does].
"""

import asyncio
import os
from nexus import UnifiedAIWrapper, AIProvider


async def main():
    # Load API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create wrapper
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.OPENAI,
        api_key=api_key
    )
    
    # Your example code here
    response = await wrapper.send_message("Hello, world!")
    print(response["content"])


if __name__ == "__main__":
    asyncio.run(main())
```

## Contributing Examples

We welcome new examples! Please:

1. Follow the template structure
2. Include clear documentation
3. Handle errors gracefully
4. Test with multiple providers when applicable
5. Submit a pull request

## Support

If you have questions about the examples:

- Check the [main documentation](../README.md)
- Open an [issue](https://github.com/yourusername/nexus-unified-wrapper/issues)
- Join our [Discord community](https://discord.gg/nexus-ai)