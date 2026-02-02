"""
Data models for MeThinks application.

These models capture all the context needed to generate
AI-ready project specifications.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Literal, Optional, Any
from enum import Enum
import json


class SkillLevel(str, Enum):
    """User skill level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class ExplanationPreference(str, Enum):
    """How much explanation the user wants."""
    GUIDED = "guided"      # Explain everything
    BALANCED = "balanced"  # Some explanation
    MINIMAL = "minimal"    # Just the code


class FeaturePriority(str, Enum):
    """Feature priority levels."""
    MUST = "must"      # MVP - required
    SHOULD = "should"  # v1.0 - important
    NICE = "nice"      # Future - nice to have


class ConversationPhase(str, Enum):
    """Phases of the MeThinks conversation."""
    DISCOVER = "discover"      # What interests you?
    EXPLORE = "explore"        # Tell me more...
    CRYSTALLIZE = "crystallize"  # So you want to build X?
    SCOPE = "scope"            # What's essential?
    PROFILE = "profile"        # What's your experience?
    REFINE = "refine"          # Anything to adjust?
    COMPLETE = "complete"      # Done


@dataclass
class UserProfile:
    """
    Captures user's background and preferences.

    This helps downstream AIs tailor their responses
    to the user's skill level and learning goals.
    """
    skill_level: SkillLevel = SkillLevel.INTERMEDIATE
    known_languages: List[str] = field(default_factory=list)
    known_frameworks: List[str] = field(default_factory=list)
    learning_goals: List[str] = field(default_factory=list)
    time_commitment: Optional[str] = None  # e.g., "5 hours/week"
    explanation_preference: ExplanationPreference = ExplanationPreference.BALANCED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_level": self.skill_level.value,
            "known_languages": self.known_languages,
            "known_frameworks": self.known_frameworks,
            "learning_goals": self.learning_goals,
            "time_commitment": self.time_commitment,
            "explanation_preference": self.explanation_preference.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserProfile":
        return cls(
            skill_level=SkillLevel(data.get("skill_level", "intermediate")),
            known_languages=data.get("known_languages", []),
            known_frameworks=data.get("known_frameworks", []),
            learning_goals=data.get("learning_goals", []),
            time_commitment=data.get("time_commitment"),
            explanation_preference=ExplanationPreference(
                data.get("explanation_preference", "balanced")
            ),
        )


@dataclass
class Feature:
    """
    A single feature of the project.

    Includes rationale so downstream AIs understand
    why this feature matters.
    """
    name: str
    description: str
    priority: FeaturePriority = FeaturePriority.SHOULD
    rationale: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "priority": self.priority.value,
            "rationale": self.rationale,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Feature":
        return cls(
            name=data["name"],
            description=data["description"],
            priority=FeaturePriority(data.get("priority", "should")),
            rationale=data.get("rationale", ""),
        )


@dataclass
class TechnicalRequirements:
    """Technical specifications for the project."""
    language: str = "Python"
    language_version: Optional[str] = "3.11+"
    frameworks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    environment: str = "local"  # local, docker, cloud

    def to_dict(self) -> Dict[str, Any]:
        return {
            "language": self.language,
            "language_version": self.language_version,
            "frameworks": self.frameworks,
            "dependencies": self.dependencies,
            "environment": self.environment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechnicalRequirements":
        return cls(
            language=data.get("language", "Python"),
            language_version=data.get("language_version", "3.11+"),
            frameworks=data.get("frameworks", []),
            dependencies=data.get("dependencies", []),
            environment=data.get("environment", "local"),
        )


@dataclass
class ProjectSpec:
    """
    Complete project specification.

    This is the main output of MeThinks - a structured document
    containing everything a downstream AI needs to understand
    and execute the project.
    """
    # Identity
    name: str
    tagline: str = ""
    slug: str = ""  # URL-safe identifier

    # Vision
    vision: str = ""
    problem_statement: str = ""
    target_user: str = ""

    # User context
    user_profile: UserProfile = field(default_factory=UserProfile)

    # Technical
    technical: TechnicalRequirements = field(default_factory=TechnicalRequirements)

    # Features
    features: List[Feature] = field(default_factory=list)

    # Architecture
    architecture_decisions: Dict[str, str] = field(default_factory=dict)

    # Boundaries
    constraints: List[str] = field(default_factory=list)
    anti_goals: List[str] = field(default_factory=list)  # What this is NOT

    # Success
    success_criteria: List[str] = field(default_factory=list)

    # Context
    conversation_summary: str = ""
    key_insights: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    methinks_version: str = "0.1.0"

    def __post_init__(self):
        if not self.slug:
            self.slug = self._generate_slug(self.name)

    @staticmethod
    def _generate_slug(name: str) -> str:
        """Generate URL-safe slug from name."""
        import re
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

    @property
    def must_have_features(self) -> List[Feature]:
        return [f for f in self.features if f.priority == FeaturePriority.MUST]

    @property
    def should_have_features(self) -> List[Feature]:
        return [f for f in self.features if f.priority == FeaturePriority.SHOULD]

    @property
    def nice_to_have_features(self) -> List[Feature]:
        return [f for f in self.features if f.priority == FeaturePriority.NICE]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "tagline": self.tagline,
            "slug": self.slug,
            "vision": self.vision,
            "problem_statement": self.problem_statement,
            "target_user": self.target_user,
            "user_profile": self.user_profile.to_dict(),
            "technical": self.technical.to_dict(),
            "features": [f.to_dict() for f in self.features],
            "architecture_decisions": self.architecture_decisions,
            "constraints": self.constraints,
            "anti_goals": self.anti_goals,
            "success_criteria": self.success_criteria,
            "conversation_summary": self.conversation_summary,
            "key_insights": self.key_insights,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "methinks_version": self.methinks_version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectSpec":
        return cls(
            name=data["name"],
            tagline=data.get("tagline", ""),
            slug=data.get("slug", ""),
            vision=data.get("vision", ""),
            problem_statement=data.get("problem_statement", ""),
            target_user=data.get("target_user", ""),
            user_profile=UserProfile.from_dict(data.get("user_profile", {})),
            technical=TechnicalRequirements.from_dict(data.get("technical", {})),
            features=[Feature.from_dict(f) for f in data.get("features", [])],
            architecture_decisions=data.get("architecture_decisions", {}),
            constraints=data.get("constraints", []),
            anti_goals=data.get("anti_goals", []),
            success_criteria=data.get("success_criteria", []),
            conversation_summary=data.get("conversation_summary", ""),
            key_insights=data.get("key_insights", []),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now(),
            methinks_version=data.get("methinks_version", "0.1.0"),
        )

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> "ProjectSpec":
        return cls.from_dict(json.loads(json_str))


@dataclass
class ConversationMessage:
    """A single message in the conversation."""
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    phase: Optional[ConversationPhase] = None
    extracted_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "phase": self.phase.value if self.phase else None,
            "extracted_data": self.extracted_data,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationMessage":
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
            phase=ConversationPhase(data["phase"]) if data.get("phase") else None,
            extracted_data=data.get("extracted_data", {}),
        )
