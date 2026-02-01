#!/usr/bin/env python3
"""
Example: Web Server Mode
Demonstrates running Nexus as a web server for applications.
"""

import os
from dotenv import load_dotenv

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus.web import WebConnector
from nexus import AIProvider


def main():
    """Run Nexus as a web server."""
    load_dotenv()
    
    # Create web connector
    connector = WebConnector(
        provider=AIProvider.OPENAI,
        api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-3.5-turbo",
        port=8000,
        cors_origins=["http://localhost:3000", "*"],  # Allow your frontend
    )
    
    print("🚀 Starting Nexus Web Server")
    print("📍 API available at: http://localhost:8000")
    print("📍 Documentation at: http://localhost:8000/docs")
    print("\nEndpoints:")
    print("  POST /chat - Send a message")
    print("  POST /chat/stream - Stream responses")
    print("  GET /sessions/{id} - Get session info")
    print("  GET /health - Health check")
    print("\nPress Ctrl+C to stop")
    
    # Run the server
    connector.run()


if __name__ == "__main__":
    main()