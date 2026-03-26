"""
Unified tool executor for all AI providers.

Integrates with the ToolRegistry for custom tools while providing
built-in file and command tools.
"""

import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime

from .tool_registry import ToolRegistry, tool, ToolMetadata


class ToolExecutor:
    """
    Executes tools/functions in a unified way across all AI providers.

    This handles file operations, code execution, and other tools
    that AIs might need to complete tasks.

    The executor integrates with ToolRegistry for custom tools while
    providing built-in tools for common operations.
    """

    def __init__(
        self,
        workspace: Optional[Path] = None,
        safe_mode: bool = True,
        registry: Optional[ToolRegistry] = None,
    ):
        """
        Initialize tool executor.

        Args:
            workspace: Working directory for file operations
            safe_mode: If True, confirms destructive operations
            registry: Optional ToolRegistry for custom tools. If None, creates new one.
        """
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.safe_mode = safe_mode
        self.executed_operations: List[Dict[str, Any]] = []

        # Initialize or use provided registry
        self.registry = registry if registry is not None else ToolRegistry()

        # Register built-in tools
        self._register_builtin_tools()

        # Legacy tools dict for backward compatibility
        self._legacy_tools: Dict[str, Callable] = {}

    @property
    def tools(self) -> Dict[str, Callable]:
        """
        Get dict of tool names to functions (backward compatibility).
        """
        result = {}
        for metadata in self.registry:
            result[metadata.name] = metadata.function
        result.update(self._legacy_tools)
        return result

    def _register_builtin_tools(self) -> None:
        """Register built-in tools with the registry."""

        @self.registry.register(
            description="Create a new file with specified content",
            category="file",
        )
        def create_file(path: str, content: str = "") -> Dict[str, Any]:
            """
            Create a new file with content.

            Args:
                path: Path to the file to create
                content: Content to write to the file
            """
            return self._create_file(path, content)

        @self.registry.register(
            description="Write content to a file (overwrites existing)",
            category="file",
        )
        def write_file(path: str, content: str = "") -> Dict[str, Any]:
            """
            Write content to a file, overwriting if it exists.

            Args:
                path: Path to the file
                content: Content to write
            """
            return self._write_file(path, content)

        @self.registry.register(
            description="Read content from a file",
            category="file",
        )
        def read_file(path: str) -> Dict[str, Any]:
            """
            Read content from a file.

            Args:
                path: Path to the file to read
            """
            return self._read_file(path)

        @self.registry.register(
            description="Edit a file by replacing content",
            category="file",
        )
        def edit_file(path: str, old_content: str, new_content: str) -> Dict[str, Any]:
            """
            Edit a file by replacing content.

            Args:
                path: Path to the file to edit
                old_content: Content to find and replace
                new_content: New content to insert
            """
            return self._edit_file(path, old_content, new_content)

        @self.registry.register(
            description="Delete a file (moves to trash in safe mode)",
            category="file",
            destructive=True,
        )
        def delete_file(path: str) -> Dict[str, Any]:
            """
            Delete a file. In safe mode, moves to trash instead.

            Args:
                path: Path to the file to delete
            """
            return self._delete_file(path)

        @self.registry.register(
            description="List files in a directory",
            category="file",
        )
        def list_files(directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
            """
            List files in a directory.

            Args:
                directory: Directory path (default: current directory)
                pattern: File pattern to match (default: *)
            """
            return self._list_files(directory, pattern)

        @self.registry.register(
            description="Execute a shell command",
            category="system",
            destructive=True,
        )
        async def execute_command(command: str, shell: bool = True) -> Dict[str, Any]:
            """
            Execute a shell command.

            Args:
                command: Command to execute
                shell: Whether to run through shell (default: True)
            """
            return await self._execute_command(command, shell)

        @self.registry.register(
            description="Search for files matching a pattern",
            category="file",
        )
        def search_files(pattern: str, directory: str = ".") -> Dict[str, Any]:
            """
            Search for files matching a pattern recursively.

            Args:
                pattern: File pattern to match (e.g., "*.py")
                directory: Directory to search in (default: current)
            """
            return self._search_files(pattern, directory)

    def register_tool(
        self,
        func: Callable = None,
        **kwargs
    ) -> Callable:
        """
        Register a custom tool.

        Can be used as a decorator:
            @executor.register_tool(description="My tool")
            def my_tool(x: int) -> str:
                ...

        Or directly:
            executor.register_tool(some_func, description="Some tool")
        """
        return self.registry.register(func, **kwargs)

    def register_tools(self, tools: List[Callable]) -> None:
        """Register multiple tools at once."""
        for func in tools:
            self.registry.register(func)

    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        confirm_callback: Optional[Callable[[ToolMetadata], bool]] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            confirm_callback: Optional callback for destructive operations

        Returns:
            Result of tool execution
        """
        # Normalize common argument name variations from different AI models
        arguments = self._normalize_arguments(tool_name, arguments)
        # Check registry first
        if tool_name in self.registry:
            # Use registry execution (handles retries, timeouts, etc.)
            operation = {
                "tool": tool_name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat()
            }

            result = await self.registry.execute(
                tool_name,
                arguments,
                confirm_callback=confirm_callback
            )

            operation["result"] = result
            operation["success"] = result.get("success", False)
            self.executed_operations.append(operation)

            return result

        # Check legacy tools
        if tool_name in self._legacy_tools:
            return await self._execute_legacy_tool(tool_name, arguments)

        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
            "available_tools": list(self.tools.keys())
        }

    async def _execute_legacy_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a legacy tool (for backward compatibility)."""
        try:
            operation = {
                "tool": tool_name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat()
            }

            tool_func = self._legacy_tools[tool_name]
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)

            operation["result"] = result
            operation["success"] = result.get("success", True)
            self.executed_operations.append(operation)

            return result

        except Exception as e:
            error_result = {
                "success": False,
                "error": str(e),
                "tool": tool_name,
                "arguments": arguments
            }
            self.executed_operations.append({
                "tool": tool_name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat(),
                "result": error_result,
                "success": False
            })
            return error_result

    def get_tool_definitions(self, format: str = "openai") -> List[Dict[str, Any]]:
        """
        Get tool definitions for AI providers.

        Args:
            format: "openai" or "anthropic"

        Returns:
            List of tool definitions
        """
        return self.registry.get_tool_definitions(format)

    # ========== Built-in tool implementations ==========

    def _normalize_arguments(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize argument names that different AI models use for the same thing.

        Models sometimes use 'filename' instead of 'path', 'file_path' instead of 'path',
        'text' instead of 'content', etc. This maps common variations to the canonical names.
        """
        args = dict(arguments)  # don't mutate the original

        # Normalize path arguments for file tools
        file_tools = {"create_file", "write_file", "read_file", "edit_file", "delete_file"}
        if tool_name in file_tools:
            if "path" not in args:
                for alt in ("filename", "file_path", "filepath", "file_name", "name"):
                    if alt in args:
                        args["path"] = args.pop(alt)
                        break

        # Normalize content arguments for write tools
        write_tools = {"create_file", "write_file"}
        if tool_name in write_tools:
            if "content" not in args:
                for alt in ("text", "data", "file_content", "body", "code", "source", "contents"):
                    if alt in args:
                        args["content"] = args.pop(alt)
                        break
            # If content is still missing, default to empty string
            # (some models call write_file with just a path)
            if "content" not in args:
                args["content"] = ""

        # Normalize command arguments
        if tool_name == "execute_command":
            if "command" not in args:
                for alt in ("cmd", "shell_command", "script", "bash"):
                    if alt in args:
                        args["command"] = args.pop(alt)
                        break

        return args

    def _create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file."""
        try:
            file_path = self._resolve_path(path)

            if file_path.exists() and self.safe_mode:
                return {
                    "success": False,
                    "error": f"File already exists: {path}",
                    "exists": True
                }

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')

            return {
                "success": True,
                "path": str(file_path),
                "size": len(content),
                "created": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    def _write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file (overwrites existing)."""
        try:
            file_path = self._resolve_path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding='utf-8')

            return {
                "success": True,
                "path": str(file_path),
                "size": len(content),
                "overwritten": True
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    def _read_file(self, path: str) -> Dict[str, Any]:
        """Read content from a file."""
        try:
            file_path = self._resolve_path(path)

            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                    "exists": False
                }

            content = file_path.read_text(encoding='utf-8')

            return {
                "success": True,
                "path": str(file_path),
                "content": content,
                "size": len(content),
                "lines": content.count('\n') + 1
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    def _edit_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Edit a file by replacing content."""
        try:
            file_path = self._resolve_path(path)

            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                    "exists": False
                }

            content = file_path.read_text(encoding='utf-8')

            if old_content not in content:
                return {
                    "success": False,
                    "error": "Old content not found in file",
                    "path": path
                }

            new_file_content = content.replace(old_content, new_content)
            file_path.write_text(new_file_content, encoding='utf-8')

            return {
                "success": True,
                "path": str(file_path),
                "replacements": content.count(old_content),
                "size": len(new_file_content)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    def _delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file."""
        try:
            file_path = self._resolve_path(path)

            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"File not found: {path}",
                    "exists": False
                }

            if self.safe_mode:
                trash_dir = self.workspace / ".nexus_trash"
                trash_dir.mkdir(exist_ok=True)

                trash_path = trash_dir / f"{file_path.name}.{datetime.now().timestamp()}"
                file_path.rename(trash_path)

                return {
                    "success": True,
                    "path": str(file_path),
                    "moved_to_trash": str(trash_path)
                }
            else:
                file_path.unlink()

                return {
                    "success": True,
                    "path": str(file_path),
                    "deleted": True
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "path": path
            }

    def _list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """List files in a directory."""
        try:
            dir_path = self._resolve_path(directory)

            if not dir_path.exists():
                return {
                    "success": False,
                    "error": f"Directory not found: {directory}",
                    "exists": False
                }

            files = []
            for item in dir_path.glob(pattern):
                files.append({
                    "name": item.name,
                    "path": str(item.relative_to(self.workspace)),
                    "is_dir": item.is_dir(),
                    "size": item.stat().st_size if item.is_file() else None
                })

            return {
                "success": True,
                "directory": str(dir_path),
                "pattern": pattern,
                "files": files,
                "count": len(files)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "directory": directory
            }

    async def _execute_command(self, command: str, shell: bool = True) -> Dict[str, Any]:
        """Execute a shell command."""
        try:
            dangerous_patterns = ['rm -rf', 'del /f', 'format', 'mkfs', ':(){']
            if self.safe_mode and any(p in command.lower() for p in dangerous_patterns):
                return {
                    "success": False,
                    "error": "Dangerous command blocked in safe mode",
                    "command": command
                }

            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.workspace
            )

            stdout, stderr = await process.communicate()

            return {
                "success": process.returncode == 0,
                "command": command,
                "stdout": stdout.decode('utf-8'),
                "stderr": stderr.decode('utf-8'),
                "return_code": process.returncode
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "command": command
            }

    def _search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Search for files matching a pattern."""
        try:
            dir_path = self._resolve_path(directory)
            matches = []

            for file_path in dir_path.rglob(pattern):
                matches.append(str(file_path.relative_to(self.workspace)))

            return {
                "success": True,
                "pattern": pattern,
                "directory": directory,
                "matches": matches,
                "count": len(matches)
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "pattern": pattern
            }

    def _resolve_path(self, path: str) -> Path:
        """Resolve path relative to workspace."""
        path_obj = Path(path)
        if path_obj.is_absolute():
            return path_obj
        return self.workspace / path

    # ========== History and state ==========

    def get_executed_operations(self) -> List[Dict[str, Any]]:
        """Get list of executed operations."""
        return self.executed_operations.copy()

    def get_created_files(self) -> List[str]:
        """Get list of created files."""
        created = []
        for op in self.executed_operations:
            if op["tool"] == "create_file" and op.get("success"):
                created.append(op["arguments"]["path"])
        return created

    def get_modified_files(self) -> List[str]:
        """Get list of modified files."""
        modified = []
        for op in self.executed_operations:
            if op["tool"] in ["write_file", "edit_file"] and op.get("success"):
                modified.append(op["arguments"]["path"])
        return modified

    def clear_history(self) -> None:
        """Clear execution history."""
        self.executed_operations.clear()

    # ========== Legacy methods for backward compatibility ==========

    # These methods are kept for backward compatibility
    def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file (legacy method)."""
        return self._create_file(path, content)

    def write_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """Write to a file (legacy method)."""
        return self._write_file(path, content)

    def read_file(self, path: str) -> Dict[str, Any]:
        """Read a file (legacy method)."""
        return self._read_file(path)

    def edit_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
        """Edit a file (legacy method)."""
        return self._edit_file(path, old_content, new_content)

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Delete a file (legacy method)."""
        return self._delete_file(path)

    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """List files (legacy method)."""
        return self._list_files(directory, pattern)

    async def execute_command(self, command: str, shell: bool = True) -> Dict[str, Any]:
        """Execute command (legacy method)."""
        return await self._execute_command(command, shell)

    def search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
        """Search files (legacy method)."""
        return self._search_files(pattern, directory)
