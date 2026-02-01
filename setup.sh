#!/bin/bash
# The Nexus Connector - One-Command Setup
# Just run: ./setup.sh

set -e

echo "🚀 Setting up The Nexus Connector..."
echo ""

# Colors for pretty output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo -e "${BLUE}Checking Python...${NC}"
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"
else
    echo "❌ Python 3 not found. Please install Python 3.8 or higher."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment exists${NC}"
fi

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Activated${NC}"

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -q --upgrade pip
pip install -q -e .
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo -e "${BLUE}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env from .env.example${NC}"
    echo -e "${YELLOW}⚠️  Edit .env and add your API keys!${NC}"
else
    echo -e "${GREEN}✓ .env file exists${NC}"
fi

# Create workspace directory
if [ ! -d "workspace" ]; then
    mkdir -p workspace
    echo -e "${GREEN}✓ Created workspace directory${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Next steps:"
echo ""
echo "  1. Add your API keys to .env:"
echo -e "     ${BLUE}nano .env${NC}  (or open in your editor)"
echo ""
echo "  2. Activate the environment:"
echo -e "     ${BLUE}source venv/bin/activate${NC}"
echo ""
echo "  3. Start chatting:"
echo -e "     ${BLUE}nexus chat${NC}"
echo ""
echo "  Or run a task:"
echo -e "     ${BLUE}nexus run \"Create a hello world Flask app\"${NC}"
echo ""
echo "  Or use in Python:"
echo -e "     ${BLUE}python examples/simple_message.py${NC}"
echo ""
echo -e "${GREEN}Happy building! 🎉${NC}"
