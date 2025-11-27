"""
Main API Router Module.

This module aggregates all API endpoint routers for version 1 of the API.
"""

from fastapi import APIRouter

from app.api.v1.endpoints import urls, health

# Create main API router
api_router = APIRouter()

# Include endpoint routers
api_router.include_router(
    health.router,
    tags=["health"],
)

api_router.include_router(
    urls.router,
    prefix="/urls",
    tags=["urls"],
)

