#!/usr/bin/env python3
"""
Example: Simple Message

This example demonstrates establishing a Nexus Connection to send messages
to different AI providers using the same interface.
"""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import NexusConnector, AIProvider


async def simple_message_example():
    """Send a simple message to an AI provider."""
    # Load environment variables
    load_dotenv()
    
    # Choose your provider
    provider = AIProvider.OPENAI  # Change this to test other providers
    api_key = os.getenv(f"{provider.value.upper()}_API_KEY")
    
    if not api_key:
        print(f"Please set {provider.value.upper()}_API_KEY environment variable")
        return
    
    # Establish a Nexus Connection
    connector = NexusConnector(
        provider=provider,
        api_key=api_key,
        verbose=True  # Enable logging
    )
    
    # Send a message through the Nexus Connection
    print(f"\n📤 Sending message through Nexus Connection to {provider.display_name}...")
    response = await connector.send_message(
        "Explain the concept of recursion in programming with a simple example."
    )
    
    # Display the response
    print(f"\n📥 Response from {provider.display_name}:")
    print("-" * 50)
    print(response["content"])
    print("-" * 50)
    
    # Show token usage if available
    if "usage" in response:
        usage = response["usage"]
        print(f"\n📊 Token Usage:")
        print(f"   Total tokens: {usage.get('total_tokens', 'N/A')}")


async def multi_provider_example():
    """Send the same message to multiple providers."""
    load_dotenv()
    
    # Define providers to test
    providers_to_test = [
        (AIProvider.OPENAI, "OPENAI_API_KEY"),
        (AIProvider.ANTHROPIC, "ANTHROPIC_API_KEY"),
        (AIProvider.GOOGLE, "GOOGLE_API_KEY"),
    ]
    
    prompt = "Write a haiku about artificial intelligence."
    
    print(f"\n🤖 Sending prompt to multiple providers:")
    print(f"Prompt: {prompt}")
    print("=" * 60)
    
    for provider, key_env in providers_to_test:
        api_key = os.getenv(key_env)
        if not api_key:
            print(f"\n❌ {provider.display_name}: No API key found")
            continue
        
        try:
            connector = NexusConnector(
                provider=provider,
                api_key=api_key,
                verbose=False
            )
            
            response = await connector.send_message(prompt)
            
            print(f"\n✅ {provider.display_name}:")
            print(response["content"])
            
        except Exception as e:
            print(f"\n❌ {provider.display_name}: Error - {str(e)}")


async def conversation_example():
    """Demonstrate a multi-turn conversation."""
    load_dotenv()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return
    
    connector = NexusConnector(
        provider=AIProvider.OPENAI,
        api_key=api_key,
        verbose=False
    )
    
    print("\n💬 Multi-turn Conversation Example")
    print("=" * 40)
    
    # First message through Nexus Connection
    response1 = await connector.send_message(
        "I'm thinking of a number between 1 and 100. Can you try to guess it?"
    )
    print(f"AI: {response1['content']}")
    
    # Second message through same Nexus Connection
    response2 = await connector.send_message(
        "Higher than 50."
    )
    print(f"\nYou: Higher than 50.")
    print(f"AI: {response2['content']}")
    
    # Third message through same Nexus Connection
    response3 = await connector.send_message(
        "Lower than 80. It's a prime number."
    )
    print(f"\nYou: Lower than 80. It's a prime number.")
    print(f"AI: {response3['content']}")


async def main():
    """Run all examples."""
    print("🚀 Nexus Simple Message Examples")
    print("=" * 60)
    
    # Example 1: Simple message
    print("\n1️⃣ Simple Message Example")
    await simple_message_example()
    
    # Example 2: Multiple providers
    print("\n\n2️⃣ Multi-Provider Example")
    await multi_provider_example()
    
    # Example 3: Conversation
    print("\n\n3️⃣ Conversation Example")
    await conversation_example()
    
    print("\n\n✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())