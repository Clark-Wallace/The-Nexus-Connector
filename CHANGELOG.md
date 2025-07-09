# Changelog

All notable changes to The Nexus Connector will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-01-05

### Added

#### Core Features
- Unified interface for 5 major AI providers (OpenAI, Anthropic, Google, xAI, DeepSeek)
- Iterative task execution pattern based on GPT-4o's proven approach
- Automatic tool/function calling with unified format
- Text-based operation extraction for providers without native tool support
- Streaming response support for real-time output
- Comprehensive error handling and logging
- Token counting and cost estimation
- Conversation history management

#### Providers
- **OpenAI Connector**: Full support for GPT-4o, GPT-4, and GPT-3.5 models
- **Anthropic Connector**: Support for Claude 3 (Opus, Sonnet, Haiku) with proper message formatting
- **Google Connector**: Gemini 2.0 and 1.5 support with text-based tool extraction
- **xAI Connector**: Grok-3 and Grok-2 support via OpenAI-compatible API
- **DeepSeek Connector**: DeepSeek-V3 and Coder models with competitive pricing

#### Architecture
- Strategy pattern for provider implementations
- Factory pattern for connector creation
- Adapter pattern for API normalization
- Extensible plugin architecture
- Type-safe implementation with Python type hints

#### Tools & Utilities
- File creation and editing
- Command execution with safety checks
- Workspace isolation
- Text-based code extraction engine
- Automatic operation application

#### Documentation
- Comprehensive README with quick start guide
- Detailed API reference
- Architecture documentation
- Contributing guidelines
- Example scripts for common use cases

#### Testing
- Unit test framework
- Integration tests for each provider
- Mock-based testing for API calls
- Coverage reporting setup

#### Development
- Pre-commit hooks configuration
- Black and isort for code formatting
- MyPy for type checking
- Ruff for linting
- GitHub Actions CI/CD ready

### Security
- API key management best practices
- Workspace isolation to prevent directory traversal
- Command execution safety with whitelisting
- No logging of sensitive information

### Performance
- Asynchronous operations throughout
- Connection pooling where available
- Efficient streaming for large responses
- Minimal overhead unified interface

## [0.2.0] - 2024-01-09

### Added

#### Major Features
- **Native Web Server Mode**: Built-in FastAPI server for web applications
  - RESTful endpoints for chat interactions
  - Server-Sent Events (SSE) for streaming
  - Session management with automatic cleanup
  - CORS support for frontend integration
  - Health check and monitoring endpoints

- **Ollama Connector**: Support for local LLM inference
  - Run models locally without API keys
  - Support for Llama 2, Mistral, CodeLlama, and more
  - Automatic model detection
  - Privacy-first AI interactions

- **Game Master Connector**: Specialized connector for RPG applications
  - Structured request/response models for game interactions
  - Prompt building for narrative context
  - Fallback handling for parse errors
  - Campaign management endpoints

#### Improvements
- Added `WebConnector` base class for easy web service creation
- Implemented `SessionStore` for managing stateful conversations
- Enhanced type safety with Pydantic models throughout
- Improved error handling with graceful fallbacks
- Added comprehensive examples for all major features

#### Developer Experience
- Better organized test structure (unit/integration/fixtures)
- GitHub Actions CI/CD pipeline
- Pre-commit hooks for code quality
- Updated documentation with web server usage
- Version management with `_version.py`

### Changed
- Updated version to 0.2.0
- Enhanced requirements.txt with optional web dependencies
- Improved pyproject.toml with new keywords and classifiers

### Fixed
- Removed duplicate CONTRIBUTING files
- Cleaned up test file organization
- Fixed import issues in examples

## [Unreleased]

### Planned
- WebSocket support for real-time communication
- Redis-backed session store for production
- Additional providers (Cohere, AI21, Replicate)
- Response caching layer
- Rate limiting and automatic retry
- GraphQL interface option
- Batch processing support
- Multi-modal support (images, audio)

### Under Consideration
- GraphQL API interface
- REST API server mode
- Kubernetes operator
- Terraform provider
- SDK for other languages (Go, Rust, TypeScript)

---

## Migration Guide

### From Individual CLI Wrappers to Nexus

If you're currently using individual CLI wrappers (anthropic-agent-cli, openai-agent-cli, etc.), migrating to Nexus is straightforward:

1. **Install Nexus**:
   ```bash
   pip install nexus-ai-wrapper
   ```

2. **Update imports**:
   ```python
   # Old
   from openai_agent_cli import OpenAIAgent
   
   # New
   from nexus import UnifiedAIWrapper, AIProvider
   ```

3. **Update initialization**:
   ```python
   # Old
   agent = OpenAIAgent(api_key="...")
   
   # New
   wrapper = UnifiedAIWrapper(
       provider=AIProvider.OPENAI,
       api_key="..."
   )
   ```

4. **Update method calls**:
   ```python
   # Old
   response = agent.complete(prompt)
   
   # New
   response = await wrapper.send_message(prompt)
   ```

### Benefits of Migration

- Single interface for all providers
- Easy provider switching
- Advanced task execution
- Better error handling
- Unified tool format
- Active development and support