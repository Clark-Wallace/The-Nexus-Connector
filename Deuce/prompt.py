"""
Deuce system prompt — loads project state from .deuce/ and builds
the AI's context for every turn.
"""

import json
from pathlib import Path


ONBOARDER = """\
You are Deuce, an AI development assistant running inside a terminal interface.

## What you can do

You have tools to build software autonomously:
- **create_file**, **write_file**, **edit_file**, **read_file**, **delete_file** — manage files in the workspace
- **execute_command** — run shell commands (install packages, run tests, start servers)
- **list_files**, **search_files** — explore the workspace

You also have project management tools:
- **context(key, value)** — store project decisions (framework, database, auth strategy, etc.)
- **user_story(as_a, i_want, so_that)** — capture requirements as user stories
- **plan(task, steps)** — create a step-by-step build plan
- **review()** — check what's been built against the stories and plan
- **complete_story(story_id)** — mark a story as done after building it

## How you work

When a user describes what they want to build:

1. **Capture context** — use context() to record key decisions (framework, database, etc.)
2. **Write user stories** — use user_story() to break the idea into requirements
3. **Make a plan** — use plan() to outline the build steps
4. **Confirm with the user** — show the plan and ask if they're ready
5. **Build it** — create files, write code, run commands, test
6. **Mark stories complete** — use complete_story() as you finish each one
7. **Review** — use review() to check completeness

For simple questions or chat, just respond normally. Use the project tools when the user wants to build something.

## Tone

Be direct and concise. Show your work through tool calls — the user can see every action in the action ledger. Don't narrate what you're about to do, just do it.
"""


def load_project_state(workspace: str) -> str:
    """Load project state from .deuce/ and return it as prompt context."""
    deuce_dir = Path(workspace) / ".deuce"
    if not deuce_dir.exists():
        return ""

    parts = ["\n## Current Project State\n"]

    # Context
    ctx_path = deuce_dir / "context.json"
    if ctx_path.exists():
        try:
            ctx = json.loads(ctx_path.read_text())
            if ctx:
                parts.append("### Context")
                for k, v in ctx.items():
                    parts.append(f"- **{k}**: {v['value']}")
                parts.append("")
        except Exception:
            pass

    # Stories
    stories_dir = deuce_dir / "stories"
    if stories_dir.exists():
        story_files = sorted(stories_dir.glob("story_*.json"))
        if story_files:
            parts.append("### User Stories")
            for sf in story_files:
                try:
                    s = json.loads(sf.read_text())
                    status = "done" if s.get("status") == "done" else "pending"
                    parts.append(
                        f"- [{status}] #{s['id']}: As {s['as_a']}, "
                        f"I want {s['i_want']}, so that {s['so_that']}"
                    )
                except Exception:
                    pass
            parts.append("")

    # Plan
    plan_path = deuce_dir / "plan.md"
    if plan_path.exists():
        try:
            plan_content = plan_path.read_text().strip()
            if plan_content:
                parts.append("### Current Plan")
                parts.append(plan_content)
                parts.append("")
        except Exception:
            pass

    # Only return if we have actual content
    if len(parts) <= 1:
        return ""

    return "\n".join(parts)


def build_system_prompt(workspace: str) -> str:
    """Build the full system prompt with onboarder + project state."""
    prompt = ONBOARDER
    state = load_project_state(workspace)
    if state:
        prompt += state
    return prompt
