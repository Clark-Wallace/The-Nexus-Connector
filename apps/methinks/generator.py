"""
Specification document generator for MeThinks.

Generates project specifications in various formats:
- Markdown (human-readable)
- Claude-optimized (for Claude Code)
- JSON (machine-readable)
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import ProjectSpec, Feature, FeaturePriority
from .session import Session


class SpecGenerator:
    """
    Generates specification documents from MeThinks sessions.
    """

    def generate(self, spec: ProjectSpec, format: str = "markdown") -> str:
        """
        Generate spec in requested format.

        Args:
            spec: The project specification
            format: Output format - "markdown", "claude", or "json"

        Returns:
            Generated specification string
        """
        if format == "claude":
            return self.generate_claude_format(spec)
        elif format == "json":
            return spec.to_json(indent=2)
        else:
            return self.generate_markdown(spec)

    def generate_markdown(self, spec: ProjectSpec) -> str:
        """Generate human-readable markdown spec."""
        lines = [
            f"# {spec.name}",
            "",
        ]

        if spec.tagline:
            lines.extend([f"*{spec.tagline}*", ""])

        # Metadata
        lines.extend([
            "## Project Overview",
            "",
            f"- **Generated:** {spec.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"- **MeThinks Version:** {spec.methinks_version}",
            "",
        ])

        # Vision
        if spec.vision:
            lines.extend([
                "## Vision",
                "",
                spec.vision,
                "",
            ])

        # Problem
        if spec.problem_statement:
            lines.extend([
                "## Problem Statement",
                "",
                spec.problem_statement,
                "",
            ])

        # Target User
        if spec.target_user:
            lines.extend([
                "## Target User",
                "",
                spec.target_user,
                "",
            ])

        # User Profile
        profile = spec.user_profile
        lines.extend([
            "## Developer Profile",
            "",
            f"- **Skill Level:** {profile.skill_level.value.title()}",
        ])
        if profile.known_languages:
            lines.append(f"- **Known Languages:** {', '.join(profile.known_languages)}")
        if profile.known_frameworks:
            lines.append(f"- **Known Frameworks:** {', '.join(profile.known_frameworks)}")
        if profile.learning_goals:
            lines.append(f"- **Learning Goals:** {', '.join(profile.learning_goals)}")
        if profile.time_commitment:
            lines.append(f"- **Time Commitment:** {profile.time_commitment}")
        lines.append(f"- **Explanation Preference:** {profile.explanation_preference.value.title()}")
        lines.append("")

        # Technical Requirements
        tech = spec.technical
        lines.extend([
            "## Technical Requirements",
            "",
            f"- **Language:** {tech.language} {tech.language_version or ''}".strip(),
            f"- **Environment:** {tech.environment}",
        ])
        if tech.frameworks:
            lines.append(f"- **Frameworks:** {', '.join(tech.frameworks)}")
        if tech.dependencies:
            lines.append(f"- **Dependencies:** {', '.join(tech.dependencies)}")
        lines.append("")

        # Features
        if spec.features:
            lines.extend([
                "## Features",
                "",
            ])

            must_have = spec.must_have_features
            if must_have:
                lines.extend([
                    "### Must Have (MVP)",
                    "",
                ])
                for f in must_have:
                    lines.append(f"- **{f.name}:** {f.description}")
                    if f.rationale:
                        lines.append(f"  - *Why:* {f.rationale}")
                lines.append("")

            should_have = spec.should_have_features
            if should_have:
                lines.extend([
                    "### Should Have (v1.0)",
                    "",
                ])
                for f in should_have:
                    lines.append(f"- **{f.name}:** {f.description}")
                    if f.rationale:
                        lines.append(f"  - *Why:* {f.rationale}")
                lines.append("")

            nice_to_have = spec.nice_to_have_features
            if nice_to_have:
                lines.extend([
                    "### Nice to Have (Future)",
                    "",
                ])
                for f in nice_to_have:
                    lines.append(f"- **{f.name}:** {f.description}")
                    if f.rationale:
                        lines.append(f"  - *Why:* {f.rationale}")
                lines.append("")

        # Architecture Decisions
        if spec.architecture_decisions:
            lines.extend([
                "## Architecture Decisions",
                "",
            ])
            for decision, rationale in spec.architecture_decisions.items():
                lines.append(f"- **{decision}:** {rationale}")
            lines.append("")

        # Constraints
        if spec.constraints:
            lines.extend([
                "## Constraints",
                "",
            ])
            for constraint in spec.constraints:
                lines.append(f"- {constraint}")
            lines.append("")

        # Anti-Goals
        if spec.anti_goals:
            lines.extend([
                "## Anti-Goals (What This Is NOT)",
                "",
            ])
            for anti in spec.anti_goals:
                lines.append(f"- {anti}")
            lines.append("")

        # Success Criteria
        if spec.success_criteria:
            lines.extend([
                "## Success Criteria",
                "",
            ])
            for criteria in spec.success_criteria:
                lines.append(f"- [ ] {criteria}")
            lines.append("")

        # Key Insights
        if spec.key_insights:
            lines.extend([
                "## Key Insights from Discovery",
                "",
            ])
            for insight in spec.key_insights:
                lines.append(f"- {insight}")
            lines.append("")

        # Conversation Summary
        if spec.conversation_summary:
            lines.extend([
                "## Discovery Conversation Summary",
                "",
                spec.conversation_summary,
                "",
            ])

        return "\n".join(lines)

    def generate_claude_format(self, spec: ProjectSpec) -> str:
        """
        Generate Claude Code optimized format.

        This format is designed to be placed in a CLAUDE.md file
        at the project root, giving Claude Code full context.
        """
        lines = [
            "# CLAUDE.md",
            "",
            f"This file provides context to Claude Code for the **{spec.name}** project.",
            "",
            "## Project Context",
            "",
        ]

        if spec.vision:
            lines.extend([
                "### What We're Building",
                "",
                spec.vision,
                "",
            ])

        if spec.problem_statement:
            lines.extend([
                "### Problem Being Solved",
                "",
                spec.problem_statement,
                "",
            ])

        # Developer Context - Critical for AI to calibrate responses
        lines.extend([
            "## Developer Context",
            "",
            "**IMPORTANT:** Calibrate explanations and code complexity to this profile:",
            "",
            f"- **Skill Level:** {spec.user_profile.skill_level.value.title()}",
        ])

        if spec.user_profile.known_languages:
            lines.append(f"- **Familiar With:** {', '.join(spec.user_profile.known_languages)}")

        if spec.user_profile.learning_goals:
            lines.append(f"- **Wants to Learn:** {', '.join(spec.user_profile.learning_goals)}")

        pref = spec.user_profile.explanation_preference.value
        if pref == "guided":
            lines.append("- **Explanation Style:** Provide detailed explanations for all code")
        elif pref == "minimal":
            lines.append("- **Explanation Style:** Minimal comments, focus on clean code")
        else:
            lines.append("- **Explanation Style:** Balance code with helpful comments")

        lines.append("")

        # Technical Stack
        tech = spec.technical
        lines.extend([
            "## Technical Stack",
            "",
            f"- **Language:** {tech.language} {tech.language_version or ''}".strip(),
        ])
        if tech.frameworks:
            lines.append(f"- **Frameworks:** {', '.join(tech.frameworks)}")
        if tech.dependencies:
            lines.append(f"- **Key Dependencies:** {', '.join(tech.dependencies)}")
        lines.append("")

        # Features with clear priority
        if spec.features:
            lines.extend([
                "## Feature Priorities",
                "",
                "When implementing, follow this priority order:",
                "",
            ])

            must_have = spec.must_have_features
            if must_have:
                lines.append("### 1. MVP (Must Complete First)")
                lines.append("")
                for i, f in enumerate(must_have, 1):
                    lines.append(f"{i}. **{f.name}** - {f.description}")
                lines.append("")

            should_have = spec.should_have_features
            if should_have:
                lines.append("### 2. Version 1.0 (After MVP)")
                lines.append("")
                for i, f in enumerate(should_have, 1):
                    lines.append(f"{i}. **{f.name}** - {f.description}")
                lines.append("")

            nice_to_have = spec.nice_to_have_features
            if nice_to_have:
                lines.append("### 3. Future Enhancements (Only If Asked)")
                lines.append("")
                for i, f in enumerate(nice_to_have, 1):
                    lines.append(f"{i}. **{f.name}** - {f.description}")
                lines.append("")

        # Architecture guidance
        if spec.architecture_decisions:
            lines.extend([
                "## Architecture Guidelines",
                "",
                "Follow these architectural decisions:",
                "",
            ])
            for decision, rationale in spec.architecture_decisions.items():
                lines.append(f"- **{decision}:** {rationale}")
            lines.append("")

        # Constraints - things AI must respect
        if spec.constraints:
            lines.extend([
                "## Constraints",
                "",
                "**These constraints must be respected:**",
                "",
            ])
            for constraint in spec.constraints:
                lines.append(f"- {constraint}")
            lines.append("")

        # Anti-goals - things AI should NOT do
        if spec.anti_goals:
            lines.extend([
                "## DO NOT",
                "",
                "**Explicitly avoid these:**",
                "",
            ])
            for anti in spec.anti_goals:
                lines.append(f"- {anti}")
            lines.append("")

        # Success criteria
        if spec.success_criteria:
            lines.extend([
                "## Definition of Done",
                "",
                "The project is complete when:",
                "",
            ])
            for criteria in spec.success_criteria:
                lines.append(f"- [ ] {criteria}")
            lines.append("")

        # Key insights for context
        if spec.key_insights:
            lines.extend([
                "## Background Context",
                "",
                "Key insights from the project discovery session:",
                "",
            ])
            for insight in spec.key_insights:
                lines.append(f"- {insight}")
            lines.append("")

        # Footer
        lines.extend([
            "---",
            "",
            f"*Generated by MeThinks v{spec.methinks_version} on {spec.created_at.strftime('%Y-%m-%d')}*",
        ])

        return "\n".join(lines)

    def save_spec(
        self,
        spec: ProjectSpec,
        path: Path,
        format: str = "markdown"
    ) -> Path:
        """Save spec to a file."""
        content = self.generate(spec, format)
        path.write_text(content)
        return path

    def save_all_formats(self, spec: ProjectSpec, directory: Path) -> dict:
        """Save spec in all formats to a directory."""
        directory.mkdir(parents=True, exist_ok=True)

        paths = {}

        # Markdown
        md_path = directory / "PROJECT_SPEC.md"
        md_path.write_text(self.generate_markdown(spec))
        paths["markdown"] = md_path

        # Claude format
        claude_path = directory / "CLAUDE.md"
        claude_path.write_text(self.generate_claude_format(spec))
        paths["claude"] = claude_path

        # JSON
        json_path = directory / "spec.json"
        json_path.write_text(spec.to_json())
        paths["json"] = json_path

        return paths
