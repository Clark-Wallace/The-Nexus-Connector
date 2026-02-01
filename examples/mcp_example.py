"""
MCP (Model Context Protocol) Integration Example

This example shows how to use MCP servers with Nexus to give your AI agent
access to external tools like filesystem, GitHub, databases, and more.

MCP servers are a standardized way to expose tools to AI models.
Nexus integrates MCP tools seamlessly alongside custom @tool functions.
"""

import asyncio
import os
from nexus import NexusConnector, tool


# You can still define custom tools alongside MCP tools
@tool(description="Get the current timestamp")
def get_timestamp() -> str:
    """Return the current timestamp."""
    from datetime import datetime
    return datetime.now().isoformat()


async def example_1_basic_mcp():
    """Example 1: Connect to well-known MCP servers."""
    print("=" * 60)
    print("Example 1: Basic MCP Server Usage")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create connector with MCP servers
    # These are well-known server names that Nexus knows how to start
    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
        model="gpt-4o-mini",
        tools=[get_timestamp],  # Custom tools
        mcp_servers=["memory"],  # MCP servers (memory is a simple key-value store)
    )

    # List known MCP servers
    print("\nKnown MCP servers:")
    for server in connector.list_known_mcp_servers():
        print(f"  - {server}")

    # Initialize MCP servers (happens automatically on first message,
    # but we can do it explicitly)
    print("\nInitializing MCP servers...")
    results = await connector.init_mcp_servers()
    for server, success in results.items():
        status = "connected" if success else "FAILED"
        print(f"  {server}: {status}")

    # Check status
    print("\nMCP Server Status:")
    for name, info in connector.get_mcp_status().items():
        print(f"  {name}: {info['state']} ({info['tools_count']} tools)")

    # List all available tools (custom + MCP)
    print("\nAll available tools:")
    for t in connector.get_tools():
        print(f"  - {t.name}: {t.description[:50]}...")

    # Now the AI can use both custom tools and MCP tools
    print("\nSending message that might use MCP memory...")
    response = await connector.send_message(
        "Store the value 'hello world' with key 'greeting' using the memory tool, "
        "then retrieve it to confirm it was stored."
    )
    print(f"Response: {response['content']}")

    await connector.close()


async def example_2_dynamic_servers():
    """Example 2: Add/remove MCP servers dynamically."""
    print("\n" + "=" * 60)
    print("Example 2: Dynamic Server Management")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Start without MCP servers
    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
        model="gpt-4o-mini",
    )

    print("\nInitial tools:", connector.get_tool_names())

    # Add MCP server dynamically
    print("\nAdding 'time' MCP server...")
    success = await connector.add_mcp_server("time")
    if success:
        print("Server added!")
        print("New tools:", connector.get_mcp_tools())

    # Use the time tool
    response = await connector.send_message(
        "What is the current time in Tokyo, Japan?"
    )
    print(f"\nResponse: {response['content']}")

    # Remove the server
    print("\nRemoving 'time' MCP server...")
    await connector.remove_mcp_server("time")
    print("Server removed. MCP tools:", connector.get_mcp_tools())

    await connector.close()


async def example_3_custom_server():
    """Example 3: Connect to a custom MCP server."""
    print("\n" + "=" * 60)
    print("Example 3: Custom MCP Server (Conceptual)")
    print("=" * 60)

    print("""
To connect to a custom MCP server, provide the command and args:

    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
    )

    # Add custom server
    await connector.add_mcp_server("my-server", config={
        "command": "python",
        "args": ["-m", "my_custom_mcp_server"],
        "env": {
            "MY_API_KEY": "secret"
        }
    })

    # Or for an npm-based server
    await connector.add_mcp_server("custom-db", config={
        "command": "npx",
        "args": ["-y", "my-org/my-mcp-server"],
    })

The server must implement the MCP protocol (JSON-RPC over stdio).
See https://modelcontextprotocol.io/ for the specification.
""")


async def example_4_filesystem_agent():
    """Example 4: Create a file-aware agent with filesystem MCP."""
    print("\n" + "=" * 60)
    print("Example 4: Filesystem-Aware Agent")
    print("=" * 60)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Note: filesystem MCP server requires npx and the MCP package
    # Install with: npm install -g @modelcontextprotocol/server-filesystem
    print("""
This example would connect to the filesystem MCP server:

    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
        mcp_servers=["filesystem"],
    )

    # Now the AI can read/write files, list directories, etc.
    result = await connector.execute_task(
        "List all Python files in the current directory and "
        "create a summary of what each one does."
    )

Prerequisites:
  - Node.js/npm installed
  - Run: npm install -g @modelcontextprotocol/server-filesystem
""")


async def example_5_github_agent():
    """Example 5: Create a GitHub-aware agent."""
    print("\n" + "=" * 60)
    print("Example 5: GitHub-Aware Agent")
    print("=" * 60)

    print("""
To create an agent that can interact with GitHub:

    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
    )

    # Add GitHub MCP server with auth
    await connector.add_mcp_server("github", env={
        "GITHUB_PERSONAL_ACCESS_TOKEN": os.getenv("GITHUB_TOKEN")
    })

    # Now the AI can search repos, create issues, make PRs, etc.
    response = await connector.send_message(
        "Search for the top 5 trending Python repositories on GitHub"
    )

Prerequisites:
  - Node.js/npm installed
  - GitHub Personal Access Token
  - Run: npm install -g @modelcontextprotocol/server-github
""")


async def main():
    """Run all examples."""
    print("Nexus MCP Integration Examples")
    print("==============================")
    print()
    print("MCP (Model Context Protocol) lets you connect AI agents to")
    print("external tools like filesystems, databases, APIs, and more.")
    print()
    print("Well-known MCP servers that Nexus supports:")
    for server in NexusConnector.list_known_mcp_servers():
        print(f"  - {server}")
    print()

    # Run examples (some are conceptual/require external setup)
    await example_1_basic_mcp()
    await example_2_dynamic_servers()
    await example_3_custom_server()
    await example_4_filesystem_agent()
    await example_5_github_agent()

    print("\n" + "=" * 60)
    print("Examples Complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
