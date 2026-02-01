"""
Unified tool executor for all AI providers.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime


class ToolExecutor:
    """
    Executes tools/functions in a unified way across all AI providers.
    
    This handles file operations, code execution, and other tools
    that AIs might need to complete tasks.
    """
    
    def __init__(self, workspace: Optional[Path] = None, safe_mode: bool = True):
        """
        Initialize tool executor.
        
        Args:
            workspace: Working directory for file operations
            safe_mode: If True, confirms destructive operations
        """
        self.workspace = Path(workspace) if workspace else Path.cwd()
        self.safe_mode = safe_mode
        self.executed_operations = []
        self.tools = self._register_builtin_tools()
    
    def _register_builtin_tools(self) -> Dict[str, Callable]:
        """Register built-in tools."""
        return {
            "create_file": self.create_file,
            "write_file": self.write_file,
            "read_file": self.read_file,
            "edit_file": self.edit_file,
            "delete_file": self.delete_file,
            "list_files": self.list_files,
            "execute_command": self.execute_command,
            "search_files": self.search_files,
        }
    
    async def execute(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Arguments for the tool
            
        Returns:
            Result of tool execution
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        try:
            # Record operation
            operation = {
                "tool": tool_name,
                "arguments": arguments,
                "timestamp": datetime.now().isoformat()
            }
            
            # Execute tool
            tool_func = self.tools[tool_name]
            if asyncio.iscoroutinefunction(tool_func):
                result = await tool_func(**arguments)
            else:
                result = tool_func(**arguments)
            
            # Record result
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
            
            operation["result"] = error_result
            operation["success"] = False
            self.executed_operations.append(operation)
            
            return error_result
    
    def create_file(self, path: str, content: str = "") -> Dict[str, Any]:
        """Create a new file."""
        try:
            file_path = self._resolve_path(path)
            
            # Check if file exists
            if file_path.exists() and self.safe_mode:
                return {
                    "success": False,
                    "error": f"File already exists: {path}",
                    "exists": True
                }
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
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
    
    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Write content to a file (overwrites existing)."""
        try:
            file_path = self._resolve_path(path)
            
            # Create parent directories
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write content
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
    
    def read_file(self, path: str) -> Dict[str, Any]:
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
    
    def edit_file(self, path: str, old_content: str, new_content: str) -> Dict[str, Any]:
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
            
            # Replace content
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
    
    def delete_file(self, path: str) -> Dict[str, Any]:
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
                # In safe mode, move to trash instead of deleting
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
    
    def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
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
    
    async def execute_command(self, command: str, shell: bool = True) -> Dict[str, Any]:
        """Execute a shell command."""
        try:
            if self.safe_mode and any(dangerous in command.lower() for dangerous in ['rm -rf', 'del /f', 'format']):
                return {
                    "success": False,
                    "error": "Dangerous command blocked in safe mode",
                    "command": command
                }
            
            # Execute command
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
    
    def search_files(self, pattern: str, directory: str = ".") -> Dict[str, Any]:
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
    
    def clear_history(self):
        """Clear execution history."""
        self.executed_operations.clear()