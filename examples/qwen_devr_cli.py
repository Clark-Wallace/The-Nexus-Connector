#!/usr/bin/env python3
"""
QwenDevr - The Ultimate Qwen CLI Development Assistant

A Claude Code-inspired CLI powered by Qwen2.5-72B-Instruct via OpenRouter API.
Fast, efficient development assistance without thinking tokens.

Usage:
    python qwen_devr_cli.py "analyze this codebase"
    python qwen_devr_cli.py --file main.py "add error handling"
    python qwen_devr_cli.py --interactive
    python qwen_devr_cli.py --project-setup "FastAPI web app"
"""

import asyncio
import argparse
import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.markdown import Markdown
import time

# Add nexus to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import NexusConnector, AIProvider

console = Console()

class QwenDevr:
    """The Ultimate Qwen Development Assistant CLI"""
    
    def __init__(self, api_key: str, workspace: str = "./qwen_workspace"):
        """Initialize QwenDevr with OpenRouter API."""
        self.workspace = Path(workspace)
        self.workspace.mkdir(exist_ok=True)
        
        # Initialize Nexus with OpenRouter endpoint for Qwen
        # Default to latest Qwen3-235B (free on OpenRouter!)
        model = kwargs.get('model', 'qwen/qwen3-235b-a22b-07-25:free')
        
        self.qwen = NexusConnector(
            provider=AIProvider.OPENAI,  # Use OpenAI connector
            api_key=api_key,
            model=model,  # OpenRouter model ID
            base_url="https://openrouter.ai/api/v1",  # OpenRouter endpoint
            workspace=str(self.workspace),
            auto_execute=True,
            max_iterations=10,
            verbose=False
        )
        
        # Store model info
        self.current_model = model
        self.model_info = self.get_model_info(model)
        
        # Development tools and patterns
        self.dev_tools = [
            "read_file", "write_file", "list_directory", "create_directory",
            "run_command", "analyze_code", "generate_tests", "refactor_code",
            "add_documentation", "fix_bugs", "optimize_performance"
        ]
        
        self.project_types = {
            "web": "FastAPI/Flask web application",
            "api": "REST API service",
            "cli": "Command-line interface tool",
            "lib": "Python library/package", 
            "data": "Data analysis/ML project",
            "game": "Game development project",
            "mobile": "Mobile app backend"
        }
        
        # Available Qwen models on OpenRouter
        self.available_models = {
            "qwen3-235b": {
                "id": "qwen/qwen3-235b-a22b-07-25:free",
                "name": "Qwen3-235B (Latest, FREE!)",
                "description": "Most advanced Qwen model, 235B parameters, completely free",
                "cost": "FREE",
                "speed": "⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯🎯"
            },
            "qwen2.5-72b": {
                "id": "qwen/qwen-2.5-72b-instruct",
                "name": "Qwen2.5-72B-Instruct",
                "description": "Previous generation, 72B parameters, very fast",
                "cost": "$0.40/1M tokens",
                "speed": "⚡⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯"
            },
            "qwen2.5-coder": {
                "id": "qwen/qwen-2.5-coder-32b-instruct",
                "name": "Qwen2.5-Coder-32B",
                "description": "Specialized for coding tasks, 32B parameters",
                "cost": "$0.20/1M tokens",
                "speed": "⚡⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯"
            }
        }
    
    def get_model_info(self, model_id: str) -> Dict[str, str]:
        """Get information about the current model."""
        for key, info in self.available_models.items():
            if info["id"] == model_id:
                return info
        return {
            "name": model_id,
            "description": "Custom model",
            "cost": "Unknown",
            "speed": "⚡",
            "quality": "🎯"
        }
    
    async def switch_model(self, model_key: str) -> Dict[str, Any]:
        """Switch to a different Qwen model."""
        if model_key not in self.available_models:
            available = ", ".join(self.available_models.keys())
            return {"success": False, "error": f"Unknown model. Available: {available}"}
        
        model_info = self.available_models[model_key]
        
        # Create new connector with different model
        self.qwen = NexusConnector(
            provider=AIProvider.OPENAI,
            api_key=self.qwen.api_key,
            model=model_info["id"],
            base_url="https://openrouter.ai/api/v1",
            workspace=str(self.workspace),
            auto_execute=True,
            max_iterations=10,
            verbose=False
        )
        
        self.current_model = model_info["id"]
        self.model_info = model_info
        
        return {
            "success": True,
            "model": model_info["name"],
            "description": model_info["description"],
            "cost": model_info["cost"]
        }
    
    def show_models(self):
        """Show available Qwen models."""
        table = Table(title="🤖 Available Qwen Models")
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Model", style="white")
        table.add_column("Description", style="white")
        table.add_column("Cost", style="green")
        table.add_column("Speed", justify="center")
        table.add_column("Quality", justify="center")
        
        for key, info in self.available_models.items():
            # Mark current model
            current = "→ " if info["id"] == self.current_model else "  "
            table.add_row(
                f"{current}{key}",
                info["name"],
                info["description"],
                info["cost"],
                info["speed"],
                info["quality"]
            )
        
        console.print(table)
    
    async def welcome(self):
        """Display welcome message."""
        model_name = self.model_info.get("name", "Qwen Model")
        model_cost = self.model_info.get("cost", "Unknown cost")
        
        welcome_text = f"""
# 🚀 QwenDevr - The Ultimate Qwen CLI

Powered by **{model_name}** via OpenRouter API  
*Cost: {model_cost} | Fast, efficient development assistance without thinking tokens*

## ✨ NEW: Qwen3-235B is FREE on OpenRouter!
Most advanced Qwen model with 235B parameters - completely free to use!

## Quick Commands:
- `analyze` - Analyze current directory
- `setup <type>` - Set up new project  
- `fix <file>` - Fix issues in file
- `test <file>` - Generate tests
- `docs` - Generate documentation
- `refactor <file>` - Refactor code
- `models` - Show/switch between Qwen models
- `help` - Show detailed help
        """
        
        console.print(Panel(
            Markdown(welcome_text),
            title="QwenDevr CLI",
            border_style="bright_blue"
        ))
    
    async def analyze_project(self, focus: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the current project/directory."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🔍 Analyzing project with Qwen...", total=100)
            
            focus_instruction = f"\nFocus specifically on: {focus}" if focus else ""
            
            analysis_prompt = f"""
            I'm QwenDevr, your development assistant. Analyze this project directory:

            Please provide a comprehensive analysis including:

            1. **Project Structure & Architecture**
               - Main components and modules
               - Design patterns used
               - Dependencies and tech stack

            2. **Code Quality Assessment**
               - Potential bugs and issues
               - Code style consistency
               - Performance bottlenecks

            3. **Development Opportunities**
               - Missing features that should be added
               - Code that needs refactoring
               - Testing gaps

            4. **Quick Wins**
               - Immediate improvements possible
               - Documentation that's needed
               - Simple optimizations

            5. **Next Steps Recommendation**
               - Priority order for improvements
               - Estimated effort for each task
               
            {focus_instruction}

            Be specific, actionable, and concise. Format as clear sections with bullet points.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(analysis_prompt)
            progress.update(task, completed=100)
            
            return {
                "success": result.success,
                "analysis": result.output if result.success else "Analysis failed",
                "files_created": result.files_created,
                "cost": getattr(self.qwen, 'total_cost', 0.0)
            }
    
    async def setup_project(self, project_type: str, name: str = None) -> Dict[str, Any]:
        """Set up a new project structure."""
        if project_type not in self.project_types:
            available = ", ".join(self.project_types.keys())
            return {"success": False, "error": f"Unknown project type. Available: {available}"}
        
        project_name = name or f"qwen_{project_type}_project"
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"🛠️ Setting up {project_type} project...", total=100)
            
            setup_prompt = f"""
            Create a complete {self.project_types[project_type]} project structure named '{project_name}'.

            Requirements:
            1. **Project Structure** - Create proper directory structure
            2. **Core Files** - Main application files with working code
            3. **Configuration** - Requirements.txt, config files, etc.
            4. **Documentation** - README.md with setup instructions
            5. **Testing** - Basic test structure and examples
            6. **Development Tools** - Pre-commit, linting setup if appropriate

            Make it production-ready with:
            - Clean, well-commented code
            - Error handling and logging
            - Environment variables for config
            - Proper Python packaging structure
            - Clear usage examples

            Create all necessary files with actual working code, not just placeholders.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(setup_prompt)
            progress.update(task, completed=100)
            
            return {
                "success": result.success,
                "output": result.output if result.success else "Setup failed",
                "files_created": result.files_created,
                "project_name": project_name
            }
    
    async def fix_file(self, file_path: str, specific_issues: str = None) -> Dict[str, Any]:
        """Fix issues in a specific file."""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"🔧 Fixing {file_path}...", total=100)
            
            issues_context = f"\nSpecific issues to address: {specific_issues}" if specific_issues else ""
            
            fix_prompt = f"""
            Analyze and fix issues in {file_path}:

            1. **Code Analysis**
               - Identify bugs, errors, and potential issues
               - Check for style consistency and best practices
               - Look for performance problems

            2. **Fixes to Apply**
               - Fix any syntax errors or bugs
               - Improve error handling and edge cases
               - Add missing type hints and docstrings
               - Optimize performance where possible
               - Ensure proper logging and debugging support

            3. **Enhancements**
               - Add input validation where needed
               - Improve code readability and structure
               - Follow Python best practices (PEP 8, etc.)
               
            {issues_context}

            Preserve the existing functionality while making improvements.
            Create a backup of the original file before making changes.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(fix_prompt)
            progress.update(task, completed=100)
            
            return {
                "success": result.success,
                "output": result.output if result.success else "Fix failed",
                "files_modified": result.files_created
            }
    
    async def generate_tests(self, file_path: str) -> Dict[str, Any]:
        """Generate comprehensive tests for a file."""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"🧪 Generating tests for {file_path}...", total=100)
            
            test_prompt = f"""
            Generate comprehensive test suite for {file_path}:

            1. **Test Coverage**
               - Unit tests for all public functions/methods
               - Edge cases and error conditions
               - Integration tests if applicable
               - Performance tests for critical functions

            2. **Test Framework**
               - Use pytest as the testing framework
               - Include fixtures for common test data
               - Use parametrized tests where appropriate
               - Add test utilities and helpers

            3. **Test Quality**
               - Clear test names that describe what's being tested
               - Proper setup and teardown
               - Mock external dependencies
               - Test both happy path and error scenarios

            4. **Test Organization**
               - Create tests/ directory if it doesn't exist
               - Name test file as test_{original_filename}.py
               - Group related tests in classes
               - Add docstrings explaining complex test scenarios

            Aim for 90%+ code coverage and include examples of how to run the tests.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(test_prompt)
            progress.update(task, completed=100)
            
            return {
                "success": result.success,
                "output": result.output if result.success else "Test generation failed",
                "test_files": result.files_created
            }
    
    async def generate_docs(self, scope: str = "project") -> Dict[str, Any]:
        """Generate documentation for the project."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("📚 Generating documentation...", total=100)
            
            docs_prompt = f"""
            Generate comprehensive documentation for this {scope}:

            1. **README.md** (if project scope)
               - Clear project description and purpose
               - Installation and setup instructions
               - Usage examples and API documentation
               - Contributing guidelines and development setup

            2. **API Documentation**
               - Document all public functions and classes
               - Include parameter descriptions and return values
               - Add usage examples for each function
               - Document any configuration options

            3. **Developer Documentation**
               - Code architecture and design decisions
               - Setup instructions for development
               - Testing and deployment processes
               - Troubleshooting common issues

            4. **User Documentation**
               - Getting started guide
               - Common use cases and tutorials
               - FAQ section
               - Configuration examples

            Make documentation clear, comprehensive, and up-to-date with the current codebase.
            Include code examples and practical usage scenarios.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(docs_prompt)
            progress.update(task, completed=100)
            
            return {
                "success": result.success,
                "output": result.output if result.success else "Documentation generation failed",
                "docs_created": result.files_created
            }
    
    async def refactor_code(self, file_path: str, requirements: str) -> Dict[str, Any]:
        """Refactor code according to requirements."""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"♻️ Refactoring {file_path}...", total=100)
            
            refactor_prompt = f"""
            Refactor {file_path} according to these requirements:
            {requirements}

            Guidelines for refactoring:

            1. **Code Structure**
               - Apply SOLID principles and clean code practices
               - Extract reusable functions and classes
               - Reduce code duplication and complexity
               - Improve naming and organization

            2. **Performance & Quality**
               - Optimize algorithms and data structures
               - Add proper error handling and validation
               - Implement logging and debugging support
               - Add type hints and comprehensive docstrings

            3. **Maintainability**
               - Break down large functions into smaller ones
               - Use design patterns where appropriate
               - Make code more testable and modular
               - Follow Python best practices and PEP 8

            4. **Backward Compatibility**
               - Preserve existing public API where possible
               - Add deprecation warnings for removed features
               - Provide migration guide if breaking changes needed

            Create a backup of the original file and document all changes made.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(refactor_prompt)
            progress.update(task, completed=100)
            
            return {
                "success": result.success,
                "output": result.output if result.success else "Refactoring failed",
                "files_modified": result.files_created
            }
    
    async def interactive_mode(self):
        """Run QwenDevr in interactive mode."""
        await self.welcome()
        
        console.print("\n💬 [bold]Interactive Mode[/bold] - Type 'help' for commands, 'exit' to quit\n")
        
        while True:
            try:
                # Get user input
                user_input = Prompt.ask("\n[bold blue]QwenDevr[/bold blue]", default="help")
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("👋 Goodbye! Happy coding with QwenDevr!")
                    break
                
                # Parse command
                parts = user_input.strip().split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Execute command
                await self.handle_command(command, args, interactive=True)
                
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye! Happy coding with QwenDevr!")
                break
            except Exception as e:
                console.print(f"❌ Error: {str(e)}", style="red")
    
    async def handle_command(self, command: str, args: List[str], interactive: bool = False):
        """Handle a single command."""
        try:
            if command == "help":
                self.show_help()
            
            elif command == "analyze":
                focus = " ".join(args) if args else None
                result = await self.analyze_project(focus)
                self.display_result("Project Analysis", result)
            
            elif command == "setup":
                if not args:
                    console.print("❌ Usage: setup <project_type> [name]", style="red")
                    console.print(f"Available types: {', '.join(self.project_types.keys())}")
                    return
                
                project_type = args[0]
                name = args[1] if len(args) > 1 else None
                result = await self.setup_project(project_type, name)
                self.display_result("Project Setup", result)
            
            elif command == "fix":
                if not args:
                    console.print("❌ Usage: fix <file_path> [specific_issues]", style="red")
                    return
                
                file_path = args[0]
                issues = " ".join(args[1:]) if len(args) > 1 else None
                result = await self.fix_file(file_path, issues)
                self.display_result("File Fix", result)
            
            elif command == "test":
                if not args:
                    console.print("❌ Usage: test <file_path>", style="red")
                    return
                
                result = await self.generate_tests(args[0])
                self.display_result("Test Generation", result)
            
            elif command == "docs":
                scope = args[0] if args else "project"
                result = await self.generate_docs(scope)
                self.display_result("Documentation", result)
            
            elif command == "refactor":
                if len(args) < 2:
                    console.print("❌ Usage: refactor <file_path> <requirements>", style="red")
                    return
                
                file_path = args[0]
                requirements = " ".join(args[1:])
                result = await self.refactor_code(file_path, requirements)
                self.display_result("Code Refactoring", result)
            
            elif command == "models":
                if not args:
                    # Show available models
                    self.show_models()
                else:
                    # Switch model
                    result = await self.switch_model(args[0])
                    if result["success"]:
                        console.print(f"✅ [green]Switched to {result['model']}[/green]")
                        console.print(f"📝 {result['description']}")
                        console.print(f"💰 Cost: {result['cost']}")
                    else:
                        console.print(f"❌ {result['error']}", style="red")
            
            elif command == "model":
                # Alias for models command
                await self.handle_command("models", args, interactive)
            
            else:
                # Treat as free-form development request
                full_request = f"{command} {' '.join(args)}"
                await self.handle_free_form_request(full_request)
        
        except Exception as e:
            console.print(f"❌ Command failed: {str(e)}", style="red")
    
    async def handle_free_form_request(self, request: str):
        """Handle free-form development requests."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("🤖 Processing request with Qwen...", total=100)
            
            enhanced_prompt = f"""
            I'm QwenDevr, your development assistant. Process this development request:

            "{request}"

            Please:
            1. Understand what the user is asking for
            2. Analyze the current project context if relevant
            3. Provide a clear, actionable response
            4. Create any necessary code, files, or documentation
            5. Give step-by-step instructions if it's a complex task

            Be practical, specific, and helpful. If you need to create or modify files, do so.
            If you need more information, ask clarifying questions.
            """
            
            progress.update(task, completed=50)
            result = await self.qwen.execute_task(enhanced_prompt)
            progress.update(task, completed=100)
            
            self.display_result("Development Request", {
                "success": result.success,
                "output": result.output if result.success else "Request failed",
                "files_created": result.files_created
            })
    
    def display_result(self, title: str, result: Dict[str, Any]):
        """Display command result in a nice format."""
        if result["success"]:
            # Success panel
            console.print(f"\n✅ [bold green]{title} Complete[/bold green]")
            
            # Show output
            if "output" in result and result["output"]:
                console.print(Panel(
                    Markdown(result["output"]),
                    title="Result",
                    border_style="green"
                ))
            
            # Show files created/modified
            files = result.get("files_created", result.get("files_modified", result.get("test_files", result.get("docs_created", []))))
            if files:
                console.print(f"\n📁 [bold]Files created/modified:[/bold]")
                for file in files:
                    console.print(f"   • {file}")
            
            # Show cost if available
            if "cost" in result:
                console.print(f"\n💰 Cost: ${result['cost']:.4f}")
        
        else:
            # Error panel
            error_msg = result.get("error", result.get("output", "Unknown error"))
            console.print(Panel(
                f"❌ {error_msg}",
                title=f"{title} Failed",
                border_style="red"
            ))
    
    def show_help(self):
        """Show detailed help information."""
        help_text = """
# 🚀 QwenDevr Commands

## Core Commands:
- `analyze [focus]` - Analyze project/codebase
- `setup <type> [name]` - Set up new project
- `fix <file> [issues]` - Fix issues in file  
- `test <file>` - Generate tests for file
- `docs [scope]` - Generate documentation
- `refactor <file> <requirements>` - Refactor code

## Model Management:
- `models` - Show available Qwen models
- `models <key>` - Switch to different model
- Available models: qwen3-235b (FREE!), qwen2.5-72b, qwen2.5-coder

## Project Types (for setup):
- `web` - FastAPI/Flask web application
- `api` - REST API service  
- `cli` - Command-line interface tool
- `lib` - Python library/package
- `data` - Data analysis/ML project
- `game` - Game development project
- `mobile` - Mobile app backend

## Examples:
```bash
analyze security  # Focus on security issues
setup web my_app  # Create web app project
fix main.py performance issues  # Fix performance
test utils.py  # Generate tests
docs api  # Generate API docs
refactor old_code.py apply SOLID principles
models qwen3-235b  # Switch to FREE Qwen3-235B
```

## ✨ NEW: Qwen3-235B (FREE!)
The latest and most powerful Qwen model is now available for FREE on OpenRouter!
- 235B parameters (vs 72B in previous version)
- Significantly improved capabilities
- Zero cost - perfect for extensive development work

## Free-form Requests:
You can also make natural language requests:
- "create a REST API for user management"
- "add logging to all my functions"
- "optimize database queries in models.py"
- "add input validation to forms"
        """
        
        console.print(Panel(
            Markdown(help_text),
            title="QwenDevr Help",
            border_style="blue"
        ))


async def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="QwenDevr - The Ultimate Qwen CLI Development Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python qwen_devr_cli.py "analyze this codebase for security issues"
  python qwen_devr_cli.py --interactive
  python qwen_devr_cli.py --file main.py "add error handling"
  python qwen_devr_cli.py --setup web my_web_app
  python qwen_devr_cli.py --test utils.py
        """
    )
    
    parser.add_argument("request", nargs="?", help="Development request to process")
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive mode")
    parser.add_argument("--file", "-f", help="Target file for operations")
    parser.add_argument("--setup", help="Set up new project of specified type")
    parser.add_argument("--test", help="Generate tests for specified file")
    parser.add_argument("--analyze", help="Analyze project with optional focus")
    parser.add_argument("--docs", help="Generate documentation")
    parser.add_argument("--workspace", "-w", default="./qwen_workspace", help="Workspace directory")
    parser.add_argument("--model", "-m", choices=["qwen3-235b", "qwen2.5-72b", "qwen2.5-coder"], 
                       default="qwen3-235b", help="Qwen model to use (default: qwen3-235b FREE!)")
    
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        console.print("❌ [red]OPENROUTER_API_KEY environment variable is required[/red]")
        console.print("\n💡 Get your API key from: https://openrouter.ai/keys")
        console.print("💡 Set it with: export OPENROUTER_API_KEY='your-key-here'")
        sys.exit(1)
    
    # Initialize QwenDevr with specified model
    available_models = {
        "qwen3-235b": "qwen/qwen3-235b-a22b-07-25:free",
        "qwen2.5-72b": "qwen/qwen-2.5-72b-instruct", 
        "qwen2.5-coder": "qwen/qwen-2.5-coder-32b-instruct"
    }
    
    selected_model = available_models[args.model]
    qwen_devr = QwenDevr(api_key, args.workspace, model=selected_model)
    
    try:
        if args.interactive:
            await qwen_devr.interactive_mode()
        
        elif args.setup:
            await qwen_devr.welcome()
            result = await qwen_devr.setup_project(args.setup)
            qwen_devr.display_result("Project Setup", result)
        
        elif args.test:
            await qwen_devr.welcome()
            result = await qwen_devr.generate_tests(args.test)
            qwen_devr.display_result("Test Generation", result)
        
        elif args.analyze is not None:
            await qwen_devr.welcome()
            result = await qwen_devr.analyze_project(args.analyze if args.analyze else None)
            qwen_devr.display_result("Project Analysis", result)
        
        elif args.docs is not None:
            await qwen_devr.welcome()
            result = await qwen_devr.generate_docs(args.docs if args.docs else "project")
            qwen_devr.display_result("Documentation", result)
        
        elif args.file and args.request:
            await qwen_devr.welcome()
            result = await qwen_devr.fix_file(args.file, args.request)
            qwen_devr.display_result("File Fix", result)
        
        elif args.request:
            await qwen_devr.welcome()
            await qwen_devr.handle_free_form_request(args.request)
        
        else:
            await qwen_devr.interactive_mode()
    
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye! Happy coding with QwenDevr!")
    except Exception as e:
        console.print(f"❌ Fatal error: {str(e)}", style="red")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())