"""
Organization models for multi-tenancy support
Using incremental bigint IDs
"""
from sqlalchemy import Column, String, Integer, JSON, Boolean, Enum, ForeignKey, BigInteger, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class OrganizationRole(str, enum.Enum):
    """Organization member role"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class OrganizationStatus(str, enum.Enum):
    """Organization status"""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DELETED = "deleted"


class Organization(Base):
    """Organization model for multi-tenancy"""

    __tablename__ = "organizations"

    # Basic Info
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    logo_url = Column(String(500))
    description = Column(String(1000))
    website = Column(String(255))

    # Status
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False)

    # Billing
    billing_email = Column(String(255))
    tax_id = Column(String(100))
    billing_address = Column(JSON, default={})

    # Limits
    max_users = Column(Integer, default=5, nullable=False)
    max_api_keys = Column(Integer, default=10, nullable=False)
    max_webhooks = Column(Integer, default=10, nullable=False)
    storage_limit = Column(Integer, default=5120, nullable=False)  # MB

    # Credits (shared among organization)
    credits = Column(Integer, default=0, nullable=False)

    # Settings
    settings = Column(JSON, default={}, nullable=False)
    features = Column(JSON, default=[], nullable=False)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    members = relationship(
        "OrganizationMember",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    api_keys = relationship(
        "ApiKey",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    webhooks = relationship(
        "Webhook",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    subscriptions = relationship(
        "Subscription",
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, slug={self.slug})>"


class OrganizationMember(Base):
    """Organization membership"""

    __tablename__ = "organization_members"

    # Foreign Keys (using BigInteger for incremental IDs)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)

    # Role
    role = Column(Enum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", back_populates="organizations")
    organization = relationship("Organization", back_populates="members")

    def __repr__(self):
        return f"<OrganizationMember(user_id={self.user_id}, org_id={self.organization_id}, role={self.role})>"


class OrganizationInvitation(Base):
    """Organization invitation for new members"""

    __tablename__ = "organization_invitations"

    # Foreign Keys
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    invited_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Invitation Details
    email = Column(String(255), nullable=False)
    role = Column(Enum(OrganizationRole), default=OrganizationRole.MEMBER, nullable=False)

    # Token
    token = Column(String(255), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Status
    accepted = Column(Boolean, default=False, nullable=False)
    accepted_at = Column(DateTime(timezone=True))

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<OrganizationInvitation(email={self.email}, org_id={self.organization_id})>"
