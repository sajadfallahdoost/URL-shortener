"""
FastAPI Dependencies Module.

This module provides reusable dependency functions for FastAPI endpoints,
including database session management, Redis client access, and other
common dependencies.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis

from app.core.database import get_db
from app.core.redis import get_redis


async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @router.get("/urls")
        async def get_urls(db: AsyncSession = Depends(get_database_session)):
            pass
    """
    async for session in get_db():
        yield session


async def get_redis_client() -> Redis:
    """
    Dependency for getting Redis client.
    
    Returns:
        Redis: Redis client instance
        
    Example:
        @router.get("/cached")
        async def get_cached(redis: Redis = Depends(get_redis_client)):
            pass
    """
    return await get_redis()

