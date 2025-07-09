# Core API Reference

This document provides comprehensive API reference for the UAP Framework core components.

## Data Models

### Task

Represents a unit of work to be executed by an agent.

```python
from uap_core.models import Task, TaskType, Priority

task = Task(
    id="unique-task-id",
    type=TaskType.TEXT_GENERATION,
    prompt="Generate a summary of the document",
    priority=Priority.HIGH,
    context={"user_id": "123", "session_id": "abc"},
    constraints={"max_tokens": 500, "temperature": 0.7},
    files=["document.pdf"],
    metadata={"department": "marketing"}
)
```

**Parameters:**
- `id` (str): Unique identifier for the task
- `type` (TaskType): Type of task to be executed
- `prompt` (str): Main instruction or query for the agent
- `priority` (Priority, optional): Task priority level (default: MEDIUM)
- `context` (Dict[str, Any], optional): Additional context information
- `constraints` (Dict[str, Any], optional): Execution constraints and parameters
- `files` (List[str], optional): List of file paths or URLs
- `metadata` (Dict[str, Any], optional): Additional metadata

**Methods:**
- `to_dict() -> Dict[str, Any]`: Serialize task to dictionary
- `from_dict(data: Dict[str, Any]) -> Task`: Create task from dictionary
- `validate() -> bool`: Validate task data

### ExecutionResult

Represents the result of task execution by an agent.

```python
from uap_core.models import ExecutionResult, Status
from datetime import datetime

result = ExecutionResult(
    task_id="unique-task-id",
    agent_id="agent-123",
    status=Status.SUCCESS,
    output="Generated summary text",
    started_at=datetime.utcnow(),
    completed_at=datetime.utcnow(),
    duration=2.5,
    cost=0.05,
    confidence=0.95,
    tokens_used=150,
    error_message=None,
    metadata={"model": "gpt-4"}
)
```

**Parameters:**
- `task_id` (str): ID of the executed task
- `agent_id` (str): ID of the agent that executed the task
- `status` (Status): Execution status
- `output` (str, optional): Generated output or result
- `started_at` (datetime): Task start timestamp
- `completed_at` (datetime, optional): Task completion timestamp
- `duration` (float, optional): Execution duration in seconds
- `cost` (float, optional): Execution cost
- `confidence` (float, optional): Confidence score (0.0-1.0)
- `tokens_used` (int, optional): Number of tokens consumed
- `error_message` (str, optional): Error message if failed
- `metadata` (Dict[str, Any], optional): Additional result metadata

### AgentCapabilities

Defines the capabilities and constraints of an agent.

```python
from uap_core.models import AgentCapabilities, TaskType

capabilities = AgentCapabilities(
    supported_tasks=[TaskType.TEXT_GENERATION, TaskType.TRANSLATION],
    languages=["python", "javascript", "java"],
    max_context_length=4000,
    supports_streaming=True,
    supports_function_calling=True,
    cost_per_token=0.001,
    max_concurrent_tasks=5,
    specializations=["technical_writing", "code_review"]
)
```

**Parameters:**
- `supported_tasks` (List[TaskType]): List of supported task types
- `languages` (List[str], optional): Supported programming languages
- `max_context_length` (int, optional): Maximum context length
- `supports_streaming` (bool, optional): Whether streaming is supported
- `supports_function_calling` (bool, optional): Function calling support
- `cost_per_token` (float, optional): Cost per token
- `max_concurrent_tasks` (int, optional): Maximum concurrent tasks
- `specializations` (List[str], optional): Agent specializations

**Methods:**
- `can_handle_task(task: Task) -> bool`: Check if agent can handle task
- `estimate_cost(task: Task) -> float`: Estimate execution cost
- `get_compatibility_score(task: Task) -> float`: Get compatibility score

## Enums

### TaskType

Enumeration of supported task types.

```python
from uap_core.models import TaskType

# Available task types
TaskType.TEXT_GENERATION      # General text generation
TaskType.CODE_GENERATION      # Code generation and programming
TaskType.TRANSLATION          # Language translation
TaskType.SUMMARIZATION        # Text summarization
TaskType.QUESTION_ANSWERING   # Question answering
TaskType.IMAGE_GENERATION     # Image generation
TaskType.IMAGE_ANALYSIS       # Image analysis and description
TaskType.DATA_ANALYSIS        # Data analysis and insights
TaskType.RESEARCH             # Research and information gathering
TaskType.CREATIVE_WRITING     # Creative writing tasks
TaskType.TECHNICAL_WRITING    # Technical documentation
TaskType.REVIEW               # Code/content review
TaskType.OPTIMIZATION         # Performance optimization
TaskType.TESTING              # Test generation and execution
TaskType.CUSTOM               # Custom task types
```

### Status

Enumeration of execution statuses.

```python
from uap_core.models import Status

Status.PENDING      # Task is queued for execution
Status.RUNNING      # Task is currently being executed
Status.SUCCESS      # Task completed successfully
Status.FAILURE      # Task failed with error
Status.CANCELLED    # Task was cancelled
Status.TIMEOUT      # Task timed out
```

### Priority

Enumeration of task priorities.

```python
from uap_core.models import Priority

Priority.LOW        # Low priority task
Priority.MEDIUM     # Medium priority task (default)
Priority.HIGH       # High priority task
Priority.URGENT     # Urgent priority task
```

## Validation

### TaskValidator

Validates task data and constraints.

```python
from uap_core.validation import TaskValidator

validator = TaskValidator()

# Validate a task
is_valid = validator.validate_task(task)

# Get validation errors
errors = validator.get_validation_errors(task)

# Validate task constraints
is_valid_constraints = validator.validate_constraints(task.constraints)
```

**Methods:**
- `validate_task(task: Task) -> bool`: Validate complete task
- `validate_prompt(prompt: str) -> bool`: Validate task prompt
- `validate_constraints(constraints: Dict[str, Any]) -> bool`: Validate constraints
- `get_validation_errors(task: Task) -> List[str]`: Get validation error messages

### AgentValidator

Validates agent capabilities and configuration.

```python
from uap_core.validation import AgentValidator

validator = AgentValidator()

# Validate agent capabilities
is_valid = validator.validate_capabilities(capabilities)

# Check task compatibility
is_compatible = validator.check_task_compatibility(capabilities, task)

# Validate agent configuration
is_valid_config = validator.validate_agent_config(agent_config)
```

**Methods:**
- `validate_capabilities(capabilities: AgentCapabilities) -> bool`: Validate capabilities
- `check_task_compatibility(capabilities: AgentCapabilities, task: Task) -> bool`: Check compatibility
- `validate_agent_config(config: Dict[str, Any]) -> bool`: Validate agent configuration
- `get_capability_score(capabilities: AgentCapabilities, task: Task) -> float`: Get capability score

## Serialization

### Serializer

Handles serialization and deserialization of UAP objects.

```python
from uap_core.serialization import Serializer

serializer = Serializer()

# Serialize to JSON
json_data = serializer.to_json(task)

# Deserialize from JSON
task = serializer.from_json(json_data, Task)

# Serialize to MessagePack
msgpack_data = serializer.to_msgpack(result)

# Deserialize from MessagePack
result = serializer.from_msgpack(msgpack_data, ExecutionResult)

# Serialize to Protocol Buffers
protobuf_data = serializer.to_protobuf(task)

# Deserialize from Protocol Buffers
task = serializer.from_protobuf(protobuf_data, Task)
```

**Methods:**
- `to_json(obj: Any) -> str`: Serialize to JSON string
- `from_json(data: str, cls: Type) -> Any`: Deserialize from JSON
- `to_msgpack(obj: Any) -> bytes`: Serialize to MessagePack
- `from_msgpack(data: bytes, cls: Type) -> Any`: Deserialize from MessagePack
- `to_protobuf(obj: Any) -> bytes`: Serialize to Protocol Buffers
- `from_protobuf(data: bytes, cls: Type) -> Any`: Deserialize from Protocol Buffers

## Configuration

### ConfigManager

Manages framework configuration settings.

```python
from uap_core.config import ConfigManager

config = ConfigManager()

# Load configuration from file
config.load_from_file("config.yaml")

# Load from environment variables
config.load_from_env()

# Get configuration values
redis_url = config.get("redis.url", "redis://localhost:6379")
log_level = config.get("logging.level", "INFO")

# Set configuration values
config.set("agent.timeout", 30)

# Get typed configuration
timeout = config.get_int("agent.timeout", 30)
enabled = config.get_bool("features.monitoring", True)
```

**Methods:**
- `load_from_file(path: str) -> None`: Load from configuration file
- `load_from_env(prefix: str = "UAP_") -> None`: Load from environment variables
- `get(key: str, default: Any = None) -> Any`: Get configuration value
- `set(key: str, value: Any) -> None`: Set configuration value
- `get_int(key: str, default: int = 0) -> int`: Get integer value
- `get_bool(key: str, default: bool = False) -> bool`: Get boolean value
- `get_float(key: str, default: float = 0.0) -> float`: Get float value
- `get_list(key: str, default: List = None) -> List`: Get list value

## Utilities

### TaskBuilder

Builder pattern for creating tasks.

```python
from uap_core.utils import TaskBuilder

task = (TaskBuilder()
    .set_type(TaskType.TEXT_GENERATION)
    .set_prompt("Generate a summary")
    .set_priority(Priority.HIGH)
    .add_context("user_id", "123")
    .add_constraint("max_tokens", 500)
    .add_file("document.pdf")
    .build())
```

**Methods:**
- `set_id(task_id: str) -> TaskBuilder`: Set task ID
- `set_type(task_type: TaskType) -> TaskBuilder`: Set task type
- `set_prompt(prompt: str) -> TaskBuilder`: Set task prompt
- `set_priority(priority: Priority) -> TaskBuilder`: Set task priority
- `add_context(key: str, value: Any) -> TaskBuilder`: Add context item
- `add_constraint(key: str, value: Any) -> TaskBuilder`: Add constraint
- `add_file(file_path: str) -> TaskBuilder`: Add file reference
- `set_metadata(metadata: Dict[str, Any]) -> TaskBuilder`: Set metadata
- `build() -> Task`: Build the task

### ResultBuilder

Builder pattern for creating execution results.

```python
from uap_core.utils import ResultBuilder

result = (ResultBuilder()
    .set_task_id("task-123")
    .set_agent_id("agent-456")
    .set_status(Status.SUCCESS)
    .set_output("Generated content")
    .set_duration(2.5)
    .set_cost(0.05)
    .set_confidence(0.95)
    .build())
```

**Methods:**
- `set_task_id(task_id: str) -> ResultBuilder`: Set task ID
- `set_agent_id(agent_id: str) -> ResultBuilder`: Set agent ID
- `set_status(status: Status) -> ResultBuilder`: Set execution status
- `set_output(output: str) -> ResultBuilder`: Set output content
- `set_error(error_message: str) -> ResultBuilder`: Set error message
- `set_duration(duration: float) -> ResultBuilder`: Set execution duration
- `set_cost(cost: float) -> ResultBuilder`: Set execution cost
- `set_confidence(confidence: float) -> ResultBuilder`: Set confidence score
- `set_tokens_used(tokens: int) -> ResultBuilder`: Set tokens used
- `add_metadata(key: str, value: Any) -> ResultBuilder`: Add metadata
- `build() -> ExecutionResult`: Build the result

## Exceptions

### UAP Framework Exceptions

Custom exceptions for error handling.

```python
from uap_core.exceptions import (
    UAP_Exception,
    TaskValidationError,
    AgentNotFoundError,
    ExecutionTimeoutError,
    InsufficientCapabilitiesError,
    AuthenticationError,
    AuthorizationError
)

try:
    result = await router.route_task(task)
except TaskValidationError as e:
    print(f"Task validation failed: {e}")
except AgentNotFoundError as e:
    print(f"No suitable agent found: {e}")
except ExecutionTimeoutError as e:
    print(f"Task execution timed out: {e}")
except UAP_Exception as e:
    print(f"UAP framework error: {e}")
```

**Exception Hierarchy:**
- `UAP_Exception`: Base exception for all UAP errors
  - `TaskValidationError`: Task validation failures
  - `AgentNotFoundError`: No suitable agent available
  - `ExecutionTimeoutError`: Task execution timeout
  - `InsufficientCapabilitiesError`: Agent lacks required capabilities
  - `AuthenticationError`: Authentication failures
  - `AuthorizationError`: Authorization failures
  - `ConfigurationError`: Configuration errors
  - `SerializationError`: Serialization/deserialization errors

## Type Hints

The UAP framework provides comprehensive type hints for better development experience:

```python
from typing import Dict, List, Optional, Union, Any
from uap_core.models import Task, ExecutionResult, AgentCapabilities

# Function with type hints
async def process_task(
    task: Task,
    agent_id: str,
    timeout: Optional[float] = None
) -> ExecutionResult:
    # Implementation
    pass

# Generic types
TaskDict = Dict[str, Any]
ResultList = List[ExecutionResult]
CapabilityMap = Dict[str, AgentCapabilities]
```

## Best Practices

### Error Handling

```python
from uap_core.exceptions import UAP_Exception
import logging

logger = logging.getLogger(__name__)

async def safe_task_execution(task: Task) -> Optional[ExecutionResult]:
    try:
        result = await router.route_task(task)
        return result
    except UAP_Exception as e:
        logger.error(f"Task execution failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
```

### Validation

```python
from uap_core.validation import TaskValidator

validator = TaskValidator()

def create_validated_task(prompt: str, task_type: TaskType) -> Task:
    task = Task(
        id=generate_task_id(),
        type=task_type,
        prompt=prompt
    )
    
    if not validator.validate_task(task):
        errors = validator.get_validation_errors(task)
        raise TaskValidationError(f"Task validation failed: {errors}")
    
    return task
```

### Configuration

```python
from uap_core.config import ConfigManager

# Initialize configuration
config = ConfigManager()
config.load_from_file("config.yaml")
config.load_from_env("UAP_")

# Use configuration in components
class MyComponent:
    def __init__(self):
        self.timeout = config.get_int("component.timeout", 30)
        self.enabled = config.get_bool("component.enabled", True)
```

This core API provides the foundation for building robust multi-agent applications with the UAP framework. All components are designed to be type-safe, well-documented, and easy to use.

