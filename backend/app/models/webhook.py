"""
Webhook models with incremental bigint ID
"""
from sqlalchemy import Column, String, Integer, JSON, Boolean, DateTime, ForeignKey, BigInteger, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class WebhookStatus(str, enum.Enum):
    """Webhook delivery status"""
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class Webhook(Base):
    """Webhook configuration model"""

    __tablename__ = "webhooks"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    # Configuration
    name = Column(String(255), nullable=False)
    url = Column(String(500), nullable=False)
    secret = Column(String(255))
    events = Column(JSON, default=[], nullable=False)
    headers = Column(JSON, default={}, nullable=False)
    description = Column(Text)

    # Retry Configuration
    max_retries = Column(Integer, default=3, nullable=False)
    retry_delay = Column(Integer, default=60, nullable=False)  # seconds
    timeout = Column(Integer, default=30, nullable=False)  # seconds

    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    verified = Column(Boolean, default=False, nullable=False)

    # Statistics
    success_count = Column(Integer, default=0, nullable=False)
    failure_count = Column(Integer, default=0, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True))
    last_error = Column(Text)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", back_populates="webhooks")
    organization = relationship("Organization", back_populates="webhooks")
    deliveries = relationship(
        "WebhookDelivery",
        back_populates="webhook",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Webhook(id={self.id}, name={self.name}, url={self.url})>"


class WebhookDelivery(Base):
    """Webhook delivery log"""

    __tablename__ = "webhook_deliveries"

    # Foreign Keys
    webhook_id = Column(BigInteger, ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False)

    # Delivery Details
    event_type = Column(String(100), nullable=False)
    payload = Column(JSON, nullable=False)

    # Request
    request_headers = Column(JSON, default={}, nullable=False)
    request_body = Column(JSON, nullable=False)

    # Response
    status_code = Column(Integer)
    response_body = Column(Text)
    response_headers = Column(JSON, default={}, nullable=False)
    response_time_ms = Column(Integer)

    # Status
    status = Column(Enum(WebhookStatus), default=WebhookStatus.PENDING, nullable=False)
    success = Column(Boolean, default=False, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    next_retry_at = Column(DateTime(timezone=True))

    # Error
    error_message = Column(Text)
    error_traceback = Column(Text)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    webhook = relationship("Webhook", back_populates="deliveries")

    def __repr__(self):
        return f"<WebhookDelivery(id={self.id}, webhook_id={self.webhook_id}, status={self.status})>"
