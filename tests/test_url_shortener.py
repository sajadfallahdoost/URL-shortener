"""
Test URL Shortener Core Functionality.

Tests for URL creation, validation, and database persistence.
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.url_service import URLService
from app.services.shortener import ShortCodeGenerator
from app.core.exceptions import InvalidURLException
from app.repositories.url_repository import URLRepository


@pytest.mark.asyncio
async def test_create_short_url_success(test_db_session: AsyncSession, fake_redis, sample_urls):
    """Test successful URL shortening."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    
    original_url = sample_urls[0]
    url = await url_service.create_short_url(original_url)
    
    assert url is not None
    assert url.short_code is not None
    assert len(url.short_code) == 5
    assert url.original_url == original_url
    assert url.click_count == 0
    assert url.created_at is not None


@pytest.mark.asyncio
async def test_duplicate_url_returns_same_short_code(
    test_db_session: AsyncSession,
    fake_redis,
    sample_urls
):
    """Test that shortening the same URL returns the same short code."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    
    original_url = sample_urls[0]
    
    # Create first time
    url1 = await url_service.create_short_url(original_url)
    
    # Create second time with same URL
    url2 = await url_service.create_short_url(original_url)
    
    assert url1.short_code == url2.short_code
    assert url1.id == url2.id


@pytest.mark.asyncio
async def test_invalid_url_rejection(test_db_session: AsyncSession, fake_redis, invalid_urls):
    """Test that invalid URLs are rejected."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    
    for invalid_url in invalid_urls:
        if invalid_url:  # Skip empty string test (different error)
            with pytest.raises(InvalidURLException):
                await url_service.create_short_url(invalid_url)


@pytest.mark.asyncio
async def test_short_code_generation_uniqueness(test_db_session: AsyncSession, sample_urls):
    """Test that generated short codes are unique."""
    repository = URLRepository(test_db_session)
    generator = ShortCodeGenerator()
    
    short_codes = set()
    
    # Generate multiple short codes
    for i, url in enumerate(sample_urls):
        short_code = generator.generate()
        
        # Ensure it's unique before adding to DB
        while await repository.check_short_code_exists(short_code):
            short_code = generator.generate()
        
        short_codes.add(short_code)
        await repository.create_url(url, short_code)
    
    # All codes should be unique
    assert len(short_codes) == len(sample_urls)


@pytest.mark.asyncio
async def test_database_persistence(test_db_session: AsyncSession, fake_redis, sample_urls):
    """Test that URL mappings are persisted to database."""
    url_service = URLService(db_session=test_db_session, redis_manager=fake_redis)
    repository = URLRepository(test_db_session)
    
    original_url = sample_urls[0]
    
    # Create URL
    created_url = await url_service.create_short_url(original_url)
    
    # Retrieve from database
    retrieved_url = await repository.get_by_short_code(created_url.short_code)
    
    assert retrieved_url is not None
    assert retrieved_url.short_code == created_url.short_code
    assert retrieved_url.original_url == original_url


@pytest.mark.asyncio
async def test_short_code_validation():
    """Test short code validation."""
    generator = ShortCodeGenerator()
    
    # Valid codes
    assert generator.is_valid("aB3xY")
    assert generator.is_valid("12345")
    assert generator.is_valid("abcde")
    
    # Invalid codes
    assert not generator.is_valid("aB3")  # Too short
    assert not generator.is_valid("aB3xY1")  # Too long
    assert not generator.is_valid("aB3x!")  # Invalid character
    assert not generator.is_valid("")  # Empty


@pytest.mark.asyncio
async def test_base62_encoding():
    """Test Base62 encoding and decoding."""
    generator = ShortCodeGenerator()
    
    # Test encode/decode cycle
    test_numbers = [0, 1, 100, 1000, 12345, 916132831]
    
    for num in test_numbers:
        encoded = generator.encode_number(num)
        decoded = generator.decode_to_number(encoded)
        assert decoded == num

