#!/bin/bash
# QwenDevr Setup Script
# Installs dependencies and sets up QwenDevr for use

echo "🚀 Setting up QwenDevr - The Ultimate Qwen CLI"
echo "=============================================="

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    echo "Please install Python 3.8+ and try again."
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Install Nexus Connector first
echo ""
echo "📦 Installing Nexus Connector..."
cd ..
pip install -e . || {
    echo "❌ Failed to install Nexus Connector"
    exit 1
}

# Go back to QwenDevr directory
cd QwenDevr

# Install QwenDevr dependencies
echo ""
echo "📦 Installing QwenDevr dependencies..."
pip install -r qwen_devr_requirements.txt || {
    echo "❌ Failed to install QwenDevr dependencies"
    exit 1
}

echo ""
echo "✅ Installation complete!"
echo ""
echo "🔑 Next steps:"
echo "1. Get your FREE OpenRouter API key: https://openrouter.ai/keys"
echo "2. Set your API key: export OPENROUTER_API_KEY='your-key-here'"
echo "3. Run QwenDevr: python qwen_devr_cli.py --interactive"
echo "4. Or try the demo: python qwen_devr_demo.py"
echo ""
echo "🎉 QwenDevr is ready to use with FREE Qwen3-235B!"
echo "Happy coding! 🚀"