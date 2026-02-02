"""
Nexus CLI - Command-line interface for The Nexus Connector.

Provides interactive chat, task execution, streaming, and provider comparison.
Designed as a backend-ready interface that any UI can build on.
"""

import asyncio
import json
import os
import sys
import select
from datetime import datetime

# Load .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from pathlib import Path
from typing import Optional, List, Dict, Any

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.live import Live
from rich.text import Text

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

from .core.unified_wrapper import UnifiedAIWrapper
from .core.base_connector import AIProvider


console = Console()

# Default config directory
NEXUS_DIR = Path.home() / ".nexus"
HISTORY_DIR = NEXUS_DIR / "history"
CONFIG_FILE = NEXUS_DIR / "config.yaml"


def load_config() -> Dict[str, Any]:
    """Load config from ~/.nexus/config.yaml"""
    if not CONFIG_FILE.exists():
        return {}

    if not HAS_YAML:
        # Fallback: try JSON format
        json_config = NEXUS_DIR / "config.json"
        if json_config.exists():
            with open(json_config) as f:
                return json.load(f)
        return {}

    try:
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


def save_config(config: Dict[str, Any]) -> None:
    """Save config to ~/.nexus/config.yaml"""
    NEXUS_DIR.mkdir(parents=True, exist_ok=True)

    if HAS_YAML:
        with open(CONFIG_FILE, "w") as f:
            yaml.dump(config, f, default_flow_style=False)
    else:
        # Fallback to JSON
        with open(NEXUS_DIR / "config.json", "w") as f:
            json.dump(config, f, indent=2)


def get_default(key: str, fallback: Any = None) -> Any:
    """Get a default value from config."""
    config = load_config()
    return config.get("defaults", {}).get(key, fallback)


def output_json(data: Dict[str, Any], pretty: bool = False) -> None:
    """Output data as JSON to stdout."""
    if pretty:
        click.echo(json.dumps(data, indent=2, default=str))
    else:
        click.echo(json.dumps(data, default=str))


def output_ndjson(data: Dict[str, Any]) -> None:
    """Output data as newline-delimited JSON (for streaming)."""
    click.echo(json.dumps(data, default=str), nl=True)
    sys.stdout.flush()


def has_stdin_data() -> bool:
    """Check if there's data available on stdin (for piping)."""
    if sys.stdin.isatty():
        return False
    # Check if there's data to read
    if hasattr(select, 'select'):
        return select.select([sys.stdin], [], [], 0.0)[0] != []
    return True  # Assume there's data on non-tty


def get_api_key(provider: str) -> Optional[str]:
    """Get API key from environment or config for a provider."""
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "ollama": "OLLAMA_API_KEY",  # Usually not needed
    }
    env_var = env_map.get(provider.lower(), f"{provider.upper()}_API_KEY")

    # Check environment first
    key = os.getenv(env_var)
    if key:
        return key

    # Fall back to config
    config = load_config()
    return config.get("api_keys", {}).get(provider.lower())


def get_default_provider() -> str:
    """Get default provider from config or fallback to openai."""
    return get_default("provider", "openai")


def get_default_model(provider: str) -> Optional[str]:
    """Get default model for a provider from config."""
    config = load_config()
    models = config.get("defaults", {}).get("models", {})
    return models.get(provider.lower())


def create_connector(provider: str, model: Optional[str] = None, json_output: bool = False, **kwargs) -> UnifiedAIWrapper:
    """Create a connector with the specified provider."""
    api_key = get_api_key(provider)
    if not api_key and provider.lower() != "ollama":
        if json_output:
            output_json({"error": f"No API key found for {provider}", "hint": f"Set {provider.upper()}_API_KEY"})
        else:
            console.print(f"[red]Error:[/red] No API key found for {provider}")
            console.print(f"Set the {provider.upper()}_API_KEY environment variable or run: nexus config set api_keys.{provider} YOUR_KEY")
        sys.exit(1)

    # Use default model from config if not specified
    if not model:
        model = get_default_model(provider)

    # Extract hooks before passing to wrapper
    on_tool_call = kwargs.pop("on_tool_call", None)
    on_tool_result = kwargs.pop("on_tool_result", None)
    on_step = kwargs.pop("on_step", None)
    on_error = kwargs.pop("on_error", None)

    wrapper = UnifiedAIWrapper(
        provider=provider,
        api_key=api_key or "",
        model=model,
        **kwargs
    )

    # Set hooks if provided
    if on_tool_call:
        wrapper._on_tool_call = on_tool_call
    if on_tool_result:
        wrapper._on_tool_result = on_tool_result
    if on_step:
        wrapper._on_step = on_step
    if on_error:
        wrapper._on_error = on_error

    return wrapper


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.option("--format", "-f", "output_format", type=click.Choice(["text", "json", "ndjson"]),
              default="text", help="Output format (text, json, ndjson)")
@click.pass_context
def cli(ctx, version, output_format):
    """
    Nexus - Universal AI CLI

    The Nexus Connector provides a unified interface for all major AI providers.
    Use 'nexus chat' for interactive mode or 'nexus run' for one-shot tasks.

    \b
    For machine-readable output, use --format json:
        nexus --format json run "Create hello.py"

    \b
    For streaming JSON (real-time updates for UIs):
        nexus --format ndjson run "Build a Flask app"
    """
    # Store format in context for subcommands
    ctx.ensure_object(dict)
    ctx.obj["format"] = output_format
    ctx.obj["json"] = output_format in ("json", "ndjson")

    if version:
        from ._version import __version__
        if output_format == "json":
            output_json({"version": __version__})
        else:
            console.print(f"Nexus Connector v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option("--provider", "-p", default="openai", help="AI provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--system", "-s", default=None, help="System prompt")
@click.option("--no-stream", is_flag=True, help="Disable streaming output")
@click.option("--load", "-l", default=None, help="Load conversation from file")
def chat(provider: str, model: Optional[str], system: Optional[str], no_stream: bool, load: Optional[str]):
    """
    Start an interactive chat session.

    Commands:
        /clear    - Clear conversation history
        /history  - Show conversation history
        /save     - Save conversation to file
        /switch   - Switch provider (e.g., /switch anthropic)
        /system   - Set system prompt
        /tokens   - Show token count
        exit      - Exit the chat

    Example:
        nexus chat --provider anthropic --model claude-3-opus-20240229
    """
    from .core.base_connector import Message

    connector = create_connector(provider, model, verbose=False)

    console.print(Panel(
        f"[bold green]Nexus Chat[/bold green]\n"
        f"Provider: {provider} | Model: {connector.connector.model}\n"
        f"Type '/help' for commands, 'exit' to quit",
        title="Connected",
        border_style="green"
    ))

    # Add system prompt if provided
    if system:
        connector.conversation_history.append(
            Message(role="system", content=system)
        )
        console.print(f"[dim]System prompt set[/dim]")

    # Load conversation if file provided
    if load:
        try:
            load_path = Path(load)
            if not load_path.exists():
                load_path = HISTORY_DIR / load
            with open(load_path) as f:
                history = json.load(f)
            for msg in history:
                connector.conversation_history.append(
                    Message(role=msg["role"], content=msg["content"])
                )
            console.print(f"[dim]Loaded {len(history)} messages from {load_path}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not load history: {e}[/yellow]")

    while True:
        try:
            # Get user input
            user_input = console.input("\n[bold cyan]You:[/bold cyan] ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() in ("exit", "quit", "/exit", "/quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.lower() in ("/help", "/?"):
                console.print(Panel(
                    "[bold]Chat Commands:[/bold]\n"
                    "  /clear    - Clear conversation history\n"
                    "  /history  - Show conversation history\n"
                    "  /save [file] - Save conversation to file\n"
                    "  /switch <provider> [model] - Switch provider\n"
                    "  /system <prompt> - Set system prompt\n"
                    "  /tokens   - Show token usage estimate\n"
                    "  /model    - Show current model info\n"
                    "  exit, quit - Exit the chat",
                    title="Help",
                    border_style="dim"
                ))
                continue

            if user_input.lower() == "/clear":
                connector.clear_history()
                console.print("[dim]History cleared[/dim]")
                continue

            if user_input.lower() == "/history":
                history = connector.get_history()
                if not history:
                    console.print("[dim]No history yet[/dim]")
                else:
                    for msg in history:
                        role = msg["role"]
                        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                        console.print(f"[dim]{role}:[/dim] {content}")
                continue

            if user_input.lower() == "/model":
                info = connector.model_info
                console.print(f"[dim]Provider: {info['provider_name']}[/dim]")
                console.print(f"[dim]Model: {info['model']}[/dim]")
                console.print(f"[dim]Session: {info['session_id']}[/dim]")
                console.print(f"[dim]Tools: {'Yes' if info['supports_tools'] else 'No'}[/dim]")
                continue

            if user_input.lower() == "/tokens":
                history = connector.get_history()
                total_chars = sum(len(msg["content"]) for msg in history)
                est_tokens = total_chars // 4
                console.print(f"[dim]Messages: {len(history)} | Est. tokens: ~{est_tokens}[/dim]")
                continue

            if user_input.startswith("/system"):
                parts = user_input.split(maxsplit=1)
                if len(parts) < 2:
                    console.print("[yellow]Usage: /system <prompt>[/yellow]")
                    continue
                from .core.base_connector import Message
                # Remove existing system message and add new one
                connector.conversation_history = [
                    m for m in connector.conversation_history if m.role != "system"
                ]
                connector.conversation_history.insert(0, Message(role="system", content=parts[1]))
                console.print("[dim]System prompt updated[/dim]")
                continue

            if user_input.startswith("/save"):
                parts = user_input.split(maxsplit=1)
                filename = parts[1] if len(parts) > 1 else f"chat_{connector.session_id}.json"
                HISTORY_DIR.mkdir(parents=True, exist_ok=True)
                filepath = HISTORY_DIR / filename
                with open(filepath, "w") as f:
                    json.dump(connector.get_history(), f, indent=2)
                console.print(f"[dim]Saved to {filepath}[/dim]")
                continue

            if user_input.startswith("/switch"):
                parts = user_input.split()
                if len(parts) < 2:
                    console.print("[yellow]Usage: /switch <provider> [model][/yellow]")
                    continue
                new_provider = parts[1]
                new_model = parts[2] if len(parts) > 2 else None
                try:
                    old_history = connector.get_history()
                    connector = create_connector(new_provider, new_model, verbose=False)
                    # Optionally restore history (without system message)
                    from .core.base_connector import Message
                    for msg in old_history:
                        if msg["role"] != "system":
                            connector.conversation_history.append(
                                Message(role=msg["role"], content=msg["content"])
                            )
                    console.print(f"[green]Switched to {new_provider} ({connector.connector.model})[/green]")
                except Exception as e:
                    console.print(f"[red]Failed to switch: {e}[/red]")
                continue

            # Send message and display response
            console.print("\n[bold green]Assistant:[/bold green] ", end="")

            try:
                if no_stream:
                    # Non-streaming mode
                    response = asyncio.run(connector.send_message(user_input))
                    content = response.get("content", "")
                    if content:
                        console.print(Markdown(content))
                    usage = response.get("usage", {})
                else:
                    # Streaming mode (default) - show tokens as they arrive
                    from .core.base_connector import Message

                    # Add to history first
                    connector.conversation_history.append(
                        Message(role="user", content=user_input)
                    )

                    full_response = ""
                    async def do_stream():
                        nonlocal full_response
                        async for chunk in connector.connector.stream_message(
                            connector.conversation_history
                        ):
                            console.print(chunk, end="")
                            full_response += chunk

                    asyncio.run(do_stream())
                    console.print()  # Newline after streaming

                    # Add assistant response to history
                    if full_response:
                        connector.conversation_history.append(
                            Message(role="assistant", content=full_response)
                        )

                    # Estimate tokens for streaming (no usage data available)
                    usage = {
                        "total_tokens": len(user_input.split()) + len(full_response.split()) * 2
                    }

                # Show token usage
                if usage:
                    total = usage.get("total_tokens", 0)
                    if total:
                        # Estimate cost (rough)
                        cost = total * 0.00001  # ~$0.01 per 1K tokens average
                        console.print(f"\n[dim]Tokens: ~{total} | Cost: ~${cost:.4f}[/dim]")

            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'exit' to quit.[/dim]")
        except EOFError:
            console.print("\n[dim]Goodbye![/dim]")
            break


@cli.command()
@click.argument("task")
@click.option("--provider", "-p", default=None, help="AI provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--output", "-o", default=None, help="Output directory for created files")
@click.option("--max-iterations", default=10, help="Maximum iterations")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
@click.pass_context
def run(ctx, task: str, provider: Optional[str], model: Optional[str], output: Optional[str],
        max_iterations: int, verbose: bool, quiet: bool):
    """
    Execute a one-shot task.

    \b
    Examples:
        nexus run "Create a Python script that sorts a list"
        nexus run "Build a Flask API" --provider anthropic
        nexus --format json run "Create hello.py"
        nexus --format ndjson run "Build a todo app"  # Real-time JSON events
    """
    output_format = ctx.obj.get("format", "text") if ctx.obj else "text"
    json_output = output_format in ("json", "ndjson")
    ndjson = output_format == "ndjson"

    # Get provider from args or config
    if not provider:
        provider = get_default_provider()

    workspace = Path(output) if output else Path.cwd()

    # Track tool calls for live display
    current_step = [0]
    tool_count = [0]
    tool_log = []  # For JSON output

    def on_tool_call(tc):
        """Show tool calls as they happen."""
        tool_count[0] += 1
        name = tc.get("name", "unknown")
        args = tc.get("arguments", {})

        # Log for JSON output
        tool_entry = {
            "event": "tool_call",
            "step": current_step[0],
            "tool": name,
            "arguments": args,
            "timestamp": datetime.now().isoformat(),
        }
        tool_log.append(tool_entry)

        if ndjson:
            output_ndjson(tool_entry)
            return

        if json_output or quiet:
            return

        # Get relevant arg to display
        if "path" in args:
            detail = args["path"]
        elif "command" in args:
            detail = args["command"][:40] + "..." if len(args.get("command", "")) > 40 else args.get("command", "")
        elif "content" in args:
            detail = f"{len(args['content'])} chars"
        else:
            detail = ""

        icon = {
            "create_file": "📝",
            "write_file": "📝",
            "read_file": "📖",
            "execute_command": "⚡",
            "run_command": "⚡",
            "list_directory": "📁",
            "search_files": "🔍",
        }.get(name, "🔧")

        if detail:
            console.print(f"  {icon} [cyan]{name}[/cyan] → {detail}")
        else:
            console.print(f"  {icon} [cyan]{name}[/cyan]")

    def on_tool_result(tr):
        """Show tool results."""
        success = tr.get("success", True)

        result_entry = {
            "event": "tool_result",
            "step": current_step[0],
            "success": success,
            "timestamp": datetime.now().isoformat(),
        }
        if not success:
            result_entry["error"] = tr.get("error", "Unknown error")

        tool_log.append(result_entry)

        if ndjson:
            output_ndjson(result_entry)
            return

        if not success and not quiet and not json_output:
            error = tr.get("error", "Unknown error")
            console.print(f"    [red]✗ {error}[/red]")

    def on_step(step, status):
        """Show iteration progress."""
        current_step[0] = step

        step_entry = {
            "event": "step",
            "step": step,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }

        if ndjson:
            output_ndjson(step_entry)
            return

        if not quiet and not json_output and status == "starting":
            console.print(f"\n[dim]Step {step}[/dim]")

    connector = create_connector(
        provider,
        model,
        json_output=json_output,
        workspace=workspace,
        max_iterations=max_iterations,
        verbose=verbose,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_step=on_step,
    )

    if not quiet and not json_output:
        console.print(Panel(
            f"[bold]Task:[/bold] {task}\n"
            f"[dim]Provider: {provider} | Model: {connector.connector.model}[/dim]",
            title="🚀 Executing Task",
            border_style="blue"
        ))

    try:
        import time
        start_time = time.time()
        result = asyncio.run(connector.execute_task(task, show_progress=False))
        total_duration = time.time() - start_time
    except Exception as e:
        if json_output:
            output_json({"success": False, "error": str(e)})
        else:
            console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)

    # Calculate cost
    cost = result.tokens_used * 0.00001  # ~$0.01 per 1K tokens average

    # JSON output
    if json_output:
        final_result = {
            "event": "complete" if not ndjson else None,
            "success": result.success,
            "task": task,
            "provider": provider,
            "model": connector.connector.model,
            "content": result.content,
            "files_created": result.files_created,
            "files_modified": result.files_modified,
            "metrics": {
                "steps": result.iterations,
                "tool_calls": tool_count[0],
                "tokens": result.tokens_used,
                "cost_estimate": round(cost, 4),
                "duration": round(result.duration, 2),
            },
        }
        if result.error:
            final_result["error"] = result.error
        if not ndjson:
            # Regular JSON: include tool log
            final_result["tool_log"] = tool_log
        else:
            # NDJSON: output final event
            final_result["event"] = "complete"

        output_json(final_result, pretty=not ndjson)
        sys.exit(0 if result.success else 1)

    # Text output
    if result.success:
        console.print("\n[bold green]✓ Task completed successfully[/bold green]")
    else:
        console.print(f"\n[bold red]✗ Task incomplete[/bold red]")
        if result.error:
            console.print(f"[red]Error: {result.error}[/red]")

    # Show created files
    if result.files_created and not quiet:
        console.print("\n[bold]Files created:[/bold]")
        for f in result.files_created:
            console.print(f"  📄 {f}")

    if result.files_modified and not quiet:
        console.print("\n[bold]Files modified:[/bold]")
        for f in result.files_modified:
            console.print(f"  ✏️  {f}")

    # Show metrics with cost estimate
    console.print(f"\n[dim]Steps: {result.iterations} | "
                  f"Tools: {tool_count[0]} | "
                  f"Tokens: {result.tokens_used} | "
                  f"Cost: ~${cost:.4f} | "
                  f"Time: {result.duration:.1f}s[/dim]")

    # Show final content
    if result.content and verbose:
        console.print("\n[bold]Output:[/bold]")
        console.print(Markdown(result.content))

    sys.exit(0 if result.success else 1)


@cli.command()
@click.argument("prompt")
@click.option("--provider", "-p", default="openai", help="AI provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
def stream(prompt: str, provider: str, model: Optional[str]):
    """
    Stream a response to stdout.

    Example:
        nexus stream "Explain quantum computing" --provider google
    """
    connector = create_connector(provider, model, verbose=False)

    async def do_stream():
        from .core.base_connector import Message
        messages = [Message(role="user", content=prompt)]
        async for chunk in connector.connector.stream_message(messages):
            console.print(chunk, end="")

    asyncio.run(do_stream())
    console.print()  # Final newline


@cli.command()
@click.argument("prompt")
@click.option("--providers", "-p", default="openai,anthropic",
              help="Comma-separated list of providers to compare")
@click.option("--model", "-m", default=None, help="Model to use (same for all)")
def compare(prompt: str, providers: str, model: Optional[str]):
    """
    Compare responses across multiple providers.

    Example:
        nexus compare "Explain REST APIs" --providers openai,anthropic,google
    """
    provider_list = [p.strip() for p in providers.split(",")]

    console.print(Panel(
        f"[bold]Prompt:[/bold] {prompt}\n"
        f"[dim]Comparing: {', '.join(provider_list)}[/dim]",
        title="Provider Comparison",
        border_style="blue"
    ))

    results = []

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        for provider in provider_list:
            task = progress.add_task(f"Querying {provider}...", total=None)

            try:
                connector = create_connector(provider, model, verbose=False)
                import time
                start = time.time()
                response = asyncio.run(connector.send_message(prompt))
                duration = time.time() - start

                results.append({
                    "provider": provider,
                    "model": connector.connector.model,
                    "content": response.get("content", ""),
                    "tokens": response.get("usage", {}).get("total_tokens", 0),
                    "duration": duration,
                    "error": None
                })
                progress.update(task, description=f"[green]✓ {provider}[/green]")

            except Exception as e:
                results.append({
                    "provider": provider,
                    "model": model,
                    "content": "",
                    "tokens": 0,
                    "duration": 0,
                    "error": str(e)
                })
                progress.update(task, description=f"[red]✗ {provider}: {e}[/red]")

    # Display comparison table
    console.print("\n")
    table = Table(title="Comparison Results", show_lines=True)
    table.add_column("Provider", style="cyan")
    table.add_column("Model", style="dim")
    table.add_column("Tokens", justify="right")
    table.add_column("Time", justify="right")

    for r in results:
        if r["error"]:
            table.add_row(r["provider"], "-", "-", f"[red]{r['error'][:30]}...[/red]")
        else:
            table.add_row(
                r["provider"],
                r["model"],
                str(r["tokens"]),
                f"{r['duration']:.2f}s"
            )

    console.print(table)

    # Display responses
    for r in results:
        if r["content"]:
            console.print(Panel(
                Markdown(r["content"]),
                title=f"{r['provider']} ({r['model']})",
                border_style="blue"
            ))


@cli.command()
@click.option("--port", "-p", default=8000, help="Port to run on")
@click.option("--host", "-h", default="0.0.0.0", help="Host to bind to")
@click.option("--provider", default="openai", help="Default AI provider")
@click.option("--model", "-m", default=None, help="Default model")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def serve(port: int, host: str, provider: str, model: Optional[str], reload: bool):
    """
    Start the Nexus web server.

    Example:
        nexus serve --port 8080 --provider anthropic
    """
    api_key = get_api_key(provider)
    if not api_key:
        console.print(f"[red]Error:[/red] No API key found for {provider}")
        sys.exit(1)

    console.print(Panel(
        f"[bold green]Starting Nexus Web Server[/bold green]\n"
        f"Provider: {provider} | Port: {port}\n"
        f"URL: http://{host}:{port}",
        title="Server",
        border_style="green"
    ))

    try:
        from .web import WebConnector

        connector = WebConnector(
            provider=AIProvider(provider.lower()),
            api_key=api_key,
            model=model,
            port=port,
            host=host
        )
        connector.run(reload=reload)

    except ImportError:
        console.print("[red]Error:[/red] Web components not installed")
        console.print("Install with: pip install nexus-connector[web]")
        sys.exit(1)


@cli.command("providers")
def list_providers():
    """List available AI providers."""
    table = Table(title="Available Providers")
    table.add_column("Provider", style="cyan")
    table.add_column("Display Name")
    table.add_column("API Key Env Var")
    table.add_column("Status")

    for provider in AIProvider:
        env_var = f"{provider.value.upper()}_API_KEY"
        has_key = bool(os.getenv(env_var))
        status = "[green]✓ Configured[/green]" if has_key else "[dim]Not configured[/dim]"

        # Ollama doesn't need an API key
        if provider == AIProvider.OLLAMA:
            status = "[green]✓ Local[/green]"

        table.add_row(
            provider.value,
            provider.display_name,
            env_var,
            status
        )

    console.print(table)


@cli.command("tools")
def list_tools():
    """List available tools for task execution."""
    from .core.tool_executor import ToolExecutor

    executor = ToolExecutor()

    table = Table(title="Available Tools")
    table.add_column("Tool", style="cyan")
    table.add_column("Category", style="dim")
    table.add_column("Description")
    table.add_column("Destructive", justify="center")

    # Get tools from registry
    for metadata in executor.registry.get_all():
        destructive = "[red]Yes[/red]" if metadata.is_destructive else "[dim]No[/dim]"
        table.add_row(
            metadata.name,
            metadata.category,
            metadata.description,
            destructive
        )

    console.print(table)

    # Show category summary
    categories = executor.registry.get_categories()
    if categories:
        console.print(f"\n[dim]Categories: {', '.join(categories)}[/dim]")


@cli.command()
@click.argument("prompt", required=False)
@click.option("--provider", "-p", default=None, help="AI provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--system", "-s", default=None, help="System prompt")
@click.pass_context
def ask(ctx, prompt: Optional[str], provider: Optional[str], model: Optional[str], system: Optional[str]):
    """
    Quick one-shot question (no task execution, just chat).

    Supports piping from stdin for scripting.

    \b
    Examples:
        nexus ask "What is Python?"
        echo "Explain Docker" | nexus ask
        cat question.txt | nexus ask --provider anthropic
        nexus --format json ask "What is 2+2?"
    """
    json_output = ctx.obj.get("json", False) if ctx.obj else False

    # Get provider from args, config, or default
    if not provider:
        provider = get_default_provider()

    # Get prompt from argument or stdin
    if not prompt:
        if has_stdin_data():
            prompt = sys.stdin.read().strip()
        else:
            if json_output:
                output_json({"error": "No prompt provided"})
            else:
                console.print("[red]Error:[/red] No prompt provided. Use: nexus ask \"your question\"")
            sys.exit(1)

    if not prompt:
        if json_output:
            output_json({"error": "Empty prompt"})
        else:
            console.print("[red]Error:[/red] Empty prompt")
        sys.exit(1)

    connector = create_connector(provider, model, json_output=json_output, verbose=False)

    # Add system prompt if provided
    if system:
        from .core.base_connector import Message
        connector.conversation_history.append(Message(role="system", content=system))

    try:
        import time
        start = time.time()
        response = asyncio.run(connector.send_message(prompt))
        duration = time.time() - start

        content = response.get("content", "")
        usage = response.get("usage", {})

        if json_output:
            output_json({
                "content": content,
                "provider": provider,
                "model": connector.connector.model,
                "tokens": usage.get("total_tokens", 0),
                "duration": round(duration, 2),
            })
        else:
            # Plain text output for piping
            console.print(content)

    except Exception as e:
        if json_output:
            output_json({"error": str(e)})
        else:
            console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)


@cli.group()
def config():
    """
    Manage Nexus configuration.

    \b
    Store defaults in ~/.nexus/config.yaml:
        nexus config set defaults.provider anthropic
        nexus config set api_keys.openai sk-xxx
        nexus config get defaults.provider
        nexus config list
    """
    pass


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """
    Set a configuration value.

    \b
    Examples:
        nexus config set defaults.provider anthropic
        nexus config set defaults.models.openai gpt-4o
        nexus config set api_keys.openai sk-xxx
    """
    cfg = load_config()

    # Parse dotted key path
    keys = key.split(".")
    current = cfg

    # Navigate/create nested structure
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]

    # Set the value (try to parse as JSON for complex types)
    try:
        parsed = json.loads(value)
        current[keys[-1]] = parsed
    except (json.JSONDecodeError, TypeError):
        current[keys[-1]] = value

    save_config(cfg)
    console.print(f"[green]✓[/green] Set {key} = {value}")


@config.command("get")
@click.argument("key")
@click.pass_context
def config_get(ctx, key: str):
    """
    Get a configuration value.

    \b
    Examples:
        nexus config get defaults.provider
        nexus config get api_keys.openai
    """
    json_output = ctx.obj.get("json", False) if ctx.obj else False
    cfg = load_config()

    # Parse dotted key path
    keys = key.split(".")
    current = cfg

    try:
        for k in keys:
            current = current[k]

        if json_output:
            output_json({key: current})
        else:
            if isinstance(current, dict):
                console.print(json.dumps(current, indent=2))
            else:
                console.print(str(current))

    except (KeyError, TypeError):
        if json_output:
            output_json({"error": f"Key not found: {key}"})
        else:
            console.print(f"[dim]Not set: {key}[/dim]")
        sys.exit(1)


@config.command("list")
@click.pass_context
def config_list(ctx):
    """Show all configuration."""
    json_output = ctx.obj.get("json", False) if ctx.obj else False
    cfg = load_config()

    if json_output:
        # Mask API keys in JSON output
        safe_cfg = cfg.copy()
        if "api_keys" in safe_cfg:
            safe_cfg["api_keys"] = {k: "***" for k in safe_cfg["api_keys"]}
        output_json(safe_cfg, pretty=True)
    else:
        if not cfg:
            console.print("[dim]No configuration set. Use 'nexus config set' to configure.[/dim]")
            return

        console.print(Panel(
            f"[bold]Config file:[/bold] {CONFIG_FILE}",
            title="Nexus Configuration",
            border_style="blue"
        ))

        # Show defaults
        if "defaults" in cfg:
            console.print("\n[bold]Defaults:[/bold]")
            for k, v in cfg["defaults"].items():
                if isinstance(v, dict):
                    console.print(f"  {k}:")
                    for k2, v2 in v.items():
                        console.print(f"    {k2}: {v2}")
                else:
                    console.print(f"  {k}: {v}")

        # Show API keys (masked)
        if "api_keys" in cfg:
            console.print("\n[bold]API Keys:[/bold]")
            for k, v in cfg["api_keys"].items():
                masked = v[:8] + "..." if len(v) > 8 else "***"
                console.print(f"  {k}: {masked}")


@config.command("unset")
@click.argument("key")
def config_unset(key: str):
    """
    Remove a configuration value.

    \b
    Example:
        nexus config unset defaults.provider
    """
    cfg = load_config()

    # Parse dotted key path
    keys = key.split(".")
    current = cfg

    try:
        for k in keys[:-1]:
            current = current[k]
        del current[keys[-1]]
        save_config(cfg)
        console.print(f"[green]✓[/green] Removed {key}")
    except (KeyError, TypeError):
        console.print(f"[dim]Key not found: {key}[/dim]")


@cli.command()
@click.option("--provider", "-p", default="openai", help="Default provider")
@click.option("--force", "-f", is_flag=True, help="Overwrite existing config")
@click.pass_context
def init(ctx, provider: str, force: bool):
    """
    Initialize Nexus configuration.

    Creates ~/.nexus/config.yaml with sensible defaults.

    \b
    Example:
        nexus init --provider anthropic
    """
    json_output = ctx.obj.get("json", False) if ctx.obj else False

    if CONFIG_FILE.exists() and not force:
        if json_output:
            output_json({"error": "Config already exists", "path": str(CONFIG_FILE)})
        else:
            console.print(f"[yellow]Config already exists:[/yellow] {CONFIG_FILE}")
            console.print("Use --force to overwrite")
        sys.exit(1)

    # Create default config
    NEXUS_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)

    default_config = {
        "defaults": {
            "provider": provider,
            "models": {
                "openai": "gpt-4o",
                "anthropic": "claude-sonnet-4-20250514",
                "google": "gemini-2.0-flash",
                "deepseek": "deepseek-chat",
            }
        },
        "api_keys": {
            # Empty - user should set these
        }
    }

    save_config(default_config)

    if json_output:
        output_json({
            "success": True,
            "config_path": str(CONFIG_FILE),
            "default_provider": provider,
        })
    else:
        console.print(Panel(
            f"[bold green]Nexus initialized![/bold green]\n\n"
            f"Config: {CONFIG_FILE}\n"
            f"History: {HISTORY_DIR}\n\n"
            f"[bold]Next steps:[/bold]\n"
            f"1. Set your API key:\n"
            f"   [cyan]nexus config set api_keys.{provider} YOUR_KEY[/cyan]\n\n"
            f"2. Or use environment variables:\n"
            f"   [cyan]export {provider.upper()}_API_KEY=YOUR_KEY[/cyan]\n\n"
            f"3. Start chatting:\n"
            f"   [cyan]nexus chat[/cyan]",
            title="Welcome to Nexus",
            border_style="green"
        ))


@cli.command()
@click.pass_context
def status(ctx):
    """
    Show Nexus status and configuration summary.

    Quick overview of what's configured and ready to use.
    """
    json_output = ctx.obj.get("json", False) if ctx.obj else False
    cfg = load_config()

    # Check providers
    providers_status = {}
    for provider in AIProvider:
        has_key = bool(get_api_key(provider.value))
        if provider == AIProvider.OLLAMA:
            providers_status[provider.value] = "local"
        elif has_key:
            providers_status[provider.value] = "ready"
        else:
            providers_status[provider.value] = "not_configured"

    default_provider = get_default_provider()
    config_exists = CONFIG_FILE.exists()

    if json_output:
        output_json({
            "config_exists": config_exists,
            "config_path": str(CONFIG_FILE),
            "default_provider": default_provider,
            "providers": providers_status,
            "ready_count": sum(1 for v in providers_status.values() if v in ("ready", "local")),
        })
    else:
        from ._version import __version__

        console.print(Panel(
            f"[bold]Nexus Connector[/bold] v{__version__}",
            border_style="blue"
        ))

        # Config status
        if config_exists:
            console.print(f"[green]✓[/green] Config: {CONFIG_FILE}")
        else:
            console.print(f"[dim]○[/dim] Config: Not initialized (run 'nexus init')")

        console.print(f"[green]✓[/green] Default provider: {default_provider}")

        # Provider status
        console.print("\n[bold]Providers:[/bold]")
        for provider, status in providers_status.items():
            if status == "ready":
                console.print(f"  [green]✓[/green] {provider}")
            elif status == "local":
                console.print(f"  [green]✓[/green] {provider} (local)")
            else:
                console.print(f"  [dim]○[/dim] {provider}")

        ready_count = sum(1 for v in providers_status.values() if v in ("ready", "local"))
        console.print(f"\n[dim]{ready_count} provider(s) ready[/dim]")


# =============================================================================
# DEVELOPER TOOLS
# =============================================================================
# These commands provide readable terminal UX for common dev tasks.


def read_file_content(filepath: str) -> tuple[str, str]:
    """Read file content and detect language from extension."""
    path = Path(filepath)
    if not path.exists():
        raise click.ClickException(f"File not found: {filepath}")

    content = path.read_text()

    # Detect language from extension
    ext_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript",
        ".jsx": "javascript",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".java": "java",
        ".cpp": "cpp",
        ".c": "c",
        ".h": "c",
        ".cs": "csharp",
        ".php": "php",
        ".swift": "swift",
        ".kt": "kotlin",
        ".scala": "scala",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "zsh",
        ".sql": "sql",
        ".html": "html",
        ".css": "css",
        ".json": "json",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".toml": "toml",
    }
    lang = ext_map.get(path.suffix.lower(), "text")

    return content, lang


def get_project_context() -> Dict[str, Any]:
    """Gather project context from current directory."""
    cwd = Path.cwd()
    context = {
        "directory": str(cwd),
        "project_type": None,
        "files": [],
    }

    # Detect project type
    if (cwd / "package.json").exists():
        context["project_type"] = "node"
    elif (cwd / "pyproject.toml").exists() or (cwd / "setup.py").exists():
        context["project_type"] = "python"
    elif (cwd / "Cargo.toml").exists():
        context["project_type"] = "rust"
    elif (cwd / "go.mod").exists():
        context["project_type"] = "go"
    elif (cwd / "Gemfile").exists():
        context["project_type"] = "ruby"

    return context


def stream_ai_response(connector, prompt: str, panel_title: str = "Response") -> str:
    """Stream AI response with nice terminal output."""
    from .core.base_connector import Message

    connector.conversation_history.append(Message(role="user", content=prompt))

    full_response = ""

    async def do_stream():
        nonlocal full_response
        async for chunk in connector.connector.stream_message(
            connector.conversation_history
        ):
            console.print(chunk, end="")
            full_response += chunk

    console.print(f"\n[bold cyan]{'─' * 60}[/bold cyan]")
    asyncio.run(do_stream())
    console.print(f"\n[bold cyan]{'─' * 60}[/bold cyan]\n")

    # Add to history
    if full_response:
        connector.conversation_history.append(
            Message(role="assistant", content=full_response)
        )

    return full_response


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default=None, help="AI provider")
@click.option("--focus", "-f", type=click.Choice(["security", "performance", "style", "bugs", "all"]),
              default="all", help="Review focus area")
@click.pass_context
def review(ctx, file: str, provider: Optional[str], focus: str):
    """
    AI-powered code review.

    Analyzes code for bugs, security issues, style, and improvements.

    \b
    Examples:
        nexus review src/api.py
        nexus review main.go --focus security
        nexus review app.ts --focus performance
    """
    if not provider:
        provider = get_default_provider()

    content, lang = read_file_content(file)
    filename = Path(file).name

    # Build focused prompt
    focus_instructions = {
        "security": "Focus specifically on security vulnerabilities, injection risks, authentication issues, and data exposure.",
        "performance": "Focus specifically on performance bottlenecks, memory leaks, inefficient algorithms, and optimization opportunities.",
        "style": "Focus specifically on code style, naming conventions, readability, and adherence to best practices.",
        "bugs": "Focus specifically on potential bugs, edge cases, error handling, and logical errors.",
        "all": "Review all aspects: bugs, security, performance, style, and general improvements."
    }

    console.print(Panel(
        f"[bold]File:[/bold] {file}\n"
        f"[bold]Language:[/bold] {lang}\n"
        f"[bold]Focus:[/bold] {focus}\n"
        f"[bold]Lines:[/bold] {len(content.splitlines())}",
        title="🔍 Code Review",
        border_style="blue"
    ))

    connector = create_connector(provider, verbose=False)

    prompt = f"""Review this {lang} code from `{filename}`.

{focus_instructions[focus]}

Structure your review as:

## Summary
Brief overall assessment (1-2 sentences)

## Issues Found
List each issue with:
- 🔴 **Critical**: [description] (line X)
- 🟡 **Warning**: [description] (line X)
- 🔵 **Suggestion**: [description] (line X)

## Recommendations
Top 3 actionable improvements

---

```{lang}
{content}
```"""

    stream_ai_response(connector, prompt, "Review Results")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default=None, help="AI provider")
@click.option("--framework", "-f", default=None, help="Test framework (pytest, jest, go test, etc.)")
@click.option("--output", "-o", default=None, help="Output file for generated tests")
@click.pass_context
def test(ctx, file: str, provider: Optional[str], framework: Optional[str], output: Optional[str]):
    """
    Generate tests for a file.

    Creates unit tests based on the code structure.

    \b
    Examples:
        nexus test src/utils.py
        nexus test api.ts --framework jest
        nexus test main.go -o main_test.go
    """
    if not provider:
        provider = get_default_provider()

    content, lang = read_file_content(file)
    filename = Path(file).name

    # Auto-detect test framework
    if not framework:
        framework_map = {
            "python": "pytest",
            "javascript": "jest",
            "typescript": "jest",
            "go": "go test",
            "rust": "cargo test",
            "ruby": "rspec",
            "java": "junit",
        }
        framework = framework_map.get(lang, "standard unit tests")

    console.print(Panel(
        f"[bold]File:[/bold] {file}\n"
        f"[bold]Language:[/bold] {lang}\n"
        f"[bold]Framework:[/bold] {framework}",
        title="🧪 Generate Tests",
        border_style="green"
    ))

    connector = create_connector(provider, verbose=False)

    prompt = f"""Generate comprehensive unit tests for this {lang} code using {framework}.

Requirements:
1. Test all public functions/methods
2. Include edge cases and error conditions
3. Use descriptive test names
4. Add brief comments explaining what each test verifies
5. Follow {framework} best practices

Structure:
- Setup/fixtures if needed
- Happy path tests
- Edge case tests
- Error handling tests

---

```{lang}
{content}
```

Generate the complete test file:"""

    response = stream_ai_response(connector, prompt, "Generated Tests")

    # Extract code block if present
    if "```" in response:
        import re
        code_match = re.search(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_match:
            test_code = code_match.group(1).strip()

            if output:
                Path(output).write_text(test_code)
                console.print(f"\n[green]✓[/green] Tests written to: {output}")
            else:
                # Suggest output file
                suggested = Path(file).stem + "_test" + Path(file).suffix
                console.print(f"\n[dim]Tip: Use -o {suggested} to save tests to a file[/dim]")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default=None, help="AI provider")
@click.option("--style", "-s", type=click.Choice(["docstring", "markdown", "readme", "api"]),
              default="docstring", help="Documentation style")
@click.option("--output", "-o", default=None, help="Output file")
@click.pass_context
def docs(ctx, file: str, provider: Optional[str], style: str, output: Optional[str]):
    """
    Generate documentation for a file.

    Creates docstrings, markdown docs, or API reference.

    \b
    Examples:
        nexus docs src/api.py
        nexus docs lib/utils.ts --style markdown
        nexus docs handlers.go --style api -o API.md
    """
    if not provider:
        provider = get_default_provider()

    content, lang = read_file_content(file)
    filename = Path(file).name

    style_instructions = {
        "docstring": f"Add comprehensive docstrings/comments to all functions, classes, and modules following {lang} conventions.",
        "markdown": "Create a markdown document explaining the code with sections for Overview, Functions/Classes, Usage Examples, and Notes.",
        "readme": "Create a README.md style document with installation, usage examples, and API overview.",
        "api": "Create API reference documentation with all public interfaces, parameters, return types, and examples.",
    }

    console.print(Panel(
        f"[bold]File:[/bold] {file}\n"
        f"[bold]Language:[/bold] {lang}\n"
        f"[bold]Style:[/bold] {style}",
        title="📚 Generate Documentation",
        border_style="yellow"
    ))

    connector = create_connector(provider, verbose=False)

    prompt = f"""Generate documentation for this {lang} code.

Task: {style_instructions[style]}

Requirements:
1. Be accurate - only document what the code actually does
2. Include parameter types and return types
3. Add usage examples where helpful
4. Note any important caveats or edge cases

---

```{lang}
{content}
```

Generate the documentation:"""

    response = stream_ai_response(connector, prompt, "Generated Documentation")

    if output:
        Path(output).write_text(response)
        console.print(f"\n[green]✓[/green] Documentation written to: {output}")


@cli.command()
@click.argument("target", required=False)
@click.option("--provider", "-p", default=None, help="AI provider")
@click.option("--error", "-e", default=None, help="Error message to explain")
@click.pass_context
def explain(ctx, target: Optional[str], provider: Optional[str], error: Optional[str]):
    """
    Explain code or errors.

    Can explain a file, code snippet, or error message.

    \b
    Examples:
        nexus explain src/complex.py
        nexus explain --error "TypeError: Cannot read property 'x' of undefined"
        cat error.log | nexus explain
    """
    if not provider:
        provider = get_default_provider()

    # Determine what to explain
    if error:
        # Explain an error message
        console.print(Panel(
            f"[bold]Error:[/bold]\n{error[:200]}{'...' if len(error) > 200 else ''}",
            title="❓ Explain Error",
            border_style="red"
        ))

        connector = create_connector(provider, verbose=False)
        prompt = f"""Explain this error message in plain terms:

```
{error}
```

Structure your explanation as:

## What This Error Means
Simple explanation of what went wrong

## Common Causes
- Cause 1
- Cause 2
- Cause 3

## How To Fix It
Step-by-step debugging approach

## Example Fix
Show a code example if applicable"""

    elif target and Path(target).exists():
        # Explain a file
        content, lang = read_file_content(target)

        console.print(Panel(
            f"[bold]File:[/bold] {target}\n"
            f"[bold]Language:[/bold] {lang}\n"
            f"[bold]Lines:[/bold] {len(content.splitlines())}",
            title="❓ Explain Code",
            border_style="magenta"
        ))

        connector = create_connector(provider, verbose=False)
        prompt = f"""Explain this {lang} code clearly.

Structure your explanation as:

## Overview
What this code does in 1-2 sentences

## How It Works
Step-by-step walkthrough of the logic

## Key Concepts
Important patterns, algorithms, or techniques used

## Dependencies
External libraries or systems it interacts with

---

```{lang}
{content}
```"""

    elif has_stdin_data():
        # Explain piped input (likely an error)
        piped_input = sys.stdin.read().strip()

        console.print(Panel(
            f"[bold]Input:[/bold]\n{piped_input[:300]}{'...' if len(piped_input) > 300 else ''}",
            title="❓ Explain",
            border_style="magenta"
        ))

        connector = create_connector(provider, verbose=False)
        prompt = f"""Explain this:

```
{piped_input}
```

If it's an error, explain what went wrong and how to fix it.
If it's code, explain what it does.
If it's output/logs, explain what happened."""

    else:
        raise click.ClickException("Provide a file path, --error message, or pipe input")

    stream_ai_response(connector, prompt, "Explanation")


@cli.command()
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option("--provider", "-p", default=None, help="AI provider")
@click.option("--error", "-e", default=None, help="Error message to fix")
@click.option("--apply", "-a", is_flag=True, help="Apply fix directly to file")
@click.pass_context
def fix(ctx, file: Optional[str], provider: Optional[str], error: Optional[str], apply: bool):
    """
    Fix code based on an error.

    Analyzes errors and suggests or applies fixes.

    \b
    Examples:
        nexus fix src/api.py --error "NameError: name 'foo' is not defined"
        python app.py 2>&1 | nexus fix src/app.py
        nexus fix main.go --error "undefined: fmt" --apply
    """
    if not provider:
        provider = get_default_provider()

    # Get error from flag or stdin
    error_msg = error
    if not error_msg and has_stdin_data():
        error_msg = sys.stdin.read().strip()

    if not error_msg:
        raise click.ClickException("Provide --error message or pipe error output")

    if not file:
        raise click.ClickException("Provide the file to fix")

    content, lang = read_file_content(file)
    filename = Path(file).name

    console.print(Panel(
        f"[bold]File:[/bold] {file}\n"
        f"[bold]Error:[/bold]\n{error_msg[:200]}{'...' if len(error_msg) > 200 else ''}",
        title="🔧 Fix Code",
        border_style="red"
    ))

    connector = create_connector(provider, verbose=False)

    prompt = f"""Fix this {lang} code based on the error.

## Error
```
{error_msg}
```

## Current Code ({filename})
```{lang}
{content}
```

## Instructions
1. Identify the root cause of the error
2. Provide the corrected code
3. Explain what you changed and why

Structure your response as:

## Problem
What caused the error (1-2 sentences)

## Solution
```{lang}
[THE COMPLETE FIXED CODE - not just the changed parts]
```

## Changes Made
- Change 1: description
- Change 2: description"""

    response = stream_ai_response(connector, prompt, "Fix")

    # Extract fixed code if --apply
    if apply:
        import re
        # Find the solution code block
        code_match = re.search(r'## Solution\s*```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_match:
            fixed_code = code_match.group(1).strip()

            # Backup original
            backup_path = Path(file).with_suffix(Path(file).suffix + ".bak")
            Path(file).rename(backup_path)

            # Write fixed code
            Path(file).write_text(fixed_code)
            console.print(f"\n[green]✓[/green] Fix applied to: {file}")
            console.print(f"[dim]  Backup saved to: {backup_path}[/dim]")
        else:
            console.print("\n[yellow]Could not extract fixed code. Apply manually.[/yellow]")


@cli.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default=None, help="AI provider")
@click.option("--goal", "-g", default=None, help="Refactoring goal")
@click.option("--output", "-o", default=None, help="Output file (default: overwrite)")
@click.pass_context
def refactor(ctx, file: str, provider: Optional[str], goal: Optional[str], output: Optional[str]):
    """
    Refactor code with AI suggestions.

    Improves code structure, readability, and maintainability.

    \b
    Examples:
        nexus refactor src/legacy.py
        nexus refactor utils.ts --goal "split into smaller functions"
        nexus refactor api.go --goal "add error handling" -o api_v2.go
    """
    if not provider:
        provider = get_default_provider()

    content, lang = read_file_content(file)
    filename = Path(file).name

    goal_text = goal if goal else "Improve code quality, readability, and maintainability"

    console.print(Panel(
        f"[bold]File:[/bold] {file}\n"
        f"[bold]Language:[/bold] {lang}\n"
        f"[bold]Goal:[/bold] {goal_text}",
        title="♻️  Refactor",
        border_style="cyan"
    ))

    connector = create_connector(provider, verbose=False)

    prompt = f"""Refactor this {lang} code.

## Goal
{goal_text}

## Current Code ({filename})
```{lang}
{content}
```

## Instructions
1. Apply the refactoring while preserving functionality
2. Follow {lang} best practices and conventions
3. Explain your changes

Structure your response as:

## Summary
What refactoring was applied (1-2 sentences)

## Refactored Code
```{lang}
[THE COMPLETE REFACTORED CODE]
```

## Changes Made
- **Change 1**: description
- **Change 2**: description
- **Change 3**: description

## Benefits
- Benefit 1
- Benefit 2"""

    response = stream_ai_response(connector, prompt, "Refactored Code")

    # Extract code if output specified
    if output:
        import re
        code_match = re.search(r'## Refactored Code\s*```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_match:
            refactored_code = code_match.group(1).strip()
            Path(output).write_text(refactored_code)
            console.print(f"\n[green]✓[/green] Refactored code written to: {output}")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
