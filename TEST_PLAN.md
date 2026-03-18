# Nexus Connector — Verification & Release Test Plan

## Purpose

This document is a handoff to Claude Code. The goal is to verify that The Nexus Connector works end-to-end, fix any issues found, and prepare for a v0.2.0 GitHub release tag.

## Context

- **Repo**: `/Users/clarkwallace/2026/The-Nexus-Connector`
- **Remote**: `https://github.com/Clark-Wallace/The-Nexus-Connector`
- **Current version**: 0.2.0 (in `nexus/_version.py` and `pyproject.toml`)
- **Python**: 3.11+ available on this machine
- **No GitHub release has been tagged yet** — 43 commits on main, no tags

## Phase 1: Environment Setup

1. `cd /Users/clarkwallace/2026/The-Nexus-Connector`
2. Create a fresh venv: `python3 -m venv .venv-test && source .venv-test/bin/activate`
3. Install in dev mode: `pip install -e ".[dev]"`
4. Verify the install: `python -c "from nexus import NexusConnector; print('Import OK')"`
5. Verify CLI entry point: `nexus --help`

**Report any import errors, missing dependencies, or CLI failures before moving on.**

## Phase 2: Smoke Tests (No API Keys Required)

Run these tests to verify core components work without hitting any external API:

### 2a. Tool Registry & Executor

```python
# File: test_smoke.py
import asyncio
from nexus.core.tool_registry import ToolRegistry, tool

@tool(description="Add two numbers")
def add(a: int, b: int) -> int:
    return a + b

@tool(description="Greet someone")
def greet(name: str) -> str:
    return f"Hello, {name}!"

registry = ToolRegistry()
registry.register(add)
registry.register(greet)

# Verify registration
assert len(registry.get_all()) == 2
assert registry.get("add") is not None
assert registry.get("greet") is not None

print("✅ Tool registry works")

# Verify tool definitions export (OpenAI format)
from nexus.core.tool_executor import ToolExecutor
executor = ToolExecutor(registry=registry)
defs = executor.get_tool_definitions(format="openai")
assert len(defs) >= 2
print(f"✅ Tool definitions export: {len(defs)} tools")

# Verify built-in tools registered
builtin_names = [t.name for t in executor.registry.get_all()]
print(f"   Built-in tools: {builtin_names}")
```

Run with: `python test_smoke.py`

### 2b. Base Connector & Provider Enum

```python
# File: test_providers.py
from nexus.core.base_connector import AIProvider

# Verify all providers exist
providers = ["openai", "anthropic", "google", "xai", "deepseek", "ollama"]
for p in providers:
    provider = AIProvider(p)
    print(f"✅ {provider.display_name} ({provider.value})")

# Verify connector creation (without API call)
from nexus.core.unified_wrapper import UnifiedAIWrapper

# This should fail gracefully with a clear error about API key
try:
    wrapper = UnifiedAIWrapper(provider="anthropic", api_key="test-key-not-real")
    print(f"✅ Wrapper initialized: {wrapper.model_info}")
except Exception as e:
    print(f"❌ Wrapper init failed: {e}")
```

Run with: `python test_providers.py`

### 2c. Router & Fallback Logic

```python
# File: test_router.py
from nexus.core.router import Router, RoutingStrategy, ProviderConfig
from nexus.core.base_connector import AIProvider

# Create router with mock providers
router = Router(strategy=RoutingStrategy.FALLBACK)
router.add_provider(ProviderConfig(
    provider=AIProvider.ANTHROPIC,
    api_key="fake-key",
    priority=1
))
router.add_provider(ProviderConfig(
    provider=AIProvider.OPENAI,
    api_key="fake-key",
    priority=2
))

# Verify provider selection
selected = router.select_provider()
print(f"✅ Router selected: {selected.value}")

# Verify fallback order
fallback = router.get_fallback_order("test message")
print(f"✅ Fallback order: {[p.value for p in fallback]}")

# Record a failure and verify it adjusts
router.record_failure(AIProvider.ANTHROPIC, "test error")
selected_after = router.select_provider()
print(f"✅ After failure, selected: {selected_after.value}")
```

Run with: `python test_router.py`

### 2d. Production Hardening Components

```python
# File: test_hardening.py
from nexus.core.retry import RetryConfig, CircuitBreaker, RETRY_CONFIGS
from nexus.core.rate_limiter import get_rate_limiter
from nexus.core.metrics import get_metrics

# Verify retry configs exist
for name in ["aggressive", "standard", "conservative", "rate_limit"]:
    assert name in RETRY_CONFIGS, f"Missing retry config: {name}"
print(f"✅ Retry configs: {list(RETRY_CONFIGS.keys())}")

# Verify circuit breaker
cb = CircuitBreaker("test-provider", failure_threshold=3, timeout=10.0)
assert cb.is_closed()
print("✅ Circuit breaker initialized (closed state)")

# Verify metrics
metrics = get_metrics()
print(f"✅ Metrics system initialized")

print("\n✅ All hardening components OK")
```

Run with: `python test_hardening.py`

## Phase 3: Live API Test (Requires API Key)

Clark has an Anthropic API key. This test verifies the full end-to-end path.

**Before running**: Ensure `.env` has `ANTHROPIC_API_KEY=sk-ant-...` set.

### 3a. Simple Chat (easy.py)

```python
# File: test_live_chat.py
from nexus.easy import chat

response = chat("Say 'Nexus connection established' and nothing else.", provider="anthropic")
print(f"Response: {response}")
assert "nexus" in response.lower() or "established" in response.lower(), "Unexpected response"
print("✅ Live chat works!")
```

### 3b. Full Connector with Observable Execution

```python
# File: test_live_connector.py
import asyncio
from nexus import NexusConnector

async def main():
    connector = NexusConnector(
        provider="anthropic",
        workspace="./test_workspace",
        on_tool_call=lambda tc: print(f"  🔧 Tool call: {tc['name']}"),
        on_tool_result=lambda tr: print(f"  ✅ Tool result: {tr['name']}"),
    )

    # Test 1: Simple message
    print("--- Test: Simple message ---")
    response = await connector.send_message("What is 2 + 2? Answer with just the number.")
    print(f"Response: {response['content']}")
    print(f"Provider: {response['provider']}")
    print(f"Usage: {response['usage']}")
    assert response['content'] is not None
    print("✅ send_message works")

    # Test 2: Conversation history
    print("\n--- Test: Conversation history ---")
    await connector.send_message("My name is Clark.")
    response2 = await connector.send_message("What is my name?")
    print(f"Response: {response2['content']}")
    assert "clark" in response2['content'].lower()
    print("✅ Conversation history works")

    # Test 3: Model info
    print(f"\n--- Model Info ---")
    print(f"  {connector.model_info}")
    print("✅ model_info works")

    # Cleanup
    connector.clear_history()
    print("\n✅ All live connector tests passed!")

asyncio.run(main())
```

### 3c. Task Execution (the core value prop)

```python
# File: test_live_task.py
import asyncio
import shutil
from pathlib import Path
from nexus import NexusConnector

async def main():
    # Clean workspace
    workspace = Path("./test_task_workspace")
    if workspace.exists():
        shutil.rmtree(workspace)
    workspace.mkdir()

    connector = NexusConnector(
        provider="anthropic",
        workspace=str(workspace),
        max_iterations=5,
        on_step=lambda step, status: print(f"  Step {step}: {status}"),
        on_tool_call=lambda tc: print(f"  🔧 {tc['name']}({list(tc['arguments'].keys())})"),
    )

    result = await connector.execute_task(
        "Create a Python file called hello.py that prints 'Hello from Nexus!'",
        show_progress=True,
    )

    print(f"\n--- Task Result ---")
    print(f"  Success: {result.success}")
    print(f"  Iterations: {result.iterations}")
    print(f"  Tokens: {result.tokens_used}")
    print(f"  Cost: ${result.cost:.4f}")
    print(f"  Files created: {result.files_created}")
    print(f"  Duration: {result.duration:.2f}s")

    # Verify the file was actually created
    hello_file = workspace / "hello.py"
    if hello_file.exists():
        print(f"\n  📄 hello.py contents:")
        print(f"  {hello_file.read_text()}")
        print("✅ Task execution works — file was created!")
    else:
        print("❌ Task completed but hello.py was not found")
        print(f"   Workspace contents: {list(workspace.iterdir())}")

asyncio.run(main())
```

## Phase 4: Fix Issues

For any test that fails in Phases 2-3:

1. **Document the error** — exact traceback and which test
2. **Fix the root cause** — don't just suppress errors
3. **Re-run the failing test** to confirm the fix
4. **Note what was changed** for the commit message

Common issues to watch for:
- Import errors from circular dependencies
- Missing `get_default_model()` on base class
- `tool_executor.get_tool_definitions()` format mismatch
- Anthropic message format edge cases (tool results need preceding assistant message)
- `easy.py` async loop handling in different Python versions

## Phase 5: Tag the v0.2.0 Release

Once all tests pass:

1. **Stage and commit any fixes**:
   ```bash
   git add -A
   git commit -m "fix: pre-release verification fixes

   - Updated Anthropic default model to claude-sonnet-4-20250514
   - [list any other fixes made during testing]
   - Verified end-to-end: install, import, tool registry, router, live API, task execution"
   ```

2. **Tag the release**:
   ```bash
   git tag -a v0.2.0 -m "v0.2.0 - Web server mode, Ollama support, smart routing

   Features:
   - 6 AI providers (OpenAI, Anthropic, Google, xAI, DeepSeek, Ollama)
   - Native FastAPI web server with SSE streaming
   - Smart routing with 7 strategies and automatic fallback
   - @tool decorator plugin system
   - MCP server integration
   - Observable execution with hooks
   - Human-in-the-loop confirmation for destructive operations
   - Circuit breakers, rate limiting, Prometheus metrics
   - Game Master connector for RPG applications
   - easy.py: one-line synchronous interface (chat, build, ask, fix, review)
   - CLI: nexus chat, nexus run, nexus compare
   - MeThinks: AI-powered project specification generator (apps/methinks)"
   ```

3. **Push tag and commits**:
   ```bash
   git push origin main
   git push origin v0.2.0
   ```

4. **Verify on GitHub**: Visit https://github.com/Clark-Wallace/The-Nexus-Connector/tags and confirm the tag appears.

## Phase 6: Cleanup

1. Remove test files created during verification:
   ```bash
   rm -f test_smoke.py test_providers.py test_router.py test_hardening.py
   rm -f test_live_chat.py test_live_connector.py test_live_task.py
   rm -rf test_workspace test_task_workspace .venv-test
   ```

2. Do NOT delete `TEST_PLAN.md` — keep it in the repo as documentation of what was verified.

## Success Criteria

All of these must be true before tagging:

- [ ] `pip install -e .` completes without errors
- [ ] `from nexus import NexusConnector` works
- [ ] `nexus --help` shows CLI options
- [ ] Tool registry creates, registers, and exports tool definitions
- [ ] Provider enum has all 6 providers
- [ ] UnifiedAIWrapper initializes with a fake API key (no crash)
- [ ] Router selects providers and handles fallback
- [ ] Circuit breaker, retry configs, and metrics initialize
- [ ] `chat()` from easy.py returns a response (live API)
- [ ] `send_message()` works with conversation history (live API)
- [ ] `execute_task()` creates a file in the workspace (live API)
- [ ] v0.2.0 tag is pushed to GitHub
