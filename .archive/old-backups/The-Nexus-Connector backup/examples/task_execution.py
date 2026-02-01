#!/usr/bin/env python3
"""
Example: Task Execution

This example demonstrates Nexus's advanced task execution capabilities,
showing how complex multi-step tasks are automatically broken down and completed.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import UnifiedAIWrapper, AIProvider


async def create_todo_app():
    """Create a complete TODO application."""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    # Create workspace for the project
    workspace = Path("./todo_app_project")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.OPENAI,
        api_key=api_key,
        workspace=workspace,
        verbose=True
    )
    
    task = """
    Create a complete Python TODO application with the following features:
    
    1. Command-line interface using argparse
    2. Add, list, complete, and delete tasks
    3. Save tasks to a JSON file
    4. Each task should have: id, title, description, created_at, completed
    5. Include error handling and validation
    6. Add a README.md with usage instructions
    7. Create a requirements.txt file
    8. Add example usage in a separate file
    
    Make it production-ready with proper structure and documentation.
    """
    
    print("🚀 Creating TODO Application...")
    print("=" * 60)
    
    result = await wrapper.execute_task(task)
    
    print(f"\n📊 Task Execution Summary:")
    print(f"   Success: {result.success}")
    print(f"   Iterations: {result.iterations}")
    print(f"   Total tokens: {result.total_tokens}")
    print(f"   Time elapsed: {result.elapsed_time:.2f}s")
    
    if result.files_created:
        print(f"\n📁 Files created:")
        for file in result.files_created:
            print(f"   ✅ {file}")
    
    if result.errors:
        print(f"\n❌ Errors encountered:")
        for error in result.errors:
            print(f"   - {error}")


async def create_web_scraper():
    """Create a web scraping tool."""
    load_dotenv()
    
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        print("Please set DEEPSEEK_API_KEY environment variable")
        return
    
    workspace = Path("./scraper_project")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=api_key,
        workspace=workspace,
        verbose=True,
        max_iterations=15  # Allow more iterations for complex task
    )
    
    task = """
    Create a professional web scraper with these specifications:
    
    1. Scrape product information from e-commerce sites
    2. Support multiple selectors (CSS and XPath)
    3. Handle pagination automatically
    4. Implement retry logic with exponential backoff
    5. Rate limiting to be respectful to servers
    6. Export data to CSV, JSON, and Excel formats
    7. Add logging with different verbosity levels
    8. Include proxy support
    9. Create a configuration file for easy customization
    10. Write comprehensive unit tests
    
    Structure it as a proper Python package with setup.py.
    """
    
    print("🕷️ Creating Web Scraper...")
    print("=" * 60)
    
    result = await wrapper.execute_task(task)
    
    # Display results
    if result.success:
        print("\n✅ Web scraper created successfully!")
        print(f"Check the '{workspace}' directory for the complete application.")
    else:
        print("\n❌ Task failed. See errors above.")


async def create_api_client():
    """Create an API client library."""
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("Please set ANTHROPIC_API_KEY environment variable")
        return
    
    workspace = Path("./api_client_project")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.ANTHROPIC,
        api_key=api_key,
        workspace=workspace,
        model="claude-3-5-sonnet-20241022",
        verbose=True
    )
    
    task = """
    Create a Python client library for a REST API with these features:
    
    1. Base client class with authentication support (API key, OAuth2)
    2. Automatic retry with exponential backoff
    3. Request/response interceptors
    4. Pagination handling
    5. Rate limiting
    6. Comprehensive error handling with custom exceptions
    7. Response caching with TTL
    8. Async and sync interfaces
    9. Type hints throughout
    10. Full test coverage with mocked responses
    11. Documentation with usage examples
    12. CLI tool for testing the API
    
    Use modern Python practices and make it pip-installable.
    """
    
    print("🔌 Creating API Client Library...")
    print("=" * 60)
    
    result = await wrapper.execute_task(task)
    
    if result.success:
        print(f"\n✅ API client library created in {result.elapsed_time:.2f} seconds!")


async def compare_task_execution():
    """Compare how different providers handle the same task."""
    load_dotenv()
    
    task = """
    Create a simple Python script that:
    1. Generates the Fibonacci sequence up to n terms
    2. Includes both iterative and recursive implementations
    3. Has proper error handling
    4. Includes docstrings and type hints
    """
    
    providers = [
        (AIProvider.OPENAI, "OPENAI_API_KEY"),
        (AIProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (AIProvider.DEEPSEEK, "DEEPSEEK_API_KEY"),
    ]
    
    print("📊 Comparing Task Execution Across Providers")
    print("=" * 60)
    print(f"Task: Create Fibonacci sequence generator")
    
    for provider, key_env in providers:
        api_key = os.getenv(key_env)
        if not api_key:
            print(f"\n❌ {provider.display_name}: No API key")
            continue
        
        workspace = Path(f"./comparison_{provider.value}")
        workspace.mkdir(exist_ok=True)
        
        try:
            wrapper = UnifiedAIWrapper(
                provider=provider,
                api_key=api_key,
                workspace=workspace,
                verbose=False
            )
            
            print(f"\n🤖 {provider.display_name}:")
            result = await wrapper.execute_task(task)
            
            print(f"   Success: {result.success}")
            print(f"   Iterations: {result.iterations}")
            print(f"   Tokens: {result.total_tokens}")
            print(f"   Time: {result.elapsed_time:.2f}s")
            print(f"   Files: {len(result.files_created)}")
            
        except Exception as e:
            print(f"   Error: {str(e)}")


async def main():
    """Run task execution examples."""
    print("🚀 Nexus Task Execution Examples")
    print("=" * 60)
    
    # Get user choice
    print("\nChoose an example to run:")
    print("1. Create TODO Application")
    print("2. Create Web Scraper")
    print("3. Create API Client Library")
    print("4. Compare Provider Task Execution")
    print("5. Run all examples")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        await create_todo_app()
    elif choice == "2":
        await create_web_scraper()
    elif choice == "3":
        await create_api_client()
    elif choice == "4":
        await compare_task_execution()
    elif choice == "5":
        await create_todo_app()
        print("\n" + "=" * 60 + "\n")
        await create_web_scraper()
        print("\n" + "=" * 60 + "\n")
        await create_api_client()
        print("\n" + "=" * 60 + "\n")
        await compare_task_execution()
    else:
        print("Invalid choice. Please run the script again.")
    
    print("\n✅ Task execution example completed!")


if __name__ == "__main__":
    asyncio.run(main())