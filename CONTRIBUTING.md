# Contributing to Nexus

First off, thank you for considering contributing to Nexus! It's people like you that make Nexus such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

- **Use a clear and descriptive title**
- **Describe the exact steps to reproduce the problem**
- **Provide specific examples**
- **Include your environment details** (OS, Python version, etc.)
- **Attach relevant logs or error messages**

### Suggesting Enhancements

Enhancement suggestions are welcome! Please provide:

- **Use a clear and descriptive title**
- **Provide a detailed description of the proposed enhancement**
- **Explain why this enhancement would be useful**
- **List any alternative solutions you've considered**

### Pull Requests

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code follows the project's style guidelines
6. Issue that pull request!

## Development Setup

```bash
# Clone your fork
git clone https://github.com/your-username/nexus-unified-wrapper.git
cd nexus-unified-wrapper

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

## Style Guidelines

### Python Style

We follow PEP 8 with a few exceptions:
- Line length: 100 characters
- Use type hints for all function parameters and return values
- Use docstrings for all public functions and classes

### Code Format

```python
from typing import Optional, List

class ExampleClass:
    """Brief description of the class.
    
    Longer description if needed.
    
    Args:
        param1: Description of param1
        param2: Description of param2
    """
    
    def __init__(self, param1: str, param2: Optional[int] = None):
        self.param1 = param1
        self.param2 = param2
    
    async def example_method(self, items: List[str]) -> bool:
        """Brief description of the method.
        
        Args:
            items: List of items to process
            
        Returns:
            True if successful, False otherwise
        """
        # Implementation here
        return True
```

### Commit Messages

- Use the present tense ("Add feature" not "Added feature")
- Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit the first line to 72 characters or less
- Reference issues and pull requests liberally after the first line

Example:
```
Add support for Cohere AI provider

- Implement CohereConnector class
- Add unit tests for Cohere integration
- Update documentation with Cohere examples

Fixes #123
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=nexus

# Run specific test file
pytest tests/test_openai_connector.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Write tests for all new functionality
- Aim for at least 80% code coverage
- Use descriptive test names
- Mock external API calls

Example test:
```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_send_message_success():
    """Test successful message sending."""
    # Arrange
    mock_response = {"content": "Test response"}
    
    with patch('nexus.connectors.openai_connector.AsyncOpenAI') as mock_client:
        connector = OpenAIConnector("test-key")
        mock_client.return_value.chat.completions.create = AsyncMock(
            return_value=mock_response
        )
        
        # Act
        result = await connector.send_message([{"role": "user", "content": "Test"}])
        
        # Assert
        assert result.content == "Test response"
```

## Adding a New AI Provider

To add support for a new AI provider:

1. **Create the Connector**
   ```python
   # nexus/connectors/newprovider_connector.py
   from ..core.base_connector import BaseConnector
   
   class NewProviderConnector(BaseConnector):
       # Implementation
   ```

2. **Add to Provider Enum**
   ```python
   # nexus/core/base_connector.py
   class AIProvider(Enum):
       NEWPROVIDER = "newprovider"
   ```

3. **Update Factory Method**
   ```python
   # nexus/core/unified_wrapper.py
   elif provider == AIProvider.NEWPROVIDER:
       from ..connectors.newprovider_connector import NewProviderConnector
       return NewProviderConnector(api_key, model, **kwargs)
   ```

4. **Add Tests**
   ```python
   # tests/test_newprovider_connector.py
   # Comprehensive tests for the new connector
   ```

5. **Update Documentation**
   - Add to supported providers table in README
   - Add usage examples
   - Update API reference

## Documentation

- Use clear, concise language
- Include code examples for all features
- Keep the README focused on getting started
- Put detailed documentation in the `/docs` directory

## Community

- Join our [Discord server](https://discord.gg/nexus-ai)
- Follow our [Twitter](https://twitter.com/nexus_ai)
- Check out our [blog](https://nexus-ai.dev/blog)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.