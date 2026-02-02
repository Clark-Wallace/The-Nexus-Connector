"""
Nexus CLI - Command-line interface for The Nexus Connector.

Provides interactive chat, task execution, streaming, and provider comparison.
"""

import asyncio
import json
import os
import sys

# Load .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
from pathlib import Path
from typing import Optional, List

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.live import Live
from rich.text import Text

from .core.unified_wrapper import UnifiedAIWrapper
from .core.base_connector import AIProvider


console = Console()

# Default config directory
NEXUS_DIR = Path.home() / ".nexus"
HISTORY_DIR = NEXUS_DIR / "history"


def get_api_key(provider: str) -> Optional[str]:
    """Get API key from environment for a provider."""
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "ollama": "OLLAMA_API_KEY",  # Usually not needed
    }
    env_var = env_map.get(provider.lower(), f"{provider.upper()}_API_KEY")
    return os.getenv(env_var)


def create_connector(provider: str, model: Optional[str] = None, **kwargs) -> UnifiedAIWrapper:
    """Create a connector with the specified provider."""
    api_key = get_api_key(provider)
    if not api_key and provider.lower() != "ollama":
        console.print(f"[red]Error:[/red] No API key found for {provider}")
        console.print(f"Set the {provider.upper()}_API_KEY environment variable")
        sys.exit(1)

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
@click.pass_context
def cli(ctx, version):
    """
    Nexus - Universal AI CLI

    The Nexus Connector provides a unified interface for all major AI providers.
    Use 'nexus chat' for interactive mode or 'nexus run' for one-shot tasks.
    """
    if version:
        from ._version import __version__
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
@click.option("--provider", "-p", default="openai", help="AI provider to use")
@click.option("--model", "-m", default=None, help="Model to use")
@click.option("--output", "-o", default=None, help="Output directory for created files")
@click.option("--max-iterations", default=10, help="Maximum iterations")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed progress")
@click.option("--quiet", "-q", is_flag=True, help="Minimal output")
def run(task: str, provider: str, model: Optional[str], output: Optional[str],
        max_iterations: int, verbose: bool, quiet: bool):
    """
    Execute a one-shot task.

    Example:
        nexus run "Create a Python script that sorts a list" --provider anthropic
    """
    workspace = Path(output) if output else Path.cwd()

    # Track tool calls for live display
    current_step = [0]
    tool_count = [0]

    def on_tool_call(tc):
        """Show tool calls as they happen."""
        tool_count[0] += 1
        name = tc.get("name", "unknown")
        args = tc.get("arguments", {})

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

        if not quiet:
            if detail:
                console.print(f"  {icon} [cyan]{name}[/cyan] → {detail}")
            else:
                console.print(f"  {icon} [cyan]{name}[/cyan]")

    def on_tool_result(tr):
        """Show tool results."""
        success = tr.get("success", True)
        if not success and not quiet:
            error = tr.get("error", "Unknown error")
            console.print(f"    [red]✗ {error}[/red]")

    def on_step(step, status):
        """Show iteration progress."""
        current_step[0] = step
        if not quiet and status == "starting":
            console.print(f"\n[dim]Step {step}[/dim]")

    connector = create_connector(
        provider,
        model,
        workspace=workspace,
        max_iterations=max_iterations,
        verbose=verbose,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_step=on_step,
    )

    if not quiet:
        console.print(Panel(
            f"[bold]Task:[/bold] {task}\n"
            f"[dim]Provider: {provider} | Model: {connector.connector.model}[/dim]",
            title="🚀 Executing Task",
            border_style="blue"
        ))

    try:
        result = asyncio.run(connector.execute_task(task, show_progress=False))
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)

    # Display results
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
    cost = result.tokens_used * 0.00001  # ~$0.01 per 1K tokens average
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


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
