#!/usr/bin/env python3
"""
Nexus Connector UI - Vibe Code with AI

A friendly interface for vibe coders to build with AI.
Features Chill Mode for guided, explained options.

Run with: python ui.py
Opens in your browser at http://localhost:7860
"""

import os
import json
import shutil
import asyncio
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple, Dict, Any
import threading

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import gradio as gr

# Projects directory
PROJECTS_DIR = Path("./projects")
PROJECTS_DIR.mkdir(exist_ok=True)

# Session store for persistent conversations
from nexus.web import SessionStore
SESSION_STORE = SessionStore(timeout_hours=24)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def run_async(coro):
    """Run async code synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider from environment."""
    key_map = {
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY",
        "google": "GOOGLE_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "xai": "XAI_API_KEY",
    }
    return os.getenv(key_map.get(provider, ""))


def get_available_providers() -> List[str]:
    """Get list of configured providers."""
    providers = []
    if os.getenv("OPENAI_API_KEY"):
        providers.append("openai")
    if os.getenv("ANTHROPIC_API_KEY"):
        providers.append("anthropic")
    if os.getenv("GOOGLE_API_KEY"):
        providers.append("google")
    if os.getenv("DEEPSEEK_API_KEY"):
        providers.append("deepseek")
    if os.getenv("XAI_API_KEY"):
        providers.append("xai")
    providers.append("ollama")
    return providers if providers else ["ollama"]


def get_connector(provider: str, session_id: str = "vibe"):
    """Get a NexusConnector with session persistence."""
    from nexus import NexusConnector

    api_key = get_api_key(provider)
    full_session_id = f"{session_id}_{provider}"

    async def _get():
        return await SESSION_STORE.get_or_create(
            full_session_id,
            lambda: NexusConnector(
                provider=provider,
                api_key=api_key or "",
                workspace=str(PROJECTS_DIR / "current"),
            )
        )

    return run_async(_get())


# =============================================================================
# SPARK GENERATION - Contextual suggestions
# =============================================================================

def generate_sparks(context: str, chill_mode: bool) -> List[Dict[str, str]]:
    """Generate contextual next-step suggestions based on what was built."""

    # Detect what was built from context
    context_lower = context.lower()

    sparks = []

    # After API/backend work
    if any(word in context_lower for word in ["api", "endpoint", "flask", "fastapi", "express", "rest"]):
        sparks = [
            {"icon": "🔐", "label": "Add Auth", "desc": "Add JWT authentication so users can securely access their data", "recommended": True, "reason": "Most APIs need auth before going live"},
            {"icon": "🧪", "label": "Add Tests", "desc": "Create unit tests to catch bugs before they happen", "recommended": False, "reason": "Good practice, but can wait until features are done"},
            {"icon": "📚", "label": "API Docs", "desc": "Generate OpenAPI/Swagger documentation", "recommended": False, "reason": "Helps others understand your API"},
        ]

    # After auth work
    elif any(word in context_lower for word in ["auth", "jwt", "login", "password", "token"]):
        sparks = [
            {"icon": "👥", "label": "User Roles", "desc": "Add admin/user roles for different permissions", "recommended": True, "reason": "Common next step after basic auth"},
            {"icon": "🔄", "label": "OAuth", "desc": "Add Google/GitHub login for easier sign-up", "recommended": False, "reason": "Nice to have, not essential"},
            {"icon": "📧", "label": "Email Verify", "desc": "Send verification emails to confirm accounts", "recommended": False, "reason": "Important for production but adds complexity"},
        ]

    # After frontend work
    elif any(word in context_lower for word in ["react", "vue", "frontend", "component", "html", "css"]):
        sparks = [
            {"icon": "🎨", "label": "Add Styling", "desc": "Make it look good with Tailwind or styled-components", "recommended": True, "reason": "UI needs to look good to feel good"},
            {"icon": "📱", "label": "Mobile Ready", "desc": "Make it responsive for phones and tablets", "recommended": False, "reason": "Important but can iterate on"},
            {"icon": "⚡", "label": "Optimize", "desc": "Add lazy loading and performance optimizations", "recommended": False, "reason": "Good for production, not urgent"},
        ]

    # After database work
    elif any(word in context_lower for word in ["database", "sqlite", "postgres", "mongo", "model"]):
        sparks = [
            {"icon": "🔄", "label": "Migrations", "desc": "Set up database migrations for schema changes", "recommended": True, "reason": "Essential for evolving your data model"},
            {"icon": "💾", "label": "Seed Data", "desc": "Create sample data for testing", "recommended": False, "reason": "Helpful for development"},
            {"icon": "📊", "label": "Admin Panel", "desc": "Build a simple admin interface to manage data", "recommended": False, "reason": "Nice for debugging and management"},
        ]

    # After tests
    elif any(word in context_lower for word in ["test", "pytest", "jest", "spec"]):
        sparks = [
            {"icon": "🔄", "label": "CI/CD", "desc": "Set up GitHub Actions to run tests automatically", "recommended": True, "reason": "Automates quality checks on every push"},
            {"icon": "📊", "label": "Coverage", "desc": "Add test coverage reporting", "recommended": False, "reason": "Shows how much code is tested"},
            {"icon": "🧪", "label": "E2E Tests", "desc": "Add end-to-end tests with Playwright or Cypress", "recommended": False, "reason": "Tests the full user flow"},
        ]

    # Generic/starting out
    else:
        sparks = [
            {"icon": "🚀", "label": "Build API", "desc": "Create a REST API backend", "recommended": True, "reason": "A solid backend is the foundation"},
            {"icon": "🎨", "label": "Build UI", "desc": "Create a frontend interface", "recommended": False, "reason": "Start here if you're visual"},
            {"icon": "🛠️", "label": "CLI Tool", "desc": "Build a command-line tool", "recommended": False, "reason": "Great for automation tasks"},
        ]

    return sparks


def format_sparks_chill(sparks: List[Dict[str, str]]) -> str:
    """Format sparks for chill mode - with explanations."""
    output = "\n\n---\n\n### ✨ What's next? Here are your options:\n\n"

    for i, spark in enumerate(sparks, 1):
        recommended = " ⭐ **Recommended**" if spark.get("recommended") else ""
        output += f"""**{i}. {spark['icon']} {spark['label']}**{recommended}

{spark['desc']}

*Why: {spark['reason']}*

"""

    output += "\n**Type a number (1-3) or tell me what you're thinking...**"
    return output


def format_sparks_fast(sparks: List[Dict[str, str]]) -> str:
    """Format sparks for fast mode - just buttons."""
    # This returns a hint that buttons should be shown
    return "SHOW_SPARK_BUTTONS"


# =============================================================================
# VIBE CODE - Main interactive coding mode
# =============================================================================

def vibe_code_respond(
    message: str,
    history: List[dict],
    provider: str,
    chill_mode: bool,
    files_created: List[str],
) -> Tuple[str, List[dict], List[str], str, str]:
    """
    Main Vibe Code response handler.
    Returns: (clear_input, history, files_created, files_display, sparks_display)
    """
    if not message or not message.strip():
        return "", history, files_created, format_files(files_created), ""

    # Handle spark button clicks (1, 2, 3)
    if message.strip() in ["1", "2", "3"]:
        # Get the last AI message to regenerate sparks
        last_ai = ""
        for msg in reversed(history):
            if msg.get("role") == "assistant":
                last_ai = msg.get("content", "")
                break

        sparks = generate_sparks(last_ai, chill_mode)
        idx = int(message.strip()) - 1
        if 0 <= idx < len(sparks):
            spark = sparks[idx]
            message = f"{spark['label']}: {spark['desc']}"

    # Add user message to history
    history = history + [{"role": "user", "content": message}]

    try:
        connector = get_connector(provider, session_id="vibe_code")

        # Track tool calls for display
        tool_log = []
        new_files = list(files_created)

        # Check if this looks like a build request
        is_build = any(word in message.lower() for word in [
            "build", "create", "make", "generate", "write", "add", "implement"
        ])

        if is_build:
            # Use execute_task for building
            async def _build():
                result = await connector.execute_task(message, show_progress=False)
                return result

            result = run_async(_build())

            # Track files
            for f in result.files_created:
                if f not in new_files:
                    new_files.append(f)
            for f in result.files_modified:
                if f not in new_files:
                    new_files.append(f)

            # Format response
            if result.success:
                response = f"✅ **Done!**\n\n{result.content[:1000]}"
                if result.files_created:
                    response += f"\n\n📁 **Files created:** {', '.join(result.files_created)}"
            else:
                response = f"⚠️ **Completed with issues:**\n\n{result.content}"

        else:
            # Regular chat for questions
            async def _chat():
                resp = await connector.send_message(message)
                return resp.get("content", "I couldn't generate a response.")

            response = run_async(_chat())

        # Add AI response to history
        history = history + [{"role": "assistant", "content": response}]

        # Generate sparks based on response
        sparks = generate_sparks(response, chill_mode)
        if chill_mode:
            sparks_display = format_sparks_chill(sparks)
        else:
            sparks_display = format_sparks_fast(sparks)

        return "", history, new_files, format_files(new_files), sparks_display

    except Exception as e:
        error_msg = f"❌ **Error:** {str(e)}"
        history = history + [{"role": "assistant", "content": error_msg}]
        return "", history, files_created, format_files(files_created), ""


def format_files(files: List[str]) -> str:
    """Format file list for display."""
    if not files:
        return "*No files created yet*"

    output = "### 📁 Files Created\n\n"
    for f in files[-10:]:  # Show last 10
        # Get icon by extension
        ext = Path(f).suffix.lower()
        icon = {
            ".py": "🐍", ".js": "📜", ".ts": "📘", ".html": "🌐",
            ".css": "🎨", ".json": "📋", ".md": "📝", ".yaml": "⚙️",
            ".yml": "⚙️", ".sql": "🗃️", ".sh": "⚡", ".go": "🔷",
            ".rs": "🦀", ".rb": "💎", ".java": "☕",
        }.get(ext, "📄")
        output += f"- {icon} `{f}`\n"

    if len(files) > 10:
        output += f"\n*...and {len(files) - 10} more*"

    return output


def new_vibe_session():
    """Start a new Vibe Code session."""
    # Clear the session
    run_async(SESSION_STORE.clear())
    return [], [], "*No files created yet*", ""


# =============================================================================
# QUICK ACTIONS - Simple one-click tools
# =============================================================================

def quick_fix(error_text: str, code_text: str, provider: str) -> str:
    """Quick fix for code errors."""
    if not error_text.strip():
        return "Please paste the error message."

    connector = get_connector(provider, session_id="quick_fix")

    prompt = f"""Fix this error:

Error:
```
{error_text}
```

{"Code:" if code_text.strip() else ""}
{"```" if code_text.strip() else ""}
{code_text if code_text.strip() else ""}
{"```" if code_text.strip() else ""}

Provide:
1. What's wrong (1 sentence)
2. The fixed code
3. What you changed"""

    async def _fix():
        resp = await connector.send_message(prompt)
        return resp.get("content", "Couldn't generate a fix.")

    return run_async(_fix())


def quick_explain(code_or_error: str, provider: str) -> str:
    """Quick explanation of code or error."""
    if not code_or_error.strip():
        return "Please paste code or an error to explain."

    connector = get_connector(provider, session_id="quick_explain")

    prompt = f"""Explain this in simple terms:

```
{code_or_error}
```

If it's an error, explain what went wrong and how to fix it.
If it's code, explain what it does step by step.
Keep it beginner-friendly."""

    async def _explain():
        resp = await connector.send_message(prompt)
        return resp.get("content", "Couldn't generate explanation.")

    return run_async(_explain())


# =============================================================================
# MR. METHINKS - Idea Generator
# =============================================================================

METHINKS_PERSONALITY = """You are Mr. MeThinks, a friendly and enthusiastic idea generator!

Your personality:
- Excited about helping people find cool project ideas
- Encouraging and positive
- You explain ideas simply, no jargon
- You tailor ideas to the person's interests and skill level
- You give concrete, buildable project ideas (not vague concepts)

When suggesting ideas:
1. Give exactly 3 project ideas
2. Each idea should have: a fun name, what it does, why it's cool
3. Mark one as "Perfect for you!" based on their interests
4. Make ideas progressively more ambitious (starter → intermediate → ambitious)
5. End with an encouraging message

Format each idea like:
### 🎯 [Fun Project Name]
**What it is:** [1 sentence]
**Why it's cool:** [1 sentence]
**You'll learn:** [2-3 skills]
**Difficulty:** ⭐/⭐⭐/⭐⭐⭐
"""


def methinks_generate(
    interests: str,
    skill_level: str,
    problem: str,
    provider: str
) -> str:
    """Generate project ideas based on user input."""

    if not interests.strip() and not problem.strip():
        return """### 👋 Hey there! I'm Mr. MeThinks!

I help you figure out what to build. Tell me a bit about yourself:

- **What are you into?** (games, music, productivity, social, data, etc.)
- **What bugs you?** (a problem you wish was solved)
- **What's your vibe?** (just learning, want a challenge, etc.)

Fill in the boxes and I'll cook up some perfect project ideas for you! 🧠✨"""

    connector = get_connector(provider, session_id="methinks")

    # Build the prompt
    prompt = f"""{METHINKS_PERSONALITY}

Here's who I'm helping:

**Their interests:** {interests if interests.strip() else "Not specified"}
**Skill level:** {skill_level}
**Problem they want to solve:** {problem if problem.strip() else "Not specified - just looking for cool ideas"}

Generate 3 perfect project ideas for them! Be specific and concrete - these should be things they can actually build."""

    async def _think():
        resp = await connector.send_message(prompt)
        return resp.get("content", "Hmm, my brain got stuck! Try again?")

    result = run_async(_think())
    return result


def methinks_random(provider: str) -> Tuple[str, str, str]:
    """Generate random interests for inspiration."""
    import random

    interests_options = [
        "music and playlists",
        "gaming and esports",
        "cooking and recipes",
        "fitness and health",
        "movies and TV shows",
        "books and reading",
        "travel and places",
        "finance and budgeting",
        "social media",
        "productivity and habits",
        "memes and humor",
        "pets and animals",
        "art and design",
        "news and current events",
        "dating and relationships",
        "learning and education",
    ]

    problems_options = [
        "I always forget things",
        "I waste too much time on my phone",
        "I can't decide what to watch/eat/do",
        "I lose track of my goals",
        "I want to share stuff with friends easier",
        "I have too many tabs open",
        "I can't find good recommendations",
        "My files are a mess",
        "I don't drink enough water",
        "I want to learn something new every day",
        "",  # Sometimes no problem, just exploring
        "",
    ]

    return (
        random.choice(interests_options),
        "Just starting out",
        random.choice(problems_options),
    )


def extract_idea_by_number(idea_text: str, number: int) -> str:
    """Extract a specific idea (1, 2, or 3) from Mr. MeThinks output."""
    lines = idea_text.split('\n')
    ideas = []
    current_idea = None

    for i, line in enumerate(lines):
        if '###' in line and '🎯' in line:
            # Found a project header
            name = line.replace('###', '').replace('🎯', '').strip()
            # Look for "What it is" in next few lines
            desc = ""
            for j in range(i+1, min(i+6, len(lines))):
                if 'What it is' in lines[j]:
                    desc = lines[j].split(':', 1)[-1].strip().strip('*')
                    break
            ideas.append({"name": name, "desc": desc})

    if 0 < number <= len(ideas):
        idea = ideas[number - 1]
        return f"Build {idea['name']}: {idea['desc']}"

    return "Build me something cool"


def use_idea_in_vibe(idea_text: str) -> str:
    """Extract the first buildable prompt from idea text for Vibe Code."""
    return extract_idea_by_number(idea_text, 1)


# =============================================================================
# UI LAYOUT
# =============================================================================

def create_ui():
    """Create the Gradio interface."""

    providers = get_available_providers()
    default_provider = providers[0]

    with gr.Blocks(title="Nexus - Vibe Code") as app:

        # Header
        gr.Markdown("""
# 🎨 Nexus Vibe Code

**Build with AI, your way.** Describe what you want, get suggestions, iterate together.
        """)

        with gr.Tabs():

            # =================================================================
            # VIBE CODE TAB - Main experience
            # =================================================================
            with gr.TabItem("🎨 Vibe Code", id="vibe"):

                with gr.Row():
                    # Main chat area
                    with gr.Column(scale=3):

                        vibe_chat = gr.Chatbot(
                            label="Vibe Code",
                            height=450,
                            placeholder="Tell me what you want to build...",
                        )

                        # Sparks display area
                        sparks_display = gr.Markdown(
                            value="",
                            elem_classes=["sparks-area"],
                        )

                        with gr.Row():
                            vibe_input = gr.Textbox(
                                label="Your message",
                                placeholder="Build me a...",
                                scale=4,
                                show_label=False,
                            )
                            vibe_send = gr.Button("Send", variant="primary", scale=1)

                        # Quick spark buttons (for fast mode)
                        with gr.Row(visible=True) as spark_buttons:
                            spark_1 = gr.Button("1️⃣", size="sm", scale=1)
                            spark_2 = gr.Button("2️⃣", size="sm", scale=1)
                            spark_3 = gr.Button("3️⃣", size="sm", scale=1)
                            gr.Button("", scale=3, visible=False)  # spacer

                    # Sidebar
                    with gr.Column(scale=1):

                        gr.Markdown("### ⚙️ Settings")

                        vibe_provider = gr.Dropdown(
                            choices=providers,
                            value=default_provider,
                            label="AI Provider",
                        )

                        chill_mode = gr.Checkbox(
                            label="🌙 Chill Mode",
                            value=True,
                            info="Explains options instead of just buttons"
                        )

                        new_session_btn = gr.Button("🆕 New Session", variant="secondary")

                        gr.Markdown("---")

                        # Files sidebar
                        files_display = gr.Markdown(
                            value="*No files created yet*",
                            label="Files",
                        )

                        download_btn = gr.Button("📥 Download All", size="sm")

                # Hidden state
                files_state = gr.State([])

            # =================================================================
            # MR. METHINKS TAB - Idea Generator
            # =================================================================
            with gr.TabItem("🧠 Mr. MeThinks", id="methinks"):

                gr.Markdown("""
## 🧠 Mr. MeThinks

**Don't know what to build? I got you!**

Tell me about yourself and I'll suggest perfect project ideas tailored just for you.
                """)

                with gr.Row():
                    with gr.Column(scale=1):

                        methinks_interests = gr.Textbox(
                            label="🎯 What are you into?",
                            placeholder="games, music, productivity, social media, data...",
                            lines=2,
                        )

                        methinks_skill = gr.Radio(
                            label="📊 Your skill level",
                            choices=["Just starting out", "Know the basics", "Pretty comfortable", "Ready for a challenge"],
                            value="Just starting out",
                        )

                        methinks_problem = gr.Textbox(
                            label="😤 What bugs you? (optional)",
                            placeholder="A problem you wish was solved... or leave blank!",
                            lines=2,
                        )

                        methinks_provider = gr.Dropdown(
                            choices=providers,
                            value=default_provider,
                            label="AI Provider",
                        )

                        with gr.Row():
                            methinks_btn = gr.Button("🧠 Think!", variant="primary", scale=2)
                            methinks_random_btn = gr.Button("🎲 Random", scale=1)

                    with gr.Column(scale=2):

                        methinks_result = gr.Markdown(
                            value="""### 👋 Hey there! I'm Mr. MeThinks!

I help you figure out what to build. Tell me a bit about yourself:

- **What are you into?** (games, music, productivity, social, data, etc.)
- **What bugs you?** (a problem you wish was solved)
- **What's your vibe?** (just learning, want a challenge, etc.)

Fill in the boxes on the left and hit **Think!** 🧠✨

Or hit **Random** 🎲 for instant inspiration!"""
                        )

                        gr.Markdown("### 👆 Pick one to build:")
                        with gr.Row():
                            idea_btn_1 = gr.Button("1️⃣ Build Idea 1", scale=1)
                            idea_btn_2 = gr.Button("2️⃣ Build Idea 2", scale=1)
                            idea_btn_3 = gr.Button("3️⃣ Build Idea 3", scale=1)

                # Store the last result for idea extraction
                methinks_last_result = gr.State("")

            # =================================================================
            # QUICK TOOLS TAB
            # =================================================================
            with gr.TabItem("🔧 Quick Tools", id="tools"):

                gr.Markdown("""
### Quick Tools

One-click tools for common tasks. No conversation needed.
                """)

                with gr.Tabs():

                    # Fix tab
                    with gr.TabItem("🔧 Fix Code"):
                        gr.Markdown("**Paste an error, get a fix.**")

                        fix_error = gr.Textbox(
                            label="Error message",
                            placeholder="TypeError: Cannot read property 'map' of undefined",
                            lines=3,
                        )
                        fix_code = gr.Textbox(
                            label="Your code (optional)",
                            placeholder="Paste the problematic code here...",
                            lines=6,
                        )
                        fix_provider = gr.Dropdown(
                            choices=providers,
                            value=default_provider,
                            label="Provider",
                        )
                        fix_btn = gr.Button("🔧 Fix It", variant="primary")
                        fix_result = gr.Markdown()

                    # Explain tab
                    with gr.TabItem("❓ Explain"):
                        gr.Markdown("**Paste anything, get an explanation.**")

                        explain_input = gr.Textbox(
                            label="Code or error to explain",
                            placeholder="Paste code, an error, or anything you want explained...",
                            lines=8,
                        )
                        explain_provider = gr.Dropdown(
                            choices=providers,
                            value=default_provider,
                            label="Provider",
                        )
                        explain_btn = gr.Button("❓ Explain", variant="primary")
                        explain_result = gr.Markdown()

            # =================================================================
            # SETTINGS TAB
            # =================================================================
            with gr.TabItem("⚙️ Settings", id="settings"):

                gr.Markdown("### Provider Status")

                status_lines = []
                for provider, env_var in [
                    ("OpenAI", "OPENAI_API_KEY"),
                    ("Anthropic", "ANTHROPIC_API_KEY"),
                    ("Google", "GOOGLE_API_KEY"),
                    ("DeepSeek", "DEEPSEEK_API_KEY"),
                    ("xAI", "XAI_API_KEY"),
                ]:
                    if os.getenv(env_var):
                        status_lines.append(f"- ✅ **{provider}**: Ready")
                    else:
                        status_lines.append(f"- ❌ **{provider}**: Not configured")

                status_lines.append(f"- 🏠 **Ollama**: {'Available' if shutil.which('ollama') else 'Not installed'}")

                gr.Markdown("\n".join(status_lines))

                gr.Markdown("""
---

### Setup

1. Copy `.env.example` to `.env`
2. Add your API keys
3. Restart the UI

```bash
cp .env.example .env
nano .env  # Add your keys
python ui.py
```

**Get API keys:**
- [OpenAI](https://platform.openai.com/api-keys)
- [Anthropic](https://console.anthropic.com/)
- [Google](https://makersuite.google.com/app/apikey)
- [DeepSeek](https://platform.deepseek.com/)
- [Ollama](https://ollama.ai/) (free, local)
                """)

        # =====================================================================
        # EVENT HANDLERS
        # =====================================================================

        # Vibe Code handlers
        def handle_vibe_send(message, history, provider, chill, files):
            return vibe_code_respond(message, history, provider, chill, files)

        vibe_send.click(
            handle_vibe_send,
            inputs=[vibe_input, vibe_chat, vibe_provider, chill_mode, files_state],
            outputs=[vibe_input, vibe_chat, files_state, files_display, sparks_display],
        )

        vibe_input.submit(
            handle_vibe_send,
            inputs=[vibe_input, vibe_chat, vibe_provider, chill_mode, files_state],
            outputs=[vibe_input, vibe_chat, files_state, files_display, sparks_display],
        )

        # Spark button handlers
        def send_spark(num, history, provider, chill, files):
            return vibe_code_respond(str(num), history, provider, chill, files)

        spark_1.click(
            lambda h, p, c, f: send_spark(1, h, p, c, f),
            inputs=[vibe_chat, vibe_provider, chill_mode, files_state],
            outputs=[vibe_input, vibe_chat, files_state, files_display, sparks_display],
        )
        spark_2.click(
            lambda h, p, c, f: send_spark(2, h, p, c, f),
            inputs=[vibe_chat, vibe_provider, chill_mode, files_state],
            outputs=[vibe_input, vibe_chat, files_state, files_display, sparks_display],
        )
        spark_3.click(
            lambda h, p, c, f: send_spark(3, h, p, c, f),
            inputs=[vibe_chat, vibe_provider, chill_mode, files_state],
            outputs=[vibe_input, vibe_chat, files_state, files_display, sparks_display],
        )

        # New session
        new_session_btn.click(
            new_vibe_session,
            outputs=[vibe_chat, files_state, files_display, sparks_display],
        )

        # Quick tools handlers
        fix_btn.click(
            quick_fix,
            inputs=[fix_error, fix_code, fix_provider],
            outputs=[fix_result],
        )

        explain_btn.click(
            quick_explain,
            inputs=[explain_input, explain_provider],
            outputs=[explain_result],
        )

        # Mr. MeThinks handlers
        def handle_methinks(interests, skill, problem, provider):
            result = methinks_generate(interests, skill, problem, provider)
            return result, result  # Return to display and store

        methinks_btn.click(
            handle_methinks,
            inputs=[methinks_interests, methinks_skill, methinks_problem, methinks_provider],
            outputs=[methinks_result, methinks_last_result],
        )

        def handle_random():
            interests, skill, problem = methinks_random(default_provider)
            return interests, skill, problem

        methinks_random_btn.click(
            handle_random,
            outputs=[methinks_interests, methinks_skill, methinks_problem],
        )

        # Idea buttons - pick a specific idea to build
        def use_idea_n(last_result, idea_num):
            if not last_result:
                return [], [], "*No files created yet*", "💡 **Hit 'Think!' first to generate ideas!**"

            # Extract the specific idea
            prompt = extract_idea_by_number(last_result, idea_num)

            # Add as first message in a new session
            new_history = [{"role": "user", "content": f"🚀 **From Mr. MeThinks:**\n\n{prompt}"}]

            return new_history, [], "*No files created yet*", f"💡 **Idea {idea_num} loaded!** Go to 🎨 Vibe Code tab and hit Send!"

        idea_btn_1.click(
            lambda r: use_idea_n(r, 1),
            inputs=[methinks_last_result],
            outputs=[vibe_chat, files_state, files_display, sparks_display],
        )
        idea_btn_2.click(
            lambda r: use_idea_n(r, 2),
            inputs=[methinks_last_result],
            outputs=[vibe_chat, files_state, files_display, sparks_display],
        )
        idea_btn_3.click(
            lambda r: use_idea_n(r, 3),
            inputs=[methinks_last_result],
            outputs=[vibe_chat, files_state, files_display, sparks_display],
        )

    return app


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("🎨 Starting Nexus Vibe Code...")
    print(f"📁 Projects: {PROJECTS_DIR.absolute()}")
    print()

    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True,
    )
