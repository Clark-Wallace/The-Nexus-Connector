"""
Task execution result class.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .execution_log import ExecutionLog


@dataclass
class TaskResult:
    """
    Result of task execution.

    This provides a unified format for task results across all AI providers.
    """
    success: bool = False
    content: str = ""
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    commands_executed: List[Dict[str, Any]] = field(default_factory=list)
    tokens_used: int = 0
    cost: float = 0.0
    duration: float = 0.0
    iterations: int = 0
    error: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_log: Optional["ExecutionLog"] = field(default=None, repr=False)
    
    def __str__(self) -> str:
        """String representation."""
        status = "✅ Success" if self.success else "❌ Failed"
        return (
            f"TaskResult({status}, "
            f"files_created={len(self.files_created)}, "
            f"files_modified={len(self.files_modified)}, "
            f"duration={self.duration:.2f}s)"
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "content": self.content,
            "files_created": self.files_created,
            "files_modified": self.files_modified,
            "files_deleted": self.files_deleted,
            "commands_executed": self.commands_executed,
            "tokens_used": self.tokens_used,
            "cost": self.cost,
            "duration": self.duration,
            "iterations": self.iterations,
            "error": self.error,
            "provider": self.provider,
            "model": self.model,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }
    
    def add_file_created(self, filepath: str):
        """Add a created file to the result."""
        if filepath not in self.files_created:
            self.files_created.append(filepath)
    
    def add_file_modified(self, filepath: str):
        """Add a modified file to the result."""
        if filepath not in self.files_modified:
            self.files_modified.append(filepath)
    
    def add_command(self, command: str, output: str = "", success: bool = True):
        """Add an executed command to the result."""
        self.commands_executed.append({
            "command": command,
            "output": output,
            "success": success,
            "timestamp": datetime.now().isoformat()
        })