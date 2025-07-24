# Technical Stack

> Last Updated: 2025-07-23
> Version: 1.0.0

## Core Technologies

### Application Framework
- **Framework:** Python (Pure Python library)
- **Version:** 3.8+
- **Language:** Python 3.8-3.12

### Async Framework
- **Framework:** asyncio
- **HTTP Client:** aiohttp 3.8.0+
- **Purpose:** Concurrent API calls and streaming

### Web Framework
- **Framework:** FastAPI
- **Version:** 0.104.0+
- **Server:** Uvicorn with standard extras

## Frontend Stack

### JavaScript Framework
- **Framework:** N/A (API-only, no frontend)
- **Integration:** Designed for any frontend via REST API

### Import Strategy
- **Strategy:** Python modules via pip
- **Package Manager:** pip
- **Python Version:** 3.8+

## Dependencies

### AI Provider SDKs
- **OpenAI:** openai 1.0.0+
- **Anthropic:** anthropic 0.25.0+
- **Google:** google-generativeai 0.3.0+
- **Ollama:** ollama 0.1.0+
- **Others:** Direct HTTP via aiohttp

### Core Libraries
- **Validation:** pydantic 2.0.0+
- **Configuration:** python-dotenv 1.0.0+
- **HTTP Sync:** requests 2.28.0+

### Development Tools
- **Testing:** pytest 7.0+, pytest-asyncio 0.21+
- **Coverage:** pytest-cov 4.0+
- **Mocking:** pytest-mock 3.10+
- **Formatting:** black 23.0+, isort 5.12+
- **Type Checking:** mypy 1.0+
- **Linting:** ruff 0.1+
- **Pre-commit:** pre-commit 3.0+

## Infrastructure

### Application Hosting
- **Platform:** Any Python-capable platform
- **Deployment:** Docker, Kubernetes, Cloud Functions
- **Requirements:** Python 3.8+ runtime

### Recommended Hosting
- **Provider:** AWS Lambda, Google Cloud Run, Azure Functions
- **Alternative:** Digital Ocean App Platform, Heroku
- **Local:** Direct Python execution

### Package Distribution
- **Registry:** PyPI (planned)
- **Current:** GitHub source installation
- **Format:** wheel and sdist

## Deployment

### CI/CD Pipeline
- **Platform:** GitHub Actions
- **Trigger:** Push to main, PR creation
- **Tests:** Unit and integration tests
- **Checks:** Type checking, linting, formatting

### Environments
- **Production:** main branch
- **Development:** feature branches
- **Testing:** Automated via pytest

### Packaging
- **Build System:** setuptools 61.0+
- **Config:** pyproject.toml (PEP 517/518)
- **Versioning:** Semantic versioning

## Architecture Patterns

### Design Patterns
- **Strategy Pattern:** Provider implementations
- **Factory Pattern:** Dynamic connector creation
- **Adapter Pattern:** Provider API normalization
- **Observer Pattern:** Streaming responses

### Code Organization
- **Structure:** Package-based modules
- **Interfaces:** Abstract base classes
- **Type Safety:** Full type annotations
- **Error Handling:** Custom exception hierarchy