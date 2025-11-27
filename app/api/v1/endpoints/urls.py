"""
URL Shortening Endpoints Module.

Provides API endpoints for URL shortening, redirection, and statistics.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.url import URLCreateRequest, URLCreateResponse, URLStatsResponse
from app.services.url_service import URLService
from app.core.dependencies import get_database_session
from app.core.redis import redis_manager
from app.core.config import settings
from app.core.exceptions import (
    URLNotFoundException,
    InvalidURLException,
    URLTooLongException,
    ShortCodeGenerationException,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_url_service(
    db: AsyncSession = Depends(get_database_session)
) -> URLService:
    """
    Dependency for URL service.
    
    Args:
        db: Database session
        
    Returns:
        URLService: Configured URL service instance
    """
    return URLService(db_session=db, redis_manager=redis_manager)


@router.post(
    "/shorten",
    response_model=URLCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Shorten URL",
    description="Create a shortened URL from a long URL"
)
async def shorten_url(
    request: URLCreateRequest,
    url_service: URLService = Depends(get_url_service)
) -> URLCreateResponse:
    """
    Create a shortened URL.
    
    Takes a long URL and returns a shortened version with a unique 5-character code.
    If the URL has been shortened before, returns the existing short code.
    
    Args:
        request: URL shortening request containing the original URL
        url_service: URL service instance
        
    Returns:
        URLCreateResponse: Created short URL with metadata
        
    Raises:
        HTTPException: 400 for invalid URL, 500 for server errors
    """
    try:
        # Create short URL
        url = await url_service.create_short_url(str(request.original_url))
        
        # Build short URL
        short_url = f"{settings.BASE_URL}/{url.short_code}"
        
        return URLCreateResponse(
            short_code=url.short_code,
            short_url=short_url,
            original_url=url.original_url,
            created_at=url.created_at
        )
        
    except InvalidURLException as e:
        logger.warning(f"Invalid URL: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except URLTooLongException as e:
        logger.warning(f"URL too long: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
        )
    except ShortCodeGenerationException as e:
        logger.error(f"Failed to generate short code: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate unique short code. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error shortening URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/{short_code}/stats",
    response_model=URLStatsResponse,
    summary="Get URL Statistics",
    description="Retrieve statistics for a shortened URL"
)
async def get_url_statistics(
    short_code: str,
    url_service: URLService = Depends(get_url_service)
) -> URLStatsResponse:
    """
    Get URL statistics.
    
    Returns detailed statistics about a shortened URL including:
    - Number of clicks/redirects
    - Creation timestamp
    - Last accessed timestamp
    
    Args:
        short_code: The short code to get statistics for
        url_service: URL service instance
        
    Returns:
        URLStatsResponse: URL statistics
        
    Raises:
        HTTPException: 404 if short code not found
    """
    try:
        url = await url_service.get_url_stats(short_code)
        
        return URLStatsResponse(
            short_code=url.short_code,
            original_url=url.original_url,
            click_count=url.click_count,
            created_at=url.created_at,
            last_accessed_at=url.last_accessed_at
        )
        
    except URLNotFoundException as e:
        logger.warning(f"URL not found: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error getting URL stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

