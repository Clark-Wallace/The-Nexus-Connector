"""
Session management for MeThinks.

Handles saving, loading, and resuming conversation sessions.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import os

from .models import (
    ProjectSpec,
    ConversationMessage,
    ConversationPhase,
    UserProfile,
)


# Default storage location - use app directory for portability
APP_DIR = Path(__file__).parent
METHINKS_DIR = APP_DIR / "data"
SESSIONS_DIR = METHINKS_DIR / "sessions"
CONFIG_FILE = METHINKS_DIR / "config.json"


def ensure_dirs():
    """Ensure MeThinks directories exist."""
    METHINKS_DIR.mkdir(parents=True, exist_ok=True)
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class Session:
    """
    A MeThinks conversation session.

    Tracks the conversation history, current phase,
    and builds up the ProjectSpec as data is extracted.
    """
    session_id: str
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # Conversation state
    phase: ConversationPhase = ConversationPhase.DISCOVER
    messages: List[ConversationMessage] = field(default_factory=list)

    # Building the spec
    spec: ProjectSpec = field(default_factory=lambda: ProjectSpec(name="Untitled"))

    # Extracted data (intermediate state before finalizing spec)
    extracted: Dict[str, Any] = field(default_factory=dict)

    # Session metadata
    is_complete: bool = False
    provider: str = "openai"  # AI provider used

    def add_message(
        self,
        role: str,
        content: str,
        extracted_data: Optional[Dict[str, Any]] = None
    ) -> ConversationMessage:
        """Add a message to the conversation."""
        msg = ConversationMessage(
            role=role,
            content=content,
            phase=self.phase,
            extracted_data=extracted_data or {},
        )
        self.messages.append(msg)
        self.updated_at = datetime.now()

        # Merge extracted data
        if extracted_data:
            self.extracted.update(extracted_data)

        return msg

    def advance_phase(self) -> ConversationPhase:
        """Advance to the next conversation phase."""
        phase_order = [
            ConversationPhase.DISCOVER,
            ConversationPhase.EXPLORE,
            ConversationPhase.CRYSTALLIZE,
            ConversationPhase.SCOPE,
            ConversationPhase.PROFILE,
            ConversationPhase.REFINE,
            ConversationPhase.COMPLETE,
        ]

        current_idx = phase_order.index(self.phase)
        if current_idx < len(phase_order) - 1:
            self.phase = phase_order[current_idx + 1]
            self.updated_at = datetime.now()

        if self.phase == ConversationPhase.COMPLETE:
            self.is_complete = True

        return self.phase

    def get_conversation_for_ai(self) -> List[Dict[str, str]]:
        """Get conversation history in format for AI APIs."""
        return [
            {"role": msg.role, "content": msg.content}
            for msg in self.messages
        ]

    def get_conversation_summary(self) -> str:
        """Generate a summary of the conversation for the spec."""
        key_points = []
        for msg in self.messages:
            if msg.role == "user" and len(msg.content) > 20:
                # Truncate long messages
                content = msg.content[:200] + "..." if len(msg.content) > 200 else msg.content
                key_points.append(f"- User: {content}")
        return "\n".join(key_points[-10:])  # Last 10 user messages

    def finalize_spec(self) -> ProjectSpec:
        """Finalize the project spec from extracted data."""
        self.spec.conversation_summary = self.get_conversation_summary()
        self.spec.updated_at = datetime.now()
        return self.spec

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "phase": self.phase.value,
            "messages": [m.to_dict() for m in self.messages],
            "spec": self.spec.to_dict(),
            "extracted": self.extracted,
            "is_complete": self.is_complete,
            "provider": self.provider,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Session":
        return cls(
            session_id=data["session_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            phase=ConversationPhase(data["phase"]),
            messages=[ConversationMessage.from_dict(m) for m in data.get("messages", [])],
            spec=ProjectSpec.from_dict(data.get("spec", {"name": "Untitled"})),
            extracted=data.get("extracted", {}),
            is_complete=data.get("is_complete", False),
            provider=data.get("provider", "openai"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "Session":
        return cls.from_dict(json.loads(json_str))


class SessionManager:
    """
    Manages session persistence and retrieval.
    """

    def __init__(self, sessions_dir: Optional[Path] = None):
        self.sessions_dir = sessions_dir or SESSIONS_DIR
        ensure_dirs()

    def _session_path(self, session_id: str) -> Path:
        """Get the file path for a session."""
        return self.sessions_dir / f"{session_id}.json"

    def _spec_path(self, session_id: str) -> Path:
        """Get the file path for the exported spec."""
        return self.sessions_dir / f"{session_id}_spec.md"

    def create_session(self, provider: str = "openai") -> Session:
        """Create a new session with unique ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_id = f"session_{timestamp}"

        session = Session(
            session_id=session_id,
            provider=provider,
        )

        self.save_session(session)
        return session

    def save_session(self, session: Session) -> Path:
        """Save a session to disk."""
        path = self._session_path(session.session_id)
        path.write_text(session.to_json())
        return path

    def load_session(self, session_id: str) -> Optional[Session]:
        """Load a session from disk."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        return Session.from_json(path.read_text())

    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its spec."""
        session_path = self._session_path(session_id)
        spec_path = self._spec_path(session_id)

        deleted = False
        if session_path.exists():
            session_path.unlink()
            deleted = True
        if spec_path.exists():
            spec_path.unlink()

        return deleted

    def list_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with summary info."""
        sessions = []
        for path in sorted(self.sessions_dir.glob("*.json"), reverse=True):
            if path.name.endswith("_spec.json"):
                continue  # Skip spec files

            try:
                session = Session.from_json(path.read_text())
                sessions.append({
                    "session_id": session.session_id,
                    "name": session.spec.name,
                    "phase": session.phase.value,
                    "is_complete": session.is_complete,
                    "created_at": session.created_at,
                    "updated_at": session.updated_at,
                    "message_count": len(session.messages),
                })
            except Exception:
                continue  # Skip corrupted files

        return sessions

    def get_recent_sessions(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get the most recent sessions."""
        return self.list_sessions()[:limit]

    def find_session_by_name(self, name: str) -> Optional[Session]:
        """Find a session by project name (partial match)."""
        name_lower = name.lower()
        for path in self.sessions_dir.glob("*.json"):
            if path.name.endswith("_spec.json"):
                continue

            try:
                session = Session.from_json(path.read_text())
                if name_lower in session.spec.name.lower():
                    return session
            except Exception:
                continue

        return None


class MeThinksConfig:
    """
    Global MeThinks configuration.
    """

    def __init__(self):
        ensure_dirs()
        self._config = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load config from disk."""
        if CONFIG_FILE.exists():
            try:
                return json.loads(CONFIG_FILE.read_text())
            except Exception:
                pass
        return self._defaults()

    def _defaults(self) -> Dict[str, Any]:
        """Default configuration."""
        return {
            "default_provider": "openai",
            "default_model": None,  # Use provider default
            "user_profile": {},  # Saved user profile
            "theme": "default",
        }

    def save(self):
        """Save config to disk."""
        CONFIG_FILE.write_text(json.dumps(self._config, indent=2))

    def get(self, key: str, default: Any = None) -> Any:
        """Get a config value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any):
        """Set a config value."""
        self._config[key] = value
        self.save()

    @property
    def default_provider(self) -> str:
        return self.get("default_provider", "openai")

    @default_provider.setter
    def default_provider(self, value: str):
        self.set("default_provider", value)

    def get_user_profile(self) -> Optional[UserProfile]:
        """Get saved user profile."""
        data = self.get("user_profile", {})
        if data:
            return UserProfile.from_dict(data)
        return None

    def save_user_profile(self, profile: UserProfile):
        """Save user profile for reuse."""
        self.set("user_profile", profile.to_dict())
