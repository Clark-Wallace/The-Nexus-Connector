"""
MeThinks - AI-powered project idea and specification generator.

Generates project ideas AND produces AI-ready specification documents
for downstream tools like Claude Code.
"""

__version__ = "0.1.0"

from .models import ProjectSpec, UserProfile, Feature
from .session import Session, SessionManager
from .generator import SpecGenerator

__all__ = [
    "ProjectSpec",
    "UserProfile",
    "Feature",
    "Session",
    "SessionManager",
    "SpecGenerator",
]
