"""
URL Repository Module.

This module provides the Data Access Layer (DAL) for URL operations,
handling all database interactions related to URL mappings.
"""

from datetime import datetime
from typing import Optional
import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.models.url import URL
from app.core.exceptions import DatabaseException

logger = logging.getLogger(__name__)


class URLRepository:
    """
    Repository for URL database operations.
    
    Provides methods for CRUD operations on URL mappings with proper
    error handling and logging.
    """
    
    def __init__(self, session: AsyncSession) -> None:
        """
        Initialize URL repository.
        
        Args:
            session: Database session for executing queries
        """
        self.session = session
    
    async def create_url(
        self,
        original_url: str,
        short_code: str
    ) -> URL:
        """
        Create a new URL mapping in the database.
        
        Args:
            original_url: The original URL to be shortened
            short_code: The generated short code
            
        Returns:
            URL: Created URL model instance
            
        Raises:
            DatabaseException: If creation fails or short code already exists
        """
        try:
            url = URL(
                original_url=original_url,
                short_code=short_code,
                click_count=0
            )
            self.session.add(url)
            await self.session.flush()
            await self.session.refresh(url)
            
            logger.info(
                f"Created URL mapping: short_code='{short_code}', "
                f"original_url='{original_url}'"
            )
            return url
            
        except IntegrityError as e:
            await self.session.rollback()
            logger.error(f"Integrity error creating URL: {e}")
            raise DatabaseException(
                operation="create_url",
                details=f"Short code '{short_code}' or URL already exists"
            )
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error creating URL: {e}")
            raise DatabaseException(operation="create_url", details=str(e))
    
    async def get_by_short_code(self, short_code: str) -> Optional[URL]:
        """
        Retrieve URL by short code.
        
        Args:
            short_code: The short code to look up
            
        Returns:
            URL model instance if found, None otherwise
            
        Raises:
            DatabaseException: If database query fails
        """
        try:
            stmt = select(URL).where(URL.short_code == short_code)
            result = await self.session.execute(stmt)
            url = result.scalar_one_or_none()
            
            if url:
                logger.debug(f"Found URL for short_code='{short_code}'")
            else:
                logger.debug(f"No URL found for short_code='{short_code}'")
            
            return url
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting URL by short code: {e}")
            raise DatabaseException(operation="get_by_short_code", details=str(e))
    
    async def get_by_original_url(self, original_url: str) -> Optional[URL]:
        """
        Retrieve URL by original URL.
        
        Useful for checking if a URL has already been shortened.
        
        Args:
            original_url: The original URL to look up
            
        Returns:
            URL model instance if found, None otherwise
            
        Raises:
            DatabaseException: If database query fails
        """
        try:
            stmt = select(URL).where(URL.original_url == original_url)
            result = await self.session.execute(stmt)
            url = result.scalar_one_or_none()
            
            if url:
                logger.debug(f"Found existing URL mapping for '{original_url}'")
            
            return url
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting URL by original URL: {e}")
            raise DatabaseException(operation="get_by_original_url", details=str(e))
    
    async def check_short_code_exists(self, short_code: str) -> bool:
        """
        Check if a short code already exists in the database.
        
        Args:
            short_code: The short code to check
            
        Returns:
            bool: True if exists, False otherwise
            
        Raises:
            DatabaseException: If database query fails
        """
        try:
            stmt = select(URL.id).where(URL.short_code == short_code)
            result = await self.session.execute(stmt)
            exists = result.scalar_one_or_none() is not None
            
            logger.debug(f"Short code '{short_code}' exists: {exists}")
            return exists
            
        except SQLAlchemyError as e:
            logger.error(f"Database error checking short code existence: {e}")
            raise DatabaseException(operation="check_short_code_exists", details=str(e))
    
    async def increment_click_count(self, short_code: str) -> bool:
        """
        Increment the click count and update last accessed timestamp.
        
        Args:
            short_code: The short code to update
            
        Returns:
            bool: True if updated successfully, False otherwise
            
        Raises:
            DatabaseException: If database update fails
        """
        try:
            stmt = (
                update(URL)
                .where(URL.short_code == short_code)
                .values(
                    click_count=URL.click_count + 1,
                    last_accessed_at=datetime.utcnow()
                )
            )
            result = await self.session.execute(stmt)
            await self.session.commit()
            
            updated = result.rowcount > 0
            if updated:
                logger.debug(f"Incremented click count for short_code='{short_code}'")
            else:
                logger.warning(f"No URL found to increment for short_code='{short_code}'")
            
            return updated
            
        except SQLAlchemyError as e:
            await self.session.rollback()
            logger.error(f"Database error incrementing click count: {e}")
            raise DatabaseException(operation="increment_click_count", details=str(e))
    
    async def get_url_stats(self, short_code: str) -> Optional[URL]:
        """
        Get URL statistics including click count and timestamps.
        
        Args:
            short_code: The short code to get stats for
            
        Returns:
            URL model instance with statistics if found, None otherwise
            
        Raises:
            DatabaseException: If database query fails
        """
        try:
            stmt = select(URL).where(URL.short_code == short_code)
            result = await self.session.execute(stmt)
            url = result.scalar_one_or_none()
            
            if url:
                logger.debug(
                    f"Retrieved stats for short_code='{short_code}': "
                    f"clicks={url.click_count}"
                )
            
            return url
            
        except SQLAlchemyError as e:
            logger.error(f"Database error getting URL stats: {e}")
            raise DatabaseException(operation="get_url_stats", details=str(e))

