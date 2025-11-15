"""
User model with incremental bigint ID
"""
from sqlalchemy import Column, String, Boolean, Enum, JSON, Integer, DateTime, BigInteger
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class UserRole(str, enum.Enum):
    """User role enumeration"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"


class UserStatus(str, enum.Enum):
    """User status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class User(Base):
    """User model with incremental bigint ID"""

    __tablename__ = "users"

    # Authentication
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Profile
    full_name = Column(String(255))
    avatar_url = Column(String(500))
    phone_number = Column(String(20))
    company_name = Column(String(255))
    bio = Column(String(1000))

    # Status and Role
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True))

    # Two-Factor Authentication
    two_factor_enabled = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(String(255))

    # Limits and Quotas
    api_rate_limit = Column(Integer, default=1000, nullable=False)  # requests per hour
    storage_limit = Column(Integer, default=1024, nullable=False)  # MB
    max_api_keys = Column(Integer, default=5, nullable=False)
    max_webhooks = Column(Integer, default=5, nullable=False)

    # Credits
    credits = Column(Integer, default=0, nullable=False)

    # Login Tracking
    last_login_at = Column(DateTime(timezone=True))
    last_login_ip = Column(String(45))  # IPv6 support
    login_count = Column(Integer, default=0, nullable=False)
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime(timezone=True))

    # Settings
    preferences = Column(JSON, default={}, nullable=False)
    notification_settings = Column(JSON, default={
        "email": True,
        "webhook": True,
        "in_app": True
    }, nullable=False)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    api_keys = relationship(
        "ApiKey",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    webhooks = relationship(
        "Webhook",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    audit_logs = relationship(
        "AuditLog",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    organizations = relationship(
        "OrganizationMember",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    payments = relationship(
        "Payment",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"

    def to_dict(self):
        """Convert to dictionary, excluding sensitive fields"""
        return {
            "id": self.id,
            "email": self.email,
            "username": self.username,
            "full_name": self.full_name,
            "avatar_url": self.avatar_url,
            "phone_number": self.phone_number,
            "company_name": self.company_name,
            "bio": self.bio,
            "role": self.role.value,
            "status": self.status.value,
            "email_verified": self.email_verified,
            "two_factor_enabled": self.two_factor_enabled,
            "credits": self.credits,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
