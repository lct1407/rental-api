"""
Webhook Service - Business logic for webhook management and delivery
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
import httpx
import hmac
import hashlib
import json

from app.models import Webhook, WebhookDelivery, WebhookStatus, User
from app.schemas import WebhookCreate, WebhookUpdate, PaginationParams
from app.core.cache import RedisCache
from app.services.user_service import UserService


class WebhookService:
    """Service for webhook operations"""

    @staticmethod
    async def create(
        db: AsyncSession,
        user_id: int,
        webhook_data: WebhookCreate
    ) -> Webhook:
        """Create a new webhook"""
        # Check if user has reached limit
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Count existing webhooks
        count_result = await db.execute(
            select(func.count(Webhook.id))
            .where(Webhook.user_id == user_id, Webhook.is_active == True)
        )
        webhook_count = count_result.scalar_one()

        if webhook_count >= user.max_webhooks:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Maximum webhook limit reached ({user.max_webhooks})"
            )

        # Generate secret if not provided
        import secrets
        webhook_secret = webhook_data.secret or secrets.token_urlsafe(32)

        # Create webhook
        webhook = Webhook(
            user_id=user_id,
            organization_id=webhook_data.organization_id,
            name=webhook_data.name,
            url=str(webhook_data.url),
            description=webhook_data.description,
            secret=webhook_secret,
            events=webhook_data.events,
            headers=webhook_data.headers or {},
            max_retries=webhook_data.max_retries,
            retry_delay=webhook_data.retry_delay,
            timeout=webhook_data.timeout,
        )

        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)

        return webhook

    @staticmethod
    async def get_by_id(db: AsyncSession, webhook_id: int) -> Optional[Webhook]:
        """Get webhook by ID"""
        result = await db.execute(
            select(Webhook).where(Webhook.id == webhook_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_webhooks(
        db: AsyncSession,
        user_id: int,
        organization_id: Optional[int] = None,
        pagination: Optional[PaginationParams] = None
    ) -> tuple[List[Webhook], int]:
        """List webhooks for a user or organization"""
        query = select(Webhook).where(Webhook.user_id == user_id)

        if organization_id:
            query = query.where(Webhook.organization_id == organization_id)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        # Order by creation date
        query = query.order_by(Webhook.created_at.desc())

        # Execute
        result = await db.execute(query)
        webhooks = result.scalars().all()

        return list(webhooks), total

    @staticmethod
    async def update(
        db: AsyncSession,
        webhook_id: int,
        webhook_data: WebhookUpdate
    ) -> Webhook:
        """Update webhook"""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        # Update fields
        update_data = webhook_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "url" and value:
                value = str(value)
            setattr(webhook, field, value)

        await db.commit()
        await db.refresh(webhook)

        return webhook

    @staticmethod
    async def delete(db: AsyncSession, webhook_id: int) -> bool:
        """Delete webhook"""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        await db.delete(webhook)
        await db.commit()

        return True

    @staticmethod
    def generate_signature(payload: str, secret: str) -> str:
        """Generate webhook signature using HMAC-SHA256"""
        signature = hmac.new(
            secret.encode(),
            payload.encode(),
            hashlib.sha256
        ).hexdigest()
        return f"sha256={signature}"

    @staticmethod
    async def trigger_webhook(
        db: AsyncSession,
        webhook_id: int,
        event_type: str,
        payload: Dict[str, Any]
    ) -> WebhookDelivery:
        """Trigger a webhook delivery"""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        if not webhook.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Webhook is not active"
            )

        # Check if webhook is subscribed to this event
        if event_type not in webhook.events and not any(
            event.endswith('.*') and event_type.startswith(event[:-2])
            for event in webhook.events
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Webhook is not subscribed to event: {event_type}"
            )

        # Create delivery record
        delivery = WebhookDelivery(
            webhook_id=webhook_id,
            event_type=event_type,
            payload=payload,
            status=WebhookStatus.PENDING
        )

        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)

        # Queue delivery for background processing
        # In production, this would be sent to Celery
        # For now, we'll deliver synchronously
        await WebhookService.deliver_webhook(db, delivery.id)

        return delivery

    @staticmethod
    async def deliver_webhook(
        db: AsyncSession,
        delivery_id: int
    ) -> WebhookDelivery:
        """Deliver webhook (actual HTTP request)"""
        # Get delivery and webhook
        result = await db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook delivery not found"
            )

        webhook = await WebhookService.get_by_id(db, delivery.webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        # Prepare payload
        payload_json = json.dumps(delivery.payload, separators=(',', ':'))

        # Generate signature
        signature = WebhookService.generate_signature(payload_json, webhook.secret)

        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Signature": signature,
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Delivery": str(delivery.id),
            "User-Agent": "API-Management-Webhook/1.0"
        }

        # Add custom headers
        if webhook.headers:
            headers.update(webhook.headers)

        # Store request details
        delivery.request_headers = headers
        delivery.request_body = delivery.payload

        # Attempt delivery
        start_time = datetime.utcnow()
        delivery.status = WebhookStatus.PENDING

        try:
            async with httpx.AsyncClient(timeout=webhook.timeout) as client:
                response = await client.post(
                    webhook.url,
                    content=payload_json,
                    headers=headers
                )

                # Calculate response time
                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Store response
                delivery.status_code = response.status_code
                delivery.response_time_ms = int(response_time)
                delivery.response_headers = dict(response.headers)

                try:
                    delivery.response_body = response.text
                except Exception:
                    delivery.response_body = None

                # Check if successful (2xx status codes)
                if 200 <= response.status_code < 300:
                    delivery.status = WebhookStatus.SUCCESS
                    delivery.success = True

                    # Update webhook statistics
                    webhook.success_count += 1
                    webhook.last_triggered_at = datetime.utcnow()
                else:
                    delivery.status = WebhookStatus.FAILED
                    delivery.success = False
                    delivery.error_message = f"HTTP {response.status_code}: {response.text[:500]}"

                    # Update webhook statistics
                    webhook.failure_count += 1
                    webhook.last_error = delivery.error_message

        except httpx.TimeoutException as e:
            delivery.status = WebhookStatus.FAILED
            delivery.success = False
            delivery.error_message = f"Timeout after {webhook.timeout}s"
            webhook.failure_count += 1
            webhook.last_error = delivery.error_message

        except httpx.RequestError as e:
            delivery.status = WebhookStatus.FAILED
            delivery.success = False
            delivery.error_message = f"Request error: {str(e)}"
            webhook.failure_count += 1
            webhook.last_error = delivery.error_message

        except Exception as e:
            delivery.status = WebhookStatus.FAILED
            delivery.success = False
            delivery.error_message = f"Unexpected error: {str(e)}"
            delivery.error_traceback = str(e)
            webhook.failure_count += 1
            webhook.last_error = delivery.error_message

        # Schedule retry if failed and retries remaining
        if not delivery.success and delivery.retry_count < webhook.max_retries:
            delivery.status = WebhookStatus.RETRYING
            delivery.next_retry_at = datetime.utcnow() + timedelta(
                seconds=webhook.retry_delay * (2 ** delivery.retry_count)  # Exponential backoff
            )
            delivery.retry_count += 1

        await db.commit()
        await db.refresh(delivery)

        return delivery

    @staticmethod
    async def retry_delivery(
        db: AsyncSession,
        delivery_id: int
    ) -> WebhookDelivery:
        """Retry a failed webhook delivery"""
        result = await db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        delivery = result.scalar_one_or_none()

        if not delivery:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook delivery not found"
            )

        if delivery.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot retry successful delivery"
            )

        # Attempt delivery again
        return await WebhookService.deliver_webhook(db, delivery_id)

    @staticmethod
    async def verify_webhook(
        db: AsyncSession,
        webhook_id: int
    ) -> bool:
        """Verify webhook URL by sending a test ping"""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        # Send test event
        test_payload = {
            "event": "webhook.test",
            "webhook_id": webhook_id,
            "timestamp": datetime.utcnow().isoformat(),
            "message": "This is a test webhook delivery"
        }

        delivery = await WebhookService.trigger_webhook(
            db,
            webhook_id,
            "webhook.test",
            test_payload
        )

        if delivery.success:
            webhook.verified = True
            await db.commit()
            return True

        return False

    @staticmethod
    async def get_deliveries(
        db: AsyncSession,
        webhook_id: int,
        pagination: Optional[PaginationParams] = None,
        status_filter: Optional[WebhookStatus] = None
    ) -> tuple[List[WebhookDelivery], int]:
        """Get webhook delivery history"""
        query = select(WebhookDelivery).where(WebhookDelivery.webhook_id == webhook_id)

        if status_filter:
            query = query.where(WebhookDelivery.status == status_filter)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination
        if pagination:
            query = query.offset(pagination.skip).limit(pagination.limit)

        # Order by creation date (newest first)
        query = query.order_by(WebhookDelivery.created_at.desc())

        # Execute
        result = await db.execute(query)
        deliveries = result.scalars().all()

        return list(deliveries), total

    @staticmethod
    async def get_delivery_by_id(
        db: AsyncSession,
        delivery_id: int
    ) -> Optional[WebhookDelivery]:
        """Get specific delivery by ID"""
        result = await db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_webhook_stats(
        db: AsyncSession,
        webhook_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get webhook statistics"""
        webhook = await WebhookService.get_by_id(db, webhook_id)
        if not webhook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Webhook not found"
            )

        # Get deliveries from last N days
        since = datetime.utcnow() - timedelta(days=days)

        # Total deliveries
        total_result = await db.execute(
            select(func.count(WebhookDelivery.id))
            .where(
                and_(
                    WebhookDelivery.webhook_id == webhook_id,
                    WebhookDelivery.created_at >= since
                )
            )
        )
        total_deliveries = total_result.scalar_one()

        # Successful deliveries
        success_result = await db.execute(
            select(func.count(WebhookDelivery.id))
            .where(
                and_(
                    WebhookDelivery.webhook_id == webhook_id,
                    WebhookDelivery.success == True,
                    WebhookDelivery.created_at >= since
                )
            )
        )
        successful_deliveries = success_result.scalar_one()

        # Failed deliveries
        failed_deliveries = total_deliveries - successful_deliveries

        # Pending deliveries
        pending_result = await db.execute(
            select(func.count(WebhookDelivery.id))
            .where(
                and_(
                    WebhookDelivery.webhook_id == webhook_id,
                    WebhookDelivery.status.in_([WebhookStatus.PENDING, WebhookStatus.RETRYING])
                )
            )
        )
        pending_deliveries = pending_result.scalar_one()

        # Average response time
        avg_time_result = await db.execute(
            select(func.avg(WebhookDelivery.response_time_ms))
            .where(
                and_(
                    WebhookDelivery.webhook_id == webhook_id,
                    WebhookDelivery.success == True,
                    WebhookDelivery.created_at >= since
                )
            )
        )
        avg_response_time = avg_time_result.scalar_one() or 0

        # Calculate success rate
        success_rate = (successful_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

        return {
            "webhook_id": webhook_id,
            "total_deliveries": total_deliveries,
            "successful_deliveries": successful_deliveries,
            "failed_deliveries": failed_deliveries,
            "pending_deliveries": pending_deliveries,
            "success_rate": round(success_rate, 2),
            "avg_response_time": round(avg_response_time, 2),
            "period_days": days
        }
