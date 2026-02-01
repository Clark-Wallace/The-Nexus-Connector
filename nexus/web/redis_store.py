"""
Redis Session Store - Distributed session management.

Drop-in replacement for the in-memory session store that uses Redis
for distributed session storage across multiple instances.
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
import logging

try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class SessionData:
    """Session data structure."""
    session_id: str
    provider: str
    model: str
    created_at: float
    last_accessed: float
    messages: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    total_tokens: int = 0
    total_cost: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        return cls(**data)


class RedisSessionStore:
    """
    Redis-backed session store for distributed deployments.

    Features:
    - Distributed session storage across multiple instances
    - Automatic session expiration
    - Session locking for concurrent access
    - Pub/sub for session events
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        prefix: str = "nexus:session:",
        default_ttl: int = 86400,  # 24 hours
        max_sessions_per_user: Optional[int] = None,
        enable_events: bool = False,
    ):
        """
        Initialize Redis session store.

        Args:
            redis_url: Redis connection URL
            prefix: Key prefix for session data
            default_ttl: Default session TTL in seconds
            max_sessions_per_user: Optional limit on sessions per user
            enable_events: Enable pub/sub for session events
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis support requires the 'redis' package. "
                "Install with: pip install redis"
            )

        self.redis_url = redis_url
        self.prefix = prefix
        self.default_ttl = default_ttl
        self.max_sessions_per_user = max_sessions_per_user
        self.enable_events = enable_events

        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None

    async def connect(self) -> None:
        """Connect to Redis."""
        if self._redis is None:
            self._redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self._redis.ping()
            logger.info(f"Connected to Redis at {self.redis_url}")

            if self.enable_events:
                self._pubsub = self._redis.pubsub()
                await self._pubsub.subscribe(f"{self.prefix}events")

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()

        if self._redis:
            await self._redis.close()
            self._redis = None
            logger.info("Disconnected from Redis")

    def _key(self, session_id: str) -> str:
        """Get Redis key for a session."""
        return f"{self.prefix}{session_id}"

    def _user_key(self, user_id: str) -> str:
        """Get Redis key for user's session list."""
        return f"{self.prefix}user:{user_id}"

    def _lock_key(self, session_id: str) -> str:
        """Get Redis key for session lock."""
        return f"{self.prefix}lock:{session_id}"

    async def create_session(
        self,
        session_id: str,
        provider: str,
        model: str,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None,
    ) -> SessionData:
        """
        Create a new session.

        Args:
            session_id: Unique session identifier
            provider: AI provider name
            model: Model name
            user_id: Optional user identifier
            metadata: Optional metadata
            ttl: Optional custom TTL

        Returns:
            Created SessionData
        """
        await self.connect()

        now = time.time()
        session = SessionData(
            session_id=session_id,
            provider=provider,
            model=model,
            created_at=now,
            last_accessed=now,
            messages=[],
            metadata=metadata or {},
        )

        # Store session
        key = self._key(session_id)
        ttl = ttl or self.default_ttl
        await self._redis.setex(key, ttl, json.dumps(session.to_dict()))

        # Track user's sessions if user_id provided
        if user_id:
            user_key = self._user_key(user_id)
            await self._redis.sadd(user_key, session_id)
            await self._redis.expire(user_key, ttl)

            # Enforce max sessions per user
            if self.max_sessions_per_user:
                await self._enforce_user_session_limit(user_id)

        # Publish event
        if self.enable_events:
            await self._publish_event("session_created", {
                "session_id": session_id,
                "provider": provider,
                "user_id": user_id,
            })

        logger.debug(f"Created session: {session_id}")
        return session

    async def get_session(self, session_id: str) -> Optional[SessionData]:
        """
        Get a session by ID.

        Args:
            session_id: Session identifier

        Returns:
            SessionData or None if not found
        """
        await self.connect()

        key = self._key(session_id)
        data = await self._redis.get(key)

        if data is None:
            return None

        session = SessionData.from_dict(json.loads(data))

        # Update last accessed
        session.last_accessed = time.time()
        await self._redis.setex(
            key,
            self.default_ttl,
            json.dumps(session.to_dict())
        )

        return session

    async def update_session(
        self,
        session_id: str,
        messages: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tokens: Optional[int] = None,
        cost: Optional[float] = None,
    ) -> Optional[SessionData]:
        """
        Update a session.

        Args:
            session_id: Session identifier
            messages: New messages list (replaces existing)
            metadata: Metadata to merge
            tokens: Tokens to add to total
            cost: Cost to add to total

        Returns:
            Updated SessionData or None if not found
        """
        await self.connect()

        # Use lock for concurrent access
        async with self._session_lock(session_id):
            session = await self.get_session(session_id)
            if session is None:
                return None

            if messages is not None:
                session.messages = messages

            if metadata:
                session.metadata.update(metadata)

            if tokens:
                session.total_tokens += tokens

            if cost:
                session.total_cost += cost

            session.last_accessed = time.time()

            # Save updated session
            key = self._key(session_id)
            await self._redis.setex(
                key,
                self.default_ttl,
                json.dumps(session.to_dict())
            )

            return session

    async def add_message(
        self,
        session_id: str,
        message: Dict[str, Any]
    ) -> Optional[SessionData]:
        """
        Add a message to a session.

        Args:
            session_id: Session identifier
            message: Message to add

        Returns:
            Updated SessionData or None if not found
        """
        await self.connect()

        async with self._session_lock(session_id):
            session = await self.get_session(session_id)
            if session is None:
                return None

            session.messages.append(message)
            session.last_accessed = time.time()

            key = self._key(session_id)
            await self._redis.setex(
                key,
                self.default_ttl,
                json.dumps(session.to_dict())
            )

            return session

    async def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: Session identifier

        Returns:
            True if deleted, False if not found
        """
        await self.connect()

        key = self._key(session_id)
        result = await self._redis.delete(key)

        if result:
            if self.enable_events:
                await self._publish_event("session_deleted", {
                    "session_id": session_id,
                })
            logger.debug(f"Deleted session: {session_id}")

        return bool(result)

    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[SessionData]:
        """
        List sessions.

        Args:
            user_id: Optional user filter
            limit: Maximum sessions to return
            offset: Offset for pagination

        Returns:
            List of SessionData
        """
        await self.connect()

        if user_id:
            # Get user's sessions
            user_key = self._user_key(user_id)
            session_ids = await self._redis.smembers(user_key)
        else:
            # Scan all sessions
            pattern = f"{self.prefix}[^:]*"  # Exclude special keys
            session_ids = []
            async for key in self._redis.scan_iter(match=pattern):
                session_id = key.replace(self.prefix, "")
                if ":" not in session_id:  # Skip user: and lock: keys
                    session_ids.append(session_id)

        # Apply pagination
        session_ids = sorted(session_ids)[offset:offset + limit]

        # Fetch session data
        sessions = []
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions.append(session)

        return sessions

    async def cleanup_expired(self) -> int:
        """
        Clean up expired sessions.

        Note: Redis handles TTL expiration automatically, but this
        can be used to clean up orphaned user session lists.

        Returns:
            Number of cleaned up entries
        """
        await self.connect()

        count = 0
        pattern = f"{self.prefix}user:*"

        async for user_key in self._redis.scan_iter(match=pattern):
            session_ids = await self._redis.smembers(user_key)
            for session_id in session_ids:
                if not await self._redis.exists(self._key(session_id)):
                    await self._redis.srem(user_key, session_id)
                    count += 1

        if count:
            logger.info(f"Cleaned up {count} expired session references")

        return count

    async def get_stats(self) -> Dict[str, Any]:
        """
        Get session store statistics.

        Returns:
            Dictionary of statistics
        """
        await self.connect()

        # Count sessions
        pattern = f"{self.prefix}[^:]*"
        session_count = 0
        total_messages = 0
        total_tokens = 0

        async for key in self._redis.scan_iter(match=pattern):
            session_id = key.replace(self.prefix, "")
            if ":" not in session_id:
                session_count += 1
                data = await self._redis.get(key)
                if data:
                    session = json.loads(data)
                    total_messages += len(session.get("messages", []))
                    total_tokens += session.get("total_tokens", 0)

        return {
            "total_sessions": session_count,
            "total_messages": total_messages,
            "total_tokens": total_tokens,
            "redis_url": self.redis_url,
            "prefix": self.prefix,
            "default_ttl": self.default_ttl,
        }

    def _session_lock(self, session_id: str):
        """Get a distributed lock for a session."""
        return RedisLock(
            self._redis,
            self._lock_key(session_id),
            timeout=10.0
        )

    async def _enforce_user_session_limit(self, user_id: str) -> None:
        """Enforce maximum sessions per user by deleting oldest."""
        if not self.max_sessions_per_user:
            return

        user_key = self._user_key(user_id)
        session_ids = list(await self._redis.smembers(user_key))

        if len(session_ids) <= self.max_sessions_per_user:
            return

        # Get session details to find oldest
        sessions_with_time = []
        for session_id in session_ids:
            session = await self.get_session(session_id)
            if session:
                sessions_with_time.append((session_id, session.last_accessed))

        # Sort by last accessed (oldest first)
        sessions_with_time.sort(key=lambda x: x[1])

        # Delete oldest sessions
        to_delete = len(sessions_with_time) - self.max_sessions_per_user
        for session_id, _ in sessions_with_time[:to_delete]:
            await self.delete_session(session_id)
            await self._redis.srem(user_key, session_id)

    async def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish a session event."""
        if not self.enable_events or not self._redis:
            return

        event = {
            "type": event_type,
            "timestamp": time.time(),
            "data": data,
        }
        await self._redis.publish(
            f"{self.prefix}events",
            json.dumps(event)
        )

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class RedisLock:
    """Simple distributed lock using Redis."""

    def __init__(
        self,
        redis_client: "redis.Redis",
        key: str,
        timeout: float = 10.0,
        blocking_timeout: float = 5.0,
    ):
        self.redis = redis_client
        self.key = key
        self.timeout = timeout
        self.blocking_timeout = blocking_timeout
        self._lock_value: Optional[str] = None

    async def __aenter__(self):
        import uuid
        self._lock_value = str(uuid.uuid4())

        end_time = time.monotonic() + self.blocking_timeout
        while time.monotonic() < end_time:
            if await self.redis.set(
                self.key,
                self._lock_value,
                nx=True,
                ex=int(self.timeout)
            ):
                return self
            await asyncio.sleep(0.1)

        raise TimeoutError(f"Could not acquire lock: {self.key}")

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Only release if we still own the lock
        current = await self.redis.get(self.key)
        if current == self._lock_value:
            await self.redis.delete(self.key)


# Factory function for easy session store creation
def create_session_store(
    backend: str = "memory",
    **kwargs
) -> Union["RedisSessionStore", Any]:
    """
    Create a session store.

    Args:
        backend: "memory" or "redis"
        **kwargs: Backend-specific configuration

    Returns:
        Session store instance
    """
    if backend == "redis":
        return RedisSessionStore(**kwargs)
    else:
        # Return the default in-memory store
        from .session_store import SessionStore
        return SessionStore()
