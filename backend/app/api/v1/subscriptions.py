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
    SubscriptionPlanResponse
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

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
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
