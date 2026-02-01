#!/usr/bin/env python3
"""
Test all 5 AI providers through Nexus unified wrapper.
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


async def test_provider(provider: AIProvider, api_key_name: str):
    """Test a single provider."""
    api_key = os.getenv(api_key_name)
    if not api_key:
        print(f"  ❌ {api_key_name} not found")
        return
    
    try:
        wrapper = UnifiedAIWrapper(
            provider=provider,
            api_key=api_key,
            verbose=False
        )
        
        # Simple test message
        response = await wrapper.send_message(
            "Complete this famous programming quote: 'Talk is cheap. Show me the...'"
        )
        
        print(f"  ✅ {provider.display_name}: {response['content']}")
        
    except Exception as e:
        print(f"  ❌ {provider.display_name}: {str(e)}")


async def main():
    """Test all providers."""
    print("🚀 Nexus - Testing All 5 AI Providers")
    print("=" * 50)
    
    providers_to_test = [
        (AIProvider.OPENAI, "OPENAI_API_KEY"),
        (AIProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (AIProvider.GOOGLE, "GOOGLE_API_KEY"),
        (AIProvider.XAI, "XAI_API_KEY"),
        (AIProvider.DEEPSEEK, "DEEPSEEK_API_KEY"),
    ]
    
    print("\nTesting all providers with the same prompt:")
    print("'Complete this famous programming quote: Talk is cheap. Show me the...'")
    print()
    
    for provider, api_key_name in providers_to_test:
        await test_provider(provider, api_key_name)
    
    print("\n✅ All tests completed!")
    print("\nNexus provides a unified interface for:")
    print("  - OpenAI GPT models")
    print("  - Anthropic Claude models")
    print("  - Google Gemini models")
    print("  - xAI Grok models")
    print("  - DeepSeek models")


if __name__ == "__main__":
    asyncio.run(main())