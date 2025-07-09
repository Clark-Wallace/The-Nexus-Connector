#!/usr/bin/env python3
"""
Test script for Nexus unified wrapper prototype.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add nexus to path
sys.path.insert(0, str(Path(__file__).parent))

from nexus import UnifiedAIWrapper, AIProvider


# Load environment variables
env_path = Path(__file__).parent.parent / "test" / ".env"
load_dotenv(env_path)


async def test_simple_message():
    """Test simple message sending."""
    print("\n=== Testing Simple Message ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        verbose=True
    )
    
    response = await wrapper.send_message("What is 2+2? Reply with just the number.")
    print(f"Response: {response['content']}")
    print(f"Tool calls: {len(response['tool_calls'])}")
    

async def test_task_execution():
    """Test task execution with file creation."""
    print("\n=== Testing Task Execution ===")
    
    # Create test workspace
    workspace = Path("test_workspace")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        workspace=workspace,
        verbose=True
    )
    
    task = """Create a Python file called 'fibonacci.py' that contains:
    1. A function to calculate the nth Fibonacci number
    2. A main block that tests the function with n=10
    3. Proper docstrings and comments
    
    Make sure the file is properly formatted and executable."""
    
    result = await wrapper.execute_task(task)
    
    print(f"\nTask Result: {result}")
    print(f"Files created: {result.files_created}")
    print(f"Success: {result.success}")
    print(f"Iterations: {result.iterations}")
    print(f"Duration: {result.duration:.2f}s")
    
    # Check if file was created
    fib_file = workspace / "fibonacci.py"
    if fib_file.exists():
        print(f"\n✅ File created successfully!")
        print(f"File content preview:")
        print("-" * 50)
        print(fib_file.read_text()[:500] + "...")


async def test_provider_switching():
    """Test switching between providers (if multiple are configured)."""
    print("\n=== Testing Provider Switching ===")
    
    providers_to_test = []
    
    # Check which providers have API keys
    if os.getenv("OPENAI_API_KEY"):
        providers_to_test.append((AIProvider.OPENAI, "gpt-4o"))
    
    if os.getenv("ANTHROPIC_API_KEY"):
        providers_to_test.append((AIProvider.ANTHROPIC, "claude-3-5-sonnet-20241022"))
    
    if os.getenv("XAI_API_KEY"):
        providers_to_test.append((AIProvider.XAI, "grok-3"))
    
    print(f"Testing {len(providers_to_test)} providers...")
    
    for provider, model in providers_to_test:
        try:
            print(f"\nTesting {provider.display_name}...")
            
            wrapper = UnifiedAIWrapper(
                provider=provider,
                api_key=os.getenv(f"{provider.value.upper()}_API_KEY") or os.getenv("XAI_API_KEY"),
                model=model,
                verbose=False
            )
            
            response = await wrapper.send_message(
                "What are you and what model are you? Reply in one sentence."
            )
            
            print(f"{provider.display_name}: {response['content']}")
            
        except Exception as e:
            print(f"{provider.display_name}: Failed - {e}")


async def main():
    """Run all tests."""
    print("🚀 Nexus Unified Wrapper - Prototype Test")
    print("=" * 50)
    
    # Test 1: Simple message
    await test_simple_message()
    
    # Test 2: Task execution
    await test_task_execution()
    
    # Test 3: Provider switching
    await test_provider_switching()
    
    print("\n✅ All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())