"""
URL Model Module.

This module defines the SQLAlchemy model for URL mappings based on the
database schema defined in docs/database/database-design.dbml.
"""

from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class URL(Base):
    """
    URL mapping model for storing short code to original URL mappings.
    
    This model implements the schema defined in database-design.dbml:
    - Stores original URLs with unique constraint
    - Generates unique 5-character short codes
    - Tracks click count and last accessed time for analytics
    
    Attributes:
        id: Primary key (auto-increment integer)
        original_url: The full original URL (unique, not null)
        short_code: The 5-character short code (unique, not null)
        created_at: Timestamp when URL was created (not null, default: now)
        click_count: Number of times the short URL was accessed (default: 0)
        last_accessed_at: Timestamp of last access (nullable)
    """
    
    __tablename__ = "urls"
    
    # Primary key
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        nullable=False,
        comment="Primary key"
    )
    
    # Original URL (unique, max 2048 chars)
    original_url: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        unique=True,
        index=True,
        comment="The full original URL"
    )
    
    # Short code (5 characters, unique)
    short_code: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        unique=True,
        index=True,
        comment="The 5-character short code"
    )
    
    # Created timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when URL was created"
    )
    
    # Click counter for analytics
    click_count: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        default=0,
        server_default="0",
        comment="Number of times the short URL was accessed"
    )
    
    # Last accessed timestamp
    last_accessed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last access"
    )
    
    # Additional indexes for performance
    __table_args__ = (
        Index("idx_short_code_created", "short_code", "created_at"),
        Index("idx_created_clicks", "created_at", "click_count"),
    )
    
    def __repr__(self) -> str:
        """String representation of URL model."""
        return (
            f"<URL(id={self.id}, short_code='{self.short_code}', "
            f"clicks={self.click_count})>"
        )
    
    def to_dict(self) -> dict:
        """
        Convert model to dictionary.
        
        Returns:
            dict: Dictionary representation of the URL model
        """
        return {
            "id": self.id,
            "original_url": self.original_url,
            "short_code": self.short_code,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "click_count": self.click_count,
            "last_accessed_at": (
                self.last_accessed_at.isoformat() if self.last_accessed_at else None
            ),
        }

