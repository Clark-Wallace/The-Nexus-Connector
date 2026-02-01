#!/usr/bin/env python3
"""
Nexus WebSocket Server - Connect ANY AI provider via WebSocket

This enhanced server supports multiple AI providers through configuration.

Usage:
    # Use default provider from .env
    python nexus_websocket_server.py
    
    # Use specific provider
    python nexus_websocket_server.py --provider anthropic --model claude-3-haiku-20240307
    
    # Use OpenRouter for multiple models
    python nexus_websocket_server.py --provider openrouter --model qwen/qwen3-coder
"""

import os
import sys
import asyncio
import argparse
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from nexus import AIProvider, UnifiedAIWrapper
from nexus.web import WebConnector

# Try to load .env file
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        load_dotenv(env_path)
        print(f"✅ Loaded configuration from {env_path}")
    else:
        print(f"ℹ️  No .env file found. Copy .env.example to .env and add your API keys.")
except ImportError:
    print("ℹ️  python-dotenv not installed. Using system environment variables.")


class NexusWebSocketServer:
    """Enhanced WebSocket server with multi-provider support"""
    
    PROVIDER_CONFIGS = {
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "default_model": "gpt-3.5-turbo",
            "name": "OpenAI"
        },
        "anthropic": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "default_model": "claude-3-haiku-20240307",
            "name": "Anthropic Claude"
        },
        "google": {
            "api_key_env": "GOOGLE_API_KEY",
            "default_model": "gemini-pro",
            "name": "Google Gemini"
        },
        "xai": {
            "api_key_env": "XAI_API_KEY",
            "default_model": "grok-1",
            "name": "xAI Grok"
        },
        "deepseek": {
            "api_key_env": "DEEPSEEK_API_KEY",
            "default_model": "deepseek-chat",
            "name": "DeepSeek"
        },
        "ollama": {
            "api_key_env": None,  # Ollama doesn't need API key
            "default_model": "llama2",
            "name": "Ollama (Local)",
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        },
        "openrouter": {
            "api_key_env": "OPENROUTER_API_KEY",
            "default_model": "qwen/qwen3-coder",
            "name": "OpenRouter",
            "base_url": "https://openrouter.ai/api/v1",
            "provider_type": "openai"  # OpenRouter uses OpenAI-compatible API
        }
    }
    
    def __init__(self, provider: str, model: Optional[str] = None):
        """Initialize server with specified provider"""
        self.provider = provider.lower()
        
        if self.provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"Unknown provider: {provider}. Available: {', '.join(self.PROVIDER_CONFIGS.keys())}")
        
        self.config = self.PROVIDER_CONFIGS[self.provider]
        self.model = model or self.config["default_model"]
        
        # Get API key
        if self.config["api_key_env"]:
            self.api_key = os.getenv(self.config["api_key_env"])
            if not self.api_key:
                raise ValueError(f"Please set {self.config['api_key_env']} in your .env file or environment")
        else:
            self.api_key = "not-needed"  # For Ollama
        
        # Get additional settings
        self.port = int(os.getenv("WEBSOCKET_PORT", "8000"))
        self.host = os.getenv("WEBSOCKET_HOST", "0.0.0.0")
        self.cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")
        self.session_timeout = int(os.getenv("SESSION_TIMEOUT_HOURS", "24"))
    
    def create_connector(self) -> WebConnector:
        """Create WebConnector for the selected provider"""
        # Handle special cases
        kwargs = {}
        
        if self.provider == "ollama":
            kwargs["base_url"] = self.config["base_url"]
        elif self.provider == "openrouter":
            # OpenRouter uses OpenAI-compatible API
            provider_enum = AIProvider.OPENAI
            kwargs["base_url"] = self.config["base_url"]
        else:
            provider_enum = AIProvider(self.provider)
        
        if self.provider == "openrouter":
            provider_enum = AIProvider.OPENAI
        else:
            provider_enum = AIProvider(self.provider)
        
        return WebConnector(
            provider=provider_enum,
            api_key=self.api_key,
            model=self.model,
            port=self.port,
            host=self.host,
            cors_origins=self.cors_origins,
            session_timeout_hours=self.session_timeout,
            **kwargs
        )
    
    def print_startup_info(self):
        """Print server startup information"""
        print("\n" + "="*60)
        print("🚀 NEXUS WEBSOCKET SERVER")
        print("="*60)
        print(f"🤖 Provider: {self.config['name']}")
        print(f"🧠 Model: {self.model}")
        print(f"🌐 Server: http://{self.host}:{self.port}")
        print(f"📡 WebSocket: ws://{self.host}:{self.port}/ws")
        print(f"💾 Session timeout: {self.session_timeout} hours")
        print("\n📍 Endpoints:")
        print(f"   Health: http://localhost:{self.port}/health")
        print(f"   Chat: http://localhost:{self.port}/chat")
        print(f"   WebSocket: ws://localhost:{self.port}/ws")
        print(f"   WS Stats: http://localhost:{self.port}/ws/stats")
        print("\n🎯 Quick Test:")
        print(f"   Open 'websocket_chat_demo.html' in your browser")
        print(f"   Or use: curl -X POST http://localhost:{self.port}/chat \\")
        print(f'            -H "Content-Type: application/json" \\')
        print(f'            -d \'{{"message": "Hello!"}}\'\n')
        print("Press Ctrl+C to stop the server.")
        print("="*60 + "\n")
    
    async def run(self):
        """Run the WebSocket server"""
        self.print_startup_info()
        
        connector = self.create_connector()
        await connector.run_async()


def list_providers():
    """List all available providers and their configuration"""
    print("\n🤖 Available AI Providers for Nexus WebSocket Server:\n")
    
    for key, config in NexusWebSocketServer.PROVIDER_CONFIGS.items():
        env_var = config.get("api_key_env", "Not required")
        is_configured = bool(os.getenv(env_var)) if env_var != "Not required" else True
        status = "✅ Configured" if is_configured else "❌ Not configured"
        
        print(f"  {key:<12} - {config['name']:<20} {status}")
        print(f"               Default model: {config['default_model']}")
        if env_var != "Not required":
            print(f"               API key env: {env_var}")
        print()
    
    # Show available models from .env
    print("\n📋 Configured Models (from .env):\n")
    for provider in ["OPENAI", "ANTHROPIC", "GOOGLE", "XAI", "DEEPSEEK", "OLLAMA", "OPENROUTER"]:
        models = os.getenv(f"{provider}_MODELS")
        if models:
            print(f"  {provider}: {models}")
    print()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Nexus WebSocket Server - Connect ANY AI provider via WebSocket",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use default provider from .env
  python nexus_websocket_server.py
  
  # Use specific provider
  python nexus_websocket_server.py --provider anthropic
  python nexus_websocket_server.py --provider openai --model gpt-4
  
  # Use OpenRouter for Qwen models
  python nexus_websocket_server.py --provider openrouter --model qwen/qwen3-coder
  
  # List all providers
  python nexus_websocket_server.py --list
        """
    )
    
    parser.add_argument(
        "--provider", "-p",
        default=os.getenv("DEFAULT_PROVIDER", "openai"),
        help="AI provider to use (default: from .env or 'openai')"
    )
    parser.add_argument(
        "--model", "-m",
        default=None,
        help="Model to use (default: provider's default model)"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List all available providers and exit"
    )
    
    args = parser.parse_args()
    
    if args.list:
        list_providers()
        return
    
    try:
        server = NexusWebSocketServer(args.provider, args.model)
        await server.run()
    except ValueError as e:
        print(f"\n❌ Error: {e}")
        print("\nRun with --list to see available providers.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped.")


if __name__ == "__main__":
    asyncio.run(main())