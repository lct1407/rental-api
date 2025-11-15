"""
Webhooks endpoints - Webhook management and delivery tracking
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookDeliveryResponse,
    WebhookTestRequest
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.webhook_service import WebhookService
from app.api.dependencies import (
    get_current_user,
    get_pagination_params
)
from app.models import User


router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post(
    "",
    response_model=WebhookResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_webhook(
    webhook_data: WebhookCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new webhook

    Creates a webhook endpoint to receive event notifications.

    **Request Body:**
    - url: Webhook endpoint URL (must be HTTPS in production)
    - events: List of events to subscribe to
      - Available events: api_key.created, api_key.deleted, payment.succeeded,
        payment.failed, subscription.created, subscription.cancelled, etc.
    - description: Optional description
    - organization_id: Optional organization ID
    - is_active: Enable/disable webhook (default: true)
    - secret: Optional webhook secret for signature verification (auto-generated if not provided)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Webhook configuration with generated secret

    **Important:** Save the webhook secret securely. Use it to verify webhook
    signatures to ensure requests are coming from our platform.
    """
    webhook = await WebhookService.create(
        db,
        user_id=current_user.id,
        webhook_data=webhook_data
    )

    return WebhookResponse.model_validate(webhook)


@router.get("", response_model=PaginatedResponse[WebhookListResponse])
async def list_webhooks(
    organization_id: Optional[int] = Query(None, description="Filter by organization"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List webhooks

    Returns paginated list of webhooks for the authenticated user.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - organization_id: Filter by organization (optional)
    - is_active: Filter by active status (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of webhooks
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    pagination_params = PaginationParams(**pagination)

    webhooks, total = await WebhookService.list_webhooks(
        db,
        user_id=current_user.id,
        organization_id=organization_id,
        is_active=is_active,
        pagination=pagination_params
    )

    return PaginatedResponse(
        items=[WebhookListResponse.model_validate(w) for w in webhooks],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


@router.get("/{webhook_id}", response_model=WebhookResponse)
async def get_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get webhook details

    Returns details of a specific webhook.

    **Path Parameters:**
    - webhook_id: Webhook ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Webhook configuration and statistics
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return WebhookResponse.model_validate(webhook)


@router.put("/{webhook_id}", response_model=WebhookResponse)
async def update_webhook(
    webhook_id: int,
    webhook_data: WebhookUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update webhook

    Updates webhook configuration.

    **Path Parameters:**
    - webhook_id: Webhook ID

    **Request Body:**
    - url: New webhook URL (optional)
    - events: New event subscriptions (optional)
    - description: New description (optional)
    - is_active: Enable/disable webhook (optional)
    - secret: New webhook secret (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Updated webhook configuration
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    updated_webhook = await WebhookService.update(db, webhook_id, webhook_data)

    return WebhookResponse.model_validate(updated_webhook)


@router.delete("/{webhook_id}")
async def delete_webhook(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete webhook

    Permanently deletes a webhook.

    **Path Parameters:**
    - webhook_id: Webhook ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Confirmation message

    **Note:** All pending deliveries for this webhook will be cancelled.
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    await WebhookService.delete(db, webhook_id)

    return {"message": "Webhook has been deleted successfully"}


@router.post("/{webhook_id}/test")
async def test_webhook(
    webhook_id: int,
    test_data: WebhookTestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test webhook

    Sends a test payload to the webhook endpoint to verify configuration.

    **Path Parameters:**
    - webhook_id: Webhook ID

    **Request Body:**
    - event_type: Event type to test (optional, defaults to "test.webhook")
    - payload: Custom test payload (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Test initiated
    - delivery_id: Webhook delivery ID to track the test

    **Note:** Check the delivery status endpoint to see if the test succeeded.
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Create test delivery
    test_payload = test_data.payload or {
        "event": test_data.event_type or "test.webhook",
        "data": {
            "test": True,
            "message": "This is a test webhook delivery",
            "timestamp": "2025-11-15T00:00:00Z"
        }
    }

    delivery = await WebhookService.create_delivery(
        db,
        webhook_id=webhook_id,
        event_type=test_data.event_type or "test.webhook",
        payload=test_payload
    )

    # Trigger delivery in background
    background_tasks.add_task(
        WebhookService.deliver_webhook,
        db,
        delivery.id
    )

    return {
        "message": "Test webhook delivery initiated",
        "delivery_id": delivery.id,
        "webhook_url": webhook.url
    }


@router.get("/{webhook_id}/deliveries", response_model=PaginatedResponse[WebhookDeliveryResponse])
async def list_webhook_deliveries(
    webhook_id: int,
    status: Optional[str] = Query(None, description="Filter by status (pending, success, failed)"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List webhook deliveries

    Returns delivery history for a webhook.

    **Path Parameters:**
    - webhook_id: Webhook ID

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - status: Filter by status (pending, success, failed)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of deliveries with status, response, and retry information
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    pagination_params = PaginationParams(**pagination)

    deliveries, total = await WebhookService.list_deliveries(
        db,
        webhook_id=webhook_id,
        status=status,
        pagination=pagination_params
    )

    return PaginatedResponse(
        items=[WebhookDeliveryResponse.model_validate(d) for d in deliveries],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


@router.get("/{webhook_id}/deliveries/{delivery_id}", response_model=WebhookDeliveryResponse)
async def get_webhook_delivery(
    webhook_id: int,
    delivery_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get webhook delivery details

    Returns detailed information about a specific webhook delivery.

    **Path Parameters:**
    - webhook_id: Webhook ID
    - delivery_id: Delivery ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Delivery details including request/response data, status, and retry history
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    delivery = await WebhookService.get_delivery_by_id(db, delivery_id)

    if not delivery or delivery.webhook_id != webhook_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    return WebhookDeliveryResponse.model_validate(delivery)


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry")
async def retry_webhook_delivery(
    webhook_id: int,
    delivery_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retry failed webhook delivery

    Manually retries a failed webhook delivery.

    **Path Parameters:**
    - webhook_id: Webhook ID
    - delivery_id: Delivery ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Retry initiated

    **Note:** This will attempt immediate delivery, bypassing the normal
    exponential backoff schedule.
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    delivery = await WebhookService.get_delivery_by_id(db, delivery_id)

    if not delivery or delivery.webhook_id != webhook_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Delivery not found"
        )

    if delivery.status == "success":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot retry successful delivery"
        )

    # Trigger retry in background
    background_tasks.add_task(
        WebhookService.deliver_webhook,
        db,
        delivery.id
    )

    return {
        "message": "Webhook delivery retry initiated",
        "delivery_id": delivery.id
    }


@router.get("/{webhook_id}/stats")
async def get_webhook_stats(
    webhook_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get webhook statistics

    Returns delivery statistics for a webhook.

    **Path Parameters:**
    - webhook_id: Webhook ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - total_deliveries: Total delivery attempts
    - successful_deliveries: Successful deliveries
    - failed_deliveries: Failed deliveries
    - pending_deliveries: Pending deliveries
    - success_rate: Success rate percentage
    - avg_response_time: Average response time in ms
    - last_delivery_at: Last delivery timestamp
    """
    webhook = await WebhookService.get_by_id(db, webhook_id)

    if not webhook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Webhook not found"
        )

    # Verify ownership
    if webhook.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    stats = await WebhookService.get_webhook_stats(db, webhook_id)

    return stats
