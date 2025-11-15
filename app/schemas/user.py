"""
User Pydantic schemas
"""
from pydantic import EmailStr, Field, field_validator
from typing import Optional, Dict
from datetime import datetime

from app.schemas.common import BaseSchema, TimestampSchema
from app.models import UserRole, UserStatus


class UserBase(BaseSchema):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)


class UserCreate(UserBase):
    """Schema for creating a user"""
    password: str = Field(..., min_length=8, max_length=100)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()


class UserUpdate(BaseSchema):
    """Schema for updating a user"""
    full_name: Optional[str] = Field(None, max_length=255)
    phone_number: Optional[str] = Field(None, max_length=20)
    company_name: Optional[str] = Field(None, max_length=255)
    bio: Optional[str] = Field(None, max_length=1000)
    avatar_url: Optional[str] = Field(None, max_length=500)
    preferences: Optional[Dict] = None
    notification_settings: Optional[Dict] = None


class UserResponse(UserBase, TimestampSchema):
    """Schema for user response"""
    id: int
    role: UserRole
    status: UserStatus
    email_verified: bool
    two_factor_enabled: bool
    credits: int
    last_login_at: Optional[datetime] = None
    avatar_url: Optional[str] = None


class UserProfileResponse(UserResponse):
    """Extended user profile with additional details"""
    api_rate_limit: int
    storage_limit: int
    max_api_keys: int
    max_webhooks: int
    login_count: int
    metadata: Optional[Dict] = None


class PasswordChange(BaseSchema):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
    confirm_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class UserAdminUpdate(BaseSchema):
    """Schema for admin updating a user"""
    role: Optional[UserRole] = None
    status: Optional[UserStatus] = None
    credits: Optional[int] = Field(None, ge=0)
    api_rate_limit: Optional[int] = Field(None, ge=0)
    storage_limit: Optional[int] = Field(None, ge=0)
    max_api_keys: Optional[int] = Field(None, ge=0)
    max_webhooks: Optional[int] = Field(None, ge=0)


class UserListResponse(UserResponse):
    """Schema for user in list responses"""
    pass


class UserSuspend(BaseSchema):
    """Schema for suspending a user"""
    reason: str = Field(..., min_length=10, max_length=500)
    duration_days: Optional[int] = Field(None, ge=1, le=365)
