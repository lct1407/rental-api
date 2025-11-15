"""
Advanced Rate Limiting Service
Supports RPM, RPH, RPD, and monthly limits with burst allowance
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from fastapi import HTTPException, status
from app.core.cache import RedisCache
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.credit import RateLimitRule, FeatureDefinition
from app.models.user import User
from app.models.subscription import Subscription
import logging

logger = logging.getLogger(__name__)


class RateLimitExceededError(HTTPException):
    """Rate limit exceeded exception"""
    def __init__(
        self,
        limit_type: str,
        limit: int,
        reset_at: str,
        headers: Optional[Dict[str, str]] = None
    ):
        detail = f"Rate limit exceeded: {limit_type}"
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers or {}
        )


class RateLimitStatus:
    """Rate limit status data class"""
    def __init__(
        self,
        current: int,
        limit: int,
        remaining: int,
        exceeded: bool,
        reset_at: Optional[datetime] = None
    ):
        self.current = current
        self.limit = limit
        self.remaining = remaining
        self.exceeded = exceeded
        self.reset_at = reset_at

    def to_dict(self) -> Dict:
        return {
            "current": self.current,
            "limit": self.limit,
            "remaining": self.remaining,
            "exceeded": self.exceeded,
            "reset_at": self.reset_at.isoformat() if self.reset_at else None
        }


class RateLimiter:
    """Advanced rate limiting service"""

    # Default limits (can be overridden by subscription plan)
    DEFAULT_LIMITS = {
        "free": {
            "rpm": 10,
            "rph": 100,
            "rpd": 1000,
            "monthly": 10000
        },
        "basic": {
            "rpm": 60,
            "rph": 1000,
            "rpd": 10000,
            "monthly": 300000
        },
        "pro": {
            "rpm": 300,
            "rph": 10000,
            "rpd": 100000,
            "monthly": 3000000
        },
        "enterprise": {
            "rpm": 1000,
            "rph": 50000,
            "rpd": 1000000,
            "monthly": float('inf')
        }
    }

    @staticmethod
    async def check_limits(
        db: AsyncSession,
        user_id: int,
        api_key_id: Optional[int] = None,
        feature_key: Optional[str] = None
    ) -> Dict[str, RateLimitStatus]:
        """Check all rate limits for a user"""
        try:
            # Get user's subscription limits
            user_limits = await RateLimiter._get_user_limits(db, user_id)

            # Get feature-specific limits if applicable
            feature_limits = {}
            if feature_key:
                feature_limits = await RateLimiter._get_feature_limits(db, feature_key)

            # Get custom rate limit rules if any
            custom_limits = await RateLimiter._get_custom_limits(
                db, user_id, api_key_id, feature_key
            )

            # Merge limits (custom > feature > user)
            final_limits = {**user_limits, **feature_limits, **custom_limits}

            # Current usage
            current_rpm = await RateLimiter._get_usage(user_id, "minute")
            current_rph = await RateLimiter._get_usage(user_id, "hour")
            current_rpd = await RateLimiter._get_usage(user_id, "day")
            current_month = await RateLimiter._get_usage(user_id, "month")

            # Build status for each limit type
            checks = {
                "rpm": RateLimitStatus(
                    current=current_rpm,
                    limit=final_limits.get("rpm", float('inf')),
                    remaining=max(0, final_limits.get("rpm", float('inf')) - current_rpm),
                    exceeded=current_rpm >= final_limits.get("rpm", float('inf')),
                    reset_at=RateLimiter._get_reset_time("minute")
                ),
                "rph": RateLimitStatus(
                    current=current_rph,
                    limit=final_limits.get("rph", float('inf')),
                    remaining=max(0, final_limits.get("rph", float('inf')) - current_rph),
                    exceeded=current_rph >= final_limits.get("rph", float('inf')),
                    reset_at=RateLimiter._get_reset_time("hour")
                ),
                "rpd": RateLimitStatus(
                    current=current_rpd,
                    limit=final_limits.get("rpd", float('inf')),
                    remaining=max(0, final_limits.get("rpd", float('inf')) - current_rpd),
                    exceeded=current_rpd >= final_limits.get("rpd", float('inf')),
                    reset_at=RateLimiter._get_reset_time("day")
                ),
                "monthly": RateLimitStatus(
                    current=current_month,
                    limit=final_limits.get("monthly", float('inf')),
                    remaining=max(0, final_limits.get("monthly", float('inf')) - current_month),
                    exceeded=current_month >= final_limits.get("monthly", float('inf')),
                    reset_at=RateLimiter._get_reset_time("month")
                )
            }

            return checks

        except Exception as e:
            logger.error(f"Failed to check rate limits for user {user_id}: {str(e)}")
            # On error, return permissive limits to avoid blocking users
            return {
                "rpm": RateLimitStatus(0, float('inf'), float('inf'), False),
                "rph": RateLimitStatus(0, float('inf'), float('inf'), False),
                "rpd": RateLimitStatus(0, float('inf'), float('inf'), False),
                "monthly": RateLimitStatus(0, float('inf'), float('inf'), False)
            }

    @staticmethod
    async def consume_request(
        db: AsyncSession,
        user_id: int,
        api_key_id: Optional[int] = None,
        feature_key: Optional[str] = None,
        increment: int = 1
    ) -> Tuple[bool, Dict[str, RateLimitStatus]]:
        """Consume a request from rate limit quota"""
        try:
            # Check limits first
            limits = await RateLimiter.check_limits(db, user_id, api_key_id, feature_key)

            # Check if any limit exceeded
            exceeded_limits = []
            for limit_type, limit_data in limits.items():
                if limit_data.exceeded:
                    exceeded_limits.append(limit_type)

            if exceeded_limits:
                # Raise exception with headers
                first_exceeded = exceeded_limits[0]
                limit_data = limits[first_exceeded]

                headers = {
                    "X-RateLimit-Limit": str(int(limit_data.limit)),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": limit_data.reset_at.isoformat() if limit_data.reset_at else "",
                    "Retry-After": str(RateLimiter._get_retry_after_seconds(first_exceeded))
                }

                raise RateLimitExceededError(
                    limit_type=first_exceeded,
                    limit=int(limit_data.limit),
                    reset_at=limit_data.reset_at.isoformat() if limit_data.reset_at else "",
                    headers=headers
                )

            # Increment counters
            await RateLimiter._increment_usage(user_id, "minute", increment)
            await RateLimiter._increment_usage(user_id, "hour", increment)
            await RateLimiter._increment_usage(user_id, "day", increment)
            await RateLimiter._increment_usage(user_id, "month", increment)

            # If API key specific, also track key usage
            if api_key_id:
                await RateLimiter._increment_usage(f"key:{api_key_id}", "hour", increment)
                await RateLimiter._increment_usage(f"key:{api_key_id}", "day", increment)

            logger.debug(f"Rate limit consumed for user {user_id}: {increment} requests")

            return True, limits

        except RateLimitExceededError:
            raise
        except Exception as e:
            logger.error(f"Failed to consume rate limit for user {user_id}: {str(e)}")
            # On error, allow the request to proceed
            return True, {}

    @staticmethod
    async def get_usage_stats(
        db: AsyncSession,
        user_id: int,
        api_key_id: Optional[int] = None
    ) -> Dict:
        """Get detailed usage statistics"""
        try:
            limits = await RateLimiter.check_limits(db, user_id, api_key_id)

            stats = {
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat(),
                "limits": {
                    limit_type: limit_status.to_dict()
                    for limit_type, limit_status in limits.items()
                },
                "approaching_limits": []
            }

            # Check if approaching any limits (>80%)
            for limit_type, limit_status in limits.items():
                if limit_status.limit != float('inf'):
                    usage_percentage = (limit_status.current / limit_status.limit) * 100
                    if usage_percentage >= 80:
                        stats["approaching_limits"].append({
                            "type": limit_type,
                            "percentage": round(usage_percentage, 2),
                            "remaining": limit_status.remaining
                        })

            return stats

        except Exception as e:
            logger.error(f"Failed to get usage stats for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def reset_limits(
        user_id: int,
        limit_type: Optional[str] = None
    ):
        """Reset rate limits for a user (admin action)"""
        try:
            if limit_type:
                # Reset specific limit type
                pattern = f"rate_limit:{user_id}:{limit_type}:*"
                await RedisCache.delete_pattern(pattern)
                logger.info(f"Reset {limit_type} limits for user {user_id}")
            else:
                # Reset all limits
                pattern = f"rate_limit:{user_id}:*"
                await RedisCache.delete_pattern(pattern)
                logger.info(f"Reset all limits for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to reset limits for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def _get_user_limits(db: AsyncSession, user_id: int) -> Dict:
        """Get user's rate limits based on subscription"""
        try:
            # Get user with subscription
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()

            if not user:
                return RateLimiter.DEFAULT_LIMITS["free"]

            # Get active subscription
            sub_result = await db.execute(
                select(Subscription).where(
                    and_(
                        Subscription.user_id == user_id,
                        Subscription.status == "active"
                    )
                ).order_by(Subscription.created_at.desc())
            )
            subscription = sub_result.scalar_one_or_none()

            if not subscription:
                return RateLimiter.DEFAULT_LIMITS["free"]

            # Get plan limits
            plan = str(subscription.plan).lower()
            return RateLimiter.DEFAULT_LIMITS.get(plan, RateLimiter.DEFAULT_LIMITS["free"])

        except Exception as e:
            logger.error(f"Failed to get user limits for user {user_id}: {str(e)}")
            return RateLimiter.DEFAULT_LIMITS["free"]

    @staticmethod
    async def _get_feature_limits(db: AsyncSession, feature_key: str) -> Dict:
        """Get feature-specific rate limits"""
        try:
            result = await db.execute(
                select(FeatureDefinition).where(
                    and_(
                        FeatureDefinition.feature_key == feature_key,
                        FeatureDefinition.is_active == True
                    )
                )
            )
            feature = result.scalar_one_or_none()

            if not feature:
                return {}

            limits = {}
            if feature.rpm_limit:
                limits["rpm"] = feature.rpm_limit
            if feature.rph_limit:
                limits["rph"] = feature.rph_limit
            if feature.rpd_limit:
                limits["rpd"] = feature.rpd_limit
            if feature.rpm_limit_monthly:
                limits["monthly"] = feature.rpm_limit_monthly

            return limits

        except Exception as e:
            logger.error(f"Failed to get feature limits for {feature_key}: {str(e)}")
            return {}

    @staticmethod
    async def _get_custom_limits(
        db: AsyncSession,
        user_id: int,
        api_key_id: Optional[int] = None,
        feature_key: Optional[str] = None
    ) -> Dict:
        """Get custom rate limit rules"""
        try:
            now = datetime.utcnow()

            # Build query for custom rules
            query = select(RateLimitRule).where(
                and_(
                    RateLimitRule.is_active == True,
                    or_(
                        RateLimitRule.valid_from.is_(None),
                        RateLimitRule.valid_from <= now
                    ),
                    or_(
                        RateLimitRule.valid_until.is_(None),
                        RateLimitRule.valid_until >= now
                    )
                )
            )

            # Add user/api_key/feature filters
            query = query.where(
                or_(
                    RateLimitRule.user_id == user_id,
                    RateLimitRule.api_key_id == api_key_id if api_key_id else False,
                    RateLimitRule.feature_key == feature_key if feature_key else False,
                    RateLimitRule.rule_type == "global"
                )
            )

            # Order by priority (lower = higher priority)
            query = query.order_by(RateLimitRule.priority)

            result = await db.execute(query)
            rules = result.scalars().all()

            if not rules:
                return {}

            # Use the highest priority rule
            rule = rules[0]

            limits = {}
            if rule.rpm_limit:
                limits["rpm"] = rule.rpm_limit
            if rule.rph_limit:
                limits["rph"] = rule.rph_limit
            if rule.rpd_limit:
                limits["rpd"] = rule.rpd_limit
            if rule.rpm_limit_monthly:
                limits["monthly"] = rule.rpm_limit_monthly

            return limits

        except Exception as e:
            logger.error(f"Failed to get custom limits for user {user_id}: {str(e)}")
            return {}

    @staticmethod
    async def _get_usage(identifier: int, period: str) -> int:
        """Get current usage for a period"""
        try:
            key = f"rate_limit:{identifier}:{period}:{RateLimiter._get_period_key(period)}"
            usage = await RedisCache.get(key)
            return int(usage) if usage else 0
        except Exception as e:
            logger.error(f"Failed to get usage for {identifier} {period}: {str(e)}")
            return 0

    @staticmethod
    async def _increment_usage(identifier: int, period: str, increment: int = 1):
        """Increment usage counter"""
        try:
            key = f"rate_limit:{identifier}:{period}:{RateLimiter._get_period_key(period)}"

            # TTL for each period type
            ttl_seconds = {
                "minute": 60,
                "hour": 3600,
                "day": 86400,
                "month": 2592000  # 30 days
            }

            current = await RedisCache.get(key)
            if current is None:
                await RedisCache.set(key, increment, expire=ttl_seconds[period])
            else:
                await RedisCache.increment(key, increment)

        except Exception as e:
            logger.error(f"Failed to increment usage for {identifier} {period}: {str(e)}")

    @staticmethod
    def _get_period_key(period: str) -> str:
        """Get period-specific key"""
        now = datetime.utcnow()
        if period == "minute":
            return now.strftime("%Y%m%d%H%M")
        elif period == "hour":
            return now.strftime("%Y%m%d%H")
        elif period == "day":
            return now.strftime("%Y%m%d")
        elif period == "month":
            return now.strftime("%Y%m")
        return ""

    @staticmethod
    def _get_reset_time(limit_type: str) -> datetime:
        """Get reset timestamp for rate limit"""
        now = datetime.utcnow()
        if limit_type == "rpm" or limit_type == "minute":
            return now.replace(second=0, microsecond=0) + timedelta(minutes=1)
        elif limit_type == "rph" or limit_type == "hour":
            return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        elif limit_type == "rpd" or limit_type == "day":
            return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        else:  # monthly
            if now.month == 12:
                return datetime(now.year + 1, 1, 1, 0, 0, 0)
            else:
                return datetime(now.year, now.month + 1, 1, 0, 0, 0)

    @staticmethod
    def _get_retry_after_seconds(limit_type: str) -> int:
        """Get retry-after seconds for rate limit"""
        reset_time = RateLimiter._get_reset_time(limit_type)
        now = datetime.utcnow()
        return int((reset_time - now).total_seconds())
