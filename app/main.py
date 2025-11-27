"""
Main Application Module.

This module initializes and configures the FastAPI application with all
necessary middleware, routers, and lifecycle event handlers.
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from fastapi import FastAPI, Request, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.core.database import database_manager
from app.core.redis import redis_manager
from app.core.logging import setup_logging
from app.core.exceptions import URLShortenerException
from app.api.v1.router import api_router
from app.services.url_service import URLService
from app.core.dependencies import get_database_session

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for initializing and cleaning up
    database and Redis connections.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize database
    database_manager.init()
    logger.info("Database initialized")
    
    # Initialize Redis
    redis_manager.init()
    logger.info("Redis initialized")
    
    # Health check
    if await redis_manager.ping():
        logger.info("Redis connection established")
    else:
        logger.warning("Redis connection failed")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await database_manager.close()
    await redis_manager.close()
    logger.info("Cleanup complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="A professional, scalable URL shortener service",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(URLShortenerException)
async def url_shortener_exception_handler(
    request: Request,
    exc: URLShortenerException
) -> JSONResponse:
    """Handle custom URL shortener exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.message,
            "details": exc.details,
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
) -> JSONResponse:
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation error",
            "details": exc.errors(),
        }
    )


# Include API routers
app.include_router(
    api_router,
    prefix="/api/v1"
)


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint redirecting to API documentation."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
        "health": "/api/v1/health"
    }


@app.get("/{short_code}", include_in_schema=False)
@limiter.limit(f"{settings.RATE_LIMIT_PER_MINUTE}/minute")
async def redirect_to_url(
    short_code: str,
    request: Request
) -> RedirectResponse:
    """
    Redirect short code to original URL.
    
    This endpoint handles the core redirection functionality.
    When a user accesses a short URL, they are redirected to the original URL.
    
    Args:
        short_code: The short code from the URL path
        request: FastAPI request object
        
    Returns:
        RedirectResponse: 307 redirect to original URL
        
    Raises:
        HTTPException: 404 if short code not found
    """
    try:
        # Get database session
        async for db in get_database_session():
            # Create URL service
            url_service = URLService(db_session=db, redis_manager=redis_manager)
            
            # Get original URL
            original_url = await url_service.get_original_url(short_code)
            
            logger.info(f"Redirecting {short_code} -> {original_url}")
            
            # 307 Temporary Redirect (preserves HTTP method)
            return RedirectResponse(
                url=original_url,
                status_code=status.HTTP_307_TEMPORARY_REDIRECT
            )
    except Exception as e:
        logger.error(f"Error redirecting: {e}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Short code '{short_code}' not found"}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )

