"""
Conversation engine for MeThinks.

Manages the guided conversation flow that extracts
project requirements from users.
"""

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from abc import ABC, abstractmethod

from .models import (
    ConversationPhase,
    ProjectSpec,
    UserProfile,
    Feature,
    FeaturePriority,
    SkillLevel,
    ExplanationPreference,
    TechnicalRequirements,
)
from .session import Session


# System prompt for MeThinks personality
METHINKS_SYSTEM_PROMPT = """You are MeThinks, a friendly AI assistant that helps people discover and define software project ideas.

Your personality:
- Warm and encouraging, especially to beginners
- Curious and explorative - you help users discover what they really want
- Practical - you guide toward achievable projects
- You use the thinking emoji 🤔 naturally in conversation

Your job is to have a natural conversation that:
1. Discovers what interests the user
2. Explores their motivations and constraints
3. Crystallizes a concrete project idea
4. Defines scope and priorities
5. Understands their technical background

IMPORTANT: Keep responses conversational and concise. Ask one or two questions at a time, not interrogation-style lists.

You will receive instructions about what phase of the conversation you're in and what information to extract."""


@dataclass
class PhaseResult:
    """Result of processing a conversation phase."""
    response: str  # AI's response to show user
    extracted_data: Dict[str, Any]  # Structured data extracted
    should_advance: bool  # Whether to move to next phase
    phase_complete: bool  # Whether this phase achieved its goal


class ConversationPhaseHandler(ABC):
    """Base class for conversation phase handlers."""

    phase: ConversationPhase
    goal: str
    extraction_keys: List[str]

    @abstractmethod
    def get_system_addition(self, context: Dict[str, Any]) -> str:
        """Get additional system prompt for this phase."""
        pass

    @abstractmethod
    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        """Get the initial message for this phase."""
        pass

    @abstractmethod
    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        """Check if this phase has gathered enough information."""
        pass

    def extract_data(self, ai_response: str, user_input: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured data from the conversation. Override for custom extraction."""
        return {}


class DiscoverPhase(ConversationPhaseHandler):
    """Phase 1: Discover what interests the user."""

    phase = ConversationPhase.DISCOVER
    goal = "Understand what the user is interested in building"
    extraction_keys = ["interest_area", "initial_idea", "motivation"]

    def get_system_addition(self, context: Dict[str, Any]) -> str:
        return """
CURRENT PHASE: DISCOVER

Goal: Find out what interests the user. They might have:
- A vague interest ("I want to learn APIs")
- A problem ("I spend too much time on X")
- A specific idea ("I want to build a todo app")

Extract:
- interest_area: General domain (web, CLI, automation, games, etc.)
- initial_idea: Any concrete project idea mentioned
- motivation: Why they want to build this (learning, solving problem, fun)

Keep it light and exploratory. One question at a time."""

    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        return "🤔 Hey! What's on your mind today? Got a project idea brewing, or just looking to build something cool?"

    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        # Need at least an interest area or initial idea
        return bool(extracted.get("interest_area") or extracted.get("initial_idea"))


class ExplorePhase(ConversationPhaseHandler):
    """Phase 2: Explore deeper into the idea."""

    phase = ConversationPhase.EXPLORE
    goal = "Understand the user's motivation and constraints"
    extraction_keys = ["problem_statement", "target_user", "constraints", "inspiration"]

    def get_system_addition(self, context: Dict[str, Any]) -> str:
        interest = context.get("interest_area", "their interest")
        idea = context.get("initial_idea", "")

        return f"""
CURRENT PHASE: EXPLORE

The user is interested in: {interest}
{"They mentioned: " + idea if idea else ""}

Goal: Dig deeper to understand:
- What problem are they solving? (or is this just for fun/learning?)
- Who would use this? (themselves, others, specific audience?)
- Any constraints? (time, platform, must-use certain tech?)
- Any inspiration? (saw something similar, combining ideas?)

Extract:
- problem_statement: The core problem or goal
- target_user: Who this is for
- constraints: Any limitations mentioned
- inspiration: Any referenced projects or ideas

Ask follow-up questions naturally. Build on what they've shared."""

    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        interest = context.get("interest_area", "that")
        idea = context.get("initial_idea", "")

        if idea:
            return f"🤔 Interesting - {idea}! Tell me more. What draws you to this? Is it solving a problem you have, or more about learning?"
        else:
            return f"🤔 Nice! What draws you to {interest}? Are you looking to solve a specific problem, or more interested in learning how things work?"

    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        # Need problem OR clear indication it's a learning project
        has_problem = bool(extracted.get("problem_statement"))
        has_target = bool(extracted.get("target_user"))
        return has_problem or has_target


class CrystallizePhase(ConversationPhaseHandler):
    """Phase 3: Crystallize into a concrete project."""

    phase = ConversationPhase.CRYSTALLIZE
    goal = "Define a clear, concrete project"
    extraction_keys = ["project_name", "tagline", "vision", "core_functionality"]

    def get_system_addition(self, context: Dict[str, Any]) -> str:
        return f"""
CURRENT PHASE: CRYSTALLIZE

What we know so far:
{json.dumps(context, indent=2, default=str)}

Goal: Crystallize this into a CONCRETE project. Propose:
- A clear project name
- A one-line tagline
- What it actually does (core functionality)

Present your understanding back to the user:
"So it sounds like you want to build [NAME] - [TAGLINE]. It would [CORE FUNCTIONALITY]. Does that capture it?"

Let them correct or confirm. This is collaborative refinement.

Extract:
- project_name: The name for this project
- tagline: One-line description
- vision: Expanded description of what it does
- core_functionality: List of main things it does"""

    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        # The AI will synthesize based on context
        return None  # Let AI generate based on context

    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        return bool(extracted.get("project_name") and extracted.get("vision"))


class ScopePhase(ConversationPhaseHandler):
    """Phase 4: Define scope and priorities."""

    phase = ConversationPhase.SCOPE
    goal = "Define MVP vs nice-to-have features"
    extraction_keys = ["must_have_features", "should_have_features", "nice_to_have_features", "anti_goals"]

    def get_system_addition(self, context: Dict[str, Any]) -> str:
        project_name = context.get("project_name", "this project")

        return f"""
CURRENT PHASE: SCOPE

Project: {project_name}
Vision: {context.get("vision", "")}

Goal: Define what's in and out of scope.

Ask about:
- What's absolutely essential for v1? (MVP)
- What would make it really good? (v1.0)
- What can wait for later? (future)
- What should this explicitly NOT do? (anti-goals)

Help them prioritize. Beginners often want everything - gently guide toward achievable MVP.

Extract:
- must_have_features: Essential for MVP (list of feature dicts with name, description)
- should_have_features: Important but not blocking (list)
- nice_to_have_features: Future enhancements (list)
- anti_goals: What this project is NOT trying to do (list of strings)"""

    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        project_name = context.get("project_name", "this")
        return f"🤔 Now let's scope {project_name}. What's the absolute minimum it needs to do to be useful? What's the simplest version that would make you happy?"

    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        return bool(extracted.get("must_have_features"))


class ProfilePhase(ConversationPhaseHandler):
    """Phase 5: Understand user's technical background."""

    phase = ConversationPhase.PROFILE
    goal = "Understand user's skill level and preferences"
    extraction_keys = ["skill_level", "known_languages", "known_frameworks", "learning_goals", "time_commitment", "explanation_preference"]

    def get_system_addition(self, context: Dict[str, Any]) -> str:
        return """
CURRENT PHASE: PROFILE

Goal: Understand the user's technical background so downstream AI can calibrate responses.

Ask naturally about:
- Their experience level (beginner/intermediate/advanced)
- Languages/frameworks they're comfortable with
- What they want to learn from this project
- How much time they can dedicate
- Do they want detailed explanations or just code?

Be encouraging regardless of level. Frame questions positively.

Extract:
- skill_level: "beginner", "intermediate", or "advanced"
- known_languages: List of programming languages they know
- known_frameworks: List of frameworks they're familiar with
- learning_goals: What they want to learn
- time_commitment: How much time they have (e.g., "5 hours/week")
- explanation_preference: "guided" (explain everything), "balanced", or "minimal" (just code)"""

    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        return "🤔 Last thing - help me understand your background so I can tailor the spec. How comfortable are you with programming? Any languages or frameworks you already know?"

    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        return bool(extracted.get("skill_level"))


class RefinePhase(ConversationPhaseHandler):
    """Phase 6: Final refinement and confirmation."""

    phase = ConversationPhase.REFINE
    goal = "Review and refine the complete specification"
    extraction_keys = ["confirmed", "adjustments"]

    def get_system_addition(self, context: Dict[str, Any]) -> str:
        return f"""
CURRENT PHASE: REFINE

We have gathered all the information. Present a summary:

Project: {context.get("project_name")}
Tagline: {context.get("tagline")}

Vision: {context.get("vision")}

MVP Features:
{json.dumps(context.get("must_have_features", []), indent=2)}

User Profile:
- Skill: {context.get("skill_level")}
- Knows: {context.get("known_languages", [])}

Ask: "Does this capture what you want to build? Anything to add or change?"

If they confirm, respond with enthusiasm and let them know the spec is ready.
If they want changes, incorporate them.

Extract:
- confirmed: true if they approve, false if they want changes
- adjustments: any changes they requested"""

    def get_initial_prompt(self, context: Dict[str, Any]) -> str:
        return None  # AI will generate summary

    def check_complete(self, extracted: Dict[str, Any]) -> bool:
        return extracted.get("confirmed", False)


class ConversationEngine:
    """
    Manages the guided conversation flow.

    Uses Nexus Connector to communicate with AI providers
    while managing conversation phases and data extraction.
    """

    PHASES = [
        DiscoverPhase(),
        ExplorePhase(),
        CrystallizePhase(),
        ScopePhase(),
        ProfilePhase(),
        RefinePhase(),
    ]

    def __init__(self, session: Session, connector=None):
        """
        Initialize conversation engine.

        Args:
            session: The MeThinks session
            connector: Optional Nexus connector (created if not provided)
        """
        self.session = session
        self.connector = connector
        self._current_phase_idx = self._get_phase_index(session.phase)

    def _get_phase_index(self, phase: ConversationPhase) -> int:
        """Get index of phase in PHASES list."""
        for i, p in enumerate(self.PHASES):
            if p.phase == phase:
                return i
        return 0

    @property
    def current_phase(self) -> ConversationPhaseHandler:
        """Get current phase handler."""
        if self._current_phase_idx >= len(self.PHASES):
            return self.PHASES[-1]
        return self.PHASES[self._current_phase_idx]

    def get_system_prompt(self) -> str:
        """Build full system prompt for current phase."""
        phase_addition = self.current_phase.get_system_addition(self.session.extracted)
        return f"{METHINKS_SYSTEM_PROMPT}\n\n{phase_addition}"

    async def get_initial_message(self) -> str:
        """Get initial message for current phase."""
        initial = self.current_phase.get_initial_prompt(self.session.extracted)

        if initial:
            return initial

        # If no static initial prompt, use AI to generate one
        if self.connector:
            response = await self._get_ai_response(
                "Generate an opening message for this phase based on what we know so far. "
                "Keep it conversational and concise."
            )
            return response

        return "🤔 Tell me more..."

    async def process_input(self, user_input: str) -> PhaseResult:
        """
        Process user input and advance conversation.

        Args:
            user_input: What the user said

        Returns:
            PhaseResult with AI response and extracted data
        """
        # Add user message to session
        self.session.add_message("user", user_input)

        # Get AI response
        if self.connector:
            ai_response = await self._get_ai_response(user_input)
        else:
            ai_response = "🤔 [AI response would go here - connector not configured]"

        # Try to extract structured data
        extracted = await self._extract_data(user_input, ai_response)

        # Add AI response to session
        self.session.add_message("assistant", ai_response, extracted)

        # Check if phase is complete
        phase_complete = self.current_phase.check_complete(self.session.extracted)

        # Determine if we should advance
        should_advance = phase_complete and self._current_phase_idx < len(self.PHASES) - 1

        if should_advance:
            self._current_phase_idx += 1
            self.session.advance_phase()

        return PhaseResult(
            response=ai_response,
            extracted_data=extracted,
            should_advance=should_advance,
            phase_complete=phase_complete,
        )

    async def _get_ai_response(self, user_input: str) -> str:
        """Get response from AI provider."""
        if not self.connector:
            return "🤔 [Connector not configured]"

        try:
            # Build messages with system prompt
            messages = [
                {"role": "system", "content": self.get_system_prompt()},
            ]

            # Add conversation history (last N messages to stay in context)
            history = self.session.get_conversation_for_ai()[-10:]
            messages.extend(history)

            # Add current input if not already in history
            if not history or history[-1].get("content") != user_input:
                messages.append({"role": "user", "content": user_input})

            # Get response from connector
            response = await self.connector.send_message(
                user_input,
                add_to_history=False,  # We manage history ourselves
            )

            return response.get("content", "🤔 I'm not sure how to respond to that.")

        except Exception as e:
            return f"🤔 Sorry, I had trouble processing that. ({str(e)[:50]})"

    async def _extract_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """
        Extract structured data from the conversation.

        Uses a combination of:
        1. Pattern matching for common formats
        2. AI extraction for complex data
        """
        extracted = {}

        # Phase-specific extraction
        phase = self.current_phase

        if phase.phase == ConversationPhase.DISCOVER:
            extracted.update(self._extract_discover_data(user_input, ai_response))

        elif phase.phase == ConversationPhase.EXPLORE:
            extracted.update(self._extract_explore_data(user_input, ai_response))

        elif phase.phase == ConversationPhase.CRYSTALLIZE:
            extracted.update(self._extract_crystallize_data(user_input, ai_response))

        elif phase.phase == ConversationPhase.SCOPE:
            extracted.update(self._extract_scope_data(user_input, ai_response))

        elif phase.phase == ConversationPhase.PROFILE:
            extracted.update(self._extract_profile_data(user_input, ai_response))

        elif phase.phase == ConversationPhase.REFINE:
            extracted.update(self._extract_refine_data(user_input, ai_response))

        return extracted

    def _extract_discover_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """Extract data from discover phase."""
        data = {}
        input_lower = user_input.lower()

        # Detect interest areas
        interest_keywords = {
            "api": "APIs/web services",
            "web": "web development",
            "cli": "command-line tools",
            "automat": "automation",
            "game": "games",
            "data": "data processing",
            "machine learning": "machine learning",
            "ml": "machine learning",
            "ai": "AI/ML",
            "bot": "bots/automation",
            "scrape": "web scraping",
            "file": "file management",
            "organiz": "organization tools",
        }

        for keyword, area in interest_keywords.items():
            if keyword in input_lower:
                data["interest_area"] = area
                break

        # If user describes a specific project, capture it
        if len(user_input) > 30:
            data["initial_idea"] = user_input

        return data

    def _extract_explore_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """Extract data from explore phase."""
        data = {}
        input_lower = user_input.lower()

        # Detect motivation
        if any(w in input_lower for w in ["learn", "understand", "how", "works"]):
            data["motivation"] = "learning"
        elif any(w in input_lower for w in ["problem", "annoying", "hate", "waste time"]):
            data["motivation"] = "problem-solving"
            data["problem_statement"] = user_input
        elif any(w in input_lower for w in ["fun", "cool", "interesting"]):
            data["motivation"] = "fun/exploration"

        # Detect target user
        if any(w in input_lower for w in ["myself", "my own", "personal", "me"]):
            data["target_user"] = "personal use"
        elif any(w in input_lower for w in ["team", "others", "people", "users"]):
            data["target_user"] = "other users"

        return data

    def _extract_crystallize_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """Extract data from crystallize phase."""
        data = {}
        input_lower = user_input.lower()

        # User confirming AI's proposal
        if any(w in input_lower for w in ["yes", "yeah", "yep", "correct", "exactly", "perfect", "that's it"]):
            # Try to extract project name from AI response
            # Look for patterns like "build [NAME]" or "[NAME] -"
            import re
            name_match = re.search(r"build\s+([A-Z][A-Za-z\s]+?)(?:\s*[-–]|\s*\.|\s*that)", ai_response)
            if name_match:
                data["project_name"] = name_match.group(1).strip()

            # Look for quoted names
            quoted_match = re.search(r'["\']([^"\']+)["\']', ai_response)
            if quoted_match and not data.get("project_name"):
                data["project_name"] = quoted_match.group(1)

            # Capture vision from AI's description
            if "would" in ai_response.lower() or "that" in ai_response.lower():
                data["vision"] = ai_response

        return data

    def _extract_scope_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """Extract data from scope phase."""
        data = {}

        # For now, capture user's response as features
        # A more sophisticated version would parse bullet points
        if len(user_input) > 20:
            # Treat as must-have features description
            if "must_have_features" not in self.session.extracted:
                data["must_have_features"] = [
                    {"name": "Core functionality", "description": user_input}
                ]

        return data

    def _extract_profile_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """Extract data from profile phase."""
        data = {}
        input_lower = user_input.lower()

        # Skill level
        if any(w in input_lower for w in ["beginner", "new to", "just started", "learning"]):
            data["skill_level"] = "beginner"
        elif any(w in input_lower for w in ["advanced", "senior", "expert", "years"]):
            data["skill_level"] = "advanced"
        elif any(w in input_lower for w in ["some", "intermediate", "comfortable", "familiar"]):
            data["skill_level"] = "intermediate"

        # Languages
        languages = []
        lang_keywords = ["python", "javascript", "typescript", "java", "go", "rust", "c++", "c#", "ruby", "php"]
        for lang in lang_keywords:
            if lang in input_lower:
                languages.append(lang.title() if lang != "c++" and lang != "c#" else lang.upper())
        if languages:
            data["known_languages"] = languages

        # Frameworks
        frameworks = []
        framework_keywords = ["react", "vue", "angular", "django", "flask", "fastapi", "express", "rails", "spring"]
        for fw in framework_keywords:
            if fw in input_lower:
                frameworks.append(fw.title())
        if frameworks:
            data["known_frameworks"] = frameworks

        return data

    def _extract_refine_data(self, user_input: str, ai_response: str) -> Dict[str, Any]:
        """Extract data from refine phase."""
        data = {}
        input_lower = user_input.lower()

        # Check for confirmation
        if any(w in input_lower for w in ["yes", "looks good", "perfect", "let's go", "generate", "done"]):
            data["confirmed"] = True
        elif any(w in input_lower for w in ["no", "change", "actually", "wait", "but"]):
            data["confirmed"] = False
            data["adjustments"] = user_input

        return data

    def build_spec(self) -> ProjectSpec:
        """Build ProjectSpec from extracted data."""
        ext = self.session.extracted
        spec = self.session.spec

        # Update spec with extracted data
        if ext.get("project_name"):
            spec.name = ext["project_name"]
        if ext.get("tagline"):
            spec.tagline = ext["tagline"]
        if ext.get("vision"):
            spec.vision = ext["vision"]
        if ext.get("problem_statement"):
            spec.problem_statement = ext["problem_statement"]
        if ext.get("target_user"):
            spec.target_user = ext["target_user"]

        # User profile
        if ext.get("skill_level"):
            spec.user_profile.skill_level = SkillLevel(ext["skill_level"])
        if ext.get("known_languages"):
            spec.user_profile.known_languages = ext["known_languages"]
        if ext.get("known_frameworks"):
            spec.user_profile.known_frameworks = ext["known_frameworks"]
        if ext.get("learning_goals"):
            spec.user_profile.learning_goals = ext["learning_goals"]
        if ext.get("time_commitment"):
            spec.user_profile.time_commitment = ext["time_commitment"]
        if ext.get("explanation_preference"):
            spec.user_profile.explanation_preference = ExplanationPreference(ext["explanation_preference"])

        # Features
        if ext.get("must_have_features"):
            for f in ext["must_have_features"]:
                if isinstance(f, dict):
                    spec.features.append(Feature(
                        name=f.get("name", "Feature"),
                        description=f.get("description", ""),
                        priority=FeaturePriority.MUST,
                    ))

        if ext.get("should_have_features"):
            for f in ext["should_have_features"]:
                if isinstance(f, dict):
                    spec.features.append(Feature(
                        name=f.get("name", "Feature"),
                        description=f.get("description", ""),
                        priority=FeaturePriority.SHOULD,
                    ))

        if ext.get("nice_to_have_features"):
            for f in ext["nice_to_have_features"]:
                if isinstance(f, dict):
                    spec.features.append(Feature(
                        name=f.get("name", "Feature"),
                        description=f.get("description", ""),
                        priority=FeaturePriority.NICE,
                    ))

        # Anti-goals and constraints
        if ext.get("anti_goals"):
            spec.anti_goals = ext["anti_goals"]
        if ext.get("constraints"):
            spec.constraints = ext["constraints"]

        # Key insights
        if ext.get("motivation"):
            spec.key_insights.append(f"Motivation: {ext['motivation']}")
        if ext.get("interest_area"):
            spec.key_insights.append(f"Interest area: {ext['interest_area']}")

        return spec
