"""
Database Configuration Module.

This module provides SQLAlchemy async engine setup, session management,
and database connection handling with proper connection pooling.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool, QueuePool

from app.core.config import settings


# Base class for SQLAlchemy models
Base = declarative_base()


class DatabaseManager:
    """
    Database connection and session manager.
    
    Handles the creation and management of database engine and sessions
    with proper connection pooling and async support.
    """
    
    def __init__(self) -> None:
        """Initialize database manager with engine and session factory."""
        self._engine: AsyncEngine | None = None
        self._session_factory: async_sessionmaker[AsyncSession] | None = None
    
    def init(self) -> None:
        """
        Initialize database engine and session factory.
        
        Creates an async SQLAlchemy engine with connection pooling
        configured based on application settings.
        """
        # Convert pydantic URL to string and ensure it's async
        database_url = str(settings.DATABASE_URL)
        
        # Create async engine
        # Note: For async engines, we don't specify poolclass
        # SQLAlchemy automatically uses AsyncAdaptedQueuePool
        engine_kwargs = {
            "echo": settings.DB_ECHO,
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_pre_ping": True,  # Verify connections before using
            "pool_recycle": 3600,   # Recycle connections after 1 hour
        }
        
        # Use NullPool for test environment
        if settings.ENVIRONMENT == "test":
            engine_kwargs["poolclass"] = NullPool
        
        self._engine = create_async_engine(
            database_url,
            **engine_kwargs
        )
        
        # Create session factory
        self._session_factory = async_sessionmaker(
            bind=self._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    
    async def close(self) -> None:
        """Close database engine and cleanup connections."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None
    
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session.
        
        Yields:
            AsyncSession: Database session for executing queries
            
        Example:
            async with database_manager.get_session() as session:
                result = await session.execute(query)
        """
        if not self._session_factory:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @property
    def engine(self) -> AsyncEngine:
        """Get database engine."""
        if not self._engine:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")
        return self._engine


# Global database manager instance
database_manager = DatabaseManager()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions.
    
    Yields:
        AsyncSession: Database session
        
    Example:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async for session in database_manager.get_session():
        yield session

