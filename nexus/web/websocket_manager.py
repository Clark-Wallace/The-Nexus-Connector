"""
WebSocket connection management for real-time communication.

This module provides WebSocket support for the Nexus Connector, enabling
real-time bidirectional communication between clients and AI providers.
"""

import asyncio
import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi.websockets import WebSocket, WebSocketDisconnect
import logging

from ..core.unified_wrapper import UnifiedAIWrapper


logger = logging.getLogger(__name__)


class ConnectionMetrics:
    """Track WebSocket connection metrics"""
    
    def __init__(self):
        self.total_connections = 0
        self.active_connections = 0
        self.total_messages = 0
        self.connection_errors = 0
    
    def track_connection(self):
        """Track a new connection"""
        self.total_connections += 1
        self.active_connections += 1
    
    def track_disconnection(self):
        """Track a disconnection"""
        self.active_connections = max(0, self.active_connections - 1)
    
    def track_message(self):
        """Track a message sent/received"""
        self.total_messages += 1
    
    def track_error(self):
        """Track a connection error"""
        self.connection_errors += 1


class ConnectionHandler:
    """Handle individual WebSocket connections"""
    
    def __init__(self, websocket: WebSocket, connection_id: str, wrapper: UnifiedAIWrapper):
        self.websocket = websocket
        self.connection_id = connection_id
        self.wrapper = wrapper
        self.connected_at = datetime.now()
        self.last_activity = datetime.now()
    
    async def accept(self):
        """Accept the WebSocket connection"""
        await self.websocket.accept()
        logger.info(f"WebSocket connection {self.connection_id} accepted")
    
    async def send_message(self, message: Dict[str, Any]):
        """Send a message through the WebSocket"""
        try:
            await self.websocket.send_json(message)
            self.last_activity = datetime.now()
        except Exception as e:
            logger.error(f"Error sending message on connection {self.connection_id}: {e}")
            raise
    
    async def receive_message(self) -> Dict[str, Any]:
        """Receive a message from the WebSocket"""
        try:
            message = await self.websocket.receive_json()
            self.last_activity = datetime.now()
            return message
        except WebSocketDisconnect:
            logger.info(f"WebSocket connection {self.connection_id} disconnected")
            raise
        except Exception as e:
            logger.error(f"Error receiving message on connection {self.connection_id}: {e}")
            raise
    
    async def handle_message(self, message_data: Dict[str, Any]):
        """Handle incoming message based on type"""
        message_type = message_data.get("type")
        user_message = message_data.get("message", "")
        session_id = message_data.get("session_id")
        
        try:
            if message_type == "chat":
                # Handle regular chat message
                response = await self.wrapper.send_message(user_message)
                
                await self.send_message({
                    "type": "response",
                    "content": response["content"],
                    "session_id": session_id,
                    "metadata": {
                        "tool_calls": response.get("tool_calls", []),
                        "tool_results": response.get("tool_results", []),
                        "tokens_used": response.get("usage", {}).get("total_tokens")
                    }
                })
            
            elif message_type == "stream":
                # Handle streaming message
                await self.send_message({
                    "type": "stream_start",
                    "session_id": session_id
                })
                
                async for chunk in self.wrapper.stream_message(user_message):
                    await self.send_message({
                        "type": "stream_chunk",
                        "content": chunk,
                        "session_id": session_id
                    })
                
                await self.send_message({
                    "type": "stream_end",
                    "session_id": session_id
                })
            
            else:
                # Unknown message type
                await self.send_message({
                    "type": "error",
                    "error": f"Unknown message type: {message_type}",
                    "session_id": session_id
                })
                
        except Exception as e:
            logger.error(f"Error handling message on connection {self.connection_id}: {e}")
            await self.send_message({
                "type": "error",
                "error": str(e),
                "session_id": session_id
            })
    
    async def close(self):
        """Close the WebSocket connection"""
        try:
            await self.websocket.close()
            logger.info(f"WebSocket connection {self.connection_id} closed")
        except Exception as e:
            logger.error(f"Error closing connection {self.connection_id}: {e}")


class ConnectionPool:
    """Manage a pool of WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, ConnectionHandler] = {}
    
    def add_connection(self, handler: ConnectionHandler):
        """Add a connection to the pool"""
        self.connections[handler.connection_id] = handler
        logger.info(f"Added connection {handler.connection_id} to pool")
    
    def remove_connection(self, connection_id: str) -> Optional[ConnectionHandler]:
        """Remove a connection from the pool"""
        handler = self.connections.pop(connection_id, None)
        if handler:
            logger.info(f"Removed connection {connection_id} from pool")
        return handler
    
    def get_connection(self, connection_id: str) -> Optional[ConnectionHandler]:
        """Get a connection from the pool"""
        return self.connections.get(connection_id)
    
    def get_all_connections(self) -> List[ConnectionHandler]:
        """Get all connections in the pool"""
        return list(self.connections.values())
    
    async def close_all(self):
        """Close all connections in the pool"""
        handlers = list(self.connections.values())
        self.connections.clear()
        
        for handler in handlers:
            try:
                await handler.close()
            except Exception as e:
                logger.error(f"Error closing connection {handler.connection_id}: {e}")


class WebSocketManager:
    """Main WebSocket connection manager"""
    
    def __init__(self, session_store, wrapper_factory=None):
        """
        Initialize WebSocket manager
        
        Args:
            session_store: Session store for managing AI wrapper instances
            wrapper_factory: Factory function to create new UnifiedAIWrapper instances
        """
        self.session_store = session_store
        self.wrapper_factory = wrapper_factory
        self.connection_pool = ConnectionPool()
        self.metrics = ConnectionMetrics()
    
    async def connect(self, websocket: WebSocket, session_id: Optional[str] = None) -> str:
        """
        Connect a new WebSocket client
        
        Args:
            websocket: The WebSocket connection
            session_id: Optional session ID for persistent conversations
            
        Returns:
            Connection ID for the new connection
        """
        # Generate unique connection ID
        connection_id = uuid.uuid4().hex
        
        try:
            # Accept the WebSocket connection
            await websocket.accept()
            
            # Get or create AI wrapper for this session
            if not session_id:
                session_id = f"ws-{connection_id}"
            
            # Get wrapper from session store
            # We need to provide a factory function
            # For now, we'll expect the WebSocketManager to be initialized with a factory
            wrapper = await self.session_store.get_or_create(
                session_id,
                self.wrapper_factory if hasattr(self, 'wrapper_factory') else None
            )
            
            # Create connection handler
            handler = ConnectionHandler(
                websocket=websocket,
                connection_id=connection_id,
                wrapper=wrapper
            )
            
            # Add to connection pool
            self.connection_pool.add_connection(handler)
            
            # Update metrics
            self.metrics.track_connection()
            
            logger.info(f"WebSocket connected: {connection_id} (session: {session_id})")
            
            return connection_id
            
        except Exception as e:
            self.metrics.track_error()
            logger.error(f"Error connecting WebSocket: {e}")
            raise
    
    async def disconnect(self, connection_id: str):
        """
        Disconnect a WebSocket client
        
        Args:
            connection_id: ID of the connection to disconnect
        """
        handler = self.connection_pool.remove_connection(connection_id)
        
        if handler:
            try:
                await handler.close()
                self.metrics.track_disconnection()
                logger.info(f"WebSocket disconnected: {connection_id}")
            except Exception as e:
                logger.error(f"Error disconnecting WebSocket {connection_id}: {e}")
    
    async def handle_connection(self, connection_id: str):
        """
        Handle messages for a WebSocket connection
        
        Args:
            connection_id: ID of the connection to handle
        """
        handler = self.connection_pool.get_connection(connection_id)
        if not handler:
            logger.error(f"Connection {connection_id} not found in pool")
            return
        
        try:
            while True:
                try:
                    # Receive message from client
                    message_data = await handler.receive_message()
                    self.metrics.track_message()
                    
                    # Handle the message
                    await handler.handle_message(message_data)
                    
                except WebSocketDisconnect:
                    # Client disconnected
                    break
                except Exception as e:
                    logger.error(f"Error handling message on connection {connection_id}: {e}")
                    self.metrics.track_error()
                    # Continue handling other messages
                    
        except Exception as e:
            logger.error(f"Fatal error in connection handler {connection_id}: {e}")
            self.metrics.track_error()
        
        finally:
            # Clean up connection
            await self.disconnect(connection_id)
    
    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients
        
        Args:
            message: Message to broadcast
        """
        connections = self.connection_pool.get_all_connections()
        
        if not connections:
            logger.info("No connections to broadcast to")
            return
        
        logger.info(f"Broadcasting message to {len(connections)} connections")
        
        # Send to all connections concurrently
        tasks = []
        for handler in connections:
            task = asyncio.create_task(handler.send_message(message))
            tasks.append(task)
        
        # Wait for all sends to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                connection_id = connections[i].connection_id
                logger.error(f"Error broadcasting to connection {connection_id}: {result}")
                self.metrics.track_error()
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get connection metrics"""
        return {
            "total_connections": self.metrics.total_connections,
            "active_connections": self.metrics.active_connections,
            "total_messages": self.metrics.total_messages,
            "connection_errors": self.metrics.connection_errors,
            "pool_size": len(self.connection_pool.connections)
        }
    
    async def cleanup(self):
        """Clean up all connections and resources"""
        logger.info("Cleaning up WebSocket manager")
        await self.connection_pool.close_all()
        
        # Reset metrics for active connections
        self.metrics.active_connections = 0