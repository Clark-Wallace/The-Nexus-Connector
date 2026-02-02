# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Architecture:** @.agent-os/product/tech-stack.md
- **Development Roadmap:** @.agent-os/product/roadmap.md
- **Decision History:** @.agent-os/product/decisions.md

### Development Standards
- **Code Style:** @~/.agent-os/standards/code-style.md
- **Best Practices:** @~/.agent-os/standards/best-practices.md

### Project Management
- **Active Specs:** @.agent-os/specs/
- **Spec Planning:** Use `@~/.agent-os/instructions/create-spec.md`
- **Tasks Execution:** Use `@~/.agent-os/instructions/execute-tasks.md`

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @.agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: @~/.agent-os/instructions/create-spec.md
   - For tasks execution: @~/.agent-os/instructions/execute-tasks.md
3. **Always**, adhere to the standards in the files listed above

## Important Notes

- Product-specific files in `.agent-os/product/` override any global standards
- User's specific instructions override (or amend) instructions found in `.agent-os/specs/...`
- Always adhere to established patterns, code style, and best practices documented above.

## Key Commands

### Development
```bash
# Install in development mode
pip install -e .

# Run tests
pytest                    # Run all tests
pytest tests/unit        # Run unit tests only
pytest tests/integration # Run integration tests
pytest -m "not slow"     # Skip slow tests
pytest --cov=nexus       # Run with coverage
pytest tests/integration/test_nexus.py::test_execute_task  # Run specific test

# Code quality checks
black nexus tests        # Format code
isort nexus tests        # Sort imports
mypy nexus              # Type check
ruff nexus              # Lint code

# Build distribution
python -m build
```

### Running the application
```bash
# CLI command (defined in pyproject.toml)
nexus

# Start web server programmatically
python -c "from nexus.web import WebConnector; import asyncio; asyncio.run(WebConnector(...).start_server())"
```

## Architecture Overview

The Nexus Connector provides a unified interface for multiple AI providers, transforming APIs into autonomous CLI tools with persistent state.

### Core Design Principles
1. **Provider Abstraction**: Each AI provider (OpenAI, Anthropic, Google, xAI, DeepSeek, Ollama) implements `BaseConnector`
2. **Unified Interface**: `UnifiedAIWrapper`/`NexusConnector` provides consistent API across all providers
3. **Async-First**: All operations use async/await for concurrent execution
4. **Tool Execution**: Native tool/function calling with automatic execution
5. **Session Management**: Persistent sessions with automatic cleanup for web apps

### Key Components

**nexus/core/**
- `base_connector.py`: Abstract base class defining the provider interface
- `unified_wrapper.py`: Main entry point, handles provider routing and task execution
- `tool_executor.py`: Executes tool/function calls from AI responses
- `text_apply_engine.py`: Fallback for providers without native tool support

**nexus/connectors/**
- Provider-specific implementations mapping APIs to unified interface
- Each connector handles authentication, message formatting, streaming, and tool calls
- Special connectors: `gm_connector.py` for RPG game management

**nexus/web/**
- `web_connector.py`: FastAPI integration for HTTP API
- `websocket_manager.py`: WebSocket support for real-time streaming
- `session_store.py`: Redis-like session persistence

**apps/**
- `methinks/`: AI-powered project specification generator (standalone app)
- `devtools/`: Development tools (planned)

### Provider Capabilities

| Provider | Native Tools | Streaming | Key Features |
|----------|--------------|-----------|--------------|
| OpenAI | ✅ | ✅ | Full tool support, function calling |
| Anthropic | ✅ | ✅ | Native tool use, streaming |
| Google | ✅ | ✅ | Native function calling via google-genai SDK |
| xAI | ✅ | ✅ | Grok models with tool support |
| DeepSeek | ✅ | ✅ | Specialized coding models |
| Ollama | ✅ | ✅ | Local LLM support |

### Testing Strategy
- Unit tests for individual connectors
- Integration tests for provider APIs
- Mock fixtures in `conftest.py`
- Use `pytest-asyncio` for async testing

## Important Notes

1. **Async Operations**: All provider operations are async - use `await` or `asyncio.run()`
2. **Tool Execution**: When `auto_execute=True`, tools are executed automatically
3. **Error Handling**: Each connector implements retry logic and graceful degradation
4. **Cost Tracking**: Token usage tracked in responses and aggregated in wrapper
5. **Session Cleanup**: Web sessions expire after 24 hours of inactivity

## Recent Changes

- **Google SDK Migration**: Migrated from deprecated `google.generativeai` to `google-genai` SDK
- **Native Google Tools**: Google connector now supports native function calling for Gemini 1.5/2.0 models
- **WebSocket Support**: Added real-time streaming via WebSocket manager
- **MeThinks App**: Added AI-powered project specification generator in `apps/methinks/`

## CLI Entry Points (pyproject.toml)

```bash
nexus          # Main Nexus CLI (nexus.cli:main)
methinks       # Project spec generator (apps.methinks.cli:main)
nexus-devtools # Development tools (apps.devtools.cli:main)
```