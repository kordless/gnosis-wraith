"""
Browser session manager for maintaining state between tool calls.
"""

from typing import Dict, Any, Optional
import asyncio
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("gnosis_wraith")

class BrowserSessionManager:
    """
    Manages browser sessions for tool chaining.
    
    This allows tools to reuse browser instances between calls,
    maintaining cookies, login state, and page context.
    """
    
    def __init__(self):
        self.sessions: Dict[str, Any] = {}
        self.session_timeout = timedelta(minutes=5)
        self._cleanup_task = None
        self._lock = asyncio.Lock()
    
    async def create_session(self, session_id: str, browser_instance: Any) -> str:
        """
        Store a browser session.
        
        Args:
            session_id: Unique identifier for the session
            browser_instance: The browser/page instance to store
            
        Returns:
            The session ID
        """
        async with self._lock:
            self.sessions[session_id] = {
                'browser': browser_instance,
                'created_at': datetime.now(),
                'last_used': datetime.now(),
                'metadata': {}
            }
            logger.info(f"Created browser session: {session_id}")
            
            # Start cleanup task if not running
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
            
            return session_id
    
    async def get_session(self, session_id: str) -> Optional[Any]:
        """
        Retrieve a browser session.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            The browser instance or None if not found/expired
        """
        async with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session['last_used'] = datetime.now()
                logger.info(f"Retrieved browser session: {session_id}")
                return session['browser']
            
            logger.warning(f"Session not found: {session_id}")
            return None
    
    async def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]):
        """
        Update session metadata (e.g., current URL, login state).
        
        Args:
            session_id: The session ID
            metadata: Metadata to merge with existing
        """
        async with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id]['metadata'].update(metadata)
                self.sessions[session_id]['last_used'] = datetime.now()
    
    async def cleanup_expired_sessions(self):
        """Remove expired sessions."""
        async with self._lock:
            now = datetime.now()
            expired = []
            
            for sid, session in self.sessions.items():
                if now - session['last_used'] > self.session_timeout:
                    expired.append(sid)
            
            for sid in expired:
                try:
                    browser = self.sessions[sid]['browser']
                    # Attempt to close browser if it has a close method
                    if hasattr(browser, 'close'):
                        await browser.close()
                    logger.info(f"Closed expired session: {sid}")
                except Exception as e:
                    logger.error(f"Error closing session {sid}: {e}")
                
                del self.sessions[sid]
            
            if expired:
                logger.info(f"Cleaned up {len(expired)} expired sessions")
    
    async def _periodic_cleanup(self):
        """Periodically clean up expired sessions."""
        while True:
            await asyncio.sleep(60)  # Check every minute
            try:
                await self.cleanup_expired_sessions()
            except Exception as e:
                logger.error(f"Error in periodic cleanup: {e}")
    
    async def close_session(self, session_id: str):
        """
        Manually close a specific session.
        
        Args:
            session_id: The session to close
        """
        async with self._lock:
            if session_id in self.sessions:
                try:
                    browser = self.sessions[session_id]['browser']
                    if hasattr(browser, 'close'):
                        await browser.close()
                    logger.info(f"Manually closed session: {session_id}")
                except Exception as e:
                    logger.error(f"Error closing session {session_id}: {e}")
                
                del self.sessions[session_id]
    
    async def close_all_sessions(self):
        """Close all browser sessions."""
        async with self._lock:
            for session_id, session in list(self.sessions.items()):
                try:
                    browser = session['browser']
                    if hasattr(browser, 'close'):
                        await browser.close()
                except Exception as e:
                    logger.error(f"Error closing session {session_id}: {e}")
            
            self.sessions.clear()
            logger.info("Closed all browser sessions")
            
            # Cancel cleanup task
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()
    
    def get_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about all active sessions.
        
        Returns:
            Dictionary of session info (without browser instances)
        """
        result = {}
        for sid, session in self.sessions.items():
            result[sid] = {
                'created_at': session['created_at'].isoformat(),
                'last_used': session['last_used'].isoformat(),
                'metadata': session['metadata'],
                'age_seconds': (datetime.now() - session['created_at']).total_seconds()
            }
        return result

# Global session manager instance
session_manager = BrowserSessionManager()