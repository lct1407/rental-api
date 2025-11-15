"""
Analytics models with incremental bigint ID
Tracks API usage and system metrics
"""
from sqlalchemy import Column, String, Integer, JSON, DateTime, ForeignKey, BigInteger, Text, Index
from sqlalchemy.orm import relationship
from app.database import Base


class ApiUsageLog(Base):
    """API usage log for analytics"""

    __tablename__ = "api_usage_logs"

    # Foreign Keys
    api_key_id = Column(BigInteger, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Request Details
    endpoint = Column(String(500), index=True, nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, index=True, nullable=False)
    response_time_ms = Column(Integer, nullable=False)

    # Request/Response (optional, can be large)
    request_headers = Column(JSON)
    request_body = Column(Text)
    response_body = Column(Text)
    error_message = Column(Text)

    # Client Info
    ip_address = Column(String(45), index=True, nullable=False)
    user_agent = Column(String(500))
    country_code = Column(String(2))
    city = Column(String(100))
    latitude = Column(String(20))
    longitude = Column(String(20))

    # Billing
    credits_consumed = Column(Integer, default=1, nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    api_key = relationship("ApiKey", back_populates="usage_logs")

    # Indexes for better query performance
    __table_args__ = (
        Index('idx_usage_user_created', 'user_id', 'created_at'),
        Index('idx_usage_endpoint_created', 'endpoint', 'created_at'),
        Index('idx_usage_status_created', 'status_code', 'created_at'),
        Index('idx_usage_ip_created', 'ip_address', 'created_at'),
    )

    def __repr__(self):
        return f"<ApiUsageLog(id={self.id}, endpoint={self.endpoint}, status={self.status_code})>"


class SystemMetric(Base):
    """System-wide metrics"""

    __tablename__ = "system_metrics"

    # Metric Details
    metric_name = Column(String(100), index=True, nullable=False)
    metric_value = Column(String(255), nullable=False)
    metric_type = Column(String(50), nullable=False)  # counter, gauge, histogram

    # Labels
    labels = Column(JSON, default={}, nullable=False)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_metric_name_created', 'metric_name', 'created_at'),
    )

    def __repr__(self):
        return f"<SystemMetric(id={self.id}, name={self.metric_name}, value={self.metric_value})>"


class UserActivity(Base):
    """User activity tracking"""

    __tablename__ = "user_activities"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Activity Details
    activity_type = Column(String(100), index=True, nullable=False)
    description = Column(Text)
    resource_type = Column(String(100))
    resource_id = Column(BigInteger)

    # Client Info
    ip_address = Column(String(45))
    user_agent = Column(String(500))

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_activity_user_created', 'user_id', 'created_at'),
        Index('idx_activity_type_created', 'activity_type', 'created_at'),
    )

    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"
