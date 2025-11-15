"""
Security module - JWT authentication, password hashing, and 2FA
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
import secrets
import pyotp
import qrcode
from io import BytesIO
import base64

from app.config import settings
from app.database import get_db

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")


class SecurityManager:
    """Security manager for authentication and authorization"""

    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)

    @staticmethod
    def create_access_token(
        data: Dict[str, Any],
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        to_encode = data.copy()

        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(
                minutes=SecurityManager.ACCESS_TOKEN_EXPIRE_MINUTES
            )

        to_encode.update({
            "exp": expire,
            "type": "access",
            "jti": secrets.token_urlsafe(32),  # JWT ID for token revocation
            "iat": datetime.utcnow()
        })

        return jwt.encode(
            to_encode,
            SecurityManager.SECRET_KEY,
            algorithm=SecurityManager.ALGORITHM
        )

    @staticmethod
    def create_refresh_token(data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(
            days=SecurityManager.REFRESH_TOKEN_EXPIRE_DAYS
        )

        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32),
            "iat": datetime.utcnow()
        })

        return jwt.encode(
            to_encode,
            SecurityManager.SECRET_KEY,
            algorithm=SecurityManager.ALGORITHM
        )

    @staticmethod
    def create_temp_token(data: Dict[str, Any], expires_minutes: int = 5) -> str:
        """Create temporary token for 2FA verification"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=expires_minutes)

        to_encode.update({
            "exp": expire,
            "type": "temp",
            "jti": secrets.token_urlsafe(32),
            "iat": datetime.utcnow()
        })

        return jwt.encode(
            to_encode,
            SecurityManager.SECRET_KEY,
            algorithm=SecurityManager.ALGORITHM
        )

    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token,
                SecurityManager.SECRET_KEY,
                algorithms=[SecurityManager.ALGORITHM]
            )
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @staticmethod
    async def get_current_user(
        token: str = Depends(oauth2_scheme),
        db: AsyncSession = Depends(get_db)
    ):
        """Get current user from JWT token"""
        from app.services.user_service import UserService
        from app.core.cache import RedisCache

        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = SecurityManager.decode_token(token)
            user_id: int = payload.get("sub")

            if user_id is None or payload.get("type") != "access":
                raise credentials_exception

            # Check if token is blacklisted
            jti = payload.get("jti")
            if await RedisCache.exists(f"blacklist:{jti}"):
                raise credentials_exception

        except JWTError:
            raise credentials_exception

        # Get user from database
        user = await UserService.get_by_id(db, user_id=user_id)
        if user is None:
            raise credentials_exception

        # Check if user is active
        from app.models import UserStatus
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )

        return user

    @staticmethod
    async def get_current_active_user(
        current_user = Depends(get_current_user)
    ):
        """Get current active user"""
        from app.models import UserStatus
        if current_user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        return current_user

    # Two-Factor Authentication

    @staticmethod
    def generate_2fa_secret() -> str:
        """Generate a new 2FA secret"""
        return pyotp.random_base32()

    @staticmethod
    def generate_2fa_qr_code(secret: str, email: str) -> str:
        """Generate QR code for 2FA setup (returns base64 encoded image)"""
        totp = pyotp.TOTP(secret)
        totp_uri = totp.provisioning_uri(
            name=email,
            issuer_name=settings.TWO_FACTOR_ISSUER
        )

        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        # Convert to base64
        buffer = BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return f"data:image/png;base64,{img_str}"

    @staticmethod
    def verify_2fa_token(secret: str, token: str) -> bool:
        """Verify 2FA token"""
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)

    # API Key Authentication

    @staticmethod
    async def verify_api_key(api_key: str, db: AsyncSession):
        """Verify API key and return associated user"""
        from app.services.api_key_service import ApiKeyService

        # Get API key from database or cache
        key_record = await ApiKeyService.verify_key(db, api_key)

        if not key_record:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )

        if not key_record.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key is inactive"
            )

        # Check expiration
        if key_record.expires_at and key_record.expires_at < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key has expired"
            )

        return key_record

    # Token Blacklisting

    @staticmethod
    async def blacklist_token(token: str):
        """Add token to blacklist"""
        from app.core.cache import RedisCache

        try:
            payload = SecurityManager.decode_token(token)
            jti = payload.get("jti")
            exp = payload.get("exp")

            if jti and exp:
                # Calculate TTL
                ttl = exp - datetime.utcnow().timestamp()
                if ttl > 0:
                    await RedisCache.set(
                        f"blacklist:{jti}",
                        "1",
                        expire=int(ttl)
                    )
        except Exception:
            pass  # Token already invalid

    # Password Reset

    @staticmethod
    def create_password_reset_token(email: str) -> str:
        """Create password reset token"""
        expires = timedelta(hours=1)
        expire = datetime.utcnow() + expires

        to_encode = {
            "sub": email,
            "type": "password_reset",
            "exp": expire,
            "jti": secrets.token_urlsafe(32)
        }

        return jwt.encode(
            to_encode,
            SecurityManager.SECRET_KEY,
            algorithm=SecurityManager.ALGORITHM
        )

    @staticmethod
    def verify_password_reset_token(token: str) -> Optional[str]:
        """Verify password reset token and return email"""
        try:
            payload = SecurityManager.decode_token(token)

            if payload.get("type") != "password_reset":
                return None

            email: str = payload.get("sub")
            return email
        except JWTError:
            return None

    # Email Verification

    @staticmethod
    def create_email_verification_token(email: str, user_id: int) -> str:
        """Create email verification token"""
        expires = timedelta(days=1)
        expire = datetime.utcnow() + expires

        to_encode = {
            "sub": user_id,
            "email": email,
            "type": "email_verification",
            "exp": expire,
            "jti": secrets.token_urlsafe(32)
        }

        return jwt.encode(
            to_encode,
            SecurityManager.SECRET_KEY,
            algorithm=SecurityManager.ALGORITHM
        )

    @staticmethod
    def verify_email_verification_token(token: str) -> Optional[Dict[str, Any]]:
        """Verify email verification token"""
        try:
            payload = SecurityManager.decode_token(token)

            if payload.get("type") != "email_verification":
                return None

            return {
                "user_id": payload.get("sub"),
                "email": payload.get("email")
            }
        except JWTError:
            return None


# Dependency for getting current user
get_current_user = SecurityManager.get_current_user
get_current_active_user = SecurityManager.get_current_active_user
