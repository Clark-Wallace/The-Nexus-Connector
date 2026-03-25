# Nexus Connector — Roadmap

## Current State: v0.2.0 (Released)

**Tagged and pushed.** All 12 verification tests passing.

### What's working:
- 6 AI providers (OpenAI, Anthropic, Google, xAI, DeepSeek, Ollama)
- Python SDK with easy.py one-liners (chat, build, ask, fix, review)
- CLI (nexus chat, nexus run, nexus compare)
- Web UI with markdown rendering
- Autonomous task execution (execute_task with iterative tool loop)
- @tool decorator plugin system
- Smart routing with 7 strategies + automatic fallback
- Circuit breakers, rate limiting, Prometheus metrics
- Observable execution hooks
- Human-in-the-loop confirmation (destructive=True)
- Checkpoint/rollback via git
- MCP server integration
- Session persistence (in-memory + Redis)
- Game Master connector for RPG applications
- MeThinks app (AI-powered project spec generator)

### Bugs fixed during v0.2.0 verification:
- Anthropic tool_use content block formatting (400 errors on multi-step tasks)
- API key auto-resolution from .env
- Default model updated to claude-sonnet-4-20250514
- Token encoding mapping for Claude 4 models

---

## Immediate Next Steps (Pre-Demo)

1. ~~**Tool execution feedback in web UI**~~ ✅ Done — tool calls, results, and completion summary shown in chat
2. ~~**Provider switching in web UI**~~ ✅ Done — dropdown selector with live switching
3. ~~**Workspace isolation**~~ ✅ Done — files created in ./workspace/ not repo root
4. **Record demo** — screen record the web UI doing a real task
5. **Add demo GIF/video to README**
6. **Get one external user to clone and try it**

---

## v0.2.x (Polish)

- ~~Create GitHub Release from v0.2.0 tag with release notes~~ ✅ Tag pushed
- ~~Markdown rendering in chat~~ ✅ Done — marked.js with styled code blocks, lists, tables
- ~~README alignment audit~~ ✅ Done — all claims verified against codebase
- Fix any issues found by first external user
- Add screenshot/GIF to README header

---

## v0.3.0 — Web UI Redesign

### Layout Overhaul
- Full-width layout with sidebar/main split
- Current UI wastes screen space — chat area too narrow

### Action Ledger (Sidebar)
- Running log of all actions taken during the session
- Shows tool calls, file operations, API calls in real time
- Collapsible entries with timestamps
- Governance value prop: user sees everything the AI does

### Settings Panel
- Accessible from header/nav
- Lists all configured AI providers with status
- Shows current default provider

### AI-Guided Provider Setup
- "Add New AI" button in settings
- Opens conversational interface:
  - AI asks: "What AI provider do you want to add?"
  - User says: "TogetherAI"
  - AI looks up provider, determines env var name and base URL
  - AI writes config to .env
  - Provider appears in settings with API key field
  - "Saved to .env" confirmation
- The Nexus value prop in action: the tool uses AI to configure AI

### Dynamic Provider Architecture (AI_PROVIDER_# Pattern)
- Replace hardcoded provider list with numbered .env config:
  ```
  AI_PROVIDER_1=anthropic
  AI_PROVIDER_1_KEY=sk-ant-...
  AI_PROVIDER_1_MODEL=claude-sonnet-4-20250514

  AI_PROVIDER_2=openai-compatible
  AI_PROVIDER_2_NAME=Together AI
  AI_PROVIDER_2_KEY=...
  AI_PROVIDER_2_BASE_URL=https://api.together.xyz/v1
  AI_PROVIDER_2_MODEL=meta-llama/Llama-3-70b-chat-hf
  ```
- Any OpenAI-compatible provider works automatically (Together, Groq, Fireworks, OpenRouter, Mistral, local vLLM)
- UI provider switcher reads numbered list dynamically
- AI-guided setup just writes the next numbered block

---

## v0.4.0 — Architecture Evolution

### LiteLLM Integration (Under the Hood)
- Use LiteLLM as the provider layer instead of custom connectors
- Gets 100+ providers for free
- Nexus focuses on what's unique: governed task execution, tool system, observability
- Positioning: "LiteLLM is for calling LLMs. Nexus is for deploying AI agents."

---

## Value Proposition

**Nexus Connector: AI that you can trust with your codebase.**

Connect any AI provider. Execute multi-step tasks autonomously.
Stay in control with observable execution, human-in-the-loop confirmation,
and automatic rollback. One interface, six providers, zero surprises.

### Who it's for:
Developers and teams who want autonomous AI agents but need safety guarantees.
People using Claude Code or Cursor who want more control over what the AI does,
the ability to swap providers without rewriting, and a trust layer between
"AI suggestion" and "code changed on disk."

### The differentiator (not provider breadth — governed execution):
- confirm_destructive=True — AI asks before dangerous operations
- Observable execution hooks — see what the AI decided and why
- Circuit breakers and fallback — fails gracefully
- Checkpoint and rollback — undo if things go wrong
- Workspace isolation — AI can't touch files outside its sandbox
- Cost tracking on every call

### Competitive positioning:
- LiteLLM: 100+ providers, unified API for sending messages. No agent execution.
- LangChain: Framework for building agents. Heavy, complex, steep learning curve.
- CrewAI/AutoGPT: Multi-agent frameworks. No governance, no observability.
- Nexus: Governed agent execution with built-in safety. Simpler than LangChain, safer than AutoGPT.

---

## Design Principle

Every project Clark builds has the same DNA: separation of thinking from action,
safety boundaries before execution, rollback capability, observability, cost tracking,
human-in-the-loop confirmation. This is the design signature. Nexus Connector is
the shipped implementation of that philosophy.
