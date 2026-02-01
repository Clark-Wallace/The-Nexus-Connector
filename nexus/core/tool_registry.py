"""
Tool Registry - Plugin system for custom tools.

Provides a @tool decorator and registry for registering custom tools
that can be used by AI providers during task execution.
"""

import asyncio
import inspect
import json
from dataclasses import dataclass, field
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Type,
    Union,
    get_type_hints,
    get_origin,
    get_args,
)
from functools import wraps


# Type mapping from Python types to JSON Schema types
PYTHON_TO_JSON_SCHEMA = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
    type(None): "null",
}


@dataclass
class ToolParameter:
    """Metadata for a tool parameter."""
    name: str
    type: str
    description: str = ""
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class ToolMetadata:
    """
    Complete metadata for a registered tool.

    This contains all information needed to:
    - Generate OpenAI-format tool definitions
    - Execute the tool
    - Validate arguments
    """
    name: str
    description: str
    function: Callable
    parameters: List[ToolParameter] = field(default_factory=list)
    category: str = "general"
    timeout: Optional[float] = None
    retry_count: int = 0
    retry_delay: float = 1.0
    is_async: bool = False
    is_destructive: bool = False
    requires_confirmation: bool = False

    def to_openai_format(self) -> Dict[str, Any]:
        """
        Generate OpenAI-compatible tool definition.

        Returns a dict that can be passed directly to OpenAI's tools parameter.
        """
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": param.type}
            if param.description:
                prop["description"] = param.description
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }
            }
        }

    def to_anthropic_format(self) -> Dict[str, Any]:
        """
        Generate Anthropic-compatible tool definition.
        """
        properties = {}
        required = []

        for param in self.parameters:
            prop = {"type": param.type}
            if param.description:
                prop["description"] = param.description
            if param.enum:
                prop["enum"] = param.enum
            properties[param.name] = prop

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required,
            }
        }


def _get_json_schema_type(python_type: Type) -> str:
    """Convert a Python type to JSON Schema type."""
    # Handle None type
    if python_type is type(None):
        return "null"

    # Handle basic types
    if python_type in PYTHON_TO_JSON_SCHEMA:
        return PYTHON_TO_JSON_SCHEMA[python_type]

    # Handle Optional types
    origin = get_origin(python_type)
    if origin is Union:
        args = get_args(python_type)
        # Check if it's Optional (Union with None)
        non_none_args = [a for a in args if a is not type(None)]
        if len(non_none_args) == 1:
            return _get_json_schema_type(non_none_args[0])
        # For actual unions, default to string
        return "string"

    # Handle List/list
    if origin in (list, List):
        return "array"

    # Handle Dict/dict
    if origin in (dict, Dict):
        return "object"

    # Default to string for unknown types
    return "string"


def _extract_parameters_from_function(func: Callable) -> List[ToolParameter]:
    """
    Extract parameter metadata from a function's signature and type hints.
    """
    sig = inspect.signature(func)
    hints = get_type_hints(func) if hasattr(func, "__annotations__") else {}

    # Get docstring for parameter descriptions
    doc = inspect.getdoc(func) or ""
    param_docs = _parse_docstring_params(doc)

    parameters = []

    for name, param in sig.parameters.items():
        # Skip self, cls, and **kwargs
        if name in ("self", "cls") or param.kind == inspect.Parameter.VAR_KEYWORD:
            continue

        # Get type
        python_type = hints.get(name, str)
        json_type = _get_json_schema_type(python_type)

        # Check if required (has no default)
        required = param.default is inspect.Parameter.empty
        default = None if required else param.default

        # Get description from docstring
        description = param_docs.get(name, "")

        parameters.append(ToolParameter(
            name=name,
            type=json_type,
            description=description,
            required=required,
            default=default,
        ))

    return parameters


def _parse_docstring_params(docstring: str) -> Dict[str, str]:
    """
    Parse parameter descriptions from a docstring.

    Supports Google-style and reStructuredText-style docstrings.
    """
    param_docs = {}
    lines = docstring.split("\n")

    current_param = None
    current_desc = []

    for line in lines:
        stripped = line.strip()

        # Google style: "param_name: description" or "param_name (type): description"
        if stripped.startswith(("Args:", "Arguments:", "Parameters:")):
            continue

        # Check for new parameter (indented with name)
        if ":" in stripped and not stripped.startswith(":"):
            parts = stripped.split(":", 1)
            # Handle "name (type): desc" format
            name_part = parts[0].strip()
            if "(" in name_part:
                name_part = name_part.split("(")[0].strip()

            if current_param:
                param_docs[current_param] = " ".join(current_desc).strip()

            current_param = name_part
            current_desc = [parts[1].strip()] if len(parts) > 1 else []

        # reStructuredText style: ":param name: description"
        elif stripped.startswith(":param "):
            if current_param:
                param_docs[current_param] = " ".join(current_desc).strip()

            match = stripped[7:]  # Remove ":param "
            if ":" in match:
                name, desc = match.split(":", 1)
                current_param = name.strip()
                current_desc = [desc.strip()]
            else:
                current_param = match.strip()
                current_desc = []

        # Continuation of current parameter description
        elif current_param and stripped and not stripped.startswith((":return", ":raises", "Returns:", "Raises:")):
            current_desc.append(stripped)

        # End of parameters section
        elif stripped.startswith((":return", ":raises", "Returns:", "Raises:")):
            if current_param:
                param_docs[current_param] = " ".join(current_desc).strip()
            break

    # Don't forget the last parameter
    if current_param:
        param_docs[current_param] = " ".join(current_desc).strip()

    return param_docs


def tool(
    description: Optional[str] = None,
    name: Optional[str] = None,
    category: str = "general",
    timeout: Optional[float] = None,
    retry: int = 0,
    retry_delay: float = 1.0,
    destructive: bool = False,
    confirm: bool = False,
) -> Callable:
    """
    Decorator to register a function as a tool.

    Usage:
        @tool(description="Search the web")
        async def search(query: str) -> str:
            '''
            Search for information on the web.

            Args:
                query: The search query
            '''
            return await do_search(query)

    Args:
        description: Tool description (defaults to docstring first line)
        name: Tool name (defaults to function name)
        category: Category for grouping tools
        timeout: Execution timeout in seconds
        retry: Number of retries on failure
        retry_delay: Delay between retries in seconds
        destructive: Whether this tool performs destructive operations
        confirm: Whether to require confirmation before execution

    Returns:
        Decorated function with attached metadata
    """
    def decorator(func: Callable) -> Callable:
        # Get function metadata
        func_name = name or func.__name__
        func_doc = inspect.getdoc(func) or ""
        func_desc = description or func_doc.split("\n")[0] if func_doc else f"Execute {func_name}"

        # Extract parameters from signature
        parameters = _extract_parameters_from_function(func)

        # Create metadata
        metadata = ToolMetadata(
            name=func_name,
            description=func_desc,
            function=func,
            parameters=parameters,
            category=category,
            timeout=timeout,
            retry_count=retry,
            retry_delay=retry_delay,
            is_async=asyncio.iscoroutinefunction(func),
            is_destructive=destructive,
            requires_confirmation=confirm or destructive,
        )

        # Attach metadata to function
        func._tool_metadata = metadata

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if metadata.is_async:
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if metadata.is_async:
                return asyncio.run(func(*args, **kwargs))
            else:
                return func(*args, **kwargs)

        # Return appropriate wrapper based on whether function is async
        wrapper = async_wrapper if metadata.is_async else sync_wrapper
        wrapper._tool_metadata = metadata
        return wrapper

    return decorator


class ToolRegistry:
    """
    Registry for managing tools.

    Provides registration, discovery, and execution of tools.
    """

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}
        self._categories: Dict[str, List[str]] = {}

    def register(
        self,
        func: Optional[Callable] = None,
        **kwargs
    ) -> Union[Callable, ToolMetadata]:
        """
        Register a tool function.

        Can be used as a decorator or called directly:

            # As decorator
            @registry.register(description="My tool")
            def my_tool(x: int) -> str:
                ...

            # Direct registration
            registry.register(some_function, description="Some tool")
        """
        def do_register(f: Callable) -> Callable:
            # If function already has metadata, use it
            if hasattr(f, "_tool_metadata"):
                metadata = f._tool_metadata
            else:
                # Create metadata from kwargs
                decorated = tool(**kwargs)(f)
                metadata = decorated._tool_metadata
                f = decorated

            # Register in tools dict
            self._tools[metadata.name] = metadata

            # Register in category
            if metadata.category not in self._categories:
                self._categories[metadata.category] = []
            if metadata.name not in self._categories[metadata.category]:
                self._categories[metadata.category].append(metadata.name)

            return f

        if func is not None:
            return do_register(func)
        return do_register

    def register_tool(self, func: Callable, **kwargs) -> ToolMetadata:
        """Register a tool and return its metadata."""
        self.register(func, **kwargs)
        return self.get(func.__name__)

    def unregister(self, name: str) -> bool:
        """Unregister a tool by name."""
        if name in self._tools:
            metadata = self._tools.pop(name)
            # Remove from category
            if metadata.category in self._categories:
                self._categories[metadata.category] = [
                    n for n in self._categories[metadata.category] if n != name
                ]
            return True
        return False

    def get(self, name: str) -> Optional[ToolMetadata]:
        """Get tool metadata by name."""
        return self._tools.get(name)

    def get_all(self) -> List[ToolMetadata]:
        """Get all registered tools."""
        return list(self._tools.values())

    def get_by_category(self, category: str) -> List[ToolMetadata]:
        """Get tools by category."""
        names = self._categories.get(category, [])
        return [self._tools[name] for name in names if name in self._tools]

    def get_categories(self) -> List[str]:
        """Get all categories."""
        return list(self._categories.keys())

    def get_tool_definitions(self, format: str = "openai") -> List[Dict[str, Any]]:
        """
        Get tool definitions in specified format.

        Args:
            format: "openai" or "anthropic"

        Returns:
            List of tool definitions
        """
        definitions = []
        for metadata in self._tools.values():
            if format == "anthropic":
                definitions.append(metadata.to_anthropic_format())
            else:
                definitions.append(metadata.to_openai_format())
        return definitions

    async def execute(
        self,
        name: str,
        arguments: Dict[str, Any],
        confirm_callback: Optional[Callable[[ToolMetadata], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.

        Args:
            name: Tool name
            arguments: Tool arguments
            confirm_callback: Optional callback for confirmation

        Returns:
            Execution result dict
        """
        metadata = self._tools.get(name)
        if not metadata:
            return {
                "success": False,
                "error": f"Unknown tool: {name}",
                "available_tools": list(self._tools.keys())
            }

        # Check for confirmation
        if metadata.requires_confirmation and confirm_callback:
            if not confirm_callback(metadata):
                return {
                    "success": False,
                    "error": "User cancelled operation",
                    "tool": name
                }

        # Execute with retry logic
        last_error = None
        for attempt in range(metadata.retry_count + 1):
            try:
                # Set up timeout
                if metadata.timeout:
                    result = await asyncio.wait_for(
                        self._execute_tool(metadata, arguments),
                        timeout=metadata.timeout
                    )
                else:
                    result = await self._execute_tool(metadata, arguments)

                return {
                    "success": True,
                    "result": result,
                    "tool": name
                }

            except asyncio.TimeoutError:
                last_error = f"Tool {name} timed out after {metadata.timeout}s"
            except Exception as e:
                last_error = str(e)

            # Wait before retry
            if attempt < metadata.retry_count:
                await asyncio.sleep(metadata.retry_delay)

        return {
            "success": False,
            "error": last_error,
            "tool": name,
            "attempts": metadata.retry_count + 1
        }

    async def _execute_tool(
        self,
        metadata: ToolMetadata,
        arguments: Dict[str, Any]
    ) -> Any:
        """Execute a tool function."""
        func = metadata.function

        if metadata.is_async:
            return await func(**arguments)
        else:
            # Run sync function in thread pool
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, lambda: func(**arguments))

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def __iter__(self):
        return iter(self._tools.values())


# Global default registry
_default_registry = ToolRegistry()


def get_default_registry() -> ToolRegistry:
    """Get the default tool registry."""
    return _default_registry


def register_tool(func: Callable = None, **kwargs):
    """Register a tool with the default registry."""
    return _default_registry.register(func, **kwargs)
