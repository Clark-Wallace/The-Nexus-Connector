# Nexus API Reference

## Table of Contents

- [Core Classes](#core-classes)
  - [UnifiedAIWrapper](#unifiedaiwrapper)
  - [AIProvider](#aiprovider)
  - [BaseConnector](#baseconnector)
- [Data Classes](#data-classes)
  - [Message](#message)
  - [Response](#response)
  - [TaskResult](#taskresult)
- [Connectors](#connectors)
  - [OpenAIConnector](#openaiconnector)
  - [AnthropicConnector](#anthropicconnector)
  - [GoogleConnector](#googleconnector)
  - [XAIConnector](#xaiconnector)
  - [DeepSeekConnector](#deepseekconnector)
  - [OllamaConnector](#ollamaconnector)
- [Web Components](#web-components)
  - [WebConnector](#webconnector)
  - [WebSocketManager](#websocketmanager)
  - [SessionStore](#sessionstore)
- [Utilities](#utilities)
  - [ToolExecutor](#toolexecutor)
  - [TextApplyEngine](#textapplyengine)

---

## Core Classes

### UnifiedAIWrapper

The main interface for interacting with AI providers.

```python
class UnifiedAIWrapper:
    def __init__(
        self,
        provider: Union[AIProvider, str],
        api_key: str,
        model: Optional[str] = None,
        workspace: Optional[Union[str, Path]] = None,
        max_iterations: int = 10,
        auto_execute: bool = True,
        safe_mode: bool = True,
        verbose: bool = False,
        **kwargs
    )
```

#### Parameters

- `provider` (AIProvider | str): The AI provider to use
- `api_key` (str): API key for authentication
- `model` (str, optional): Specific model to use (defaults to provider's default)
- `workspace` (str | Path, optional): Working directory for file operations
- `max_iterations` (int): Maximum iterations for task execution (default: 10)
- `auto_execute` (bool): Automatically execute tool calls (default: True)
- `safe_mode` (bool): Require confirmation for destructive operations (default: True)
- `verbose` (bool): Enable detailed logging (default: False)
- `**kwargs`: Additional provider-specific parameters

#### Methods

##### send_message

Send a single message to the AI provider.

```python
async def send_message(
    self,
    message: str,
    tools: Optional[List[Dict]] = None,
    **kwargs
) -> Dict[str, Any]
```

**Parameters:**
- `message` (str): The message to send
- `tools` (List[Dict], optional): Tools available to the AI
- `**kwargs`: Additional provider-specific parameters

**Returns:**
- Dict containing:
  - `content` (str): Response content
  - `tool_calls` (List[Dict]): Any tool calls made
  - `usage` (Dict): Token usage information
  - `finish_reason` (str): Reason for completion

##### execute_task

Execute a complex multi-step task.

```python
async def execute_task(
    self,
    task: str,
    tools: Optional[List[Dict]] = None,
    **kwargs
) -> TaskResult
```

**Parameters:**
- `task` (str): Task description
- `tools` (List[Dict], optional): Tools available for execution
- `**kwargs`: Additional parameters

**Returns:**
- `TaskResult` object with execution details

##### stream_message

Stream response tokens as they arrive.

```python
async def stream_message(
    self,
    message: str,
    **kwargs
) -> AsyncIterator[str]
```

**Parameters:**
- `message` (str): The message to send
- `**kwargs`: Additional parameters

**Yields:**
- `str`: Response chunks as they arrive

##### count_tokens

Count tokens for a given text.

```python
def count_tokens(self, text: str) -> int
```

**Parameters:**
- `text` (str): Text to count tokens for

**Returns:**
- `int`: Estimated token count

##### clear_history

Clear the conversation history.

```python
def clear_history(self) -> None
```

---

### AIProvider

Enum representing supported AI providers.

```python
class AIProvider(Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    XAI = "xai"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"
```

#### Properties

##### display_name

Get human-friendly display name.

```python
@property
def display_name(self) -> str
```

---

### BaseConnector

Abstract base class for all AI provider connectors.

```python
class BaseConnector(ABC):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    )
```

#### Abstract Methods

##### send_message

```python
@abstractmethod
async def send_message(
    self,
    messages: List[Message],
    **kwargs
) -> Response
```

##### stream_message

```python
@abstractmethod
async def stream_message(
    self,
    messages: List[Message],
    **kwargs
) -> AsyncIterator[str]
```

##### count_tokens

```python
@abstractmethod
def count_tokens(self, text: str) -> int
```

##### supports_tools

```python
@abstractmethod
def supports_tools(self) -> bool
```

---

## Data Classes

### Message

Represents a conversation message.

```python
@dataclass
class Message:
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict]] = None
    tool_call_id: Optional[str] = None
```

### Response

Represents an AI response.

```python
@dataclass
class Response:
    content: str
    tool_calls: List[Dict]
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None
```

### TaskResult

Represents the result of task execution.

```python
@dataclass
class TaskResult:
    success: bool
    iterations: int
    total_tokens: int
    files_created: List[str]
    files_modified: List[str]
    commands_executed: List[Dict]
    errors: List[str]
    elapsed_time: float
```

---

## Connectors

### OpenAIConnector

Connector for OpenAI GPT models.

```python
class OpenAIConnector(BaseConnector):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        base_url: Optional[str] = None,
        organization: Optional[str] = None,
        **kwargs
    )
```

**Supported Models:**
- gpt-4o
- gpt-4o-mini
- gpt-4-turbo
- gpt-4
- gpt-3.5-turbo

### AnthropicConnector

Connector for Anthropic Claude models.

```python
class AnthropicConnector(BaseConnector):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        max_tokens: int = 4096,
        **kwargs
    )
```

**Supported Models:**
- claude-sonnet-4-20250514
- claude-opus-4-20250514
- claude-3-7-sonnet-20250219
- claude-3-5-sonnet-20241022
- claude-3-5-haiku-20241022
- claude-3-opus-20240229
- claude-3-haiku-20240307

### GoogleConnector

Connector for Google Gemini models. Uses the `google-genai` SDK with native function calling support.

```python
class GoogleConnector(BaseConnector):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    )
```

**Supported Models:**
- gemini-2.0-flash (default)
- gemini-2.0-flash-exp
- gemini-2.0-pro
- gemini-2.0-pro-exp
- gemini-1.5-pro
- gemini-1.5-pro-latest
- gemini-1.5-flash
- gemini-1.5-flash-latest

**Note:** Native function calling is supported for Gemini 1.5 and 2.0 models.

### XAIConnector

Connector for xAI Grok models.

```python
class XAIConnector(OpenAIConnector):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    )
```

**Supported Models:**
- grok-3
- grok-2

### DeepSeekConnector

Connector for DeepSeek models.

```python
class DeepSeekConnector(OpenAIConnector):
    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        **kwargs
    )
```

**Supported Models:**
- deepseek-chat
- deepseek-coder

### OllamaConnector

Connector for local Ollama models.

```python
class OllamaConnector(BaseConnector):
    def __init__(
        self,
        api_key: str = "",  # Not required for local
        model: Optional[str] = None,
        host: str = "http://localhost:11434",
        **kwargs
    )
```

**Supported Models:**
- Any model installed locally via `ollama pull`
- Default: llama3.2

**Note:** Requires Ollama running locally. No API key needed.

---

## Web Components

### WebConnector

FastAPI-based web server for HTTP API access.

```python
class WebConnector:
    def __init__(
        self,
        wrapper_factory: Callable[[], UnifiedAIWrapper],
        host: str = "0.0.0.0",
        port: int = 8000,
        cors_origins: List[str] = ["*"]
    )

    async def start_server(self) -> None
```

**Endpoints:**
- `POST /chat` - Send a message
- `POST /chat/stream` - Stream a response
- `POST /task` - Execute a task
- `GET /health` - Health check

### WebSocketManager

Real-time bidirectional communication via WebSocket.

```python
class WebSocketManager:
    def __init__(
        self,
        wrapper_factory: Callable[[], UnifiedAIWrapper]
    )

    async def handle_connection(
        self,
        websocket: WebSocket,
        session_id: Optional[str] = None
    ) -> None
```

**Message Types:**
- `message` - Send a chat message
- `stream` - Stream a response
- `task` - Execute a task
- `clear` - Clear conversation history

### SessionStore

In-memory session storage with automatic cleanup.

```python
class SessionStore:
    def __init__(
        self,
        ttl: int = 86400  # 24 hours
    )

    def get(self, session_id: str) -> Optional[Dict]
    def set(self, session_id: str, data: Dict) -> None
    def delete(self, session_id: str) -> None
    def cleanup(self) -> int  # Returns cleaned count
```

---

## Utilities

### ToolExecutor

Executes tool calls from AI responses.

```python
class ToolExecutor:
    def __init__(
        self,
        workspace: Path,
        safe_mode: bool = True
    )
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]
```

**Supported Tools:**
- `create_file`: Create or overwrite a file
- `read_file`: Read file contents
- `edit_file`: Edit file contents
- `execute_command`: Run shell commands
- `list_directory`: List directory contents

### TextApplyEngine

Extracts and applies operations from text responses.

```python
class TextApplyEngine:
    def __init__(
        self,
        workspace: Path,
        tool_executor: ToolExecutor
    )
    
    def extract_operations(
        self,
        text: str
    ) -> List[Dict[str, Any]]
    
    async def apply_operations(
        self,
        text: str
    ) -> Dict[str, Any]
```

**Extracted Operations:**
- File creation from code blocks
- Command execution from shell blocks
- File operations from natural language

---

## Error Handling

### Common Exceptions

```python
# Provider not supported
ValueError: "Unsupported provider: unknown"

# API key missing
ValueError: "API key is required"

# Model not supported
ValueError: "Model 'gpt-5' is not supported by OpenAI"

# Tool execution failed
ToolExecutionError: "Failed to create file: Permission denied"

# API errors
APIError: "Rate limit exceeded"
```

### Error Response Format

```python
{
    "success": False,
    "error": {
        "type": "api_error",
        "message": "Rate limit exceeded",
        "details": {...}
    }
}
```

---

## Advanced Configuration

### Provider-Specific Options

#### OpenAI
```python
wrapper = UnifiedAIWrapper(
    provider=AIProvider.OPENAI,
    api_key="...",
    organization="org-xxx",  # Optional organization ID
    temperature=0.7,
    top_p=1.0,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    logit_bias={},
    user="user-123"
)
```

#### Anthropic
```python
wrapper = UnifiedAIWrapper(
    provider=AIProvider.ANTHROPIC,
    api_key="...",
    max_tokens=4096,  # Required for Claude
    temperature=0.7,
    top_p=1.0,
    top_k=40
)
```

#### Google
```python
wrapper = UnifiedAIWrapper(
    provider=AIProvider.GOOGLE,
    api_key="...",
    temperature=0.7,
    top_p=0.95,
    top_k=40,
    candidate_count=1,
    stop_sequences=[]
)
```

---

## Tool Definition Format

### OpenAI-style Tools

```python
tools = [{
    "type": "function",
    "function": {
        "name": "create_file",
        "description": "Create a new file with content",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File path relative to workspace"
                },
                "content": {
                    "type": "string", 
                    "description": "File content"
                }
            },
            "required": ["path", "content"]
        }
    }
}]
```

### Tool Response Format

```python
{
    "success": True,
    "result": {
        "path": "example.py",
        "size": 1234,
        "created": True
    }
}
```