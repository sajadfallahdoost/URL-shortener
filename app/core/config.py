"""
Application Configuration Module.

This module handles all configuration management using Pydantic Settings,
supporting environment-based configuration for development, staging, and production.
"""

from typing import Literal
from pydantic import Field, PostgresDsn, RedisDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    Attributes:
        APP_NAME: Application name
        APP_VERSION: Application version
        ENVIRONMENT: Current environment (development, staging, production)
        DEBUG: Debug mode flag
        HOST: Server host address
        PORT: Server port
        BASE_URL: Base URL for generating short URLs
        
        DATABASE_URL: PostgreSQL connection string
        DB_POOL_SIZE: Database connection pool size
        DB_MAX_OVERFLOW: Maximum overflow connections
        
        REDIS_URL: Redis connection string
        REDIS_CACHE_TTL: Cache time-to-live in seconds (default: 24 hours)
        
        RATE_LIMIT_PER_MINUTE: Rate limit per minute per IP
        REQUEST_TIMEOUT: Request timeout in seconds
        
        LOG_LEVEL: Logging level
        CORS_ORIGINS: Allowed CORS origins (comma-separated)
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application Settings
    APP_NAME: str = Field(default="URL Shortener", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    ENVIRONMENT: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Current environment"
    )
    DEBUG: bool = Field(default=True, description="Debug mode")
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    BASE_URL: str = Field(default="http://localhost:8000", description="Base URL for short URLs")
    
    # Database Settings
    DATABASE_URL: PostgresDsn = Field(
        default="postgresql+asyncpg://url_shortner_user:sdjnnfejsajad3574nndfkd@localhost:5432/url_shortner",
        description="PostgreSQL connection string"
    )
    DB_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DB_MAX_OVERFLOW: int = Field(default=10, description="Maximum overflow connections")
    DB_ECHO: bool = Field(default=False, description="Echo SQL statements")
    
    # Redis Settings
    REDIS_URL: RedisDsn = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    REDIS_CACHE_TTL: int = Field(default=86400, description="Cache TTL in seconds (24 hours)")
    REDIS_MAX_CONNECTIONS: int = Field(default=50, description="Maximum Redis connections")
    
    # Security & Performance
    RATE_LIMIT_PER_MINUTE: int = Field(default=100, description="Rate limit per IP per minute")
    REQUEST_TIMEOUT: int = Field(default=30, description="Request timeout in seconds")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Logging level")
    
    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:3000,http://localhost:8000",
        description="Allowed CORS origins (comma-separated)"
    )
    
    # URL Shortener Specific
    SHORT_CODE_LENGTH: int = Field(default=5, description="Length of short codes")
    MAX_URL_LENGTH: int = Field(default=2048, description="Maximum URL length")
    MAX_COLLISION_RETRIES: int = Field(default=3, description="Max retries for collision detection")
    
    @field_validator("CORS_ORIGINS")
    @classmethod
    def parse_cors_origins(cls, v: str) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"


# Global settings instance
settings = Settings()

