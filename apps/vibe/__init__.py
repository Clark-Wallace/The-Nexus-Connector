"""
Vibe Code - Interactive AI coding assistant.

A friendly interface for building with AI, featuring:
- Sparks: Contextual next-step suggestions
- Chill Mode: Explained options with reasoning
- Mr. MeThinks: Project idea generator

Available interfaces:
- TUI: Terminal UI with clickable panels (nexus vibe --tui)
- Web: Gradio-based web interface (nexus vibe --web)
- CLI: Text-based interactive mode (nexus vibe)
"""

from .sparks import generate_sparks, format_sparks_chill, format_sparks_text
from .methinks import MrMeThinks

__all__ = [
    "generate_sparks",
    "format_sparks_chill",
    "format_sparks_text",
    "MrMeThinks",
]
