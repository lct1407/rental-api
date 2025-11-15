"""
Email Service - Business logic for sending emails with templates
"""
from typing import Optional, Dict, Any, List
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import EmailStr
from jinja2 import Template
from datetime import datetime

from app.config import settings


# Email configuration
email_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_TLS,
    MAIL_SSL_TLS=settings.MAIL_SSL,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# Initialize FastMail
fastmail = FastMail(email_config)


# Email Templates

WELCOME_EMAIL_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6366f1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Welcome to {{ app_name }}!</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_name }},</h2>
            <p>Thank you for joining {{ app_name }}! We're excited to have you on board.</p>
            <p>Your account has been successfully created and you can now start using our API management platform.</p>
            <p>Here's what you can do next:</p>
            <ul>
                <li>Create your first API key</li>
                <li>Set up webhooks for notifications</li>
                <li>Explore our analytics dashboard</li>
                <li>Check out our documentation</li>
            </ul>
            <a href="{{ app_url }}/dashboard" class="button">Go to Dashboard</a>
        </div>
        <div class="footer">
            <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
            <p>If you have any questions, reply to this email or contact us at support@{{ domain }}</p>
        </div>
    </div>
</body>
</html>
"""

EMAIL_VERIFICATION_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6366f1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
        .code { background-color: #e5e7eb; padding: 15px; border-radius: 4px; font-family: monospace; font-size: 18px; text-align: center; letter-spacing: 2px; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Verify Your Email</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_name }},</h2>
            <p>Please verify your email address to complete your registration.</p>
            <p>Click the button below to verify your email:</p>
            <a href="{{ verification_url }}" class="button">Verify Email</a>
            <p>Or copy and paste this link into your browser:</p>
            <div class="code">{{ verification_url }}</div>
            <p><small>This link will expire in 24 hours.</small></p>
        </div>
        <div class="footer">
            <p>If you didn't create an account, you can safely ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""

PASSWORD_RESET_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6366f1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
        .warning { background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Reset Your Password</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_name }},</h2>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>
            <a href="{{ reset_url }}" class="button">Reset Password</a>
            <p>Or copy and paste this link into your browser:</p>
            <div class="code">{{ reset_url }}</div>
            <p><small>This link will expire in 1 hour.</small></p>
            <div class="warning">
                <strong>Security Note:</strong> If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
            </div>
        </div>
        <div class="footer">
            <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

API_KEY_CREATED_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6366f1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .key-box { background-color: #e5e7eb; padding: 15px; border-radius: 4px; font-family: monospace; word-break: break-all; }
        .warning { background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px; margin: 10px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>New API Key Created</h1>
        </div>
        <div class="content">
            <h2>Hi {{ user_name }},</h2>
            <p>A new API key has been created for your account:</p>
            <p><strong>Key Name:</strong> {{ key_name }}</p>
            <p><strong>Created:</strong> {{ created_at }}</p>
            <div class="warning">
                <strong>Security Alert:</strong> If you didn't create this API key, please log in to your account immediately and revoke it.
            </div>
            <p>You can manage your API keys from your dashboard.</p>
        </div>
        <div class="footer">
            <p>&copy; {{ year }} {{ app_name }}. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
"""

ORGANIZATION_INVITE_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #6366f1; color: white; padding: 20px; text-align: center; }
        .content { padding: 20px; background-color: #f9f9f9; }
        .button { display: inline-block; padding: 12px 24px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 4px; margin: 10px 0; }
        .info-box { background-color: #eff6ff; border-left: 4px solid: #3b82f6; padding: 12px; margin: 10px 0; }
        .footer { text-align: center; padding: 20px; font-size: 12px; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>You've Been Invited!</h1>
        </div>
        <div class="content">
            <h2>Hi there,</h2>
            <p>{{ inviter_name }} has invited you to join <strong>{{ organization_name }}</strong> on {{ app_name }}.</p>
            <div class="info-box">
                <p><strong>Organization:</strong> {{ organization_name }}</p>
                <p><strong>Role:</strong> {{ role }}</p>
                <p><strong>Invited by:</strong> {{ inviter_name }}</p>
            </div>
            <p>Click the button below to accept the invitation:</p>
            <a href="{{ invite_url }}" class="button">Accept Invitation</a>
            <p><small>This invitation will expire in 7 days.</small></p>
        </div>
        <div class="footer">
            <p>If you don't want to join this organization, you can safely ignore this email.</p>
        </div>
    </div>
</body>
</html>
"""


class EmailService:
    """Service for sending emails"""

    @staticmethod
    async def send_email(
        recipients: List[EmailStr],
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> bool:
        """Send email"""
        try:
            message = MessageSchema(
                subject=subject,
                recipients=recipients,
                body=text_body or html_body,
                html=html_body,
                subtype=MessageType.html
            )

            await fastmail.send_message(message)
            return True
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
            return False

    @staticmethod
    async def send_welcome_email(
        email: EmailStr,
        user_name: str
    ) -> bool:
        """Send welcome email to new user"""
        template = Template(WELCOME_EMAIL_TEMPLATE)
        html_body = template.render(
            app_name=settings.APP_NAME,
            user_name=user_name,
            app_url="https://yourapp.com",  # Replace with actual URL
            year=datetime.utcnow().year,
            domain="yourapp.com"
        )

        return await EmailService.send_email(
            recipients=[email],
            subject=f"Welcome to {settings.APP_NAME}!",
            html_body=html_body
        )

    @staticmethod
    async def send_verification_email(
        email: EmailStr,
        user_name: str,
        verification_token: str
    ) -> bool:
        """Send email verification email"""
        verification_url = f"https://yourapp.com/verify-email?token={verification_token}"

        template = Template(EMAIL_VERIFICATION_TEMPLATE)
        html_body = template.render(
            user_name=user_name,
            verification_url=verification_url
        )

        return await EmailService.send_email(
            recipients=[email],
            subject="Verify your email address",
            html_body=html_body
        )

    @staticmethod
    async def send_password_reset_email(
        email: EmailStr,
        user_name: str,
        reset_token: str
    ) -> bool:
        """Send password reset email"""
        reset_url = f"https://yourapp.com/reset-password?token={reset_token}"

        template = Template(PASSWORD_RESET_TEMPLATE)
        html_body = template.render(
            user_name=user_name,
            reset_url=reset_url,
            year=datetime.utcnow().year,
            app_name=settings.APP_NAME
        )

        return await EmailService.send_email(
            recipients=[email],
            subject="Reset your password",
            html_body=html_body
        )

    @staticmethod
    async def send_api_key_created_notification(
        email: EmailStr,
        user_name: str,
        key_name: str
    ) -> bool:
        """Send notification when API key is created"""
        template = Template(API_KEY_CREATED_TEMPLATE)
        html_body = template.render(
            user_name=user_name,
            key_name=key_name,
            created_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
            year=datetime.utcnow().year,
            app_name=settings.APP_NAME
        )

        return await EmailService.send_email(
            recipients=[email],
            subject="New API Key Created",
            html_body=html_body
        )

    @staticmethod
    async def send_organization_invitation(
        email: EmailStr,
        organization_name: str,
        inviter_name: str,
        role: str,
        invite_token: str
    ) -> bool:
        """Send organization invitation email"""
        invite_url = f"https://yourapp.com/accept-invite?token={invite_token}"

        template = Template(ORGANIZATION_INVITE_TEMPLATE)
        html_body = template.render(
            organization_name=organization_name,
            inviter_name=inviter_name,
            role=role,
            invite_url=invite_url,
            app_name=settings.APP_NAME
        )

        return await EmailService.send_email(
            recipients=[email],
            subject=f"You've been invited to join {organization_name}",
            html_body=html_body
        )

    @staticmethod
    async def send_subscription_confirmation(
        email: EmailStr,
        user_name: str,
        plan_name: str,
        amount: str,
        billing_cycle: str
    ) -> bool:
        """Send subscription confirmation email"""
        html_body = f"""
        <h2>Hi {user_name},</h2>
        <p>Your subscription to the {plan_name} plan has been confirmed!</p>
        <p><strong>Plan:</strong> {plan_name}</p>
        <p><strong>Amount:</strong> ${amount}/{billing_cycle}</p>
        <p>Thank you for subscribing!</p>
        """

        return await EmailService.send_email(
            recipients=[email],
            subject="Subscription Confirmed",
            html_body=html_body
        )

    @staticmethod
    async def send_payment_receipt(
        email: EmailStr,
        user_name: str,
        amount: str,
        description: str,
        receipt_url: Optional[str] = None
    ) -> bool:
        """Send payment receipt email"""
        html_body = f"""
        <h2>Hi {user_name},</h2>
        <p>Thank you for your payment!</p>
        <p><strong>Amount:</strong> ${amount}</p>
        <p><strong>Description:</strong> {description}</p>
        """

        if receipt_url:
            html_body += f'<p><a href="{receipt_url}">View Receipt</a></p>'

        return await EmailService.send_email(
            recipients=[email],
            subject="Payment Receipt",
            html_body=html_body
        )
