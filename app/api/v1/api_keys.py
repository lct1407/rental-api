"""
API Keys endpoints - API key management
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyWithSecret,
    ApiKeyListResponse
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.api_key_service import ApiKeyService
from app.api.dependencies import (
    get_current_user,
    get_pagination_params,
    require_permissions
)
from app.models import User
from app.core.permissions import Permission


router = APIRouter(prefix="/api-keys", tags=["API Keys"])


@router.post(
    "",
    response_model=ApiKeyWithSecret,
    status_code=status.HTTP_201_CREATED
)
async def create_api_key(
    key_data: ApiKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new API key

    Creates a new API key for the authenticated user. The full API key is
    returned only once - save it securely!

    **Request Body:**
    - name: Descriptive name for the key (required)
    - description: Optional description
    - organization_id: Optional organization ID (for organization keys)
    - scopes: List of permission scopes (default: ["read:*"])
    - ip_whitelist: List of allowed IP addresses (optional)
    - allowed_origins: List of allowed origins for CORS (optional)
    - rate_limit_per_hour: Custom hourly rate limit (optional)
    - rate_limit_per_day: Custom daily rate limit (optional)
    - expires_in_days: Expiration in days (optional, no expiration if not set)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - id: API key ID
    - key: **Full API key (only shown once!)**
    - name, description, scopes, etc.

    **IMPORTANT:** The full API key is only returned once. Store it securely!
    """
    api_key, full_key = await ApiKeyService.create(
        db,
        user_id=current_user.id,
        api_key_data=key_data
    )

    # Send email notification (in production)
    # await EmailService.send_api_key_created_notification(
    #     current_user.email,
    #     current_user.full_name,
    #     api_key.name
    # )

    return ApiKeyWithSecret(
        **ApiKeyResponse.model_validate(api_key).model_dump(),
        key=full_key
    )


@router.get("", response_model=PaginatedResponse[ApiKeyListResponse])
async def list_my_api_keys(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List API keys

    Returns paginated list of API keys for the authenticated user.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - organization_id: Filter by organization (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of API keys (without full key!)
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages

    **Note:** Full API keys are never returned in list endpoints, only
    the prefix and last 4 characters.
    """
    pagination_params = PaginationParams(**pagination)

    keys, total = await ApiKeyService.list_keys(
        db,
        user_id=current_user.id,
        organization_id=organization_id,
        pagination=pagination_params
    )

    return PaginatedResponse(
        items=[ApiKeyListResponse.model_validate(k) for k in keys],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


@router.get("/{key_id}", response_model=ApiKeyResponse)
async def get_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get API key details

    Returns details of a specific API key.

    **Path Parameters:**
    - key_id: API key ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - API key details (without full key)

    **Note:** Full API key is never returned after creation. You can only
    see the prefix and last 4 characters.
    """
    api_key = await ApiKeyService.get_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return ApiKeyResponse.model_validate(api_key)


@router.put("/{key_id}", response_model=ApiKeyResponse)
async def update_api_key(
    key_id: int,
    key_data: ApiKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update API key

    Updates API key configuration (name, description, scopes, etc.)

    **Path Parameters:**
    - key_id: API key ID

    **Request Body:**
    - name: New name (optional)
    - description: New description (optional)
    - scopes: New scopes (optional)
    - ip_whitelist: New IP whitelist (optional)
    - allowed_origins: New allowed origins (optional)
    - rate_limit_per_hour: New hourly rate limit (optional)
    - rate_limit_per_day: New daily rate limit (optional)
    - is_active: Enable/disable key (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Updated API key details

    **Note:** The actual key value cannot be changed. Use rotate endpoint
    to generate a new key while keeping configuration.
    """
    api_key = await ApiKeyService.get_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    updated_key = await ApiKeyService.update(db, key_id, key_data)

    return ApiKeyResponse.model_validate(updated_key)


@router.delete("/{key_id}")
async def delete_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete API key

    Permanently deletes an API key. This action cannot be undone.

    **Path Parameters:**
    - key_id: API key ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Confirmation message

    **Warning:** All requests using this API key will be rejected immediately.
    """
    api_key = await ApiKeyService.get_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    await ApiKeyService.delete(db, key_id)

    return {"message": "API key has been deleted successfully"}


@router.post("/{key_id}/rotate", response_model=ApiKeyWithSecret)
async def rotate_api_key(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Rotate API key

    Generates a new key value while keeping all configuration (name, scopes,
    rate limits, etc.). The old key is immediately invalidated.

    **Path Parameters:**
    - key_id: API key ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - id: API key ID (same)
    - key: **New full API key (only shown once!)**
    - name, description, scopes, etc. (unchanged)

    **IMPORTANT:**
    - The old key is immediately invalidated
    - The new key is only shown once - save it securely!
    - Update all applications using this key
    """
    api_key = await ApiKeyService.get_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    rotated_key, new_full_key = await ApiKeyService.rotate(db, key_id)

    # Send email notification (in production)
    # await EmailService.send_api_key_rotated_notification(
    #     current_user.email,
    #     current_user.full_name,
    #     rotated_key.name
    # )

    return ApiKeyWithSecret(
        **ApiKeyResponse.model_validate(rotated_key).model_dump(),
        key=new_full_key
    )


@router.get("/{key_id}/usage")
async def get_api_key_usage(
    key_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get API key usage statistics

    Returns usage statistics for a specific API key.

    **Path Parameters:**
    - key_id: API key ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - usage_count: Total requests made with this key
    - last_used_at: Last usage timestamp
    - last_used_ip: Last IP address that used the key
    - hourly_limit: Hourly rate limit
    - daily_limit: Daily rate limit
    - hourly_remaining: Remaining hourly requests
    - daily_remaining: Remaining daily requests
    """
    api_key = await ApiKeyService.get_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Get rate limit usage from Redis
    from app.core.cache import RedisCache

    hour_key = f"rate_limit:api_key:{api_key.id}:hour"
    day_key = f"rate_limit:api_key:{api_key.id}:day"

    hour_count = await RedisCache.get(hour_key)
    day_count = await RedisCache.get(day_key)

    hourly_used = int(hour_count) if hour_count else 0
    daily_used = int(day_count) if day_count else 0

    return {
        "usage_count": api_key.usage_count,
        "last_used_at": api_key.last_used_at,
        "last_used_ip": api_key.last_used_ip,
        "hourly_limit": api_key.rate_limit_per_hour,
        "daily_limit": api_key.rate_limit_per_day,
        "hourly_used": hourly_used,
        "hourly_remaining": max(0, api_key.rate_limit_per_hour - hourly_used),
        "daily_used": daily_used,
        "daily_remaining": max(0, api_key.rate_limit_per_day - daily_used),
        "is_active": api_key.is_active,
        "expires_at": api_key.expires_at,
        "is_expired": api_key.is_expired()
    }


@router.get("/{key_id}/logs")
async def get_api_key_logs(
    key_id: int,
    endpoint: Optional[str] = Query(None, description="Filter by endpoint"),
    method: Optional[str] = Query(None, description="Filter by HTTP method"),
    status: Optional[int] = Query(None, description="Filter by status code"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get API key request history/logs

    Returns paginated request logs for a specific API key with optional filters.

    **Path Parameters:**
    - key_id: API key ID

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - endpoint: Filter by endpoint path (optional)
    - method: Filter by HTTP method (GET, POST, etc) (optional)
    - status: Filter by HTTP status code (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of request logs with method, endpoint, status, credits, latency, timestamp
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    from sqlalchemy import select, and_, func
    from app.models import ApiUsageLog

    api_key = await ApiKeyService.get_by_id(db, key_id)

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found"
        )

    # Verify ownership
    if api_key.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Build query conditions
    conditions = [ApiUsageLog.api_key_id == key_id]

    if endpoint:
        conditions.append(ApiUsageLog.endpoint.ilike(f"%{endpoint}%"))

    if method:
        conditions.append(ApiUsageLog.method == method.upper())

    if status is not None:
        conditions.append(ApiUsageLog.status_code == status)

    # Get paginated logs
    query = select(ApiUsageLog).where(
        and_(*conditions)
    ).order_by(
        ApiUsageLog.created_at.desc()
    ).limit(
        pagination["limit"]
    ).offset(
        pagination["skip"]
    )

    result = await db.execute(query)
    logs = result.scalars().all()

    # Get total count
    count_query = select(func.count(ApiUsageLog.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Format response
    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "method": log.method,
            "endpoint": log.endpoint,
            "status": log.status_code,
            "credits": log.credits_consumed,
            "latency": log.response_time_ms,
            "timestamp": log.created_at.isoformat() if log.created_at else None,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent
        })

    return PaginatedResponse(
        items=items,
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )
