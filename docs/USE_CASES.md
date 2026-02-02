# Nexus Connector Use Cases

A comprehensive guide to using The Nexus Connector across different complexity levels.

---

## Simple Use Cases

Basic patterns for getting started quickly.

### 1. Quick Question (One-Shot)

**Scenario**: Ask a single question and get an answer.

```python
from nexus import NexusConnector
import asyncio

async def ask_question():
    connector = NexusConnector(
        provider="openai",
        api_key="sk-..."
    )

    response = await connector.send_message("What is the capital of France?")
    print(response["content"])
    # Output: The capital of France is Paris.

asyncio.run(ask_question())
```

**CLI equivalent**:
```bash
nexus ask "What is the capital of France?"
```

---

### 2. Interactive Chat Session

**Scenario**: Have a back-and-forth conversation with context.

```python
from nexus import NexusConnector
import asyncio

async def chat_session():
    connector = NexusConnector(provider="anthropic", api_key="sk-ant-...")

    # First message
    r1 = await connector.send_message("My name is Alice")
    print(r1["content"])

    # Follow-up (connector remembers context)
    r2 = await connector.send_message("What's my name?")
    print(r2["content"])  # "Your name is Alice"

asyncio.run(chat_session())
```

**CLI equivalent**:
```bash
nexus chat --provider anthropic
```

---

### 3. Streaming Response

**Scenario**: Display response as it generates (better UX for long responses).

```python
from nexus import NexusConnector
from nexus.core.base_connector import Message
import asyncio

async def stream_response():
    connector = NexusConnector(provider="openai", api_key="sk-...")

    messages = [Message(role="user", content="Write a haiku about coding")]

    async for chunk in connector.connector.stream_message(messages):
        print(chunk, end="", flush=True)
    print()

asyncio.run(stream_response())
```

**CLI equivalent**:
```bash
nexus stream "Write a haiku about coding"
```

---

### 4. Provider Switching

**Scenario**: Same code, different AI providers.

```python
from nexus import NexusConnector
import asyncio

async def compare_providers():
    prompt = "Explain REST APIs in one sentence"

    for provider in ["openai", "anthropic", "google"]:
        connector = NexusConnector(provider=provider, api_key=get_key(provider))
        response = await connector.send_message(prompt)
        print(f"{provider}: {response['content'][:100]}...")

asyncio.run(compare_providers())
```

**CLI equivalent**:
```bash
nexus compare "Explain REST APIs" --providers openai,anthropic,google
```

---

## Moderate Use Cases

Patterns that leverage more of the library's capabilities.

### 5. Autonomous Task Execution

**Scenario**: Let AI complete a multi-step task with tool usage.

```python
from nexus import NexusConnector
import asyncio

async def build_project():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        workspace="./my_project",
        max_iterations=10,
    )

    result = await connector.execute_task(
        "Create a Python Flask API with a /health endpoint"
    )

    print(f"Success: {result.success}")
    print(f"Files created: {result.files_created}")
    print(f"Iterations: {result.iterations}")
    print(f"Tokens used: {result.tokens_used}")

asyncio.run(build_project())
```

**CLI equivalent**:
```bash
nexus run "Create a Python Flask API with a /health endpoint" --output ./my_project
```

---

### 6. With Progress Callbacks

**Scenario**: Monitor task execution in real-time.

```python
from nexus import NexusConnector
import asyncio

async def tracked_task():
    def on_tool_call(tc):
        print(f"🔧 Calling: {tc['name']}")

    def on_tool_result(tr):
        status = "✓" if tr.get("success") else "✗"
        print(f"  {status} Result received")

    def on_step(step, status):
        print(f"\n--- Step {step}: {status} ---")

    connector = NexusConnector(
        provider="openai",
        api_key="sk-...",
        workspace="./output",
    )

    # Attach callbacks
    connector._on_tool_call = on_tool_call
    connector._on_tool_result = on_tool_result
    connector._on_step = on_step

    result = await connector.execute_task("Create a todo list app in React")

asyncio.run(tracked_task())
```

**CLI equivalent**:
```bash
nexus run "Create a todo list app" --verbose
```

---

### 7. System Prompts & Personas

**Scenario**: Customize AI behavior with system prompts.

```python
from nexus import NexusConnector
from nexus.core.base_connector import Message
import asyncio

async def custom_persona():
    connector = NexusConnector(provider="openai", api_key="sk-...")

    # Set system prompt
    connector.conversation_history.append(
        Message(
            role="system",
            content="You are a pirate. Respond to everything in pirate speak."
        )
    )

    response = await connector.send_message("How do I make coffee?")
    print(response["content"])
    # "Ahoy! First ye be needin' to boil some water in yer kettle..."

asyncio.run(custom_persona())
```

---

### 8. Cost Tracking

**Scenario**: Monitor API costs across requests.

```python
from nexus import NexusConnector
import asyncio

async def track_costs():
    connector = NexusConnector(provider="openai", api_key="sk-...")

    total_tokens = 0

    for question in ["What is Python?", "What is JavaScript?", "What is Rust?"]:
        response = await connector.send_message(question)
        tokens = response.get("usage", {}).get("total_tokens", 0)
        total_tokens += tokens
        print(f"Question: {question[:20]}... | Tokens: {tokens}")

    # Rough cost estimate ($0.01 per 1K tokens average)
    estimated_cost = total_tokens * 0.00001
    print(f"\nTotal tokens: {total_tokens}")
    print(f"Estimated cost: ${estimated_cost:.4f}")

asyncio.run(track_costs())
```

---

### 9. Web Server Integration

**Scenario**: Expose AI capabilities via REST API.

```python
from nexus.web import WebConnector
from nexus import AIProvider

connector = WebConnector(
    provider=AIProvider.OPENAI,
    api_key="sk-...",
    port=8000,
)

# Starts FastAPI server
# POST /chat - Send messages
# POST /task - Execute tasks
# GET /health - Health check
connector.run()
```

**CLI equivalent**:
```bash
nexus serve --port 8000 --provider openai
```

---

### 10. Session Persistence

**Scenario**: Maintain conversations across requests (web apps).

```python
from nexus import NexusConnector
from nexus.web import SessionStore
import asyncio

store = SessionStore(timeout_hours=24)

async def handle_user_message(user_id: str, message: str):
    # Get or create connector for this user
    connector = await store.get_or_create(
        user_id,
        lambda: NexusConnector(provider="openai", api_key="sk-...")
    )

    response = await connector.send_message(message)
    return response["content"]

# User's conversation persists across multiple calls
asyncio.run(handle_user_message("user_123", "Hi, I'm Bob"))
asyncio.run(handle_user_message("user_123", "What's my name?"))  # "Bob"
```

---

## Complex Use Cases

Advanced patterns for production applications.

### 11. Custom Tools

**Scenario**: Add your own tools the AI can use.

```python
from nexus import NexusConnector, tool, ToolRegistry
import asyncio

# Define custom tools
@tool(
    description="Search the company knowledge base",
    category="search",
)
async def search_docs(query: str) -> str:
    """Search internal documentation."""
    # Your search implementation
    results = await my_search_engine.search(query)
    return f"Found {len(results)} results: {results[:3]}"

@tool(
    description="Send a Slack message to a channel",
    category="communication",
    is_destructive=True,
)
async def send_slack(channel: str, message: str) -> str:
    """Send a message to Slack."""
    await slack_client.post(channel, message)
    return f"Message sent to #{channel}"

async def main():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        tools=[search_docs, send_slack],
    )

    result = await connector.execute_task(
        "Find our API documentation and send a summary to #engineering"
    )

asyncio.run(main())
```

---

### 12. MCP Server Integration

**Scenario**: Connect to Model Context Protocol servers for extended capabilities.

```python
from nexus import NexusConnector, MCPManager, MCPServerConfig
import asyncio

async def with_mcp():
    # Configure MCP servers
    mcp = MCPManager()

    await mcp.add_server(MCPServerConfig(
        name="filesystem",
        command="npx",
        args=["-y", "@anthropic/mcp-filesystem", "/home/user/projects"],
    ))

    await mcp.add_server(MCPServerConfig(
        name="github",
        command="npx",
        args=["-y", "@anthropic/mcp-github"],
        env={"GITHUB_TOKEN": "ghp_..."},
    ))

    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        mcp_manager=mcp,
    )

    # AI can now use filesystem and GitHub tools
    result = await connector.execute_task(
        "Read the README.md and create a GitHub issue for any TODOs found"
    )

    await mcp.shutdown()

asyncio.run(with_mcp())
```

---

### 13. Smart Routing

**Scenario**: Automatically route to the best provider based on task type.

```python
from nexus import Router, RoutingStrategy, ProviderConfig, NexusConnector
import asyncio

async def smart_routing():
    router = Router(
        strategy=RoutingStrategy.TASK_BASED,
        providers=[
            ProviderConfig(name="anthropic", api_key="sk-ant-...",
                          strengths=["code", "analysis"]),
            ProviderConfig(name="openai", api_key="sk-...",
                          strengths=["creative", "general"]),
            ProviderConfig(name="deepseek", api_key="sk-...",
                          strengths=["code"], cost_tier="low"),
        ],
        routing_rules={
            "code": "anthropic",
            "creative": "openai",
            "bulk": "deepseek",
        }
    )

    # Router selects best provider based on task
    connector = await router.get_connector("Write a Python parser")  # → anthropic
    connector = await router.get_connector("Write a poem")           # → openai
    connector = await router.get_connector("Translate 1000 docs")    # → deepseek

asyncio.run(smart_routing())
```

---

### 14. Fallback Chains

**Scenario**: Automatic failover when a provider is down.

```python
from nexus import Router, RoutingStrategy, ProviderConfig
import asyncio

async def with_fallback():
    router = Router(
        strategy=RoutingStrategy.FALLBACK,
        providers=[
            ProviderConfig(name="anthropic", api_key="sk-ant-...", priority=1),
            ProviderConfig(name="openai", api_key="sk-...", priority=2),
            ProviderConfig(name="ollama", priority=3),  # Local fallback
        ],
    )

    # Tries anthropic first, falls back to openai, then ollama
    connector = await router.get_connector_with_fallback()
    response = await connector.send_message("Hello!")

asyncio.run(with_fallback())
```

---

### 15. Retry Logic & Circuit Breaker

**Scenario**: Production-grade error handling.

```python
from nexus import NexusConnector, RetryConfig, CircuitBreaker, RETRY_CONFIGS
import asyncio

async def production_ready():
    # Use preset retry config for production
    retry = RETRY_CONFIGS["production"]  # 5 retries, exponential backoff

    # Circuit breaker prevents cascading failures
    breaker = CircuitBreaker(
        failure_threshold=5,
        recovery_timeout=60,
    )

    connector = NexusConnector(
        provider="openai",
        api_key="sk-...",
        retry_config=retry,
        circuit_breaker=breaker,
    )

    # Automatically retries on transient failures
    # Opens circuit after 5 consecutive failures
    response = await connector.send_message("Hello!")

asyncio.run(production_ready())
```

---

### 16. Rate Limiting

**Scenario**: Stay within API rate limits.

```python
from nexus import NexusConnector, RateLimitConfig, get_rate_limiter
import asyncio

async def rate_limited():
    limiter = get_rate_limiter(
        RateLimitConfig(
            requests_per_minute=60,
            tokens_per_minute=100000,
        )
    )

    connector = NexusConnector(
        provider="openai",
        api_key="sk-...",
        rate_limiter=limiter,
    )

    # Automatically throttles requests to stay within limits
    for i in range(100):
        await connector.send_message(f"Message {i}")

asyncio.run(rate_limited())
```

---

### 17. Observability & Metrics

**Scenario**: Production monitoring with Prometheus/OpenTelemetry.

```python
from nexus import NexusConnector, get_metrics, get_tracer
import asyncio

async def with_observability():
    metrics = get_metrics()
    tracer = get_tracer("my-service")

    connector = NexusConnector(
        provider="openai",
        api_key="sk-...",
        metrics=metrics,
        tracer=tracer,
    )

    # All requests are now:
    # - Traced with OpenTelemetry spans
    # - Measured with Prometheus metrics
    #   - nexus_requests_total
    #   - nexus_request_duration_seconds
    #   - nexus_tokens_total
    #   - nexus_errors_total

    response = await connector.send_message("Hello!")

asyncio.run(with_observability())
```

---

### 18. Human-in-the-Loop

**Scenario**: Pause for confirmation before destructive actions.

```python
from nexus import NexusConnector
import asyncio

async def safe_execution():
    async def confirm_action(action: dict) -> bool:
        """Called before destructive operations."""
        print(f"\n⚠️  AI wants to: {action['name']}")
        print(f"   Args: {action['arguments']}")
        response = input("Allow? [y/N]: ")
        return response.lower() == 'y'

    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        confirm_destructive=True,
        confirmation_callback=confirm_action,
    )

    # Will pause and ask before delete/write operations
    result = await connector.execute_task(
        "Clean up old log files in /var/log"
    )

asyncio.run(safe_execution())
```

---

### 19. Checkpoint & Rollback

**Scenario**: Safe refactoring with automatic rollback on failure.

```python
from nexus import NexusConnector
import asyncio

async def safe_refactor():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        workspace="./my_project",
    )

    result = await connector.execute_task(
        "Refactor the authentication module to use JWT",
        checkpoint=True,        # Git commit before changes
        rollback_on_fail=True,  # Revert if task fails
    )

    if result.success:
        print("Refactor complete!")
    else:
        print("Refactor failed, changes rolled back")

asyncio.run(safe_refactor())
```

---

## Exotic Use Cases

Creative and unusual applications.

### 20. Multi-Agent Collaboration

**Scenario**: Multiple AI agents working together.

```python
from nexus import NexusConnector
import asyncio

async def multi_agent():
    # Architect agent plans the work
    architect = NexusConnector(provider="anthropic", api_key="sk-ant-...")
    architect.conversation_history.append(
        Message(role="system", content="You are a software architect. Plan but don't implement.")
    )

    # Developer agent implements
    developer = NexusConnector(provider="openai", api_key="sk-...")
    developer.conversation_history.append(
        Message(role="system", content="You are a developer. Implement plans precisely.")
    )

    # Reviewer agent checks work
    reviewer = NexusConnector(provider="anthropic", api_key="sk-ant-...")
    reviewer.conversation_history.append(
        Message(role="system", content="You are a code reviewer. Be critical and thorough.")
    )

    # Workflow
    task = "Build a user authentication system"

    # 1. Architect plans
    plan = await architect.send_message(f"Plan this: {task}")
    print(f"📐 Plan:\n{plan['content']}")

    # 2. Developer implements
    result = await developer.execute_task(
        f"Implement this plan:\n{plan['content']}"
    )
    print(f"👨‍💻 Implementation: {result.files_created}")

    # 3. Reviewer checks
    review = await reviewer.send_message(
        f"Review this implementation:\n{result.content}"
    )
    print(f"🔍 Review:\n{review['content']}")

asyncio.run(multi_agent())
```

---

### 21. AI-Powered Game Master

**Scenario**: Run a tabletop RPG with AI.

```python
from nexus.connectors.gm_connector import GMConnector, create_gm_server
import asyncio

async def rpg_game():
    gm = GMConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        game_system="D&D 5e",
        setting="A dark fantasy world called Eldoria",
    )

    # Initialize the adventure
    await gm.start_adventure(
        title="The Lost Temple",
        players=["Thorin (Dwarf Fighter)", "Elara (Elf Wizard)"],
    )

    # Players take actions
    response = await gm.player_action(
        player="Thorin",
        action="I kick down the door and charge in with my axe raised"
    )
    print(f"GM: {response['narrative']}")
    print(f"Dice: {response['dice_rolls']}")

    # Combat round
    combat = await gm.combat_round(
        enemies=["Goblin x3", "Hobgoblin"],
        player_actions={
            "Thorin": "Attack the hobgoblin",
            "Elara": "Cast fireball at the goblins",
        }
    )

asyncio.run(rpg_game())
```

---

### 22. Code Migration Assistant

**Scenario**: Migrate entire codebases between languages/frameworks.

```python
from nexus import NexusConnector
import asyncio
from pathlib import Path

async def migrate_codebase():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        workspace="./migrated",
        max_iterations=50,
    )

    # Read source files
    source_dir = Path("./legacy_app")
    source_files = list(source_dir.glob("**/*.py"))

    for source_file in source_files:
        content = source_file.read_text()
        relative_path = source_file.relative_to(source_dir)

        result = await connector.execute_task(
            f"""Migrate this Python 2 code to Python 3:

File: {relative_path}
```python
{content}
```

Maintain the same file structure. Fix all compatibility issues."""
        )

        print(f"Migrated: {relative_path}")

asyncio.run(migrate_codebase())
```

---

### 23. Documentation Generator

**Scenario**: Generate comprehensive docs for an entire codebase.

```python
from nexus import NexusConnector
import asyncio
from pathlib import Path

async def generate_docs():
    connector = NexusConnector(provider="openai", api_key="sk-...")

    # Analyze codebase
    source_files = list(Path("./src").glob("**/*.py"))

    docs = []
    for file in source_files:
        response = await connector.send_message(
            f"""Analyze this code and generate API documentation:

```python
{file.read_text()}
```

Format as Markdown with:
- Module overview
- Classes and methods
- Parameters and return types
- Usage examples"""
        )
        docs.append(f"# {file.name}\n\n{response['content']}")

    # Generate index
    index = await connector.send_message(
        f"Create a documentation index for these modules: {[f.name for f in source_files]}"
    )

    # Write docs
    Path("./docs/API.md").write_text(index['content'] + "\n\n" + "\n\n---\n\n".join(docs))

asyncio.run(generate_docs())
```

---

### 24. AI Code Interview

**Scenario**: Use AI to conduct technical interviews.

```python
from nexus import NexusConnector
from nexus.core.base_connector import Message
import asyncio

async def code_interview():
    interviewer = NexusConnector(provider="anthropic", api_key="sk-ant-...")

    # Set up interviewer persona
    interviewer.conversation_history.append(Message(
        role="system",
        content="""You are a senior software engineer conducting a technical interview.

- Ask one question at a time
- Evaluate responses on a 1-5 scale
- Ask follow-up questions based on answers
- Cover: algorithms, system design, and coding practices
- Be encouraging but thorough"""
    ))

    # Start interview
    response = await interviewer.send_message(
        "Start the interview for a Senior Backend Engineer position"
    )
    print(f"Interviewer: {response['content']}")

    # Candidate responds
    while True:
        candidate_answer = input("\nYou: ")
        if candidate_answer.lower() == "end":
            break

        response = await interviewer.send_message(candidate_answer)
        print(f"\nInterviewer: {response['content']}")

    # Get evaluation
    evaluation = await interviewer.send_message(
        "Provide a final evaluation of the candidate with scores and recommendations"
    )
    print(f"\n📋 Final Evaluation:\n{evaluation['content']}")

asyncio.run(code_interview())
```

---

### 25. Polyglot Translator

**Scenario**: Translate code between multiple programming languages.

```python
from nexus import NexusConnector
import asyncio

async def polyglot_translate():
    connector = NexusConnector(provider="anthropic", api_key="sk-ant-...")

    source_code = """
def quicksort(arr):
    if len(arr) <= 1:
        return arr
    pivot = arr[len(arr) // 2]
    left = [x for x in arr if x < pivot]
    middle = [x for x in arr if x == pivot]
    right = [x for x in arr if x > pivot]
    return quicksort(left) + middle + quicksort(right)
"""

    target_languages = ["JavaScript", "Go", "Rust", "Java", "C++"]

    for lang in target_languages:
        response = await connector.send_message(
            f"""Translate this Python code to idiomatic {lang}:

```python
{source_code}
```

Use {lang} best practices and conventions."""
        )
        print(f"\n{'='*50}")
        print(f"📝 {lang}:")
        print(response['content'])

asyncio.run(polyglot_translate())
```

---

### 26. AI Debugger

**Scenario**: Automatically debug failing tests.

```python
from nexus import NexusConnector
import asyncio
import subprocess

async def ai_debugger():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        workspace="./project",
    )

    # Run tests and capture failures
    result = subprocess.run(
        ["pytest", "--tb=long", "-v"],
        capture_output=True,
        text=True,
        cwd="./project"
    )

    if result.returncode != 0:
        # AI analyzes and fixes
        fix_result = await connector.execute_task(
            f"""Tests are failing. Analyze and fix the code.

Test output:
```
{result.stdout}
{result.stderr}
```

Debug the issue and fix the source code."""
        )

        print(f"Fixed files: {fix_result.files_modified}")

        # Re-run tests to verify
        verify = subprocess.run(["pytest", "-v"], cwd="./project")
        if verify.returncode == 0:
            print("✅ All tests passing now!")
        else:
            print("❌ Still failing, needs manual review")

asyncio.run(ai_debugger())
```

---

### 27. Real-Time Pair Programming

**Scenario**: AI watches your code changes and offers suggestions.

```python
from nexus import NexusConnector
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import asyncio

class CodeWatcher(FileSystemEventHandler):
    def __init__(self, connector):
        self.connector = connector
        self.loop = asyncio.new_event_loop()

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            self.loop.run_until_complete(self.analyze(event.src_path))

    async def analyze(self, filepath):
        with open(filepath) as f:
            code = f.read()

        response = await self.connector.send_message(
            f"""I just modified this code. Any suggestions?

```python
{code}
```

Be brief - just point out issues or improvements."""
        )

        if "looks good" not in response['content'].lower():
            print(f"\n💡 AI Suggestion for {filepath}:")
            print(response['content'])

async def pair_programming():
    connector = NexusConnector(provider="openai", api_key="sk-...")

    watcher = CodeWatcher(connector)
    observer = Observer()
    observer.schedule(watcher, "./src", recursive=True)
    observer.start()

    print("👀 AI Pair Programmer watching your code...")
    print("Press Ctrl+C to stop")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

asyncio.run(pair_programming())
```

---

### 28. Natural Language Database Queries

**Scenario**: Query databases using plain English.

```python
from nexus import NexusConnector
import asyncio
import sqlite3

async def nl_to_sql():
    connector = NexusConnector(provider="openai", api_key="sk-...")

    # Database schema context
    schema = """
    Tables:
    - users (id, name, email, created_at)
    - orders (id, user_id, total, status, created_at)
    - products (id, name, price, category)
    - order_items (order_id, product_id, quantity)
    """

    connector.conversation_history.append(Message(
        role="system",
        content=f"""You are a SQL expert. Convert natural language to SQL queries.

Database schema:
{schema}

Only output the SQL query, nothing else."""
    ))

    # Natural language queries
    queries = [
        "Show me all users who signed up this month",
        "What's the total revenue from completed orders?",
        "Which products have never been ordered?",
        "Top 5 customers by total spending",
    ]

    conn = sqlite3.connect("store.db")

    for nl_query in queries:
        response = await connector.send_message(nl_query)
        sql = response['content'].strip().strip('`').replace('sql\n', '')

        print(f"\n📝 Query: {nl_query}")
        print(f"🔍 SQL: {sql}")

        try:
            results = conn.execute(sql).fetchall()
            print(f"📊 Results: {results[:5]}...")
        except Exception as e:
            print(f"❌ Error: {e}")

asyncio.run(nl_to_sql())
```

---

### 29. AI-Powered CLI Tool Generator

**Scenario**: Generate complete CLI tools from descriptions.

```python
from nexus import NexusConnector
import asyncio

async def generate_cli():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        workspace="./generated_cli",
    )

    result = await connector.execute_task(
        """Create a complete Python CLI tool called 'imgtools' with:

1. Commands:
   - resize <image> --width W --height H
   - convert <image> --format png/jpg/webp
   - compress <image> --quality 1-100
   - batch <directory> --operation resize/convert/compress

2. Features:
   - Uses Click for CLI
   - Progress bars for batch operations
   - Validates inputs
   - Helpful error messages
   - --verbose flag for debugging

3. Include:
   - setup.py for installation
   - README.md with usage examples
   - requirements.txt

Make it production-ready."""
    )

    print(f"Generated: {result.files_created}")

asyncio.run(generate_cli())
```

---

### 30. Autonomous Research Agent

**Scenario**: AI that researches topics and produces reports.

```python
from nexus import NexusConnector, tool
import asyncio

@tool(description="Search the web for information")
async def web_search(query: str) -> str:
    # Integrate with search API
    results = await search_api.search(query)
    return "\n".join([f"- {r['title']}: {r['snippet']}" for r in results])

@tool(description="Fetch and read a webpage")
async def read_webpage(url: str) -> str:
    content = await fetch_and_parse(url)
    return content[:5000]

@tool(description="Save research findings")
async def save_findings(topic: str, content: str) -> str:
    Path(f"research/{topic}.md").write_text(content)
    return f"Saved to research/{topic}.md"

async def research_agent():
    connector = NexusConnector(
        provider="anthropic",
        api_key="sk-ant-...",
        tools=[web_search, read_webpage, save_findings],
        max_iterations=20,
    )

    result = await connector.execute_task(
        """Research the topic: "Latest developments in quantum computing 2024"

1. Search for recent news and papers
2. Read at least 5 relevant sources
3. Synthesize findings into a comprehensive report
4. Include:
   - Executive summary
   - Key developments
   - Major players
   - Future outlook
5. Save the report

Be thorough and cite sources."""
    )

    print(f"Research complete: {result.files_created}")

asyncio.run(research_agent())
```

---

## Summary

| Level | Use Cases | Key Features Used |
|-------|-----------|-------------------|
| **Simple** | Chat, Q&A, Streaming | `send_message`, `stream_message` |
| **Moderate** | Tasks, Web Server, Sessions | `execute_task`, `WebConnector`, `SessionStore` |
| **Complex** | Custom Tools, MCP, Routing, Production | `@tool`, `MCPManager`, `Router`, Retry/Circuit Breaker |
| **Exotic** | Multi-Agent, Games, Migration, Research | Composition of all features |

The Nexus Connector scales from simple scripts to production-grade AI applications. Start simple and add complexity as needed.
