#!/usr/bin/env python3
"""
Nexus Web UI Launcher

Starts the Nexus WebConnector server and serves the chat demo frontend.
Auto-detects provider and API key from .env file.

Usage:
    python ui.py
"""

import os
import sys
import threading
import webbrowser
from pathlib import Path

# Load .env before anything else
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Provider detection (same logic as nexus/easy.py)
KEY_MAP = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "xai": "XAI_API_KEY",
}

PROVIDER_NAMES = {
    "anthropic": "Anthropic Claude",
    "openai": "OpenAI",
    "google": "Google Gemini",
    "deepseek": "DeepSeek",
    "xai": "xAI Grok",
    "ollama": "Ollama (Local)",
}


def detect_provider():
    """Auto-detect provider from NEXUS_DEFAULT_PROVIDER or first available API key."""
    provider = os.getenv("NEXUS_DEFAULT_PROVIDER")
    if provider and provider in KEY_MAP:
        api_key = os.getenv(KEY_MAP[provider])
        if api_key:
            return provider, api_key

    for prov, env_var in KEY_MAP.items():
        api_key = os.getenv(env_var)
        if api_key:
            return prov, api_key

    return None, None


def main():
    provider, api_key = detect_provider()

    if not provider or not api_key:
        print("\n  No API key found!\n")
        print("  Set at least one API key in .env (copy from .env.example):\n")
        for prov, env_var in KEY_MAP.items():
            print(f"    {env_var}=your-key-here    # {PROVIDER_NAMES[prov]}")
        print(f"\n  cp .env.example .env  # then edit .env\n")
        sys.exit(1)

    # Import after env is loaded
    from nexus.core.base_connector import AIProvider
    from nexus.web.web_connector import WebConnector
    from fastapi.responses import HTMLResponse

    port = int(os.getenv("NEXUS_PORT", "8000"))
    host = "127.0.0.1"

    # Disable request auth for local UI (NEXUS_API_KEY is for production deployments)
    saved_nexus_key = os.environ.pop("NEXUS_API_KEY", None)

    connector = WebConnector(
        provider=AIProvider(provider),
        api_key=api_key,
        model=os.getenv("NEXUS_DEFAULT_MODEL") or None,
        port=port,
        host=host,
    )

    # Restore env var in case other code needs it
    if saved_nexus_key:
        os.environ["NEXUS_API_KEY"] = saved_nexus_key

    # Serve the chat demo HTML at /
    html_path = Path(__file__).parent / "examples" / "nexus_chat_demo.html"
    html_content = html_path.read_text()

    @connector.app.get("/", response_class=HTMLResponse)
    async def serve_ui():
        return html_content

    # Auto-open browser after server starts
    @connector.app.on_event("startup")
    async def open_browser():
        url = f"http://localhost:{port}"
        threading.Timer(1.0, webbrowser.open, args=[url]).start()

    provider_display = PROVIDER_NAMES.get(provider, provider)
    print(f"\n  Nexus Web UI")
    print(f"  Provider:  {provider_display}")
    print(f"  Server:    http://localhost:{port}")
    print(f"  Health:    http://localhost:{port}/health")
    print(f"  API docs:  http://localhost:{port}/docs")
    print(f"\n  Press Ctrl+C to stop.\n")

    try:
        connector.run(log_level="warning")
    except KeyboardInterrupt:
        print("\n  Shutting down.\n")


if __name__ == "__main__":
    main()
