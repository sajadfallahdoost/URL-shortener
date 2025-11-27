"""
Pytest Configuration and Fixtures.

This module provides test fixtures for database, Redis, and FastAPI client setup.
"""

import pytest
import pytest_asyncio
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient
from fakeredis import aioredis as fake_aioredis

from app.main import app
from app.core.database import Base, get_db
from app.core.redis import redis_manager
from app.core.config import settings

# Test database URL (SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture
async def test_engine():
    """Create test database engine."""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session


@pytest_asyncio.fixture
async def fake_redis():
    """Create fake Redis client for testing."""
    fake_redis_client = fake_aioredis.FakeRedis(decode_responses=True)
    
    # Replace redis_manager client
    original_client = redis_manager._client
    redis_manager._client = fake_redis_client
    
    yield fake_redis_client
    
    # Restore original client
    redis_manager._client = original_client
    await fake_redis_client.close()


@pytest_asyncio.fixture
async def test_client(test_db_session, fake_redis) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with overridden dependencies."""
    
    async def override_get_db():
        yield test_db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return [
        "https://www.example.com/very/long/path/to/page",
        "https://github.com/user/repository/issues/123",
        "https://www.amazon.com/product/dp/B08N5WRWNW",
        "https://stackoverflow.com/questions/12345/how-to-do-something",
    ]


@pytest.fixture
def invalid_urls():
    """Invalid URLs for testing."""
    return [
        "",
        "not-a-url",
        "http://",
        "ftp://invalid-protocol.com",
        "http://localhost/local-resource",  # Should be blocked
        "http://127.0.0.1/internal",  # Should be blocked
    ]

