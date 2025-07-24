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

## CLI Development Tools

### 🚀 QwenDevr - The Ultimate Qwen CLI (`qwen_devr_cli.py`)
**Claude Code-inspired development assistant powered by Qwen2.5-72B-Instruct via OpenRouter**

A comprehensive CLI tool that provides:
- 🎯 **Claude Code-like Interface** - Familiar commands for development tasks
- ⚡ **Fast & Efficient** - No thinking tokens, direct responses from Qwen2.5  
- 🛠️ **Complete Toolkit** - Project setup, code analysis, testing, docs, refactoring
- 💬 **Interactive Mode** - Chat-like interface for development assistance
- 📁 **Project Management** - Create and manage different project types

```bash
# Setup and demo
pip install rich click typer prompt-toolkit
export OPENROUTER_API_KEY="your-key-here"

# Interactive mode (recommended)
python examples/qwen_devr_cli.py --interactive

# Quick commands
python examples/qwen_devr_cli.py "analyze this codebase"
python examples/qwen_devr_cli.py --setup web my_app
python examples/qwen_devr_cli.py --file main.py "add error handling"

# Demo (no API key needed)
python examples/qwen_devr_demo.py
```

**Available Commands:**
- `analyze [focus]` - Analyze project/codebase with optional focus area
- `setup <type> [name]` - Create new projects (web, api, cli, lib, data, game, mobile)
- `fix <file> [issues]` - Fix issues in specific files
- `test <file>` - Generate comprehensive test suites
- `docs [scope]` - Generate documentation
- `refactor <file> <requirements>` - Refactor code with specific requirements

**Project Types:** web, api, cli, lib, data, game, mobile

**Why Qwen2.5-72B?** Fast, no thinking tokens (unlike DeepSeek), excellent code quality, cost-effective via OpenRouter.

See `qwen_devr_setup.md` for complete setup guide and examples.

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