"""
Short Code Generator Module.

This module provides the URL shortening algorithm using Base62 encoding
to generate unique 5-character short codes.
"""

import random
import string
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


class ShortCodeGenerator:
    """
    Generates unique short codes for URLs using Base62 encoding.
    
    Base62 uses: a-z (26) + A-Z (26) + 0-9 (10) = 62 characters
    With 5 characters: 62^5 = 916,132,832 possible unique codes
    """
    
    # Base62 character set: a-z, A-Z, 0-9
    BASE62_CHARS = string.ascii_letters + string.digits  # a-zA-Z0-9
    
    def __init__(self) -> None:
        """Initialize short code generator."""
        self.code_length = settings.SHORT_CODE_LENGTH
    
    def generate(self) -> str:
        """
        Generate a random short code.
        
        Uses random selection from Base62 character set to create
        a 5-character code.
        
        Returns:
            str: Generated short code (e.g., "aB3xY")
            
        Example:
            >>> generator = ShortCodeGenerator()
            >>> code = generator.generate()
            >>> len(code)
            5
            >>> all(c in ShortCodeGenerator.BASE62_CHARS for c in code)
            True
        """
        code = ''.join(
            random.choices(
                self.BASE62_CHARS,
                k=self.code_length
            )
        )
        
        logger.debug(f"Generated short code: {code}")
        return code
    
    def is_valid(self, code: str) -> bool:
        """
        Validate if a code matches the expected format.
        
        Args:
            code: Code to validate
            
        Returns:
            bool: True if valid, False otherwise
            
        Example:
            >>> generator = ShortCodeGenerator()
            >>> generator.is_valid("aB3xY")
            True
            >>> generator.is_valid("aB3")
            False
            >>> generator.is_valid("aB3x!")
            False
        """
        if len(code) != self.code_length:
            return False
        
        return all(c in self.BASE62_CHARS for c in code)
    
    @staticmethod
    def encode_number(num: int) -> str:
        """
        Encode a number to Base62 string.
        
        This is an alternative method that can be used for
        sequential ID-based encoding instead of random generation.
        
        Args:
            num: Number to encode
            
        Returns:
            str: Base62 encoded string
            
        Example:
            >>> ShortCodeGenerator.encode_number(12345)
            '3D7'
            >>> ShortCodeGenerator.encode_number(916132831)  # Max for 5 chars
            'zzzzz'
        """
        if num == 0:
            return ShortCodeGenerator.BASE62_CHARS[0]
        
        result = []
        base = len(ShortCodeGenerator.BASE62_CHARS)
        
        while num > 0:
            num, remainder = divmod(num, base)
            result.append(ShortCodeGenerator.BASE62_CHARS[remainder])
        
        return ''.join(reversed(result))
    
    @staticmethod
    def decode_to_number(code: str) -> int:
        """
        Decode a Base62 string to number.
        
        Args:
            code: Base62 encoded string
            
        Returns:
            int: Decoded number
            
        Example:
            >>> ShortCodeGenerator.decode_to_number('3D7')
            12345
        """
        base = len(ShortCodeGenerator.BASE62_CHARS)
        num = 0
        
        for char in code:
            num = num * base + ShortCodeGenerator.BASE62_CHARS.index(char)
        
        return num

