"""
Admin Pydantic schemas
"""
from pydantic import Field
from typing import Optional, List, Dict
from datetime import datetime

from app.schemas.common import BaseSchema
from app.schemas.user import UserListResponse
from app.models import UserRole, UserStatus


class AdminDashboardStats(BaseSchema):
    """Schema for admin dashboard statistics"""
    total_users: int
    active_users: int
    suspended_users: int
    new_users_today: int
    new_users_week: int
    new_users_month: int

    total_api_keys: int
    active_api_keys: int

    total_webhooks: int
    active_webhooks: int

    total_api_calls_today: int
    total_api_calls_week: int
    total_api_calls_month: int

    total_revenue_today: float
    total_revenue_week: float
    total_revenue_month: float

    active_subscriptions: int
    trial_subscriptions: int
    canceled_subscriptions: int

    avg_response_time: float
    error_rate: float
    uptime_percentage: float


class RecentActivity(BaseSchema):
    """Schema for recent activity"""
    id: int
    user_id: int
    username: str
    activity_type: str
    description: str
    ip_address: Optional[str] = None
    created_at: datetime


class SystemHealth(BaseSchema):
    """Schema for system health"""
    database: str  # healthy, degraded, down
    redis: str
    celery: str
    storage: str
    overall: str
    uptime: float
    last_check: datetime


class UserManagementFilter(BaseSchema):
    """Schema for user management filtering"""
    search: Optional[str] = None
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    sort_by: str = Field(default="created_at", pattern="^(created_at|email|username|last_login_at)$")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class BroadcastMessage(BaseSchema):
    """Schema for broadcasting messages"""
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=5000)
    target: str = Field(default="all", pattern="^(all|role|plan|active|trial)$")
    role: Optional[UserRole] = None
    plan: Optional[str] = None
    channels: List[str] = Field(
        default=["email", "in_app"],
        description="Notification channels"
    )
    schedule_for: Optional[datetime] = None  # For scheduled messages


class MaintenanceMode(BaseSchema):
    """Schema for maintenance mode"""
    enabled: bool
    message: Optional[str] = Field(None, max_length=500)
    allowed_ips: Optional[List[str]] = Field(default_factory=list)
    estimated_duration: Optional[int] = None  # minutes


class SystemConfig(BaseSchema):
    """Schema for system configuration"""
    key: str
    value: str
    description: Optional[str] = None


class AuditLogFilter(BaseSchema):
    """Schema for audit log filtering"""
    user_id: Optional[int] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    ip_address: Optional[str] = None


class AuditLogResponse(BaseSchema):
    """Schema for audit log response"""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    action: str
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None
    ip_address: Optional[str] = None
    old_values: Optional[Dict] = None
    new_values: Optional[Dict] = None
    success: bool
    created_at: datetime


class SecurityEventResponse(BaseSchema):
    """Schema for security event response"""
    id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    event_type: str
    severity: str
    description: str
    ip_address: Optional[str] = None
    endpoint: Optional[str] = None
    resolved: bool
    resolved_at: Optional[datetime] = None
    created_at: datetime


class BatchUserAction(BaseSchema):
    """Schema for batch user actions"""
    user_ids: List[int] = Field(..., min_items=1, max_items=100)
    action: str = Field(..., pattern="^(suspend|activate|delete|update_role)$")
    reason: Optional[str] = Field(None, max_length=500)
    role: Optional[UserRole] = None  # For update_role action


class SystemReport(BaseSchema):
    """Schema for system report"""
    report_type: str = Field(..., pattern="^(users|revenue|usage|performance)$")
    period: str = Field(..., pattern="^(today|week|month|year|custom)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    format: str = Field(default="pdf", pattern="^(pdf|csv|json)$")


class CacheStats(BaseSchema):
    """Schema for cache statistics"""
    total_keys: int
    memory_used: str
    hit_rate: float
    total_hits: int
    total_misses: int
    evicted_keys: int
    top_keys: List[Dict]


class DatabaseStats(BaseSchema):
    """Schema for database statistics"""
    total_connections: int
    active_connections: int
    idle_connections: int
    database_size: str
    table_sizes: Dict[str, str]
    slow_queries: List[Dict]


class FeatureFlag(BaseSchema):
    """Schema for feature flags"""
    name: str
    enabled: bool
    description: Optional[str] = None
    rollout_percentage: int = Field(default=100, ge=0, le=100)
    target_users: Optional[List[int]] = None
    target_roles: Optional[List[UserRole]] = None
