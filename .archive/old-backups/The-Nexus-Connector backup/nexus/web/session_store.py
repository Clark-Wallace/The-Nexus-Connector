"""
SessionStore - Manages web sessions for Nexus
"""

import asyncio
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class SessionStore:
    """
    Manages sessions for web-based Nexus usage.
    Handles creation, retrieval, and cleanup of conversation sessions.
    """
    
    def __init__(self, timeout_hours: int = 24):
        """
        Initialize the session store.
        
        Args:
            timeout_hours: Hours before a session is considered expired
        """
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.timeout_hours = timeout_hours
        self.created_at = datetime.now()
        self._cleanup_task: Optional[asyncio.Task] = None
    
    async def get_or_create(
        self,
        session_id: str,
        factory: Callable[[], Any]
    ) -> Any:
        """
        Get an existing session or create a new one.
        
        Args:
            session_id: Unique session identifier
            factory: Callable that creates a new wrapper instance
            
        Returns:
            The wrapper instance for this session
        """
        if session_id in self.sessions:
            # Update last activity
            self.sessions[session_id]["last_activity"] = datetime.now()
            return self.sessions[session_id]["wrapper"]
        
        # Create new session
        wrapper = factory()
        self.sessions[session_id] = {
            "wrapper": wrapper,
            "created_at": datetime.now(),
            "last_activity": datetime.now()
        }
        
        logger.info(f"Created new session: {session_id}")
        return wrapper
    
    async def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        return self.sessions.get(session_id)
    
    async def delete(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"Deleted session: {session_id}")
            return True
        return False
    
    async def cleanup_expired(self):
        """Remove expired sessions"""
        now = datetime.now()
        expired_cutoff = now - timedelta(hours=self.timeout_hours)
        
        expired_sessions = [
            session_id
            for session_id, session_data in self.sessions.items()
            if session_data["last_activity"] < expired_cutoff
        ]
        
        for session_id in expired_sessions:
            await self.delete(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
    
    async def cleanup_loop(self):
        """Background task to periodically clean up expired sessions"""
        while True:
            try:
                await asyncio.sleep(3600)  # Check every hour
                await self.cleanup_expired()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    async def clear(self):
        """Clear all sessions"""
        count = len(self.sessions)
        self.sessions.clear()
        logger.info(f"Cleared {count} sessions")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session store statistics"""
        now = datetime.now()
        
        if not self.sessions:
            return {
                "total_sessions": 0,
                "oldest_session": None,
                "newest_session": None,
                "average_age_minutes": 0
            }
        
        ages = [
            (now - session["created_at"]).total_seconds() / 60
            for session in self.sessions.values()
        ]
        
        return {
            "total_sessions": len(self.sessions),
            "oldest_session": min(
                session["created_at"] for session in self.sessions.values()
            ).isoformat(),
            "newest_session": max(
                session["created_at"] for session in self.sessions.values()
            ).isoformat(),
            "average_age_minutes": sum(ages) / len(ages)
        }