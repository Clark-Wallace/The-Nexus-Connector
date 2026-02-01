"""
Custom Tools Example - Demonstrates the Nexus plugin system.

This example shows how to create custom tools using the @tool decorator
and register them with the NexusConnector.
"""

import asyncio
import os
from nexus import NexusConnector, tool


# Define custom tools using the @tool decorator
@tool(description="Search the web for information")
async def web_search(query: str, max_results: int = 5) -> str:
    """
    Search the web for information.

    Args:
        query: The search query
        max_results: Maximum number of results to return
    """
    # This is a mock implementation - in real use, you'd integrate
    # with a search API like SerpAPI, Bing, or Google Custom Search
    return f"Mock search results for '{query}' (max {max_results} results)"


@tool(description="Get the current weather for a location")
async def get_weather(location: str, units: str = "celsius") -> str:
    """
    Get current weather for a location.

    Args:
        location: City name or coordinates
        units: Temperature units (celsius or fahrenheit)
    """
    # Mock implementation
    return f"Weather in {location}: 22°{units[0].upper()}, Partly cloudy"


@tool(description="Calculate mathematical expressions", category="math")
def calculate(expression: str) -> str:
    """
    Safely evaluate a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate
    """
    # Only allow safe math operations
    allowed = set("0123456789+-*/.() ")
    if not all(c in allowed for c in expression):
        return "Error: Invalid characters in expression"

    try:
        result = eval(expression)
        return f"{expression} = {result}"
    except Exception as e:
        return f"Error: {e}"


@tool(
    description="Send a notification message",
    category="notifications",
    destructive=False
)
async def send_notification(title: str, message: str, urgency: str = "normal") -> str:
    """
    Send a notification.

    Args:
        title: Notification title
        message: Notification message
        urgency: Urgency level (low, normal, high)
    """
    # Mock implementation
    print(f"📢 [{urgency.upper()}] {title}: {message}")
    return f"Notification sent: {title}"


async def main():
    # Get API key from environment
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create connector with custom tools
    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
        model="gpt-4o",
        tools=[web_search, get_weather, calculate, send_notification],
        # Add observability hooks
        on_tool_call=lambda tc: print(f"  🔧 Calling: {tc['name']}"),
        on_tool_result=lambda tr: print(f"  ✓ Result: {tr['name']} -> {str(tr['result'])[:50]}..."),
    )

    print("=" * 60)
    print("Nexus Custom Tools Example")
    print("=" * 60)

    # Show registered tools
    print("\nRegistered tools:")
    for t in connector.get_tools():
        print(f"  - {t.name}: {t.description}")

    print("\n" + "-" * 60)

    # Example 1: Simple tool usage
    print("\n📝 Example 1: Ask about weather")
    response = await connector.send_message(
        "What's the weather like in San Francisco?"
    )
    print(f"Response: {response['content']}")

    # Example 2: Multiple tools
    print("\n📝 Example 2: Multi-tool query")
    connector.clear_history()
    response = await connector.send_message(
        "Search for 'Python tutorials' and then calculate 15 * 7 + 3"
    )
    print(f"Response: {response['content']}")

    # Example 3: Task execution with custom tools
    print("\n📝 Example 3: Task execution")
    connector.clear_history()
    result = await connector.execute_task(
        "1. Check the weather in Tokyo\n"
        "2. Calculate 100 / 4\n"
        "3. Send a notification with the results",
        show_progress=True
    )
    print(f"\nTask completed: {result.success}")
    print(f"Iterations: {result.iterations}")
    print(f"Tokens used: {result.tokens_used}")


if __name__ == "__main__":
    asyncio.run(main())
