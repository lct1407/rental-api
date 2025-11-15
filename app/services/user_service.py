"""
User Service - Business logic for user management
"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, or_, and_, func
from fastapi import HTTPException, status
from datetime import datetime

from app.models import User, UserRole, UserStatus
from app.schemas import UserCreate, UserUpdate, UserAdminUpdate, PaginationParams
from app.core.security import SecurityManager
from app.core.cache import RedisCache, cache, invalidate_cache


class UserService:
    """Service for user operations"""

    @staticmethod
    async def create(db: AsyncSession, user_data: UserCreate) -> User:
        """Create a new user"""
        # Check if email already exists
        existing = await UserService.get_by_email(db, user_data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )

        # Check if username already exists
        existing = await UserService.get_by_username(db, user_data.username)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )

        # Hash password
        hashed_password = SecurityManager.hash_password(user_data.password)

        # Create user
        user = User(
            email=user_data.email,
            username=user_data.username.lower(),
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            company_name=user_data.company_name,
            bio=user_data.bio,
            role=UserRole.USER,  # Default role
            status=UserStatus.ACTIVE,
        )

        db.add(user)
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @cache(key_prefix="user", expire=3600)
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        """Get user by ID (cached)"""
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        """Get user by username"""
        result = await db.execute(
            select(User).where(User.username == username.lower())
        )
        return result.scalar_one_or_none()

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def update(
        db: AsyncSession,
        user_id: int,
        user_data: UserUpdate
    ) -> User:
        """Update user profile"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def admin_update(
        db: AsyncSession,
        user_id: int,
        admin_data: UserAdminUpdate
    ) -> User:
        """Admin update user (can change role, status, limits)"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Update fields
        update_data = admin_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def delete(db: AsyncSession, user_id: int) -> bool:
        """Delete user (soft delete by setting status)"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Soft delete
        user.status = UserStatus.DELETED
        await db.commit()

        return True

    @staticmethod
    async def list_users(
        db: AsyncSession,
        pagination: PaginationParams,
        search: Optional[str] = None,
        role: Optional[UserRole] = None,
        status: Optional[UserStatus] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> tuple[List[User], int]:
        """List users with filtering and pagination"""
        query = select(User)

        # Apply filters
        filters = []
        if search:
            search_filter = or_(
                User.email.ilike(f"%{search}%"),
                User.username.ilike(f"%{search}%"),
                User.full_name.ilike(f"%{search}%")
            )
            filters.append(search_filter)

        if role:
            filters.append(User.role == role)

        if status:
            filters.append(User.status == status)

        if filters:
            query = query.where(and_(*filters))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply sorting
        sort_column = getattr(User, sort_by, User.created_at)
        if sort_order == "desc":
            query = query.order_by(sort_column.desc())
        else:
            query = query.order_by(sort_column.asc())

        # Apply pagination
        query = query.offset(pagination.skip).limit(pagination.limit)

        # Execute
        result = await db.execute(query)
        users = result.scalars().all()

        return list(users), total

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def suspend(
        db: AsyncSession,
        user_id: int,
        reason: str,
        duration_days: Optional[int] = None
    ) -> User:
        """Suspend a user"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.status = UserStatus.SUSPENDED

        if duration_days:
            from datetime import timedelta
            user.locked_until = datetime.utcnow() + timedelta(days=duration_days)

        # Store suspension reason in metadata
        if not user.metadata:
            user.metadata = {}
        user.metadata["suspension_reason"] = reason
        user.metadata["suspended_at"] = datetime.utcnow().isoformat()

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def activate(db: AsyncSession, user_id: int) -> User:
        """Activate a suspended user"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.status = UserStatus.ACTIVE
        user.locked_until = None

        # Remove suspension metadata
        if user.metadata and "suspension_reason" in user.metadata:
            del user.metadata["suspension_reason"]
            del user.metadata["suspended_at"]

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def verify_email(db: AsyncSession, user_id: int) -> User:
        """Mark user's email as verified"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.email_verified = True
        user.email_verified_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def update_login_info(
        db: AsyncSession,
        user_id: int,
        ip_address: str
    ) -> None:
        """Update user's last login information"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=datetime.utcnow(),
                last_login_ip=ip_address,
                login_count=User.login_count + 1,
                failed_login_attempts=0  # Reset failed attempts on successful login
            )
        )
        await db.commit()

    @staticmethod
    async def increment_failed_login(db: AsyncSession, user_id: int) -> None:
        """Increment failed login attempts"""
        await db.execute(
            update(User)
            .where(User.id == user_id)
            .values(failed_login_attempts=User.failed_login_attempts + 1)
        )
        await db.commit()

        # Check if account should be locked
        user = await UserService.get_by_id(db, user_id)
        if user and user.failed_login_attempts >= 5:
            # Lock account for 30 minutes after 5 failed attempts
            from datetime import timedelta
            user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            user.status = UserStatus.SUSPENDED
            await db.commit()

    @staticmethod
    async def get_stats(db: AsyncSession) -> dict:
        """Get user statistics"""
        # Total users
        total_result = await db.execute(select(func.count(User.id)))
        total = total_result.scalar_one()

        # Active users
        active_result = await db.execute(
            select(func.count(User.id))
            .where(User.status == UserStatus.ACTIVE)
        )
        active = active_result.scalar_one()

        # Suspended users
        suspended_result = await db.execute(
            select(func.count(User.id))
            .where(User.status == UserStatus.SUSPENDED)
        )
        suspended = suspended_result.scalar_one()

        # New users today
        from datetime import date
        today = date.today()
        new_today_result = await db.execute(
            select(func.count(User.id))
            .where(func.date(User.created_at) == today)
        )
        new_today = new_today_result.scalar_one()

        return {
            "total": total,
            "active": active,
            "suspended": suspended,
            "inactive": total - active - suspended,
            "new_today": new_today
        }

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def add_credits(
        db: AsyncSession,
        user_id: int,
        credits: int
    ) -> User:
        """Add credits to user account"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        user.credits += credits
        await db.commit()
        await db.refresh(user)

        return user

    @staticmethod
    @invalidate_cache(key_prefix="user")
    async def consume_credits(
        db: AsyncSession,
        user_id: int,
        credits: int
    ) -> bool:
        """Consume credits from user account"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.credits < credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits"
            )

        user.credits -= credits
        await db.commit()

        return True
