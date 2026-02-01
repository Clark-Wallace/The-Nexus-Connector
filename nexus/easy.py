"""
Nexus Easy Mode - For when you just want it to work.

No async/await, no configuration headaches. Just vibes.

Usage:
    from nexus.easy import chat, build, ask

    # Chat with AI
    response = chat("What's the best way to learn Python?")

    # Build something
    result = build("Create a Flask API with user login")

    # Quick question
    answer = ask("What does this error mean?", context=error_message)
"""

import asyncio
import os
from typing import Optional, List, Any, Dict
from functools import wraps

# Try to load .env file automatically
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def _get_connector(provider: Optional[str] = None, **kwargs):
    """Get a connector with sensible defaults."""
    from nexus import NexusConnector

    # Auto-detect provider from environment
    if provider is None:
        provider = os.getenv("NEXUS_DEFAULT_PROVIDER")
        if not provider:
            # Try to find an available API key
            if os.getenv("ANTHROPIC_API_KEY"):
                provider = "anthropic"
            elif os.getenv("OPENAI_API_KEY"):
                provider = "openai"
            elif os.getenv("GOOGLE_API_KEY"):
                provider = "google"
            elif os.getenv("DEEPSEEK_API_KEY"):
                provider = "deepseek"
            elif os.getenv("XAI_API_KEY"):
                provider = "xai"
            else:
                provider = "ollama"  # Fallback to local

    # Get API key for provider
    api_key = kwargs.pop("api_key", None)
    if not api_key:
        key_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GOOGLE_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "xai": "XAI_API_KEY",
        }
        if provider in key_map:
            api_key = os.getenv(key_map[provider])

    # Set workspace
    workspace = kwargs.pop("workspace", None)
    if not workspace:
        workspace = os.getenv("NEXUS_WORKSPACE", "./workspace")

    return NexusConnector(
        provider=provider,
        api_key=api_key,
        workspace=workspace,
        **kwargs
    )


def _run_async(coro):
    """Run async code synchronously."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're in an async context, create new loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def chat(message: str, provider: Optional[str] = None, **kwargs) -> str:
    """
    Chat with an AI. Returns the response as a string.

    Examples:
        >>> response = chat("Explain Python decorators")
        >>> print(response)

        >>> response = chat("Write a haiku", provider="anthropic")
    """
    connector = _get_connector(provider, **kwargs)

    async def _chat():
        response = await connector.send_message(message)
        return response.get("content", "")

    return _run_async(_chat())


def ask(question: str, context: Optional[str] = None, provider: Optional[str] = None, **kwargs) -> str:
    """
    Ask a quick question, optionally with context.

    Examples:
        >>> answer = ask("What does this error mean?", context=error_text)

        >>> answer = ask("How do I parse JSON in Python?")
    """
    if context:
        message = f"{question}\n\nContext:\n{context}"
    else:
        message = question

    return chat(message, provider=provider, **kwargs)


def build(task: str, provider: Optional[str] = None, show_progress: bool = True, **kwargs) -> Dict[str, Any]:
    """
    Build something. The AI will create files and execute the task.

    Returns a dict with:
        - success: bool
        - files_created: list of files made
        - files_modified: list of files changed
        - content: AI's final response
        - cost: estimated cost in USD

    Examples:
        >>> result = build("Create a Flask API with CRUD endpoints for users")
        >>> print(f"Created: {result['files_created']}")

        >>> result = build("Write tests for app.py")
        >>> if result['success']:
        ...     print("Tests created!")
    """
    connector = _get_connector(provider, **kwargs)

    async def _build():
        result = await connector.execute_task(task, show_progress=show_progress)
        return {
            "success": result.success,
            "files_created": result.files_created,
            "files_modified": result.files_modified,
            "content": result.content,
            "iterations": result.iterations,
            "tokens_used": result.tokens_used,
            "cost": getattr(result, "cost", 0.0),
        }

    return _run_async(_build())


def explain(code: str, provider: Optional[str] = None, **kwargs) -> str:
    """
    Explain what code does.

    Examples:
        >>> explanation = explain('''
        ...     def fib(n):
        ...         return n if n < 2 else fib(n-1) + fib(n-2)
        ... ''')
    """
    return chat(f"Explain this code:\n\n```\n{code}\n```", provider=provider, **kwargs)


def fix(code: str, error: Optional[str] = None, provider: Optional[str] = None, **kwargs) -> str:
    """
    Fix buggy code.

    Examples:
        >>> fixed = fix(my_broken_code, error=traceback_text)
        >>> print(fixed)
    """
    if error:
        message = f"Fix this code. Error: {error}\n\n```\n{code}\n```"
    else:
        message = f"Fix any bugs in this code:\n\n```\n{code}\n```"

    return chat(message, provider=provider, **kwargs)


def improve(code: str, provider: Optional[str] = None, **kwargs) -> str:
    """
    Improve code quality, readability, and performance.

    Examples:
        >>> better = improve(my_messy_code)
    """
    return chat(
        f"Improve this code. Make it cleaner, more readable, and more efficient. "
        f"Return only the improved code:\n\n```\n{code}\n```",
        provider=provider,
        **kwargs
    )


def review(code: str, provider: Optional[str] = None, **kwargs) -> str:
    """
    Get a code review.

    Examples:
        >>> feedback = review(my_code)
        >>> print(feedback)
    """
    return chat(
        f"Review this code. Point out bugs, security issues, and areas for improvement:\n\n```\n{code}\n```",
        provider=provider,
        **kwargs
    )


# Convenience aliases
send = chat
create = build
make = build
run = build
generate = build


# Quick test when run directly
if __name__ == "__main__":
    print("Testing Nexus Easy Mode...")
    print()

    # Test chat
    response = chat("Say 'Hello from Nexus!' and nothing else.")
    print(f"Chat test: {response}")
    print()

    print("Easy mode is working! Try:")
    print("  from nexus.easy import chat, build, ask")
    print("  chat('Hello!')")
