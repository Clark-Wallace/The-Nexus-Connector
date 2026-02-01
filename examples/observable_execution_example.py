"""
Observable Execution Example - Demonstrates hooks, logging, and human-in-the-loop.

This example shows how to:
- Use execution hooks for full visibility
- Enable human-in-the-loop confirmation
- Use the execution log for detailed tracking
- Enable checkpoint/rollback for safe operations
"""

import asyncio
import os
from pathlib import Path
from nexus import NexusConnector
from nexus.core.execution_log import ExecutionLog


def on_message(msg):
    """Called for each message sent/received."""
    role = msg.role if hasattr(msg, 'role') else 'unknown'
    content = msg.content[:50] if hasattr(msg, 'content') else str(msg)[:50]
    print(f"  📨 [{role}] {content}...")


def on_tool_call(tool_info):
    """Called before each tool execution."""
    name = tool_info.get('name', 'unknown')
    args = tool_info.get('arguments', {})
    print(f"  🔧 Tool call: {name}")
    for k, v in args.items():
        v_str = str(v)[:30] + "..." if len(str(v)) > 30 else str(v)
        print(f"      {k}: {v_str}")


def on_tool_result(result_info):
    """Called after each tool execution."""
    name = result_info.get('name', 'unknown')
    result = result_info.get('result', {})
    success = result.get('success', False)
    status = "✓" if success else "✗"
    print(f"  {status} {name} completed")


def on_step(step: int, status: str):
    """Called at each iteration step."""
    print(f"\n📍 Step {step}: {status}")


def on_error(error: Exception):
    """Called when an error occurs."""
    print(f"  ❌ Error: {error}")


def confirm_callback(tool_metadata):
    """
    Callback for human-in-the-loop confirmation.

    Return True to proceed, False to cancel.
    """
    print(f"\n⚠️  Confirmation required for: {tool_metadata.name}")
    print(f"    Description: {tool_metadata.description}")
    if tool_metadata.is_destructive:
        print("    ⚠️  This is a DESTRUCTIVE operation")

    response = input("    Proceed? [y/N]: ").strip().lower()
    return response == 'y'


async def main():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set OPENAI_API_KEY environment variable")
        return

    # Create a temporary workspace
    workspace = Path("./nexus_example_workspace")
    workspace.mkdir(exist_ok=True)

    print("=" * 60)
    print("Nexus Observable Execution Example")
    print("=" * 60)

    # Create connector with all observability hooks
    connector = NexusConnector(
        provider="openai",
        api_key=api_key,
        model="gpt-4o-mini",
        workspace=workspace,
        max_iterations=5,
        safe_mode=True,
        verbose=True,
        # Observability hooks
        on_message=on_message,
        on_tool_call=on_tool_call,
        on_tool_result=on_tool_result,
        on_step=on_step,
        on_error=on_error,
    )

    print(f"\nWorkspace: {workspace.absolute()}")
    print(f"Provider: {connector.provider.display_name}")
    print(f"Model: {connector.connector.model}")

    # Example 1: Basic observable execution
    print("\n" + "-" * 60)
    print("Example 1: Observable Task Execution")
    print("-" * 60)

    result = await connector.execute_task(
        "Create a Python file called 'hello.py' that prints 'Hello from Nexus!'",
        show_progress=True,
        log_path=str(workspace / "execution_log.json"),
    )

    print(f"\n📊 Task Result:")
    print(f"   Success: {result.success}")
    print(f"   Iterations: {result.iterations}")
    print(f"   Duration: {result.duration:.2f}s")
    print(f"   Tokens: {result.tokens_used}")
    print(f"   Files created: {result.files_created}")

    # Show execution log summary
    if result.execution_log:
        metrics = result.execution_log.get_metrics()
        print(f"\n📋 Execution Log Summary:")
        print(f"   Total messages: {metrics.total_messages}")
        print(f"   Total tool calls: {metrics.total_tool_calls}")
        print(f"   Steps completed: {metrics.steps_completed}")
        if metrics.errors:
            print(f"   Errors: {metrics.errors}")

    # Example 2: Human-in-the-loop (simulated)
    print("\n" + "-" * 60)
    print("Example 2: Human-in-the-Loop (with confirmation)")
    print("-" * 60)
    print("(This would pause before destructive operations)")

    connector.clear_history()

    # Note: In real usage, you'd pass confirm_callback to execute_task
    # For this example, we'll just show the pattern
    print("""
To enable human-in-the-loop confirmation:

    result = await connector.execute_task(
        "Delete all .tmp files",
        confirm_destructive=True,  # Pause before delete/rm
        confirm_callback=my_callback,
    )

Or for all tool calls:

    result = await connector.execute_task(
        "Refactor the auth module",
        confirm_all=True,  # Pause before EVERY tool call
    )
""")

    # Example 3: Checkpoint and rollback
    print("\n" + "-" * 60)
    print("Example 3: Checkpoint/Rollback Pattern")
    print("-" * 60)
    print("""
For safe operations that can be rolled back:

    result = await connector.execute_task(
        "Refactor the authentication module",
        checkpoint=True,        # Git commit before changes
        rollback_on_fail=True,  # Revert if task fails
    )

This creates a git checkpoint before making changes,
and automatically rolls back if the task fails.
""")

    # Clean up
    print("\n" + "-" * 60)
    print("Cleanup")
    print("-" * 60)

    # Check if hello.py was created
    hello_file = workspace / "hello.py"
    if hello_file.exists():
        print(f"✓ Created file: {hello_file}")
        print(f"  Content: {hello_file.read_text()[:100]}...")

    # Show saved log
    log_file = workspace / "execution_log.json"
    if log_file.exists():
        print(f"✓ Execution log saved: {log_file}")

    print("\n✅ Example complete!")


if __name__ == "__main__":
    asyncio.run(main())
