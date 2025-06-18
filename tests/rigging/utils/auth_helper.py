"""
Authentication Helper for Tests

Provides utilities for authenticated API testing.
"""

import aiohttp
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from rigging.config import config


class AuthenticatedClient:
    """Helper class for making authenticated API requests"""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize with optional token override"""
        self.token = token or config.GNOSIS_API_TOKEN
        self.base_url = config.BASE_URL
        self.headers = self._get_headers()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication"""
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if self.token:
            headers['Authorization'] = f'Bearer {self.token}'
        
        return headers
    
    @asynccontextmanager
    async def session(self):
        """Create authenticated aiohttp session"""
        async with aiohttp.ClientSession(headers=self.headers) as session:
            yield session
    
    async def crawl(self, url: str, **options) -> Dict[str, Any]:
        """Perform authenticated crawl"""
        data = {
            "url": url,
            "javascript": options.get("javascript", False),
            "screenshot": options.get("screenshot", False),
            "full_content": options.get("full_content", False),
            "depth": options.get("depth", 0),
            "session_id": options.get("session_id"),
            "response_format": options.get("response_format", "full")
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        async with self.session() as session:
            async with session.post(
                f"{self.base_url}/api/v2/crawl",
                json=data
            ) as response:
                result = await response.json()
                
                # Add status code to result
                result['_status_code'] = response.status
                
                if response.status != 200:
                    result['success'] = False
                    result['error'] = result.get('error', f"HTTP {response.status}")
                
                return result
    
    async def search(self, query: str, limit: int = 10, offset: int = 0) -> Dict[str, Any]:
        """Search previous crawls"""
        data = {
            "query": query,
            "limit": limit,
            "offset": offset
        }
        
        async with self.session() as session:
            async with session.post(
                f"{self.base_url}/api/v2/search",
                json=data
            ) as response:
                result = await response.json()
                result['_status_code'] = response.status
                return result
    
    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get async job status"""
        async with self.session() as session:
            async with session.get(
                f"{self.base_url}/api/v2/jobs/{job_id}"
            ) as response:
                result = await response.json()
                result['_status_code'] = response.status
                return result


def require_auth(func):
    """Decorator to skip tests if no auth token is configured"""
    def wrapper(*args, **kwargs):
        if not config.check_gnosis_auth():
            import pytest
            pytest.skip("No Gnosis API token configured")
        return func(*args, **kwargs)
    
    # Preserve async nature if needed
    if hasattr(func, '__aenter__'):
        wrapper.__aenter__ = func.__aenter__
        wrapper.__aexit__ = func.__aexit__
    
    return wrapper


# Convenience functions
async def authenticated_crawl(url: str, **options) -> Dict[str, Any]:
    """Quick authenticated crawl"""
    client = AuthenticatedClient()
    return await client.crawl(url, **options)


async def authenticated_search(query: str, **options) -> Dict[str, Any]:
    """Quick authenticated search"""
    client = AuthenticatedClient()
    return await client.search(query, **options)