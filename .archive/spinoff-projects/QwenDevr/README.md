# QwenDevr - The Ultimate Qwen CLI

🚀 **Claude Code-inspired development assistant powered by Qwen3-Coder-480B via OpenRouter**

## ✨ NEW: Qwen3-Coder-480B Released Today!

The latest Qwen3-Coder is a Mixture-of-Experts (MoE) model with 480B total parameters (35B active), optimized for agentic coding tasks, function calling, and tool use!

## ✨ Features

- **🎯 Claude Code-like Interface** - Familiar commands for development tasks
- **⚡ Lightning Fast** - No thinking tokens, direct responses from Qwen3-235B  
- **💰 Cost-Effective** - Competitive pricing with OpenRouter credits
- **🚀 Most Advanced** - 235B parameters, 3x larger than previous generation
- **🛠️ Complete Toolkit** - Project setup, analysis, testing, docs, refactoring
- **💬 Interactive Mode** - Chat-like interface for development assistance
- **📁 Project Management** - Create and manage 7 different project types
- **🔄 Model Switching** - Switch between Qwen models with full awareness
- **📊 Model Status** - Always know which model you're using

## 🚀 Quick Start

### 1. Install Dependencies
```bash
# From QwenDevr directory
pip install -r qwen_devr_requirements.txt

# Or install manually
pip install rich click typer prompt-toolkit
```

### 2. Get FREE OpenRouter API Key
1. Visit: https://openrouter.ai/keys
2. Sign up and get your API key (free tier available)
3. Set your API key (choose one method):

**Option A: Use .env file (recommended):**
```bash
# .env file is already created - just update with your key
echo "OPENROUTER_API_KEY=your-key-here" > .env
```

**Option B: Environment variable:**
```bash
export OPENROUTER_API_KEY="your-key-here"
```

### 3. Run QwenDevr
```bash
# Interactive mode (recommended)
python qwen_devr_cli.py --interactive

# Quick commands (defaults to Qwen3-235B)
python qwen_devr_cli.py "analyze this codebase"
python qwen_devr_cli.py --setup web my_app
python qwen_devr_cli.py --file main.py "add error handling"

# Demo (no API key needed)
python qwen_devr_demo.py
```

## 🛠️ Available Commands

### Core Development Commands
- `analyze [focus]` - Analyze project/codebase with optional focus
- `setup <type> [name]` - Create new projects
- `fix <file> [issues]` - Fix issues in specific files
- `test <file>` - Generate comprehensive test suites
- `docs [scope]` - Generate documentation
- `refactor <file> <requirements>` - Refactor code

### Model Management
- `models` - Show available Qwen models (⭐ marks current)
- `models <key>` - Switch to different model
- `status` - Show current model and capabilities
- Available: qwen3-235b, qwen2.5-72b, qwen2.5-coder

### Project Types
Create these project types with `setup <type>`:
- **web** - FastAPI/Flask web application
- **api** - REST API service
- **cli** - Command-line interface tool
- **lib** - Python library/package
- **data** - Data analysis/ML project
- **game** - Game development project
- **mobile** - Mobile app backend

## 📊 Model Comparison

| Model | Parameters | Speed | Quality | Cost | Tools |
|-------|------------|-------|---------|------|-------|
| **🆕 Qwen3-235B** | 235B | ⚡⚡⚡⚡ | 🎯🎯🎯🎯🎯 | 💰💰 | 💬 Text-only |
| Qwen2.5-72B | 72B | ⚡⚡⚡⚡⚡ | 🎯🎯🎯🎯 | 💰💰 | 🛠️ Full tools |
| Qwen2.5-Coder | 32B | ⚡⚡⚡⚡⚡ | 🎯🎯🎯🎯 | 💰 | 🛠️ Full tools |
| DeepSeek-R1 | 671B | ⚡ | 🎯🎯🎯🎯🎯 | 💰 | 🛠️ Full tools |
| Claude-3.5 | ? | ⚡⚡ | 🎯🎯🎯🎯 | 💰💰💰 | 🛠️ Full tools |
| GPT-4o | ? | ⚡⚡ | 🎯🎯🎯 | 💰💰💰 | 🛠️ Full tools |

## 🎮 Usage Examples

### Interactive Session
```bash
$ python qwen_devr_cli.py --interactive

🚀 QwenDevr - The Ultimate Qwen CLI
Powered by Qwen3-235B (Latest, FREE!) via OpenRouter API

QwenDevr> analyze security
🔍 Analyzing project with Qwen...
✅ Project Analysis Complete

QwenDevr> setup api user_service
🛠️ Setting up api project...
✅ Project Setup Complete

QwenDevr> models
🤖 Available Qwen Models (⭐ shows current model)

QwenDevr> models qwen2.5-coder
🔄 Model Switch
✅ Model Switched Successfully!
🤖 Now using: Qwen2.5-Coder-32B
🔧 Tools: ✅ Tool support enabled

QwenDevr> status
📊 Current QwenDevr Status
Model Key: ⭐ qwen2.5-coder
Tool Support: 🛠️ Enabled

QwenDevr> fix main.py performance issues
🔧 Fixing main.py...
✅ File Fix Complete
```

### Command Line Usage
```bash
# Project analysis
python qwen_devr_cli.py --analyze "security vulnerabilities"

# Create new projects
python qwen_devr_cli.py --setup web my_web_app
python qwen_devr_cli.py --setup api user_service

# Fix and improve code
python qwen_devr_cli.py --file utils.py "add input validation"
python qwen_devr_cli.py --test models.py

# Use specific models
python qwen_devr_cli.py --model qwen3-235b "create a FastAPI app"
python qwen_devr_cli.py --model qwen2.5-coder "optimize this algorithm"

# Natural language requests
python qwen_devr_cli.py "create a Redis caching layer"
python qwen_devr_cli.py "add comprehensive logging to all functions"
```

## 📁 File Structure

```
QwenDevr/
├── qwen_devr_cli.py           # Main CLI application
├── qwen_devr_demo.py          # Interactive demo (no API key needed)
├── qwen_devr_setup.md         # Detailed setup guide
├── qwen_devr_requirements.txt # Dependencies
├── README.md                  # This file
└── qwen_workspace/            # Generated workspace (created on first run)
    ├── projects/              # Generated projects
    ├── analysis/              # Analysis reports
    ├── tests/                # Generated tests
    ├── docs/                 # Generated documentation
    └── backups/              # File backups
```

## 🎯 Model Awareness & Control

QwenDevr keeps you informed about which model you're using at all times:

### **🔍 Always Know Your Model**
- **Welcome Screen** - Shows current model prominently
- **⭐ Star Indicator** - Current model marked in models table
- **Status Command** - Detailed model information anytime
- **Tool Support Warnings** - Clear indicators for text-only vs full-tool models

### **🔄 Smart Model Switching**
```bash
# See all models with current marked
QwenDevr> models

# Switch with prominent confirmation
QwenDevr> models qwen2.5-72b
🔄 Model Switch
✅ Model Switched Successfully!
🤖 Now using: Qwen2.5-72B-Instruct
🔧 Tools: ✅ Tool support enabled

# Check status anytime
QwenDevr> status
📊 Current QwenDevr Status
Model Key: ⭐ qwen2.5-72b
Tool Support: 🛠️ Enabled
```

### **⚠️ Text-only vs Full-tool Models**
- **Qwen3-235B**: 💬 Text-only (conversations, advice, code review)
- **Qwen2.5-72B/Coder**: 🛠️ Full tools (file operations, project setup, testing)

QwenDevr automatically adjusts capabilities based on your current model.

## 🎯 Why Choose QwenDevr?

### vs DeepSeek
- ✅ **No thinking tokens** - Direct responses without verbose reasoning
- ✅ **Cost-effective** - Competitive pricing with OpenRouter
- ✅ **Faster** - No delay from thinking process

### vs Claude Code  
- ✅ **Cost-effective** - Lower API costs vs Claude's premium pricing
- ✅ **Model choice** - Switch between different Qwen models
- ✅ **Self-hosted** - Run your own development assistant

### vs GPT-4o
- ✅ **Better value** - Lower cost vs OpenAI's expensive rates
- ✅ **235B parameters** - Larger than many commercial models
- ✅ **Development focused** - Optimized for coding tasks

## 🛠️ Advanced Usage

### Environment Configuration

**Using .env file (recommended):**
```bash
# .env file in QwenDevr directory
OPENROUTER_API_KEY=your-key-here
QWEN_WORKSPACE=./my_workspace
QWEN_MODEL=qwen3-235b
```

**Using environment variables:**
```bash
export OPENROUTER_API_KEY="your-key-here"
export QWEN_WORKSPACE="./my_workspace"     # Custom workspace
export QWEN_MODEL="qwen3-235b"             # Default model
```

### Custom Model Selection
```bash
# Use coding specialist
python qwen_devr_cli.py --model qwen2.5-coder "refactor this code"

# Use latest free model (default)
python qwen_devr_cli.py --model qwen3-235b "build a web scraper"

# Use fast general model
python qwen_devr_cli.py --model qwen2.5-72b "analyze performance"
```

## 🤝 Integration with Development Workflow

QwenDevr works perfectly with:
- **VS Code** - Generate code, then edit in your IDE
- **Git** - Respects repositories and .gitignore files
- **Testing** - Integrates with pytest, coverage tools
- **CI/CD** - Generate GitHub Actions, pre-commit hooks
- **Documentation** - Creates Sphinx, MkDocs, or Markdown docs

## 🆘 Troubleshooting

### Common Issues

**API Key Error:**
```bash
❌ OPENROUTER_API_KEY environment variable is required
```
**Solution:** Get your free API key from https://openrouter.ai/keys

**Import Error:**
```bash
❌ ModuleNotFoundError: No module named 'nexus'
```
**Solution:** Install Nexus Connector first:
```bash
cd ..
pip install -e .
```

**Model Not Available:**
```bash
❌ Model qwen/qwen3-235b-a22b-07-25:free not found
```
**Solution:** Check OpenRouter for model availability or try qwen2.5-72b

### Debug Mode
```bash
# Run with verbose output
python -v qwen_devr_cli.py --interactive

# Check model status
python qwen_devr_cli.py
QwenDevr> models
```

## 📖 More Information

- **Detailed Setup:** `qwen_devr_setup.md`
- **Main Project:** ../README.md
- **Nexus Integration:** ../NEXUS_INTEGRATION_GUIDE.md
- **OpenRouter Models:** https://openrouter.ai/models

## 🎉 Get Started

Try the demo first (no API key needed):
```bash
python qwen_devr_demo.py
```

Then get your free OpenRouter API key and start building:
```bash
export OPENROUTER_API_KEY="your-key"
python qwen_devr_cli.py --interactive
```

**QwenDevr - Making AI-assisted development completely free and accessible! 🚀**