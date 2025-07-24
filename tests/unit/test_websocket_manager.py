"""
Tests for WebSocket connection management functionality.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.websockets import WebSocket, WebSocketDisconnect
import json

from nexus.web.websocket_manager import (
    WebSocketManager,
    ConnectionHandler,
    ConnectionPool,
    ConnectionMetrics
)


class TestConnectionMetrics:
    """Test WebSocket connection metrics tracking"""
    
    def test_init_metrics(self):
        """Test metrics initialization"""
        metrics = ConnectionMetrics()
        assert metrics.total_connections == 0
        assert metrics.active_connections == 0
        assert metrics.total_messages == 0
        assert metrics.connection_errors == 0
    
    def test_track_connection(self):
        """Test connection tracking"""
        metrics = ConnectionMetrics()
        
        # Track new connection
        metrics.track_connection()
        assert metrics.total_connections == 1
        assert metrics.active_connections == 1
        
        # Track another connection
        metrics.track_connection()
        assert metrics.total_connections == 2
        assert metrics.active_connections == 2
    
    def test_track_disconnection(self):
        """Test disconnection tracking"""
        metrics = ConnectionMetrics()
        metrics.track_connection()
        metrics.track_connection()
        
        # Track disconnection
        metrics.track_disconnection()
        assert metrics.total_connections == 2
        assert metrics.active_connections == 1
    
    def test_track_message(self):
        """Test message tracking"""
        metrics = ConnectionMetrics()
        
        metrics.track_message()
        assert metrics.total_messages == 1
        
        metrics.track_message()
        assert metrics.total_messages == 2
    
    def test_track_error(self):
        """Test error tracking"""
        metrics = ConnectionMetrics()
        
        metrics.track_error()
        assert metrics.connection_errors == 1
        
        metrics.track_error()
        assert metrics.connection_errors == 2


class TestConnectionHandler:
    """Test individual WebSocket connection handling"""
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.receive_text = AsyncMock()
        websocket.receive_json = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_unified_wrapper(self):
        """Create a mock UnifiedAIWrapper"""
        wrapper = AsyncMock()
        wrapper.send_message = AsyncMock(return_value={
            "content": "Test response",
            "usage": {"total_tokens": 100}
        })
        wrapper.stream_message = AsyncMock()
        return wrapper
    
    @pytest.fixture
    def connection_handler(self, mock_websocket, mock_unified_wrapper):
        """Create a ConnectionHandler instance"""
        return ConnectionHandler(
            websocket=mock_websocket,
            connection_id="test-conn-123",
            wrapper=mock_unified_wrapper
        )
    
    @pytest.mark.asyncio
    async def test_accept_connection(self, connection_handler, mock_websocket):
        """Test accepting a WebSocket connection"""
        await connection_handler.accept()
        mock_websocket.accept.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message(self, connection_handler, mock_websocket):
        """Test sending a message through WebSocket"""
        message = {"type": "response", "content": "Hello"}
        
        await connection_handler.send_message(message)
        mock_websocket.send_json.assert_called_once_with(message)
    
    @pytest.mark.asyncio
    async def test_receive_message(self, connection_handler, mock_websocket):
        """Test receiving a message from WebSocket"""
        expected_message = {"type": "chat", "message": "Hello"}
        mock_websocket.receive_json.return_value = expected_message
        
        message = await connection_handler.receive_message()
        assert message == expected_message
        mock_websocket.receive_json.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_chat_message(self, connection_handler, mock_unified_wrapper, mock_websocket):
        """Test handling a chat message"""
        chat_data = {
            "type": "chat",
            "message": "Hello AI",
            "session_id": "test-session"
        }
        
        await connection_handler.handle_message(chat_data)
        
        mock_unified_wrapper.send_message.assert_called_once_with("Hello AI")
        mock_websocket.send_json.assert_called()
    
    @pytest.mark.asyncio
    async def test_handle_stream_message(self, connection_handler, mock_unified_wrapper, mock_websocket):
        """Test handling a streaming message"""
        chat_data = {
            "type": "stream",
            "message": "Stream this response",
            "session_id": "test-session"
        }
        
        # Mock streaming response
        async def mock_stream():
            yield "Hello "
            yield "streaming "
            yield "world!"
        
        mock_unified_wrapper.stream_message.return_value = mock_stream()
        
        await connection_handler.handle_message(chat_data)
        
        mock_unified_wrapper.stream_message.assert_called_once_with("Stream this response")
        # Should send multiple chunks
        assert mock_websocket.send_json.call_count >= 3
    
    @pytest.mark.asyncio
    async def test_close_connection(self, connection_handler, mock_websocket):
        """Test closing a WebSocket connection"""
        await connection_handler.close()
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_handle_disconnect_error(self, connection_handler, mock_websocket):
        """Test handling WebSocket disconnect during message receive"""
        mock_websocket.receive_json.side_effect = WebSocketDisconnect()
        
        with pytest.raises(WebSocketDisconnect):
            await connection_handler.receive_message()


class TestConnectionPool:
    """Test WebSocket connection pool management"""
    
    @pytest.fixture
    def connection_pool(self):
        """Create a ConnectionPool instance"""
        return ConnectionPool()
    
    @pytest.fixture
    def mock_connection_handler(self):
        """Create a mock ConnectionHandler"""
        handler = Mock(spec=ConnectionHandler)
        handler.connection_id = "test-conn-123"
        handler.close = AsyncMock()
        return handler
    
    def test_add_connection(self, connection_pool, mock_connection_handler):
        """Test adding a connection to the pool"""
        connection_pool.add_connection(mock_connection_handler)
        
        assert len(connection_pool.connections) == 1
        assert "test-conn-123" in connection_pool.connections
        assert connection_pool.connections["test-conn-123"] == mock_connection_handler
    
    def test_remove_connection(self, connection_pool, mock_connection_handler):
        """Test removing a connection from the pool"""
        connection_pool.add_connection(mock_connection_handler)
        
        removed = connection_pool.remove_connection("test-conn-123")
        
        assert removed == mock_connection_handler
        assert len(connection_pool.connections) == 0
        assert "test-conn-123" not in connection_pool.connections
    
    def test_remove_nonexistent_connection(self, connection_pool):
        """Test removing a connection that doesn't exist"""
        removed = connection_pool.remove_connection("nonexistent")
        assert removed is None
    
    def test_get_connection(self, connection_pool, mock_connection_handler):
        """Test getting a connection from the pool"""
        connection_pool.add_connection(mock_connection_handler)
        
        retrieved = connection_pool.get_connection("test-conn-123")
        assert retrieved == mock_connection_handler
    
    def test_get_nonexistent_connection(self, connection_pool):
        """Test getting a connection that doesn't exist"""
        retrieved = connection_pool.get_connection("nonexistent")
        assert retrieved is None
    
    def test_get_all_connections(self, connection_pool):
        """Test getting all connections"""
        handler1 = Mock(spec=ConnectionHandler)
        handler1.connection_id = "conn-1"
        handler2 = Mock(spec=ConnectionHandler)
        handler2.connection_id = "conn-2"
        
        connection_pool.add_connection(handler1)
        connection_pool.add_connection(handler2)
        
        all_connections = connection_pool.get_all_connections()
        assert len(all_connections) == 2
        assert handler1 in all_connections
        assert handler2 in all_connections
    
    @pytest.mark.asyncio
    async def test_close_all_connections(self, connection_pool):
        """Test closing all connections in the pool"""
        handler1 = Mock(spec=ConnectionHandler)
        handler1.connection_id = "conn-1"
        handler1.close = AsyncMock()
        
        handler2 = Mock(spec=ConnectionHandler)
        handler2.connection_id = "conn-2"
        handler2.close = AsyncMock()
        
        connection_pool.add_connection(handler1)
        connection_pool.add_connection(handler2)
        
        await connection_pool.close_all()
        
        handler1.close.assert_called_once()
        handler2.close.assert_called_once()
        assert len(connection_pool.connections) == 0


class TestWebSocketManager:
    """Test the main WebSocket manager"""
    
    @pytest.fixture
    def mock_session_store(self):
        """Create a mock SessionStore"""
        store = AsyncMock()
        return store
    
    @pytest.fixture
    def websocket_manager(self, mock_session_store):
        """Create a WebSocketManager instance"""
        return WebSocketManager(session_store=mock_session_store)
    
    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket"""
        websocket = Mock(spec=WebSocket)
        websocket.accept = AsyncMock()
        websocket.send_json = AsyncMock()
        websocket.receive_json = AsyncMock()
        websocket.close = AsyncMock()
        return websocket
    
    @pytest.fixture
    def mock_unified_wrapper(self):
        """Create a mock UnifiedAIWrapper"""
        wrapper = AsyncMock()
        wrapper.send_message = AsyncMock(return_value={
            "content": "Test response",
            "usage": {"total_tokens": 100}
        })
        return wrapper
    
    @pytest.mark.asyncio
    async def test_connect_websocket(self, websocket_manager, mock_websocket, mock_session_store, mock_unified_wrapper):
        """Test connecting a new WebSocket"""
        session_id = "test-session-123"
        mock_session_store.get_or_create.return_value = mock_unified_wrapper
        
        with patch('uuid.uuid4', return_value=Mock(hex="test-conn-123")):
            connection_id = await websocket_manager.connect(mock_websocket, session_id)
        
        assert connection_id == "test-conn-123"
        assert len(websocket_manager.connection_pool.connections) == 1
        mock_websocket.accept.assert_called_once()
        websocket_manager.metrics.total_connections == 1
        websocket_manager.metrics.active_connections == 1
    
    @pytest.mark.asyncio
    async def test_disconnect_websocket(self, websocket_manager, mock_websocket, mock_session_store, mock_unified_wrapper):
        """Test disconnecting a WebSocket"""
        session_id = "test-session-123"
        mock_session_store.get_or_create.return_value = mock_unified_wrapper
        
        with patch('uuid.uuid4', return_value=Mock(hex="test-conn-123")):
            connection_id = await websocket_manager.connect(mock_websocket, session_id)
        
        await websocket_manager.disconnect(connection_id)
        
        assert len(websocket_manager.connection_pool.connections) == 0
        websocket_manager.metrics.active_connections == 0
    
    @pytest.mark.asyncio
    async def test_handle_websocket_communication(self, websocket_manager, mock_websocket, mock_session_store, mock_unified_wrapper):
        """Test handling WebSocket communication loop"""
        session_id = "test-session-123"
        mock_session_store.get_or_create.return_value = mock_unified_wrapper
        
        # Mock message sequence: chat message then disconnect
        messages = [
            {"type": "chat", "message": "Hello", "session_id": session_id},
            WebSocketDisconnect()
        ]
        mock_websocket.receive_json.side_effect = messages
        
        with patch('uuid.uuid4', return_value=Mock(hex="test-conn-123")):
            connection_id = await websocket_manager.connect(mock_websocket, session_id)
            
            # This should handle messages until disconnect
            await websocket_manager.handle_connection(connection_id)
        
        # Should have processed the chat message
        mock_unified_wrapper.send_message.assert_called_once_with("Hello")
        # Connection should be cleaned up
        assert len(websocket_manager.connection_pool.connections) == 0
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, websocket_manager, mock_session_store, mock_unified_wrapper):
        """Test broadcasting a message to all connections"""
        # Create multiple connections
        websocket1 = Mock(spec=WebSocket)
        websocket1.accept = AsyncMock()
        websocket1.send_json = AsyncMock()
        
        websocket2 = Mock(spec=WebSocket)
        websocket2.accept = AsyncMock()
        websocket2.send_json = AsyncMock()
        
        mock_session_store.get_or_create.return_value = mock_unified_wrapper
        
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.side_effect = [
                Mock(hex="conn-1"),
                Mock(hex="conn-2")
            ]
            
            await websocket_manager.connect(websocket1, "session-1")
            await websocket_manager.connect(websocket2, "session-2")
        
        # Broadcast message
        broadcast_msg = {"type": "broadcast", "content": "Hello everyone"}
        await websocket_manager.broadcast(broadcast_msg)
        
        websocket1.send_json.assert_called_with(broadcast_msg)
        websocket2.send_json.assert_called_with(broadcast_msg)
    
    def test_get_metrics(self, websocket_manager):
        """Test getting connection metrics"""
        metrics = websocket_manager.get_metrics()
        
        assert "total_connections" in metrics
        assert "active_connections" in metrics
        assert "total_messages" in metrics
        assert "connection_errors" in metrics
        assert metrics["total_connections"] == 0
        assert metrics["active_connections"] == 0
    
    @pytest.mark.asyncio
    async def test_cleanup_all_connections(self, websocket_manager, mock_websocket, mock_session_store, mock_unified_wrapper):
        """Test cleaning up all connections"""
        mock_session_store.get_or_create.return_value = mock_unified_wrapper
        
        with patch('uuid.uuid4', return_value=Mock(hex="test-conn-123")):
            await websocket_manager.connect(mock_websocket, "test-session")
        
        await websocket_manager.cleanup()
        
        assert len(websocket_manager.connection_pool.connections) == 0
        mock_websocket.close.assert_called_once()


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality"""
    
    @pytest.mark.asyncio
    async def test_full_websocket_lifecycle(self):
        """Test complete WebSocket connection lifecycle"""
        from nexus.web.session_store import SessionStore
        from nexus.core.unified_wrapper import UnifiedAIWrapper
        from nexus.core.base_connector import AIProvider
        
        # Create real session store and mock wrapper creation
        session_store = SessionStore(timeout_hours=1)
        
        with patch('nexus.web.websocket_manager.UnifiedAIWrapper') as mock_wrapper_class:
            mock_wrapper = AsyncMock()
            mock_wrapper.send_message.return_value = {
                "content": "Hello from AI",
                "usage": {"total_tokens": 50}
            }
            mock_wrapper_class.return_value = mock_wrapper
            
            manager = WebSocketManager(session_store=session_store)
            
            # Create mock WebSocket
            mock_websocket = Mock(spec=WebSocket)
            mock_websocket.accept = AsyncMock()
            mock_websocket.send_json = AsyncMock()
            mock_websocket.receive_json = AsyncMock()
            mock_websocket.close = AsyncMock()
            
            # Test connection
            with patch('uuid.uuid4', return_value=Mock(hex="integration-test")):
                connection_id = await manager.connect(mock_websocket, "test-session")
            
            assert connection_id == "integration-test"
            assert manager.get_metrics()["active_connections"] == 1
            
            # Test message handling
            connection = manager.connection_pool.get_connection(connection_id)
            assert connection is not None
            
            await connection.handle_message({
                "type": "chat",
                "message": "Test message",
                "session_id": "test-session"
            })
            
            mock_wrapper.send_message.assert_called_once_with("Test message")
            
            # Test cleanup
            await manager.cleanup()
            assert manager.get_metrics()["active_connections"] == 0