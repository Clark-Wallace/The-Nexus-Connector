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
import logging
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

# Suppress ALL verbose logging - must be done before any imports
import sys
import os

# Completely disable all logging
logging.disable(logging.CRITICAL)

# Also set environment variable to suppress any child process logging
os.environ['PYTHONWARNINGS'] = 'ignore'

# Redirect stderr to devnull during imports
original_stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, fall back to system env vars

# Add nexus to path (QwenDevr is now in its own folder)
sys.path.insert(0, str(Path(__file__).parent.parent))

# Monkey patch the logger before importing nexus
import nexus.utils.logger
def silent_logger(name: str, verbose: bool = False) -> logging.Logger:
    """Return a logger that outputs nothing."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.CRITICAL)
    logger.handlers = []
    return logger

nexus.utils.logger.get_logger = silent_logger

from nexus import NexusConnector, AIProvider

# Restore stderr after imports
sys.stderr = original_stderr

console = Console()

class QwenDevr:
    """The Ultimate Qwen Development Assistant CLI"""
    
    def __init__(self, api_key: str, workspace: str = None, model: str = 'qwen/qwen3-coder'):
        """Initialize QwenDevr with OpenRouter API."""
        # Use current directory if no workspace specified
        self.workspace = Path(workspace) if workspace else Path.cwd()
        if workspace:
            self.workspace.mkdir(exist_ok=True)
        
        # Available Qwen models on OpenRouter (define first)
        self.available_models = {
            "qwen3-coder": {
                "id": "qwen/qwen3-coder",
                "name": "Qwen3-Coder-480B (NEW!)",
                "description": "MoE coding specialist, 480B total/35B active, released today!",
                "cost": "$0.40/1M tokens",
                "speed": "⚡⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯🎯",
                "tools": True  # Tool support available
            },
            "qwen3-235b": {
                "id": "qwen/qwen3-235b-a22b-07-25",
                "name": "Qwen3-235B (Latest)",
                "description": "Most advanced Qwen model, 235B parameters",
                "cost": "$0.40/1M tokens",
                "speed": "⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯🎯",
                "tools": False  # No tool support
            },
            "qwen2.5-72b": {
                "id": "qwen/qwen-2.5-72b-instruct",
                "name": "Qwen2.5-72B-Instruct",
                "description": "Previous generation, 72B parameters, very fast, supports tools",
                "cost": "$0.40/1M tokens",
                "speed": "⚡⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯",
                "tools": True  # Tool support available
            },
            "qwen2.5-coder": {
                "id": "qwen/qwen-2.5-coder-32b-instruct",
                "name": "Qwen2.5-Coder-32B",
                "description": "Specialized for coding tasks, 32B parameters, supports tools",
                "cost": "$0.20/1M tokens",
                "speed": "⚡⚡⚡⚡⚡",
                "quality": "🎯🎯🎯🎯",
                "tools": True  # Tool support available
            }
        }
        
        # Store model info (now that available_models is defined)
        self.current_model = model
        self.model_info = self.get_model_info(model)
        
        # Check if model supports tools
        supports_tools = self.model_info.get("tools", False)
        
        # Initialize Nexus with OpenRouter endpoint for Qwen
        # Suppress initialization message
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                self.qwen = NexusConnector(
                    provider=AIProvider.OPENAI,  # Use OpenAI connector
                    api_key=api_key,
                    model=model,  # OpenRouter model ID
                    base_url="https://openrouter.ai/api/v1",  # OpenRouter endpoint
                    workspace=str(Path.cwd()),  # Use actual current directory where command is run
                    auto_execute=supports_tools,  # Only auto-execute if model supports tools
                    max_iterations=10,
                    verbose=False
                )
            finally:
                sys.stdout = old_stdout
        
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
        supports_tools = model_info.get("tools", False)
        
        # Create new connector with different model
        # Suppress initialization message
        with open(os.devnull, 'w') as devnull:
            old_stdout = sys.stdout
            sys.stdout = devnull
            try:
                self.qwen = NexusConnector(
                    provider=AIProvider.OPENAI,
                    api_key=self.qwen.api_key,
                    model=model_info["id"],
                    base_url="https://openrouter.ai/api/v1",
                    workspace=str(Path.cwd()),  # Use actual current directory where command is run
                    auto_execute=supports_tools,  # Only auto-execute if model supports tools
                    max_iterations=10,
                    verbose=False
                )
            finally:
                sys.stdout = old_stdout
        
        self.current_model = model_info["id"]
        self.model_info = model_info
        
        tool_status = "✅ Tool support enabled" if supports_tools else "⚠️ No tool support (text-only mode)"
        
        return {
            "success": True,
            "model": model_info["name"],
            "description": model_info["description"],
            "cost": model_info["cost"],
            "tools": tool_status
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
        table.add_column("Tools", justify="center")
        
        for key, info in self.available_models.items():
            # Mark current model with star
            current = "⭐ " if info["id"] == self.current_model else "   "
            tools_icon = "🛠️" if info.get("tools", False) else "💬"
            # Highlight current model row
            style = "bold yellow" if info["id"] == self.current_model else None
            table.add_row(
                f"{current}{key}",
                info["name"],
                info["description"],
                info["cost"],
                info["speed"],
                info["quality"],
                tools_icon,
                style=style
            )
        
        console.print(table)
    
    def show_status(self):
        """Show current model status and capabilities."""
        model_name = self.model_info.get("name", "Unknown Model")
        model_cost = self.model_info.get("cost", "Unknown cost")
        supports_tools = self.model_info.get("tools", False)
        
        # Get current model key
        current_key = "unknown"
        for key, info in self.available_models.items():
            if info["id"] == self.current_model:
                current_key = key
                break
        
        status_table = Table(title="📊 Current QwenDevr Status")
        status_table.add_column("Property", style="cyan", no_wrap=True)
        status_table.add_column("Value", style="white")
        
        status_table.add_row("Model Key", f"⭐ {current_key}")
        status_table.add_row("Model Name", model_name)
        status_table.add_row("Model ID", self.current_model)
        status_table.add_row("Cost", model_cost)
        status_table.add_row("Speed", self.model_info.get("speed", "⚡"))
        status_table.add_row("Quality", self.model_info.get("quality", "🎯"))
        status_table.add_row("Tool Support", "🛠️ Enabled" if supports_tools else "💬 Text-only")
        status_table.add_row("Auto-Execute", "✅ On" if supports_tools else "❌ Off (text-only)")
        status_table.add_row("Working Directory", str(Path.cwd()))
        
        console.print(status_table)
        
        # Show capabilities based on model
        if not supports_tools:
            console.print("\n⚠️  [yellow]Current model is text-only. For full development capabilities:")
            console.print("   • Switch to qwen2.5-72b or qwen2.5-coder")
            console.print("   • Use: [bold]models qwen2.5-72b[/bold]")
    
    async def welcome(self):
        """Display welcome message."""
        model_name = self.model_info.get("name", "Qwen Model")
        supports_tools = self.model_info.get("tools", False)
        
        # Get current model key for display
        current_key = "unknown"
        for key, info in self.available_models.items():
            if info["id"] == self.current_model:
                current_key = key
                break
        
        # Clear any initialization messages
        console.clear()
        
        # Fancy header
        header = f"""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║  ██████╗ ██╗    ██╗███████╗███╗   ██╗██████╗ ███████╗██╗   ██╗ ║
║ ██╔═══██╗██║    ██║██╔════╝████╗  ██║██╔══██╗██╔════╝██║   ██║ ║
║ ██║   ██║██║ █╗ ██║█████╗  ██╔██╗ ██║██║  ██║█████╗  ██║   ██║ ║
║ ██║▄▄ ██║██║███╗██║██╔══╝  ██║╚██╗██║██║  ██║██╔══╝  ╚██╗ ██╔╝ ║
║ ╚██████╔╝╚███╔███╔╝███████╗██║ ╚████║██████╔╝███████╗ ╚████╔╝  ║
║  ╚══▀▀═╝  ╚══╝╚══╝ ╚══════╝╚═╝  ╚═══╝╚═════╝ ╚══════╝  ╚═══╝   ║
║                                                                  ║
║              🤖 Powered by {model_name:<37} ║
║              ⚡ Model: {current_key:<41} ║
║              🛠️  Tools: {('Enabled' if supports_tools else 'Text-only'):<40} ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
"""
        console.print(header, style="bright_cyan")
        
        if not supports_tools:
            console.print("⚠️  Text-only mode. Use `models qwen2.5-72b` for full capabilities.", style="yellow")
        
        console.print("\n💡 Type your request or use `help` for commands.", style="dim")
    
    async def analyze_project(self, focus: Optional[str] = None) -> Dict[str, Any]:
        """Analyze the current project/directory."""
        # Show what we're doing
        console.print(f"\n🔍 [bold]Analyzing project{f' with focus on {focus}' if focus else ''}...[/bold]")
        
        with console.status("[bold cyan]Qwen is analyzing your codebase...[/bold cyan]", spinner="dots"):
            
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
            result = await self.qwen.execute_task(analysis_prompt)
            
            return {
                "success": result.success,
                "analysis": result.content if result.success else "Analysis failed",
                "files_created": result.files_created,
                "cost": getattr(self.qwen, 'total_cost', 0.0)
            }
    
    async def setup_project(self, project_type: str, name: str = None) -> Dict[str, Any]:
        """Set up a new project structure."""
        if project_type not in self.project_types:
            available = ", ".join(self.project_types.keys())
            return {"success": False, "error": f"Unknown project type. Available: {available}"}
        
        project_name = name or f"qwen_{project_type}_project"
        
        with console.status(f"🛠️ Setting up {project_type} project...", spinner="dots"):
            
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
            
            result = await self.qwen.execute_task(setup_prompt)
            
            return {
                "success": result.success,
                "output": result.content if result.success else "Setup failed",
                "files_created": result.files_created,
                "project_name": project_name
            }
    
    async def fix_file(self, file_path: str, specific_issues: str = None) -> Dict[str, Any]:
        """Fix issues in a specific file."""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        with console.status(f"🔧 Fixing {file_path}...", spinner="dots"):
            
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
            
            result = await self.qwen.execute_task(fix_prompt)
            
            return {
                "success": result.success,
                "output": result.content if result.success else "Fix failed",
                "files_modified": result.files_created
            }
    
    async def generate_tests(self, file_path: str) -> Dict[str, Any]:
        """Generate comprehensive tests for a file."""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        with console.status(f"🧪 Generating tests for {file_path}...", spinner="dots"):
            
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
            
            result = await self.qwen.execute_task(test_prompt)
            
            return {
                "success": result.success,
                "output": result.content if result.success else "Test generation failed",
                "test_files": result.files_created
            }
    
    async def generate_docs(self, scope: str = "project") -> Dict[str, Any]:
        """Generate documentation for the project."""
        with console.status("📚 Generating documentation...", spinner="dots"):
            
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
            
            result = await self.qwen.execute_task(docs_prompt)
            
            return {
                "success": result.success,
                "output": result.content if result.success else "Documentation generation failed",
                "docs_created": result.files_created
            }
    
    async def refactor_code(self, file_path: str, requirements: str) -> Dict[str, Any]:
        """Refactor code according to requirements."""
        if not Path(file_path).exists():
            return {"success": False, "error": f"File {file_path} not found"}
        
        with console.status(f"♻️ Refactoring {file_path}...", spinner="dots"):
            
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
            
            result = await self.qwen.execute_task(refactor_prompt)
            
            return {
                "success": result.success,
                "output": result.content if result.success else "Refactoring failed",
                "files_modified": result.files_created
            }
    
    async def interactive_mode(self):
        """Run QwenDevr in interactive mode."""
        await self.welcome()
        console.print()
        
        while True:
            try:
                # Get user input
                try:
                    user_input = Prompt.ask("QwenDevr")
                except EOFError:
                    console.print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    console.print("👋 Goodbye!")
                    break
                
                # Parse command
                parts = user_input.strip().split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Execute command
                await self.handle_command(command, args, interactive=True)
                
            except KeyboardInterrupt:
                console.print("\n👋 Goodbye!")
                break
            except Exception as e:
                console.print(f"❌ Error: {str(e)}")
    
    async def handle_command(self, command: str, args: List[str], interactive: bool = False):
        """Handle a single command."""
        try:
            if command == "help":
                self.show_help()
            
            elif command == "analyze":
                focus = " ".join(args) if args else None
                await self.handle_free_form_request(f"analyze this project" + (f" focusing on {focus}" if focus else ""))
            
            elif command == "setup":
                if not args:
                    console.print("❌ Usage: setup <project_type> [name]")
                    console.print(f"Available types: {', '.join(self.project_types.keys())}")
                    return
                
                project_type = args[0]
                name = args[1] if len(args) > 1 else None
                await self.handle_free_form_request(f"set up a {project_type} project" + (f" named {name}" if name else ""))
            
            elif command == "fix":
                if not args:
                    console.print("❌ Usage: fix <file_path> [specific_issues]")
                    return
                
                file_path = args[0]
                issues = " ".join(args[1:]) if len(args) > 1 else None
                await self.handle_free_form_request(f"fix {file_path}" + (f" - {issues}" if issues else ""))
            
            elif command == "test":
                if not args:
                    console.print("❌ Usage: test <file_path>")
                    return
                
                await self.handle_free_form_request(f"generate tests for {args[0]}")
            
            elif command == "docs":
                scope = args[0] if args else "project"
                await self.handle_free_form_request(f"generate documentation for {scope}")
            
            elif command == "refactor":
                if len(args) < 2:
                    console.print("❌ Usage: refactor <file_path> <requirements>")
                    return
                
                file_path = args[0]
                requirements = " ".join(args[1:])
                await self.handle_free_form_request(f"refactor {file_path} to {requirements}")
            
            elif command == "models":
                if not args:
                    # Show available models
                    self.show_models()
                else:
                    # Switch model
                    result = await self.switch_model(args[0])
                    if result["success"]:
                        # Prominent model switch notification
                        switch_panel = Panel(
                            f"""✅ **Model Switched Successfully!**

🤖 **Now using:** {result['model']}
📝 **Description:** {result['description']}
💰 **Cost:** {result['cost']}
🔧 **Tools:** {result['tools']}

Type `status` anytime to check your current model.""",
                            title="🔄 Model Switch",
                            border_style="green"
                        )
                        console.print(switch_panel)
                    else:
                        console.print(f"❌ {result['error']}", style="red")
            
            elif command == "model":
                # Alias for models command
                await self.handle_command("models", args, interactive)
            
            elif command == "status":
                self.show_status()
            
            elif command == "mkdir" or command == "create-folder":
                if not args:
                    console.print("❌ Usage: mkdir <folder_name>", style="red")
                    return
                
                folder_name = args[0]
                try:
                    Path(folder_name).mkdir(exist_ok=True)
                    console.print(f"✅ Created folder: {folder_name}")
                except Exception as e:
                    console.print(f"❌ Failed to create folder: {e}", style="red")
            
            elif command == "ls" or command == "list":
                try:
                    cwd = Path.cwd()
                    items = list(cwd.iterdir())
                    console.print(f"\n📁 Contents of {cwd}:")
                    for item in sorted(items):
                        icon = "📁" if item.is_dir() else "📄"
                        console.print(f"   {icon} {item.name}")
                except Exception as e:
                    console.print(f"❌ Failed to list directory: {e}", style="red")
            
            else:
                # Treat as free-form development request
                full_request = f"{command} {' '.join(args)}"
                await self.handle_free_form_request(full_request)
        
        except Exception as e:
            console.print(f"❌ Command failed: {str(e)}", style="red")
    
    async def handle_free_form_request(self, request: str):
        """Handle free-form development requests like Claude Code."""
        # Check for simple greetings
        simple_greetings = ['hello', 'hi', 'hey', 'howdy', 'greetings', 'hello qwen', 'hi qwen']
        if request.strip().lower() in simple_greetings:
            console.print(f"👋 Hello! I'm Qwen, your development assistant.")
            return
        
        # Check for simple folder creation requests
        request_lower = request.strip().lower()
        if any(phrase in request_lower for phrase in ['create a folder', 'make a folder', 'create folder', 'make folder', 'mkdir']):
            # Extract folder name if specified
            import re
            patterns = [
                r'(?:folder|directory)\s+(?:called|named)\s+["\']?(\w+)["\']?',
                r'(?:create|make)\s+["\']?(\w+)["\']?\s+(?:folder|directory)',
                r'(?:folder|directory)\s+["\']?(\w+)["\']?',
                r'mkdir\s+["\']?(\w+)["\']?'
            ]
            
            folder_name = None
            for pattern in patterns:
                match = re.search(pattern, request_lower)
                if match:
                    folder_name = match.group(1)
                    break
            
            if not folder_name:
                folder_name = "new_folder"
            
            try:
                Path(folder_name).mkdir(exist_ok=True)
                console.print(f"✅ Created folder: {folder_name}")
                console.print(f"📁 Location: {Path(folder_name).absolute()}")
                return
            except Exception as e:
                console.print(f"❌ Failed to create folder: {e}", style="red")
                return
            
        # Check if current model supports tools
        supports_tools = self.model_info.get("tools", False)
        if not supports_tools:
            console.print("⚠️  Current model (Qwen3-235B) is text-only. For file operations, switch to:")
            console.print("   • `models qwen2.5-72b` - Full development capabilities")
            console.print("   • `models qwen2.5-coder` - Coding specialist")
            console.print("\nFor now, I can provide advice and explanations in text-only mode.")
            
        # Simple, direct prompt like Claude Code
        simple_prompt = f"""You are Qwen, a development assistant with file system access. The user said: "{request}"

IMPORTANT: If the user asks you to check, verify, or do something with files/folders, you MUST use your tools to actually do it. Don't just say what you would do - actually do it.

Available tools: create_file, read_file, list_files, execute_command

Current directory: {Path.cwd()}

Be direct and execute actions immediately when asked."""

        try:
            # Show what we're doing with a nice status
            status_messages = [
                "🤖 Understanding your request...",
                "🔍 Planning the approach...",
                "🛠️ Executing tasks...",
                "📝 Creating files...",
                "✨ Finalizing..."
            ]
            
            # Start the task
            console.print(f"\n[bold]→ Task:[/bold] {request}")
            
            # Execute with animated status
            import random
            status_idx = 0
            
            async def execute_with_status():
                with console.status("[bold cyan]" + status_messages[0] + "[/bold cyan]", spinner="dots") as status:
                    # Start a background task to update status
                    async def update_status():
                        nonlocal status_idx
                        import asyncio
                        while status_idx < len(status_messages) - 1:
                            await asyncio.sleep(1.5)
                            status_idx += 1
                            status.update(f"[bold cyan]{status_messages[status_idx]}[/bold cyan]")
                    
                    # Run status updates in background
                    status_task = asyncio.create_task(update_status())
                    
                    try:
                        # Execute the actual task
                        result = await self.qwen.execute_task(simple_prompt)
                        status_task.cancel()
                        return result
                    except:
                        status_task.cancel()
                        raise
            
            result = await execute_with_status()
            
            if result.success:
                # Extract clean response without the iterations and guidance
                content = result.content
                
                # Remove common patterns from the messy output
                if "[Guidance provided]" in content:
                    content = content.split("[Guidance provided]")[0].strip()
                if "--- Iteration" in content:
                    content = content.split("--- Iteration")[0].strip()
                if "task complete" in content.lower():
                    content = content.replace("task complete", "").strip()
                
                # Show clean output
                if content:
                    console.print(f"\n{content}")
                
                # Show any files created with nice formatting
                if result.files_created:
                    console.print(f"\n[bold green]✨ Created {len(result.files_created)} file{'s' if len(result.files_created) > 1 else ''}:[/bold green]")
                    for file in result.files_created:
                        file_path = Path(file)
                        size = file_path.stat().st_size if file_path.exists() else 0
                        console.print(f"   📄 [cyan]{file_path.name}[/cyan] ({size} bytes) → {file_path.absolute()}")
                
                # If no files were created but the response suggests they should have been
                if not result.files_created and any(phrase in content.lower() for phrase in ["created", "made", "written", "saved"]):
                    console.print("\n⚠️  [yellow]Note: It seems like files should have been created but weren't.[/yellow]")
                    console.print("[yellow]Try switching to qwen2.5-72b model for better file operations: `models qwen2.5-72b`[/yellow]")
                    
            else:
                console.print(f"❌ {result.error or 'Request failed'}")
                
        except Exception as e:
            console.print(f"❌ Error: {str(e)}")
    
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

## 🚀 Instant Commands (No AI Processing):
- `mkdir <name>` - Create folder instantly
- `ls` - List current directory contents
- `models` - Show/switch AI models
- `status` - Show current model info

## 🤖 AI Commands (Requires Tool-Enabled Model):
- `analyze [focus]` - Analyze project/codebase
- `setup <type> [name]` - Set up new project
- `fix <file> [issues]` - Fix issues in file  
- `test <file>` - Generate tests for file
- `docs [scope]` - Generate documentation
- `refactor <file> <requirements>` - Refactor code

## Model Management:
- `models` - Show available Qwen models (⭐ marks current)
- `models <key>` - Switch to different model
- `status` - Show current model and capabilities
- Available models: qwen3-coder (default), qwen3-235b, qwen2.5-72b, qwen2.5-coder

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
    parser.add_argument("--workspace", "-w", default=None, help="Workspace directory (default: current directory)")
    parser.add_argument("--model", "-m", choices=["qwen3-coder", "qwen3-235b", "qwen2.5-72b", "qwen2.5-coder"], 
                       default="qwen3-coder", help="Qwen model to use (default: qwen3-coder - NEW!)")
    
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
        "qwen3-coder": "qwen/qwen3-coder",
        "qwen3-235b": "qwen/qwen3-235b-a22b-07-25",
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