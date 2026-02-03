# Nexus Architecture

## Overview

Nexus is designed with a modular, extensible architecture that provides a unified interface for multiple AI providers while maintaining provider-specific optimizations. The architecture follows SOLID principles and uses well-established design patterns to ensure maintainability and scalability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Application                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      UnifiedAIWrapper                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ • Session Management                                     │   │
│  │ • Conversation History                                   │   │
│  │ • Iterative Task Execution                             │   │
│  │ • Provider Factory                                      │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
             ▼                               ▼
┌─────────────────────────┐      ┌─────────────────────────┐
│    BaseConnector        │      │    ToolExecutor         │
│  (Abstract Interface)    │      │  • File Operations      │
│  • send_message()       │      │  • Command Execution    │
│  • stream_message()     │      │  • Safety Checks        │
│  • supports_tools()     │      └─────────────────────────┘
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Connector Layer                           │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌─────┐ ┌──────────┐    │
│  │ OpenAI  │ │Anthropic │ │ Google │ │ xAI │ │ DeepSeek │    │
│  └─────────┘ └──────────┘ └────────┘ └─────┘ └──────────┘    │
│  ┌────────┐                                                     │
│  │ Ollama │  (Local LLM support)                               │
│  └────────┘                                                     │
└─────────────────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External AI Provider APIs                     │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. UnifiedAIWrapper

The main entry point and orchestrator of the system.

**Responsibilities:**
- Provider selection and initialization
- Session and conversation management
- Iterative task execution logic
- High-level API for users

**Key Design Decisions:**
- Uses factory pattern for connector creation
- Implements the proven GPT-4o iterative execution pattern
- Maintains conversation history for context
- Provides both synchronous and asynchronous interfaces

### 2. BaseConnector

Abstract base class defining the interface all connectors must implement.

**Responsibilities:**
- Define common interface for all providers
- Enforce consistent data structures
- Provide base implementation for common functionality

**Design Pattern:** Strategy Pattern
- Each connector is a concrete strategy
- UnifiedAIWrapper is the context that uses these strategies

### 3. Provider Connectors

Concrete implementations for each AI provider.

**OpenAIConnector:**
- Native tool/function calling support
- Streaming via Server-Sent Events
- Direct API integration

**AnthropicConnector:**
- Handles Claude's unique message format
- Converts tool results to user messages
- Supports all Claude 3 models

**GoogleConnector:**
- Uses `google-genai` SDK (new unified SDK)
- Native function calling for Gemini 1.5/2.0 models
- Handles Gemini-specific parameters (top_k, etc.)

**XAIConnector:**
- Extends OpenAIConnector (compatible API)
- Custom endpoint configuration
- Grok-specific model handling

**DeepSeekConnector:**
- Extends OpenAIConnector
- Cost-optimized for large contexts
- DeepSeek-specific endpoints

**OllamaConnector:**
- Local LLM support via Ollama
- No API key required
- Tool support for compatible models
- Configurable host endpoint

### 4. ToolExecutor

Handles execution of tool calls from AI responses.

**Responsibilities:**
- File system operations
- Command execution
- Safety validations
- Result formatting

**Security Features:**
- Workspace isolation
- Command whitelisting/blacklisting
- Confirmation prompts for destructive operations

### 5. TextApplyEngine

Extracts operations from text responses for providers without native tool support.

**Responsibilities:**
- Parse code blocks from responses
- Identify file operations
- Extract shell commands
- Apply operations via ToolExecutor

**Pattern Matching:**
- Code blocks with file indicators
- Natural language file creation patterns
- Shell/bash command blocks

### 6. Web Components

**WebConnector:**
- FastAPI-based HTTP server
- REST endpoints for chat, streaming, and task execution
- CORS support for browser clients
- Health check endpoint

**WebSocketManager:**
- Real-time bidirectional communication
- Session-aware connections
- Streaming message support
- Automatic reconnection handling

**SessionStore:**
- In-memory session storage
- Automatic TTL-based cleanup (24 hours default)
- Thread-safe operations
- Per-session conversation history

```
┌─────────────────────────────────────────────────────────────────┐
│                         Web Layer                                │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  WebConnector   │  │ WebSocketManager │  │ SessionStore │  │
│  │  (REST API)     │  │  (Real-time)     │  │  (State)     │  │
│  └────────┬────────┘  └────────┬─────────┘  └──────┬───────┘  │
│           │                    │                    │          │
│           └────────────────────┴────────────────────┘          │
│                              │                                  │
│                              ▼                                  │
│                    UnifiedAIWrapper                             │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### 1. Message Send Flow

```
User Message
    │
    ▼
UnifiedAIWrapper.send_message()
    │
    ├─> Add to conversation history
    │
    ├─> Select appropriate connector
    │
    ▼
Connector.send_message()
    │
    ├─> Format messages for provider
    │
    ├─> Make API call
    │
    ├─> Parse response
    │
    ▼
Response object
    │
    ├─> Extract tool calls (if any)
    │
    ├─> Execute tools (if auto_execute=True)
    │
    ▼
Return unified response
```

### 2. Task Execution Flow

```
Task Description
    │
    ▼
UnifiedAIWrapper.execute_task()
    │
    ▼
┌─> Iteration Loop (max_iterations)
│       │
│       ├─> Send message/continuation
│       │
│       ├─> Receive response
│       │
│       ├─> Execute tool calls
│       │
│       ├─> Check completion
│       │
│       └─> Continue or finish
│
└─> Return TaskResult
```

## Design Patterns

### 1. Strategy Pattern
- **Context:** UnifiedAIWrapper
- **Strategy Interface:** BaseConnector
- **Concrete Strategies:** Provider connectors
- **Benefit:** Easy to add new providers without modifying core logic

### 2. Factory Pattern
- **Factory Method:** `_create_connector()`
- **Products:** Connector instances
- **Benefit:** Encapsulates connector creation logic

### 3. Adapter Pattern
- **Adaptee:** Provider-specific APIs
- **Adapter:** Individual connectors
- **Target:** BaseConnector interface
- **Benefit:** Uniform interface for diverse APIs

### 4. Template Method Pattern
- **Abstract Class:** BaseConnector
- **Template Methods:** Common operations
- **Hook Methods:** Provider-specific implementations
- **Benefit:** Code reuse and consistent behavior

### 5. Iterator Pattern
- **Implementation:** Streaming responses
- **Benefit:** Memory-efficient handling of large responses

## Extension Points

### 1. Adding New Providers

```python
# 1. Create connector
class NewProviderConnector(BaseConnector):
    async def send_message(self, messages, **kwargs):
        # Provider-specific implementation
        pass

# 2. Add to AIProvider enum
class AIProvider(Enum):
    NEWPROVIDER = "newprovider"

# 3. Update factory in UnifiedAIWrapper
elif provider == AIProvider.NEWPROVIDER:
    from ..connectors.newprovider_connector import NewProviderConnector
    return NewProviderConnector(api_key, model, **kwargs)
```

### 2. Custom Tool Implementation

```python
# Add to ToolExecutor
async def execute_custom_tool(self, tool_name: str, args: Dict):
    if tool_name == "my_custom_tool":
        # Custom implementation
        return {"success": True, "result": ...}
```

### 3. Response Processing

```python
# Custom response processor
class CustomResponseProcessor:
    def process(self, response: Response) -> Response:
        # Custom processing logic
        return modified_response
```

## Performance Considerations

### 1. Async/Await Throughout
- All I/O operations are asynchronous
- Prevents blocking on API calls
- Enables concurrent operations

### 2. Streaming Support
- Memory-efficient for large responses
- Better user experience with real-time output
- Implemented via async generators

### 3. Connection Pooling
- Reuse HTTP connections where possible
- Implemented in provider SDKs
- Reduces latency

### 4. Caching Considerations
- Conversation history maintained in memory
- No response caching by default (can be added)
- Tool execution results not cached

## Security Architecture

### 1. API Key Management
- Keys passed directly, not stored
- Support for environment variables
- No key logging

### 2. Workspace Isolation
- All file operations confined to workspace
- Path traversal prevention
- No access outside designated directory

### 3. Command Execution Safety
- Whitelist/blacklist support
- Timeout protection
- User confirmation for destructive operations

### 4. Input Validation
- Parameter validation at all levels
- Type checking with Python type hints
- Sanitization of file paths

## Error Handling Strategy

### 1. Graceful Degradation
- Provider errors don't crash the system
- Fallback behaviors for missing features
- Clear error messages to users

### 2. Error Propagation
- Errors wrapped in consistent format
- Original error details preserved
- Stack traces in verbose mode

### 3. Retry Logic
- Not implemented by default
- Can be added at connector level
- Provider-specific retry strategies

## Testing Architecture

### 1. Unit Tests
- Mock external API calls
- Test individual components
- High coverage target (>80%)

### 2. Integration Tests
- Test full message flow
- Verify provider compatibility
- End-to-end scenarios

### 3. Provider Tests
- Individual test suites per provider
- Real API calls (requires keys)
- Verify provider-specific features

## Future Architecture Considerations

### 1. Plugin System
- Dynamic loading of connectors
- Third-party connector support
- Hook system for customization

### 2. Caching Layer
- Response caching
- Embedding caching
- Configurable cache strategies

### 3. Middleware Pipeline
- Request/response interceptors
- Custom processing stages
- Monitoring and logging hooks

### 4. Load Balancing
- Multiple API keys per provider
- Automatic failover
- Rate limit management