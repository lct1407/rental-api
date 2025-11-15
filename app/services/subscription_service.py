"""
Subscription Service - Business logic for subscription and billing management
Supports both Stripe and PayPal payment providers
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from datetime import datetime, timedelta
from decimal import Decimal

from app.models import (
    Subscription,
    Payment,
    Invoice,
    CreditTransaction,
    SubscriptionPlan,
    SubscriptionStatus,
    PaymentProvider,
    PaymentStatus,
    User
)
from app.schemas import (
    SubscriptionCreate,
    SubscriptionUpdate,
    PaymentCreate,
    CreditPurchaseRequest,
    PaginationParams
)
from app.services.user_service import UserService


# Subscription plan pricing (in USD)
PLAN_PRICING = {
    SubscriptionPlan.FREE: {"monthly": Decimal("0.00"), "yearly": Decimal("0.00")},
    SubscriptionPlan.BASIC: {"monthly": Decimal("19.99"), "yearly": Decimal("199.99")},
    SubscriptionPlan.PRO: {"monthly": Decimal("49.99"), "yearly": Decimal("499.99")},
    SubscriptionPlan.ENTERPRISE: {"monthly": Decimal("199.99"), "yearly": Decimal("1999.99")},
}

# Plan features and limits
PLAN_FEATURES = {
    SubscriptionPlan.FREE: {
        "features": ["1,000 API calls/month", "Basic analytics", "Email support"],
        "limits": {
            "api_calls_per_month": 1000,
            "max_api_keys": 1,
            "max_webhooks": 1,
            "storage_mb": 100,
        }
    },
    SubscriptionPlan.BASIC: {
        "features": [
            "50,000 API calls/month",
            "Advanced analytics",
            "Priority email support",
            "5 API keys",
            "5 webhooks"
        ],
        "limits": {
            "api_calls_per_month": 50000,
            "max_api_keys": 5,
            "max_webhooks": 5,
            "storage_mb": 1024,
        }
    },
    SubscriptionPlan.PRO: {
        "features": [
            "500,000 API calls/month",
            "Real-time analytics",
            "24/7 priority support",
            "20 API keys",
            "20 webhooks",
            "Custom integrations"
        ],
        "limits": {
            "api_calls_per_month": 500000,
            "max_api_keys": 20,
            "max_webhooks": 20,
            "storage_mb": 10240,
        }
    },
    SubscriptionPlan.ENTERPRISE: {
        "features": [
            "Unlimited API calls",
            "Custom analytics",
            "Dedicated support",
            "Unlimited API keys",
            "Unlimited webhooks",
            "SLA guarantee",
            "Custom features"
        ],
        "limits": {
            "api_calls_per_month": -1,  # Unlimited
            "max_api_keys": -1,
            "max_webhooks": -1,
            "storage_mb": -1,
        }
    },
}


class SubscriptionService:
    """Service for subscription and billing operations"""

    @staticmethod
    async def get_plan_info(plan: SubscriptionPlan) -> Dict[str, Any]:
        """Get subscription plan information"""
        pricing = PLAN_PRICING.get(plan, {"monthly": Decimal("0.00"), "yearly": Decimal("0.00")})
        features_info = PLAN_FEATURES.get(plan, {"features": [], "limits": {}})

        return {
            "plan": plan,
            "name": plan.value.title(),
            "description": f"{plan.value.title()} plan",
            "price_monthly": pricing["monthly"],
            "price_yearly": pricing["yearly"],
            "features": features_info["features"],
            "limits": features_info["limits"],
            "popular": plan == SubscriptionPlan.PRO  # Mark PRO as popular
        }

    @staticmethod
    async def get_all_plans() -> List[Dict[str, Any]]:
        """Get all subscription plans"""
        plans = []
        for plan in SubscriptionPlan:
            plan_info = await SubscriptionService.get_plan_info(plan)
            plans.append(plan_info)
        return plans

    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        user_id: int,
        subscription_data: SubscriptionCreate
    ) -> Subscription:
        """Create a new subscription"""
        # Check if user already has an active subscription
        existing = await SubscriptionService.get_active_subscription(db, user_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active subscription"
            )

        # Get pricing
        pricing = PLAN_PRICING[subscription_data.plan]
        price = pricing["monthly"] if subscription_data.billing_cycle == "monthly" else pricing["yearly"]

        # Get features and limits
        features_info = PLAN_FEATURES[subscription_data.plan]

        # Create subscription
        subscription = Subscription(
            user_id=user_id,
            organization_id=subscription_data.organization_id,
            plan=subscription_data.plan,
            status=SubscriptionStatus.TRIALING if subscription_data.plan != SubscriptionPlan.FREE else SubscriptionStatus.ACTIVE,
            billing_cycle=subscription_data.billing_cycle,
            price=price,
            currency="USD",
            provider=subscription_data.payment_provider,
            features=features_info["features"],
            limits=features_info["limits"],
        )

        # Set trial period for paid plans (14 days)
        if subscription_data.plan != SubscriptionPlan.FREE:
            subscription.trial_start = datetime.utcnow()
            subscription.trial_end = datetime.utcnow() + timedelta(days=14)

        # Set billing period
        subscription.current_period_start = datetime.utcnow()
        if subscription_data.billing_cycle == "monthly":
            subscription.current_period_end = datetime.utcnow() + timedelta(days=30)
        else:
            subscription.current_period_end = datetime.utcnow() + timedelta(days=365)

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)

        # Update user limits based on plan
        await SubscriptionService.apply_plan_limits(db, user_id, subscription_data.plan)

        # For paid plans, create initial payment (will be processed by Stripe/PayPal)
        if subscription_data.plan != SubscriptionPlan.FREE:
            # Payment creation handled separately through payment service
            pass

        return subscription

    @staticmethod
    async def get_active_subscription(
        db: AsyncSession,
        user_id: int
    ) -> Optional[Subscription]:
        """Get user's active subscription"""
        result = await db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status.in_([
                        SubscriptionStatus.ACTIVE,
                        SubscriptionStatus.TRIALING,
                        SubscriptionStatus.PAST_DUE
                    ])
                )
            )
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_subscription(
        db: AsyncSession,
        subscription_id: int,
        update_data: SubscriptionUpdate
    ) -> Subscription:
        """Update subscription (change plan or billing cycle)"""
        subscription = await db.get(Subscription, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if subscription.status == SubscriptionStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update canceled subscription"
            )

        # Update plan
        if update_data.plan and update_data.plan != subscription.plan:
            old_plan = subscription.plan
            subscription.plan = update_data.plan

            # Update pricing
            pricing = PLAN_PRICING[update_data.plan]
            subscription.price = pricing["monthly"] if subscription.billing_cycle == "monthly" else pricing["yearly"]

            # Update features and limits
            features_info = PLAN_FEATURES[update_data.plan]
            subscription.features = features_info["features"]
            subscription.limits = features_info["limits"]

            # Apply new limits to user
            await SubscriptionService.apply_plan_limits(db, subscription.user_id, update_data.plan)

        # Update billing cycle
        if update_data.billing_cycle and update_data.billing_cycle != subscription.billing_cycle:
            subscription.billing_cycle = update_data.billing_cycle
            pricing = PLAN_PRICING[subscription.plan]
            subscription.price = pricing["monthly"] if update_data.billing_cycle == "monthly" else pricing["yearly"]

        await db.commit()
        await db.refresh(subscription)

        return subscription

    @staticmethod
    async def cancel_subscription(
        db: AsyncSession,
        subscription_id: int,
        cancel_at_period_end: bool = True,
        reason: Optional[str] = None
    ) -> Subscription:
        """Cancel subscription"""
        subscription = await db.get(Subscription, subscription_id)
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Subscription not found"
            )

        if subscription.status == SubscriptionStatus.CANCELED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Subscription is already canceled"
            )

        subscription.canceled_at = datetime.utcnow()

        if cancel_at_period_end:
            # Keep subscription active until period end
            subscription.status = SubscriptionStatus.ACTIVE
            # Will be set to CANCELED by background job after period end
        else:
            # Cancel immediately
            subscription.status = SubscriptionStatus.CANCELED
            subscription.ended_at = datetime.utcnow()

            # Downgrade to free plan
            await SubscriptionService.apply_plan_limits(db, subscription.user_id, SubscriptionPlan.FREE)

        # Store cancellation reason in metadata
        if not subscription.metadata:
            subscription.metadata = {}
        subscription.metadata["cancellation_reason"] = reason

        await db.commit()
        await db.refresh(subscription)

        return subscription

    @staticmethod
    async def apply_plan_limits(
        db: AsyncSession,
        user_id: int,
        plan: SubscriptionPlan
    ) -> None:
        """Apply subscription plan limits to user"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            return

        limits = PLAN_FEATURES[plan]["limits"]

        # Update user limits
        if limits["max_api_keys"] > 0:
            user.max_api_keys = limits["max_api_keys"]
        else:
            user.max_api_keys = 999  # Unlimited

        if limits["max_webhooks"] > 0:
            user.max_webhooks = limits["max_webhooks"]
        else:
            user.max_webhooks = 999  # Unlimited

        if limits["storage_mb"] > 0:
            user.storage_limit = limits["storage_mb"]
        else:
            user.storage_limit = 999999  # Unlimited

        await db.commit()

    # Credit Management

    @staticmethod
    async def purchase_credits(
        db: AsyncSession,
        user_id: int,
        purchase_data: CreditPurchaseRequest
    ) -> Dict[str, Any]:
        """Purchase credits"""
        # Calculate price (example: $0.01 per credit)
        price_per_credit = Decimal("0.01")
        total_amount = Decimal(purchase_data.credits) * price_per_credit

        # Create payment record
        payment = Payment(
            user_id=user_id,
            amount=total_amount,
            currency="USD",
            status=PaymentStatus.PENDING,
            provider=purchase_data.payment_provider,
            description=f"Purchase {purchase_data.credits} credits",
            credits_purchased=purchase_data.credits
        )

        db.add(payment)
        await db.commit()
        await db.refresh(payment)

        # Payment processing handled by Stripe/PayPal service
        # After successful payment, credits will be added via webhook

        return {
            "payment_id": payment.id,
            "credits": purchase_data.credits,
            "amount": total_amount,
            "currency": "USD",
            "provider": purchase_data.payment_provider
        }

    @staticmethod
    async def add_credits_after_payment(
        db: AsyncSession,
        payment_id: int
    ) -> CreditTransaction:
        """Add credits to user after successful payment"""
        payment = await db.get(Payment, payment_id)
        if not payment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment not found"
            )

        if payment.status != PaymentStatus.SUCCEEDED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment has not been completed"
            )

        # Add credits to user
        user = await UserService.get_by_id(db, payment.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        old_balance = user.credits
        user.credits += payment.credits_purchased

        # Create credit transaction record
        transaction = CreditTransaction(
            user_id=payment.user_id,
            payment_id=payment_id,
            amount=payment.credits_purchased,
            balance_after=user.credits,
            transaction_type="purchase",
            description=f"Purchased {payment.credits_purchased} credits"
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return transaction

    @staticmethod
    async def consume_credits_for_usage(
        db: AsyncSession,
        user_id: int,
        credits: int,
        description: str
    ) -> CreditTransaction:
        """Consume credits for API usage"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if user.credits < credits:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Insufficient credits"
            )

        # Consume credits
        user.credits -= credits

        # Create transaction record
        transaction = CreditTransaction(
            user_id=user_id,
            amount=-credits,  # Negative for consumption
            balance_after=user.credits,
            transaction_type="usage",
            description=description
        )

        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        return transaction

    @staticmethod
    async def get_credit_balance(
        db: AsyncSession,
        user_id: int
    ) -> Dict[str, Any]:
        """Get user's credit balance and history"""
        user = await UserService.get_by_id(db, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Get recent transactions
        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.user_id == user_id)
            .order_by(CreditTransaction.created_at.desc())
            .limit(10)
        )
        recent_transactions = result.scalars().all()

        # Calculate totals
        total_purchased_result = await db.execute(
            select(func.sum(CreditTransaction.amount))
            .where(
                and_(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.transaction_type == "purchase"
                )
            )
        )
        total_purchased = total_purchased_result.scalar_one() or 0

        total_used_result = await db.execute(
            select(func.sum(CreditTransaction.amount))
            .where(
                and_(
                    CreditTransaction.user_id == user_id,
                    CreditTransaction.transaction_type == "usage"
                )
            )
        )
        total_used = abs(total_used_result.scalar_one() or 0)

        return {
            "user_id": user_id,
            "current_balance": user.credits,
            "total_purchased": total_purchased,
            "total_used": total_used,
            "recent_transactions": recent_transactions
        }
