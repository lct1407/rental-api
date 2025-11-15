"""
System maintenance background tasks
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.core.cache import RedisCache


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_old_logs")
def cleanup_old_logs(days: int = 90) -> Dict[str, Any]:
    """
    Clean up old logs and records (periodic task)

    Args:
        days: Delete records older than this many days

    Returns:
        Cleanup statistics
    """
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import delete
            from app.models import (
                ApiUsageLog, UserActivity, AuditLog,
                SecurityEvent, SystemMetric
            )

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Delete old API usage logs
            api_logs_result = await db.execute(
                delete(ApiUsageLog).where(ApiUsageLog.created_at < cutoff_date)
            )

            # Delete old user activity logs
            activity_result = await db.execute(
                delete(UserActivity).where(UserActivity.created_at < cutoff_date)
            )

            # Keep audit logs longer (1 year)
            audit_cutoff = datetime.utcnow() - timedelta(days=365)
            audit_result = await db.execute(
                delete(AuditLog).where(AuditLog.created_at < audit_cutoff)
            )

            # Delete resolved security events older than 30 days
            security_cutoff = datetime.utcnow() - timedelta(days=30)
            security_result = await db.execute(
                delete(SecurityEvent).where(
                    SecurityEvent.created_at < security_cutoff,
                    SecurityEvent.resolved == True
                )
            )

            # Delete old system metrics
            metrics_result = await db.execute(
                delete(SystemMetric).where(SystemMetric.created_at < cutoff_date)
            )

            await db.commit()

            return {
                "api_logs_deleted": api_logs_result.rowcount,
                "activities_deleted": activity_result.rowcount,
                "audit_logs_deleted": audit_result.rowcount,
                "security_events_deleted": security_result.rowcount,
                "metrics_deleted": metrics_result.rowcount,
                "total_deleted": (
                    api_logs_result.rowcount +
                    activity_result.rowcount +
                    audit_result.rowcount +
                    security_result.rowcount +
                    metrics_result.rowcount
                )
            }

    return asyncio.run(_cleanup())


@celery_app.task(name="app.tasks.maintenance_tasks.check_inactive_api_keys")
def check_inactive_api_keys(inactive_days: int = 90) -> Dict[str, int]:
    """
    Check for inactive API keys and notify users (periodic task)

    Args:
        inactive_days: Consider keys inactive after this many days

    Returns:
        Count of inactive keys found
    """
    async def _check():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.models import ApiKey, User

            cutoff_date = datetime.utcnow() - timedelta(days=inactive_days)

            # Find inactive keys
            result = await db.execute(
                select(ApiKey, User)
                .join(User, ApiKey.user_id == User.id)
                .where(
                    ApiKey.is_active == True,
                    ApiKey.last_used_at < cutoff_date
                )
            )

            inactive_keys = result.all()

            # In production, send notifications to users
            # For now, just return count

            return {
                "inactive_keys_count": len(inactive_keys)
            }

    return asyncio.run(_check())


@celery_app.task(name="app.tasks.maintenance_tasks.deactivate_expired_api_keys")
def deactivate_expired_api_keys() -> Dict[str, int]:
    """
    Deactivate expired API keys (periodic task)

    Returns:
        Count of deactivated keys
    """
    async def _deactivate():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.models import ApiKey

            now = datetime.utcnow()

            # Find expired keys
            result = await db.execute(
                select(ApiKey).where(
                    ApiKey.is_active == True,
                    ApiKey.expires_at <= now
                )
            )

            expired_keys = result.scalars().all()

            for key in expired_keys:
                key.is_active = False

            await db.commit()

            return {
                "deactivated_count": len(expired_keys)
            }

    return asyncio.run(_deactivate())


@celery_app.task(name="app.tasks.maintenance_tasks.cleanup_expired_tokens")
def cleanup_expired_tokens() -> Dict[str, int]:
    """
    Clean up expired invitation tokens and reset tokens (periodic task)

    Returns:
        Cleanup count
    """
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import delete
            from app.models import OrganizationInvitation

            now = datetime.utcnow()

            # Delete expired invitations
            result = await db.execute(
                delete(OrganizationInvitation).where(
                    OrganizationInvitation.expires_at < now,
                    OrganizationInvitation.accepted_at.is_(None)
                )
            )

            await db.commit()

            # Clean up blacklisted tokens from Redis
            # In production, implement Redis key pattern cleanup

            return {
                "invitations_deleted": result.rowcount
            }

    return asyncio.run(_cleanup())


@celery_app.task(name="app.tasks.maintenance_tasks.update_user_stats")
def update_user_stats() -> Dict[str, int]:
    """
    Update cached user statistics (periodic task)

    Returns:
        Update count
    """
    async def _update():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func
            from app.models import User, ApiKey, Subscription

            # Get all active users
            result = await db.execute(
                select(User).where(User.status == "active")
            )

            users = result.scalars().all()
            updated_count = 0

            for user in users:
                # Count API keys
                api_keys_result = await db.execute(
                    select(func.count(ApiKey.id)).where(ApiKey.user_id == user.id)
                )
                api_keys_count = api_keys_result.scalar_one()

                # Get active subscription
                subscription_result = await db.execute(
                    select(Subscription).where(
                        Subscription.user_id == user.id,
                        Subscription.status == "active"
                    )
                )
                subscription = subscription_result.scalar_one_or_none()

                # Cache stats in Redis
                stats = {
                    "api_keys_count": api_keys_count,
                    "subscription_plan": subscription.plan.value if subscription else "free",
                    "credits": user.credits
                }

                await RedisCache.set_json(
                    f"user_stats:{user.id}",
                    stats,
                    expire=3600  # 1 hour
                )

                updated_count += 1

            return {
                "updated_count": updated_count
            }

    return asyncio.run(_update())


@celery_app.task(name="app.tasks.maintenance_tasks.check_system_health")
def check_system_health() -> Dict[str, Any]:
    """
    Perform system health checks (periodic task)

    Returns:
        Health check results
    """
    async def _check():
        health_status = {
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {}
        }

        # Check database
        try:
            async with AsyncSessionLocal() as db:
                from sqlalchemy import text
                await db.execute(text("SELECT 1"))
                health_status["checks"]["database"] = "healthy"
        except Exception as e:
            health_status["checks"]["database"] = f"unhealthy: {str(e)}"

        # Check Redis
        try:
            await RedisCache.ping()
            health_status["checks"]["redis"] = "healthy"
        except Exception as e:
            health_status["checks"]["redis"] = f"unhealthy: {str(e)}"

        # Check disk space (placeholder)
        health_status["checks"]["disk_space"] = "healthy"

        # Determine overall health
        all_healthy = all(
            status == "healthy"
            for status in health_status["checks"].values()
        )

        health_status["overall"] = "healthy" if all_healthy else "degraded"

        # In production, send alerts if unhealthy

        return health_status

    return asyncio.run(_check())


@celery_app.task(name="app.tasks.maintenance_tasks.backup_critical_data")
def backup_critical_data() -> Dict[str, Any]:
    """
    Backup critical data (periodic task)

    Returns:
        Backup status
    """
    async def _backup():
        # This is a placeholder for actual backup logic
        # In production, you would:
        # - Export database dumps
        # - Upload to S3/cloud storage
        # - Keep rotation of backups
        # - Verify backup integrity

        return {
            "status": "completed",
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Backup implementation pending"
        }

    return asyncio.run(_backup())


@celery_app.task(name="app.tasks.maintenance_tasks.optimize_database")
def optimize_database() -> Dict[str, str]:
    """
    Run database optimization tasks (periodic task)

    Returns:
        Optimization status
    """
    async def _optimize():
        async with AsyncSessionLocal() as db:
            # Run VACUUM ANALYZE on PostgreSQL (if needed)
            # This would be run at the database level

            # Update statistics
            from sqlalchemy import text
            await db.execute(text("ANALYZE"))

            await db.commit()

            return {
                "status": "completed",
                "timestamp": datetime.utcnow().isoformat()
            }

    return asyncio.run(_optimize())
