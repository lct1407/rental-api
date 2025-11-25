"""
Subscriptions and Billing endpoints - Subscription management, payments, and billing
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    PaymentCreate,
    PaymentResponse,
    CreditPurchaseRequest,
    InvoiceResponse,
    CreditTransactionResponse,
    SubscriptionPlanInfo
)
from app.schemas.common import PaginationParams, PaginatedResponse
from app.services.subscription_service import SubscriptionService
from app.services.payment_service import PaymentService
from app.api.dependencies import (
    get_current_user,
    get_pagination_params
)
from app.models import User, SubscriptionPlan


router = APIRouter(prefix="/subscriptions", tags=["Subscriptions & Billing"])


# ============================================================================
# Subscription Plans
# ============================================================================

@router.get("/plans", response_model=List[SubscriptionPlanInfo])
async def get_subscription_plans():
    """
    Get available subscription plans

    Returns list of all available subscription plans with pricing and features.

    **Response:**
    - List of subscription plans with:
      - plan: Plan name (free, basic, pro, enterprise)
      - monthly_price: Monthly pricing
      - yearly_price: Yearly pricing (with discount)
      - features: List of features
      - limits: Usage limits

    **Note:** Yearly plans typically offer a discount (e.g., 2 months free).
    """
    plans = await SubscriptionService.get_available_plans()

    return plans


# ============================================================================
# User Subscription Management
# ============================================================================

@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current subscription

    Returns the authenticated user's current subscription details.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Subscription details including plan, status, billing cycle, and expiration
    """
    subscription = await SubscriptionService.get_user_subscription(db, current_user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    return SubscriptionResponse.model_validate(subscription)


@router.post("/subscribe", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new subscription

    Creates a new subscription for the authenticated user.

    **Request Body:**
    - plan: Subscription plan (basic, pro, enterprise)
    - billing_cycle: Billing cycle (monthly, yearly)
    - payment_method: Payment method ID from Stripe/PayPal
    - auto_renew: Auto-renewal enabled (default: true)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Created subscription details

    **Note:** FREE plan is automatically assigned to new users. This endpoint
    is for upgrading to paid plans.
    """
    subscription = await SubscriptionService.create_subscription(
        db,
        user_id=current_user.id,
        subscription_data=subscription_data
    )

    return SubscriptionResponse.model_validate(subscription)


@router.put("/me", response_model=SubscriptionResponse)
async def update_my_subscription(
    subscription_data: SubscriptionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update subscription

    Updates the authenticated user's subscription (upgrade, downgrade, change billing cycle).

    **Request Body:**
    - plan: New plan (optional)
    - billing_cycle: New billing cycle (optional)
    - auto_renew: Enable/disable auto-renewal (optional)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Updated subscription details

    **Note:**
    - Upgrades are applied immediately
    - Downgrades take effect at the end of the current billing period
    """
    subscription = await SubscriptionService.get_user_subscription(db, current_user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    updated_subscription = await SubscriptionService.update_subscription(
        db,
        subscription_id=subscription.id,
        subscription_data=subscription_data
    )

    return SubscriptionResponse.model_validate(updated_subscription)


@router.post("/me/cancel")
async def cancel_my_subscription(
    immediate: bool = Query(False, description="Cancel immediately instead of at period end"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel subscription

    Cancels the authenticated user's subscription.

    **Query Parameters:**
    - immediate: Cancel immediately (default: false - cancels at period end)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - message: Confirmation message
    - effective_date: When cancellation takes effect

    **Note:**
    - By default, you retain access until the end of the billing period
    - Use immediate=true to cancel access immediately (no refund)
    """
    subscription = await SubscriptionService.get_user_subscription(db, current_user.id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )

    cancelled_subscription = await SubscriptionService.cancel_subscription(
        db,
        subscription_id=subscription.id,
        immediate=immediate
    )

    return {
        "message": "Subscription has been cancelled",
        "effective_date": cancelled_subscription.current_period_end,
        "immediate": immediate
    }


# ============================================================================
# Credits
# ============================================================================

@router.get("/credits")
async def get_credit_balance(
    current_user: User = Depends(get_current_user)
):
    """
    Get credit balance

    Returns the authenticated user's current credit balance.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - credits: Current credit balance
    - subscription_credits: Credits from subscription
    - purchased_credits: Purchased additional credits
    """
    return {
        "credits": current_user.credits,
        "user_id": current_user.id
    }


@router.post("/credits/purchase", response_model=PaymentResponse)
async def purchase_credits(
    purchase_data: CreditPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Purchase credits

    Purchases additional credits for the authenticated user.

    **Request Body:**
    - credits: Number of credits to purchase
    - payment_provider: Payment provider (stripe or paypal)
    - payment_method_id: Payment method ID from provider

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - payment: Payment details
    - credits_added: Number of credits added
    - new_balance: New credit balance

    **Pricing:**
    - Credits are typically priced at $0.10 per credit
    - Bulk discounts may apply
    """
    result = await SubscriptionService.purchase_credits(
        db,
        user_id=current_user.id,
        purchase_data=purchase_data
    )

    return result


@router.get("/credits/history", response_model=PaginatedResponse[CreditTransactionResponse])
async def get_credit_history(
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit transaction history

    Returns paginated credit transaction history.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of credit transactions (purchases, usage, refunds)
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    pagination_params = PaginationParams(**pagination)

    transactions, total = await SubscriptionService.get_credit_transactions(
        db,
        user_id=current_user.id,
        pagination=pagination_params
    )

    return PaginatedResponse(
        items=[CreditTransactionResponse.model_validate(t) for t in transactions],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


# ============================================================================
# Payment History
# ============================================================================

@router.get("/payments", response_model=PaginatedResponse[PaymentResponse])
async def get_payment_history(
    status: Optional[str] = Query(None, description="Filter by status"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment history

    Returns paginated payment history.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - status: Filter by status (pending, completed, failed, refunded)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of payments
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    pagination_params = PaginationParams(**pagination)

    payments, total = await PaymentService.get_user_payments(
        db,
        user_id=current_user.id,
        status=status,
        pagination=pagination_params
    )

    return PaginatedResponse(
        items=[PaymentResponse.model_validate(p) for p in payments],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


@router.get("/payments/{payment_id}", response_model=PaymentResponse)
async def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment details

    Returns details of a specific payment.

    **Path Parameters:**
    - payment_id: Payment ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Payment details including status, amount, provider, and transaction ID
    """
    payment = await PaymentService.get_payment_by_id(db, payment_id)

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    # Verify ownership
    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return PaymentResponse.model_validate(payment)


# ============================================================================
# Invoices
# ============================================================================

@router.get("/invoices", response_model=PaginatedResponse[InvoiceResponse])
async def get_invoices(
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get invoices

    Returns paginated list of invoices.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of invoices
    - total: Total count
    - page: Current page
    - limit: Items per page
    - pages: Total pages
    """
    pagination_params = PaginationParams(**pagination)

    invoices, total = await SubscriptionService.get_user_invoices(
        db,
        user_id=current_user.id,
        pagination=pagination_params
    )

    return PaginatedResponse(
        items=[InvoiceResponse.model_validate(i) for i in invoices],
        total=total,
        page=(pagination["skip"] // pagination["limit"]) + 1,
        limit=pagination["limit"],
        pages=(total + pagination["limit"] - 1) // pagination["limit"]
    )


@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get invoice details

    Returns details of a specific invoice.

    **Path Parameters:**
    - invoice_id: Invoice ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Invoice details including items, amounts, and payment status
    """
    invoice = await SubscriptionService.get_invoice_by_id(db, invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Verify ownership
    if invoice.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    return InvoiceResponse.model_validate(invoice)


@router.get("/invoices/{invoice_id}/download")
async def download_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download invoice PDF

    Generates and downloads invoice as PDF.

    **Path Parameters:**
    - invoice_id: Invoice ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - PDF file download

    **Note:** This is a placeholder. Actual PDF generation would be implemented
    using a library like reportlab or weasyprint.
    """
    invoice = await SubscriptionService.get_invoice_by_id(db, invoice_id)

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )

    # Verify ownership
    if invoice.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # TODO: Generate PDF
    # For now, return invoice data
    return {
        "message": "PDF generation not yet implemented",
        "invoice": InvoiceResponse.model_validate(invoice)
    }


# ============================================================================
# Billing Information
# ============================================================================

@router.get("/billing-info")
async def get_billing_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get billing information

    Returns billing information including payment methods and billing address.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Billing information and saved payment methods
    """
    # This would integrate with Stripe/PayPal to get payment methods
    return {
        "user_id": current_user.id,
        "email": current_user.email,
        "payment_methods": [],  # TODO: Fetch from Stripe/PayPal
        "billing_address": None  # TODO: Implement billing address storage
    }


@router.get("/usage-summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage summary

    Returns current billing period usage summary.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - Current usage, limits, and estimated costs
    """
    subscription = await SubscriptionService.get_user_subscription(db, current_user.id)

    # Get current usage stats
    # This would integrate with AnalyticsService
    return {
        "subscription_plan": subscription.plan.value if subscription else SubscriptionPlan.FREE.value,
        "current_period_start": subscription.current_period_start if subscription else None,
        "current_period_end": subscription.current_period_end if subscription else None,
        "credits_remaining": current_user.credits,
        "api_calls_this_period": 0,  # TODO: Get from AnalyticsService
        "estimated_cost": 0.00  # TODO: Calculate based on usage
    }


# ============================================================================
# Credit Purchase & Billing
# ============================================================================

@router.post("/credits/purchase")
async def purchase_credits(
    amount: int = Query(..., ge=5, le=5000, description="Purchase amount in USD ($5-$5000)"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Purchase credits

    Creates a Stripe checkout session for credit purchase with bonus tiers:
    - $5-$49: No bonus
    - $50-$99: 10% bonus
    - $100-$499: 20% bonus
    - $500+: 30% bonus

    **Query Parameters:**
    - amount: Purchase amount in USD (minimum $5, maximum $5000)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - checkout_url: Stripe checkout URL
    - base_credits: Credits for the amount (amount * 100)
    - bonus_credits: Bonus credits based on tier
    - total_credits: Base + bonus credits
    - amount: Purchase amount in USD
    """
    # Calculate base credits (1 USD = 100 credits)
    base_credits = amount * 100

    # Calculate bonus based on tiers
    if amount >= 500:
        bonus_rate = 0.30
    elif amount >= 100:
        bonus_rate = 0.20
    elif amount >= 50:
        bonus_rate = 0.10
    else:
        bonus_rate = 0.0

    bonus_credits = int(base_credits * bonus_rate)
    total_credits = base_credits + bonus_credits

    # Create Stripe checkout session
    checkout_url = await PaymentService.create_credit_purchase_session(
        db=db,
        user=current_user,
        amount=amount,
        credits=total_credits,
        bonus_credits=bonus_credits
    )

    return {
        "checkout_url": checkout_url,
        "base_credits": base_credits,
        "bonus_credits": bonus_credits,
        "total_credits": total_credits,
        "amount": amount,
        "bonus_rate": bonus_rate * 100
    }


@router.get("/billing/invoices", response_model=List[InvoiceResponse])
async def get_my_invoices(
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user invoices

    Returns paginated list of invoices for the authenticated user.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - List of invoices with ID, date, amount, status, PDF link
    """
    from sqlalchemy import select
    from app.models import Invoice

    # Build query
    query = select(Invoice).where(
        Invoice.user_id == current_user.id
    ).order_by(
        Invoice.created_at.desc()
    ).limit(
        pagination["limit"]
    ).offset(
        pagination["skip"]
    )

    result = await db.execute(query)
    invoices = result.scalars().all()

    return [InvoiceResponse.model_validate(inv) for inv in invoices]


@router.get("/billing/payment-method")
async def get_payment_method(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment method

    Returns the user's current payment method on file.

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - type: Payment method type (card, paypal, etc)
    - last4: Last 4 digits of card
    - brand: Card brand (Visa, Mastercard, etc)
    - exp_month: Expiration month
    - exp_year: Expiration year
    """
    from sqlalchemy import select
    from app.models import Payment

    # Get most recent successful payment to extract payment method
    result = await db.execute(
        select(Payment)
        .where(Payment.user_id == current_user.id)
        .where(Payment.status == "succeeded")
        .order_by(Payment.created_at.desc())
        .limit(1)
    )

    payment = result.scalar_one_or_none()

    if not payment:
        return {
            "type": None,
            "last4": None,
            "brand": None,
            "exp_month": None,
            "exp_year": None,
            "message": "No payment method on file"
        }

    return {
        "type": payment.payment_method_type or "card",
        "last4": payment.payment_method_last4 or "****",
        "brand": payment.payment_method_brand or "Unknown",
        "exp_month": 12,  # TODO: Store expiration in payment model
        "exp_year": 2024,  # TODO: Store expiration in payment model
    }


@router.get("/billing/credit-history", response_model=PaginatedResponse[CreditTransactionResponse])
async def get_credit_history(
    date_range: str = Query("30d", description="Time range: 7d, 30d, 90d, all"),
    transaction_type: Optional[str] = Query(None, description="Filter by type: in, out, all"),
    service_id: Optional[int] = Query(None, description="Filter by service ID"),
    pagination: dict = Depends(get_pagination_params),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit transaction history

    Returns paginated credit transaction history with filters.

    **Query Parameters:**
    - page: Page number (default: 1)
    - limit: Items per page (1-100, default: 20)
    - date_range: Time range filter (7d, 30d, 90d, all)
    - transaction_type: Filter by type (in, out, all)
    - service_id: Filter by service ID

    **Headers:**
    - Authorization: Bearer {access_token}

    **Response:**
    - items: List of credit transactions
    - total: Total count
    - summary: Aggregated totals (total_in, total_out, net_change)
    """
    from sqlalchemy import select, and_, func
    from app.models import CreditTransaction, Service
    from datetime import datetime, timedelta

    # Calculate date filter
    now = datetime.utcnow()
    if date_range == "7d":
        start_date = now - timedelta(days=7)
    elif date_range == "30d":
        start_date = now - timedelta(days=30)
    elif date_range == "90d":
        start_date = now - timedelta(days=90)
    else:
        start_date = None

    # Build base query
    conditions = [CreditTransaction.user_id == current_user.id]

    if start_date:
        conditions.append(CreditTransaction.created_at >= start_date)

    if transaction_type == "in":
        conditions.append(CreditTransaction.amount > 0)
    elif transaction_type == "out":
        conditions.append(CreditTransaction.amount < 0)

    if service_id:
        conditions.append(CreditTransaction.service_id == service_id)

    # Get paginated transactions
    query = select(CreditTransaction).where(
        and_(*conditions)
    ).order_by(
        CreditTransaction.created_at.desc()
    ).limit(
        pagination["limit"]
    ).offset(
        pagination["skip"]
    )

    result = await db.execute(query)
    transactions = result.scalars().all()

    # Get total count
    count_query = select(func.count(CreditTransaction.id)).where(and_(*conditions))
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Calculate summary
    summary_query = select(
        func.sum(CreditTransaction.amount).filter(CreditTransaction.amount > 0).label('total_in'),
        func.sum(CreditTransaction.amount).filter(CreditTransaction.amount < 0).label('total_out'),
        func.sum(CreditTransaction.amount).label('net_change')
    ).where(and_(*conditions))

    summary_result = await db.execute(summary_query)
    summary_row = summary_result.one()

    total_in = summary_row.total_in or 0
    total_out = abs(summary_row.total_out or 0)
    net_change = summary_row.net_change or 0

    return {
        "items": [CreditTransactionResponse.model_validate(t) for t in transactions],
        "total": total,
        "page": (pagination["skip"] // pagination["limit"]) + 1,
        "limit": pagination["limit"],
        "pages": (total + pagination["limit"] - 1) // pagination["limit"],
        "summary": {
            "total_in": total_in,
            "total_out": total_out,
            "net_change": net_change
        }
    }
