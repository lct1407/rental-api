"""
Authentication Pydantic schemas
"""
from pydantic import EmailStr, Field, field_validator
from typing import Optional

from app.schemas.common import BaseSchema
from app.schemas.user import UserResponse


class UserRegister(BaseSchema):
    """Schema for user registration"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    full_name: Optional[str] = Field(None, max_length=255)

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
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()


class UserLogin(BaseSchema):
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseSchema):
    """Schema for token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes
    user: UserResponse


class TempTokenResponse(BaseSchema):
    """Schema for temporary token response (2FA)"""
    requires_2fa: bool = True
    temp_token: str
    message: str = "Please provide your 2FA code"


class RefreshTokenRequest(BaseSchema):
    """Schema for refresh token request"""
    refresh_token: str


class TwoFactorEnable(BaseSchema):
    """Schema for enabling 2FA"""
    password: str  # Require password confirmation


class TwoFactorEnableResponse(BaseSchema):
    """Schema for 2FA enable response"""
    secret: str
    qr_code: str  # Base64 encoded QR code image
    backup_codes: list[str]  # Backup codes for recovery
    message: str = "Scan the QR code with your authenticator app"


class TwoFactorVerify(BaseSchema):
    """Schema for verifying 2FA code"""
    temp_token: Optional[str] = None  # For login flow
    code: str = Field(..., min_length=6, max_length=6)

    @field_validator('code')
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate 2FA code format"""
        if not v.isdigit():
            raise ValueError('2FA code must be 6 digits')
        return v


class TwoFactorDisable(BaseSchema):
    """Schema for disabling 2FA"""
    password: str
    code: str = Field(..., min_length=6, max_length=6)


class PasswordResetRequest(BaseSchema):
    """Schema for password reset request"""
    email: EmailStr


class PasswordReset(BaseSchema):
    """Schema for password reset"""
    token: str
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
        if not any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v):
            raise ValueError('Password must contain at least one special character')
        return v

    @field_validator('confirm_password')
    @classmethod
    def passwords_match(cls, v: str, info) -> str:
        """Ensure passwords match"""
        if 'new_password' in info.data and v != info.data['new_password']:
            raise ValueError('Passwords do not match')
        return v


class EmailVerificationRequest(BaseSchema):
    """Schema for requesting email verification"""
    pass  # Uses current user from token


class EmailVerify(BaseSchema):
    """Schema for verifying email"""
    token: str


class LogoutRequest(BaseSchema):
    """Schema for logout request"""
    logout_all_devices: bool = False  # Optional: logout from all devices
