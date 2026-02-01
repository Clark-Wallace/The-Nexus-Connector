#!/usr/bin/env python3
"""
WebSocket Server Example - Real-time chat with AI through Nexus

This example shows how to run a web server with WebSocket support
for real-time AI conversations.

Usage:
    python websocket_server_example.py
    
Then open websocket_chat_demo.html in your browser.
"""

import os
import asyncio
from pathlib import Path

# Add parent directory to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.web import create_web_connector


async def main():
    """Run WebSocket-enabled Nexus server"""
    
    # Create web connector with WebSocket support
    connector = create_web_connector(
        provider="openai",  # Change to your provider
        api_key=os.getenv("OPENAI_API_KEY"),  # Set your API key
        model="gpt-3.5-turbo",  # Change to your model
        port=8000,
        cors_origins=["*"]  # Allow all origins for demo
    )
    
    print("\n🚀 Nexus WebSocket Server Starting...")
    print("📡 WebSocket endpoint: ws://localhost:8000/ws")
    print("🌐 Health check: http://localhost:8000/health")
    print("📊 WebSocket stats: http://localhost:8000/ws/stats")
    print("\n📂 Open 'websocket_chat_demo.html' in your browser to test!")
    print("\nPress Ctrl+C to stop the server.\n")
    
    # Run the server
    await connector.run_async()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped.")