"""
Health Check Endpoint Module.

Provides endpoints for monitoring application health and service status.
"""

from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_database_session
from app.core.redis import redis_manager
from app.schemas.url import HealthCheckResponse

router = APIRouter()


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Health Check",
    description="Check the health status of the application and its dependencies"
)
async def health_check(
    db: AsyncSession = Depends(get_database_session)
) -> HealthCheckResponse:
    """
    Health check endpoint.
    
    Checks the status of:
    - Database connection
    - Redis connection
    
    Returns:
        HealthCheckResponse: Health status of all services
    """
    # Check database connection
    db_status = "connected"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "disconnected"
    
    # Check Redis connection
    redis_status = "connected" if await redis_manager.ping() else "disconnected"
    
    # Determine overall status
    overall_status = (
        "healthy"
        if db_status == "connected" and redis_status == "connected"
        else "unhealthy"
    )
    
    return HealthCheckResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        timestamp=datetime.utcnow()
    )

