#!/usr/bin/env python3
"""
Test script for Google Gemini connector in Nexus.
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


async def test_gemini_simple():
    """Test Gemini with simple message."""
    print("\n=== Testing Gemini Simple Message ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.GOOGLE,
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash",
        verbose=True
    )
    
    response = await wrapper.send_message(
        "What is Google Gemini and what are its key strengths? Reply in 2-3 sentences."
    )
    
    print(f"\nResponse: {response['content']}")
    print(f"Tool calls: {len(response.get('tool_calls', []))}")
    

async def test_gemini_code_generation():
    """Test Gemini code generation capabilities."""
    print("\n=== Testing Gemini Code Generation ===")
    
    # Create test workspace
    workspace = Path("test_gemini_workspace")
    workspace.mkdir(exist_ok=True)
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.GOOGLE,
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash",
        workspace=workspace,
        verbose=True
    )
    
    # Since Gemini doesn't support tools in the same way, 
    # we'll ask it to provide the code and then save it manually
    task = """Generate Python code for a simple web scraper that:
    1. Takes a URL as input
    2. Fetches the page content
    3. Extracts all links from the page
    4. Saves the links to a CSV file
    
    Include error handling and proper documentation.
    Format the response as a complete Python script."""
    
    response = await wrapper.send_message(task)
    
    print(f"\nGemini Response (first 500 chars):")
    print(response['content'][:500] + "..." if len(response['content']) > 500 else response['content'])
    
    # Extract code from response and save it
    if "```python" in response['content']:
        # Extract code between ```python and ```
        code_start = response['content'].find("```python") + 9
        code_end = response['content'].find("```", code_start)
        if code_end > code_start:
            code = response['content'][code_start:code_end].strip()
            
            # Save the code
            scraper_file = workspace / "web_scraper.py"
            scraper_file.write_text(code)
            print(f"\n✅ Extracted and saved code to {scraper_file}")
            print(f"File size: {scraper_file.stat().st_size} bytes")
    

async def test_gemini_analysis():
    """Test Gemini's analysis capabilities."""
    print("\n=== Testing Gemini Analysis ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.GOOGLE,
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash",
        verbose=False
    )
    
    analysis_prompt = """Analyze the following sorting algorithm and explain:
1. What sorting algorithm is this?
2. Time complexity (best, average, worst case)
3. Space complexity
4. When to use this algorithm

def mystery_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i+1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr
"""
    
    response = await wrapper.send_message(analysis_prompt)
    print(f"\nGemini Analysis:\n{response['content']}")


async def test_gemini_creative():
    """Test Gemini's creative capabilities."""
    print("\n=== Testing Gemini Creative Writing ===")
    
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.GOOGLE,
        api_key=os.getenv("GOOGLE_API_KEY"),
        model="gemini-2.0-flash",
        verbose=False
    )
    
    creative_prompt = """Write a short story (100-150 words) about a programmer who discovers their code is writing itself. Make it mysterious and thought-provoking."""
    
    response = await wrapper.send_message(creative_prompt)
    print(f"\nGemini Creative Response:\n{response['content']}")


async def test_gemini_models():
    """Test different Gemini models."""
    print("\n=== Testing Different Gemini Models ===")
    
    models_to_test = [
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]
    
    prompt = "Explain quantum computing in one sentence for a 10-year-old."
    
    for model in models_to_test:
        try:
            print(f"\nTesting {model}...")
            wrapper = UnifiedAIWrapper(
                provider=AIProvider.GOOGLE,
                api_key=os.getenv("GOOGLE_API_KEY"),
                model=model,
                verbose=False
            )
            
            response = await wrapper.send_message(prompt)
            print(f"{model}: {response['content']}")
            
        except Exception as e:
            print(f"{model}: Failed - {e}")


async def main():
    """Run all Gemini tests."""
    print("🚀 Nexus - Google Gemini Connector Test")
    print("=" * 50)
    
    # Check if API key is available
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ GOOGLE_API_KEY not found in environment")
        print("Please set your Google API key to test")
        return
    
    try:
        # Test 1: Simple message
        await test_gemini_simple()
        
        # Test 2: Code generation
        await test_gemini_code_generation()
        
        # Test 3: Code analysis
        await test_gemini_analysis()
        
        # Test 4: Creative writing
        await test_gemini_creative()
        
        # Test 5: Different models
        await test_gemini_models()
        
        print("\n✅ All Gemini tests completed!")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())