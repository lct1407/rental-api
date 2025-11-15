"""
API Key model with incremental bigint ID
"""
from sqlalchemy import Column, String, Integer, JSON, Boolean, DateTime, ForeignKey, BigInteger, Text
from sqlalchemy.orm import relationship
from app.database import Base


class ApiKey(Base):
    """API Key model for authentication"""

    __tablename__ = "api_keys"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    # Key Details
    name = Column(String(255), nullable=False)
    key_hash = Column(String(255), unique=True, index=True, nullable=False)
    key_prefix = Column(String(20), index=True, nullable=False)  # First 8 chars for identification
    last_four = Column(String(10), nullable=False)

    # Permissions and Scopes
    scopes = Column(JSON, default=[], nullable=False)
    ip_whitelist = Column(JSON, default=[], nullable=False)
    allowed_origins = Column(JSON, default=[], nullable=False)

    # Rate Limiting
    rate_limit_per_hour = Column(Integer, default=1000, nullable=False)
    rate_limit_per_day = Column(Integer, default=10000, nullable=False)
    rate_limit_per_month = Column(Integer, default=100000, nullable=False)

    # Usage Tracking
    last_used_at = Column(DateTime(timezone=True))
    last_used_ip = Column(String(45))
    usage_count = Column(Integer, default=0, nullable=False)

    # Expiration
    expires_at = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)
    description = Column(Text)

    # Relationships
    user = relationship("User", back_populates="api_keys")
    organization = relationship("Organization", back_populates="api_keys")
    usage_logs = relationship(
        "ApiUsageLog",
        back_populates="api_key",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<ApiKey(id={self.id}, name={self.name}, user_id={self.user_id})>"

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            "id": self.id,
            "name": self.name,
            "key_prefix": self.key_prefix,
            "last_four": self.last_four,
            "scopes": self.scopes,
            "is_active": self.is_active,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "usage_count": self.usage_count,
        }

        if include_sensitive:
            data["key_hash"] = self.key_hash

        return data
