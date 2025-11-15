"""
Analytics Pydantic schemas
"""
from pydantic import Field
from typing import Optional, List, Dict
from datetime import datetime

from app.schemas.common import BaseSchema


class DateRangeFilter(BaseSchema):
    """Schema for date range filtering"""
    start_date: datetime
    end_date: datetime
    granularity: str = Field(
        default="day",
        pattern="^(hour|day|week|month)$"
    )


class UsageStatsSummary(BaseSchema):
    """Schema for usage statistics summary"""
    total_requests: int
    successful_requests: int
    failed_requests: int
    total_credits: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    unique_ips: int


class UsageStatsTimeSeries(BaseSchema):
    """Schema for time series usage data"""
    timestamp: datetime
    requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    credits: int
    errors: int


class UsageStatsResponse(BaseSchema):
    """Schema for usage statistics response"""
    summary: UsageStatsSummary
    time_series: List[UsageStatsTimeSeries]
    status_distribution: Dict[int, int]  # status_code: count
    top_endpoints: List[Dict]  # [{endpoint, method, count, avg_time}]
    top_errors: List[Dict]  # [{endpoint, error, count}]


class RealTimeMetrics(BaseSchema):
    """Schema for real-time metrics"""
    current_rps: float  # Requests per second
    avg_response_time: float
    max_response_time: float
    active_connections: int
    timestamp: datetime


class EndpointStats(BaseSchema):
    """Schema for endpoint statistics"""
    endpoint: str
    method: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    p95_response_time: float
    p99_response_time: float
    error_rate: float
    requests_by_status: Dict[int, int]


class GeographicStats(BaseSchema):
    """Schema for geographic statistics"""
    country_code: str
    country_name: str
    request_count: int
    percentage: float


class ApiKeyAnalytics(BaseSchema):
    """Schema for API key analytics"""
    api_key_id: int
    api_key_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    last_used_at: Optional[datetime] = None
    requests_by_day: List[Dict]


class UserActivityLog(BaseSchema):
    """Schema for user activity log"""
    id: int
    activity_type: str
    description: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[int] = None
    ip_address: Optional[str] = None
    created_at: datetime


class SystemMetrics(BaseSchema):
    """Schema for system-wide metrics"""
    total_users: int
    active_users_today: int
    active_users_week: int
    active_users_month: int
    total_api_calls_today: int
    total_api_calls_week: int
    total_api_calls_month: int
    total_revenue_today: float
    total_revenue_week: float
    total_revenue_month: float
    avg_response_time: float
    error_rate: float
    uptime_percentage: float


class AnalyticsExportRequest(BaseSchema):
    """Schema for requesting analytics export"""
    start_date: datetime
    end_date: datetime
    format: str = Field(default="csv", pattern="^(csv|json|pdf)$")
    include_raw_data: bool = False
    metrics: Optional[List[str]] = None


class AnalyticsExportResponse(BaseSchema):
    """Schema for analytics export response"""
    export_id: str
    status: str  # pending, processing, completed, failed
    download_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime
