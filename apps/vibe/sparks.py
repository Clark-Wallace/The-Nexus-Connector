"""
Sparks - Contextual next-step suggestions for Vibe Code.

Sparks analyze what was just built and suggest logical next steps,
helping users continue their flow without having to think about what comes next.
"""

from typing import List, Dict, Any


def generate_sparks(context: Any, include_reason: bool = True) -> List[Dict[str, str]]:
    """
    Generate contextual next-step suggestions based on what was built.

    Args:
        context: The last response/action (converted to string for analysis)
        include_reason: Whether to include "why" reasoning for each spark

    Returns:
        List of spark dictionaries with keys:
        - icon: Emoji icon
        - label: Short label (e.g., "Add Auth")
        - desc: Description of what it does
        - recommended: Boolean, True if this is the best next step
        - reason: Why this is a good next step (if include_reason=True)
    """
    # Safety: ensure context is a string
    if not isinstance(context, str):
        context = str(context) if context else ""

    context_lower = context.lower()

    # After API/backend work
    if any(word in context_lower for word in ["api", "endpoint", "flask", "fastapi", "express", "rest", "django"]):
        return [
            {
                "icon": "🔐",
                "label": "Add Auth",
                "desc": "Add JWT authentication so users can securely access their data",
                "recommended": True,
                "reason": "Most APIs need auth before going live"
            },
            {
                "icon": "🧪",
                "label": "Add Tests",
                "desc": "Create unit tests to catch bugs before they happen",
                "recommended": False,
                "reason": "Good practice, but can wait until features are done"
            },
            {
                "icon": "📚",
                "label": "API Docs",
                "desc": "Generate OpenAPI/Swagger documentation",
                "recommended": False,
                "reason": "Helps others understand your API"
            },
        ]

    # After auth work
    elif any(word in context_lower for word in ["auth", "jwt", "login", "password", "token", "session"]):
        return [
            {
                "icon": "👥",
                "label": "User Roles",
                "desc": "Add admin/user roles for different permissions",
                "recommended": True,
                "reason": "Common next step after basic auth"
            },
            {
                "icon": "🔄",
                "label": "OAuth",
                "desc": "Add Google/GitHub login for easier sign-up",
                "recommended": False,
                "reason": "Nice to have, not essential"
            },
            {
                "icon": "📧",
                "label": "Email Verify",
                "desc": "Send verification emails to confirm accounts",
                "recommended": False,
                "reason": "Important for production but adds complexity"
            },
        ]

    # After frontend work
    elif any(word in context_lower for word in ["react", "vue", "frontend", "component", "html", "css", "svelte", "next"]):
        return [
            {
                "icon": "🎨",
                "label": "Add Styling",
                "desc": "Make it look good with Tailwind or styled-components",
                "recommended": True,
                "reason": "UI needs to look good to feel good"
            },
            {
                "icon": "📱",
                "label": "Mobile Ready",
                "desc": "Make it responsive for phones and tablets",
                "recommended": False,
                "reason": "Important but can iterate on"
            },
            {
                "icon": "⚡",
                "label": "Optimize",
                "desc": "Add lazy loading and performance optimizations",
                "recommended": False,
                "reason": "Good for production, not urgent"
            },
        ]

    # After database work
    elif any(word in context_lower for word in ["database", "sqlite", "postgres", "mongo", "model", "schema", "sql"]):
        return [
            {
                "icon": "🔄",
                "label": "Migrations",
                "desc": "Set up database migrations for schema changes",
                "recommended": True,
                "reason": "Essential for evolving your data model"
            },
            {
                "icon": "💾",
                "label": "Seed Data",
                "desc": "Create sample data for testing",
                "recommended": False,
                "reason": "Helpful for development"
            },
            {
                "icon": "📊",
                "label": "Admin Panel",
                "desc": "Build a simple admin interface to manage data",
                "recommended": False,
                "reason": "Nice for debugging and management"
            },
        ]

    # After tests
    elif any(word in context_lower for word in ["test", "pytest", "jest", "spec", "coverage"]):
        return [
            {
                "icon": "🔄",
                "label": "CI/CD",
                "desc": "Set up GitHub Actions to run tests automatically",
                "recommended": True,
                "reason": "Automates quality checks on every push"
            },
            {
                "icon": "📊",
                "label": "Coverage",
                "desc": "Add test coverage reporting",
                "recommended": False,
                "reason": "Shows how much code is tested"
            },
            {
                "icon": "🧪",
                "label": "E2E Tests",
                "desc": "Add end-to-end tests with Playwright or Cypress",
                "recommended": False,
                "reason": "Tests the full user flow"
            },
        ]

    # After CLI work
    elif any(word in context_lower for word in ["cli", "command", "argparse", "click", "terminal"]):
        return [
            {
                "icon": "📦",
                "label": "Package It",
                "desc": "Make it installable with pip/npm",
                "recommended": True,
                "reason": "Makes distribution easy"
            },
            {
                "icon": "🎨",
                "label": "Add Colors",
                "desc": "Add rich terminal output with colors",
                "recommended": False,
                "reason": "Better user experience"
            },
            {
                "icon": "📚",
                "label": "Help Docs",
                "desc": "Add comprehensive --help documentation",
                "recommended": False,
                "reason": "Users need to know how to use it"
            },
        ]

    # After deployment/docker work
    elif any(word in context_lower for word in ["docker", "deploy", "kubernetes", "container", "nginx"]):
        return [
            {
                "icon": "📊",
                "label": "Monitoring",
                "desc": "Add health checks and logging",
                "recommended": True,
                "reason": "Know when things break"
            },
            {
                "icon": "🔒",
                "label": "SSL/HTTPS",
                "desc": "Set up secure connections",
                "recommended": False,
                "reason": "Required for production"
            },
            {
                "icon": "🔄",
                "label": "Auto-Scale",
                "desc": "Configure auto-scaling for traffic",
                "recommended": False,
                "reason": "Handle growth automatically"
            },
        ]

    # Default/starting suggestions
    else:
        return [
            {
                "icon": "🚀",
                "label": "Build API",
                "desc": "Create a REST API backend",
                "recommended": True,
                "reason": "A solid backend is the foundation"
            },
            {
                "icon": "🎨",
                "label": "Build UI",
                "desc": "Create a frontend interface",
                "recommended": False,
                "reason": "Start here if you're visual"
            },
            {
                "icon": "🛠️",
                "label": "CLI Tool",
                "desc": "Build a command-line tool",
                "recommended": False,
                "reason": "Great for automation tasks"
            },
        ]


def format_sparks_chill(sparks: List[Dict[str, str]]) -> str:
    """
    Format sparks for chill mode - with full explanations.

    Args:
        sparks: List of spark dictionaries

    Returns:
        Formatted markdown string with explanations
    """
    output = "\n\n---\n\n### ✨ What's next? Here are your options:\n\n"

    for i, spark in enumerate(sparks, 1):
        recommended = " ⭐ **Recommended**" if spark.get("recommended") else ""
        output += f"""**{i}. {spark['icon']} {spark['label']}**{recommended}

{spark['desc']}

*Why: {spark['reason']}*

"""

    output += "\n**Type a number (1-3) or tell me what you're thinking...**"
    return output


def format_sparks_text(sparks: List[Dict[str, str]], show_reasons: bool = False) -> str:
    """
    Format sparks for text/CLI display.

    Args:
        sparks: List of spark dictionaries
        show_reasons: Whether to include the "why" reasoning

    Returns:
        Formatted text string
    """
    lines = ["\n✨ What's next?\n"]

    for i, spark in enumerate(sparks, 1):
        rec = " ⭐ Recommended" if spark.get("recommended") else ""
        lines.append(f"  [{i}] {spark['icon']} {spark['label']}{rec}")

        if show_reasons:
            lines.append(f"      {spark['desc']}")
            lines.append(f"      Why: {spark['reason']}")

        lines.append("")

    return "\n".join(lines)


def format_sparks_buttons(sparks: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Format sparks for button-based UI (returns data for buttons).

    Args:
        sparks: List of spark dictionaries

    Returns:
        List of simplified spark data for buttons
    """
    return [
        {
            "index": i,
            "icon": s["icon"],
            "label": s["label"],
            "desc": s["desc"],
            "recommended": s.get("recommended", False),
        }
        for i, s in enumerate(sparks, 1)
    ]
