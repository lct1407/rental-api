"""
Dashboard API endpoints - User dashboard metrics and analytics
"""
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, timedelta

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models import User, ApiUsageLog, Service


router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/metrics")
async def get_dashboard_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard KPIs and metrics

    Returns key performance indicators for the user dashboard including:
    - Monthly request count with % change
    - Error rate percentage
    - Active services count
    - Plan usage statistics
    - Credit balance (free, paid, total)
    """
    # Calculate monthly requests
    now = datetime.utcnow()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (month_start - timedelta(days=1)).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Current month requests
    current_month_result = await db.execute(
        select(func.count(ApiUsageLog.id))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= month_start)
    )
    monthly_requests = current_month_result.scalar_one() or 0

    # Last month requests for comparison
    last_month_result = await db.execute(
        select(func.count(ApiUsageLog.id))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= last_month_start)
        .where(ApiUsageLog.created_at < month_start)
    )
    last_month_count = last_month_result.scalar_one() or 0

    # Calculate % change
    if last_month_count > 0:
        monthly_change = round(((monthly_requests - last_month_count) / last_month_count) * 100, 1)
    else:
        monthly_change = 100.0 if monthly_requests > 0 else 0.0

    # Calculate error rate (4xx and 5xx responses)
    error_result = await db.execute(
        select(func.count(ApiUsageLog.id))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= month_start)
        .where(ApiUsageLog.status_code >= 400)
    )
    error_count = error_result.scalar_one() or 0
    error_rate = round((error_count / monthly_requests * 100), 2) if monthly_requests > 0 else 0.0

    # Count distinct services used this month
    services_result = await db.execute(
        select(func.count(func.distinct(ApiUsageLog.endpoint)))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= month_start)
    )
    active_services = services_result.scalar_one() or 0

    # Determine plan limits based on subscription plan
    plan_limits = {
        "free": 1000,
        "basic": 50000,
        "pro": 2000000,
        "enterprise": 10000000,
        "unlimited": None
    }

    plan_name = current_user.plan if hasattr(current_user, 'plan') else "free"
    plan_limit = plan_limits.get(plan_name, 1000)
    plan_percentage = round((monthly_requests / plan_limit) * 100, 1) if plan_limit else 0

    return {
        "monthly_requests": monthly_requests,
        "monthly_requests_change": monthly_change,
        "error_rate": error_rate,
        "active_services": active_services,
        "plan": {
            "name": f"{plan_name.title()} Plan" if plan_name else "Free Plan",
            "usage": monthly_requests,
            "limit": plan_limit,
            "percentage": plan_percentage
        },
        "credit_balance": {
            "free": current_user.credits_free,
            "paid": current_user.credits_paid,
            "total": current_user.credits_total
        }
    }


@router.get("/usage-chart")
async def get_usage_chart(
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    time_range: str = Query("7d", description="Time range: 24h, 7d, 30d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage chart data (time series)

    Returns time-series data for requests and credits over the specified time range.
    Can be filtered by service.
    """
    # Parse time range
    now = datetime.utcnow()
    if time_range == "24h":
        start_time = now - timedelta(hours=24)
        interval = timedelta(hours=1)
        data_points = 24
    elif time_range == "7d":
        start_time = now - timedelta(days=7)
        interval = timedelta(days=1)
        data_points = 7
    elif time_range == "30d":
        start_time = now - timedelta(days=30)
        interval = timedelta(days=1)
        data_points = 30
    else:
        start_time = now - timedelta(days=7)
        interval = timedelta(days=1)
        data_points = 7

    # Build query
    query = select(
        func.date_trunc('day' if time_range != '24h' else 'hour', ApiUsageLog.created_at).label('period'),
        func.count(ApiUsageLog.id).label('requests'),
        func.sum(ApiUsageLog.credits_consumed).label('credits')
    ).where(
        ApiUsageLog.user_id == current_user.id
    ).where(
        ApiUsageLog.created_at >= start_time
    ).group_by(
        'period'
    ).order_by(
        'period'
    )

    # Add service filter if provided
    if service_id:
        service_result = await db.execute(
            select(Service.endpoint).where(Service.id == service_id)
        )
        service = service_result.scalar_one_or_none()
        if service:
            query = query.where(ApiUsageLog.endpoint == service)

    result = await db.execute(query)
    rows = result.all()

    # Format results
    chart_data = []
    for row in rows:
        chart_data.append({
            "date": row.period.strftime("%Y-%m-%d" if time_range != '24h' else "%Y-%m-%d %H:00"),
            "requests": row.requests or 0,
            "credits": row.credits or 0
        })

    return chart_data


@router.get("/service-breakdown")
async def get_service_breakdown(
    time_range: str = Query("30d", description="Time range: 7d, 30d, 90d"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get service usage breakdown

    Returns percentage breakdown of API usage by service for the specified time range.
    """
    # Parse time range
    now = datetime.utcnow()
    if time_range == "7d":
        start_time = now - timedelta(days=7)
    elif time_range == "30d":
        start_time = now - timedelta(days=30)
    elif time_range == "90d":
        start_time = now - timedelta(days=90)
    else:
        start_time = now - timedelta(days=30)

    # Get total requests
    total_result = await db.execute(
        select(func.count(ApiUsageLog.id))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= start_time)
    )
    total_requests = total_result.scalar_one() or 0

    if total_requests == 0:
        return []

    # Get breakdown by endpoint
    breakdown_result = await db.execute(
        select(
            ApiUsageLog.endpoint,
            func.count(ApiUsageLog.id).label('requests'),
            func.sum(ApiUsageLog.credits_consumed).label('credits')
        )
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= start_time)
        .group_by(ApiUsageLog.endpoint)
        .order_by(func.count(ApiUsageLog.id).desc())
        .limit(10)  # Top 10 services
    )

    rows = breakdown_result.all()

    # Format results with service names
    breakdown_data = []
    for row in rows:
        # Try to match endpoint to a service
        service_result = await db.execute(
            select(Service.name).where(Service.endpoint == row.endpoint)
        )
        service_name = service_result.scalar_one_or_none()

        if not service_name:
            # Extract service name from endpoint
            service_name = row.endpoint.split('/')[-1].replace('-', ' ').title() if row.endpoint else "Unknown"

        percentage = round((row.requests / total_requests) * 100, 1)

        breakdown_data.append({
            "service": service_name,
            "requests": row.requests,
            "percentage": percentage,
            "credits": row.credits or 0
        })

    return breakdown_data


@router.get("/quick-stats")
async def get_quick_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get quick statistics for dashboard widgets

    Returns simplified stats for quick dashboard widgets
    """
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = now - timedelta(days=7)

    # Today's requests
    today_result = await db.execute(
        select(func.count(ApiUsageLog.id))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= today_start)
    )
    requests_today = today_result.scalar_one() or 0

    # This week's requests
    week_result = await db.execute(
        select(func.count(ApiUsageLog.id))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= week_start)
    )
    requests_week = week_result.scalar_one() or 0

    # Average response time
    avg_response_result = await db.execute(
        select(func.avg(ApiUsageLog.response_time_ms))
        .where(ApiUsageLog.user_id == current_user.id)
        .where(ApiUsageLog.created_at >= week_start)
    )
    avg_response_time = avg_response_result.scalar_one() or 0

    return {
        "requests_today": requests_today,
        "requests_this_week": requests_week,
        "avg_response_time_ms": round(avg_response_time, 2) if avg_response_time else 0,
        "credits_remaining": current_user.credits_total,
        "plan": current_user.plan if hasattr(current_user, 'plan') else "free"
    }
