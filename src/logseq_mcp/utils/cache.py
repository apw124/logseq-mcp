"""Caching utilities for the Logseq MCP server."""
from datetime import datetime, timedelta
from typing import Any, Callable, Optional, Dict, Tuple


class ResourceCache:
    """Cache for MCP resources with configurable TTL."""
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize the cache with a time-to-live setting.
        
        Args:
            ttl_seconds: Time in seconds before cache entries expire (default: 300)
        """
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._ttl = timedelta(seconds=ttl_seconds)
    
    def get_or_fetch(self, key: str, fetcher: Callable[[], Any]) -> Any:
        """
        Get value from cache or fetch it if not present/expired.
        
        Args:
            key: Cache key
            fetcher: Function to call if value needs to be fetched
            
        Returns:
            Cached or freshly fetched value
        """
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now() - timestamp < self._ttl:
                return data
        
        # Fetch new data
        data = fetcher()
        self._cache[key] = (data, datetime.now())
        return data
    
    def invalidate(self, key: Optional[str] = None) -> None:
        """
        Invalidate cache entries.
        
        Args:
            key: Specific key to invalidate, or None to clear all
        """
        if key:
            self._cache.pop(key, None)
        else:
            self._cache.clear()
    
    def is_cached(self, key: str) -> bool:
        """
        Check if a key exists in cache and is not expired.
        
        Args:
            key: Cache key to check
            
        Returns:
            True if key exists and is not expired
        """
        if key not in self._cache:
            return False
        
        _, timestamp = self._cache[key]
        return datetime.now() - timestamp < self._ttl