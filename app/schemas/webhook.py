"""
Webhook Pydantic schemas
"""
from pydantic import Field, HttpUrl, field_validator
from typing import Optional, List, Dict
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampSchema
from app.models import WebhookStatus


class WebhookBase(BaseSchema):
    """Base webhook schema"""
    name: str = Field(..., min_length=1, max_length=255)
    url: HttpUrl
    description: Optional[str] = Field(None, max_length=1000)


class WebhookCreate(WebhookBase):
    """Schema for creating a webhook"""
    events: List[str] = Field(..., min_items=1)
    secret: Optional[str] = Field(None, min_length=16, max_length=255)
    headers: Optional[Dict[str, str]] = Field(default_factory=dict)
    max_retries: int = Field(default=3, ge=0, le=10)
    retry_delay: int = Field(default=60, ge=10, le=3600)  # seconds
    timeout: int = Field(default=30, ge=5, le=300)  # seconds
    organization_id: Optional[int] = None

    @field_validator('events')
    @classmethod
    def validate_events(cls, v: List[str]) -> List[str]:
        """Validate webhook events"""
        valid_events = [
            'api_key.created',
            'api_key.updated',
            'api_key.deleted',
            'api_key.rotated',
            'user.created',
            'user.updated',
            'user.deleted',
            'subscription.created',
            'subscription.updated',
            'subscription.canceled',
            'payment.succeeded',
            'payment.failed',
            'invoice.created',
            'invoice.paid',
            'webhook.test'
        ]
        for event in v:
            if event not in valid_events and not event.endswith('.*'):
                raise ValueError(
                    f'Invalid event: {event}. Valid events: {", ".join(valid_events)}'
                )
        return v


class WebhookUpdate(BaseSchema):
    """Schema for updating a webhook"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    url: Optional[HttpUrl] = None
    description: Optional[str] = Field(None, max_length=1000)
    events: Optional[List[str]] = None
    headers: Optional[Dict[str, str]] = None
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    retry_delay: Optional[int] = Field(None, ge=10, le=3600)
    timeout: Optional[int] = Field(None, ge=5, le=300)
    is_active: Optional[bool] = None


class WebhookResponse(WebhookBase, TimestampSchema):
    """Schema for webhook response"""
    id: int
    events: List[str]
    is_active: bool
    verified: bool
    success_count: int
    failure_count: int
    last_triggered_at: Optional[datetime] = None
    last_error: Optional[str] = None
    max_retries: int
    retry_delay: int
    timeout: int


class WebhookListResponse(WebhookResponse):
    """Schema for webhook in list responses"""
    user_id: int
    organization_id: Optional[int] = None


class WebhookTest(BaseSchema):
    """Schema for testing a webhook"""
    event_type: str = Field(default="webhook.test")
    payload: Optional[Dict] = Field(default_factory=dict)


class WebhookDeliveryResponse(TimestampSchema):
    """Schema for webhook delivery response"""
    id: int
    webhook_id: int
    event_type: str
    status: WebhookStatus
    status_code: Optional[int] = None
    response_time_ms: Optional[int] = None
    success: bool
    retry_count: int
    next_retry_at: Optional[datetime] = None
    error_message: Optional[str] = None


class WebhookDeliveryListResponse(WebhookDeliveryResponse):
    """Schema for webhook delivery in list"""
    payload: Optional[Dict] = None


class WebhookDeliveryDetailResponse(WebhookDeliveryResponse):
    """Schema for detailed webhook delivery"""
    payload: Dict
    request_headers: Dict
    request_body: Dict
    response_body: Optional[str] = None
    response_headers: Optional[Dict] = None
    error_traceback: Optional[str] = None


class WebhookStats(BaseSchema):
    """Schema for webhook statistics"""
    webhook_id: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    pending_deliveries: int
    success_rate: float
    avg_response_time: float
    deliveries_by_event: Dict[str, int]
    deliveries_over_time: List[Dict]
    recent_errors: List[str]
