"""
Organization Pydantic schemas
"""
from pydantic import Field, field_validator
from typing import Optional, Dict, List
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampSchema
from app.models import OrganizationRole, OrganizationStatus


class OrganizationBase(BaseSchema):
    """Base organization schema"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)


class OrganizationCreate(OrganizationBase):
    """Schema for creating an organization"""
    slug: Optional[str] = Field(None, min_length=3, max_length=100)

    @field_validator('slug')
    @classmethod
    def validate_slug(cls, v: Optional[str]) -> Optional[str]:
        """Validate organization slug"""
        if v:
            if not v.replace('-', '').replace('_', '').isalnum():
                raise ValueError('Slug can only contain letters, numbers, hyphens, and underscores')
            return v.lower()
        return v


class OrganizationUpdate(BaseSchema):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    website: Optional[str] = Field(None, max_length=255)
    logo_url: Optional[str] = Field(None, max_length=500)
    billing_email: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Optional[Dict] = None
    settings: Optional[Dict] = None


class OrganizationResponse(OrganizationBase, TimestampSchema):
    """Schema for organization response"""
    id: int
    slug: str
    logo_url: Optional[str] = None
    status: OrganizationStatus
    max_users: int
    max_api_keys: int
    max_webhooks: int
    storage_limit: int
    credits: int


class OrganizationDetailResponse(OrganizationResponse):
    """Schema for detailed organization response"""
    billing_email: Optional[str] = None
    billing_address: Optional[Dict] = None
    settings: Dict
    features: List[str]
    member_count: int
    api_key_count: int
    webhook_count: int


class OrganizationMemberBase(BaseSchema):
    """Base organization member schema"""
    role: OrganizationRole


class OrganizationMemberResponse(OrganizationMemberBase, TimestampSchema):
    """Schema for organization member response"""
    id: int
    user_id: int
    organization_id: int
    is_active: bool
    # User details
    email: str
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None


class OrganizationInviteCreate(BaseSchema):
    """Schema for inviting a member to organization"""
    email: str
    role: OrganizationRole = OrganizationRole.MEMBER


class OrganizationInviteResponse(BaseSchema):
    """Schema for organization invitation response"""
    id: int
    organization_id: int
    email: str
    role: OrganizationRole
    token: str
    expires_at: datetime
    invited_by: str  # Username of inviter


class OrganizationInviteAccept(BaseSchema):
    """Schema for accepting organization invitation"""
    token: str


class OrganizationMemberUpdate(BaseSchema):
    """Schema for updating organization member"""
    role: OrganizationRole


class OrganizationStats(BaseSchema):
    """Schema for organization statistics"""
    organization_id: int
    total_api_calls: int
    total_credits_used: int
    active_members: int
    active_api_keys: int
    active_webhooks: int
    storage_used: int
    api_calls_by_day: List[Dict]
    top_endpoints: List[Dict]
