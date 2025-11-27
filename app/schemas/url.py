"""
URL Schemas Module.

This module defines Pydantic schemas for URL-related API requests and responses,
including validation rules and serialization logic.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator

from app.core.config import settings


class URLBase(BaseModel):
    """Base schema for URL with common fields."""
    
    original_url: HttpUrl = Field(
        ...,
        description="The original URL to be shortened",
        examples=["https://www.example.com/very/long/path/to/page"]
    )


class URLCreateRequest(URLBase):
    """
    Schema for URL shortening request.
    
    Validates that the provided URL is valid and within length limits.
    """
    
    @field_validator("original_url")
    @classmethod
    def validate_url_length(cls, v: HttpUrl) -> HttpUrl:
        """
        Validate URL length.
        
        Args:
            v: URL to validate
            
        Returns:
            HttpUrl: Validated URL
            
        Raises:
            ValueError: If URL exceeds maximum length
        """
        url_str = str(v)
        if len(url_str) > settings.MAX_URL_LENGTH:
            raise ValueError(
                f"URL length ({len(url_str)}) exceeds maximum allowed "
                f"length ({settings.MAX_URL_LENGTH})"
            )
        return v
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "original_url": "https://www.example.com/very/long/path/to/page"
            }
        }


class URLCreateResponse(BaseModel):
    """
    Schema for URL shortening response.
    
    Returns the short URL along with metadata about the created mapping.
    """
    
    short_code: str = Field(
        ...,
        description="The generated short code",
        min_length=5,
        max_length=5,
        examples=["aB3xY"]
    )
    
    short_url: str = Field(
        ...,
        description="The complete shortened URL",
        examples=["http://localhost:8000/aB3xY"]
    )
    
    original_url: str = Field(
        ...,
        description="The original URL",
        examples=["https://www.example.com/very/long/path/to/page"]
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when the URL was created"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "short_code": "aB3xY",
                "short_url": "http://localhost:8000/aB3xY",
                "original_url": "https://www.example.com/very/long/path/to/page",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }


class URLStatsResponse(BaseModel):
    """
    Schema for URL statistics response.
    
    Provides analytics data about a shortened URL including click count
    and access timestamps.
    """
    
    short_code: str = Field(
        ...,
        description="The short code",
        examples=["aB3xY"]
    )
    
    original_url: str = Field(
        ...,
        description="The original URL",
        examples=["https://www.example.com/very/long/path/to/page"]
    )
    
    click_count: int = Field(
        ...,
        description="Number of times the short URL was accessed",
        ge=0
    )
    
    created_at: datetime = Field(
        ...,
        description="Timestamp when the URL was created"
    )
    
    last_accessed_at: Optional[datetime] = Field(
        None,
        description="Timestamp of last access (null if never accessed)"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "short_code": "aB3xY",
                "original_url": "https://www.example.com/very/long/path/to/page",
                "click_count": 42,
                "created_at": "2024-01-15T10:30:00Z",
                "last_accessed_at": "2024-01-15T14:20:00Z"
            }
        }


class HealthCheckResponse(BaseModel):
    """
    Schema for health check response.
    
    Indicates the health status of the application and its dependencies.
    """
    
    status: str = Field(
        ...,
        description="Overall health status",
        examples=["healthy"]
    )
    
    database: str = Field(
        ...,
        description="Database connection status",
        examples=["connected"]
    )
    
    redis: str = Field(
        ...,
        description="Redis connection status",
        examples=["connected"]
    )
    
    timestamp: datetime = Field(
        ...,
        description="Timestamp of health check"
    )
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database": "connected",
                "redis": "connected",
                "timestamp": "2024-01-15T10:30:00Z"
            }
        }

