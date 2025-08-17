"""
Redis Caching System for JobSwitch.ai
Handles caching of frequently accessed data like job recommendations, user profiles, and AI responses
"""
import json
import logging
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta
import redis.asyncio as redis
from redis.asyncio import Redis
from app.core.config import settings

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Redis-based cache manager for the application
    """
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.enabled = settings.redis_enabled
        self.redis_url = settings.redis_url
        
        # Cache TTL settings (in seconds)
        self.cache_ttl = {
            "job_recommendations": 3600,  # 1 hour
            "job_search_results": 1800,   # 30 minutes
            "user_profile": 7200,         # 2 hours
            "skills_analysis": 3600,      # 1 hour
            "resume_optimization": 1800,  # 30 minutes
            "interview_questions": 7200,  # 2 hours
            "career_roadmap": 14400,      # 4 hours
            "networking_contacts": 3600,  # 1 hour
            "ai_responses": 1800,         # 30 minutes
            "default": 3600               # 1 hour default
        }
    
    async def initialize(self):
        """
        Initialize Redis connection
        """
        if not self.enabled:
            logger.info("Redis caching is disabled")
            return
        
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Test connection
            await self.redis_client.ping()
            logger.info("Redis cache initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis cache: {str(e)}")
            self.enabled = False
            self.redis_client = None
    
    async def close(self):
        """
        Close Redis connection
        """
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis cache connection closed")
    
    def _get_cache_key(self, category: str, identifier: str) -> str:
        """
        Generate cache key with consistent format
        
        Args:
            category: Cache category (e.g., 'job_recommendations', 'user_profile')
            identifier: Unique identifier for the cached item
            
        Returns:
            Formatted cache key
        """
        return f"jobswitch:{category}:{identifier}"
    
    def _serialize_data(self, data: Any) -> str:
        """
        Serialize data for Redis storage
        
        Args:
            data: Data to serialize
            
        Returns:
            JSON string representation
        """
        try:
            if isinstance(data, (dict, list)):
                return json.dumps(data, default=str)
            else:
                return str(data)
        except Exception as e:
            logger.error(f"Error serializing data: {str(e)}")
            return str(data)
    
    def _deserialize_data(self, data: str) -> Any:
        """
        Deserialize data from Redis storage
        
        Args:
            data: JSON string to deserialize
            
        Returns:
            Deserialized data
        """
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return data
    
    async def set(self, category: str, identifier: str, data: Any, ttl: Optional[int] = None) -> bool:
        """
        Store data in cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            data: Data to cache
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            serialized_data = self._serialize_data(data)
            
            # Use category-specific TTL or provided TTL
            cache_ttl = ttl or self.cache_ttl.get(category, self.cache_ttl["default"])
            
            await self.redis_client.setex(cache_key, cache_ttl, serialized_data)
            
            logger.debug(f"Cached data: {cache_key} (TTL: {cache_ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"Error setting cache: {str(e)}")
            return False
    
    async def get(self, category: str, identifier: str) -> Optional[Any]:
        """
        Retrieve data from cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            
        Returns:
            Cached data or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug(f"Cache hit: {cache_key}")
                return self._deserialize_data(cached_data)
            else:
                logger.debug(f"Cache miss: {cache_key}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting cache: {str(e)}")
            return None
    
    async def delete(self, category: str, identifier: str) -> bool:
        """
        Delete data from cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            result = await self.redis_client.delete(cache_key)
            
            logger.debug(f"Deleted from cache: {cache_key}")
            return result > 0
            
        except Exception as e:
            logger.error(f"Error deleting from cache: {str(e)}")
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete multiple keys matching a pattern
        
        Args:
            pattern: Redis key pattern (e.g., 'jobswitch:user_profile:*')
            
        Returns:
            Number of keys deleted
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            keys = await self.redis_client.keys(pattern)
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.debug(f"Deleted {deleted} keys matching pattern: {pattern}")
                return deleted
            return 0
            
        except Exception as e:
            logger.error(f"Error deleting pattern from cache: {str(e)}")
            return 0
    
    async def exists(self, category: str, identifier: str) -> bool:
        """
        Check if key exists in cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            
        Returns:
            True if key exists, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            result = await self.redis_client.exists(cache_key)
            return result > 0
            
        except Exception as e:
            logger.error(f"Error checking cache existence: {str(e)}")
            return False
    
    async def get_ttl(self, category: str, identifier: str) -> int:
        """
        Get remaining TTL for a cached item
        
        Args:
            category: Cache category
            identifier: Unique identifier
            
        Returns:
            Remaining TTL in seconds (-1 if no TTL, -2 if key doesn't exist)
        """
        if not self.enabled or not self.redis_client:
            return -2
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            return await self.redis_client.ttl(cache_key)
            
        except Exception as e:
            logger.error(f"Error getting TTL: {str(e)}")
            return -2
    
    async def increment(self, category: str, identifier: str, amount: int = 1) -> Optional[int]:
        """
        Increment a numeric value in cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            amount: Amount to increment by
            
        Returns:
            New value after increment, or None if error
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            result = await self.redis_client.incrby(cache_key, amount)
            
            logger.debug(f"Incremented cache: {cache_key} by {amount} = {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error incrementing cache: {str(e)}")
            return None
    
    async def set_hash(self, category: str, identifier: str, field_values: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Store hash data in cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            field_values: Dictionary of field-value pairs
            ttl: Time to live in seconds (optional)
            
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            
            # Serialize all values
            serialized_values = {
                field: self._serialize_data(value) 
                for field, value in field_values.items()
            }
            
            await self.redis_client.hset(cache_key, mapping=serialized_values)
            
            # Set TTL if provided
            if ttl:
                await self.redis_client.expire(cache_key, ttl)
            
            logger.debug(f"Cached hash: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Error setting hash cache: {str(e)}")
            return False
    
    async def get_hash(self, category: str, identifier: str, field: Optional[str] = None) -> Optional[Union[Dict[str, Any], Any]]:
        """
        Retrieve hash data from cache
        
        Args:
            category: Cache category
            identifier: Unique identifier
            field: Specific field to retrieve (optional, returns all if None)
            
        Returns:
            Hash data or specific field value, or None if not found
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            cache_key = self._get_cache_key(category, identifier)
            
            if field:
                # Get specific field
                cached_data = await self.redis_client.hget(cache_key, field)
                if cached_data:
                    return self._deserialize_data(cached_data)
            else:
                # Get all fields
                cached_data = await self.redis_client.hgetall(cache_key)
                if cached_data:
                    return {
                        field: self._deserialize_data(value)
                        for field, value in cached_data.items()
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting hash cache: {str(e)}")
            return None
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        if not self.enabled or not self.redis_client:
            return {"enabled": False}
        
        try:
            info = await self.redis_client.info()
            
            # Get key count by category
            key_counts = {}
            for category in self.cache_ttl.keys():
                if category != "default":
                    pattern = f"jobswitch:{category}:*"
                    keys = await self.redis_client.keys(pattern)
                    key_counts[category] = len(keys)
            
            return {
                "enabled": True,
                "connected_clients": info.get("connected_clients", 0),
                "used_memory": info.get("used_memory_human", "0B"),
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
                "hit_rate": self._calculate_hit_rate(
                    info.get("keyspace_hits", 0),
                    info.get("keyspace_misses", 0)
                ),
                "key_counts": key_counts,
                "cache_ttl_settings": self.cache_ttl
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {str(e)}")
            return {"enabled": True, "error": str(e)}
    
    def _calculate_hit_rate(self, hits: int, misses: int) -> float:
        """
        Calculate cache hit rate percentage
        
        Args:
            hits: Number of cache hits
            misses: Number of cache misses
            
        Returns:
            Hit rate as percentage
        """
        total = hits + misses
        if total == 0:
            return 0.0
        return round((hits / total) * 100, 2)
    
    async def clear_all(self) -> bool:
        """
        Clear all JobSwitch cache data (use with caution)
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            pattern = "jobswitch:*"
            deleted = await self.delete_pattern(pattern)
            logger.info(f"Cleared all cache data: {deleted} keys deleted")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False


# Global cache manager instance
cache_manager = CacheManager()


# Convenience functions for common cache operations
async def cache_job_recommendations(user_id: str, recommendations: List[Dict[str, Any]]) -> bool:
    """Cache job recommendations for a user"""
    return await cache_manager.set("job_recommendations", user_id, recommendations)


async def get_cached_job_recommendations(user_id: str) -> Optional[List[Dict[str, Any]]]:
    """Get cached job recommendations for a user"""
    return await cache_manager.get("job_recommendations", user_id)


async def cache_user_profile(user_id: str, profile_data: Dict[str, Any]) -> bool:
    """Cache user profile data"""
    return await cache_manager.set("user_profile", user_id, profile_data)


async def get_cached_user_profile(user_id: str) -> Optional[Dict[str, Any]]:
    """Get cached user profile data"""
    return await cache_manager.get("user_profile", user_id)


async def cache_ai_response(prompt_hash: str, response: str, category: str = "ai_responses") -> bool:
    """Cache AI response for reuse"""
    return await cache_manager.set(category, prompt_hash, response)


async def get_cached_ai_response(prompt_hash: str, category: str = "ai_responses") -> Optional[str]:
    """Get cached AI response"""
    return await cache_manager.get(category, prompt_hash)


async def invalidate_user_cache(user_id: str) -> int:
    """Invalidate all cache entries for a user"""
    patterns = [
        f"jobswitch:job_recommendations:{user_id}",
        f"jobswitch:user_profile:{user_id}",
        f"jobswitch:skills_analysis:{user_id}",
        f"jobswitch:resume_optimization:{user_id}*",
        f"jobswitch:career_roadmap:{user_id}",
        f"jobswitch:networking_contacts:{user_id}*"
    ]
    
    total_deleted = 0
    for pattern in patterns:
        deleted = await cache_manager.delete_pattern(pattern)
        total_deleted += deleted
    
    return total_deleted

def get_redis_client() -> Optional[Redis]:
    """
    Get the Redis client instance
    
    Returns:
        Redis client instance or None if not available
    """
    return cache_manager.redis_client if cache_manager.enabled else None

def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics from the global cache manager"""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're in an async context, we can't use asyncio.run
            # Return a placeholder for now
            return {
                "status": "cache_active",
                "note": "Stats available via async method"
            }
        else:
            return asyncio.run(cache_manager.get_cache_stats())
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

# Export commonly used functions
__all__ = [
    'CacheManager',
    'cache_manager',
    'get_cache_stats'
]