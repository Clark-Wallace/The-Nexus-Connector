# CLAUDE.md

This file provides context to Claude Code for the **MeThinks** project.

## What This Is

MeThinks is an AI-powered project idea and specification generator. It helps users who have a vague idea (or no idea) crystallize it into a concrete project with a detailed specification that downstream AI tools (like Claude Code) can understand.

**The core problem it solves:** There's a "context cliff" between ideation and execution. Users have to re-explain everything to each new AI tool. MeThinks captures all context once and exports it in AI-ready formats.

## Project Structure

```
methinks/
├── __init__.py          # Package exports
├── __main__.py          # Entry point for `python -m methinks`
├── cli.py               # Click-based CLI (main interface)
├── models.py            # Data models (ProjectSpec, UserProfile, Feature, etc.)
├── session.py           # Session management and persistence
├── conversation.py      # Guided conversation engine (6 phases)
├── generator.py         # Spec generator (markdown, claude, json formats)
├── data/                # User data (gitignored)
│   └── sessions/        # Saved session JSON files
├── prompts/             # (Future) Phase-specific prompts
├── templates/           # (Future) Customizable spec templates
└── tui/                 # (Future) Textual-based terminal UI
```

## Key Concepts

### Conversation Phases
The guided conversation follows 6 phases:
1. **Discover** - What interests you?
2. **Explore** - Tell me more, what's the motivation?
3. **Crystallize** - Propose a concrete project
4. **Scope** - Define MVP vs nice-to-have features
5. **Profile** - Understand user's skill level and preferences
6. **Refine** - Review and confirm the specification

### Output Formats
- **Markdown** - Human-readable PROJECT_SPEC.md
- **Claude** - CLAUDE.md optimized for Claude Code context
- **JSON** - Machine-readable spec for programmatic use

### Data Models
- `ProjectSpec` - Complete project specification
- `UserProfile` - Skill level, known languages, learning goals, preferences
- `Feature` - Name, description, priority (must/should/nice), rationale
- `Session` - Conversation state, messages, extracted data

## CLI Commands

```bash
methinks new              # Start guided session
methinks new -p anthropic # Use specific provider
methinks resume [ID]      # Resume previous session
methinks list             # List saved sessions
methinks show <ID>        # View a session's spec
methinks export <ID>      # Export spec to file
methinks quick "idea"     # One-liner to spec (skip guided flow)
methinks delete <ID>      # Delete a session
```

## Dependencies

**Required:**
- `click` - CLI framework
- `rich` - Terminal formatting
- `python-dotenv` - Environment variable loading

**For AI (one of):**
- `nexus-connector` - Universal AI interface (preferred)
- `openai` - Direct OpenAI API
- `anthropic` - Direct Anthropic API

## Development Notes

### Adding a New Conversation Phase
1. Create a new `ConversationPhaseHandler` subclass in `conversation.py`
2. Define `phase`, `goal`, `extraction_keys`
3. Implement `get_system_addition()`, `get_initial_prompt()`, `check_complete()`
4. Add extraction logic in `_extract_*_data()` method
5. Add to `PHASES` list in `ConversationEngine`

### Adding a New Export Format
1. Add method in `generator.py` (e.g., `generate_notion_format()`)
2. Update `generate()` to handle new format string
3. Add CLI option in `export` command

### Session Storage
Sessions are stored as JSON in `data/sessions/`. Each session contains:
- Full conversation history
- Extracted structured data
- Building ProjectSpec
- Metadata (timestamps, provider used)

## Environment Variables

Set in `.env` file:
```
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

## Running

```bash
# As module (recommended)
python -m methinks new

# If installed via pip
methinks new
```

## Future Plans

- **TUI** - Rich terminal UI with Textual (live context panel, clickable suggestions)
- **Project Scaffolding** - Generate project structure along with spec
- **Templates** - Customizable spec templates for different project types
- **Memory** - Remember user profile across sessions
