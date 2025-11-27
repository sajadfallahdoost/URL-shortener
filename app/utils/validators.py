"""
URL Validation Utilities Module.

This module provides utilities for validating URLs, checking for malicious
patterns, and ensuring URL safety.
"""

import re
import logging
from urllib.parse import urlparse
from typing import List

from app.core.config import settings

logger = logging.getLogger(__name__)


class URLValidator:
    """
    URL validation and safety checking utility.
    
    Provides methods to validate URL format, check for malicious patterns,
    and ensure URLs are safe to process.
    """
    
    # Blocked domains/patterns (for security)
    BLOCKED_PATTERNS: List[str] = [
        r"localhost",
        r"127\.0\.0\.1",
        r"0\.0\.0\.0",
        r"169\.254\.",  # Link-local addresses
        r"10\.",        # Private network
        r"172\.1[6-9]\.",  # Private network
        r"172\.2[0-9]\.",  # Private network
        r"172\.3[0-1]\.",  # Private network
        r"192\.168\.",  # Private network
    ]
    
    # Allowed schemes
    ALLOWED_SCHEMES = ["http", "https"]
    
    def is_valid_url(self, url: str) -> bool:
        """
        Validate URL format and basic requirements.
        
        Args:
            url: URL to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not url or not isinstance(url, str):
            return False
        
        # Check length
        if len(url) > settings.MAX_URL_LENGTH:
            logger.warning(f"URL exceeds maximum length: {len(url)} > {settings.MAX_URL_LENGTH}")
            return False
        
        # Parse URL
        try:
            parsed = urlparse(url)
        except Exception as e:
            logger.warning(f"Failed to parse URL: {e}")
            return False
        
        # Check scheme
        if parsed.scheme not in self.ALLOWED_SCHEMES:
            logger.warning(f"Invalid URL scheme: {parsed.scheme}")
            return False
        
        # Check if domain exists
        if not parsed.netloc:
            logger.warning("URL missing domain")
            return False
        
        return True
    
    def is_safe_url(self, url: str) -> bool:
        """
        Check if URL is safe (not pointing to blocked domains or local resources).
        
        Helps prevent SSRF (Server-Side Request Forgery) attacks.
        
        Args:
            url: URL to check
            
        Returns:
            bool: True if safe, False otherwise
        """
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower()
            
            # Remove port if present
            if ":" in host:
                host = host.split(":")[0]
            
            # Check against blocked patterns
            for pattern in self.BLOCKED_PATTERNS:
                if re.search(pattern, host, re.IGNORECASE):
                    logger.warning(f"URL blocked by pattern '{pattern}': {url}")
                    return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Error checking URL safety: {e}")
            return False
    
    def is_valid_short_code(self, code: str) -> bool:
        """
        Validate short code format.
        
        Args:
            code: Short code to validate
            
        Returns:
            bool: True if valid, False otherwise
        """
        if not code or not isinstance(code, str):
            return False
        
        if len(code) != settings.SHORT_CODE_LENGTH:
            return False
        
        # Check if alphanumeric
        return code.isalnum()
    
    def sanitize_url(self, url: str) -> str:
        """
        Sanitize URL by removing whitespace and ensuring proper format.
        
        Args:
            url: URL to sanitize
            
        Returns:
            str: Sanitized URL
        """
        # Remove leading/trailing whitespace
        url = url.strip()
        
        # Ensure scheme is present
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        return url

