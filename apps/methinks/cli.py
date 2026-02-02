"""
MeThinks CLI - Command-line interface for project idea generation.

Usage:
    methinks new              Start a new MeThinks session
    methinks resume [ID]      Resume a previous session
    methinks list             List saved sessions
    methinks show <ID>        Show a session's spec
    methinks export <ID>      Export spec to file
    methinks quick "<idea>"   Quick mode - generate spec from one-liner
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt, Confirm

from .models import ConversationPhase, SkillLevel
from .session import Session, SessionManager, MeThinksConfig
from .conversation import ConversationEngine
from .generator import SpecGenerator


console = Console()


def get_connector(provider: str = "openai"):
    """Get a Nexus connector for AI communication."""
    try:
        from nexus import NexusConnector
        import os

        # Get API key from environment
        api_key = os.getenv(f"{provider.upper()}_API_KEY")
        if not api_key:
            return None

        return NexusConnector(
            provider=provider,
            api_key=api_key,
            verbose=False,
        )
    except ImportError:
        return None
    except Exception:
        return None


@click.group(invoke_without_command=True)
@click.option("--version", "-v", is_flag=True, help="Show version")
@click.pass_context
def cli(ctx, version):
    """
    MeThinks - AI-powered project idea generator.

    Generate project ideas AND AI-ready specifications for tools like Claude Code.

    Start with: methinks new
    """
    if version:
        from . import __version__
        console.print(f"MeThinks v{__version__}")
        return

    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())


@cli.command()
@click.option("--provider", "-p", default="openai", help="AI provider to use")
@click.option("--quick", "-q", is_flag=True, help="Quick mode - fewer questions")
def new(provider: str, quick: bool):
    """Start a new MeThinks session."""
    config = MeThinksConfig()
    manager = SessionManager()

    # Check for API key
    connector = get_connector(provider)
    if not connector:
        console.print(Panel(
            f"[yellow]No API key found for {provider}.[/yellow]\n\n"
            f"Set {provider.upper()}_API_KEY environment variable to enable AI responses.\n\n"
            "[dim]Running in demo mode - responses will be simulated.[/dim]",
            title="API Key Missing",
            border_style="yellow"
        ))

    # Create new session
    session = manager.create_session(provider=provider)

    console.print(Panel(
        "[bold green]Welcome to MeThinks![/bold green]\n\n"
        "I'll help you discover and define your project idea.\n"
        "When we're done, you'll have a spec ready for Claude Code.\n\n"
        "[dim]Type 'quit' to exit, 'save' to save progress.[/dim]",
        title="🤔 MeThinks",
        border_style="green"
    ))

    # Run conversation loop
    asyncio.run(conversation_loop(session, connector, manager, quick))


async def conversation_loop(
    session: Session,
    connector,
    manager: SessionManager,
    quick: bool = False
):
    """Main conversation loop."""
    engine = ConversationEngine(session, connector)
    generator = SpecGenerator()

    # Get initial message
    initial_msg = await engine.get_initial_message()
    console.print(f"\n[bold cyan]🤔 MeThinks:[/bold cyan] {initial_msg}\n")

    while session.phase != ConversationPhase.COMPLETE:
        try:
            # Get user input
            user_input = Prompt.ask("[bold green]You[/bold green]")

            # Handle special commands
            if user_input.lower() in ("quit", "exit", "q"):
                if Confirm.ask("Save session before quitting?", default=True):
                    manager.save_session(session)
                    console.print(f"[dim]Session saved: {session.session_id}[/dim]")
                break

            if user_input.lower() == "save":
                manager.save_session(session)
                console.print(f"[dim]Session saved: {session.session_id}[/dim]")
                continue

            if user_input.lower() == "status":
                show_session_status(session)
                continue

            if user_input.lower() == "skip":
                # Skip current phase (for testing)
                session.advance_phase()
                console.print(f"[dim]Skipped to: {session.phase.value}[/dim]")
                initial_msg = await engine.get_initial_message()
                console.print(f"\n[bold cyan]🤔 MeThinks:[/bold cyan] {initial_msg}\n")
                continue

            if not user_input.strip():
                continue

            # Process input
            result = await engine.process_input(user_input)

            # Show response
            console.print(f"\n[bold cyan]🤔 MeThinks:[/bold cyan] {result.response}\n")

            # Show phase transition
            if result.should_advance:
                console.print(f"[dim]Moving to: {session.phase.value}[/dim]\n")

            # Auto-save periodically
            manager.save_session(session)

        except KeyboardInterrupt:
            console.print("\n[dim]Interrupted. Type 'quit' to exit.[/dim]")
        except EOFError:
            break

    # Session complete - generate spec
    if session.phase == ConversationPhase.COMPLETE:
        console.print(Panel(
            "[bold green]Session complete![/bold green]\n\n"
            "Generating your project specification...",
            border_style="green"
        ))

        # Build and save spec
        spec = engine.build_spec()
        session.spec = spec
        session.finalize_spec()
        manager.save_session(session)

        # Show spec preview
        spec_md = generator.generate_markdown(spec)
        console.print("\n")
        console.print(Panel(
            Markdown(spec_md),
            title=f"📋 {spec.name} - Project Specification",
            border_style="blue"
        ))

        # Offer export options
        console.print("\n[bold]Export options:[/bold]")
        console.print(f"  methinks export {session.session_id} --format claude -o CLAUDE.md")
        console.print(f"  methinks export {session.session_id} --format md -o PROJECT_SPEC.md")


def show_session_status(session: Session):
    """Show current session status."""
    console.print(Panel(
        f"[bold]Session:[/bold] {session.session_id}\n"
        f"[bold]Phase:[/bold] {session.phase.value}\n"
        f"[bold]Messages:[/bold] {len(session.messages)}\n"
        f"[bold]Project:[/bold] {session.spec.name}\n\n"
        f"[bold]Extracted data:[/bold]\n"
        + "\n".join(f"  • {k}: {v}" for k, v in list(session.extracted.items())[:10]),
        title="Session Status",
        border_style="blue"
    ))


@cli.command()
@click.argument("session_id", required=False)
def resume(session_id: Optional[str]):
    """Resume a previous session."""
    manager = SessionManager()

    if not session_id:
        # Show recent sessions
        sessions = manager.get_recent_sessions(5)
        if not sessions:
            console.print("[yellow]No sessions found.[/yellow]")
            return

        console.print("[bold]Recent sessions:[/bold]\n")
        for i, s in enumerate(sessions, 1):
            status = "✓" if s["is_complete"] else f"({s['phase']})"
            console.print(f"  {i}. {s['session_id']} - {s['name']} {status}")

        console.print("\n[dim]Use: methinks resume <session_id>[/dim]")
        return

    # Load session
    session = manager.load_session(session_id)
    if not session:
        # Try partial match
        session = manager.find_session_by_name(session_id)

    if not session:
        console.print(f"[red]Session not found: {session_id}[/red]")
        return

    console.print(Panel(
        f"[bold]Resuming:[/bold] {session.spec.name}\n"
        f"[bold]Phase:[/bold] {session.phase.value}\n"
        f"[bold]Messages:[/bold] {len(session.messages)}",
        title="Session Resumed",
        border_style="green"
    ))

    connector = get_connector(session.provider)
    asyncio.run(conversation_loop(session, connector, manager))


@cli.command("list")
def list_sessions():
    """List all saved sessions."""
    manager = SessionManager()
    sessions = manager.list_sessions()

    if not sessions:
        console.print("[dim]No sessions found.[/dim]")
        return

    table = Table(title="MeThinks Sessions")
    table.add_column("ID", style="cyan")
    table.add_column("Project")
    table.add_column("Phase")
    table.add_column("Messages", justify="right")
    table.add_column("Updated")

    for s in sessions:
        status = "✓" if s["is_complete"] else s["phase"]
        updated = s["updated_at"].strftime("%Y-%m-%d %H:%M")
        table.add_row(
            s["session_id"][-15:],  # Truncate ID
            s["name"][:30],
            status,
            str(s["message_count"]),
            updated
        )

    console.print(table)


@cli.command()
@click.argument("session_id")
def show(session_id: str):
    """Show a session's specification."""
    manager = SessionManager()
    session = manager.load_session(session_id)

    if not session:
        session = manager.find_session_by_name(session_id)

    if not session:
        console.print(f"[red]Session not found: {session_id}[/red]")
        return

    generator = SpecGenerator()
    spec_md = generator.generate_markdown(session.spec)

    console.print(Panel(
        Markdown(spec_md),
        title=f"📋 {session.spec.name}",
        border_style="blue"
    ))


@cli.command()
@click.argument("session_id")
@click.option("--format", "-f", "fmt", default="markdown",
              type=click.Choice(["markdown", "claude", "json"]),
              help="Output format")
@click.option("--output", "-o", default=None, help="Output file path")
def export(session_id: str, fmt: str, output: Optional[str]):
    """Export a session's spec to a file."""
    manager = SessionManager()
    session = manager.load_session(session_id)

    if not session:
        session = manager.find_session_by_name(session_id)

    if not session:
        console.print(f"[red]Session not found: {session_id}[/red]")
        return

    generator = SpecGenerator()
    content = generator.generate(session.spec, fmt)

    if output:
        path = Path(output)
        path.write_text(content)
        console.print(f"[green]✓[/green] Exported to: {path}")
    else:
        # Print to stdout
        console.print(content)


@cli.command()
@click.argument("idea")
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--output", "-o", default=None, help="Output file")
@click.option("--skill", "-s", default="intermediate",
              type=click.Choice(["beginner", "intermediate", "advanced"]),
              help="Your skill level")
def quick(idea: str, provider: str, output: Optional[str], skill: str):
    """
    Quick mode - generate spec from a one-liner.

    Example:
        methinks quick "A CLI tool to organize my downloads folder"
    """
    console.print(f"[bold cyan]🤔 Processing:[/bold cyan] {idea}\n")

    connector = get_connector(provider)

    if not connector:
        console.print("[yellow]No API key - generating basic spec.[/yellow]\n")
        # Generate basic spec without AI
        from .models import ProjectSpec, UserProfile

        spec = ProjectSpec(
            name=idea[:50],
            tagline=idea,
            vision=idea,
            user_profile=UserProfile(skill_level=SkillLevel(skill)),
        )
    else:
        # Use AI to expand the idea
        asyncio.run(quick_generate(idea, connector, skill))
        return

    generator = SpecGenerator()
    content = generator.generate_claude_format(spec)

    if output:
        Path(output).write_text(content)
        console.print(f"[green]✓[/green] Exported to: {output}")
    else:
        console.print(Panel(Markdown(content), title="Generated Spec", border_style="blue"))


async def quick_generate(idea: str, connector, skill: str):
    """Generate spec from one-liner using AI."""
    from .models import ProjectSpec, UserProfile, SkillLevel

    prompt = f"""Based on this project idea, generate a concise but complete project specification.

Idea: {idea}

User skill level: {skill}

Return a JSON object with these fields:
- name: Project name (short, catchy)
- tagline: One-line description
- vision: 2-3 sentences about what this does and why
- problem_statement: What problem does this solve?
- must_have_features: Array of {{name, description}} for MVP features
- should_have_features: Array of {{name, description}} for v1.0 features
- tech_recommendation: Suggested language/framework and why
- success_criteria: Array of strings for "definition of done"

Keep it practical and achievable for a {skill} developer."""

    try:
        response = await connector.send_message(prompt)
        content = response.get("content", "")

        # Try to parse JSON from response
        import json
        import re

        # Find JSON in response
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            data = json.loads(json_match.group())

            spec = ProjectSpec(
                name=data.get("name", idea[:30]),
                tagline=data.get("tagline", idea),
                vision=data.get("vision", idea),
                problem_statement=data.get("problem_statement", ""),
                user_profile=UserProfile(skill_level=SkillLevel(skill)),
            )

            # Add features
            from .models import Feature, FeaturePriority
            for f in data.get("must_have_features", []):
                spec.features.append(Feature(
                    name=f.get("name", "Feature"),
                    description=f.get("description", ""),
                    priority=FeaturePriority.MUST
                ))

            for f in data.get("should_have_features", []):
                spec.features.append(Feature(
                    name=f.get("name", "Feature"),
                    description=f.get("description", ""),
                    priority=FeaturePriority.SHOULD
                ))

            if data.get("success_criteria"):
                spec.success_criteria = data["success_criteria"]

            if data.get("tech_recommendation"):
                spec.architecture_decisions["Technology Choice"] = data["tech_recommendation"]

            generator = SpecGenerator()
            console.print(Panel(
                Markdown(generator.generate_claude_format(spec)),
                title=f"📋 {spec.name}",
                border_style="blue"
            ))

            # Offer to save
            if Confirm.ask("\nSave this spec?", default=True):
                manager = SessionManager()
                session = manager.create_session()
                session.spec = spec
                session.is_complete = True
                manager.save_session(session)
                console.print(f"[green]✓[/green] Saved as: {session.session_id}")

    except Exception as e:
        console.print(f"[red]Error generating spec: {e}[/red]")


@cli.command()
@click.argument("session_id")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def delete(session_id: str, yes: bool):
    """Delete a session."""
    manager = SessionManager()

    if not yes:
        if not Confirm.ask(f"Delete session {session_id}?", default=False):
            return

    if manager.delete_session(session_id):
        console.print(f"[green]✓[/green] Deleted: {session_id}")
    else:
        console.print(f"[red]Session not found: {session_id}[/red]")


def main():
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
