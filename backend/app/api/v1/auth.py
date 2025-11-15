"""
Auth API endpoints - Registration, Login, 2FA, Password Management
"""
from typing import Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    RefreshTokenRequest,
    TwoFactorEnable,
    TwoFactorVerify,
    TwoFactorDisable,
    TwoFactorLogin,
    PasswordResetRequest,
    PasswordReset,
    PasswordChange,
    EmailVerification
)
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.api.dependencies import get_current_user, get_client_ip
from app.models import User


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=Dict, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user

    Creates a new user account and returns access and refresh tokens.

    **Request Body:**
    - email: Valid email address (unique)
    - username: Username (unique, lowercase, 3-50 chars)
    - password: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
    - full_name: User's full name
    - phone_number: Optional phone number
    - company_name: Optional company name

    **Response:**
    - access_token: JWT access token (30 min expiry)
    - refresh_token: JWT refresh token (7 days expiry)
    - token_type: "bearer"
    - user: User profile data
    """
    result = await AuthService.register(db, user_data)

    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "user": UserResponse.model_validate(result["user"])
    }


@router.post("/login", response_model=Dict)
async def login(
    credentials: UserLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user

    Authenticates user with email and password. If 2FA is enabled, returns
    temporary token for 2FA verification.

    **Request Body:**
    - email: User's email address
    - password: User's password

    **Response (No 2FA):**
    - access_token: JWT access token
    - refresh_token: JWT refresh token
    - token_type: "bearer"
    - expires_in: Token expiration in seconds
    - user: User profile data

    **Response (With 2FA):**
    - requires_2fa: true
    - temp_token: Temporary token for 2FA verification
    - message: Instructions
    """
    ip_address = get_client_ip(request)

    result = await AuthService.login(
        db,
        email=credentials.email,
        password=credentials.password,
        ip_address=ip_address
    )

    # If 2FA is required, return temp token
    if result.get("requires_2fa"):
        return result

    # Otherwise, return full authentication
    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"],
        "user": UserResponse.model_validate(result["user"])
    }


@router.post("/2fa/login", response_model=Dict)
async def verify_2fa_login(
    verify_data: TwoFactorLogin,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Complete login with 2FA

    Verifies 2FA code and completes the login process.

    **Request Body:**
    - temp_token: Temporary token from login response
    - code: 6-digit TOTP code from authenticator app

    **Response:**
    - access_token: JWT access token
    - refresh_token: JWT refresh token
    - token_type: "bearer"
    - expires_in: Token expiration in seconds
    - user: User profile data
    """
    ip_address = get_client_ip(request)

    result = await AuthService.verify_2fa_and_login(
        db,
        temp_token=verify_data.temp_token,
        code=verify_data.code,
        ip_address=ip_address
    )

    return {
        "access_token": result["access_token"],
        "refresh_token": result["refresh_token"],
        "token_type": result["token_type"],
        "expires_in": result["expires_in"],
        "user": UserResponse.model_validate(result["user"])
    }


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    request: Request = None
):
    """
    Logout user

    Blacklists the current access token.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Success message
    """
    # Get token from request
    token = request.headers.get("Authorization", "").replace("Bearer ", "")

    await AuthService.logout(token)

    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token

    Generates new access token using refresh token.

    **Request Body:**
    - refresh_token: Valid refresh token

    **Response:**
    - access_token: New JWT access token
    - refresh_token: Same refresh token (remains valid)
    - token_type: "bearer"
    - expires_in: Token expiration in seconds
    """
    result = await AuthService.refresh_access_token(db, refresh_data.refresh_token)

    return TokenResponse(**result)


@router.post("/2fa/enable", response_model=Dict)
async def enable_2fa(
    enable_data: TwoFactorEnable,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Enable two-factor authentication

    Generates TOTP secret and QR code for setting up 2FA.

    **Request Body:**
    - password: Current password for verification

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - secret: TOTP secret (save securely)
    - qr_code: Base64 encoded QR code image
    - backup_codes: List of 10 backup codes
    - message: Setup instructions

    **Important:** Save the backup codes securely. They can be used if you lose
    access to your authenticator app. After receiving this response, call the
    verify endpoint to activate 2FA.
    """
    result = await AuthService.enable_2fa(
        db,
        user_id=current_user.id,
        password=enable_data.password
    )

    return result


@router.post("/2fa/verify")
async def verify_2fa_setup(
    verify_data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Verify and activate 2FA

    Verifies the 2FA code and activates two-factor authentication.

    **Request Body:**
    - code: 6-digit TOTP code from authenticator app

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Success message
    """
    await AuthService.verify_and_enable_2fa(
        db,
        user_id=current_user.id,
        code=verify_data.code
    )

    return {"message": "Two-factor authentication has been enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    disable_data: TwoFactorDisable,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Disable two-factor authentication

    Disables 2FA after verifying password and current 2FA code.

    **Request Body:**
    - password: Current password
    - code: Current 6-digit TOTP code

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Success message
    """
    await AuthService.disable_2fa(
        db,
        user_id=current_user.id,
        password=disable_data.password,
        code=disable_data.code
    )

    return {"message": "Two-factor authentication has been disabled"}


@router.post("/password/reset-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Request password reset

    Sends password reset email with token.

    **Request Body:**
    - email: Email address of the account

    **Response:**
    - message: Success message (always returned for security)

    **Note:** For security reasons, this endpoint always returns success
    even if the email doesn't exist. If the email exists, a password reset
    link will be sent.
    """
    token = await AuthService.request_password_reset(db, reset_request.email)

    # In production, this would send an email
    # For development, we return the token
    return {
        "message": "If an account exists with this email, a password reset link has been sent",
        "token": token  # Remove this in production!
    }


@router.post("/password/reset")
async def reset_password(
    reset_data: PasswordReset,
    db: AsyncSession = Depends(get_db)
):
    """
    Reset password

    Resets password using the reset token from email.

    **Request Body:**
    - token: Password reset token from email
    - new_password: New password (strong password required)

    **Response:**
    - message: Success message
    """
    await AuthService.reset_password(
        db,
        token=reset_data.token,
        new_password=reset_data.new_password
    )

    return {"message": "Password has been reset successfully"}


@router.post("/password/change")
async def change_password(
    change_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change password

    Changes password for authenticated user.

    **Request Body:**
    - current_password: Current password
    - new_password: New password (strong password required)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Success message
    """
    await AuthService.change_password(
        db,
        user_id=current_user.id,
        current_password=change_data.current_password,
        new_password=change_data.new_password
    )

    return {"message": "Password has been changed successfully"}


@router.post("/email/verify")
async def verify_email(
    verification_data: EmailVerification,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify email address

    Verifies user's email address using the verification token.

    **Request Body:**
    - token: Email verification token from email

    **Response:**
    - message: Success message
    """
    await AuthService.verify_email(db, verification_data.token)

    return {"message": "Email has been verified successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user profile

    Returns the profile of the currently authenticated user.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - User profile data
    """
    return UserResponse.model_validate(current_user)
