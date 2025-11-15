"""
Advanced Credit Management Service
Handles credit grants, consumption, expiration, and comprehensive tracking
"""
from typing import Dict, Optional, List, Tuple, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import joinedload
from app.models.credit import (
    CreditWallet, CreditLedger, CreditPackage,
    FeatureDefinition, CreditPricing, CreditType, CreditTransactionType
)
from app.models.user import User, UserRole
from app.models.subscription import Subscription, SubscriptionPlan, Payment
from app.core.cache import RedisCache
from app.core.exceptions import AppException
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)


class InsufficientCreditsError(AppException):
    """Insufficient credits exception"""
    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="INSUFFICIENT_CREDITS"
        )


class CreditService:
    """Credit management service"""

    @staticmethod
    async def initialize_wallet(
        db: AsyncSession,
        user_id: int,
        initial_credits: int = 0
    ) -> CreditWallet:
        """Initialize credit wallet for new user"""
        try:
            # Check if wallet already exists
            result = await db.execute(
                select(CreditWallet).where(CreditWallet.user_id == user_id)
            )
            existing_wallet = result.scalar_one_or_none()

            if existing_wallet:
                return existing_wallet

            # Create new wallet
            now = datetime.utcnow()
            next_reset = CreditService._get_next_monthly_reset(now)

            wallet = CreditWallet(
                user_id=user_id,
                total_balance=initial_credits,
                monthly_balance=initial_credits,
                last_monthly_reset=now,
                next_monthly_reset=next_reset
            )

            db.add(wallet)

            # Create initial credit package if credits > 0
            if initial_credits > 0:
                package = CreditPackage(
                    wallet_id=wallet.id,
                    user_id=user_id,
                    credit_type=CreditType.MONTHLY_GRANT,
                    original_amount=initial_credits,
                    remaining_amount=initial_credits,
                    expires_at=next_reset,
                    priority=1  # Highest priority for monthly credits
                )
                db.add(package)

                # Log the transaction
                await CreditService._log_transaction(
                    db=db,
                    wallet=wallet,
                    transaction_type=CreditTransactionType.CREDIT,
                    credit_type=CreditType.MONTHLY_GRANT,
                    amount=initial_credits,
                    description="Initial credit wallet setup"
                )

            await db.commit()
            await db.refresh(wallet)

            logger.info(f"Initialized credit wallet for user {user_id} with {initial_credits} credits")
            return wallet

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to initialize wallet for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def grant_monthly_credits(
        db: AsyncSession,
        user_id: int,
        monthly_credits: int,
        allow_rollover: bool = False,
        max_rollover: int = 0
    ) -> Dict:
        """Grant monthly credits based on subscription"""
        try:
            # Get wallet
            result = await db.execute(
                select(CreditWallet).where(CreditWallet.user_id == user_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                wallet = await CreditService.initialize_wallet(db, user_id, monthly_credits)
                return {
                    "status": "initialized",
                    "credits_granted": monthly_credits,
                    "next_reset": wallet.next_monthly_reset
                }

            # Check if credits should be granted
            now = datetime.utcnow()
            if wallet.next_monthly_reset and wallet.next_monthly_reset > now:
                return {
                    "status": "not_due",
                    "next_reset": wallet.next_monthly_reset,
                    "days_remaining": (wallet.next_monthly_reset - now).days
                }

            # Handle rollover if enabled
            rollover_amount = 0
            if allow_rollover and wallet.monthly_balance > 0:
                rollover_amount = min(wallet.monthly_balance, max_rollover)
                logger.info(f"Rolling over {rollover_amount} credits for user {user_id}")

            # Expire old monthly credit packages
            expired_result = await db.execute(
                select(CreditPackage).where(
                    and_(
                        CreditPackage.wallet_id == wallet.id,
                        CreditPackage.credit_type == CreditType.MONTHLY_GRANT,
                        CreditPackage.is_expired == False
                    )
                )
            )

            for package in expired_result.scalars():
                if package.remaining_amount > 0:
                    wallet.total_balance -= package.remaining_amount
                    wallet.monthly_balance -= package.remaining_amount

                package.is_expired = True
                package.expired_at = now

            # Grant new monthly credits
            new_credits = monthly_credits + rollover_amount

            wallet.monthly_balance = new_credits
            wallet.total_balance += new_credits
            wallet.monthly_consumed = 0
            wallet.last_monthly_reset = now
            wallet.next_monthly_reset = CreditService._get_next_monthly_reset(now)
            wallet.alert_sent = False  # Reset low balance alert

            # Create new credit package
            package = CreditPackage(
                wallet_id=wallet.id,
                user_id=user_id,
                credit_type=CreditType.MONTHLY_GRANT,
                original_amount=new_credits,
                remaining_amount=new_credits,
                expires_at=wallet.next_monthly_reset,
                priority=1
            )
            db.add(package)

            # Log transaction
            description = f"Monthly credit grant: {monthly_credits}"
            if rollover_amount > 0:
                description += f" (including {rollover_amount} rollover)"

            await CreditService._log_transaction(
                db=db,
                wallet=wallet,
                transaction_type=CreditTransactionType.CREDIT,
                credit_type=CreditType.MONTHLY_GRANT,
                amount=new_credits,
                description=description
            )

            await db.commit()
            await db.refresh(wallet)

            # Clear cache
            await RedisCache.delete(f"credit_balance:{user_id}")

            logger.info(f"Granted {new_credits} monthly credits to user {user_id}")

            return {
                "status": "granted",
                "credits_granted": new_credits,
                "monthly_credits": monthly_credits,
                "rollover": rollover_amount,
                "next_reset": wallet.next_monthly_reset
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to grant monthly credits to user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def purchase_credits(
        db: AsyncSession,
        user_id: int,
        amount: int,
        payment_id: int,
        price: float,
        currency: str = "USD",
        valid_days: int = 365
    ) -> CreditPackage:
        """Purchase credits with expiration"""
        try:
            # Get or create wallet
            result = await db.execute(
                select(CreditWallet).where(CreditWallet.user_id == user_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                wallet = await CreditService.initialize_wallet(db, user_id, 0)

            # Create credit package with expiration
            expires_at = datetime.utcnow() + timedelta(days=valid_days)

            package = CreditPackage(
                wallet_id=wallet.id,
                user_id=user_id,
                credit_type=CreditType.PURCHASED,
                original_amount=amount,
                remaining_amount=amount,
                expires_at=expires_at,
                payment_id=payment_id,
                purchase_price=price,
                currency=currency,
                priority=3  # Lower priority than monthly credits
            )
            db.add(package)

            # Update wallet balance
            wallet.total_balance += amount
            wallet.purchased_balance += amount

            # Log transaction
            await CreditService._log_transaction(
                db=db,
                wallet=wallet,
                transaction_type=CreditTransactionType.CREDIT,
                credit_type=CreditType.PURCHASED,
                amount=amount,
                description=f"Purchased {amount} credits for {price} {currency}",
                source_id=str(payment_id),
                source_type="purchase"
            )

            await db.commit()
            await db.refresh(package)

            # Clear cache
            await RedisCache.delete(f"credit_balance:{user_id}")

            logger.info(f"User {user_id} purchased {amount} credits for {price} {currency}")
            return package

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to process credit purchase for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def consume_credits(
        db: AsyncSession,
        user_id: int,
        feature_key: str,
        amount: Optional[int] = None,
        metadata: Optional[Dict] = None,
        check_only: bool = False,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, Dict]:
        """Consume credits for a feature"""
        try:
            # Get user and check if admin
            user_result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = user_result.scalar_one_or_none()

            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            # Get feature definition
            feature_result = await db.execute(
                select(FeatureDefinition).where(
                    and_(
                        FeatureDefinition.feature_key == feature_key,
                        FeatureDefinition.is_active == True
                    )
                )
            )
            feature = feature_result.scalar_one_or_none()

            if not feature:
                # If feature not defined, use amount or default to 1
                actual_cost = amount or 1
                feature_name = feature_key
                is_exempt = False
            else:
                # Check if admin is exempt
                if user.role == UserRole.SUPER_ADMIN and feature.super_admin_exempt:
                    is_exempt = True
                elif user.role == UserRole.ADMIN and feature.admin_exempt:
                    is_exempt = True
                else:
                    is_exempt = False

                if is_exempt:
                    return True, {
                        "credits_consumed": 0,
                        "remaining_balance": "unlimited",
                        "admin_exempt": True,
                        "feature": feature_key
                    }

                # Calculate actual cost
                actual_cost = amount or feature.credit_cost
                feature_name = feature.feature_name

                # Apply cost modifiers if any
                if metadata and feature.cost_modifiers:
                    for modifier_key, modifier_rules in feature.cost_modifiers.items():
                        if modifier_key in metadata:
                            modifier_value = metadata[modifier_key]
                            if isinstance(modifier_rules, dict):
                                if modifier_value in modifier_rules:
                                    actual_cost *= modifier_rules[modifier_value]
                                elif "per_unit" in modifier_rules:
                                    actual_cost += modifier_value * modifier_rules["per_unit"]

            actual_cost = int(actual_cost)

            # Get wallet
            wallet_result = await db.execute(
                select(CreditWallet).where(CreditWallet.user_id == user_id)
            )
            wallet = wallet_result.scalar_one_or_none()

            if not wallet:
                raise InsufficientCreditsError("No credit wallet found. Please purchase credits.")

            # Check if sufficient balance
            if wallet.total_balance < actual_cost:
                raise InsufficientCreditsError(
                    f"Insufficient credits. Required: {actual_cost}, Available: {wallet.total_balance}"
                )

            if check_only:
                return True, {
                    "can_consume": True,
                    "required_credits": actual_cost,
                    "available_credits": wallet.total_balance,
                    "remaining_after": wallet.total_balance - actual_cost
                }

            # Consume credits using FIFO from packages (by priority and expiration)
            remaining_to_consume = actual_cost

            # Get active packages ordered by priority and expiration
            packages_result = await db.execute(
                select(CreditPackage).where(
                    and_(
                        CreditPackage.wallet_id == wallet.id,
                        CreditPackage.remaining_amount > 0,
                        CreditPackage.is_expired == False,
                        CreditPackage.expires_at > datetime.utcnow()
                    )
                ).order_by(CreditPackage.priority, CreditPackage.expires_at)
            )

            for package in packages_result.scalars():
                if remaining_to_consume <= 0:
                    break

                consume_from_package = min(remaining_to_consume, package.remaining_amount)
                package.remaining_amount -= consume_from_package
                package.consumed_amount += consume_from_package
                remaining_to_consume -= consume_from_package

                # Update specific balance types
                if package.credit_type == CreditType.MONTHLY_GRANT:
                    wallet.monthly_balance -= consume_from_package
                elif package.credit_type == CreditType.PURCHASED:
                    wallet.purchased_balance -= consume_from_package
                elif package.credit_type in [CreditType.BONUS, CreditType.PROMOTIONAL]:
                    wallet.bonus_balance -= consume_from_package

            # Update wallet totals
            wallet.total_balance -= actual_cost
            wallet.total_consumed += actual_cost
            wallet.monthly_consumed += actual_cost
            wallet.lifetime_consumed += actual_cost
            wallet.last_consumption = datetime.utcnow()

            # Log transaction
            await CreditService._log_transaction(
                db=db,
                wallet=wallet,
                transaction_type=CreditTransactionType.DEBIT,
                credit_type=None,
                amount=-actual_cost,
                description=f"Consumed {actual_cost} credits for {feature_name}",
                feature_id=feature.id if feature else None,
                feature_name=feature_name,
                metadata=metadata or {},
                ip_address=ip_address,
                user_agent=user_agent
            )

            await db.commit()

            # Update cache
            await RedisCache.set(
                f"credit_balance:{user_id}",
                wallet.total_balance,
                expire=300  # 5 minutes cache
            )

            logger.info(f"User {user_id} consumed {actual_cost} credits for {feature_key}")

            return True, {
                "credits_consumed": actual_cost,
                "remaining_balance": wallet.total_balance,
                "feature": feature_key,
                "feature_name": feature_name
            }

        except InsufficientCreditsError:
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to consume credits for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def get_credit_balance(
        db: AsyncSession,
        user_id: int,
        include_packages: bool = True
    ) -> Dict:
        """Get detailed credit balance"""
        try:
            # Get wallet
            result = await db.execute(
                select(CreditWallet)
                .options(joinedload(CreditWallet.credit_packages))
                .where(CreditWallet.user_id == user_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                return {
                    "total_balance": 0,
                    "monthly_balance": 0,
                    "purchased_balance": 0,
                    "bonus_balance": 0,
                    "monthly_consumed": 0,
                    "total_consumed": 0,
                    "lifetime_consumed": 0,
                    "next_monthly_reset": None,
                    "expiring_soon": 0,
                    "low_balance_warning": False,
                    "packages": []
                }

            # Get expiring soon credits (within 7 days)
            expiring_result = await db.execute(
                select(func.sum(CreditPackage.remaining_amount)).where(
                    and_(
                        CreditPackage.wallet_id == wallet.id,
                        CreditPackage.is_expired == False,
                        CreditPackage.expires_at <= datetime.utcnow() + timedelta(days=7),
                        CreditPackage.remaining_amount > 0
                    )
                )
            )
            expiring_amount = expiring_result.scalar() or 0

            packages_data = []
            if include_packages:
                packages = await db.execute(
                    select(CreditPackage).where(
                        and_(
                            CreditPackage.wallet_id == wallet.id,
                            CreditPackage.remaining_amount > 0,
                            CreditPackage.is_expired == False
                        )
                    ).order_by(CreditPackage.priority, CreditPackage.expires_at)
                )

                for package in packages.scalars():
                    days_until_expiry = (package.expires_at - datetime.utcnow()).days
                    packages_data.append({
                        "id": package.id,
                        "credit_type": package.credit_type,
                        "remaining_amount": package.remaining_amount,
                        "original_amount": package.original_amount,
                        "consumed_amount": package.consumed_amount,
                        "expires_at": package.expires_at,
                        "days_until_expiry": max(0, days_until_expiry),
                        "is_expired": package.is_expired,
                        "priority": package.priority
                    })

            return {
                "total_balance": wallet.total_balance,
                "monthly_balance": wallet.monthly_balance,
                "purchased_balance": wallet.purchased_balance,
                "bonus_balance": wallet.bonus_balance,
                "monthly_consumed": wallet.monthly_consumed,
                "total_consumed": wallet.total_consumed,
                "lifetime_consumed": wallet.lifetime_consumed,
                "next_monthly_reset": wallet.next_monthly_reset.isoformat() if wallet.next_monthly_reset else None,
                "last_consumption": wallet.last_consumption.isoformat() if wallet.last_consumption else None,
                "expiring_soon": int(expiring_amount),
                "low_balance_warning": wallet.total_balance <= wallet.low_balance_threshold,
                "packages": packages_data
            }

        except Exception as e:
            logger.error(f"Failed to get credit balance for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def grant_bonus_credits(
        db: AsyncSession,
        user_id: int,
        amount: int,
        credit_type: CreditType,
        expires_in_days: int,
        reason: str,
        granted_by_id: int,
        notes: Optional[str] = None
    ) -> CreditPackage:
        """Grant bonus/promotional credits (admin action)"""
        try:
            # Get or create wallet
            result = await db.execute(
                select(CreditWallet).where(CreditWallet.user_id == user_id)
            )
            wallet = result.scalar_one_or_none()

            if not wallet:
                wallet = await CreditService.initialize_wallet(db, user_id, 0)

            # Create credit package
            expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            package = CreditPackage(
                wallet_id=wallet.id,
                user_id=user_id,
                credit_type=credit_type,
                original_amount=amount,
                remaining_amount=amount,
                expires_at=expires_at,
                granted_by_id=granted_by_id,
                grant_reason=reason,
                notes=notes,
                priority=4  # Lowest priority
            )
            db.add(package)

            # Update wallet balance
            wallet.total_balance += amount
            wallet.bonus_balance += amount

            # Log transaction
            await CreditService._log_transaction(
                db=db,
                wallet=wallet,
                transaction_type=CreditTransactionType.CREDIT,
                credit_type=credit_type,
                amount=amount,
                description=f"Bonus credits granted: {reason}",
                admin_id=granted_by_id,
                admin_notes=notes
            )

            await db.commit()
            await db.refresh(package)

            # Clear cache
            await RedisCache.delete(f"credit_balance:{user_id}")

            logger.info(f"Granted {amount} {credit_type} credits to user {user_id} by admin {granted_by_id}")
            return package

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to grant bonus credits to user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def expire_credits(db: AsyncSession) -> int:
        """Expire old credits (run daily via scheduler)"""
        try:
            now = datetime.utcnow()

            # Find expired packages
            expired_result = await db.execute(
                select(CreditPackage).where(
                    and_(
                        CreditPackage.expires_at <= now,
                        CreditPackage.is_expired == False,
                        CreditPackage.remaining_amount > 0
                    )
                )
            )

            expired_count = 0

            for package in expired_result.scalars():
                wallet_result = await db.execute(
                    select(CreditWallet).where(CreditWallet.id == package.wallet_id)
                )
                wallet = wallet_result.scalar_one()

                # Update wallet balance
                wallet.total_balance -= package.remaining_amount

                if package.credit_type == CreditType.MONTHLY_GRANT:
                    wallet.monthly_balance -= package.remaining_amount
                elif package.credit_type == CreditType.PURCHASED:
                    wallet.purchased_balance -= package.remaining_amount
                elif package.credit_type in [CreditType.BONUS, CreditType.PROMOTIONAL]:
                    wallet.bonus_balance -= package.remaining_amount

                # Mark as expired
                package.is_expired = True
                package.expired_at = now

                # Log expiration
                await CreditService._log_transaction(
                    db=db,
                    wallet=wallet,
                    transaction_type=CreditTransactionType.EXPIRE,
                    credit_type=package.credit_type,
                    amount=-package.remaining_amount,
                    description=f"Credits expired ({package.remaining_amount} credits from package {package.id})"
                )

                # Clear cache
                await RedisCache.delete(f"credit_balance:{wallet.user_id}")

                expired_count += 1

            await db.commit()

            logger.info(f"Expired {expired_count} credit packages")
            return expired_count

        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to expire credits: {str(e)}")
            raise

    @staticmethod
    async def get_transaction_history(
        db: AsyncSession,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        transaction_type: Optional[CreditTransactionType] = None,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[CreditLedger], int]:
        """Get credit transaction history"""
        try:
            # Build query
            query = select(CreditLedger).where(CreditLedger.user_id == user_id)

            if start_date:
                query = query.where(CreditLedger.created_at >= start_date)

            if end_date:
                query = query.where(CreditLedger.created_at <= end_date)

            if transaction_type:
                query = query.where(CreditLedger.transaction_type == transaction_type)

            # Get total count
            count_query = select(func.count()).select_from(CreditLedger).where(CreditLedger.user_id == user_id)
            if start_date:
                count_query = count_query.where(CreditLedger.created_at >= start_date)
            if end_date:
                count_query = count_query.where(CreditLedger.created_at <= end_date)
            if transaction_type:
                count_query = count_query.where(CreditLedger.transaction_type == transaction_type)

            count_result = await db.execute(count_query)
            total = count_result.scalar()

            # Get transactions
            query = query.order_by(desc(CreditLedger.created_at)).offset(skip).limit(limit)
            result = await db.execute(query)
            transactions = result.scalars().all()

            return transactions, total

        except Exception as e:
            logger.error(f"Failed to get transaction history for user {user_id}: {str(e)}")
            raise

    @staticmethod
    async def _log_transaction(
        db: AsyncSession,
        wallet: CreditWallet,
        transaction_type: CreditTransactionType,
        credit_type: Optional[CreditType],
        amount: int,
        description: str,
        feature_id: Optional[int] = None,
        feature_name: Optional[str] = None,
        source_id: Optional[str] = None,
        source_type: Optional[str] = None,
        admin_id: Optional[int] = None,
        admin_notes: Optional[str] = None,
        metadata: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log credit transaction"""
        ledger = CreditLedger(
            wallet_id=wallet.id,
            user_id=wallet.user_id,
            transaction_type=transaction_type,
            credit_type=credit_type,
            amount=amount,
            balance_before=wallet.total_balance - amount if amount > 0 else wallet.total_balance,
            balance_after=wallet.total_balance,
            description=description,
            feature_id=feature_id,
            feature_name=feature_name,
            source_id=source_id,
            source_type=source_type,
            admin_id=admin_id,
            admin_notes=admin_notes,
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(ledger)

    @staticmethod
    def _get_next_monthly_reset(current_date: datetime) -> datetime:
        """Calculate next monthly reset date (1st of next month)"""
        if current_date.month == 12:
            return datetime(current_date.year + 1, 1, 1, 0, 0, 0)
        else:
            return datetime(current_date.year, current_date.month + 1, 1, 0, 0, 0)
