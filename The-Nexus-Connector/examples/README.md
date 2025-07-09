# Nexus Examples

This directory contains example scripts demonstrating various features and use cases of the Nexus Unified AI Wrapper.

## Basic Examples

### 1. Simple Message (`simple_message.py`)
Basic example of sending a message to different AI providers.

```bash
python examples/simple_message.py
```

### 2. Provider Comparison (`compare_providers.py`)
Compare responses from multiple AI providers for the same prompt.

```bash
python examples/compare_providers.py
```

### 3. Streaming Response (`streaming_example.py`)
Demonstrate real-time streaming of AI responses.

```bash
python examples/streaming_example.py
```

## Advanced Examples

### 4. Task Execution (`task_execution.py`)
Execute complex multi-step tasks with automatic continuation.

```bash
python examples/task_execution.py
```

### 5. Code Generation (`code_generation.py`)
Generate complete applications with file creation and organization.

```bash
python examples/code_generation.py
```

### 6. Tool Usage (`tool_usage.py`)
Demonstrate custom tool definition and execution.

```bash
python examples/tool_usage.py
```

## Real-World Applications

### 7. Web Scraper (`web_scraper_builder.py`)
Build a complete web scraping application.

```bash
python examples/web_scraper_builder.py
```

### 8. API Client Generator (`api_client_generator.py`)
Generate API client libraries from specifications.

```bash
python examples/api_client_generator.py
```

### 9. Test Suite Creator (`test_suite_creator.py`)
Automatically generate comprehensive test suites.

```bash
python examples/test_suite_creator.py
```

### 10. Documentation Generator (`doc_generator.py`)
Generate project documentation from code.

```bash
python examples/doc_generator.py
```

## Configuration Examples

### 11. Custom Connector (`custom_connector.py`)
Implement a custom AI provider connector.

```bash
python examples/custom_connector.py
```

### 12. Middleware Usage (`middleware_example.py`)
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