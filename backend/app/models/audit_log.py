"""
Audit log model with incremental bigint ID
Tracks all important system actions for security and compliance
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, BigInteger, Text, Index, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class AuditAction(str, enum.Enum):
    """Audit action types"""
    # User actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_LOGIN_FAILED = "user_login_failed"
    USER_PASSWORD_CHANGED = "user_password_changed"
    USER_EMAIL_VERIFIED = "user_email_verified"
    USER_2FA_ENABLED = "user_2fa_enabled"
    USER_2FA_DISABLED = "user_2fa_disabled"

    # API Key actions
    API_KEY_CREATED = "api_key_created"
    API_KEY_UPDATED = "api_key_updated"
    API_KEY_DELETED = "api_key_deleted"
    API_KEY_ROTATED = "api_key_rotated"

    # Webhook actions
    WEBHOOK_CREATED = "webhook_created"
    WEBHOOK_UPDATED = "webhook_updated"
    WEBHOOK_DELETED = "webhook_deleted"

    # Organization actions
    ORG_CREATED = "org_created"
    ORG_UPDATED = "org_updated"
    ORG_DELETED = "org_deleted"
    ORG_MEMBER_ADDED = "org_member_added"
    ORG_MEMBER_REMOVED = "org_member_removed"
    ORG_MEMBER_ROLE_CHANGED = "org_member_role_changed"

    # Payment actions
    PAYMENT_CREATED = "payment_created"
    PAYMENT_SUCCEEDED = "payment_succeeded"
    PAYMENT_FAILED = "payment_failed"
    PAYMENT_REFUNDED = "payment_refunded"

    # Subscription actions
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELED = "subscription_canceled"

    # Admin actions
    USER_SUSPENDED = "user_suspended"
    USER_UNSUSPENDED = "user_unsuspended"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    MAINTENANCE_MODE_ENABLED = "maintenance_mode_enabled"
    MAINTENANCE_MODE_DISABLED = "maintenance_mode_disabled"

    # Security actions
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class AuditLog(Base):
    """Audit log for tracking system actions"""

    __tablename__ = "audit_logs"

    # Foreign Keys (nullable because some actions may not have a user)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)

    # Action Details
    action = Column(Enum(AuditAction), index=True, nullable=False)
    resource_type = Column(String(100), index=True)
    resource_id = Column(BigInteger)
    description = Column(Text)

    # Request Context
    ip_address = Column(String(45), index=True)
    user_agent = Column(String(500))

    # Changes
    old_values = Column(JSON)
    new_values = Column(JSON)

    # Status
    success = Column(Column(String(50), default=True, nullable=False))
    error_message = Column(Text)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", back_populates="audit_logs")

    # Indexes for better query performance
    __table_args__ = (
        Index('idx_audit_user_created', 'user_id', 'created_at'),
        Index('idx_audit_action_created', 'action', 'created_at'),
        Index('idx_audit_resource_created', 'resource_type', 'resource_id', 'created_at'),
        Index('idx_audit_ip_created', 'ip_address', 'created_at'),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, user_id={self.user_id})>"


class SecurityEvent(Base):
    """Security-specific events"""

    __tablename__ = "security_events"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Event Details
    event_type = Column(String(100), index=True, nullable=False)
    severity = Column(String(20), index=True, nullable=False)  # low, medium, high, critical
    description = Column(Text, nullable=False)

    # Context
    ip_address = Column(String(45), index=True)
    user_agent = Column(String(500))
    endpoint = Column(String(500))

    # Status
    resolved = Column(Column(String(50), default=False, nullable=False))
    resolved_at = Column(DateTime(timezone=True))
    resolved_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"))

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_security_type_created', 'event_type', 'created_at'),
        Index('idx_security_severity_created', 'severity', 'created_at'),
    )

    def __repr__(self):
        return f"<SecurityEvent(id={self.id}, type={self.event_type}, severity={self.severity})>"
