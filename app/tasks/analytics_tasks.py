"""
Analytics and reporting background tasks
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models import ApiUsageLog, SystemMetric


@celery_app.task(name="app.tasks.analytics_tasks.aggregate_hourly_analytics")
def aggregate_hourly_analytics() -> Dict[str, Any]:
    """
    Aggregate hourly analytics data (periodic task)

    Aggregates:
    - API call counts by endpoint
    - Average response times
    - Error rates
    - Top users by usage

    Returns:
        Aggregation statistics
    """
    async def _aggregate():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func

            now = datetime.utcnow()
            hour_ago = now - timedelta(hours=1)

            # Aggregate API calls
            total_calls_result = await db.execute(
                select(func.count(ApiUsageLog.id))
                .where(ApiUsageLog.created_at >= hour_ago)
            )
            total_calls = total_calls_result.scalar_one()

            # Average response time
            avg_response_result = await db.execute(
                select(func.avg(ApiUsageLog.response_time))
                .where(ApiUsageLog.created_at >= hour_ago)
            )
            avg_response = avg_response_result.scalar_one() or 0

            # Error rate
            error_calls_result = await db.execute(
                select(func.count(ApiUsageLog.id))
                .where(
                    ApiUsageLog.created_at >= hour_ago,
                    ApiUsageLog.status_code >= 400
                )
            )
            error_calls = error_calls_result.scalar_one()
            error_rate = (error_calls / total_calls * 100) if total_calls > 0 else 0

            # Store metrics
            metrics = [
                SystemMetric(
                    metric_name="api.calls.hourly",
                    metric_value=float(total_calls),
                    tags={"period": "hourly"}
                ),
                SystemMetric(
                    metric_name="api.response_time.avg_hourly",
                    metric_value=float(avg_response),
                    tags={"period": "hourly"}
                ),
                SystemMetric(
                    metric_name="api.error_rate.hourly",
                    metric_value=float(error_rate),
                    tags={"period": "hourly"}
                )
            ]

            for metric in metrics:
                db.add(metric)

            await db.commit()

            return {
                "total_calls": total_calls,
                "avg_response_time": avg_response,
                "error_rate": error_rate,
                "period": "hourly",
                "timestamp": now.isoformat()
            }

    return asyncio.run(_aggregate())


@celery_app.task(name="app.tasks.analytics_tasks.generate_daily_reports")
def generate_daily_reports() -> Dict[str, Any]:
    """
    Generate daily analytics reports (periodic task)

    Returns:
        Report generation status
    """
    async def _generate():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func
            from app.models import User, Payment

            yesterday = datetime.utcnow() - timedelta(days=1)
            yesterday_start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_end = yesterday_start + timedelta(days=1)

            # API usage stats
            api_calls_result = await db.execute(
                select(func.count(ApiUsageLog.id))
                .where(
                    ApiUsageLog.created_at >= yesterday_start,
                    ApiUsageLog.created_at < yesterday_end
                )
            )
            api_calls = api_calls_result.scalar_one()

            # Revenue stats
            revenue_result = await db.execute(
                select(func.sum(Payment.amount))
                .where(
                    Payment.paid_at >= yesterday_start,
                    Payment.paid_at < yesterday_end,
                    Payment.status == "completed"
                )
            )
            revenue = revenue_result.scalar_one() or 0

            # New users
            new_users_result = await db.execute(
                select(func.count(User.id))
                .where(
                    User.created_at >= yesterday_start,
                    User.created_at < yesterday_end
                )
            )
            new_users = new_users_result.scalar_one()

            # Store daily metrics
            metrics = [
                SystemMetric(
                    metric_name="daily.api_calls",
                    metric_value=float(api_calls),
                    tags={"date": yesterday_start.date().isoformat()}
                ),
                SystemMetric(
                    metric_name="daily.revenue",
                    metric_value=float(revenue),
                    tags={"date": yesterday_start.date().isoformat()}
                ),
                SystemMetric(
                    metric_name="daily.new_users",
                    metric_value=float(new_users),
                    tags={"date": yesterday_start.date().isoformat()}
                )
            ]

            for metric in metrics:
                db.add(metric)

            await db.commit()

            # In production, you might:
            # - Send report email to admins
            # - Generate PDF report
            # - Update dashboard cache

            return {
                "date": yesterday_start.date().isoformat(),
                "api_calls": api_calls,
                "revenue": float(revenue),
                "new_users": new_users
            }

    return asyncio.run(_generate())


@celery_app.task(name="app.tasks.analytics_tasks.calculate_user_usage_stats")
def calculate_user_usage_stats(user_id: int, period: str = "daily") -> Dict[str, Any]:
    """
    Calculate usage statistics for a specific user

    Args:
        user_id: User ID
        period: Period (daily, weekly, monthly)

    Returns:
        Usage statistics
    """
    async def _calculate():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select, func

            now = datetime.utcnow()

            if period == "daily":
                start = now - timedelta(days=1)
            elif period == "weekly":
                start = now - timedelta(weeks=1)
            else:  # monthly
                start = now - timedelta(days=30)

            # Total calls
            total_calls_result = await db.execute(
                select(func.count(ApiUsageLog.id))
                .where(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= start
                )
            )
            total_calls = total_calls_result.scalar_one()

            # Success rate
            successful_calls_result = await db.execute(
                select(func.count(ApiUsageLog.id))
                .where(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= start,
                    ApiUsageLog.status_code < 400
                )
            )
            successful_calls = successful_calls_result.scalar_one()
            success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0

            # Average response time
            avg_response_result = await db.execute(
                select(func.avg(ApiUsageLog.response_time))
                .where(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= start
                )
            )
            avg_response = avg_response_result.scalar_one() or 0

            return {
                "user_id": user_id,
                "period": period,
                "total_calls": total_calls,
                "successful_calls": successful_calls,
                "success_rate": success_rate,
                "avg_response_time": float(avg_response)
            }

    return asyncio.run(_calculate())


@celery_app.task(name="app.tasks.analytics_tasks.cleanup_old_logs")
def cleanup_old_logs(days: int = 90) -> Dict[str, int]:
    """
    Clean up old analytics logs

    Args:
        days: Delete logs older than this many days

    Returns:
        Count of deleted logs
    """
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import delete

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Delete old API usage logs
            api_logs_result = await db.execute(
                delete(ApiUsageLog)
                .where(ApiUsageLog.created_at < cutoff_date)
            )

            # Delete old system metrics
            metrics_result = await db.execute(
                delete(SystemMetric)
                .where(SystemMetric.created_at < cutoff_date)
            )

            await db.commit()

            return {
                "api_logs_deleted": api_logs_result.rowcount,
                "metrics_deleted": metrics_result.rowcount,
                "total_deleted": api_logs_result.rowcount + metrics_result.rowcount
            }

    return asyncio.run(_cleanup())


@celery_app.task(name="app.tasks.analytics_tasks.track_api_call")
def track_api_call(
    user_id: int,
    api_key_id: int,
    endpoint: str,
    method: str,
    status_code: int,
    response_time: int,
    ip_address: str = None,
    user_agent: str = None
) -> Dict[str, bool]:
    """
    Track API call asynchronously

    Args:
        user_id: User ID
        api_key_id: API key ID
        endpoint: Endpoint path
        method: HTTP method
        status_code: Response status code
        response_time: Response time in ms
        ip_address: Client IP
        user_agent: User agent

    Returns:
        Tracking status
    """
    async def _track():
        async with AsyncSessionLocal() as db:
            from app.services.analytics_service import AnalyticsService

            await AnalyticsService.track_api_usage(
                db,
                api_key_id=api_key_id,
                user_id=user_id,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time=response_time,
                ip_address=ip_address,
                user_agent=user_agent
            )

            return {"success": True}

    return asyncio.run(_track())
