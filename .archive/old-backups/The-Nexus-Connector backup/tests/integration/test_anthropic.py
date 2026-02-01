#!/usr/bin/env python3
"""
Test script for Anthropic Claude connector in Nexus.
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


async def test_anthropic_simple():
    """Test Anthropic with simple message."""
    print("\n=== Testing Anthropic Simple Message ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-20241022",
        verbose=True
    )
    
    response = await wrapper.send_message(
        "What is Claude and what are its key strengths? Reply in 2-3 sentences."
    )
    
    print(f"\nResponse: {response['content']}")
    print(f"Tool calls: {len(response.get('tool_calls', []))}")
    

async def test_anthropic_task():
    """Test Anthropic with a coding task."""
    print("\n=== Testing Anthropic Task Execution ===")
    
    # Create test workspace
    workspace = Path("test_anthropic_workspace")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-20241022",
        workspace=workspace,
        verbose=True
    )
    
    # Test with a task that requires file creation
    task = """Create a Python script called 'fibonacci.py' that:
    1. Defines a function to generate Fibonacci numbers
    2. Includes both iterative and recursive implementations
    3. Has a main function that prints the first 10 Fibonacci numbers
    4. Includes docstrings and type hints"""
    
    result = await wrapper.execute_task(task)
    
    print(f"\nTask Success: {result.success}")
    print(f"Iterations: {result.iterations}")
    print(f"Files created: {result.files_created}")
    print(f"Files modified: {result.files_modified}")
    
    # Check if file was created
    fib_file = workspace / "fibonacci.py"
    if fib_file.exists():
        print(f"\n✅ File created successfully: {fib_file}")
        print(f"File size: {fib_file.stat().st_size} bytes")
    

async def test_anthropic_analysis():
    """Test Anthropic's code analysis capabilities."""
    print("\n=== Testing Anthropic Code Analysis ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-20241022",
        verbose=False
    )
    
    # Test code analysis
    code_to_analyze = '''
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
'''
    
    analysis_prompt = f"""Analyze this sorting algorithm:

{code_to_analyze}

Provide:
1. Algorithm identification
2. Time complexity (best, average, worst)
3. Space complexity
4. Pros and cons
5. One optimization suggestion"""
    
    response = await wrapper.send_message(analysis_prompt)
    print(f"\nClaude's Analysis:\n{response['content']}")


async def test_anthropic_conversation():
    """Test Anthropic multi-turn conversation."""
    print("\n=== Testing Anthropic Conversation ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.ANTHROPIC,
        api_key=os.getenv("ANTHROPIC_API_KEY"),
        model="claude-3-5-sonnet-20241022",
        verbose=False
    )
    
    # First message
    response1 = await wrapper.send_message(
        "I'm thinking of a sorting algorithm that has O(n log n) average time complexity. Can you guess which one?"
    )
    print(f"\nClaude: {response1['content']}")
    
    # Follow-up
    response2 = await wrapper.send_message(
        "Good guesses! The one I'm thinking of uses a 'divide and conquer' approach. Any more specific guess?"
    )
    print(f"\nClaude: {response2['content']}")
    
    # Final message
    response3 = await wrapper.send_message(
        "Yes, it was merge sort! Can you briefly explain how it differs from quicksort?"
    )
    print(f"\nClaude: {response3['content']}")


async def test_anthropic_models():
    """Test different Claude models."""
    print("\n=== Testing Different Claude Models ===")
    
    models_to_test = [
        "claude-3-5-sonnet-20241022",
        "claude-3-haiku-20240307",
    ]
    
    prompt = "Write a haiku about programming in Python."
    
    for model in models_to_test:
        try:
            print(f"\nTesting {model}...")
            wrapper = UnifiedAIWrapper(
                provider=AIProvider.ANTHROPIC,
                api_key=os.getenv("ANTHROPIC_API_KEY"),
                model=model,
                verbose=False
            )
            
            response = await wrapper.send_message(prompt)
            print(f"{model}:\n{response['content']}")
            
        except Exception as e:
            print(f"{model}: Failed - {e}")


async def main():
    """Run all Anthropic tests."""
    print("🚀 Nexus - Anthropic Claude Connector Test")
    print("=" * 50)
    
    # Check if API key is available
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY not found in environment")
        print("Please set your Anthropic API key to test")
        return
    
    try:
        # Test 1: Simple message
        await test_anthropic_simple()
        
        # Test 2: Task execution with file creation
        await test_anthropic_task()
        
        # Test 3: Code analysis
        await test_anthropic_analysis()
        
        # Test 4: Multi-turn conversation
        await test_anthropic_conversation()
        
        # Test 5: Different models
        await test_anthropic_models()
        
        print("\n✅ All Anthropic tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())