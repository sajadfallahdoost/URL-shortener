"""
URL Service Module.

This module provides business logic for URL shortening operations,
including URL validation, short code generation, caching, and statistics.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.url import URL
from app.repositories.url_repository import URLRepository
from app.services.shortener import ShortCodeGenerator
from app.core.redis import RedisManager
from app.core.config import settings
from app.core.exceptions import (
    URLNotFoundException,
    InvalidURLException,
    ShortCodeGenerationException,
)
from app.utils.validators import URLValidator

logger = logging.getLogger(__name__)


class URLService:
    """
    Service for URL shortening operations.
    
    Handles business logic for creating short URLs, retrieving original URLs,
    managing cache, and providing statistics.
    """
    
    def __init__(
        self,
        db_session: AsyncSession,
        redis_manager: RedisManager
    ) -> None:
        """
        Initialize URL service.
        
        Args:
            db_session: Database session for persistence
            redis_manager: Redis manager for caching
        """
        self.repository = URLRepository(db_session)
        self.redis = redis_manager
        self.generator = ShortCodeGenerator()
        self.validator = URLValidator()
    
    async def create_short_url(self, original_url: str) -> URL:
        """
        Create a shortened URL.
        
        Steps:
        1. Validate the original URL
        2. Check if URL already exists (return existing if found)
        3. Generate unique short code
        4. Save to database
        5. Cache in Redis
        
        Args:
            original_url: The URL to shorten
            
        Returns:
            URL: Created or existing URL model instance
            
        Raises:
            InvalidURLException: If URL is invalid
            ShortCodeGenerationException: If unable to generate unique code
        """
        # Validate URL
        if not self.validator.is_valid_url(original_url):
            logger.warning(f"Invalid URL provided: {original_url}")
            raise InvalidURLException(original_url, "Invalid URL format")
        
        if not self.validator.is_safe_url(original_url):
            logger.warning(f"Unsafe URL provided: {original_url}")
            raise InvalidURLException(original_url, "URL appears to be malicious")
        
        # Check if URL already exists
        existing_url = await self.repository.get_by_original_url(original_url)
        if existing_url:
            logger.info(
                f"URL already exists: {original_url} -> {existing_url.short_code}"
            )
            # Refresh cache
            await self._cache_url(existing_url.short_code, original_url)
            return existing_url
        
        # Generate unique short code
        short_code = await self._generate_unique_short_code()
        
        # Create URL mapping in database
        url = await self.repository.create_url(original_url, short_code)
        
        # Cache in Redis
        await self._cache_url(short_code, original_url)
        
        logger.info(f"Created short URL: {original_url} -> {short_code}")
        return url
    
    async def get_original_url(self, short_code: str) -> str:
        """
        Get original URL from short code with caching.
        
        Implements read-through cache pattern:
        1. Check Redis cache
        2. If not found, query database
        3. Update cache
        4. Increment click count asynchronously
        
        Args:
            short_code: The short code to resolve
            
        Returns:
            str: Original URL
            
        Raises:
            URLNotFoundException: If short code not found
        """
        # Check cache first
        cache_key = self._get_cache_key(short_code)
        cached_url = await self.redis.get(cache_key)
        
        if cached_url:
            logger.debug(f"Cache hit for short_code: {short_code}")
            # Increment click count in background
            await self.repository.increment_click_count(short_code)
            return cached_url
        
        # Cache miss - query database
        logger.debug(f"Cache miss for short_code: {short_code}")
        url = await self.repository.get_by_short_code(short_code)
        
        if not url:
            logger.warning(f"Short code not found: {short_code}")
            raise URLNotFoundException(short_code)
        
        # Update cache
        await self._cache_url(short_code, url.original_url)
        
        # Increment click count
        await self.repository.increment_click_count(short_code)
        
        logger.info(f"Resolved short code: {short_code} -> {url.original_url}")
        return url.original_url
    
    async def get_url_stats(self, short_code: str) -> URL:
        """
        Get URL statistics.
        
        Args:
            short_code: The short code to get stats for
            
        Returns:
            URL: URL model with statistics
            
        Raises:
            URLNotFoundException: If short code not found
        """
        url = await self.repository.get_url_stats(short_code)
        
        if not url:
            logger.warning(f"Short code not found for stats: {short_code}")
            raise URLNotFoundException(short_code)
        
        logger.debug(
            f"Retrieved stats for {short_code}: "
            f"clicks={url.click_count}, created={url.created_at}"
        )
        return url
    
    async def _generate_unique_short_code(self) -> str:
        """
        Generate a unique short code with collision detection.
        
        Attempts to generate a unique code, retrying if collision occurs.
        
        Returns:
            str: Unique short code
            
        Raises:
            ShortCodeGenerationException: If unable to generate after max retries
        """
        max_retries = settings.MAX_COLLISION_RETRIES
        
        for attempt in range(max_retries):
            short_code = self.generator.generate()
            
            # Check if code already exists
            exists = await self.repository.check_short_code_exists(short_code)
            
            if not exists:
                logger.debug(
                    f"Generated unique short code: {short_code} "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                return short_code
            
            logger.warning(
                f"Short code collision: {short_code} "
                f"(attempt {attempt + 1}/{max_retries})"
            )
        
        # Failed to generate unique code
        logger.error(f"Failed to generate unique short code after {max_retries} attempts")
        raise ShortCodeGenerationException(max_retries)
    
    async def _cache_url(self, short_code: str, original_url: str) -> None:
        """
        Cache URL mapping in Redis.
        
        Args:
            short_code: The short code
            original_url: The original URL
        """
        cache_key = self._get_cache_key(short_code)
        success = await self.redis.set(cache_key, original_url)
        
        if success:
            logger.debug(f"Cached URL: {cache_key} -> {original_url}")
        else:
            logger.warning(f"Failed to cache URL: {cache_key}")
    
    @staticmethod
    def _get_cache_key(short_code: str) -> str:
        """
        Get Redis cache key for short code.
        
        Args:
            short_code: The short code
            
        Returns:
            str: Cache key
        """
        return f"url:short:{short_code}"

