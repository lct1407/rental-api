"""
Admin Credit Management API Endpoints
Admin-only endpoints for managing credits, features, and system-wide credit operations
"""
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from typing import Optional, List
from datetime import datetime, timedelta

from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User, UserRole
from app.models.credit import (
    CreditWallet, CreditLedger, CreditPackage, FeatureDefinition,
    CreditPricing, RateLimitRule, CreditType, CreditTransactionType
)
from app.models.subscription import Payment
from app.services.credit_service import CreditService
from app.core.permissions import require_role
from app.schemas.credit import (
    AdminGrantCreditsRequest,
    AdminAdjustCreditsRequest,
    AdminCreditAdjustmentResponse,
    AdminCreditOverview,
    FeatureDefinitionCreate,
    FeatureDefinitionUpdate,
    FeatureCostResponse,
    RateLimitRuleCreate,
    RateLimitRuleResponse,
    BulkCreditGrantRequest,
    BulkCreditGrantResponse,
    CreditActivityResponse,
    CreditLedgerResponse
)

router = APIRouter(prefix="/admin/credits", tags=["Admin - Credits"])


# ==================== System Overview ====================

@router.get("/overview", response_model=AdminCreditOverview)
async def get_credit_overview(
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide credit statistics

    Provides overview of:
        - Total credits in system by type
        - Active wallets count
        - Monthly consumption and revenue
        - Top consumers
    """
    # Total credits in system
    totals_result = await db.execute(
        select(
            func.sum(CreditWallet.total_balance).label("total"),
            func.sum(CreditWallet.monthly_balance).label("monthly"),
            func.sum(CreditWallet.purchased_balance).label("purchased"),
            func.sum(CreditWallet.bonus_balance).label("bonus"),
            func.count(CreditWallet.id).label("wallets")
        )
    )
    totals = totals_result.first()

    # Credits consumed this month
    month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    consumption_result = await db.execute(
        select(func.sum(CreditLedger.amount)).where(
            and_(
                CreditLedger.transaction_type == CreditTransactionType.DEBIT,
                CreditLedger.created_at >= month_start
            )
        )
    )
    monthly_consumption = abs(consumption_result.scalar() or 0)

    # Revenue from credit purchases this month
    revenue_result = await db.execute(
        select(func.sum(Payment.amount)).where(
            and_(
                Payment.status == "succeeded",
                Payment.credits_purchased > 0,
                Payment.created_at >= month_start
            )
        )
    )
    monthly_revenue = revenue_result.scalar() or 0

    # Top consumers this month
    top_consumers_result = await db.execute(
        select(
            User.id,
            User.email,
            User.full_name,
            User.username,
            func.sum(func.abs(CreditLedger.amount)).label("consumed")
        ).join(
            CreditLedger, CreditLedger.user_id == User.id
        ).where(
            and_(
                CreditLedger.transaction_type == CreditTransactionType.DEBIT,
                CreditLedger.created_at >= month_start
            )
        ).group_by(User.id).order_by(desc("consumed")).limit(10)
    )

    top_consumers = []
    for row in top_consumers_result:
        top_consumers.append({
            "user_id": row.id,
            "email": row.email,
            "name": row.full_name or row.username,
            "credits_consumed": int(row.consumed)
        })

    total_wallets = totals.wallets or 1  # Avoid division by zero

    return AdminCreditOverview(
        total_credits_in_system=int(totals.total or 0),
        monthly_balance_total=int(totals.monthly or 0),
        purchased_balance_total=int(totals.purchased or 0),
        bonus_balance_total=int(totals.bonus or 0),
        active_wallets=int(totals.wallets or 0),
        monthly_consumption=monthly_consumption,
        monthly_revenue=monthly_revenue,
        average_consumption_per_user=monthly_consumption / total_wallets,
        top_consumers=top_consumers
    )


# ==================== User Credit Management ====================

@router.get("/users/{user_id}", response_model=dict)
async def get_user_credit_details(
    user_id: int,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed credit information for a specific user

    Includes:
        - Current wallet status
        - All active credit packages
        - Recent transaction history
    """
    # Get wallet
    wallet_result = await db.execute(
        select(CreditWallet).where(CreditWallet.user_id == user_id)
    )
    wallet = wallet_result.scalar_one_or_none()

    if not wallet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Credit wallet not found"
        )

    # Get packages
    packages_result = await db.execute(
        select(CreditPackage).where(
            CreditPackage.wallet_id == wallet.id
        ).order_by(CreditPackage.expires_at)
    )
    packages = packages_result.scalars().all()

    # Get recent transactions (last 100)
    transactions_result = await db.execute(
        select(CreditLedger).where(
            CreditLedger.wallet_id == wallet.id
        ).order_by(desc(CreditLedger.created_at)).limit(100)
    )
    transactions = transactions_result.scalars().all()

    # Get user info
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "username": user.username,
            "role": user.role
        },
        "wallet": {
            "id": wallet.id,
            "total_balance": wallet.total_balance,
            "monthly_balance": wallet.monthly_balance,
            "purchased_balance": wallet.purchased_balance,
            "bonus_balance": wallet.bonus_balance,
            "total_consumed": wallet.total_consumed,
            "monthly_consumed": wallet.monthly_consumed,
            "lifetime_consumed": wallet.lifetime_consumed,
            "last_reset": wallet.last_monthly_reset.isoformat() if wallet.last_monthly_reset else None,
            "next_reset": wallet.next_monthly_reset.isoformat() if wallet.next_monthly_reset else None,
            "last_consumption": wallet.last_consumption.isoformat() if wallet.last_consumption else None
        },
        "packages": [
            {
                "id": pkg.id,
                "type": pkg.credit_type,
                "original": pkg.original_amount,
                "remaining": pkg.remaining_amount,
                "consumed": pkg.consumed_amount,
                "expires_at": pkg.expires_at.isoformat(),
                "is_expired": pkg.is_expired,
                "priority": pkg.priority,
                "created_at": pkg.created_at.isoformat()
            }
            for pkg in packages
        ],
        "recent_transactions": [
            {
                "id": txn.id,
                "type": txn.transaction_type,
                "credit_type": txn.credit_type,
                "amount": txn.amount,
                "balance_after": txn.balance_after,
                "description": txn.description,
                "feature": txn.feature_name,
                "created_at": txn.created_at.isoformat()
            }
            for txn in transactions
        ]
    }


@router.post("/users/grant", response_model=AdminCreditAdjustmentResponse)
async def grant_credits_to_user(
    request: AdminGrantCreditsRequest,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Grant bonus credits to a user

    Admin can grant:
        - Bonus credits
        - Promotional credits
        - Refund credits
        - Any custom amount
    """
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == request.user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Grant credits
        package = await CreditService.grant_bonus_credits(
            db=db,
            user_id=request.user_id,
            amount=request.amount,
            credit_type=request.credit_type,
            expires_in_days=request.expires_in_days,
            reason=request.reason,
            granted_by_id=current_admin.id,
            notes=request.notes
        )

        # Get updated balance
        balance = await CreditService.get_credit_balance(db, request.user_id, include_packages=False)

        # TODO: Send notification to user
        # await NotificationService.send_notification(
        #     user_id=request.user_id,
        #     type="CREDITS_GRANTED",
        #     data={
        #         "amount": request.amount,
        #         "reason": request.reason,
        #         "expires_at": package.expires_at.isoformat()
        #     }
        # )

        return AdminCreditAdjustmentResponse(
            success=True,
            user_id=request.user_id,
            adjustment=request.amount,
            new_balance=balance["total_balance"],
            action="CREDITS_GRANTED",
            reason=request.reason,
            package_id=package.id,
            transaction_id=0  # This would be the ledger ID
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to grant credits: {str(e)}"
        )


@router.post("/users/adjust", response_model=AdminCreditAdjustmentResponse)
async def adjust_user_credits(
    request: AdminAdjustCreditsRequest,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Manually adjust user credits (add or remove)

    Super Admin only. Can be used for:
        - Error corrections
        - Special adjustments
        - Credit refunds or deductions
    """
    try:
        # Verify user exists
        user_result = await db.execute(select(User).where(User.id == request.user_id))
        user = user_result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        if request.adjustment > 0:
            # Grant credits
            package = await CreditService.grant_bonus_credits(
                db=db,
                user_id=request.user_id,
                amount=request.adjustment,
                credit_type=CreditType.BONUS,
                expires_in_days=365,
                reason=request.reason,
                granted_by_id=current_admin.id,
                notes=request.notes
            )
            action = "CREDITS_ADDED"
            package_id = package.id

        else:
            # Deduct credits
            await CreditService.consume_credits(
                db=db,
                user_id=request.user_id,
                feature_key="admin_adjustment",
                amount=abs(request.adjustment),
                metadata={
                    "reason": request.reason,
                    "admin_id": current_admin.id,
                    "admin_name": current_admin.full_name or current_admin.username,
                    "notes": request.notes
                }
            )
            action = "CREDITS_DEDUCTED"
            package_id = None

        # Get updated balance
        balance = await CreditService.get_credit_balance(db, request.user_id, include_packages=False)

        # Log admin action in audit log
        # TODO: Implement audit logging
        # await AuditService.log_event(
        #     db,
        #     user_id=current_admin.id,
        #     action=f"ADMIN_{action}",
        #     resource_id=request.user_id,
        #     metadata={
        #         "amount": request.adjustment,
        #         "reason": request.reason
        #     }
        # )

        return AdminCreditAdjustmentResponse(
            success=True,
            user_id=request.user_id,
            adjustment=request.adjustment,
            new_balance=balance["total_balance"],
            action=action,
            reason=request.reason,
            package_id=package_id,
            transaction_id=0
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to adjust credits: {str(e)}"
        )


@router.post("/users/bulk-grant", response_model=BulkCreditGrantResponse)
async def bulk_grant_credits(
    request: BulkCreditGrantRequest,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk grant credits to multiple users

    Useful for:
        - Promotional campaigns
        - Compensation for outages
        - Mass credit distribution
    """
    results = []
    successful = 0
    failed = 0

    for user_id in request.user_ids:
        try:
            package = await CreditService.grant_bonus_credits(
                db=db,
                user_id=user_id,
                amount=request.amount,
                credit_type=request.credit_type,
                expires_in_days=request.expires_in_days,
                reason=request.reason,
                granted_by_id=current_admin.id
            )

            results.append({
                "user_id": user_id,
                "success": True,
                "package_id": package.id,
                "amount": request.amount
            })
            successful += 1

        except Exception as e:
            results.append({
                "user_id": user_id,
                "success": False,
                "error": str(e)
            })
            failed += 1

    return BulkCreditGrantResponse(
        total_users=len(request.user_ids),
        successful=successful,
        failed=failed,
        results=results
    )


# ==================== Feature Management ====================

@router.post("/features", response_model=FeatureCostResponse)
async def create_feature_definition(
    feature: FeatureDefinitionCreate,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new feature definition with credit cost and rate limits
    """
    # Check if feature already exists
    existing = await db.execute(
        select(FeatureDefinition).where(FeatureDefinition.feature_key == feature.feature_key)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Feature already exists"
        )

    # Create feature
    new_feature = FeatureDefinition(**feature.model_dump())
    db.add(new_feature)
    await db.commit()
    await db.refresh(new_feature)

    return FeatureCostResponse.model_validate(new_feature)


@router.put("/features/{feature_id}", response_model=FeatureCostResponse)
async def update_feature_definition(
    feature_id: int,
    feature: FeatureDefinitionUpdate,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Update feature definition
    """
    result = await db.execute(
        select(FeatureDefinition).where(FeatureDefinition.id == feature_id)
    )
    existing_feature = result.scalar_one_or_none()

    if not existing_feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )

    # Update fields
    update_data = feature.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(existing_feature, field, value)

    await db.commit()
    await db.refresh(existing_feature)

    return FeatureCostResponse.model_validate(existing_feature)


@router.delete("/features/{feature_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_feature_definition(
    feature_id: int,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete (or deactivate) a feature definition
    """
    result = await db.execute(
        select(FeatureDefinition).where(FeatureDefinition.id == feature_id)
    )
    feature = result.scalar_one_or_none()

    if not feature:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature not found"
        )

    # Soft delete by marking as inactive
    feature.is_active = False
    await db.commit()


# ==================== Rate Limit Rules ====================

@router.post("/rate-limits", response_model=RateLimitRuleResponse)
async def create_rate_limit_rule(
    rule: RateLimitRuleCreate,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Create custom rate limit rule
    """
    new_rule = RateLimitRule(
        **rule.model_dump(exclude_unset=True),
        created_by_id=current_admin.id
    )
    db.add(new_rule)
    await db.commit()
    await db.refresh(new_rule)

    # Convert to response
    response_data = {
        **{k: v for k, v in new_rule.__dict__.items() if not k.startswith('_')},
        "created_by_name": current_admin.full_name or current_admin.username
    }

    return RateLimitRuleResponse(**response_data)


@router.get("/rate-limits", response_model=List[RateLimitRuleResponse])
async def get_rate_limit_rules(
    user_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all rate limit rules with optional filters
    """
    query = select(RateLimitRule)

    if user_id:
        query = query.where(RateLimitRule.user_id == user_id)

    if is_active is not None:
        query = query.where(RateLimitRule.is_active == is_active)

    query = query.order_by(RateLimitRule.priority, desc(RateLimitRule.created_at))

    result = await db.execute(query)
    rules = result.scalars().all()

    # Convert to responses
    responses = []
    for rule in rules:
        created_by_name = None
        if rule.created_by_id:
            user_result = await db.execute(select(User).where(User.id == rule.created_by_id))
            creator = user_result.scalar_one_or_none()
            if creator:
                created_by_name = creator.full_name or creator.username

        response_data = {
            **{k: v for k, v in rule.__dict__.items() if not k.startswith('_')},
            "created_by_name": created_by_name
        }
        responses.append(RateLimitRuleResponse(**response_data))

    return responses


@router.delete("/rate-limits/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rate_limit_rule(
    rule_id: int,
    current_admin: User = Depends(require_role(UserRole.SUPER_ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a rate limit rule
    """
    result = await db.execute(
        select(RateLimitRule).where(RateLimitRule.id == rule_id)
    )
    rule = result.scalar_one_or_none()

    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rate limit rule not found"
        )

    await db.delete(rule)
    await db.commit()


# ==================== Credit Activity Tracking ====================

@router.get("/activity", response_model=CreditActivityResponse)
async def get_all_credit_activity(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    user_id: Optional[int] = None,
    transaction_type: Optional[CreditTransactionType] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    current_admin: User = Depends(require_role(UserRole.ADMIN)),
    db: AsyncSession = Depends(get_db)
):
    """
    Get system-wide credit activity with filters

    Admin can view all credit transactions across the system.
    """
    query = select(CreditLedger)

    if user_id:
        query = query.where(CreditLedger.user_id == user_id)

    if transaction_type:
        query = query.where(CreditLedger.transaction_type == transaction_type)

    if start_date:
        query = query.where(CreditLedger.created_at >= start_date)

    if end_date:
        query = query.where(CreditLedger.created_at <= end_date)

    # Get total count
    count_query = select(func.count()).select_from(CreditLedger)
    if user_id:
        count_query = count_query.where(CreditLedger.user_id == user_id)
    if transaction_type:
        count_query = count_query.where(CreditLedger.transaction_type == transaction_type)
    if start_date:
        count_query = count_query.where(CreditLedger.created_at >= start_date)
    if end_date:
        count_query = count_query.where(CreditLedger.created_at <= end_date)

    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get transactions
    query = query.order_by(desc(CreditLedger.created_at)).offset(skip).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()

    # Calculate pagination
    total_pages = (total + limit - 1) // limit
    current_page = (skip // limit) + 1

    # Convert to responses
    transaction_responses = []
    for txn in transactions:
        admin_name = None
        if txn.admin_id:
            admin_result = await db.execute(select(User).where(User.id == txn.admin_id))
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
