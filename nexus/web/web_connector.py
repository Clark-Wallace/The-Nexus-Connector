"""
WebConnector - Web-enabled Nexus Connector for establishing Nexus Connections via HTTP
"""

import asyncio
import json
import os
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
from datetime import datetime
import uuid

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from pydantic import BaseModel

from ..core.unified_wrapper import UnifiedAIWrapper
from ..core.base_connector import AIProvider, Message
from .session_store import SessionStore
from .websocket_manager import WebSocketManager


class WebRequest(BaseModel):
    """Standard web request format"""
    session_id: Optional[str] = None
    message: str
    context: Optional[Dict[str, Any]] = None
    stream: bool = False


class WebResponse(BaseModel):
    """Standard web response format"""
    session_id: str
    content: str
    metadata: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None


class APIKeyAuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware for API key authentication.

    Supports both header-based auth (Authorization: Bearer <key>) and
    query parameter auth (?api_key=<key>).

    Set NEXUS_API_KEY environment variable to enable authentication.
    """

    def __init__(self, app, api_key: Optional[str] = None):
        super().__init__(app)
        self.api_key = api_key or os.getenv("NEXUS_API_KEY")

    async def dispatch(self, request: Request, call_next):
        # Skip auth if no API key is configured
        if not self.api_key:
            return await call_next(request)

        # Allow health check without auth
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        # Check Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            if token == self.api_key:
                return await call_next(request)

        # Check X-API-Key header
        api_key_header = request.headers.get("X-API-Key", "")
        if api_key_header == self.api_key:
            return await call_next(request)

        # Check query parameter
        api_key_param = request.query_params.get("api_key", "")
        if api_key_param == self.api_key:
            return await call_next(request)

        # Authentication failed
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing API key"}
        )


class WebConnector:
    """
    Web-enabled Nexus Connector with built-in server capabilities.
    This allows web applications to establish Nexus Connections via HTTP.
    """
    
    def __init__(
        self,
        provider: AIProvider,
        api_key: str,
        model: Optional[str] = None,
        port: int = 8000,
        host: str = "0.0.0.0",
        cors_origins: List[str] = ["*"],
        session_timeout_hours: int = 24,
        auth_api_key: Optional[str] = None,
        require_auth: bool = False,
        **wrapper_kwargs
    ):
        """
        Initialize WebConnector with web server capabilities.

        Args:
            provider: AI provider to use
            api_key: API key for the provider
            model: Model to use (optional)
            port: Port to run web server on
            host: Host to bind to
            cors_origins: Allowed CORS origins
            session_timeout_hours: How long to keep sessions alive
            auth_api_key: API key for authenticating requests (or use NEXUS_API_KEY env)
            require_auth: If True and no auth_api_key provided, fail startup
            **wrapper_kwargs: Additional arguments for UnifiedAIWrapper
        """
        self.provider = provider
        self.api_key = api_key
        self.model = model
        self.port = port
        self.host = host
        self.wrapper_kwargs = wrapper_kwargs

        # Authentication configuration
        self.auth_api_key = auth_api_key or os.getenv("NEXUS_API_KEY")
        if require_auth and not self.auth_api_key:
            raise ValueError(
                "Authentication required but no API key provided. "
                "Set NEXUS_API_KEY environment variable or pass auth_api_key parameter."
            )

        # Session management
        self.session_store = SessionStore(timeout_hours=session_timeout_hours)

        # Factory for creating wrapper instances
        self.wrapper_factory = lambda: UnifiedAIWrapper(
            provider=self.provider,
            api_key=self.api_key,
            model=self.model,
            **self.wrapper_kwargs
        )

        # WebSocket manager
        self.ws_manager = WebSocketManager(self.session_store, self.wrapper_factory)

        # Create FastAPI app
        self.app = FastAPI(
            title="Nexus Web Connector",
            description="Web-enabled Nexus AI Wrapper",
            version="1.0.0"
        )

        # Add authentication middleware (if configured)
        if self.auth_api_key:
            self.app.add_middleware(APIKeyAuthMiddleware, api_key=self.auth_api_key)

        # Add CORS middleware
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Setup routes
        self._setup_routes()

        # Lifecycle management
        self.app.add_event_handler("startup", self._on_startup)
        self.app.add_event_handler("shutdown", self._on_shutdown)
    
    def _setup_routes(self):
        """Setup FastAPI routes"""
        
        @self.app.post("/chat", response_model=WebResponse)
        async def chat(request: WebRequest):
            """Send a message and get a response"""
            try:
                # Get or create session
                session_id = request.session_id or str(uuid.uuid4())
                wrapper = await self.session_store.get_or_create(
                    session_id,
                    lambda: UnifiedAIWrapper(
                        provider=self.provider,
                        api_key=self.api_key,
                        model=self.model,
                        **self.wrapper_kwargs
                    )
                )
                
                # Add context to message if provided
                message = request.message
                if request.context:
                    # Prepend context as system message
                    context_msg = f"Context: {json.dumps(request.context)}\n\n"
                    message = context_msg + message
                
                # Send message
                response = await wrapper.send_message(message)
                
                return WebResponse(
                    session_id=session_id,
                    content=response["content"],
                    metadata={
                        "tool_calls": response.get("tool_calls", []),
                        "tool_results": response.get("tool_results", [])
                    },
                    tokens_used=response.get("usage", {}).get("total_tokens")
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.post("/chat/stream")
        async def chat_stream(request: WebRequest):
            """Stream a response"""
            try:
                session_id = request.session_id or str(uuid.uuid4())
                wrapper = await self.session_store.get_or_create(
                    session_id,
                    lambda: UnifiedAIWrapper(
                        provider=self.provider,
                        api_key=self.api_key,
                        model=self.model,
                        **self.wrapper_kwargs
                    )
                )
                
                async def generate():
                    """Generate streaming response"""
                    # Send session ID first
                    yield f"data: {json.dumps({'type': 'session', 'session_id': session_id})}\n\n"
                    
                    # Stream the response
                    async for chunk in wrapper.stream_message(request.message):
                        yield f"data: {json.dumps({'type': 'content', 'content': chunk})}\n\n"
                    
                    yield "data: [DONE]\n\n"
                
                return StreamingResponse(
                    generate(),
                    media_type="text/event-stream"
                )
                
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        
        @self.app.get("/sessions/{session_id}")
        async def get_session(session_id: str):
            """Get session information"""
            session = await self.session_store.get(session_id)
            if not session:
                raise HTTPException(status_code=404, detail="Session not found")
            
            wrapper = session["wrapper"]
            return {
                "session_id": session_id,
                "created_at": session["created_at"].isoformat(),
                "last_activity": session["last_activity"].isoformat(),
                "message_count": len(wrapper.conversation_history),
                "conversation_length": sum(
                    len(msg.content) for msg in wrapper.conversation_history
                )
            }
        
        @self.app.delete("/sessions/{session_id}")
        async def delete_session(session_id: str):
            """Delete a session"""
            success = await self.session_store.delete(session_id)
            if not success:
                raise HTTPException(status_code=404, detail="Session not found")
            return {"message": f"Session {session_id} deleted"}
        
        @self.app.get("/health")
        async def health():
            """Health check endpoint"""
            return {
                "status": "healthy",
                "provider": self.provider.value,
                "model": self.model,
                "active_sessions": len(self.session_store.sessions),
                "auth_enabled": bool(self.auth_api_key),
                "uptime_seconds": (
                    datetime.now() - self.session_store.created_at
                ).total_seconds()
            }
        
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket, session_id: Optional[str] = None):
            """WebSocket endpoint for real-time chat"""
            connection_id = None
            
            try:
                # Connect the WebSocket
                connection_id = await self.ws_manager.connect(websocket, session_id)
                
                # Send welcome message
                await websocket.send_json({
                    "type": "connected",
                    "connection_id": connection_id,
                    "session_id": session_id or f"ws-{connection_id}",
                    "message": "Connected to Nexus WebSocket"
                })
                
                # Handle the connection
                await self.ws_manager.handle_connection(connection_id)
                
            except WebSocketDisconnect:
                pass  # Normal disconnect
            except Exception as e:
                print(f"WebSocket error: {e}")
            finally:
                # Clean up
                if connection_id:
                    await self.ws_manager.disconnect(connection_id)
        
        @self.app.get("/ws/stats")
        async def websocket_stats():
            """Get WebSocket connection statistics"""
            return self.ws_manager.get_metrics()
    
    async def _on_startup(self):
        """Startup event handler"""
        # Start cleanup task
        asyncio.create_task(self.session_store.cleanup_loop())
        print(f"Nexus Web Connector started on {self.host}:{self.port}")
    
    async def _on_shutdown(self):
        """Shutdown event handler"""
        # Clean up WebSocket connections
        await self.ws_manager.cleanup()
        # Clean up all sessions
        await self.session_store.clear()
        print("Nexus Web Connector shut down")
    
    def run(self, **kwargs):
        """Run the web server"""
        uvicorn.run(
            self.app,
            host=self.host,
            port=self.port,
            **kwargs
        )
    
    async def run_async(self, **kwargs):
        """Run the web server asynchronously"""
        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            **kwargs
        )
        server = uvicorn.Server(config)
        await server.serve()


# Convenience function for quick setup
def create_web_connector(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    port: int = 8000,
    **kwargs
) -> WebConnector:
    """
    Create a web-enabled Nexus connector.
    
    Example:
        connector = create_web_connector(
            provider="openai",
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4",
            port=8000
        )
        connector.run()
    """
    import os
    
    if not api_key:
        # Try to get from environment
        env_key = f"{provider.upper()}_API_KEY"
        api_key = os.getenv(env_key)
        if not api_key:
            raise ValueError(f"No API key provided and {env_key} not set")
    
    return WebConnector(
        provider=AIProvider(provider.lower()),
        api_key=api_key,
        model=model,
        port=port,
        **kwargs
    )