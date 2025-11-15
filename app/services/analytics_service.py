"""
Analytics Service - Business logic for usage tracking and analytics
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from datetime import datetime, timedelta
from collections import defaultdict

from app.models import ApiUsageLog, ApiKey, User, SystemMetric, UserActivity
from app.schemas import DateRangeFilter, PaginationParams


class AnalyticsService:
    """Service for analytics and reporting"""

    @staticmethod
    async def track_api_usage(
        db: AsyncSession,
        api_key_id: int,
        user_id: int,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: int,
        ip_address: str,
        user_agent: Optional[str] = None,
        credits_consumed: int = 1,
        error_message: Optional[str] = None
    ) -> ApiUsageLog:
        """Track API usage"""
        log = ApiUsageLog(
            api_key_id=api_key_id,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent,
            credits_consumed=credits_consumed,
            error_message=error_message
        )

        db.add(log)
        await db.commit()

        return log

    @staticmethod
    async def get_usage_stats(
        db: AsyncSession,
        user_id: int,
        date_filter: DateRangeFilter
    ) -> Dict[str, Any]:
        """Get comprehensive usage statistics"""
        # Base query
        base_query = select(ApiUsageLog).where(
            and_(
                ApiUsageLog.user_id == user_id,
                ApiUsageLog.created_at >= date_filter.start_date,
                ApiUsageLog.created_at <= date_filter.end_date
            )
        )

        # Total requests
        total_result = await db.execute(
            select(func.count(ApiUsageLog.id)).select_from(base_query.subquery())
        )
        total_requests = total_result.scalar_one()

        # Successful requests (2xx status codes)
        success_result = await db.execute(
            select(func.count(ApiUsageLog.id))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.status_code >= 200,
                    ApiUsageLog.status_code < 300,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        successful_requests = success_result.scalar_one()

        # Failed requests (4xx, 5xx)
        failed_requests = total_requests - successful_requests

        # Total credits consumed
        credits_result = await db.execute(
            select(func.sum(ApiUsageLog.credits_consumed))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        total_credits = credits_result.scalar_one() or 0

        # Average response time
        avg_time_result = await db.execute(
            select(func.avg(ApiUsageLog.response_time_ms))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        avg_response_time = avg_time_result.scalar_one() or 0

        # P95 response time
        p95_result = await db.execute(
            select(func.percentile_cont(0.95).within_group(ApiUsageLog.response_time_ms))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        p95_response_time = p95_result.scalar_one() or 0

        # P99 response time
        p99_result = await db.execute(
            select(func.percentile_cont(0.99).within_group(ApiUsageLog.response_time_ms))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        p99_response_time = p99_result.scalar_one() or 0

        # Unique IPs
        unique_ips_result = await db.execute(
            select(func.count(func.distinct(ApiUsageLog.ip_address)))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        unique_ips = unique_ips_result.scalar_one()

        # Calculate error rate
        error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

        # Get status code distribution
        status_distribution = await AnalyticsService.get_status_distribution(
            db, user_id, date_filter
        )

        # Get top endpoints
        top_endpoints = await AnalyticsService.get_top_endpoints(
            db, user_id, date_filter, limit=10
        )

        # Get time series data
        time_series = await AnalyticsService.get_time_series_data(
            db, user_id, date_filter
        )

        return {
            "summary": {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "failed_requests": failed_requests,
                "total_credits": total_credits,
                "avg_response_time": round(float(avg_response_time), 2),
                "p95_response_time": round(float(p95_response_time), 2),
                "p99_response_time": round(float(p99_response_time), 2),
                "error_rate": round(error_rate, 2),
                "unique_ips": unique_ips
            },
            "time_series": time_series,
            "status_distribution": status_distribution,
            "top_endpoints": top_endpoints
        }

    @staticmethod
    async def get_status_distribution(
        db: AsyncSession,
        user_id: int,
        date_filter: DateRangeFilter
    ) -> Dict[int, int]:
        """Get distribution of status codes"""
        result = await db.execute(
            select(
                ApiUsageLog.status_code,
                func.count(ApiUsageLog.id).label("count")
            )
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
            .group_by(ApiUsageLog.status_code)
            .order_by(desc("count"))
        )

        return {row.status_code: row.count for row in result}

    @staticmethod
    async def get_top_endpoints(
        db: AsyncSession,
        user_id: int,
        date_filter: DateRangeFilter,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top endpoints by request count"""
        result = await db.execute(
            select(
                ApiUsageLog.endpoint,
                ApiUsageLog.method,
                func.count(ApiUsageLog.id).label("count"),
                func.avg(ApiUsageLog.response_time_ms).label("avg_time")
            )
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
            .group_by(ApiUsageLog.endpoint, ApiUsageLog.method)
            .order_by(desc("count"))
            .limit(limit)
        )

        return [
            {
                "endpoint": row.endpoint,
                "method": row.method,
                "count": row.count,
                "avg_response_time": round(float(row.avg_time), 2)
            }
            for row in result
        ]

    @staticmethod
    async def get_time_series_data(
        db: AsyncSession,
        user_id: int,
        date_filter: DateRangeFilter
    ) -> List[Dict[str, Any]]:
        """Get time series data based on granularity"""
        # Determine time bucket based on granularity
        granularity_map = {
            "hour": "hour",
            "day": "day",
            "week": "week",
            "month": "month"
        }

        time_bucket = granularity_map.get(date_filter.granularity, "day")

        result = await db.execute(
            select(
                func.date_trunc(time_bucket, ApiUsageLog.created_at).label("timestamp"),
                func.count(ApiUsageLog.id).label("requests"),
                func.avg(ApiUsageLog.response_time_ms).label("avg_time"),
                func.percentile_cont(0.95).within_group(ApiUsageLog.response_time_ms).label("p95_time"),
                func.percentile_cont(0.99).within_group(ApiUsageLog.response_time_ms).label("p99_time"),
                func.sum(ApiUsageLog.credits_consumed).label("credits"),
                func.count().filter(ApiUsageLog.status_code >= 400).label("errors")
            )
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
            .group_by("timestamp")
            .order_by("timestamp")
        )

        return [
            {
                "timestamp": row.timestamp.isoformat(),
                "requests": row.requests,
                "avg_response_time": round(float(row.avg_time), 2),
                "p95_response_time": round(float(row.p95_time or 0), 2),
                "p99_response_time": round(float(row.p99_time or 0), 2),
                "credits": row.credits or 0,
                "errors": row.errors or 0
            }
            for row in result
        ]

    @staticmethod
    async def get_real_time_metrics(
        db: AsyncSession,
        user_id: int,
        window_minutes: int = 5
    ) -> Dict[str, Any]:
        """Get real-time metrics for the last N minutes"""
        since = datetime.utcnow() - timedelta(minutes=window_minutes)

        result = await db.execute(
            select(
                func.count(ApiUsageLog.id).label("requests"),
                func.avg(ApiUsageLog.response_time_ms).label("avg_time"),
                func.max(ApiUsageLog.response_time_ms).label("max_time")
            )
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.created_at >= since
                )
            )
        )

        row = result.first()

        if not row or row.requests == 0:
            return {
                "current_rps": 0,
                "avg_response_time": 0,
                "max_response_time": 0,
                "timestamp": datetime.utcnow().isoformat()
            }

        # Calculate requests per second
        rps = row.requests / (window_minutes * 60)

        return {
            "current_rps": round(rps, 2),
            "avg_response_time": round(float(row.avg_time), 2),
            "max_response_time": row.max_time,
            "timestamp": datetime.utcnow().isoformat()
        }

    @staticmethod
    async def get_endpoint_stats(
        db: AsyncSession,
        user_id: int,
        endpoint: str,
        date_filter: DateRangeFilter
    ) -> Dict[str, Any]:
        """Get statistics for a specific endpoint"""
        # Total requests
        total_result = await db.execute(
            select(func.count(ApiUsageLog.id))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.endpoint == endpoint,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        total_requests = total_result.scalar_one()

        # Successful requests
        success_result = await db.execute(
            select(func.count(ApiUsageLog.id))
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.endpoint == endpoint,
                    ApiUsageLog.status_code >= 200,
                    ApiUsageLog.status_code < 300,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        successful_requests = success_result.scalar_one()

        # Response times
        time_result = await db.execute(
            select(
                func.avg(ApiUsageLog.response_time_ms).label("avg"),
                func.percentile_cont(0.95).within_group(ApiUsageLog.response_time_ms).label("p95"),
                func.percentile_cont(0.99).within_group(ApiUsageLog.response_time_ms).label("p99")
            )
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.endpoint == endpoint,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
        )
        times = time_result.first()

        # Status code distribution
        status_result = await db.execute(
            select(
                ApiUsageLog.status_code,
                func.count(ApiUsageLog.id).label("count")
            )
            .where(
                and_(
                    ApiUsageLog.user_id == user_id,
                    ApiUsageLog.endpoint == endpoint,
                    ApiUsageLog.created_at >= date_filter.start_date,
                    ApiUsageLog.created_at <= date_filter.end_date
                )
            )
            .group_by(ApiUsageLog.status_code)
        )

        status_distribution = {row.status_code: row.count for row in status_result}

        error_rate = ((total_requests - successful_requests) / total_requests * 100) if total_requests > 0 else 0

        return {
            "endpoint": endpoint,
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": total_requests - successful_requests,
            "avg_response_time": round(float(times.avg or 0), 2),
            "p95_response_time": round(float(times.p95 or 0), 2),
            "p99_response_time": round(float(times.p99 or 0), 2),
            "error_rate": round(error_rate, 2),
            "requests_by_status": status_distribution
        }

    @staticmethod
    async def track_user_activity(
        db: AsyncSession,
        user_id: int,
        activity_type: str,
        description: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserActivity:
        """Track user activity"""
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=ip_address,
            user_agent=user_agent
        )

        db.add(activity)
        await db.commit()

        return activity

    @staticmethod
    async def get_user_activities(
        db: AsyncSession,
        user_id: int,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[UserActivity], int]:
        """Get user activity history"""
        query = select(UserActivity).where(UserActivity.user_id == user_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        # Order by creation date (newest first)
        query = query.order_by(UserActivity.created_at.desc())

        # Execute
        result = await db.execute(query)
        activities = result.scalars().all()

        return list(activities), total
