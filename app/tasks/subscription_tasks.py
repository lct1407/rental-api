"""
Subscription and billing background tasks
"""
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.core.celery_app import celery_app
from app.database import AsyncSessionLocal
from app.models import Subscription, SubscriptionStatus, User
from app.tasks.email_tasks import send_expiring_subscription_reminder, send_subscription_confirmation


@celery_app.task(name="app.tasks.subscription_tasks.check_expiring_subscriptions")
def check_expiring_subscriptions() -> Dict[str, int]:
    """
    Check for expiring subscriptions and send reminders (periodic task)

    Returns:
        Count of reminders sent
    """
    async def _check():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            now = datetime.utcnow()
            reminder_dates = [
                now + timedelta(days=7),   # 7 days before expiry
                now + timedelta(days=3),   # 3 days before expiry
                now + timedelta(days=1)    # 1 day before expiry
            ]

            reminders_sent = 0

            for reminder_date in reminder_dates:
                result = await db.execute(
                    select(Subscription, User)
                    .join(User, Subscription.user_id == User.id)
                    .where(
                        Subscription.status == SubscriptionStatus.ACTIVE,
                        Subscription.cancel_at_period_end == True,
                        Subscription.current_period_end >= now,
                        Subscription.current_period_end <= reminder_date
                    )
                )

                subscriptions = result.all()

                for subscription, user in subscriptions:
                    days_until_expiry = (subscription.current_period_end - now).days

                    # Send reminder email
                    send_expiring_subscription_reminder.delay(
                        email=user.email,
                        user_name=user.full_name,
                        plan_name=subscription.plan.value,
                        days_until_expiry=days_until_expiry
                    )

                    reminders_sent += 1

            return {
                "reminders_sent": reminders_sent
            }

    return asyncio.run(_check())


@celery_app.task(name="app.tasks.subscription_tasks.renew_subscriptions")
def renew_subscriptions() -> Dict[str, Any]:
    """
    Auto-renew subscriptions (periodic task)

    Returns:
        Renewal statistics
    """
    async def _renew():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.services.subscription_service import SubscriptionService

            now = datetime.utcnow()

            # Find subscriptions due for renewal
            result = await db.execute(
                select(Subscription)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.auto_renew == True,
                    Subscription.current_period_end <= now
                )
            )

            subscriptions = result.scalars().all()

            renewed_count = 0
            failed_count = 0

            for subscription in subscriptions:
                try:
                    # Process renewal
                    await SubscriptionService.renew_subscription(db, subscription.id)
                    renewed_count += 1

                except Exception as e:
                    print(f"Failed to renew subscription {subscription.id}: {e}")
                    # Mark subscription as past_due
                    subscription.status = SubscriptionStatus.PAST_DUE
                    await db.commit()
                    failed_count += 1

            return {
                "renewed_count": renewed_count,
                "failed_count": failed_count,
                "total": len(subscriptions)
            }

    return asyncio.run(_renew())


@celery_app.task(name="app.tasks.subscription_tasks.cancel_expired_subscriptions")
def cancel_expired_subscriptions() -> Dict[str, int]:
    """
    Cancel subscriptions that are past their grace period

    Returns:
        Count of cancelled subscriptions
    """
    async def _cancel():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            now = datetime.utcnow()
            grace_period = timedelta(days=7)  # 7 day grace period
            cutoff = now - grace_period

            # Find past_due subscriptions beyond grace period
            result = await db.execute(
                select(Subscription)
                .where(
                    Subscription.status == SubscriptionStatus.PAST_DUE,
                    Subscription.current_period_end < cutoff
                )
            )

            subscriptions = result.scalars().all()

            for subscription in subscriptions:
                subscription.status = SubscriptionStatus.CANCELLED
                subscription.cancelled_at = now

            await db.commit()

            return {
                "cancelled_count": len(subscriptions)
            }

    return asyncio.run(_cancel())


@celery_app.task(name="app.tasks.subscription_tasks.allocate_monthly_credits")
def allocate_monthly_credits() -> Dict[str, Any]:
    """
    Allocate monthly credits to active subscriptions (periodic task)

    Returns:
        Allocation statistics
    """
    async def _allocate():
        async with AsyncSessionLocal() as db:
            from sqlalchemy import select
            from app.models import CreditTransaction, TransactionType, SubscriptionPlan

            # Credit allocation per plan
            PLAN_CREDITS = {
                SubscriptionPlan.FREE: 100,
                SubscriptionPlan.BASIC: 1000,
                SubscriptionPlan.PRO: 5000,
                SubscriptionPlan.ENTERPRISE: 50000
            }

            now = datetime.utcnow()
            first_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

            # Find active subscriptions
            result = await db.execute(
                select(Subscription, User)
                .join(User, Subscription.user_id == User.id)
                .where(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.current_period_start <= now,
                    Subscription.current_period_end >= now
                )
            )

            subscriptions = result.all()
            allocated_count = 0

            for subscription, user in subscriptions:
                credits_to_add = PLAN_CREDITS.get(subscription.plan, 0)

                if credits_to_add > 0:
                    # Add credits to user
                    user.credits += credits_to_add

                    # Create transaction record
                    transaction = CreditTransaction(
                        user_id=user.id,
                        amount=credits_to_add,
                        transaction_type=TransactionType.SUBSCRIPTION,
                        description=f"{subscription.plan.value} plan monthly credits",
                        reference_id=subscription.id,
                        reference_type="subscription",
                        balance_after=user.credits
                    )
                    db.add(transaction)

                    allocated_count += 1

            await db.commit()

            return {
                "allocated_count": allocated_count,
                "timestamp": now.isoformat()
            }

    return asyncio.run(_allocate())


@celery_app.task(name="app.tasks.subscription_tasks.process_payment")
def process_payment(
    user_id: int,
    amount: float,
    currency: str,
    provider: str,
    payment_method_id: str,
    description: str
) -> Dict[str, Any]:
    """
    Process payment asynchronously

    Args:
        user_id: User ID
        amount: Amount to charge
        currency: Currency code
        provider: Payment provider (stripe/paypal)
        payment_method_id: Payment method ID
        description: Payment description

    Returns:
        Payment result
    """
    async def _process():
        async with AsyncSessionLocal() as db:
            from decimal import Decimal
            from app.services.payment_service import PaymentService, StripePaymentService, PayPalPaymentService
            from app.schemas.subscription import PaymentCreate
            from app.models import PaymentProvider

            try:
                # Create payment record
                payment_data = PaymentCreate(
                    amount=Decimal(str(amount)),
                    currency=currency,
                    provider=PaymentProvider.STRIPE if provider == "stripe" else PaymentProvider.PAYPAL,
                    payment_method=payment_method_id,
                    description=description
                )

                payment = await PaymentService.create_payment(db, user_id, payment_data)

                # Process with provider
                if provider == "stripe":
                    result = await StripePaymentService.create_payment_intent(
                        Decimal(str(amount)),
                        currency,
                        payment_method_id
                    )
                else:
                    result = await PayPalPaymentService.create_order(
                        Decimal(str(amount)),
                        currency,
                        description
                    )

                return {
                    "payment_id": payment.id,
                    "status": "completed",
                    "provider_transaction_id": result.get("id")
                }

            except Exception as e:
                return {
                    "status": "failed",
                    "error": str(e)
                }

    return asyncio.run(_process())
