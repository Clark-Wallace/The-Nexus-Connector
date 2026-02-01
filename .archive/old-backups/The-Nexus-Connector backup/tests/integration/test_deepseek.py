#!/usr/bin/env python3
"""
Test script for DeepSeek connector in Nexus.
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


async def test_deepseek_simple():
    """Test DeepSeek with simple message."""
    print("\n=== Testing DeepSeek Simple Message ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model="deepseek-chat",
        verbose=True
    )
    
    response = await wrapper.send_message(
        "What is DeepSeek and what makes it good for coding tasks? Reply in 2-3 sentences."
    )
    
    print(f"\nResponse: {response['content']}")
    print(f"Tool calls: {len(response.get('tool_calls', []))}")
    

async def test_deepseek_code_generation():
    """Test DeepSeek code generation capabilities."""
    print("\n=== Testing DeepSeek Code Generation ===")
    
    # Create test workspace
    workspace = Path("test_deepseek_workspace")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model="deepseek-chat",
        workspace=workspace,
        verbose=True
    )
    
    task = """Create a Python file called 'binary_search.py' that implements:
    1. A recursive binary search function
    2. An iterative binary search function
    3. A test function that demonstrates both work correctly
    4. Proper docstrings and type hints
    
    Make the code clean, efficient, and well-documented."""
    
    result = await wrapper.execute_task(task)
    
    print(f"\nTask Result: {result}")
    print(f"Success: {result.success}")
    print(f"Files created: {result.files_created}")
    print(f"Iterations: {result.iterations}")
    print(f"Duration: {result.duration:.2f}s")
    
    # Check if file was created
    binary_file = workspace / "binary_search.py"
    if binary_file.exists():
        print(f"\n✅ File created successfully!")
        print(f"File size: {binary_file.stat().st_size} bytes")
        print(f"\nFile content preview:")
        print("-" * 50)
        content = binary_file.read_text()
        print(content[:500] + "..." if len(content) > 500 else content)
    else:
        print(f"\n❌ File was not created")


async def test_deepseek_analysis():
    """Test DeepSeek's code analysis capabilities."""
    print("\n=== Testing DeepSeek Code Analysis ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model="deepseek-chat",
        verbose=False
    )
    
    # Create a code sample to analyze
    code_sample = '''
def calculate_fibonacci(n):
    if n <= 0:
        return []
    elif n == 1:
        return [0]
    elif n == 2:
        return [0, 1]
    else:
        fib = [0, 1]
        for i in range(2, n):
            fib.append(fib[i-1] + fib[i-2])
        return fib

# Test the function
result = calculate_fibonacci(10)
print(f"First 10 Fibonacci numbers: {result}")
'''
    
    analysis_prompt = f"""Analyze this Python code and provide:
1. A brief description of what it does
2. Time and space complexity
3. One potential optimization
4. Any issues or improvements

Code:
```python
{code_sample}
```
"""
    
    response = await wrapper.send_message(analysis_prompt)
    print(f"\nDeepSeek Analysis:\n{response['content']}")


async def test_deepseek_vs_openai():
    """Compare DeepSeek and OpenAI on the same task."""
    print("\n=== Comparing DeepSeek vs OpenAI ===")
    
    prompt = "Write a Python one-liner that checks if a string is a palindrome. Be concise."
    
    # Test DeepSeek
    deepseek_wrapper = UnifiedAIWrapper(
        provider=AIProvider.DEEPSEEK,
        api_key=os.getenv("DEEPSEEK_API_KEY"),
        model="deepseek-chat",
        verbose=False
    )
    
    deepseek_response = await deepseek_wrapper.send_message(prompt)
    
    # Test OpenAI
    openai_wrapper = UnifiedAIWrapper(
        provider=AIProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o",
        verbose=False
    )
    
    openai_response = await openai_wrapper.send_message(prompt)
    
    print(f"\nPrompt: {prompt}")
    print(f"\nDeepSeek Response:\n{deepseek_response['content']}")
    print(f"\nOpenAI Response:\n{openai_response['content']}")


async def main():
    """Run all DeepSeek tests."""
    print("🚀 Nexus - DeepSeek Connector Test")
    print("=" * 50)
    
    # Check if API key is available
    if not os.getenv("DEEPSEEK_API_KEY"):
        print("❌ DEEPSEEK_API_KEY not found in environment")
        print("Please set your DeepSeek API key to test")
        return
    
    try:
        # Test 1: Simple message
        await test_deepseek_simple()
        
        # Test 2: Code generation with file creation
        await test_deepseek_code_generation()
        
        # Test 3: Code analysis
        await test_deepseek_analysis()
        
        # Test 4: Compare with OpenAI
        if os.getenv("OPENAI_API_KEY"):
            await test_deepseek_vs_openai()
        
        print("\n✅ All DeepSeek tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())