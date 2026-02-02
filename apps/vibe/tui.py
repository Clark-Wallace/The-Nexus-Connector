#!/usr/bin/env python3
"""
Nexus Vibe Code TUI - A beautiful terminal interface for building with AI.

Run with: python -m apps.vibe.tui
Or via CLI: nexus vibe --tui
"""

import asyncio
import os
from pathlib import Path
from typing import List

# Load environment
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical, ScrollableContainer
from textual.widgets import Static, Button, Input, Markdown, Log
from textual.binding import Binding

# Import from the Nexus library
from nexus import NexusConnector

# Import from our local sparks module
from .sparks import generate_sparks


# =============================================================================
# CUSTOM WIDGETS
# =============================================================================

class SparkButton(Button):
    """A spark suggestion button."""

    def __init__(self, icon: str, label: str, desc: str, index: int):
        super().__init__(f"{icon} {label}", id=f"spark_{index}")
        self.spark_label = label
        self.spark_desc = desc
        self.spark_index = index


class ChatMessage(Static):
    """A single chat message."""

    def __init__(self, role: str, message_content: str):
        self.msg_role = role
        self.msg_content = message_content
        super().__init__()

    def compose(self) -> ComposeResult:
        if self.msg_role == "user":
            yield Static(f"[bold cyan]You:[/bold cyan] {self.msg_content}", classes="user-msg")
        else:
            yield Markdown(self.msg_content, classes="assistant-msg")


class FileItem(Static):
    """A file in the sidebar."""

    def __init__(self, filename: str):
        ext = Path(filename).suffix.lower()
        icons = {
            ".py": "🐍", ".js": "📜", ".ts": "📘", ".html": "🌐",
            ".css": "🎨", ".json": "📋", ".md": "📝", ".yaml": "⚙️",
        }
        icon = icons.get(ext, "📄")
        super().__init__(f"{icon} {filename}")


# =============================================================================
# MAIN APP
# =============================================================================

class VibeCodeApp(App):
    """Vibe Code TUI Application."""

    CSS = """
    Screen {
        layout: grid;
        grid-size: 4 3;
        grid-rows: auto 1fr auto;
    }

    #header-panel {
        column-span: 4;
        height: 3;
        background: $primary-darken-2;
        padding: 0 1;
    }

    #chat-panel {
        column-span: 3;
        row-span: 1;
        border: solid $primary;
        padding: 1;
    }

    #sidebar {
        column-span: 1;
        row-span: 1;
        border: solid $secondary;
        padding: 1;
    }

    #sparks-panel {
        column-span: 3;
        height: auto;
        max-height: 12;
        border: solid $success;
        padding: 1;
    }

    #input-panel {
        column-span: 3;
        height: 3;
        padding: 0 1;
    }

    #files-panel {
        column-span: 1;
        height: auto;
        border: solid $warning;
        padding: 1;
    }

    .spark-row {
        height: 3;
        layout: horizontal;
    }

    SparkButton {
        margin: 0 1;
        min-width: 16;
    }

    #chat-scroll {
        height: 100%;
    }

    .user-msg {
        margin: 1 0;
        padding: 0 1;
        background: $primary-darken-3;
    }

    .assistant-msg {
        margin: 1 0;
        padding: 0 1;
    }

    #tool-log {
        height: 6;
        border: solid $error;
        margin-top: 1;
    }

    #status-bar {
        column-span: 4;
        height: 1;
        background: $primary-darken-2;
    }

    .hidden {
        display: none;
    }
    """

    BINDINGS = [
        Binding("ctrl+c", "quit", "Quit"),
        Binding("ctrl+n", "new_session", "New Session"),
        Binding("ctrl+i", "ideas", "Mr. MeThinks"),
        Binding("escape", "clear_input", "Clear"),
    ]

    def __init__(self, provider: str = "openai"):
        super().__init__()
        self.provider = provider
        self.connector = None
        self.files_created: List[str] = []
        self.last_response = ""
        self.current_sparks = []
        self.chill_mode = True

    def compose(self) -> ComposeResult:
        yield Static(
            f"[bold]🎨 Vibe Code[/bold] | Provider: {self.provider} | [dim]Ctrl+N: New | Ctrl+I: Ideas | Ctrl+C: Quit[/dim]",
            id="header-panel"
        )

        # Main chat area
        with ScrollableContainer(id="chat-panel"):
            yield Static("[dim]Tell me what you want to build...[/dim]", id="chat-placeholder")

        # Sidebar
        with Vertical(id="sidebar"):
            yield Static("[bold]⚙️ Settings[/bold]")
            yield Button("🌙 Chill Mode", id="toggle-chill", variant="primary")
            yield Button("🆕 New Session", id="new-session")
            yield Static("")
            yield Static("[bold]📁 Files[/bold]")
            with Vertical(id="files-list"):
                yield Static("[dim]No files yet[/dim]", id="no-files")

        # Sparks panel
        with Vertical(id="sparks-panel"):
            yield Static("[bold cyan]✨ What's next?[/bold cyan]", id="sparks-title")
            with Horizontal(classes="spark-row"):
                yield SparkButton("🚀", "Build API", "REST backend", 0)
                yield SparkButton("🎨", "Build UI", "Frontend", 1)
                yield SparkButton("🛠️", "CLI Tool", "Command line", 2)
            with Horizontal(classes="spark-row"):
                yield SparkButton("🤖", "Bot", "Discord/Slack", 3)
                yield SparkButton("📊", "Dashboard", "Data viz", 4)

        # Input area
        with Horizontal(id="input-panel"):
            yield Input(placeholder="Type what you want to build...", id="chat-input")
            yield Button("Send", id="send-btn", variant="success")

        # Tool log (hidden initially)
        yield Log(id="tool-log", classes="hidden")

        # Status bar
        yield Static("[dim]Ready to vibe[/dim]", id="status-bar")

    async def on_mount(self) -> None:
        """Initialize the connector."""
        self.connector = self._create_connector()
        self.query_one("#chat-input", Input).focus()

    def _create_connector(self) -> NexusConnector:
        """Create a new connector."""
        api_key = os.getenv(f"{self.provider.upper()}_API_KEY", "")
        return NexusConnector(
            provider=self.provider,
            api_key=api_key,
            workspace=str(Path.cwd()),
        )

    def _update_sparks(self, sparks: List[dict]) -> None:
        """Update the spark buttons."""
        self.current_sparks = sparks

        # Get the spark rows
        spark_rows = self.query(".spark-row")

        # Update first row (3 sparks)
        if len(spark_rows) >= 1:
            buttons = list(spark_rows[0].query(SparkButton))
            for i, btn in enumerate(buttons):
                if i < len(sparks):
                    spark = sparks[i]
                    btn.label = f"{spark['icon']} {spark['label']}"
                    btn.spark_label = spark['label']
                    btn.spark_desc = spark.get('desc', '')

        # Update second row (remaining sparks)
        if len(spark_rows) >= 2:
            buttons = list(spark_rows[1].query(SparkButton))
            for i, btn in enumerate(buttons):
                idx = i + 3
                if idx < len(sparks):
                    spark = sparks[idx]
                    btn.label = f"{spark['icon']} {spark['label']}"
                    btn.spark_label = spark['label']
                    btn.spark_desc = spark.get('desc', '')

    def _add_message(self, role: str, content: str) -> None:
        """Add a message to the chat."""
        chat_panel = self.query_one("#chat-panel", ScrollableContainer)

        # Remove placeholder if it exists
        try:
            placeholder = self.query_one("#chat-placeholder", Static)
            placeholder.remove()
        except Exception:
            pass  # Already removed

        # Add message
        chat_panel.mount(ChatMessage(role, content))
        chat_panel.scroll_end()

    def _update_files(self) -> None:
        """Update the files sidebar."""
        files_list = self.query_one("#files-list", Vertical)

        # Clear existing "no files" message
        try:
            no_files = self.query_one("#no-files", Static)
            no_files.remove()
        except Exception:
            pass  # Already removed

        # Remove existing file items
        for child in list(files_list.children):
            if isinstance(child, FileItem):
                child.remove()

        # Add files
        if self.files_created:
            for f in self.files_created[-8:]:  # Last 8 files
                files_list.mount(FileItem(f))
        else:
            files_list.mount(Static("[dim]No files yet[/dim]", id="no-files"))

    def _update_status(self, message: str) -> None:
        """Update the status bar."""
        self.query_one("#status-bar", Static).update(message)

    async def _send_message(self, message: str) -> None:
        """Send a message and handle the response."""
        if not message.strip():
            return

        # Add user message
        self._add_message("user", message)
        self._update_status("[bold yellow]🔨 Building...[/bold yellow]")

        # Show tool log
        tool_log = self.query_one("#tool-log", Log)
        tool_log.remove_class("hidden")
        tool_log.clear()

        # Check if build request
        is_build = any(word in message.lower() for word in [
            "build", "create", "make", "add", "implement", "write", "generate"
        ])

        try:
            if is_build:
                # Track tool calls
                def on_tool_call(tc):
                    name = tc.get("name", "unknown")
                    args = tc.get("arguments", {})
                    detail = args.get("path", args.get("command", ""))[:40]
                    icon = {"create_file": "📝", "execute_command": "⚡"}.get(name, "🔧")
                    tool_log.write_line(f"{icon} {name} {detail}")

                self.connector._on_tool_call = on_tool_call

                # Execute task
                result = await self.connector.execute_task(message, show_progress=False)

                # Track files
                for f in result.files_created:
                    if f not in self.files_created:
                        self.files_created.append(f)

                # Format response
                if result.success:
                    response = f"✅ **Done!**\n\n{result.content[:1000]}"
                    if result.files_created:
                        response += f"\n\n📁 **Files:** {', '.join(result.files_created)}"
                else:
                    response = f"⚠️ **Issues:**\n\n{result.content}"

                self.last_response = result.content

            else:
                # Regular chat
                resp = await self.connector.send_message(message)
                response = resp.get("content", "No response")
                self.last_response = response

            # Add response
            self._add_message("assistant", response)

            # Update sparks
            sparks = generate_sparks(self.last_response)
            self._update_sparks(sparks)

            # Update files
            self._update_files()

            self._update_status("[bold green]✅ Ready[/bold green]")

        except Exception as e:
            self._add_message("assistant", f"❌ **Error:** {str(e)}")
            self._update_status(f"[bold red]Error: {str(e)[:30]}[/bold red]")

        # Hide tool log after a bit
        tool_log.add_class("hidden")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "send-btn":
            input_widget = self.query_one("#chat-input", Input)
            message = input_widget.value
            input_widget.value = ""
            await self._send_message(message)

        elif button_id == "new-session":
            self.action_new_session()

        elif button_id == "toggle-chill":
            self.chill_mode = not self.chill_mode
            mode = "🌙 Chill" if self.chill_mode else "⚡ Fast"
            event.button.label = f"{mode} Mode"

        elif button_id and button_id.startswith("spark_"):
            # Spark button clicked
            if isinstance(event.button, SparkButton):
                message = f"{event.button.spark_label}: {event.button.spark_desc}"
                await self._send_message(message)

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle enter key in input."""
        if event.input.id == "chat-input":
            message = event.value
            event.input.value = ""
            await self._send_message(message)

    def action_new_session(self) -> None:
        """Start a new session."""
        self.connector = self._create_connector()
        self.files_created = []
        self.last_response = ""

        # Clear chat
        chat_panel = self.query_one("#chat-panel", ScrollableContainer)
        for child in list(chat_panel.children):
            child.remove()
        chat_panel.mount(Static("[dim]Tell me what you want to build...[/dim]", id="chat-placeholder"))

        # Reset sparks
        self._update_sparks(generate_sparks(""))

        # Clear files
        self._update_files()

        self._update_status("[dim]New session started[/dim]")

    def action_ideas(self) -> None:
        """Open Mr. MeThinks."""
        self._add_message("assistant", """🧠 **Mr. MeThinks - Idea Generator**

Tell me:
- What are you into? (games, music, productivity...)
- Your skill level? (beginner/intermediate/advanced)
- A problem to solve? (optional)

Example: "I like music, I'm a beginner, I want to organize my playlists"
""")

    def action_clear_input(self) -> None:
        """Clear the input."""
        self.query_one("#chat-input", Input).value = ""

    def action_quit(self) -> None:
        """Quit the app."""
        self.exit()


def run_tui(provider: str = "openai"):
    """Run the Vibe Code TUI."""
    app = VibeCodeApp(provider=provider)
    app.run()


if __name__ == "__main__":
    run_tui()
