#!/usr/bin/env python3
"""
Test CRUD capabilities of QwenDevr with different models
"""

import asyncio
import os
from pathlib import Path
import sys
import logging

# Suppress logging
logging.getLogger("nexus").setLevel(logging.CRITICAL)
logging.getLogger("nexus.core").setLevel(logging.CRITICAL)
logging.getLogger("nexus.core.unified_wrapper").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)
logging.getLogger("openai").setLevel(logging.CRITICAL)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import NexusConnector, AIProvider

async def test_model(model_id: str, has_tools: bool):
    """Test a model's file creation capabilities."""
    print(f"\n{'='*60}")
    print(f"Testing: {model_id}")
    print(f"Tool Support: {'✅ Yes' if has_tools else '❌ No'}")
    print('='*60)
    
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not set")
        return
    
    connector = NexusConnector(
        provider=AIProvider.OPENAI,
        api_key=api_key,
        model=model_id,
        base_url="https://openrouter.ai/api/v1",
        workspace="./test_workspace",
        auto_execute=has_tools,
        max_iterations=5,
        verbose=False
    )
    
    # Test task: Create a simple HTML file
    task = "Create a file called hello.html with a basic Hello World HTML page"
    
    print(f"\nTask: {task}")
    print("Processing...")
    
    result = await connector.execute_task(task)
    
    print(f"\n✅ Success: {result.success}")
    print(f"📁 Files Created: {result.files_created}")
    
    # Check if file actually exists
    test_file = Path("./test_workspace/hello.html")
    if test_file.exists():
        print(f"✅ File exists: {test_file}")
        print(f"📄 File size: {test_file.stat().st_size} bytes")
    else:
        print("❌ File was NOT created")
    
    # Clean up
    if test_file.exists():
        print("📄 File content:")
        print(test_file.read_text())
        # test_file.unlink()
        # print("🧹 Cleaned up test file")
        print("🗂️ File kept for inspection")

async def main():
    """Test different models."""
    print("🚀 QwenDevr CRUD Capability Test")
    
    # Test new Qwen3-Coder model
    await test_model("qwen/qwen3-coder", has_tools=True)
    
    # Test text-only model
    # await test_model("qwen/qwen3-235b-a22b-07-25", has_tools=False)
    
    # Test tool-enabled model
    # await test_model("qwen/qwen-2.5-72b-instruct", has_tools=True)

if __name__ == "__main__":
    asyncio.run(main())