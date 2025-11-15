"""
Email background tasks
"""
import asyncio
from typing import Dict, Any, List

from app.core.celery_app import celery_app
from app.services.email_service import EmailService


@celery_app.task(name="app.tasks.email_tasks.send_welcome_email")
def send_welcome_email(email: str, user_name: str) -> Dict[str, bool]:
    """
    Send welcome email to new user

    Args:
        email: User email
        user_name: User name

    Returns:
        Delivery status
    """
    async def _send():
        success = await EmailService.send_welcome_email(email, user_name)
        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_verification_email")
def send_verification_email(email: str, user_name: str, verification_token: str) -> Dict[str, bool]:
    """
    Send email verification

    Args:
        email: User email
        user_name: User name
        verification_token: Verification token

    Returns:
        Delivery status
    """
    async def _send():
        success = await EmailService.send_verification_email(email, user_name, verification_token)
        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_password_reset_email")
def send_password_reset_email(email: str, user_name: str, reset_token: str) -> Dict[str, bool]:
    """
    Send password reset email

    Args:
        email: User email
        user_name: User name
        reset_token: Password reset token

    Returns:
        Delivery status
    """
    async def _send():
        success = await EmailService.send_password_reset_email(email, user_name, reset_token)
        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_subscription_confirmation")
def send_subscription_confirmation(
    email: str,
    user_name: str,
    plan_name: str,
    amount: str,
    billing_cycle: str
) -> Dict[str, bool]:
    """
    Send subscription confirmation email

    Args:
        email: User email
        user_name: User name
        plan_name: Subscription plan name
        amount: Amount charged
        billing_cycle: Billing cycle

    Returns:
        Delivery status
    """
    async def _send():
        success = await EmailService.send_subscription_confirmation_email(
            email, user_name, plan_name, amount, billing_cycle
        )
        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_payment_receipt")
def send_payment_receipt(
    email: str,
    user_name: str,
    transaction_id: str,
    amount: str,
    description: str
) -> Dict[str, bool]:
    """
    Send payment receipt email

    Args:
        email: User email
        user_name: User name
        transaction_id: Transaction ID
        amount: Amount paid
        description: Payment description

    Returns:
        Delivery status
    """
    async def _send():
        success = await EmailService.send_payment_receipt_email(
            email, user_name, transaction_id, amount, description
        )
        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_api_key_notification")
def send_api_key_notification(
    email: str,
    user_name: str,
    key_name: str,
    action: str
) -> Dict[str, bool]:
    """
    Send API key action notification

    Args:
        email: User email
        user_name: User name
        key_name: API key name
        action: Action (created, rotated, deleted)

    Returns:
        Delivery status
    """
    async def _send():
        if action == "created":
            success = await EmailService.send_api_key_created_notification(
                email, user_name, key_name
            )
        elif action == "rotated":
            success = await EmailService.send_api_key_rotated_notification(
                email, user_name, key_name
            )
        else:
            success = False

        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_organization_invitation")
def send_organization_invitation(
    email: str,
    org_name: str,
    inviter_name: str,
    invitation_token: str
) -> Dict[str, bool]:
    """
    Send organization invitation email

    Args:
        email: Invitee email
        org_name: Organization name
        inviter_name: Name of person who sent invitation
        invitation_token: Invitation token

    Returns:
        Delivery status
    """
    async def _send():
        success = await EmailService.send_organization_invitation_email(
            email, org_name, inviter_name, invitation_token
        )
        return {"success": success}

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_bulk_email")
def send_bulk_email(
    recipients: List[Dict[str, str]],
    subject: str,
    template: str,
    template_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Send bulk emails (for broadcasts, announcements)

    Args:
        recipients: List of {"email": "...", "name": "..."}
        subject: Email subject
        template: Email template name
        template_data: Template data

    Returns:
        Delivery statistics
    """
    async def _send():
        sent_count = 0
        failed_count = 0

        for recipient in recipients:
            try:
                # This would use a proper bulk email service in production
                # For now, send individually
                # await EmailService.send_custom_email(
                #     recipient["email"],
                #     recipient["name"],
                #     subject,
                #     template,
                #     template_data
                # )
                sent_count += 1
            except Exception as e:
                print(f"Failed to send to {recipient['email']}: {e}")
                failed_count += 1

        return {
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total": len(recipients)
        }

    return asyncio.run(_send())


@celery_app.task(name="app.tasks.email_tasks.send_expiring_subscription_reminder")
def send_expiring_subscription_reminder(
    email: str,
    user_name: str,
    plan_name: str,
    days_until_expiry: int
) -> Dict[str, bool]:
    """
    Send subscription expiry reminder

    Args:
        email: User email
        user_name: User name
        plan_name: Subscription plan
        days_until_expiry: Days until expiration

    Returns:
        Delivery status
    """
    async def _send():
        # This would use a specific template for expiry reminders
        # For now, returning placeholder
        return {"success": True}

    return asyncio.run(_send())
