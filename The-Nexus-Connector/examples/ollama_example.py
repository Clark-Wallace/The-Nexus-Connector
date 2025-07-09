#!/usr/bin/env python3
"""
Example: Ollama Integration
Demonstrates using local models with Ollama.
"""

import asyncio
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import UnifiedAIWrapper, AIProvider


async def main():
    """Run examples with Ollama."""
    print("🦙 Nexus + Ollama Example")
    print("=" * 40)
    
    # Make sure Ollama is running
    print("\n⚠️  Make sure Ollama is running:")
    print("   brew install ollama")
    print("   ollama serve")
    print("   ollama pull llama2")
    print()
    
    # Create wrapper for Ollama
    wrapper = UnifiedAIWrapper(
        provider=AIProvider.OLLAMA,
        api_key="not-needed",  # Ollama doesn't need API keys
        model="llama2",
        verbose=True
    )
    
    # Example 1: Simple chat
    print("\n1️⃣ Simple Chat")
    print("-" * 20)
    response = await wrapper.send_message(
        "Explain quantum computing in one paragraph."
    )
    print(response["content"])
    
    # Example 2: Code generation (using codellama if available)
    print("\n\n2️⃣ Code Generation")
    print("-" * 20)
    
    # Try to use codellama if available
    try:
        code_wrapper = UnifiedAIWrapper(
            provider=AIProvider.OLLAMA,
            api_key="not-needed",
            model="codellama"
        )
        
        response = await code_wrapper.send_message(
            "Write a Python function to calculate fibonacci numbers."
        )
        print(response["content"])
    except Exception as e:
        print(f"CodeLlama not available: {e}")
        print("Run: ollama pull codellama")
    
    # Example 3: Streaming responses
    print("\n\n3️⃣ Streaming Response")
    print("-" * 20)
    print("Tell me a short story about AI:")
    
    async for chunk in wrapper.stream_message(
        "Tell me a very short story about a friendly AI (2 sentences)."
    ):
        print(chunk, end="", flush=True)
    print()
    
    # Show token usage (estimated)
    print(f"\n\n📊 Estimated tokens used: ~{response.get('usage', {}).get('total_tokens', 'N/A')}")
    print("\n✅ Ollama integration complete!")


if __name__ == "__main__":
    asyncio.run(main())