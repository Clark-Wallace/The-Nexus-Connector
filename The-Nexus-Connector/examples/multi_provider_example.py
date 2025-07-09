#!/usr/bin/env python3
"""
Example: Multi-Provider Comparison
Compare responses from different AI providers.
"""

import asyncio
import os
import time
from pathlib import Path
import sys
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import UnifiedAIWrapper, AIProvider


async def test_provider(provider: AIProvider, api_key: str, model: str, prompt: str):
    """Test a single provider and return results."""
    try:
        wrapper = UnifiedAIWrapper(
            provider=provider,
            api_key=api_key,
            model=model,
            verbose=False
        )
        
        start_time = time.time()
        response = await wrapper.send_message(prompt)
        elapsed = time.time() - start_time
        
        return {
            "provider": provider.display_name,
            "model": model,
            "response": response["content"],
            "tokens": response.get("usage", {}).get("total_tokens", "N/A"),
            "time": f"{elapsed:.2f}s",
            "success": True
        }
    except Exception as e:
        return {
            "provider": provider.display_name,
            "model": model,
            "error": str(e),
            "success": False
        }


async def main():
    """Compare multiple providers."""
    load_dotenv()
    
    print("🤖 Multi-Provider Comparison")
    print("=" * 60)
    
    # The prompt to test
    prompt = "Write a haiku about artificial intelligence."
    print(f"\nPrompt: {prompt}")
    print("-" * 60)
    
    # Define providers to test
    providers = [
        {
            "provider": AIProvider.OPENAI,
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model": "gpt-3.5-turbo",
        },
        {
            "provider": AIProvider.ANTHROPIC,
            "api_key": os.getenv("ANTHROPIC_API_KEY"),
            "model": "claude-3-haiku-20240307",
        },
        {
            "provider": AIProvider.GOOGLE,
            "api_key": os.getenv("GOOGLE_API_KEY"),
            "model": "gemini-pro",
        },
        {
            "provider": AIProvider.OLLAMA,
            "api_key": "not-needed",
            "model": "llama2",
        },
    ]
    
    # Filter out providers without API keys
    active_providers = [
        p for p in providers 
        if p["api_key"] or p["provider"] == AIProvider.OLLAMA
    ]
    
    if not active_providers:
        print("❌ No API keys found. Please set environment variables:")
        print("   OPENAI_API_KEY")
        print("   ANTHROPIC_API_KEY")
        print("   GOOGLE_API_KEY")
        return
    
    # Test all providers concurrently
    print(f"\nTesting {len(active_providers)} providers...")
    
    tasks = [
        test_provider(
            p["provider"],
            p["api_key"],
            p["model"],
            prompt
        )
        for p in active_providers
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Display results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    for result in results:
        print(f"\n📍 {result['provider']} ({result.get('model', 'N/A')})")
        print(f"⏱️  Time: {result.get('time', 'N/A')}")
        print(f"📊 Tokens: {result.get('tokens', 'N/A')}")
        
        if result["success"]:
            print(f"📝 Response:\n{result['response']}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")
        
        print("-" * 40)
    
    # Summary
    successful = sum(1 for r in results if r["success"])
    print(f"\n✅ Success: {successful}/{len(results)} providers")
    
    # Performance comparison
    if successful > 1:
        print("\n⚡ Performance Summary:")
        sorted_results = sorted(
            [r for r in results if r["success"]],
            key=lambda x: float(x["time"].rstrip("s"))
        )
        for i, r in enumerate(sorted_results, 1):
            print(f"{i}. {r['provider']}: {r['time']}")


if __name__ == "__main__":
    asyncio.run(main())