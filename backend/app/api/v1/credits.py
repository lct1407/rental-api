"""
Credit Management API Endpoints
User-facing endpoints for viewing balance, transactions, and purchasing credits
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.credit import CreditLedger, CreditType, CreditTransactionType
from app.services.credit_service import CreditService
from app.schemas.credit import (
    CreditBalanceResponse,
    CreditLedgerResponse,
    CreditActivityResponse,
    CreditPurchaseRequest,
    CreditPurchaseResponse,
    CreditPricingResponse,
    FeatureCostResponse,
    CreditConsumptionSimulation,
    CreditConsumptionResponse,
    CreditUsageReport
)
from sqlalchemy import select

router = APIRouter(prefix="/credits", tags=["Credits"])


@router.get("/balance", response_model=CreditBalanceResponse)
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current credit balance with detailed breakdown

    Returns:
        - Total balance across all credit types
        - Monthly, purchased, and bonus balances
        - Consumption stats
        - Active credit packages
        - Expiring credits warning
    """
    balance = await CreditService.get_credit_balance(
        db, current_user.id, include_packages=True
    )

    return balance


@router.get("/transactions", response_model=CreditActivityResponse)
async def get_credit_transactions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Max number of records to return"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    transaction_type: Optional[CreditTransactionType] = Query(None, description="Filter by transaction type"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit transaction history with pagination and filters

    Query Parameters:
        - skip: Pagination offset
        - limit: Number of records per page
        - start_date: Filter transactions from this date
        - end_date: Filter transactions until this date
        - transaction_type: Filter by type (credit, debit, expire, etc.)
    """
    # Default date range if not provided
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=90)

    if not end_date:
        end_date = datetime.utcnow()

    # Get transactions
    transactions, total = await CreditService.get_transaction_history(
        db=db,
        user_id=current_user.id,
        start_date=start_date,
        end_date=end_date,
        transaction_type=transaction_type,
        skip=skip,
        limit=limit
    )

    # Calculate pagination
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1

    # Convert to response format
    transaction_responses = []
    for txn in transactions:
        # Get admin name if admin action
        admin_name = None
        if txn.admin_id:
            admin_result = await db.execute(
                select(User).where(User.id == txn.admin_id)
            )
            admin = admin_result.scalar_one_or_none()
            if admin:
                admin_name = admin.full_name or admin.username

        transaction_responses.append(CreditLedgerResponse(
            id=txn.id,
            transaction_type=txn.transaction_type,
            credit_type=txn.credit_type,
            amount=txn.amount,
            balance_before=txn.balance_before,
            balance_after=txn.balance_after,
            description=txn.description,
            feature_name=txn.feature_name,
            source_type=txn.source_type,
            source_id=txn.source_id,
            admin_id=txn.admin_id,
            admin_name=admin_name,
            admin_notes=txn.admin_notes,
            metadata=txn.metadata,
            created_at=txn.created_at,
            ip_address=txn.ip_address
        ))

    return CreditActivityResponse(
        total=total,
        page=current_page,
        page_size=limit,
        total_pages=total_pages,
        transactions=transaction_responses
    )


@router.post("/simulate", response_model=CreditConsumptionResponse)
async def simulate_credit_consumption(
    simulation: CreditConsumptionSimulation,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Simulate credit consumption without actually consuming credits

    Useful for:
        - Checking if user has enough credits
        - Previewing credit cost before making request
        - Building credit usage estimators
    """
    try:
        can_consume, result = await CreditService.consume_credits(
            db=db,
            user_id=current_user.id,
            feature_key=simulation.feature_key,
            metadata=simulation.metadata,
            check_only=True
        )

        warnings = []

        # Add warnings if approaching low balance
        if result.get("available_credits", 0) < 100:
            warnings.append("Credit balance is low. Consider purchasing more credits.")

        return CreditConsumptionResponse(
            can_consume=can_consume,
            required_credits=result.get("required_credits", 0),
            available_credits=result.get("available_credits", 0),
            remaining_after=result.get("remaining_after"),
            warnings=warnings
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to simulate consumption: {str(e)}"
        )


@router.get("/pricing", response_model=List[CreditPricingResponse])
async def get_credit_pricing(
    db: AsyncSession = Depends(get_db)
):
    """
    Get available credit packages for purchase

    Returns all active credit pricing tiers with:
        - Credit amount
        - Price and currency
        - Discounts
        - Validity period
        - Features/benefits
    """
    from app.models.credit import CreditPricing

    result = await db.execute(
        select(CreditPricing)
        .where(CreditPricing.is_active == True)
        .order_by(CreditPricing.display_order, CreditPricing.credits)
    )
    packages = result.scalars().all()

    pricing_responses = []
    for pkg in packages:
        price_per_credit = float(pkg.price) / pkg.credits if pkg.credits > 0 else 0

        pricing_responses.append(CreditPricingResponse(
            id=pkg.id,
            name=pkg.name,
            display_name=pkg.display_name,
            credits=pkg.credits,
            price=pkg.price,
            currency=pkg.currency,
            discount_percentage=pkg.discount_percentage,
            original_price=pkg.original_price,
            price_per_credit=price_per_credit,
            validity_days=pkg.valid_days,
            is_featured=pkg.is_featured,
            is_popular=pkg.is_popular,
            badge_text=pkg.badge_text,
            description=pkg.description,
            features=pkg.features
        ))

    return pricing_responses


@router.post("/purchase", response_model=CreditPurchaseResponse)
async def purchase_credits(
    purchase_request: CreditPurchaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Purchase additional credits

    Creates a Stripe/PayPal checkout session for credit purchase.
    After successful payment, credits are automatically added to wallet.
    """
    from app.models.credit import CreditPricing
    from app.services.payment_service import PaymentService

    # Get pricing package
    pricing_result = await db.execute(
        select(CreditPricing).where(
            CreditPricing.id == purchase_request.pricing_id,
            CreditPricing.is_active == True
        )
    )
    pricing = pricing_result.scalar_one_or_none()

    if not pricing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pricing package not found"
        )

    # Validate quantity
    if pricing.min_purchase_count and purchase_request.quantity < pricing.min_purchase_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Minimum purchase quantity is {pricing.min_purchase_count}"
        )

    if pricing.max_purchase_count and purchase_request.quantity > pricing.max_purchase_count:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Maximum purchase quantity is {pricing.max_purchase_count}"
        )

    # Calculate total
    total_credits = pricing.credits * purchase_request.quantity
    total_price = float(pricing.price) * purchase_request.quantity

    # Create checkout session
    try:
        # This is a placeholder - you'll need to implement actual payment integration
        checkout_url = f"https://checkout.stripe.com/pay/..."
        session_id = f"cs_{current_user.id}_{datetime.utcnow().timestamp()}"

        # In production, use PaymentService to create actual Stripe/PayPal session
        # checkout_session = await PaymentService.create_credit_purchase_session(
        #     user_id=current_user.id,
        #     pricing_id=pricing.id,
        #     quantity=purchase_request.quantity,
        #     success_url=purchase_request.success_url,
        #     cancel_url=purchase_request.cancel_url
        # )

        return CreditPurchaseResponse(
            checkout_url=checkout_url,
            session_id=session_id,
            amount=total_credits,
            credits=total_credits,
            price=total_price,
            currency=pricing.currency,
            expires_in_days=pricing.valid_days
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create checkout session: {str(e)}"
        )


@router.get("/features/costs", response_model=List[FeatureCostResponse])
async def get_feature_costs(
    category: Optional[str] = Query(None, description="Filter by category"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credit costs for all features

    Shows how many credits each API feature consumes.
    Useful for cost planning and budgeting.
    """
    from app.models.credit import FeatureDefinition

    query = select(FeatureDefinition).where(FeatureDefinition.is_active == True)

    if category:
        query = query.where(FeatureDefinition.category == category)

    query = query.order_by(FeatureDefinition.category, FeatureDefinition.display_order)

    result = await db.execute(query)
    features = result.scalars().all()

    feature_responses = []
    for feature in features:
        feature_responses.append(FeatureCostResponse(
            id=feature.id,
            feature_key=feature.feature_key,
            feature_name=feature.feature_name,
            category=feature.category,
            credit_cost=feature.credit_cost,
            admin_exempt=feature.admin_exempt,
            super_admin_exempt=feature.super_admin_exempt,
            rpm_limit=feature.rpm_limit,
            rph_limit=feature.rph_limit,
            rpd_limit=feature.rpd_limit,
            rpm_limit_monthly=feature.rpm_limit_monthly,
            cost_modifiers=feature.cost_modifiers,
            plan_overrides=feature.plan_overrides,
            description=feature.description,
            is_active=feature.is_active
        ))

    return feature_responses


@router.get("/usage/report", response_model=CreditUsageReport)
async def get_usage_report(
    month: int = Query(..., ge=1, le=12, description="Month (1-12)"),
    year: int = Query(..., ge=2024, description="Year"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get monthly credit usage report

    Provides detailed breakdown of:
        - Total credits consumed
        - Usage by feature
        - Usage by day
        - Top consuming features
        - Average cost per request
    """
    from sqlalchemy import func

    # Calculate period start and end
    period_start = datetime(year, month, 1)
    if month == 12:
        period_end = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        period_end = datetime(year, month + 1, 1) - timedelta(seconds=1)

    # Get all debit transactions in period
    debits_result = await db.execute(
        select(CreditLedger).where(
            CreditLedger.user_id == current_user.id,
            CreditLedger.transaction_type == CreditTransactionType.DEBIT,
            CreditLedger.created_at >= period_start,
            CreditLedger.created_at <= period_end
        )
    )
    debits = debits_result.scalars().all()

    # Calculate totals
    total_credits_consumed = sum(abs(d.amount) for d in debits)
    total_requests = len(debits)
    average_cost = total_credits_consumed / total_requests if total_requests > 0 else 0

    # Group by feature
    by_feature_dict = {}
    for debit in debits:
        feature_key = debit.metadata.get("feature_key", "unknown")
        feature_name = debit.feature_name or "Unknown"

        if feature_key not in by_feature_dict:
            by_feature_dict[feature_key] = {
                "feature_key": feature_key,
                "feature_name": feature_name,
                "credits_consumed": 0,
                "request_count": 0
            }

        by_feature_dict[feature_key]["credits_consumed"] += abs(debit.amount)
        by_feature_dict[feature_key]["request_count"] += 1

    # Calculate percentages
    by_feature = []
    for feature_data in by_feature_dict.values():
        percentage = (feature_data["credits_consumed"] / total_credits_consumed * 100) if total_credits_consumed > 0 else 0
        feature_data["percentage_of_total"] = round(percentage, 2)
        by_feature.append(feature_data)

    # Sort by consumption
    by_feature.sort(key=lambda x: x["credits_consumed"], reverse=True)
    top_consuming = by_feature[:5]

    # Group by day
    by_day_dict = {}
    for debit in debits:
        day_key = debit.created_at.strftime("%Y-%m-%d")

        if day_key not in by_day_dict:
            by_day_dict[day_key] = {
                "date": day_key,
                "credits_consumed": 0,
                "request_count": 0
            }

        by_day_dict[day_key]["credits_consumed"] += abs(debit.amount)
        by_day_dict[day_key]["request_count"] += 1

    by_day = sorted(by_day_dict.values(), key=lambda x: x["date"])

    return CreditUsageReport(
        period_start=period_start,
        period_end=period_end,
        total_credits_consumed=total_credits_consumed,
        total_requests=total_requests,
        average_cost_per_request=round(average_cost, 2),
        by_feature=by_feature,
        by_day=by_day,
        top_consuming_features=top_consuming
    )


@router.get("/expiring", response_model=List[dict])
async def get_expiring_credits(
    days: int = Query(30, ge=1, le=365, description="Days ahead to check"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get credits expiring within specified days

    Helps users track and use credits before they expire.
    """
    from app.models.credit import CreditPackage

    cutoff_date = datetime.utcnow() + timedelta(days=days)

    result = await db.execute(
        select(CreditPackage).where(
            CreditPackage.user_id == current_user.id,
            CreditPackage.is_expired == False,
            CreditPackage.remaining_amount > 0,
            CreditPackage.expires_at <= cutoff_date
        ).order_by(CreditPackage.expires_at)
    )
    packages = result.scalars().all()

    expiring_packages = []
    for pkg in packages:
        days_until_expiry = (pkg.expires_at - datetime.utcnow()).days

        expiring_packages.append({
            "id": pkg.id,
            "credit_type": pkg.credit_type,
            "remaining_amount": pkg.remaining_amount,
            "original_amount": pkg.original_amount,
            "expires_at": pkg.expires_at.isoformat(),
            "days_until_expiry": max(0, days_until_expiry),
            "created_at": pkg.created_at.isoformat()
        })

    return expiring_packages
