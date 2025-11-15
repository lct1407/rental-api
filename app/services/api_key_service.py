"""
API Key Service - Business logic for API key management
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import secrets
import hashlib

from app.models import ApiKey, User
from app.schemas import ApiKeyCreate, ApiKeyUpdate, PaginationParams
from app.core.cache import RedisCache, cache, invalidate_cache
from app.services.user_service import UserService


class ApiKeyService:
    """Service for API key operations"""

    @staticmethod
    def generate_api_key() -> tuple[str, str, str, str]:
        """
        Generate a new API key

        Returns:
            tuple: (full_key, key_hash, key_prefix, last_four)
        """
        # Generate random key (32 bytes = 64 hex chars)
        key_bytes = secrets.token_bytes(32)
        full_key = f"sk_{key_bytes.hex()}"

        # Hash the key for storage
        key_hash = hashlib.sha256(full_key.encode()).hexdigest()

        # Store prefix and last 4 for identification
        key_prefix = full_key[:12]  # "sk_" + first 8 chars
        last_four = full_key[-4:]

        return full_key, key_hash, key_prefix, last_four

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        api_key_data: ApiKeyCreate
    ) -> tuple[ApiKey, str]:
        """Create a new API key"""
        # Check if user has reached limit
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Count existing keys
        count_result = await db.execute(
            select(func.count(ApiKey.id))
            .where(ApiKey.user_id == user_id, ApiKey.is_active == True)
        )
        key_count = count_result.scalar_one()

        if key_count >= user.max_api_keys:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum API key limit reached ({user.max_api_keys})"
            )

        # Generate API key
        full_key, key_hash, key_prefix, last_four = ApiKeyService.generate_api_key()

        # Calculate expiration
        expires_at = None
        if api_key_data.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=api_key_data.expires_in_days)

        # Create API key
        api_key = ApiKey(
            user_id=user_id,
            organization_id=api_key_data.organization_id,
            name=api_key_data.name,
            description=api_key_data.description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            last_four=last_four,
            scopes=api_key_data.scopes,
            ip_whitelist=api_key_data.ip_whitelist,
            allowed_origins=api_key_data.allowed_origins,
            rate_limit_per_hour=api_key_data.rate_limit_per_hour or user.api_rate_limit,
            rate_limit_per_day=api_key_data.rate_limit_per_day or (user.api_rate_limit * 24),
            expires_at=expires_at,
        )

        db.add(api_key)
        await db.commit()
        await db.refresh(api_key)

        # Cache the key hash for fast verification
        await RedisCache.set(
            f"api_key:{key_hash}",
            api_key.id,
            expire=86400  # 24 hours
        )

        return api_key, full_key

    @staticmethod
    async def get_by_id(db: AsyncSession, key_id: int) -> Optional[ApiKey]:
        """Get API key by ID"""
        result = await db.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    @cache(key_prefix="api_key_by_hash", expire=3600)
    async def get_by_key_hash(db: AsyncSession, key_hash: str) -> Optional[ApiKey]:
        """Get API key by hash (cached)"""
        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def verify_key(db: AsyncSession, api_key: str) -> Optional[ApiKey]:
        """Verify API key and return key record"""
        # Hash the provided key
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()

        # Try to get from cache first
        cached_id = await RedisCache.get(f"api_key:{key_hash}")
        if cached_id:
            return await ApiKeyService.get_by_id(db, int(cached_id))

        # Get from database
        api_key_record = await ApiKeyService.get_by_key_hash(db, key_hash)

        if api_key_record:
            # Cache for future lookups
            await RedisCache.set(
                f"api_key:{key_hash}",
                api_key_record.id,
                expire=86400
            )

        return api_key_record

    @staticmethod
    async def list_keys(
        db: AsyncSession,
        user_id: int,
        organization_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[ApiKey], int]:
        """List API keys for a user or organization"""
        query = select(ApiKey).where(ApiKey.user_id == user_id)

        if organization_id:
            query = query.where(ApiKey.organization_id == organization_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        # Order by creation date
        query = query.order_by(ApiKey.created_at.desc())

        # Execute
        result = await db.execute(query)
        keys = result.scalars().all()

        return list(keys), total

    @staticmethod
    @invalidate_cache(key_prefix="api_key_by_hash")
    async def update(
        db: AsyncSession,
        key_id: int,
        key_data: ApiKeyUpdate
    ) -> ApiKey:
        """Update API key"""
        api_key = await ApiKeyService.get_by_id(db, key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # Update fields
        update_data = key_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(api_key, field, value)

        await db.commit()
        await db.refresh(api_key)

        # Invalidate cache
        await RedisCache.delete(f"api_key:{api_key.key_hash}")

        return api_key

    @staticmethod
    @invalidate_cache(key_prefix="api_key_by_hash")
    async def delete(db: AsyncSession, key_id: int) -> bool:
        """Delete API key"""
        api_key = await ApiKeyService.get_by_id(db, key_id)
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # Invalidate cache
        await RedisCache.delete(f"api_key:{api_key.key_hash}")

        # Delete from database
        await db.delete(api_key)
        await db.commit()

        return True

    @staticmethod
    @invalidate_cache(key_prefix="api_key_by_hash")
    async def rotate(
        db: AsyncSession,
        key_id: int
    ) -> tuple[ApiKey, str]:
        """Rotate API key (generate new key while keeping settings)"""
        old_key = await ApiKeyService.get_by_id(db, key_id)
        if not old_key:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API key not found"
            )

        # Generate new key
        full_key, key_hash, key_prefix, last_four = ApiKeyService.generate_api_key()

        # Invalidate old key cache
        await RedisCache.delete(f"api_key:{old_key.key_hash}")

        # Update key
        old_key.key_hash = key_hash
        old_key.key_prefix = key_prefix
        old_key.last_four = last_four

        await db.commit()
        await db.refresh(old_key)

        # Cache new key
        await RedisCache.set(
            f"api_key:{key_hash}",
            old_key.id,
            expire=86400
        )

        return old_key, full_key

    @staticmethod
    async def update_usage(
        db: AsyncSession,
        key_id: int,
        ip_address: str
    ) -> None:
        """Update API key usage statistics"""
        api_key = await ApiKeyService.get_by_id(db, key_id)
        if api_key:
            api_key.usage_count += 1
            api_key.last_used_at = datetime.utcnow()
            api_key.last_used_ip = ip_address
            await db.commit()

    @staticmethod
    async def check_rate_limit(
        db: AsyncSession,
        api_key: ApiKey,
        ip_address: str
    ) -> bool:
        """Check if API key has exceeded rate limit"""
        # Check hourly limit
        hour_key = f"rate_limit:api_key:{api_key.id}:hour"
        hour_count = await RedisCache.get(hour_key)

        if hour_count and int(hour_count) >= api_key.rate_limit_per_hour:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Hourly rate limit exceeded for this API key"
            )

        # Check daily limit
        day_key = f"rate_limit:api_key:{api_key.id}:day"
        day_count = await RedisCache.get(day_key)

        if day_count and int(day_count) >= api_key.rate_limit_per_day:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily rate limit exceeded for this API key"
            )

        # Increment counters
        if hour_count is None:
            await RedisCache.set(hour_key, 1, expire=3600)
        else:
            await RedisCache.incr(hour_key)

        if day_count is None:
            await RedisCache.set(day_key, 1, expire=86400)
        else:
            await RedisCache.incr(day_key)

        return True

    @staticmethod
    async def check_ip_whitelist(api_key: ApiKey, ip_address: str) -> bool:
        """Check if IP is whitelisted for API key"""
        if api_key.ip_whitelist and len(api_key.ip_whitelist) > 0:
            if ip_address not in api_key.ip_whitelist:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="IP address not whitelisted for this API key"
                )
        return True

    @staticmethod
    async def check_scopes(api_key: ApiKey, required_scopes: List[str]) -> bool:
        """Check if API key has required scopes"""
        if not all(scope in api_key.scopes for scope in required_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="API key does not have required scopes"
            )
        return True
