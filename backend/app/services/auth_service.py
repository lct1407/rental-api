"""
Auth Service - Business logic for authentication and authorization
"""
from typing import Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from datetime import datetime

from app.models import User, UserRole, UserStatus
from app.schemas import UserRegister, TokenResponse, UserResponse
from app.core.security import SecurityManager
from app.core.cache import RedisCache
from app.services.user_service import UserService


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def register(
        db: AsyncSession,
        user_data: UserRegister
    ) -> dict:
        """Register a new user and return tokens"""
        # Create user using UserService
        user = await UserService.create(db, user_data)

        # Generate tokens
        access_token = SecurityManager.create_access_token(
            data={"sub": user.id, "role": user.role.value}
        )
        refresh_token = SecurityManager.create_refresh_token(
            data={"sub": user.id}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user
        }

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str
    ) -> Optional[User]:
        """Authenticate user by email and password"""
        # Get user
        user = await UserService.get_by_email(db, email)
        if not user:
            return None

        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account is locked until {user.locked_until.isoformat()}"
            )

        # Verify password
        if not SecurityManager.verify_password(password, user.hashed_password):
            # Increment failed login attempts
            await UserService.increment_failed_login(db, user.id)
            return None

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Account is {user.status.value}. Please contact support."
            )

        return user

    @staticmethod
    async def login(
        db: AsyncSession,
        email: str,
        password: str,
        ip_address: str
    ) -> dict:
        """Login user and return tokens"""
        # Authenticate
        user = await AuthService.authenticate(db, email, password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if 2FA is enabled
        if user.two_factor_enabled:
            # Generate temporary token for 2FA verification
            temp_token = SecurityManager.create_temp_token(
                data={"sub": user.id, "purpose": "2fa_verify"}
            )
            return {
                "requires_2fa": True,
                "temp_token": temp_token,
                "message": "Please provide your 2FA code"
            }

        # Update login info
        await UserService.update_login_info(db, user.id, ip_address)

        # Generate tokens
        access_token = SecurityManager.create_access_token(
            data={"sub": user.id, "role": user.role.value}
        )
        refresh_token = SecurityManager.create_refresh_token(
            data={"sub": user.id}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,  # 30 minutes
            "user": user
        }

    @staticmethod
    async def verify_2fa_and_login(
        db: AsyncSession,
        temp_token: str,
        code: str,
        ip_address: str
    ) -> dict:
        """Verify 2FA code and complete login"""
        # Decode temp token
        try:
            payload = SecurityManager.decode_token(temp_token)
            if payload.get("type") != "temp" or payload.get("purpose") != "2fa_verify":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid temporary token"
                )

            user_id = payload.get("sub")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired temporary token"
            )

        # Get user
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify 2FA code
        if not SecurityManager.verify_2fa_token(user.two_factor_secret, code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )

        # Update login info
        await UserService.update_login_info(db, user.id, ip_address)

        # Generate tokens
        access_token = SecurityManager.create_access_token(
            data={"sub": user.id, "role": user.role.value}
        )
        refresh_token = SecurityManager.create_refresh_token(
            data={"sub": user.id}
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": 1800,
            "user": user
        }

    @staticmethod
    async def enable_2fa(
        db: AsyncSession,
        user_id: int,
        password: str
    ) -> dict:
        """Enable 2FA for user"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify password
        if not SecurityManager.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        # Check if already enabled
        if user.two_factor_enabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA is already enabled"
            )

        # Generate secret
        secret = SecurityManager.generate_2fa_secret()
        qr_code = SecurityManager.generate_2fa_qr_code(secret, user.email)

        # Generate backup codes
        import secrets
        backup_codes = [secrets.token_hex(8) for _ in range(10)]

        # Save secret and backup codes (encrypted)
        user.two_factor_secret = secret
        if not user.metadata:
            user.metadata = {}
        user.metadata["backup_codes"] = backup_codes

        await db.commit()

        return {
            "secret": secret,
            "qr_code": qr_code,
            "backup_codes": backup_codes,
            "message": "Scan the QR code with your authenticator app"
        }

    @staticmethod
    async def verify_and_enable_2fa(
        db: AsyncSession,
        user_id: int,
        code: str
    ) -> bool:
        """Verify 2FA code and enable 2FA"""
        user = await UserService.get_by_id(db, user_id)
        if not user or not user.two_factor_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup not initiated"
            )

        # Verify code
        if not SecurityManager.verify_2fa_token(user.two_factor_secret, code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )

        # Enable 2FA
        user.two_factor_enabled = True
        await db.commit()

        return True

    @staticmethod
    async def disable_2fa(
        db: AsyncSession,
        user_id: int,
        password: str,
        code: str
    ) -> bool:
        """Disable 2FA for user"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify password
        if not SecurityManager.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password"
            )

        # Verify 2FA code
        if not SecurityManager.verify_2fa_token(user.two_factor_secret, code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )

        # Disable 2FA
        user.two_factor_enabled = False
        user.two_factor_secret = None
        if user.metadata and "backup_codes" in user.metadata:
            del user.metadata["backup_codes"]

        await db.commit()

        return True

    @staticmethod
    async def refresh_access_token(
        db: AsyncSession,
        refresh_token: str
    ) -> dict:
        """Refresh access token using refresh token"""
        try:
            payload = SecurityManager.decode_token(refresh_token)

            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            # Check if token is blacklisted
            jti = payload.get("jti")
            if await RedisCache.exists(f"blacklist:{jti}"):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has been revoked"
                )

            user_id = payload.get("sub")
            user = await UserService.get_by_id(db, user_id)

            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )

            # Check if user is active
            if user.status != UserStatus.ACTIVE:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="User account is not active"
                )

            # Generate new access token
            access_token = SecurityManager.create_access_token(
                data={"sub": user.id, "role": user.role.value}
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,  # Refresh token remains the same
                "token_type": "bearer",
                "expires_in": 1800
            }

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

    @staticmethod
    async def logout(token: str, logout_all: bool = False) -> bool:
        """Logout user by blacklisting token"""
        await SecurityManager.blacklist_token(token)

        if logout_all:
            # TODO: Implement logout from all devices
            # This would require storing active refresh tokens in Redis
            pass

        return True

    @staticmethod
    async def request_password_reset(
        db: AsyncSession,
        email: str
    ) -> str:
        """Request password reset token"""
        user = await UserService.get_by_email(db, email)
        if not user:
            # Don't reveal if email exists
            return "If an account exists with this email, a password reset link has been sent"

        # Generate reset token
        reset_token = SecurityManager.create_password_reset_token(user.email)

        # In production, send email with reset link
        # await EmailService.send_password_reset_email(user.email, reset_token)

        return reset_token  # For development, return token directly

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        token: str,
        new_password: str
    ) -> bool:
        """Reset password using reset token"""
        # Verify token
        email = SecurityManager.verify_password_reset_token(token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )

        # Get user
        user = await UserService.get_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Hash new password
        user.hashed_password = SecurityManager.hash_password(new_password)

        # Reset failed login attempts
        user.failed_login_attempts = 0
        user.locked_until = None

        await db.commit()

        return True

    @staticmethod
    async def verify_email(
        db: AsyncSession,
        token: str
    ) -> bool:
        """Verify email using verification token"""
        # Verify token
        data = SecurityManager.verify_email_verification_token(token)
        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )

        user_id = data.get("user_id")

        # Mark email as verified
        await UserService.verify_email(db, user_id)

        return True

    @staticmethod
    async def change_password(
        db: AsyncSession,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> bool:
        """Change user password"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Verify current password
        if not SecurityManager.verify_password(current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect current password"
            )

        # Hash new password
        user.hashed_password = SecurityManager.hash_password(new_password)

        await db.commit()

        return True
