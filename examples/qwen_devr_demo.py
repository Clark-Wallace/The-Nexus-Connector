#!/usr/bin/env python3
"""
QwenDevr Demo Script

This script demonstrates QwenDevr's capabilities without needing an API key.
Shows the CLI interface, command parsing, and example workflows.
"""

import asyncio
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from rich.columns import Columns

console = Console()

def demo_welcome():
    """Show QwenDevr welcome demo."""
    welcome_text = """
# 🚀 QwenDevr - The Ultimate Qwen CLI

Powered by **Qwen2.5-72B-Instruct** via OpenRouter API  
*Fast, efficient development assistance without thinking tokens*

## Why QwenDevr?
- ⚡ **No Thinking Tokens** - Direct responses, no verbose reasoning like DeepSeek
- 🎯 **Claude Code-like Interface** - Familiar commands for developers  
- 🛠️ **Complete Toolkit** - Analysis, setup, testing, docs, refactoring
- 💰 **Cost Effective** - Qwen2.5 offers great value on OpenRouter
- 🚀 **Production Ready** - Built on Nexus Connector framework
    """
    
    console.print(Panel(
        Markdown(welcome_text),
        title="QwenDevr Demo",
        border_style="bright_blue"
    ))

def demo_commands():
    """Show available commands."""
    
    # Create commands table
    table = Table(title="🛠️ QwenDevr Commands")
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    table.add_column("Example", style="green")
    
    commands = [
        ("analyze [focus]", "Analyze project/codebase", "analyze security"),
        ("setup <type> [name]", "Create new project", "setup web my_app"),
        ("fix <file> [issues]", "Fix issues in file", "fix main.py bugs"),
        ("test <file>", "Generate tests", "test utils.py"),
        ("docs [scope]", "Generate documentation", "docs api"),
        ("refactor <file> <req>", "Refactor code", "refactor old.py SOLID"),
        ("Interactive Mode", "Chat-like interface", "python qwen_devr_cli.py -i"),
    ]
    
    for command, desc, example in commands:
        table.add_row(command, desc, example)
    
    console.print(table)

def demo_project_types():
    """Show supported project types."""
    
    project_types = [
        ("🌐 web", "FastAPI/Flask web application\nwith database integration"),
        ("🔌 api", "REST API service with\nauthentication & validation"),
        ("⚡ cli", "Command-line interface tool\nwith Click/Typer framework"),
        ("📦 lib", "Python library/package\nwith proper structure"),
        ("📊 data", "Data analysis/ML project\nwith Jupyter setup"),
        ("🎮 game", "Game development project\nwith assets structure"),
        ("📱 mobile", "Mobile app backend\nwith API endpoints"),
    ]
    
    panels = []
    for title, desc in project_types:
        panels.append(Panel(desc, title=title, border_style="blue"))
    
    console.print("\n")
    console.print(Columns(panels, equal=True, expand=True))

def demo_comparison():
    """Show model comparison."""
    
    table = Table(title="🤖 Model Comparison")
    table.add_column("Model", style="cyan")
    table.add_column("Parameters", justify="center")
    table.add_column("Speed", justify="center")
    table.add_column("Code Quality", justify="center")
    table.add_column("Thinking Tokens", justify="center")
    table.add_column("Cost", justify="center")
    
    models = [
        ("🆕 Qwen3-235B", "235B", "⚡⚡⚡⚡", "🎯🎯🎯🎯🎯", "✅ None", "🆓 FREE!"),
        ("Qwen2.5-72B", "72B", "⚡⚡⚡⚡⚡", "🎯🎯🎯🎯", "✅ None", "💰💰"),
        ("DeepSeek-R1", "671B", "⚡", "🎯🎯🎯🎯🎯", "❌ Verbose", "💰"),
        ("Claude-3.5", "?", "⚡⚡", "🎯🎯🎯🎯", "✅ None", "💰💰💰"),
        ("GPT-4o", "?", "⚡⚡", "🎯🎯🎯", "✅ None", "💰💰💰"),
    ]
    
    for model, params, speed, quality, thinking, cost in models:
        table.add_row(model, params, speed, quality, thinking, cost)
    
    console.print("\n")
    console.print(table)
    
    # Highlight the new FREE model
    console.print("\n🎉 [bold green]NEW: Qwen3-235B is completely FREE on OpenRouter![/bold green]")
    console.print("• 235B parameters (3x larger than Qwen2.5-72B)")
    console.print("• Significantly improved capabilities")
    console.print("• Zero cost for unlimited usage")
    console.print("• Perfect for extensive development work")

def demo_workflow_examples():
    """Show example workflows."""
    
    workflows = [
        {
            "title": "🔍 Project Analysis Workflow",
            "steps": [
                "python qwen_devr_cli.py --analyze",
                "Review generated analysis report",
                "Address identified issues",
                "Re-analyze to verify improvements"
            ]
        },
        {
            "title": "🚀 New Project Setup Workflow", 
            "steps": [
                "python qwen_devr_cli.py --setup web my_app",
                "Review generated project structure",
                "Customize configuration files",
                "Run initial tests and development server"
            ]
        },
        {
            "title": "🧪 Testing Workflow",
            "steps": [
                "python qwen_devr_cli.py --test models.py",
                "Review generated test cases",
                "Run tests: pytest tests/",
                "Fix any failing tests"
            ]
        },
        {
            "title": "📚 Documentation Workflow",
            "steps": [
                "python qwen_devr_cli.py --docs",
                "Review generated documentation",
                "Add custom sections if needed",
                "Deploy docs to GitHub Pages"
            ]
        }
    ]
    
    for workflow in workflows:
        steps_text = "\n".join([f"{i+1}. {step}" for i, step in enumerate(workflow["steps"])])
        console.print(Panel(
            steps_text,
            title=workflow["title"],
            border_style="green"
        ))

def demo_interactive_session():
    """Show what interactive session looks like."""
    
    session_demo = """
**QwenDevr Interactive Session Demo:**

```bash
$ python qwen_devr_cli.py --interactive

🚀 QwenDevr - The Ultimate Qwen CLI
Powered by Qwen2.5-72B-Instruct via OpenRouter API

💬 Interactive Mode - Type 'help' for commands, 'exit' to quit

QwenDevr> analyze security
🔍 Analyzing project with Qwen...
✅ Project Analysis Complete
📁 Files created: security_analysis.md

QwenDevr> setup api user_service  
🛠️ Setting up api project...
✅ Project Setup Complete
📁 Files created: user_service/ (15 files)

QwenDevr> test models.py
🧪 Generating tests for models.py...
✅ Test Generation Complete
📁 Files created: tests/test_models.py

QwenDevr> create a Redis caching layer
🤖 Processing request with Qwen...
✅ Development Request Complete
📁 Files created: cache.py, redis_config.py

QwenDevr> exit
👋 Goodbye! Happy coding with QwenDevr!
```
    """
    
    console.print(Panel(
        Markdown(session_demo),
        title="💬 Interactive Mode Demo",
        border_style="magenta"
    ))

def demo_setup_instructions():
    """Show setup instructions."""
    
    setup_text = """
# 🛠️ Quick Setup Instructions

## 1. Install Dependencies
```bash
pip install rich click typer prompt-toolkit
```

## 2. Get OpenRouter API Key
- Visit: https://openrouter.ai/keys
- Sign up and get your API key
- Set environment variable:
```bash
export OPENROUTER_API_KEY="your-key-here"
```

## 3. Run QwenDevr
```bash
# Interactive mode (recommended)
python qwen_devr_cli.py --interactive

# Quick commands
python qwen_devr_cli.py "analyze this codebase"
python qwen_devr_cli.py --setup web my_app
```

## 4. Start Developing!
QwenDevr will create a workspace directory and help you build amazing projects.
    """
    
    console.print(Panel(
        Markdown(setup_text),
        title="⚡ Quick Setup",
        border_style="yellow"
    ))

async def main():
    """Run the demo."""
    console.clear()
    
    # Welcome and overview
    demo_welcome()
    
    console.input("\n[bold blue]Press Enter to see available commands...[/bold blue]")
    console.clear()
    
    # Commands overview
    demo_commands()
    
    console.input("\n[bold blue]Press Enter to see project types...[/bold blue]")
    console.clear()
    
    # Project types
    demo_project_types()
    
    console.input("\n[bold blue]Press Enter to see model comparison...[/bold blue]")
    console.clear()
    
    # Model comparison
    demo_comparison()
    
    console.input("\n[bold blue]Press Enter to see workflow examples...[/bold blue]")
    console.clear()
    
    # Workflow examples
    demo_workflow_examples()
    
    console.input("\n[bold blue]Press Enter to see interactive session demo...[/bold blue]")
    console.clear()
    
    # Interactive session demo
    demo_interactive_session()
    
    console.input("\n[bold blue]Press Enter to see setup instructions...[/bold blue]")
    console.clear()
    
    # Setup instructions
    demo_setup_instructions()
    
    # Final message
    console.print("\n" + "="*60)
    console.print("🚀 [bold]QwenDevr Demo Complete![/bold]")
    console.print("\n💡 [yellow]Ready to try the real thing?[/yellow]")
    console.print("1. Get your OpenRouter API key: https://openrouter.ai/keys")
    console.print("2. Run: python qwen_devr_cli.py --interactive")
    console.print("3. Start building amazing projects with Qwen! 🎯")
    console.print("="*60)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("\n👋 Demo ended. Happy coding!")