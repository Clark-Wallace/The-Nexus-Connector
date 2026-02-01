# QwenDevr - The Ultimate Qwen CLI Setup Guide

🚀 **Claude Code-inspired development assistant powered by Qwen3-235B (FREE!) via OpenRouter**

## Features

- **🎯 Claude Code-like Interface** - Familiar commands for development tasks
- **⚡ Fast & Efficient** - No thinking tokens, direct responses from Qwen3-235B
- **🆓 Completely FREE** - Qwen3-235B is free on OpenRouter with unlimited usage!
- **🚀 Most Advanced** - 235B parameters, 3x larger than previous generation
- **🛠️ Comprehensive Tools** - Project setup, code analysis, testing, docs, refactoring
- **💬 Interactive Mode** - Chat-like interface for development assistance
- **📁 Project Management** - Create and manage different project types
- **🔧 Auto-execution** - Automatically creates files and runs tasks
- **🔄 Model Switching** - Switch between Qwen models on the fly

## Quick Start

### 1. Install Dependencies

```bash
# Install QwenDevr requirements
pip install -r qwen_devr_requirements.txt

# Or install individual packages
pip install rich click typer prompt-toolkit
```

### 2. Get OpenRouter API Key

1. Go to [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Get your API key from [API Keys page](https://openrouter.ai/keys)
4. Set environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

### 3. Run QwenDevr

```bash
# Interactive mode (recommended for first use)
python qwen_devr_cli.py --interactive

# Quick commands (defaults to FREE Qwen3-235B!)
python qwen_devr_cli.py "analyze this codebase"
python qwen_devr_cli.py --setup web my_app
python qwen_devr_cli.py --file main.py "add error handling"

# Use specific models
python qwen_devr_cli.py --model qwen3-235b "create a FastAPI app"  # FREE!
python qwen_devr_cli.py --model qwen2.5-coder "optimize this code"  # Coding specialist
```

## Usage Examples

### Project Analysis
```bash
# Analyze entire project
python qwen_devr_cli.py --analyze

# Focus on specific areas
python qwen_devr_cli.py --analyze "security vulnerabilities"
python qwen_devr_cli.py --analyze "performance issues"
```

### Project Setup
```bash
# Create different project types
python qwen_devr_cli.py --setup web my_web_app
python qwen_devr_cli.py --setup api user_service
python qwen_devr_cli.py --setup cli my_tool
python qwen_devr_cli.py --setup lib my_library
```

### Code Operations
```bash
# Fix issues in files
python qwen_devr_cli.py --file app.py "add input validation"
python qwen_devr_cli.py --file utils.py "improve error handling"

# Generate tests
python qwen_devr_cli.py --test models.py
python qwen_devr_cli.py --test utils.py

# Generate documentation
python qwen_devr_cli.py --docs
python qwen_devr_cli.py --docs api
```

### Free-form Requests
```bash
# Natural language requests
python qwen_devr_cli.py "create a REST API for user management"
python qwen_devr_cli.py "add logging to all my functions"
python qwen_devr_cli.py "optimize database queries"
python qwen_devr_cli.py "set up CI/CD with GitHub Actions"
```

### Interactive Mode
```bash
# Start interactive session
python qwen_devr_cli.py --interactive

# Available commands in interactive mode:
QwenDevr> analyze security
QwenDevr> setup web my_app
QwenDevr> fix main.py performance
QwenDevr> test utils.py
QwenDevr> docs api
QwenDevr> help
QwenDevr> exit
```

## Project Types

QwenDevr can set up these project types:

- **web** - FastAPI/Flask web application with database
- **api** - REST API service with authentication
- **cli** - Command-line interface tool with Click/Typer
- **lib** - Python library/package with proper structure
- **data** - Data analysis/ML project with Jupyter setup
- **game** - Game development project structure
- **mobile** - Mobile app backend with API endpoints

## Commands Reference

| Command | Description | Example |
|---------|-------------|---------|
| `analyze [focus]` | Analyze project/codebase | `analyze security` |
| `setup <type> [name]` | Create new project | `setup web my_app` |
| `fix <file> [issues]` | Fix issues in file | `fix main.py bugs` |
| `test <file>` | Generate tests | `test utils.py` |
| `docs [scope]` | Generate docs | `docs api` |
| `refactor <file> <req>` | Refactor code | `refactor old.py SOLID` |
| `help` | Show help | `help` |
| `exit` | Exit interactive mode | `exit` |

## Configuration

### Environment Variables

```bash
# Required
export OPENROUTER_API_KEY="your-key-here"

# Optional
export QWEN_WORKSPACE="./my_workspace"  # Default: ./qwen_workspace
export QWEN_MODEL="qwen/qwen-2.5-72b-instruct"  # Default model
```

### Workspace Directory

QwenDevr creates a workspace directory for generated files:

```
qwen_workspace/
├── projects/          # Generated projects
├── analysis/          # Analysis reports
├── tests/            # Generated test files
├── docs/             # Generated documentation
└── backups/          # File backups
```

## 🎉 NEW: Why Qwen3-235B?

- **🆓 COMPLETELY FREE**: Zero cost on OpenRouter with unlimited usage!
- **🚀 Most Advanced**: 235B parameters, 3x larger than Qwen2.5-72B
- **⚡ Lightning Fast**: No thinking tokens like DeepSeek, direct responses
- **🎯 Superior Quality**: Significantly improved capabilities over previous generation
- **🔧 Perfect for Development**: Excellent for code generation, analysis, and complex tasks
- **📦 Production Ready**: Stable, consistent responses without hallucination

## Model Comparison

| Model | Parameters | Speed | Code Quality | Thinking Tokens | Cost |
|-------|------------|-------|--------------|----------------|------|
| **🆕 Qwen3-235B** | 235B | ⚡⚡⚡⚡ | 🎯🎯🎯🎯🎯 | ✅ None | 🆓 **FREE!** |
| Qwen2.5-72B | 72B | ⚡⚡⚡⚡⚡ | 🎯🎯🎯🎯 | ✅ None | 💰💰 |
| Qwen2.5-Coder | 32B | ⚡⚡⚡⚡⚡ | 🎯🎯🎯🎯 | ✅ None | 💰 |
| DeepSeek-R1 | 671B | ⚡ | 🎯🎯🎯🎯🎯 | ❌ Verbose | 💰 |
| Claude-3.5-Sonnet | ? | ⚡⚡ | 🎯🎯🎯🎯 | ✅ None | 💰💰💰 |
| GPT-4o | ? | ⚡⚡ | 🎯🎯🎯 | ✅ None | 💰💰💰 |

### Available Models in QwenDevr:

- **qwen3-235b** - Latest, most powerful, FREE! (default)
- **qwen2.5-72b** - Previous generation, very fast
- **qwen2.5-coder** - Specialized for coding tasks

Switch models anytime with: `models qwen3-235b`

## Integration with Other Tools

QwenDevr works great alongside:

- **VS Code** - Use QwenDevr to generate code, then edit in VS Code
- **Git** - QwenDevr respects Git repositories and .gitignore
- **CI/CD** - Can generate GitHub Actions, pre-commit hooks
- **Testing** - Integrates with pytest, unittest, coverage tools
- **Documentation** - Generates Sphinx, MkDocs, or simple Markdown

## Troubleshooting

### Common Issues

**API Key Error:**
```bash
❌ OPENROUTER_API_KEY environment variable is required
```
Solution: Set your OpenRouter API key as environment variable

**Model Not Found:**
```bash
❌ Model qwen/qwen-2.5-72b-instruct not found
```
Solution: Check [OpenRouter models page](https://openrouter.ai/models) for available models

**Permission Denied:**
```bash
❌ Permission denied writing to workspace
```
Solution: Create workspace directory or use `--workspace` flag

### Debug Mode

Run with Python's debug flag for detailed output:
```bash
python -v qwen_devr_cli.py --interactive
```

## Support & Contributing

- **Issues**: Report issues with the CLI functionality
- **Features**: Suggest new development tools and commands
- **Models**: Request support for other OpenRouter models
- **Integration**: Ideas for IDE and tool integrations

## License

Same as The Nexus Connector - MIT License

---

**QwenDevr - Making AI-assisted development fast, efficient, and practical! 🚀**