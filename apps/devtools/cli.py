"""
DevTools CLI - AI-powered developer tools for The Nexus Connector.

These commands provide readable terminal UX for common dev tasks.
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

# Import from Nexus library
from nexus import NexusConnector

console = Console()


def get_api_key(provider: str) -> Optional[str]:
    """Get API key for a provider."""
    import os
    env_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GOOGLE_API_KEY",
        "xai": "XAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }
    return os.getenv(env_map.get(provider.lower(), f"{provider.upper()}_API_KEY"))


def create_connector(provider: str, **kwargs) -> NexusConnector:
    """Create a NexusConnector for the given provider."""
    api_key = get_api_key(provider)
    if not api_key and provider.lower() != "ollama":
        console.print(f"[red]Error:[/red] No API key found for {provider}")
        sys.exit(1)

    return NexusConnector(
        provider=provider,
        api_key=api_key or "",
        **kwargs
    )


def read_file_content(filepath: str) -> tuple[str, str]:
    """Read file content and detect language from extension."""
    path = Path(filepath)
    if not path.exists():
        raise click.ClickException(f"File not found: {filepath}")

    content = path.read_text()

    ext_map = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "typescript", ".jsx": "javascript", ".go": "go",
        ".rs": "rust", ".rb": "ruby", ".java": "java", ".cpp": "cpp",
        ".c": "c", ".h": "c", ".cs": "csharp", ".php": "php",
        ".swift": "swift", ".kt": "kotlin", ".scala": "scala",
        ".sh": "bash", ".sql": "sql", ".html": "html", ".css": "css",
        ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".md": "markdown",
    }
    lang = ext_map.get(path.suffix.lower(), "text")

    return content, lang


def stream_ai_response(connector, prompt: str) -> str:
    """Stream AI response with nice terminal output."""
    from nexus.core.base_connector import Message

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

    if full_response:
        connector.conversation_history.append(
            Message(role="assistant", content=full_response)
        )

    return full_response


# =============================================================================
# CLI GROUP
# =============================================================================

@click.group()
def devtools():
    """AI-powered developer tools."""
    pass


@devtools.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--focus", "-f", type=click.Choice(["security", "performance", "style", "bugs", "all"]),
              default="all", help="Review focus area")
def review(file: str, provider: str, focus: str):
    """
    AI-powered code review.

    Analyzes code for bugs, security issues, style, and improvements.

    Examples:
        nexus-devtools review src/api.py
        nexus-devtools review main.go --focus security
    """
    content, lang = read_file_content(file)
    filename = Path(file).name

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

    stream_ai_response(connector, prompt)


@devtools.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--framework", "-f", default=None, help="Test framework")
@click.option("--output", "-o", default=None, help="Output file")
def test(file: str, provider: str, framework: Optional[str], output: Optional[str]):
    """
    Generate tests for a file.

    Examples:
        nexus-devtools test src/utils.py
        nexus-devtools test api.ts --framework jest -o api.test.ts
    """
    content, lang = read_file_content(file)

    if not framework:
        framework_map = {
            "python": "pytest", "javascript": "jest", "typescript": "jest",
            "go": "go test", "rust": "cargo test", "ruby": "rspec", "java": "junit",
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

---

```{lang}
{content}
```

Generate the complete test file:"""

    response = stream_ai_response(connector, prompt)

    if output and "```" in response:
        import re
        code_match = re.search(r'```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_match:
            Path(output).write_text(code_match.group(1).strip())
            console.print(f"\n[green]✓[/green] Tests written to: {output}")


@devtools.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--style", "-s", type=click.Choice(["docstring", "markdown", "readme", "api"]),
              default="docstring", help="Documentation style")
@click.option("--output", "-o", default=None, help="Output file")
def docs(file: str, provider: str, style: str, output: Optional[str]):
    """
    Generate documentation for a file.

    Examples:
        nexus-devtools docs src/api.py
        nexus-devtools docs lib/utils.ts --style markdown -o DOCS.md
    """
    content, lang = read_file_content(file)

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

    response = stream_ai_response(connector, prompt)

    if output:
        Path(output).write_text(response)
        console.print(f"\n[green]✓[/green] Documentation written to: {output}")


@devtools.command()
@click.argument("target", required=False)
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--error", "-e", default=None, help="Error message to explain")
def explain(target: Optional[str], provider: str, error: Optional[str]):
    """
    Explain code or errors.

    Examples:
        nexus-devtools explain src/complex.py
        nexus-devtools explain --error "TypeError: Cannot read property 'x'"
    """
    import select

    def has_stdin_data() -> bool:
        if sys.stdin.isatty():
            return False
        if hasattr(select, 'select'):
            return select.select([sys.stdin], [], [], 0.0)[0] != []
        return True

    connector = create_connector(provider, verbose=False)

    if error:
        console.print(Panel(
            f"[bold]Error:[/bold]\n{error[:200]}{'...' if len(error) > 200 else ''}",
            title="❓ Explain Error",
            border_style="red"
        ))

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
        content, lang = read_file_content(target)

        console.print(Panel(
            f"[bold]File:[/bold] {target}\n"
            f"[bold]Language:[/bold] {lang}\n"
            f"[bold]Lines:[/bold] {len(content.splitlines())}",
            title="❓ Explain Code",
            border_style="magenta"
        ))

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
        piped_input = sys.stdin.read().strip()

        console.print(Panel(
            f"[bold]Input:[/bold]\n{piped_input[:300]}{'...' if len(piped_input) > 300 else ''}",
            title="❓ Explain",
            border_style="magenta"
        ))

        prompt = f"""Explain this:

```
{piped_input}
```

If it's an error, explain what went wrong and how to fix it.
If it's code, explain what it does.
If it's output/logs, explain what happened."""

    else:
        raise click.ClickException("Provide a file path, --error message, or pipe input")

    stream_ai_response(connector, prompt)


@devtools.command()
@click.argument("file", required=False, type=click.Path(exists=True))
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--error", "-e", default=None, help="Error message to fix")
@click.option("--apply", "-a", is_flag=True, help="Apply fix directly")
def fix(file: Optional[str], provider: str, error: Optional[str], apply: bool):
    """
    Fix code based on an error.

    Examples:
        nexus-devtools fix src/api.py --error "NameError: name 'foo' not defined"
        python app.py 2>&1 | nexus-devtools fix src/app.py --apply
    """
    import select

    def has_stdin_data() -> bool:
        if sys.stdin.isatty():
            return False
        if hasattr(select, 'select'):
            return select.select([sys.stdin], [], [], 0.0)[0] != []
        return True

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

    response = stream_ai_response(connector, prompt)

    if apply:
        import re
        code_match = re.search(r'## Solution\s*```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_match:
            fixed_code = code_match.group(1).strip()
            backup_path = Path(file).with_suffix(Path(file).suffix + ".bak")
            Path(file).rename(backup_path)
            Path(file).write_text(fixed_code)
            console.print(f"\n[green]✓[/green] Fix applied to: {file}")
            console.print(f"[dim]  Backup saved to: {backup_path}[/dim]")
        else:
            console.print("\n[yellow]Could not extract fixed code. Apply manually.[/yellow]")


@devtools.command()
@click.argument("file", type=click.Path(exists=True))
@click.option("--provider", "-p", default="openai", help="AI provider")
@click.option("--goal", "-g", default=None, help="Refactoring goal")
@click.option("--output", "-o", default=None, help="Output file")
def refactor(file: str, provider: str, goal: Optional[str], output: Optional[str]):
    """
    Refactor code with AI suggestions.

    Examples:
        nexus-devtools refactor src/legacy.py
        nexus-devtools refactor utils.ts --goal "split into smaller functions"
    """
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

## Benefits
- Benefit 1
- Benefit 2"""

    response = stream_ai_response(connector, prompt)

    if output:
        import re
        code_match = re.search(r'## Refactored Code\s*```(?:\w+)?\n(.*?)```', response, re.DOTALL)
        if code_match:
            Path(output).write_text(code_match.group(1).strip())
            console.print(f"\n[green]✓[/green] Refactored code written to: {output}")


def main():
    """Entry point."""
    devtools()


if __name__ == "__main__":
    main()
