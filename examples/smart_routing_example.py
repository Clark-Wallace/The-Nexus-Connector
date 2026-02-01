"""
Smart Routing Example - Intelligent provider selection and fallback.

This example shows how to use Nexus's smart routing to:
- Automatically select the best provider for each task
- Route tasks by type (code → Claude, math → GPT-4, etc.)
- Handle failures with automatic fallback
- Use different routing strategies (cost, quality, latency)
"""

import asyncio
import os
from nexus import (
    NexusConnector,
    Router,
    RoutingStrategy,
    ProviderConfig,
    AIProvider,
    create_router_from_env,
)


async def example_1_auto_routing():
    """Example 1: Automatic routing from environment variables."""
    print("=" * 60)
    print("Example 1: Auto-Routing from Environment")
    print("=" * 60)

    # The simplest way - just use router="auto"
    # This reads API keys from environment variables and creates
    # a router with fallback strategy
    try:
        connector = NexusConnector(
            router="auto",  # Reads OPENAI_API_KEY, ANTHROPIC_API_KEY, etc.
        )

        print(f"Initial provider: {connector.provider.value}")
        print(f"Model: {connector.connector.model}")

        response = await connector.send_message("What is 2 + 2?")
        print(f"Response: {response['content'][:100]}...")
        print(f"Provider used: {response.get('provider', 'unknown')}")

        await connector.close()

    except ValueError as e:
        print(f"Note: {e}")
        print("Set API keys in environment to use auto-routing.")


async def example_2_task_based_routing():
    """Example 2: Route tasks by type."""
    print("\n" + "=" * 60)
    print("Example 2: Task-Based Routing")
    print("=" * 60)

    # Define routing rules: task type → provider
    # The router automatically classifies tasks and routes accordingly
    routing_rules = {
        "code": "anthropic",    # Claude is great for code
        "math": "openai",       # GPT-4 for math
        "creative": "anthropic", # Claude for creative writing
        "analysis": "anthropic", # Claude for analysis
        "general": "openai",    # GPT-4 for general queries
    }

    try:
        connector = NexusConnector(
            router="auto",
            routing_rules=routing_rules,
        )

        tasks = [
            "Write a Python function to calculate fibonacci numbers",
            "Calculate the integral of sin(x) from 0 to pi",
            "Write a haiku about artificial intelligence",
            "Analyze the pros and cons of microservices architecture",
        ]

        for task in tasks:
            print(f"\nTask: {task[:50]}...")
            response = await connector.send_message(task)
            print(f"  Provider: {response.get('provider', 'unknown')}")
            print(f"  Response: {response['content'][:80]}...")

        await connector.close()

    except ValueError as e:
        print(f"Note: {e}")


async def example_3_manual_router():
    """Example 3: Manually configure a router."""
    print("\n" + "=" * 60)
    print("Example 3: Manual Router Configuration")
    print("=" * 60)

    # Create a router with explicit provider configuration
    router = Router(
        strategy=RoutingStrategy.QUALITY,  # Select highest quality provider
        routing_rules={
            "code": "deepseek",  # DeepSeek for code (cheap + good)
        },
    )

    # Add providers manually
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    deepseek_key = os.getenv("DEEPSEEK_API_KEY")

    if openai_key:
        router.add_provider(ProviderConfig(
            provider=AIProvider.OPENAI,
            api_key=openai_key,
            model="gpt-4o-mini",
            priority=90,
            tags=["fast", "reliable"],
        ))

    if anthropic_key:
        router.add_provider(ProviderConfig(
            provider=AIProvider.ANTHROPIC,
            api_key=anthropic_key,
            model="claude-sonnet-4-20250514",
            priority=100,  # Highest priority
            tags=["quality", "code"],
        ))

    if deepseek_key:
        router.add_provider(ProviderConfig(
            provider=AIProvider.DEEPSEEK,
            api_key=deepseek_key,
            model="deepseek-chat",
            priority=80,
            tags=["cheap", "code"],
        ))

    if not router.get_available_providers():
        print("No providers configured. Set API keys in environment.")
        return

    print(f"Available providers: {[p.value for p in router.get_available_providers()]}")

    connector = NexusConnector(router=router)
    print(f"Selected provider: {connector.provider.value}")

    response = await connector.send_message("Explain recursion in one sentence.")
    print(f"Response: {response['content']}")

    await connector.close()


async def example_4_fallback():
    """Example 4: Automatic fallback on failure."""
    print("\n" + "=" * 60)
    print("Example 4: Automatic Fallback")
    print("=" * 60)

    print("""
When a provider fails, Nexus automatically tries the next one:

    connector = NexusConnector(
        router="auto",
        fallback_enabled=True,      # Enable fallback (default)
        max_fallback_attempts=3,    # Try up to 3 providers
        on_provider_switch=lambda old, new, reason: print(f"Switched: {old} → {new}")
    )

The fallback order is determined by:
1. Task-based routing rules (if configured)
2. Provider priority
3. Historical success rate

If Provider A fails:
  → Try Provider B
  → If B fails, try Provider C
  → If all fail, raise the last error
""")


async def example_5_routing_strategies():
    """Example 5: Different routing strategies."""
    print("\n" + "=" * 60)
    print("Example 5: Routing Strategies")
    print("=" * 60)

    strategies = {
        "cost": "Select the cheapest provider (DeepSeek, Ollama)",
        "quality": "Select the best provider for the task type",
        "latency": "Select the fastest provider (based on history)",
        "fallback": "Use priority order, try next on failure",
        "round_robin": "Distribute evenly across providers",
        "random": "Random selection (optionally weighted)",
        "adaptive": "Combine quality, cost, latency, and success rate",
    }

    print("\nAvailable strategies:")
    for strategy, description in strategies.items():
        print(f"  {strategy:12} - {description}")

    print("\nUsage:")
    print("""
    # Cost-optimized (cheapest provider)
    connector = NexusConnector(router="cost")

    # Quality-optimized (best for task type)
    connector = NexusConnector(router="quality")

    # Latency-optimized (fastest based on history)
    connector = NexusConnector(router="latency")

    # Adaptive (balances all factors)
    connector = NexusConnector(router="adaptive")
""")


async def example_6_monitoring():
    """Example 6: Monitor routing statistics."""
    print("\n" + "=" * 60)
    print("Example 6: Routing Statistics")
    print("=" * 60)

    try:
        connector = NexusConnector(router="auto")

        # Send a few messages
        for prompt in ["Hello!", "What is Python?", "Count to 5"]:
            await connector.send_message(prompt)

        # Get router statistics
        if connector._router:
            print("\nProvider Statistics:")
            stats = connector._router.get_stats()
            for provider, data in stats.items():
                print(f"\n  {provider}:")
                print(f"    Requests: {data['total_requests']}")
                print(f"    Success Rate: {data['success_rate']:.1%}")
                print(f"    Avg Latency: {data['avg_latency_ms']:.1f}ms")
                print(f"    Enabled: {data['enabled']}")

        await connector.close()

    except ValueError as e:
        print(f"Note: {e}")


async def example_7_provider_hooks():
    """Example 7: React to provider switches."""
    print("\n" + "=" * 60)
    print("Example 7: Provider Switch Hooks")
    print("=" * 60)

    def on_switch(old_provider, new_provider, reason):
        print(f"  ⚡ Provider switched: {old_provider.value} → {new_provider.value}")
        print(f"     Reason: {reason}")

    print("""
Track provider switches with the on_provider_switch hook:

    connector = NexusConnector(
        router="auto",
        on_provider_switch=lambda old, new, reason:
            print(f"Switched from {old.value} to {new.value}: {reason}")
    )

This fires when:
- Router selects a different provider for a task
- A provider fails and fallback kicks in
- You manually switch providers
""")


async def main():
    """Run all examples."""
    print("Nexus Smart Routing Examples")
    print("============================")
    print()
    print("Smart routing lets you:")
    print("  - Auto-select the best provider for each task")
    print("  - Route by task type (code, math, creative, etc.)")
    print("  - Handle failures with automatic fallback")
    print("  - Optimize for cost, quality, or latency")
    print()

    await example_1_auto_routing()
    await example_2_task_based_routing()
    await example_3_manual_router()
    await example_4_fallback()
    await example_5_routing_strategies()
    await example_6_monitoring()
    await example_7_provider_hooks()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
