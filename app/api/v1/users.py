"""
Users API endpoints - User profile management and settings
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.user import UserResponse, UserUpdate, UserListResponse
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.user_service import UserService
from app.api.dependencies import (
    get_current_user,
    get_current_admin_user,
    require_permissions,
    get_pagination_params
)
from app.models import User, UserRole, UserStatus
from app.core.permissions import Permission


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile

    Returns the full profile of the authenticated user.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Complete user profile with all fields
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile

    Updates the authenticated user's profile information.

    **Request Body:**
    - full_name: Full name (optional)
    - phone_number: Phone number (optional)
    - company_name: Company name (optional)
    - bio: Biography/description (optional)
    - avatar_url: Avatar image URL (optional)
    - timezone: User's timezone (optional)
    - language: Preferred language (optional)
    - notification_preferences: JSON notification settings (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Updated user profile
    """
    updated_user = await UserService.update(db, current_user.id, user_data)

    return UserResponse.model_validate(updated_user)


@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's account

    Soft deletes the authenticated user's account by setting status to DELETED.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Confirmation message

    **Note:** This is a soft delete. Account data is retained but inaccessible.
    Contact support to permanently delete data.
    """
    await UserService.delete(db, current_user.id)

    return {"message": "Account has been deleted successfully"}


@router.get("/me/stats")
async def get_my_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's statistics

    Returns usage statistics and account information for the authenticated user.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - credits: Current credit balance
    - api_keys_count: Number of API keys
    - api_calls_today: API calls made today
    - api_calls_month: API calls made this month
    - subscription_plan: Current subscription plan
    - member_since: Account creation date
    """
    # This is a simplified version - you might want to create a dedicated stats service
    from app.services.api_key_service import ApiKeyService
    from app.services.analytics_service import AnalyticsService
    from datetime import datetime, timedelta

    # Count API keys
    api_keys, total_keys = await ApiKeyService.list_keys(
        db,
        user_id=current_user.id,
        pagination=PaginationParams(skip=0, limit=1000)
    )

    # Get usage stats for today and this month
    today = datetime.utcnow().date()
    month_start = datetime.utcnow().replace(day=1)

    # You would implement these in AnalyticsService
    # For now, returning basic stats
    return {
        "credits": current_user.credits,
        "api_keys_count": total_keys,
        "subscription_plan": current_user.plan.value if hasattr(current_user, 'plan') else None,
        "member_since": current_user.created_at,
        "last_login": current_user.last_login_at,
        "total_logins": current_user.login_count,
        "email_verified": current_user.email_verified,
        "two_factor_enabled": current_user.two_factor_enabled
    }


# ============================================================================
# Admin Endpoints - User Management
# ============================================================================

@router.get(
    "",
    response_model=PaginatedResponse[UserListResponse],
    dependencies=[Depends(require_permissions([Permission.MANAGE_USERS]))]
)
async def list_users(
    search: Optional[str] = Query(None, description="Search by email, username, or name"),
    role: Optional[UserRole] = Query(None, description="Filter by role"),
    status: Optional[UserStatus] = Query(None, description="Filter by status"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List all users (Admin only)

    Returns paginated list of users with filtering and sorting.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - search: Search by email, username, or full name
    - role: Filter by role (user, admin, super_admin)
    - status: Filter by status (active, inactive, suspended, deleted)
    - sort_by: Sort field (created_at, email, username, last_login_at)
    - sort_order: Sort order (asc, desc)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - items: List of users
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    pagination_params = PaginationParams(**pagination)

    users, total = await UserService.list_users(
        db,
        pagination=pagination_params,
        search=search,
        role=role,
        status=status,
        sort_by=sort_by,
        sort_order=sort_order
    )

    return PaginatedResponse(
        items=[UserListResponse.model_validate(u) for u in users],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions([Permission.MANAGE_USERS]))]
)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (Admin only)

    Returns full user profile by ID.

    **Path Parameters:**
    - user_id: User ID

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Complete user profile
    """
    user = await UserService.get_by_id(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/suspend",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions([Permission.MANAGE_USERS]))]
)
async def suspend_user(
    user_id: int,
    reason: str = Query(..., description="Reason for suspension"),
    duration_days: Optional[int] = Query(None, description="Suspension duration in days"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Suspend user account (Admin only)

    Suspends a user account with optional duration.

    **Path Parameters:**
    - user_id: User ID to suspend

    **Query Parameters:**
    - reason: Reason for suspension (required)
    - duration_days: Duration in days (optional, permanent if not specified)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Updated user profile with suspended status
    """
    suspended_user = await UserService.suspend(
        db,
        user_id=user_id,
        reason=reason,
        duration_days=duration_days
    )

    return UserResponse.model_validate(suspended_user)


@router.put(
    "/{user_id}/activate",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions([Permission.MANAGE_USERS]))]
)
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate suspended user (Admin only)

    Activates a suspended user account.

    **Path Parameters:**
    - user_id: User ID to activate

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Updated user profile with active status
    """
    activated_user = await UserService.activate(db, user_id)

    return UserResponse.model_validate(activated_user)


@router.post(
    "/{user_id}/credits",
    response_model=UserResponse,
    dependencies=[Depends(require_permissions([Permission.MANAGE_BILLING]))]
)
async def add_credits_to_user(
    user_id: int,
    credits: int = Query(..., ge=1, description="Number of credits to add"),
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Add credits to user account (Admin only)

    Adds credits to a user's account balance.

    **Path Parameters:**
    - user_id: User ID

    **Query Parameters:**
    - credits: Number of credits to add (minimum: 1)

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - Updated user profile with new credit balance
    """
    updated_user = await UserService.add_credits(db, user_id, credits)

    return UserResponse.model_validate(updated_user)


@router.get(
    "/stats/overview",
    dependencies=[Depends(require_permissions([Permission.VIEW_ANALYTICS]))]
)
async def get_users_overview(
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user statistics overview (Admin only)

    Returns aggregate statistics about users.

    **Headers:**
    - Authorization: Bearer {admin_access_token}

    **Response:**
    - total: Total users
    - active: Active users
    - suspended: Suspended users
    - inactive: Inactive users
    - new_today: New users today
    """
    stats = await UserService.get_stats(db)

    return stats
