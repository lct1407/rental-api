"""
Service model with incremental bigint ID
Represents available API services in the platform
"""
from sqlalchemy import Column, String, Integer, Boolean, Text
from app.database import Base


class Service(Base):
    """Service model for API service catalog"""

    __tablename__ = "services"

    # Service Details
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    endpoint = Column(String(500), nullable=False)
    description = Column(Text)

    # Billing
    credits_per_call = Column(Integer, default=1, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self):
        return f"<Service(id={self.id}, name={self.name}, slug={self.slug})>"

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "endpoint": self.endpoint,
            "description": self.description,
            "credits_per_call": self.credits_per_call,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
