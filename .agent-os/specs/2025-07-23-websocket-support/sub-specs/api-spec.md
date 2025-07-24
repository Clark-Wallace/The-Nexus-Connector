# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-07-23-websocket-support/spec.md

> Created: 2025-07-23
> Version: 1.0.0

## Endpoints

### WS /ws/{session_id}

**Purpose:** Establish WebSocket connection for real-time AI conversation streaming
**Parameters:** 
- `session_id` (path): Session identifier for maintaining conversation state
**Connection Upgrade:** HTTP to WebSocket protocol upgrade
**Authentication:** Session-based (existing session must be valid)

**Message Types:**

#### Client → Server Messages

**Send Message:**
```json
{
  "type": "message",
  "content": "Hello, how are you?",
  "provider": "openai",
  "model": "gpt-4",
  "auto_execute": true
}
```

**Get Session Info:**
```json
{
  "type": "get_session",
  "session_id": "session_123"
}
```

**Ping/Heartbeat:**
```json
{
  "type": "ping"
}
```

#### Server → Client Messages

**Response Streaming:**
```json
{
  "type": "response_chunk",
  "content": "Hello! I'm doing well, thank you for asking.",
  "session_id": "session_123",
  "message_id": "msg_456",
  "provider": "openai",
  "is_complete": false
}
```

**Response Complete:**
```json
{
  "type": "response_complete",
  "session_id": "session_123",
  "message_id": "msg_456",
  "token_usage": {
    "prompt_tokens": 10,
    "completion_tokens": 15,
    "total_tokens": 25
  },
  "cost": 0.0001
}
```

**Session Information:**
```json
{
  "type": "session_info",
  "session_id": "session_123",
  "message_count": 5,
  "created_at": "2025-07-23T10:00:00Z",
  "last_activity": "2025-07-23T10:05:00Z"
}
```

**Error Messages:**
```json
{
  "type": "error",
  "error": "Invalid session ID",
  "code": "SESSION_NOT_FOUND",
  "session_id": "session_123"
}
```

**Pong/Heartbeat Response:**
```json
{
  "type": "pong"
}
```

**Errors:**
- `400`: Invalid session ID format
- `404`: Session not found or expired
- `403`: Session access denied
- `500`: Internal server error during AI processing

## WebSocket Connection Lifecycle

1. **Connection Establishment**
   - Client upgrades HTTP connection to WebSocket at `/ws/{session_id}`
   - Server validates session ID and establishes connection
   - Server sends initial session info message

2. **Active Communication**
   - Client sends messages using defined message types
   - Server streams AI responses in real-time chunks
   - Bidirectional heartbeat for connection health

3. **Connection Termination**
   - Client or server can close connection
   - Server performs cleanup and removes from connection registry
   - Session state is preserved for future connections

## Integration with Existing REST API

- WebSocket endpoint supplements existing REST endpoints
- Session management remains unified between REST and WebSocket
- Same authentication and authorization mechanisms
- Shared session store and AI provider routing