"""
Webhook background tasks
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.services.webhook_service import WebhookService
from app.models import WebhookDelivery, WebhookStatus


@celery_app.task(name="app.tasks.webhook_tasks.deliver_webhook", bind=True)
def deliver_webhook(self, delivery_id: int) -> Dict[str, Any]:
    """
    Deliver webhook in background

    Args:
        delivery_id: Webhook delivery ID

    Returns:
        Delivery result
    """
    async def _deliver():
        async with AsyncSessionLocal() as db:
            try:
                delivery = await WebhookService.deliver_webhook(db, delivery_id)

                return {
                    "delivery_id": delivery.id,
                    "status": delivery.status.value,
                    "response_status": delivery.response_status_code,
                    "retry_count": delivery.retry_count
                }

            except Exception as e:
                # If delivery fails and has retries left, schedule retry
                delivery = await WebhookService.get_delivery_by_id(db, delivery_id)

                if delivery and delivery.retry_count < 5:  # Max 5 retries
                    # Exponential backoff: 2^retry_count minutes
                    countdown = 60 * (2 ** delivery.retry_count)

                    # Schedule retry
                    self.retry(countdown=countdown, exc=e)

                raise

    return asyncio.run(_deliver())


@celery_app.task(name="app.tasks.webhook_tasks.retry_failed_webhooks")
def retry_failed_webhooks() -> Dict[str, int]:
    """
    Retry failed webhook deliveries (periodic task)

    Returns:
        Count of retried deliveries
    """
    async def _retry():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            # Find failed deliveries that are due for retry
            now = datetime.utcnow()

            result = await db.execute(
                select(WebhookDelivery)
                .where(
                    WebhookDelivery.status == WebhookStatus.FAILED,
                    WebhookDelivery.retry_count < 5,
                    WebhookDelivery.next_retry_at <= now
                )
                .limit(100)  # Process 100 at a time
            )

            deliveries = result.scalars().all()

            # Trigger delivery for each
            for delivery in deliveries:
                deliver_webhook.delay(delivery.id)

            return {
                "retried_count": len(deliveries)
            }

    return asyncio.run(_retry())


@celery_app.task(name="app.tasks.webhook_tasks.send_webhook_event")
def send_webhook_event(
    user_id: int,
    event_type: str,
    payload: Dict[str, Any],
    organization_id: int = None
) -> Dict[str, int]:
    """
    Send webhook event to all subscribed webhooks

    Args:
        user_id: User ID
        event_type: Event type (e.g., "api_key.created")
        payload: Event payload
        organization_id: Optional organization ID

    Returns:
        Count of webhooks triggered
    """
    async def _send():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.models import Webhook

            # Find all webhooks subscribed to this event
            query = select(Webhook).where(
                Webhook.user_id == user_id,
                Webhook.is_active == True
            )

            if organization_id:
                query = query.where(Webhook.organization_id == organization_id)

            result = await db.execute(query)
            webhooks = result.scalars().all()

            triggered_count = 0

            for webhook in webhooks:
                # Check if webhook is subscribed to this event
                if "*" in webhook.events or event_type in webhook.events:
                    # Create delivery record
                    delivery = await WebhookService.create_delivery(
                        db,
                        webhook_id=webhook.id,
                        event_type=event_type,
                        payload=payload
                    )

                    # Trigger delivery in background
                    deliver_webhook.delay(delivery.id)

                    triggered_count += 1

            return {
                "triggered_count": triggered_count
            }

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.webhook_tasks.cleanup_old_deliveries")
def cleanup_old_deliveries(days: int = 30) -> Dict[str, int]:
    """
    Clean up old webhook deliveries

    Args:
        days: Delete deliveries older than this many days

    Returns:
        Count of deleted deliveries
    """
    async def _cleanup():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import delete

            cutoff_date = datetime.utcnow() - timedelta(days=days)

            # Delete successful deliveries older than cutoff
            result = await db.execute(
                delete(WebhookDelivery)
                .where(
                    WebhookDelivery.status == WebhookStatus.SUCCESS,
                    WebhookDelivery.created_at < cutoff_date
                )
            )

            await db.commit()

            return {
                "deleted_count": result.rowcount
            }

    return asyncio.run(_cleanup())
