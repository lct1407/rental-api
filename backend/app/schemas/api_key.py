"""
API Key Pydantic schemas
"""
from pydantic import Field, field_validator
from typing import Optional, List
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampSchema


class ApiKeyBase(BaseSchema):
    """Base API key schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)


class ApiKeyCreate(ApiKeyBase):
    """Schema for creating an API key"""
    scopes: List[str] = Field(default_factory=list)
    ip_whitelist: List[str] = Field(default_factory=list)
    allowed_origins: List[str] = Field(default_factory=list)
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    expires_in_days: Optional[int] = Field(None, ge=1, le=365)
    organization_id: Optional[int] = None

    @field_validator('scopes')
    @classmethod
    def validate_scopes(cls, v: List[str]) -> List[str]:
        """Validate scopes"""
        valid_scopes = [
            'read', 'write', 'delete',
            'api:read', 'api:write',
            'webhooks:read', 'webhooks:write',
            'analytics:read',
            'admin'
        ]
        for scope in v:
            if scope not in valid_scopes:
                raise ValueError(f'Invalid scope: {scope}. Valid scopes: {", ".join(valid_scopes)}')
        return v

    @field_validator('ip_whitelist')
    @classmethod
    def validate_ip_whitelist(cls, v: List[str]) -> List[str]:
        """Validate IP addresses"""
        import ipaddress
        for ip in v:
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise ValueError(f'Invalid IP address: {ip}')
        return v


class ApiKeyUpdate(BaseSchema):
    """Schema for updating an API key"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    scopes: Optional[List[str]] = None
    ip_whitelist: Optional[List[str]] = None
    allowed_origins: Optional[List[str]] = None
    rate_limit_per_hour: Optional[int] = Field(None, ge=1, le=100000)
    rate_limit_per_day: Optional[int] = Field(None, ge=1, le=1000000)
    is_active: Optional[bool] = None


class ApiKeyResponse(ApiKeyBase, TimestampSchema):
    """Schema for API key response"""
    id: int
    key_prefix: str
    last_four: str
    scopes: List[str]
    is_active: bool
    last_used_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    usage_count: int
    rate_limit_per_hour: int
    rate_limit_per_day: int


class ApiKeyWithSecret(ApiKeyResponse):
    """Schema for API key response with secret (only shown once)"""
    key: str  # Full API key - only shown on creation


class ApiKeyListResponse(ApiKeyResponse):
    """Schema for API key in list responses"""
    user_id: int
    organization_id: Optional[int] = None


class ApiKeyUsageStats(BaseSchema):
    """Schema for API key usage statistics"""
    key_id: int
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_response_time: float
    requests_by_status: dict
    requests_by_endpoint: dict
    requests_over_time: List[dict]
    top_ips: List[dict]


class ApiKeyRotateResponse(ApiKeyResponse):
    """Schema for API key rotation response"""
    new_key: str  # New API key
    old_key_expires_at: datetime  # When old key will stop working
    message: str = "API key rotated successfully. Update your applications with the new key."
