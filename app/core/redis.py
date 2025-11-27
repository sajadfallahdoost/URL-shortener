"""
Redis Configuration Module.

This module provides Redis client setup with connection pooling,
health checks, and helper methods for caching operations.
"""

import logging
from typing import Any
import json
from redis import asyncio as aioredis
from redis.asyncio import Redis, ConnectionPool
from redis.exceptions import RedisError, ConnectionError as RedisConnectionError

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisManager:
    """
    Redis connection manager with connection pooling and health checks.
    
    Provides methods for caching operations with automatic serialization
    and error handling.
    """
    
    def __init__(self) -> None:
        """Initialize Redis manager."""
        self._pool: ConnectionPool | None = None
        self._client: Redis | None = None
    
    def init(self) -> None:
        """
        Initialize Redis connection pool and client.
        
        Creates a connection pool with configuration from settings
        and establishes a Redis client connection.
        """
        redis_url = str(settings.REDIS_URL)
        
        # Create connection pool
        self._pool = ConnectionPool.from_url(
            redis_url,
            max_connections=settings.REDIS_MAX_CONNECTIONS,
            decode_responses=True,
            encoding="utf-8",
            socket_connect_timeout=5,
            socket_keepalive=True,
            health_check_interval=30,
        )
        
        # Create Redis client
        self._client = Redis(connection_pool=self._pool)
        
        logger.info("Redis connection initialized successfully")
    
    async def close(self) -> None:
        """Close Redis connections and cleanup resources."""
        if self._client:
            await self._client.close()
            self._client = None
        
        if self._pool:
            await self._pool.disconnect()
            self._pool = None
        
        logger.info("Redis connections closed")
    
    async def ping(self) -> bool:
        """
        Check Redis connection health.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            if not self._client:
                return False
            return await self._client.ping()
        except (RedisError, RedisConnectionError) as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def get(self, key: str) -> str | None:
        """
        Get value from Redis by key.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        try:
            if not self._client:
                raise RuntimeError("RedisManager not initialized. Call init() first.")
            return await self._client.get(key)
        except RedisError as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None
    
    async def set(
        self,
        key: str,
        value: str,
        ttl: int | None = None
    ) -> bool:
        """
        Set value in Redis with optional TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (defaults to settings.REDIS_CACHE_TTL)
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self._client:
                raise RuntimeError("RedisManager not initialized. Call init() first.")
            
            ttl = ttl or settings.REDIS_CACHE_TTL
            return await self._client.setex(key, ttl, value)
        except RedisError as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key to delete
            
        Returns:
            bool: True if deleted, False otherwise
        """
        try:
            if not self._client:
                raise RuntimeError("RedisManager not initialized. Call init() first.")
            result = await self._client.delete(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if exists, False otherwise
        """
        try:
            if not self._client:
                raise RuntimeError("RedisManager not initialized. Call init() first.")
            result = await self._client.exists(key)
            return result > 0
        except RedisError as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int | None:
        """
        Increment value in Redis.
        
        Args:
            key: Cache key
            amount: Amount to increment by
            
        Returns:
            New value after increment or None on error
        """
        try:
            if not self._client:
                raise RuntimeError("RedisManager not initialized. Call init() first.")
            return await self._client.incrby(key, amount)
        except RedisError as e:
            logger.error(f"Redis INCREMENT error for key '{key}': {e}")
            return None
    
    async def set_json(self, key: str, value: Any, ttl: int | None = None) -> bool:
        """
        Set JSON-serializable value in Redis.
        
        Args:
            key: Cache key
            value: Value to serialize and cache
            ttl: Time-to-live in seconds
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            json_value = json.dumps(value)
            return await self.set(key, json_value, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON serialization error for key '{key}': {e}")
            return False
    
    async def get_json(self, key: str) -> Any | None:
        """
        Get and deserialize JSON value from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            Deserialized value or None if not found or error
        """
        try:
            value = await self.get(key)
            if value is None:
                return None
            return json.loads(value)
        except (TypeError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"JSON deserialization error for key '{key}': {e}")
            return None
    
    @property
    def client(self) -> Redis:
        """Get Redis client instance."""
        if not self._client:
            raise RuntimeError("RedisManager not initialized. Call init() first.")
        return self._client


# Global Redis manager instance
redis_manager = RedisManager()


async def get_redis() -> Redis:
    """
    FastAPI dependency for Redis client.
    
    Returns:
        Redis: Redis client instance
        
    Example:
        @app.get("/cached-data")
        async def get_data(redis: Redis = Depends(get_redis)):
            return await redis.get("my_key")
    """
    return redis_manager.client

