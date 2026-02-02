# MeThinks

**AI-powered project idea and specification generator**

MeThinks helps you go from "I want to build something" to a complete, AI-ready project specification in minutes.

## The Problem

You have a vague idea. You start chatting with Claude Code or Cursor. But you spend the first 20 minutes explaining:
- What you want to build
- Your skill level
- What technologies you prefer
- What's essential vs nice-to-have
- What you explicitly DON'T want

Then you switch tools and do it all over again.

## The Solution

MeThinks has a guided conversation that captures all this context ONCE, then exports it as a specification file that any AI tool can understand.

```
You → MeThinks → CLAUDE.md → Claude Code (fully context-aware)
```

## Quick Start

```bash
# Install dependencies
pip install click rich python-dotenv openai

# Set your API key
echo "OPENAI_API_KEY=sk-..." > .env

# Run MeThinks
python -m methinks new
```

## Usage

### Guided Session (Recommended)

```bash
python -m methinks new
```

MeThinks will guide you through 6 phases:
1. **Discover** - What interests you?
2. **Explore** - Tell me more about your motivation
3. **Crystallize** - "So you want to build X?"
4. **Scope** - What's MVP vs nice-to-have?
5. **Profile** - What's your experience level?
6. **Refine** - Review and confirm

At the end, you get a complete project specification.

### Quick Mode

Already know what you want? Skip the conversation:

```bash
python -m methinks quick "A CLI tool that organizes my downloads folder by file type"
```

### Other Commands

```bash
python -m methinks list              # List saved sessions
python -m methinks show <ID>         # View a spec
python -m methinks resume <ID>       # Continue a session
python -m methinks export <ID> -f claude -o CLAUDE.md  # Export for Claude Code
python -m methinks delete <ID>       # Delete a session
```

## Export Formats

| Format | Flag | Use Case |
|--------|------|----------|
| Markdown | `--format markdown` | Human-readable spec |
| Claude | `--format claude` | Optimized for Claude Code |
| JSON | `--format json` | Programmatic use |

### Example: Export for Claude Code

```bash
python -m methinks export session_20240115 --format claude -o ~/myproject/CLAUDE.md
```

Now when you open `~/myproject/` in Claude Code, it knows:
- What you're building
- Your skill level (calibrates explanations)
- Feature priorities (MVP first)
- What NOT to do (anti-goals)

## Configuration

### API Keys

Create a `.env` file:

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Choose Provider

```bash
python -m methinks new --provider openai      # Default
python -m methinks new --provider anthropic
```

## Example Output

After a MeThinks session, you get something like:

```markdown
# CLAUDE.md

## Project Context

### What We're Building
A CLI tool that automatically organizes files in your Downloads
folder by type and date.

## Developer Context

**IMPORTANT:** Calibrate explanations to this profile:
- **Skill Level:** Intermediate
- **Familiar With:** Python
- **Wants to Learn:** File system APIs, CLI design

## Feature Priorities

### 1. MVP (Must Complete First)
1. **File sorting** - Sort by file type (.pdf, .jpg, etc.)
2. **Dry run mode** - Preview changes before applying

### 2. Version 1.0 (After MVP)
1. **Date grouping** - Group by download date
2. **Custom rules** - User-defined sorting rules

## DO NOT
- Don't add a GUI - this is CLI only
- Don't require external services or databases
```

## Sessions

Sessions are saved locally in `data/sessions/`. Each session contains:
- Full conversation history
- Extracted structured data
- The building specification

You can resume any session:

```bash
python -m methinks list
python -m methinks resume session_20240115_143022
```

## Requirements

- Python 3.8+
- `click` - CLI framework
- `rich` - Pretty terminal output
- `python-dotenv` - Load .env files
- `openai` or `anthropic` - AI provider SDK

Install all:
```bash
pip install click rich python-dotenv openai anthropic
```

## License

MIT

---

*MeThinks - Because every project deserves a proper introduction.*
