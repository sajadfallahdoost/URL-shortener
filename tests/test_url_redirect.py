"""
Test URL Redirection Functionality.

Tests for URL redirection, click counting, and cache behavior.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.url_service import URLService
from app.repositories.url_repository import URLRepository
from app.core.exceptions import URLNotFoundException


@pytest.mark.asyncio
async def test_successful_redirect(test_db_session: AsyncSession, fake_redis, sample_urls):
    """Test successful URL redirect."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    
    original_url = sample_urls[0]
    
    # Create short URL
    created_url = await url_service.create_short_url(original_url)
    
    # Get original URL
    retrieved_url = await url_service.get_original_url(created_url.short_code)
    
    assert retrieved_url == original_url


@pytest.mark.asyncio
async def test_nonexistent_short_code(test_db_session: AsyncSession, fake_redis):
    """Test accessing non-existent short code returns 404."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    
    with pytest.raises(URLNotFoundException):
        await url_service.get_original_url("XXXXX")


@pytest.mark.asyncio
async def test_click_count_increment(test_db_session: AsyncSession, fake_redis, sample_urls):
    """Test that click count increments on each access."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    repository = URLRepository(test_db_session)
    
    original_url = sample_urls[0]
    
    # Create short URL
    created_url = await url_service.create_short_url(original_url)
    
    # Access multiple times
    for i in range(5):
        await url_service.get_original_url(created_url.short_code)
    
    # Check click count
    url_stats = await repository.get_url_stats(created_url.short_code)
    assert url_stats.click_count == 5


@pytest.mark.asyncio
async def test_last_accessed_timestamp_update(
    test_db_session: AsyncSession,
    fake_redis,
    sample_urls
):
    """Test that last_accessed_at is updated on access."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    repository = URLRepository(test_db_session)
    
    original_url = sample_urls[0]
    
    # Create short URL
    created_url = await url_service.create_short_url(original_url)
    
    # Initially, last_accessed_at should be None
    url_before = await repository.get_url_stats(created_url.short_code)
    assert url_before.last_accessed_at is None
    
    # Access the URL
    await url_service.get_original_url(created_url.short_code)
    
    # Now last_accessed_at should be set
    url_after = await repository.get_url_stats(created_url.short_code)
    assert url_after.last_accessed_at is not None


@pytest.mark.asyncio
async def test_cache_hit_scenario(test_db_session: AsyncSession, fake_redis, sample_urls):
    """Test that cached URLs are retrieved from Redis."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    
    original_url = sample_urls[0]
    
    # Create short URL (this caches it)
    created_url = await url_service.create_short_url(original_url)
    
    # First access - should be cached
    cache_key = f"url:short:{created_url.short_code}"
    cached_value = await fake_redis.get(cache_key)
    assert cached_value == original_url
    
    # Retrieve from cache
    retrieved_url = await url_service.get_original_url(created_url.short_code)
    assert retrieved_url == original_url


@pytest.mark.asyncio
async def test_cache_miss_scenario(test_db_session: AsyncSession, fake_redis, sample_urls):
    """Test that uncached URLs are retrieved from database and then cached."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    repository = URLRepository(test_db_session)
    
    original_url = sample_urls[0]
    
    # Create URL directly in database (bypass caching)
    short_code = "TEST1"
    await repository.create_url(original_url, short_code)
    
    # Cache should be empty
    cache_key = f"url:short:{short_code}"
    cached_value = await fake_redis.get(cache_key)
    assert cached_value is None
    
    # Retrieve URL (should cache it)
    retrieved_url = await url_service.get_original_url(short_code)
    assert retrieved_url == original_url
    
    # Now it should be cached
    cached_value = await fake_redis.get(cache_key)
    assert cached_value == original_url

