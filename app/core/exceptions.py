"""
Custom Exception Classes Module.

This module defines application-specific exceptions for better error handling
and consistent error responses across the application.
"""

from typing import Any


class URLShortenerException(Exception):
    """Base exception for URL Shortener application."""
    
    def __init__(self, message: str, status_code: int = 500, details: Any = None) -> None:
        """
        Initialize exception.
        
        Args:
            message: Error message
            status_code: HTTP status code
            details: Additional error details
        """
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class URLNotFoundException(URLShortenerException):
    """Raised when a short code is not found in the database."""
    
    def __init__(self, short_code: str) -> None:
        """
        Initialize exception.
        
        Args:
            short_code: The short code that was not found
        """
        super().__init__(
            message=f"URL with short code '{short_code}' not found",
            status_code=404,
            details={"short_code": short_code}
        )


class InvalidURLException(URLShortenerException):
    """Raised when an invalid URL is provided."""
    
    def __init__(self, url: str, reason: str = "Invalid URL format") -> None:
        """
        Initialize exception.
        
        Args:
            url: The invalid URL
            reason: Reason why URL is invalid
        """
        super().__init__(
            message=reason,
            status_code=400,
            details={"url": url, "reason": reason}
        )


class URLTooLongException(URLShortenerException):
    """Raised when URL exceeds maximum length."""
    
    def __init__(self, url_length: int, max_length: int) -> None:
        """
        Initialize exception.
        
        Args:
            url_length: Length of the provided URL
            max_length: Maximum allowed URL length
        """
        super().__init__(
            message=f"URL length ({url_length}) exceeds maximum allowed length ({max_length})",
            status_code=400,
            details={"url_length": url_length, "max_length": max_length}
        )


class ShortCodeGenerationException(URLShortenerException):
    """Raised when unable to generate a unique short code after retries."""
    
    def __init__(self, retries: int) -> None:
        """
        Initialize exception.
        
        Args:
            retries: Number of retries attempted
        """
        super().__init__(
            message=f"Failed to generate unique short code after {retries} attempts",
            status_code=500,
            details={"retries": retries}
        )


class DatabaseException(URLShortenerException):
    """Raised when a database operation fails."""
    
    def __init__(self, operation: str, details: Any = None) -> None:
        """
        Initialize exception.
        
        Args:
            operation: The database operation that failed
            details: Additional error details
        """
        super().__init__(
            message=f"Database operation failed: {operation}",
            status_code=500,
            details={"operation": operation, "details": details}
        )


class CacheException(URLShortenerException):
    """Raised when a cache operation fails."""
    
    def __init__(self, operation: str, details: Any = None) -> None:
        """
        Initialize exception.
        
        Args:
            operation: The cache operation that failed
            details: Additional error details
        """
        super().__init__(
            message=f"Cache operation failed: {operation}",
            status_code=500,
            details={"operation": operation, "details": details}
        )


class RateLimitException(URLShortenerException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, limit: int, window: str = "minute") -> None:
        """
        Initialize exception.
        
        Args:
            limit: Rate limit threshold
            window: Time window for the limit
        """
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=429,
            details={"limit": limit, "window": window}
        )

