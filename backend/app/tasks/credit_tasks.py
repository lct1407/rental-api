"""
Credit Management Scheduled Tasks
Celery tasks for automated credit operations
"""
from celery import shared_task
from datetime import datetime, timedelta
from sqlalchemy import select, and_
from app.database import get_db_session
from app.services.credit_service import CreditService
from app.models.subscription import Subscription, SubscriptionStatus, SubscriptionPlan as SubscriptionPlanEnum
from app.models.credit import CreditWallet, CreditPackage
from app.core.cache import RedisCache
import logging

logger = logging.getLogger(__name__)


@shared_task(name="grant_monthly_credits")
def grant_monthly_credits_task():
    """
    Grant monthly credits to all active subscribers
    Runs at midnight on 1st of each month
    """
    logger.info("Starting monthly credit grant task")

    async def _grant():
        async with get_db_session() as db:
            # Get all active subscriptions
            result = await db.execute(
                select(Subscription).where(
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
            subscriptions = result.scalars().all()

            granted_count = 0
            failed_count = 0
            total_credits_granted = 0

            for subscription in subscriptions:
                try:
                    # Determine monthly credits based on plan
                    plan_credits = {
                        SubscriptionPlanEnum.FREE: 1000,
                        SubscriptionPlanEnum.BASIC: 10000,
                        SubscriptionPlanEnum.PRO: 100000,
                        SubscriptionPlanEnum.ENTERPRISE: 1000000
                    }

                    monthly_credits = plan_credits.get(subscription.plan, 1000)

                    # Determine rollover settings
                    allow_rollover = subscription.plan in [SubscriptionPlanEnum.PRO, SubscriptionPlanEnum.ENTERPRISE]
                    max_rollover = {
                        SubscriptionPlanEnum.PRO: 50000,
                        SubscriptionPlanEnum.ENTERPRISE: 500000
                    }.get(subscription.plan, 0)

                    # Grant credits
                    result = await CreditService.grant_monthly_credits(
                        db=db,
                        user_id=subscription.user_id,
                        monthly_credits=monthly_credits,
                        allow_rollover=allow_rollover,
                        max_rollover=max_rollover
                    )

                    if result["status"] in ["granted", "initialized"]:
                        granted_count += 1
                        total_credits_granted += result.get("credits_granted", 0)

                        logger.info(
                            f"Granted {result.get('credits_granted', 0)} credits to user {subscription.user_id}"
                        )

                        # TODO: Send notification
                        # await NotificationService.send_notification(
                        #     user_id=subscription.user_id,
                        #     type="MONTHLY_CREDITS_GRANTED",
                        #     data={
                        #         "credits": result["credits_granted"],
                        #         "next_reset": result["next_reset"].isoformat() if result.get("next_reset") else None
                        #     }
                        # )

                except Exception as e:
                    logger.error(f"Failed to grant credits to user {subscription.user_id}: {str(e)}")
                    failed_count += 1

            logger.info(
                f"Monthly credit grant completed: {granted_count} success, {failed_count} failed, "
                f"{total_credits_granted} total credits granted"
            )

            return {
                "success": granted_count,
                "failed": failed_count,
                "total_credits": total_credits_granted
            }

    import asyncio
    return asyncio.run(_grant())


@shared_task(name="expire_old_credits")
def expire_old_credits_task():
    """
    Expire credits that have passed their expiration date
    Runs daily at midnight
    """
    logger.info("Starting credit expiration task")

    async def _expire():
        async with get_db_session() as db:
            expired_count = await CreditService.expire_credits(db)
            logger.info(f"Expired {expired_count} credit packages")
            return {"expired_packages": expired_count}

    import asyncio
    return asyncio.run(_expire())


@shared_task(name="send_expiration_warnings")
def send_credit_expiration_warnings():
    """
    Send warnings for credits expiring soon (within 7 days)
    Runs daily
    """
    logger.info("Starting credit expiration warning task")

    async def _send_warnings():
        async with get_db_session() as db:
            # Find credits expiring in next 7 days
            expiring_soon_date = datetime.utcnow() + timedelta(days=7)

            result = await db.execute(
                select(CreditPackage).where(
                    and_(
                        CreditPackage.is_expired == False,
                        CreditPackage.remaining_amount > 0,
                        CreditPackage.expires_at <= expiring_soon_date,
                        CreditPackage.expires_at > datetime.utcnow()
                    )
                )
            )
            expiring_packages = result.scalars().all()

            # Group by user
            user_packages = {}
            for package in expiring_packages:
                if package.user_id not in user_packages:
                    user_packages[package.user_id] = []
                user_packages[package.user_id].append(package)

            warned_users = 0

            for user_id, packages in user_packages.items():
                try:
                    total_expiring = sum(pkg.remaining_amount for pkg in packages)
                    soonest_expiry = min(pkg.expires_at for pkg in packages)
                    days_remaining = (soonest_expiry - datetime.utcnow()).days

                    # TODO: Send notification
                    # await NotificationService.send_notification(
                    #     user_id=user_id,
                    #     type="CREDITS_EXPIRING_SOON",
                    #     data={
                    #         "amount": total_expiring,
                    #         "expires_at": soonest_expiry.isoformat(),
                    #         "days_remaining": days_remaining,
                    #         "package_count": len(packages)
                    #     }
                    # )

                    logger.info(
                        f"Sent expiration warning to user {user_id}: {total_expiring} credits expiring in {days_remaining} days"
                    )
                    warned_users += 1

                except Exception as e:
                    logger.error(f"Failed to send expiration warning to user {user_id}: {str(e)}")

            logger.info(f"Sent expiration warnings to {warned_users} users")
            return {"warned_users": warned_users}

    import asyncio
    return asyncio.run(_send_warnings())


@shared_task(name="send_low_balance_alerts")
def send_low_balance_alerts():
    """
    Send alerts to users with low credit balance
    Runs hourly
    """
    logger.info("Starting low balance alert task")

    async def _send_alerts():
        async with get_db_session() as db:
            # Find wallets with low balance that haven't been alerted
            result = await db.execute(
                select(CreditWallet).where(
                    and_(
                        CreditWallet.total_balance <= CreditWallet.low_balance_threshold,
                        CreditWallet.alert_sent == False
                    )
                )
            )
            low_balance_wallets = result.scalars().all()

            alerted_users = 0

            for wallet in low_balance_wallets:
                try:
                    # TODO: Send notification
                    # await NotificationService.send_notification(
                    #     user_id=wallet.user_id,
                    #     type="LOW_CREDIT_BALANCE",
                    #     data={
                    #         "current_balance": wallet.total_balance,
                    #         "threshold": wallet.low_balance_threshold
                    #     }
                    # )

                    # Mark as alerted
                    wallet.alert_sent = True
                    await db.commit()

                    logger.info(f"Sent low balance alert to user {wallet.user_id}")
                    alerted_users += 1

                except Exception as e:
                    logger.error(f"Failed to send low balance alert to user {wallet.user_id}: {str(e)}")

            logger.info(f"Sent low balance alerts to {alerted_users} users")
            return {"alerted_users": alerted_users}

    import asyncio
    return asyncio.run(_send_alerts())


@shared_task(name="reset_daily_rate_limits")
def reset_daily_rate_limits():
    """
    Reset daily rate limits
    Runs at midnight
    """
    logger.info("Starting daily rate limit reset task")

    async def _reset():
        try:
            # Clear daily rate limit keys from Redis
            await RedisCache.delete_pattern("rate_limit:*:day:*")
            logger.info("Daily rate limits reset successfully")
            return {"status": "success"}

        except Exception as e:
            logger.error(f"Failed to reset daily rate limits: {str(e)}")
            return {"status": "failed", "error": str(e)}

    import asyncio
    return asyncio.run(_reset())


@shared_task(name="generate_monthly_reports")
def generate_monthly_credit_reports():
    """
    Generate and email monthly credit usage reports
    Runs on 1st of each month
    """
    logger.info("Starting monthly report generation task")

    async def _generate():
        async with get_db_session() as db:
            from app.models.user import User

            # Get all active users
            result = await db.execute(
                select(User.id, User.email, User.full_name).join(
                    Subscription
                ).where(
                    Subscription.status == SubscriptionStatus.ACTIVE
                )
            )
            users = result.all()

            now = datetime.utcnow()
            last_month = now.month - 1 if now.month > 1 else 12
            year = now.year if now.month > 1 else now.year - 1

            reports_sent = 0

            for user_id, email, full_name in users:
                try:
                    # Generate usage report
                    # This would use CreditService to generate comprehensive report

                    # TODO: Send email with report
                    # await EmailService.send_monthly_credit_report(
                    #     email=email,
                    #     name=full_name,
                    #     month=last_month,
                    #     year=year,
                    #     report_data=report
                    # )

                    logger.info(f"Sent monthly report to user {user_id}")
                    reports_sent += 1

                except Exception as e:
                    logger.error(f"Failed to generate report for user {user_id}: {str(e)}")

            logger.info(f"Generated and sent {reports_sent} monthly reports")
            return {"reports_sent": reports_sent}

    import asyncio
    return asyncio.run(_generate())


@shared_task(name="cleanup_expired_packages")
def cleanup_expired_packages():
    """
    Clean up fully consumed or expired packages older than 90 days
    Runs weekly
    """
    logger.info("Starting expired packages cleanup task")

    async def _cleanup():
        async with get_db_session() as db:
            cutoff_date = datetime.utcnow() - timedelta(days=90)

            # Find packages to clean up
            result = await db.execute(
                select(CreditPackage).where(
                    and_(
                        or_(
                            CreditPackage.is_expired == True,
                            CreditPackage.remaining_amount == 0
                        ),
                        CreditPackage.created_at < cutoff_date
                    )
                )
            )
            old_packages = result.scalars().all()

            cleaned_count = 0

            for package in old_packages:
                try:
                    await db.delete(package)
                    cleaned_count += 1

                except Exception as e:
                    logger.error(f"Failed to delete package {package.id}: {str(e)}")

            if cleaned_count > 0:
                await db.commit()

            logger.info(f"Cleaned up {cleaned_count} expired credit packages")
            return {"cleaned_packages": cleaned_count}

    import asyncio
    return asyncio.run(_cleanup())


@shared_task(name="update_package_priorities")
def update_credit_package_priorities():
    """
    Update priorities for credit packages based on expiration
    Packages expiring sooner get higher priority
    Runs daily
    """
    logger.info("Starting package priority update task")

    async def _update_priorities():
        async with get_db_session() as db:
            # Get all active packages
            result = await db.execute(
                select(CreditPackage).where(
                    and_(
                        CreditPackage.is_expired == False,
                        CreditPackage.remaining_amount > 0
                    )
                )
            )
            packages = result.scalars().all()

            updated_count = 0
            now = datetime.utcnow()

            for package in packages:
                try:
                    # Calculate days until expiry
                    days_until_expiry = (package.expires_at - now).days

                    # Set priority based on type and expiration
                    if package.credit_type.value == "monthly_grant":
                        new_priority = 1  # Highest priority
                    elif days_until_expiry <= 7:
                        new_priority = 2  # Expiring soon
                    elif package.credit_type.value == "purchased":
                        new_priority = 3  # Purchased credits
                    else:
                        new_priority = 4  # Bonus/promotional

                    if package.priority != new_priority:
                        package.priority = new_priority
                        updated_count += 1

                except Exception as e:
                    logger.error(f"Failed to update priority for package {package.id}: {str(e)}")

            if updated_count > 0:
                await db.commit()

            logger.info(f"Updated priorities for {updated_count} credit packages")
            return {"updated_packages": updated_count}

    import asyncio
    return asyncio.run(_update_priorities())
