#!/usr/bin/env python3
"""
Nexus Connector UI - A friendly web interface for building with AI.

Run with: python ui.py
Opens in your browser at http://localhost:7860
"""

import os
import json
import shutil
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Tuple
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

# Session store for persistent conversations (the Nexus way!)
from nexus.web import SessionStore
SESSION_STORE = SessionStore(timeout_hours=24)


def get_connector_for_build(provider: str, api_key: Optional[str] = None):
    """Get a fresh NexusConnector for building (no session needed)."""
    from nexus import NexusConnector

    # Get API key from param or environment
    if not api_key:
        key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "xai": "XAI_API_KEY",
        }
        if provider in key_map:
            api_key = os.getenv(key_map[provider])

    return NexusConnector(
        provider=provider,
        api_key=api_key,
        workspace=str(PROJECTS_DIR / "current"),
    )


def get_session_connector(provider: str, api_key: Optional[str] = None, session_id: str = "default"):
    """Get a persistent connector from the session store (the Nexus way!)."""
    from nexus import NexusConnector

    # Get API key from param or environment
    if not api_key:
        key_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "xai": "XAI_API_KEY",
        }
        if provider in key_map:
            api_key = os.getenv(key_map[provider])

    # Create a unique session key based on provider
    full_session_id = f"{session_id}_{provider}"

    # Get or create connector from session store
    async def _get():
        return await SESSION_STORE.get_or_create(
            full_session_id,
            lambda: NexusConnector(
                provider=provider,
                api_key=api_key,
                workspace=str(PROJECTS_DIR / "current"),
            )
        )

    return run_async(_get())


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


# =============================================================================
# CHAT FUNCTIONS
# =============================================================================

def chat_response(message: str, history: List[dict], provider: str, api_key: str) -> Tuple[str, List[dict]]:
    """Handle chat messages using Nexus session persistence."""
    if not message or not message.strip():
        return "", history

    # Add user message to history for display
    history = history + [{"role": "user", "content": message}]

    try:
        # Get persistent connector from session store
        # This maintains conversation history automatically!
        connector = get_session_connector(
            provider,
            api_key if api_key and api_key.strip() else None,
            session_id="ui_chat"
        )

        async def _chat():
            response = await connector.send_message(message)
            return response.get("content", "No response")

        response = run_async(_chat())
        history = history + [{"role": "assistant", "content": response}]
        return "", history

    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        history = history + [{"role": "assistant", "content": error_msg}]
        return "", history


# =============================================================================
# BUILD FUNCTIONS
# =============================================================================

def build_project(
    description: str,
    project_name: str,
    provider: str,
    api_key: str,
    progress=gr.Progress()
) -> Tuple[str, str, str]:
    """Build a project from description."""
    if not description.strip():
        return "Please describe what you want to build.", "", ""

    # Create project directory
    if not project_name.strip():
        project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    project_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project_name)
    project_path = PROJECTS_DIR / project_name

    # Clean up if exists
    if project_path.exists():
        shutil.rmtree(project_path)
    project_path.mkdir(parents=True)

    try:
        progress(0.1, desc="Starting build...")

        connector = get_connector_for_build(provider, api_key if api_key and api_key.strip() else None)
        connector.workspace = str(project_path)

        async def _build():
            result = await connector.execute_task(description, show_progress=False)
            return result

        progress(0.3, desc="AI is working...")
        result = run_async(_build())
        progress(0.9, desc="Finishing up...")

        # Save project metadata
        metadata = {
            "name": project_name,
            "description": description,
            "created": datetime.now().isoformat(),
            "provider": provider,
            "success": result.success,
            "files_created": result.files_created,
            "files_modified": result.files_modified,
            "iterations": result.iterations,
            "tokens_used": result.tokens_used,
        }

        with open(project_path / ".nexus_project.json", "w") as f:
            json.dump(metadata, f, indent=2)

        # Build file tree
        file_tree = get_file_tree(project_path)

        # Get status message
        if result.success:
            status = f"""✅ **Project Built Successfully!**

**Project:** {project_name}
**Location:** `{project_path}`

**Files Created:** {len(result.files_created)}
**Iterations:** {result.iterations}
**Tokens Used:** {result.tokens_used}

{result.content[:500] + '...' if len(result.content) > 500 else result.content}
"""
        else:
            status = f"""⚠️ **Build completed with issues**

{result.content}
"""

        progress(1.0, desc="Done!")
        return status, file_tree, project_name

    except Exception as e:
        return f"❌ **Error:** {str(e)}", "", ""


def get_file_tree(path: Path, prefix: str = "") -> str:
    """Generate a file tree string."""
    if not path.exists():
        return ""

    items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
    tree = []

    for i, item in enumerate(items):
        if item.name.startswith(".") and item.name != ".nexus_project.json":
            continue

        is_last = i == len(items) - 1
        current_prefix = "└── " if is_last else "├── "

        if item.is_dir():
            tree.append(f"{prefix}{current_prefix}📁 {item.name}/")
            next_prefix = prefix + ("    " if is_last else "│   ")
            tree.append(get_file_tree(item, next_prefix))
        else:
            # Get file icon based on extension
            ext = item.suffix.lower()
            icon = {
                ".py": "🐍",
                ".js": "📜",
                ".ts": "📘",
                ".html": "🌐",
                ".css": "🎨",
                ".json": "📋",
                ".md": "📝",
                ".txt": "📄",
                ".yaml": "⚙️",
                ".yml": "⚙️",
                ".sql": "🗃️",
                ".sh": "💻",
            }.get(ext, "📄")
            tree.append(f"{prefix}{current_prefix}{icon} {item.name}")

    return "\n".join(tree)


def view_file(project_name: str, file_path: str) -> str:
    """View a file's contents."""
    if not project_name or not file_path:
        return "Select a project and file to view."

    full_path = PROJECTS_DIR / project_name / file_path.strip()

    if not full_path.exists():
        return f"File not found: {file_path}"

    if full_path.is_dir():
        return f"This is a directory: {file_path}"

    try:
        content = full_path.read_text()
        ext = full_path.suffix.lower()
        lang = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".html": "html",
            ".css": "css",
            ".json": "json",
            ".md": "markdown",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".sql": "sql",
            ".sh": "bash",
        }.get(ext, "")

        return f"```{lang}\n{content}\n```"
    except Exception as e:
        return f"Error reading file: {e}"


# =============================================================================
# PROJECT MANAGEMENT
# =============================================================================

def list_projects() -> List[List[str]]:
    """List all saved projects."""
    projects = []

    for project_dir in sorted(PROJECTS_DIR.iterdir(), reverse=True):
        if not project_dir.is_dir():
            continue

        metadata_file = project_dir / ".nexus_project.json"
        if metadata_file.exists():
            try:
                with open(metadata_file) as f:
                    meta = json.load(f)

                projects.append([
                    meta.get("name", project_dir.name),
                    meta.get("description", "")[:50] + "..." if len(meta.get("description", "")) > 50 else meta.get("description", ""),
                    meta.get("created", "")[:10],
                    "✅" if meta.get("success") else "⚠️",
                    str(len(meta.get("files_created", []))),
                ])
            except:
                projects.append([
                    project_dir.name,
                    "(No metadata)",
                    "",
                    "?",
                    "?",
                ])
        else:
            # Count files
            file_count = sum(1 for _ in project_dir.rglob("*") if _.is_file())
            projects.append([
                project_dir.name,
                "(Imported project)",
                "",
                "📁",
                str(file_count),
            ])

    return projects


def load_project(project_name: str) -> Tuple[str, str, str]:
    """Load a project's details."""
    if not project_name:
        return "", "", ""

    project_path = PROJECTS_DIR / project_name

    if not project_path.exists():
        return "Project not found", "", ""

    # Load metadata
    metadata_file = project_path / ".nexus_project.json"
    if metadata_file.exists():
        with open(metadata_file) as f:
            meta = json.load(f)

        info = f"""## {meta.get('name', project_name)}

**Description:** {meta.get('description', 'N/A')}

**Created:** {meta.get('created', 'Unknown')}
**Provider:** {meta.get('provider', 'Unknown')}
**Status:** {'✅ Success' if meta.get('success') else '⚠️ Issues'}
**Files:** {len(meta.get('files_created', []))} created, {len(meta.get('files_modified', []))} modified
**Tokens:** {meta.get('tokens_used', 'N/A')}
"""
    else:
        info = f"## {project_name}\n\n(No metadata available)"

    # Get file tree
    file_tree = get_file_tree(project_path)

    return info, file_tree, project_name


def delete_project(project_name: str) -> Tuple[str, List[List[str]]]:
    """Delete a project."""
    if not project_name:
        return "No project selected", list_projects()

    project_path = PROJECTS_DIR / project_name

    if project_path.exists():
        shutil.rmtree(project_path)
        return f"✅ Deleted: {project_name}", list_projects()

    return f"Project not found: {project_name}", list_projects()


def download_project(project_name: str) -> Optional[str]:
    """Create a zip file of the project for download."""
    if not project_name:
        return None

    project_path = PROJECTS_DIR / project_name

    if not project_path.exists():
        return None

    # Create zip
    zip_path = PROJECTS_DIR / f"{project_name}.zip"
    shutil.make_archive(str(zip_path.with_suffix("")), "zip", project_path)

    return str(zip_path)


def get_project_files(project_name: str) -> List[str]:
    """Get list of files in a project for dropdown."""
    if not project_name:
        return []

    project_path = PROJECTS_DIR / project_name
    if not project_path.exists():
        return []

    files = []
    for f in project_path.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            rel_path = f.relative_to(project_path)
            files.append(str(rel_path))

    return sorted(files)


# =============================================================================
# UI LAYOUT
# =============================================================================

def create_ui():
    """Create the Gradio interface."""

    # Check for available providers
    available_providers = []
    if os.getenv("ANTHROPIC_API_KEY"):
        available_providers.append("anthropic")
    if os.getenv("OPENAI_API_KEY"):
        available_providers.append("openai")
    if os.getenv("GOOGLE_API_KEY"):
        available_providers.append("google")
    if os.getenv("DEEPSEEK_API_KEY"):
        available_providers.append("deepseek")
    if os.getenv("XAI_API_KEY"):
        available_providers.append("xai")
    available_providers.append("ollama")  # Always available if installed

    default_provider = available_providers[0] if available_providers else "ollama"

    with gr.Blocks(title="Nexus Connector") as app:

        gr.Markdown("""
        # 🚀 Nexus Connector

        **Build apps with AI. No coding required.**

        Describe what you want, and Nexus will build it for you.
        """)

        with gr.Tabs():
            # =================================================================
            # BUILD TAB
            # =================================================================
            with gr.TabItem("🔨 Build", id="build"):
                with gr.Row():
                    with gr.Column(scale=2):
                        build_description = gr.Textbox(
                            label="What do you want to build?",
                            placeholder="Example: Create a Flask REST API with user authentication, SQLite database, and unit tests",
                            lines=4,
                        )

                        with gr.Row():
                            build_name = gr.Textbox(
                                label="Project Name (optional)",
                                placeholder="my-awesome-project",
                                scale=2,
                            )
                            build_provider = gr.Dropdown(
                                choices=["anthropic", "openai", "google", "deepseek", "xai", "ollama"],
                                value=default_provider,
                                label="AI Provider",
                                scale=1,
                            )

                        build_btn = gr.Button("🚀 Build It!", variant="primary", size="lg")

                        build_status = gr.Markdown(label="Status")

                    with gr.Column(scale=1):
                        gr.Markdown("### 📁 Project Files")
                        build_files = gr.Markdown(
                            elem_classes=["file-tree"],
                            value="*Your project files will appear here*"
                        )

                # Quick templates
                gr.Markdown("### ⚡ Quick Templates")
                with gr.Row():
                    gr.Button("Flask API").click(
                        lambda: "Create a Flask REST API with CRUD endpoints for a todo list, including SQLite database and error handling",
                        outputs=build_description
                    )
                    gr.Button("CLI Tool").click(
                        lambda: "Create a Python CLI tool that converts CSV files to JSON, with argument parsing and help text",
                        outputs=build_description
                    )
                    gr.Button("Web Scraper").click(
                        lambda: "Create a Python web scraper that extracts article titles and links from a news website, saves to JSON",
                        outputs=build_description
                    )
                    gr.Button("Discord Bot").click(
                        lambda: "Create a Discord bot with commands: !hello, !roll (dice), !quote (random quote), using discord.py",
                        outputs=build_description
                    )

            # =================================================================
            # CHAT TAB
            # =================================================================
            with gr.TabItem("💬 Chat", id="chat"):
                chatbot = gr.Chatbot(
                    label="Chat with AI",
                    height=400,
                )

                with gr.Row():
                    chat_input = gr.Textbox(
                        label="Message",
                        placeholder="Ask anything...",
                        scale=4,
                        show_label=False,
                    )
                    chat_provider = gr.Dropdown(
                        choices=["anthropic", "openai", "google", "deepseek", "xai", "ollama"],
                        value=default_provider,
                        label="Provider",
                        scale=1,
                    )

                with gr.Row():
                    chat_btn = gr.Button("Send", variant="primary")
                    clear_btn = gr.Button("Clear")

            # =================================================================
            # PROJECTS TAB
            # =================================================================
            with gr.TabItem("📂 Projects", id="projects"):
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### Saved Projects")
                        refresh_btn = gr.Button("🔄 Refresh")

                        projects_table = gr.Dataframe(
                            headers=["Name", "Description", "Created", "Status", "Files"],
                            datatype=["str", "str", "str", "str", "str"],
                            value=list_projects(),
                            interactive=False,
                            wrap=True,
                        )

                        with gr.Row():
                            delete_btn = gr.Button("🗑️ Delete", variant="stop")
                            download_btn = gr.Button("📥 Download")

                    with gr.Column(scale=1):
                        project_info = gr.Markdown("*Select a project to view details*")
                        project_tree = gr.Markdown(elem_classes=["file-tree"])

                        with gr.Row():
                            file_dropdown = gr.Dropdown(
                                label="View File",
                                choices=[],
                                interactive=True,
                            )

                        file_content = gr.Markdown()

                # Hidden state for selected project
                selected_project = gr.State("")
                download_file = gr.File(label="Download", visible=False)

            # =================================================================
            # SETTINGS TAB
            # =================================================================
            with gr.TabItem("⚙️ Settings", id="settings"):
                gr.Markdown("""
                ### API Keys

                Add your API keys here, or set them in your `.env` file.

                Keys entered here are only stored in your browser session.
                """)

                api_key_input = gr.Textbox(
                    label="API Key (optional override)",
                    placeholder="sk-... or sk-ant-...",
                    type="password",
                )

                gr.Markdown("""
                ### Provider Status
                """)

                status_text = []
                for provider, env_var in [
                    ("Anthropic", "ANTHROPIC_API_KEY"),
                    ("OpenAI", "OPENAI_API_KEY"),
                    ("Google", "GOOGLE_API_KEY"),
                    ("DeepSeek", "DEEPSEEK_API_KEY"),
                    ("xAI", "XAI_API_KEY"),
                ]:
                    if os.getenv(env_var):
                        status_text.append(f"- ✅ **{provider}**: Configured")
                    else:
                        status_text.append(f"- ❌ **{provider}**: Not configured")

                status_text.append(f"- 🏠 **Ollama**: {'Available' if shutil.which('ollama') else 'Not installed'}")

                gr.Markdown("\n".join(status_text))

                gr.Markdown("""
                ### Quick Setup

                ```bash
                # Copy the example and add your keys
                cp .env.example .env
                nano .env  # Add your API keys
                ```

                Get API keys:
                - [Anthropic Console](https://console.anthropic.com/)
                - [OpenAI Platform](https://platform.openai.com/api-keys)
                - [Google AI Studio](https://makersuite.google.com/app/apikey)
                - [DeepSeek Platform](https://platform.deepseek.com/)
                - [Ollama](https://ollama.ai/) (free, runs locally)
                """)

        # =====================================================================
        # EVENT HANDLERS
        # =====================================================================

        # Build tab
        build_btn.click(
            build_project,
            inputs=[build_description, build_name, build_provider, api_key_input],
            outputs=[build_status, build_files, selected_project],
        )

        # Chat tab
        chat_btn.click(
            chat_response,
            inputs=[chat_input, chatbot, chat_provider, api_key_input],
            outputs=[chat_input, chatbot],
        )
        chat_input.submit(
            chat_response,
            inputs=[chat_input, chatbot, chat_provider, api_key_input],
            outputs=[chat_input, chatbot],
        )
        def clear_chat():
            """Clear chat history and session."""
            # Clear all chat sessions
            run_async(SESSION_STORE.clear())
            return []

        clear_btn.click(clear_chat, outputs=[chatbot])

        # Projects tab
        refresh_btn.click(list_projects, outputs=[projects_table])

        def on_project_select(evt: gr.SelectData, projects_data):
            if evt.index[0] < len(projects_data):
                project_name = projects_data[evt.index[0]][0]
                info, tree, name = load_project(project_name)
                files = get_project_files(project_name)
                return info, tree, name, gr.Dropdown(choices=files)
            return "", "", "", gr.Dropdown(choices=[])

        projects_table.select(
            on_project_select,
            inputs=[projects_table],
            outputs=[project_info, project_tree, selected_project, file_dropdown],
        )

        file_dropdown.change(
            view_file,
            inputs=[selected_project, file_dropdown],
            outputs=[file_content],
        )

        delete_btn.click(
            delete_project,
            inputs=[selected_project],
            outputs=[project_info, projects_table],
        )

        download_btn.click(
            download_project,
            inputs=[selected_project],
            outputs=[download_file],
        )

    return app


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Nexus Connector UI...")
    print(f"📁 Projects will be saved to: {PROJECTS_DIR.absolute()}")
    print()

    app = create_ui()
    app.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,  # Set to True to get a public URL
        inbrowser=True,  # Auto-open browser
    )
