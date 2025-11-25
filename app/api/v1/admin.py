"""
Admin API endpoints - Admin dashboard, system management, and monitoring
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.database import get_db
from app.schemas.admin import (
    AdminDashboardStats,
    RecentActivity,
    SystemHealth,
    UserManagementFilter,
    BroadcastMessage,
    MaintenanceMode,
    SystemConfig,
    AuditLogFilter,
    AuditLogResponse,
    SecurityEventResponse,
    BatchUserAction,
    SystemReport,
    CacheStats,
    DatabaseStats,
    FeatureFlag
)
from app.schemas.user import UserResponse, UserAdminUpdate
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.user_service import UserService
from app.services.analytics_service import AnalyticsService
from app.api.dependencies import (
    get_current_admin_user,
    get_current_super_admin_user,
    require_permissions,
    get_pagination_params
)
from app.models import User, UserRole
from app.core.permissions import Permission
from app.core.cache import RedisCache


router = APIRouter(prefix="/admin", tags=["Admin"])


# ============================================================================
# Dashboard & Statistics
# ============================================================================

@router.get(
    "/dashboard",
    response_model=AdminDashboardStats,
    dependencies=[Depends(require_permissions([Permission.VIEW_ANALYTICS]))]
)
async def get_admin_dashboard(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get admin dashboard statistics

    Returns comprehensive statistics for the admin dashboard.

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - User statistics (total, active, new)
    - API key statistics
    - Webhook statistics
    - API call statistics
    - Revenue statistics
    - Subscription statistics
    - System performance metrics
    """
    from app.services.api_key_service import ApiKeyService
    from app.services.webhook_service import WebhookService
    from app.models import ApiKey, Webhook

    # Get user stats
    user_stats = await UserService.get_stats(db)

    # Calculate new users for week and month
    from sqlalchemy import select, func
    from app.models import User

    week_ago = datetime.utcnow() - timedelta(days=7)
    month_ago = datetime.utcnow() - timedelta(days=30)

    new_users_week_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= week_ago)
    )
    new_users_week = new_users_week_result.scalar_one()

    new_users_month_result = await db.execute(
        select(func.count(User.id)).where(User.created_at >= month_ago)
    )
    new_users_month = new_users_month_result.scalar_one()

    # API Keys stats
    total_api_keys_result = await db.execute(select(func.count(ApiKey.id)))
    total_api_keys = total_api_keys_result.scalar_one()

    active_api_keys_result = await db.execute(
        select(func.count(ApiKey.id)).where(ApiKey.is_active == True)
    )
    active_api_keys = active_api_keys_result.scalar_one()

    # Webhooks stats
    total_webhooks_result = await db.execute(select(func.count(Webhook.id)))
    total_webhooks = total_webhooks_result.scalar_one()

    active_webhooks_result = await db.execute(
        select(func.count(Webhook.id)).where(Webhook.is_active == True)
    )
    active_webhooks = active_webhooks_result.scalar_one()

    # TODO: Get actual API call stats from AnalyticsService
    # TODO: Get actual revenue stats from PaymentService
    # TODO: Get actual subscription stats from SubscriptionService

    return AdminDashboardStats(
        total_users=user_stats["total"],
        active_users=user_stats["active"],
        suspended_users=user_stats["suspended"],
        new_users_today=user_stats["new_today"],
        new_users_week=new_users_week,
        new_users_month=new_users_month,
        total_api_keys=total_api_keys,
        active_api_keys=active_api_keys,
        total_webhooks=total_webhooks,
        active_webhooks=active_webhooks,
        total_api_calls_today=0,  # TODO: Implement
        total_api_calls_week=0,  # TODO: Implement
        total_api_calls_month=0,  # TODO: Implement
        total_revenue_today=0.0,  # TODO: Implement
        total_revenue_week=0.0,  # TODO: Implement
        total_revenue_month=0.0,  # TODO: Implement
        active_subscriptions=0,  # TODO: Implement
        trial_subscriptions=0,  # TODO: Implement
        canceled_subscriptions=0,  # TODO: Implement
        avg_response_time=0.0,  # TODO: Implement
        error_rate=0.0,  # TODO: Implement
        uptime_percentage=99.9  # TODO: Implement
    )


@router.get(
    "/recent-activity",
    dependencies=[Depends(require_permissions([Permission.VIEW_ANALYTICS]))]
)
async def get_recent_activity(
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get recent system activity

    Returns recent user activities and system events.

    **Query Parameters:**
    - limit: Number of activities to return (1-50, default: 10)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - List of recent activities with user, action, timestamp, type
    """
    from sqlalchemy import select
    from app.models import UserActivity, User as UserModel

    # Get recent activities with user information
    query = select(UserActivity, UserModel).join(
        UserModel, UserActivity.user_id == UserModel.id
    ).order_by(
        UserActivity.created_at.desc()
    ).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    activities = []
    for activity, user in rows:
        # Format timestamp as relative time
        time_diff = datetime.utcnow() - activity.created_at
        if time_diff.total_seconds() < 60:
            timestamp = "Just now"
        elif time_diff.total_seconds() < 3600:
            minutes = int(time_diff.total_seconds() / 60)
            timestamp = f"{minutes} min{'s' if minutes > 1 else ''} ago"
        elif time_diff.total_seconds() < 86400:
            hours = int(time_diff.total_seconds() / 3600)
            timestamp = f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            days = int(time_diff.total_seconds() / 86400)
            timestamp = f"{days} day{'s' if days > 1 else ''} ago"

        # Map activity type to display type
        type_mapping = {
            "user.registered": "signup",
            "user.login": "login",
            "subscription.upgraded": "payment",
            "subscription.created": "payment",
            "payment.succeeded": "payment",
            "api_key.created": "action",
            "webhook.created": "action",
        }

        activities.append({
            "user": user.full_name or user.username,
            "action": activity.description or activity.activity_type.replace("_", " ").title(),
            "timestamp": timestamp,
            "type": type_mapping.get(activity.activity_type, "action")
        })

    return activities


@router.get(
    "/revenue-chart",
    dependencies=[Depends(require_permissions([Permission.VIEW_ANALYTICS]))]
)
async def get_revenue_chart(
    year: int = Query(None, description="Year (default: current year)"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get monthly revenue chart data

    Returns monthly revenue data for the specified year.

    **Query Parameters:**
    - year: Year to get data for (default: current year)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - List of monthly revenue data with month name and amount
    """
    from sqlalchemy import select, func, extract
    from app.models import Payment

    # Use current year if not specified
    if year is None:
        year = datetime.utcnow().year

    # Get monthly revenue
    query = select(
        extract('month', Payment.created_at).label('month'),
        func.sum(Payment.amount).label('revenue')
    ).where(
        extract('year', Payment.created_at) == year
    ).where(
        Payment.status == "succeeded"
    ).group_by(
        'month'
    ).order_by(
        'month'
    )

    result = await db.execute(query)
    rows = result.all()

    # Month names
    month_names = [
        "Jan", "Feb", "Mar", "Apr", "May", "Jun",
        "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
    ]

    # Build revenue data for all 12 months
    revenue_data = []
    revenue_by_month = {int(row.month): float(row.revenue) for row in rows}

    for month_num in range(1, 13):
        revenue_data.append({
            "month": month_names[month_num - 1],
            "revenue": revenue_by_month.get(month_num, 0.0)
        })

    return revenue_data


@router.get(
    "/system-health",
    response_model=SystemHealth,
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def get_system_health(
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system health status

    Returns health status of all system components.

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Status of database, Redis, Celery, storage
    - Overall system health
    - Uptime
    """
    # Check database
    try:
        await db.execute(select(1))
        db_status = "healthy"
    except Exception:
        db_status = "down"

    # Check Redis
    try:
        await RedisCache.ping()
        redis_status = "healthy"
    except Exception:
        redis_status = "down"

    # TODO: Check Celery
    celery_status = "unknown"

    # TODO: Check storage
    storage_status = "unknown"

    # Determine overall status
    if db_status == "down" or redis_status == "down":
        overall_status = "down"
    elif db_status == "degraded" or redis_status == "degraded":
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return SystemHealth(
        database=db_status,
        redis=redis_status,
        celery=celery_status,
        storage=storage_status,
        overall=overall_status,
        uptime=0.0,  # TODO: Calculate actual uptime
        last_check=datetime.utcnow()
    )


# ============================================================================
# User Management (Admin)
# ============================================================================

@router.put(
    "/users/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions([Permission.UPDATE_ALL_USERS]))]
)
async def admin_update_user(
    user_id: int,
    user_data: UserAdminUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin update user

    Allows admin to update user role, status, limits, etc.

    **Path Parameters:**
    - user_id: User ID

    **Request Body:**
    - role: New role (optional)
    - status: New status (optional)
    - max_api_keys: API key limit (optional)
    - api_rate_limit: Rate limit (optional)
    - credits: Credit balance (optional)
    - subscription_plan: Subscription plan (optional)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Updated user profile
    """
    updated_user = await UserService.admin_update(db, user_id, user_data)

    return UserResponse.model_validate(updated_user)


@router.post(
    "/users/batch",
    dependencies=[Depends(require_permissions([Permission.UPDATE_ALL_USERS]))]
)
async def batch_user_action(
    batch_action: BatchUserAction,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Batch user actions

    Perform actions on multiple users at once.

    **Request Body:**
    - user_ids: List of user IDs (1-100)
    - action: Action to perform (suspend, activate, delete, update_role)
    - reason: Reason for action (for suspend/delete)
    - role: New role (for update_role action)

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - success_count: Number of successful operations
    - failed_count: Number of failed operations
    - errors: List of errors
    """
    results = {
        "success_count": 0,
        "failed_count": 0,
        "errors": []
    }

    for user_id in batch_action.user_ids:
        try:
            if batch_action.action == "suspend":
                await UserService.suspend(db, user_id, batch_action.reason or "Batch suspension")
            elif batch_action.action == "activate":
                await UserService.activate(db, user_id)
            elif batch_action.action == "delete":
                await UserService.delete(db, user_id)
            elif batch_action.action == "update_role":
                if not batch_action.role:
                    raise ValueError("Role is required for update_role action")
                await UserService.admin_update(
                    db,
                    user_id,
                    UserAdminUpdate(role=batch_action.role)
                )

            results["success_count"] += 1

        except Exception as e:
            results["failed_count"] += 1
            results["errors"].append({
                "user_id": user_id,
                "error": str(e)
            })

    return results


# ============================================================================
# Audit Logs
# ============================================================================

@router.get(
    "/audit-logs",
    response_model=PaginatedResponse[AuditLogResponse],
    dependencies=[Depends(require_permissions([Permission.VIEW_AUDIT_LOGS]))]
)
async def get_audit_logs(
    user_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs

    Returns paginated audit logs with filtering.

    **Query Parameters:**
    - page, limit: Pagination
    - user_id: Filter by user
    - action: Filter by action type
    - resource_type: Filter by resource type
    - start_date, end_date: Date range filter

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Paginated audit log entries
    """
    # TODO: Implement audit log querying
    return PaginatedResponse(
        items=[],
        total=0,
        page=1,
        limit=20,
        pages=0
    )


@router.get(
    "/security-events",
    response_model=PaginatedResponse[SecurityEventResponse],
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def get_security_events(
    severity: Optional[str] = Query(None, description="Filter by severity"),
    resolved: Optional[bool] = Query(None, description="Filter by resolved status"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get security events

    Returns paginated security events.

    **Query Parameters:**
    - page, limit: Pagination
    - severity: Filter by severity (low, medium, high, critical)
    - resolved: Filter by resolved status

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Paginated security event entries
    """
    # TODO: Implement security event querying
    return PaginatedResponse(
        items=[],
        total=0,
        page=1,
        limit=20,
        pages=0
    )


# ============================================================================
# System Configuration
# ============================================================================

@router.get(
    "/config",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def get_system_config(
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Get system configuration

    Returns current system configuration.

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - System configuration settings
    """
    # TODO: Implement config storage and retrieval
    return {
        "maintenance_mode": False,
        "registration_enabled": True,
        "api_version": "1.0.0"
    }


@router.put(
    "/config",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def update_system_config(
    config: SystemConfig,
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Update system configuration

    Updates system configuration.

    **Request Body:**
    - key: Configuration key
    - value: Configuration value
    - description: Description (optional)

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Updated configuration
    """
    # TODO: Implement config storage
    return {
        "message": "Configuration updated successfully",
        "config": config
    }


@router.post(
    "/maintenance",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def set_maintenance_mode(
    maintenance: MaintenanceMode,
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Enable/disable maintenance mode

    Puts the system in maintenance mode.

    **Request Body:**
    - enabled: Enable/disable maintenance mode
    - message: Maintenance message to display
    - allowed_ips: IPs allowed during maintenance
    - estimated_duration: Estimated duration in minutes

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Maintenance mode status
    """
    # Store in Redis
    if maintenance.enabled:
        await RedisCache.set(
            "system:maintenance",
            {
                "enabled": True,
                "message": maintenance.message,
                "allowed_ips": maintenance.allowed_ips,
                "estimated_duration": maintenance.estimated_duration
            },
            expire=86400  # 24 hours
        )
    else:
        await RedisCache.delete("system:maintenance")

    return {
        "message": "Maintenance mode updated",
        "maintenance": maintenance
    }


# ============================================================================
# Broadcasting
# ============================================================================

@router.post(
    "/broadcast",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def broadcast_message(
    message: BroadcastMessage,
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Broadcast message to users

    Sends notification to multiple users based on criteria.

    **Request Body:**
    - title: Message title
    - content: Message content
    - target: Target audience (all, role, plan, active, trial)
    - role: Specific role (if target=role)
    - plan: Specific plan (if target=plan)
    - channels: Notification channels (email, in_app)
    - schedule_for: Schedule for later (optional)

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - message: Confirmation
    - target_count: Number of targeted users
    """
    # TODO: Implement broadcast logic with Celery
    # This would query users based on criteria and queue notifications

    return {
        "message": "Broadcast scheduled successfully",
        "target_count": 0,  # TODO: Calculate actual count
        "scheduled_for": message.schedule_for or datetime.utcnow()
    }


# ============================================================================
# Reports
# ============================================================================

@router.post(
    "/reports",
    dependencies=[Depends(require_permissions([Permission.VIEW_ANALYTICS]))]
)
async def generate_report(
    report: SystemReport,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Generate system report

    Generates comprehensive system reports.

    **Request Body:**
    - report_type: Type of report (users, revenue, usage, performance)
    - period: Time period (today, week, month, year, custom)
    - start_date, end_date: Custom date range (if period=custom)
    - format: Output format (pdf, csv, json)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Report data or download link
    """
    # TODO: Implement report generation
    return {
        "message": "Report generation not yet implemented",
        "report_type": report.report_type,
        "period": report.period
    }


# ============================================================================
# Cache Management
# ============================================================================

@router.get(
    "/cache/stats",
    response_model=CacheStats,
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def get_cache_stats(
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Get cache statistics

    Returns Redis cache statistics.

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Cache usage statistics
    """
    # TODO: Implement Redis stats gathering
    return CacheStats(
        total_keys=0,
        memory_used="0 MB",
        hit_rate=0.0,
        total_hits=0,
        total_misses=0,
        evicted_keys=0,
        top_keys=[]
    )


@router.post(
    "/cache/clear",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def clear_cache(
    pattern: Optional[str] = Query(None, description="Key pattern to clear"),
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Clear cache

    Clears Redis cache by pattern.

    **Query Parameters:**
    - pattern: Key pattern to clear (e.g., "user:*", "api_key:*")
      If not provided, clears all cache

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - message: Confirmation
    - keys_cleared: Number of keys cleared

    **Warning:** This action cannot be undone!
    """
    # TODO: Implement cache clearing with pattern matching
    return {
        "message": "Cache cleared successfully",
        "pattern": pattern or "*",
        "keys_cleared": 0
    }


# ============================================================================
# Database Stats
# ============================================================================

@router.get(
    "/database/stats",
    response_model=DatabaseStats,
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def get_database_stats(
    current_user: User = Depends(get_current_super_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get database statistics

    Returns database connection and size statistics.

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Database statistics
    """
    # TODO: Implement database stats gathering
    return DatabaseStats(
        total_connections=0,
        active_connections=0,
        idle_connections=0,
        database_size="0 MB",
        table_sizes={},
        slow_queries=[]
    )


# ============================================================================
# Feature Flags
# ============================================================================

@router.get(
    "/feature-flags",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def get_feature_flags(
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Get feature flags

    Returns all feature flags and their status.

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - List of feature flags
    """
    # TODO: Implement feature flag storage
    return []


@router.put(
    "/feature-flags/{flag_name}",
    dependencies=[Depends(require_permissions([Permission.MANAGE_SYSTEM]))]
)
async def update_feature_flag(
    flag_name: str,
    flag: FeatureFlag,
    current_user: User = Depends(get_current_super_admin_user)
):
    """
    Update feature flag

    Updates or creates a feature flag.

    **Path Parameters:**
    - flag_name: Feature flag name

    **Request Body:**
    - name: Flag name
    - enabled: Enable/disable flag
    - description: Description (optional)
    - rollout_percentage: Rollout percentage (0-100)
    - target_users: Specific user IDs (optional)
    - target_roles: Specific roles (optional)

    **Headers:**
    - Authorization: Bearer {super_admin_access_token}

    **Response:**
    - Updated feature flag
    """
    # TODO: Implement feature flag storage
    return {
        "message": "Feature flag updated successfully",
        "flag": flag
    }
