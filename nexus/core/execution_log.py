"""
Execution Log - Structured logging for task execution.

Provides detailed tracking of all operations during task execution,
including messages, tool calls, file operations, and metrics.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from enum import Enum


class LogEventType(Enum):
    """Types of events in the execution log."""
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    COMMAND_EXECUTED = "command_executed"
    ERROR = "error"
    WARNING = "warning"
    STEP_START = "step_start"
    STEP_END = "step_end"
    TASK_START = "task_start"
    TASK_END = "task_end"
    CHECKPOINT = "checkpoint"
    ROLLBACK = "rollback"


@dataclass
class LogEvent:
    """A single event in the execution log."""
    type: LogEventType
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    tokens: Optional[int] = None
    cost: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "type": self.type.value,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "duration_ms": self.duration_ms,
            "tokens": self.tokens,
            "cost": self.cost,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogEvent":
        """Create from dictionary."""
        return cls(
            type=LogEventType(data["type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            data=data.get("data", {}),
            duration_ms=data.get("duration_ms"),
            tokens=data.get("tokens"),
            cost=data.get("cost"),
        )


@dataclass
class ExecutionMetrics:
    """Aggregated metrics for task execution."""
    total_messages: int = 0
    total_tool_calls: int = 0
    total_tokens: int = 0
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_cost: float = 0.0
    total_duration_ms: float = 0.0
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    commands_executed: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    steps_completed: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class ExecutionLog:
    """
    Structured execution log for task execution.

    Tracks all operations, messages, tool calls, and metrics
    during a task execution session.

    Usage:
        log = ExecutionLog(task="Create a web server")

        # Log events as they happen
        log.log_message_sent("Create a Flask app")
        log.log_message_received("I'll create a Flask application...")
        log.log_tool_call("create_file", {"path": "app.py", "content": "..."})
        log.log_tool_result("create_file", {"success": True})

        # Get summary
        metrics = log.get_metrics()
        print(f"Total tokens: {metrics.total_tokens}")

        # Export log
        log.save("execution.json")
    """

    def __init__(
        self,
        task: str,
        session_id: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize execution log.

        Args:
            task: Task description
            session_id: Session identifier
            provider: AI provider name
            model: Model name
        """
        self.task = task
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.provider = provider
        self.model = model
        self.started_at = datetime.now()
        self.ended_at: Optional[datetime] = None
        self.events: List[LogEvent] = []
        self._metrics = ExecutionMetrics()

        # Log task start
        self._add_event(LogEventType.TASK_START, {
            "task": task,
            "session_id": session_id,
            "provider": provider,
            "model": model,
        })

    def _add_event(
        self,
        event_type: LogEventType,
        data: Dict[str, Any],
        duration_ms: Optional[float] = None,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
    ) -> LogEvent:
        """Add an event to the log."""
        event = LogEvent(
            type=event_type,
            timestamp=datetime.now(),
            data=data,
            duration_ms=duration_ms,
            tokens=tokens,
            cost=cost,
        )
        self.events.append(event)

        # Update metrics
        if tokens:
            self._metrics.total_tokens += tokens
        if cost:
            self._metrics.total_cost += cost
        if duration_ms:
            self._metrics.total_duration_ms += duration_ms

        return event

    def log_message_sent(
        self,
        content: str,
        role: str = "user",
        tokens: Optional[int] = None,
    ) -> LogEvent:
        """Log a message sent to the AI."""
        self._metrics.total_messages += 1
        if tokens:
            self._metrics.prompt_tokens += tokens
        return self._add_event(
            LogEventType.MESSAGE_SENT,
            {"role": role, "content": content[:500]},  # Truncate for log
            tokens=tokens,
        )

    def log_message_received(
        self,
        content: str,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
        duration_ms: Optional[float] = None,
    ) -> LogEvent:
        """Log a message received from the AI."""
        self._metrics.total_messages += 1
        if tokens:
            self._metrics.completion_tokens += tokens
        return self._add_event(
            LogEventType.MESSAGE_RECEIVED,
            {"content": content[:500]},  # Truncate for log
            duration_ms=duration_ms,
            tokens=tokens,
            cost=cost,
        )

    def log_tool_call(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        tool_id: Optional[str] = None,
    ) -> LogEvent:
        """Log a tool call."""
        self._metrics.total_tool_calls += 1
        return self._add_event(
            LogEventType.TOOL_CALL,
            {
                "tool": tool_name,
                "arguments": arguments,
                "tool_id": tool_id,
            }
        )

    def log_tool_result(
        self,
        tool_name: str,
        result: Dict[str, Any],
        success: bool = True,
        duration_ms: Optional[float] = None,
    ) -> LogEvent:
        """Log a tool result."""
        # Track file operations
        if success:
            if tool_name == "create_file" and "path" in result:
                self._metrics.files_created.append(result.get("path", ""))
            elif tool_name in ("write_file", "edit_file") and "path" in result:
                self._metrics.files_modified.append(result.get("path", ""))
            elif tool_name == "delete_file" and "path" in result:
                self._metrics.files_deleted.append(result.get("path", ""))
            elif tool_name == "execute_command":
                cmd = result.get("command", "")
                self._metrics.commands_executed.append(cmd[:100])

        return self._add_event(
            LogEventType.TOOL_RESULT,
            {
                "tool": tool_name,
                "success": success,
                "result_summary": self._summarize_result(result),
            },
            duration_ms=duration_ms,
        )

    def log_error(
        self,
        error: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> LogEvent:
        """Log an error."""
        self._metrics.errors.append(error[:200])
        return self._add_event(
            LogEventType.ERROR,
            {"error": error, "context": context or {}},
        )

    def log_warning(
        self,
        warning: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> LogEvent:
        """Log a warning."""
        return self._add_event(
            LogEventType.WARNING,
            {"warning": warning, "context": context or {}},
        )

    def log_step_start(self, step: int, description: str = "") -> LogEvent:
        """Log the start of an execution step."""
        return self._add_event(
            LogEventType.STEP_START,
            {"step": step, "description": description},
        )

    def log_step_end(
        self,
        step: int,
        success: bool = True,
        duration_ms: Optional[float] = None,
    ) -> LogEvent:
        """Log the end of an execution step."""
        if success:
            self._metrics.steps_completed += 1
        return self._add_event(
            LogEventType.STEP_END,
            {"step": step, "success": success},
            duration_ms=duration_ms,
        )

    def log_checkpoint(self, checkpoint_id: str, description: str = "") -> LogEvent:
        """Log a checkpoint (e.g., git commit before changes)."""
        return self._add_event(
            LogEventType.CHECKPOINT,
            {"checkpoint_id": checkpoint_id, "description": description},
        )

    def log_rollback(self, checkpoint_id: str, reason: str = "") -> LogEvent:
        """Log a rollback to a checkpoint."""
        return self._add_event(
            LogEventType.ROLLBACK,
            {"checkpoint_id": checkpoint_id, "reason": reason},
        )

    def finish(self, success: bool = True) -> None:
        """Mark the task as finished."""
        self.ended_at = datetime.now()
        self._add_event(
            LogEventType.TASK_END,
            {
                "success": success,
                "duration_seconds": (self.ended_at - self.started_at).total_seconds(),
            },
        )

    def get_metrics(self) -> ExecutionMetrics:
        """Get aggregated execution metrics."""
        return self._metrics

    def get_events(
        self,
        event_type: Optional[LogEventType] = None,
    ) -> List[LogEvent]:
        """Get events, optionally filtered by type."""
        if event_type:
            return [e for e in self.events if e.type == event_type]
        return self.events.copy()

    def get_tool_calls(self) -> List[Dict[str, Any]]:
        """Get all tool calls with their results."""
        calls = []
        for event in self.events:
            if event.type == LogEventType.TOOL_CALL:
                call = {"call": event.data}
                # Find matching result
                for e in self.events:
                    if (e.type == LogEventType.TOOL_RESULT and
                        e.data.get("tool") == event.data.get("tool")):
                        call["result"] = e.data
                        break
                calls.append(call)
        return calls

    def _summarize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary of a result for logging."""
        summary = {}
        for key, value in result.items():
            if key == "content" and isinstance(value, str) and len(value) > 200:
                summary[key] = value[:200] + "..."
            elif isinstance(value, (str, int, float, bool)):
                summary[key] = value
            elif isinstance(value, list):
                summary[key] = f"[{len(value)} items]"
            elif isinstance(value, dict):
                summary[key] = f"{{{len(value)} keys}}"
            else:
                summary[key] = str(type(value).__name__)
        return summary

    def to_dict(self) -> Dict[str, Any]:
        """Convert log to dictionary for serialization."""
        return {
            "task": self.task,
            "session_id": self.session_id,
            "provider": self.provider,
            "model": self.model,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "metrics": self._metrics.to_dict(),
            "events": [e.to_dict() for e in self.events],
        }

    def save(self, path: str) -> None:
        """Save log to a JSON file."""
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str) -> "ExecutionLog":
        """Load log from a JSON file."""
        with open(path) as f:
            data = json.load(f)

        log = cls(
            task=data["task"],
            session_id=data["session_id"],
            provider=data.get("provider"),
            model=data.get("model"),
        )

        log.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("ended_at"):
            log.ended_at = datetime.fromisoformat(data["ended_at"])

        log.events = [LogEvent.from_dict(e) for e in data["events"]]

        # Restore metrics
        metrics_data = data.get("metrics", {})
        log._metrics = ExecutionMetrics(**{
            k: v for k, v in metrics_data.items()
            if k in ExecutionMetrics.__dataclass_fields__
        })

        return log

    def __repr__(self) -> str:
        return (
            f"ExecutionLog(task='{self.task[:30]}...', "
            f"events={len(self.events)}, "
            f"tokens={self._metrics.total_tokens})"
        )
