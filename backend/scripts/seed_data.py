"""
Database seed script - Populate with sample data for development/testing
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db, engine
from app.models import (
    User, UserRole, UserStatus, SubscriptionPlan,
    Organization, OrganizationMember, OrganizationRole,
    ApiKey, Webhook, Subscription, SubscriptionStatus,
    Payment, PaymentProvider, PaymentStatus,
    CreditTransaction
)
from app.core.security import SecurityManager
from app.services.api_key_service import ApiKeyService


async def clear_database(db: AsyncSession):
    """Clear all data from database"""
    print("🗑️  Clearing database...")

    # Delete in correct order (respecting foreign keys)
    await db.execute(text("DELETE FROM security_events"))
    await db.execute(text("DELETE FROM audit_logs"))
    await db.execute(text("DELETE FROM user_activities"))
    await db.execute(text("DELETE FROM system_metrics"))
    await db.execute(text("DELETE FROM api_usage_logs"))
    await db.execute(text("DELETE FROM credit_transactions"))
    await db.execute(text("DELETE FROM invoices"))
    await db.execute(text("DELETE FROM payments"))
    await db.execute(text("DELETE FROM subscriptions"))
    await db.execute(text("DELETE FROM webhook_deliveries"))
    await db.execute(text("DELETE FROM webhooks"))
    await db.execute(text("DELETE FROM api_keys"))
    await db.execute(text("DELETE FROM organization_invitations"))
    await db.execute(text("DELETE FROM organization_members"))
    await db.execute(text("DELETE FROM organizations"))
    await db.execute(text("DELETE FROM users"))

    # Reset sequences
    await db.execute(text("ALTER SEQUENCE users_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE organizations_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE api_keys_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE webhooks_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE subscriptions_id_seq RESTART WITH 1"))
    await db.execute(text("ALTER SEQUENCE payments_id_seq RESTART WITH 1"))

    await db.commit()
    print("✅ Database cleared")


async def seed_users(db: AsyncSession):
    """Create sample users"""
    print("\n👥 Creating users...")

    users_data = [
        {
            "email": "admin@example.com",
            "username": "admin",
            "password": "Admin123!@#",
            "full_name": "System Administrator",
            "role": UserRole.SUPER_ADMIN,
            "status": UserStatus.ACTIVE,
            "plan": SubscriptionPlan.ENTERPRISE,
            "credits": 100000,
            "email_verified": True,
            "phone_number": "+1234567890",
            "company_name": "RentAPI Platform"
        },
        {
            "email": "john@acme.com",
            "username": "johndoe",
            "password": "User123!@#",
            "full_name": "John Doe",
            "role": UserRole.USER,
            "status": UserStatus.ACTIVE,
            "plan": SubscriptionPlan.PRO,
            "credits": 5000,
            "email_verified": True,
            "phone_number": "+1234567891",
            "company_name": "Acme Corporation",
            "bio": "Software engineer building awesome APIs"
        },
        {
            "email": "jane@startup.io",
            "username": "janesmith",
            "password": "User123!@#",
            "full_name": "Jane Smith",
            "role": UserRole.USER,
            "status": UserStatus.ACTIVE,
            "plan": SubscriptionPlan.BASIC,
            "credits": 1000,
            "email_verified": True,
            "phone_number": "+1234567892",
            "company_name": "StartupIO",
            "bio": "Product manager exploring API monetization"
        },
        {
            "email": "bob@freelance.dev",
            "username": "bobwilson",
            "password": "User123!@#",
            "full_name": "Bob Wilson",
            "role": UserRole.USER,
            "status": UserStatus.ACTIVE,
            "plan": SubscriptionPlan.FREE,
            "credits": 100,
            "email_verified": False,
            "company_name": "Freelance Developer"
        },
        {
            "email": "alice@enterprise.com",
            "username": "alicejohnson",
            "password": "User123!@#",
            "full_name": "Alice Johnson",
            "role": UserRole.ADMIN,
            "status": UserStatus.ACTIVE,
            "plan": SubscriptionPlan.ENTERPRISE,
            "credits": 50000,
            "email_verified": True,
            "phone_number": "+1234567893",
            "company_name": "Enterprise Solutions Inc"
        },
        {
            "email": "charlie@suspended.com",
            "username": "charlie",
            "password": "User123!@#",
            "full_name": "Charlie Brown",
            "role": UserRole.USER,
            "status": UserStatus.SUSPENDED,
            "plan": SubscriptionPlan.BASIC,
            "credits": 0,
            "email_verified": True
        }
    ]

    created_users = []

    for user_data in users_data:
        password = user_data.pop("password")
        hashed_password = SecurityManager.hash_password(password)

        user = User(
            **user_data,
            hashed_password=hashed_password,
            email_verified_at=datetime.utcnow() if user_data.get("email_verified") else None,
            last_login_at=datetime.utcnow() - timedelta(hours=2),
            last_login_ip="127.0.0.1",
            login_count=5
        )

        db.add(user)
        created_users.append(user)

    await db.commit()

    # Refresh to get IDs
    for user in created_users:
        await db.refresh(user)

    print(f"✅ Created {len(created_users)} users")
    return created_users


async def seed_organizations(db: AsyncSession, users: list):
    """Create sample organizations"""
    print("\n🏢 Creating organizations...")

    orgs_data = [
        {
            "name": "Acme Corporation",
            "slug": "acme-corp",
            "description": "Leading provider of business solutions",
            "owner_user_id": users[1].id  # John
        },
        {
            "name": "StartupIO",
            "slug": "startup-io",
            "description": "Innovative startup building the future",
            "owner_user_id": users[2].id  # Jane
        },
        {
            "name": "Enterprise Solutions",
            "slug": "enterprise-solutions",
            "description": "Enterprise-grade software solutions",
            "owner_user_id": users[4].id  # Alice
        }
    ]

    created_orgs = []

    for org_data in orgs_data:
        owner_id = org_data.pop("owner_user_id")
        org = Organization(**org_data)
        db.add(org)
        await db.flush()

        # Add owner as member
        member = OrganizationMember(
            organization_id=org.id,
            user_id=owner_id,
            role=OrganizationRole.OWNER
        )
        db.add(member)

        created_orgs.append(org)

    await db.commit()

    for org in created_orgs:
        await db.refresh(org)

    print(f"✅ Created {len(created_orgs)} organizations")
    return created_orgs


async def seed_api_keys(db: AsyncSession, users: list, organizations: list):
    """Create sample API keys"""
    print("\n🔑 Creating API keys...")

    keys_data = [
        {
            "user": users[1],  # John
            "name": "Production API Key",
            "description": "Main production key for Acme services",
            "organization_id": organizations[0].id,
            "scopes": ["read:*", "write:*"],
            "rate_limit_per_hour": 10000,
            "rate_limit_per_day": 100000
        },
        {
            "user": users[1],  # John
            "name": "Development Key",
            "description": "Development and testing",
            "scopes": ["read:*"],
            "rate_limit_per_hour": 1000,
            "rate_limit_per_day": 10000
        },
        {
            "user": users[2],  # Jane
            "name": "Startup API Key",
            "description": "StartupIO production key",
            "organization_id": organizations[1].id,
            "scopes": ["read:profile", "read:analytics", "write:webhooks"],
            "rate_limit_per_hour": 5000,
            "rate_limit_per_day": 50000
        },
        {
            "user": users[3],  # Bob
            "name": "Free Tier Key",
            "description": "Personal project API key",
            "scopes": ["read:profile"],
            "rate_limit_per_hour": 100,
            "rate_limit_per_day": 1000
        },
        {
            "user": users[4],  # Alice
            "name": "Enterprise Master Key",
            "description": "High-volume enterprise key",
            "organization_id": organizations[2].id,
            "scopes": ["read:*", "write:*", "admin:*"],
            "rate_limit_per_hour": 50000,
            "rate_limit_per_day": 500000
        }
    ]

    created_keys = []
    full_keys = []

    for key_data in keys_data:
        user = key_data.pop("user")

        # Generate key using service
        from app.schemas.api_key import ApiKeyCreate

        api_key_create = ApiKeyCreate(**key_data)
        api_key, full_key = await ApiKeyService.create(db, user.id, api_key_create)

        created_keys.append(api_key)
        full_keys.append({
            "name": key_data["name"],
            "key": full_key,
            "user": user.email
        })

    print(f"✅ Created {len(created_keys)} API keys")
    print("\n📋 API Keys (save these for testing):")
    for key_info in full_keys:
        print(f"   {key_info['name']} ({key_info['user']})")
        print(f"   Key: {key_info['key']}")
        print()

    return created_keys


async def seed_webhooks(db: AsyncSession, users: list, organizations: list):
    """Create sample webhooks"""
    print("\n🪝 Creating webhooks...")

    webhooks_data = [
        {
            "user_id": users[1].id,  # John
            "organization_id": organizations[0].id,
            "name": "Acme Production Webhook",
            "url": "https://acme.com/webhooks/api-events",
            "events": ["api_key.created", "api_key.deleted", "payment.succeeded"],
            "description": "Acme production webhook",
            "secret": SecurityManager.generate_secret(32),
            "is_active": True
        },
        {
            "user_id": users[2].id,  # Jane
            "organization_id": organizations[1].id,
            "name": "Subscription Events Webhook",
            "url": "https://startup.io/api/webhooks",
            "events": ["subscription.created", "subscription.cancelled", "payment.failed"],
            "description": "Subscription events webhook",
            "secret": SecurityManager.generate_secret(32),
            "is_active": True
        },
        {
            "user_id": users[4].id,  # Alice
            "organization_id": organizations[2].id,
            "name": "Enterprise All Events",
            "url": "https://enterprise.com/webhooks/all",
            "events": ["*"],
            "description": "All events webhook",
            "secret": SecurityManager.generate_secret(32),
            "is_active": True
        }
    ]

    created_webhooks = []

    for webhook_data in webhooks_data:
        webhook = Webhook(**webhook_data)
        db.add(webhook)
        created_webhooks.append(webhook)

    await db.commit()

    for webhook in created_webhooks:
        await db.refresh(webhook)

    print(f"✅ Created {len(created_webhooks)} webhooks")
    return created_webhooks


async def seed_subscriptions(db: AsyncSession, users: list):
    """Create sample subscriptions"""
    print("\n💳 Creating subscriptions...")

    subscriptions_data = [
        {
            "user_id": users[1].id,  # John - Pro plan
            "plan": SubscriptionPlan.PRO,
            "status": SubscriptionStatus.ACTIVE,
            "billing_cycle": "monthly",
            "price": Decimal("49.99"),
            "provider": PaymentProvider.STRIPE,
            "current_period_start": datetime.utcnow() - timedelta(days=10),
            "current_period_end": datetime.utcnow() + timedelta(days=20)
        },
        {
            "user_id": users[2].id,  # Jane - Basic plan
            "plan": SubscriptionPlan.BASIC,
            "status": SubscriptionStatus.ACTIVE,
            "billing_cycle": "yearly",
            "price": Decimal("199.99"),
            "provider": PaymentProvider.PAYPAL,
            "current_period_start": datetime.utcnow() - timedelta(days=30),
            "current_period_end": datetime.utcnow() + timedelta(days=335)
        },
        {
            "user_id": users[4].id,  # Alice - Enterprise plan
            "plan": SubscriptionPlan.ENTERPRISE,
            "status": SubscriptionStatus.ACTIVE,
            "billing_cycle": "yearly",
            "price": Decimal("1999.99"),
            "provider": PaymentProvider.STRIPE,
            "current_period_start": datetime.utcnow() - timedelta(days=60),
            "current_period_end": datetime.utcnow() + timedelta(days=305)
        }
    ]

    created_subscriptions = []

    for sub_data in subscriptions_data:
        subscription = Subscription(**sub_data)
        db.add(subscription)
        created_subscriptions.append(subscription)

    await db.commit()

    for sub in created_subscriptions:
        await db.refresh(sub)

    print(f"✅ Created {len(created_subscriptions)} subscriptions")
    return created_subscriptions


async def seed_payments(db: AsyncSession, users: list, subscriptions: list):
    """Create sample payment records"""
    print("\n💰 Creating payment records...")

    payments_data = [
        {
            "user_id": users[1].id,
            "subscription_id": subscriptions[0].id,
            "amount": Decimal("49.99"),
            "currency": "USD",
            "status": PaymentStatus.SUCCEEDED,
            "provider": PaymentProvider.STRIPE,
            "provider_transaction_id": "pi_3Abc123Stripe",
            "payment_method": "card",
            "description": "Pro Plan - Monthly",
            "paid_at": datetime.utcnow() - timedelta(days=10)
        },
        {
            "user_id": users[2].id,
            "subscription_id": subscriptions[1].id,
            "amount": Decimal("199.99"),
            "currency": "USD",
            "status": PaymentStatus.SUCCEEDED,
            "provider": PaymentProvider.PAYPAL,
            "provider_transaction_id": "PAYID-ABC123",
            "payment_method": "paypal",
            "description": "Basic Plan - Yearly",
            "paid_at": datetime.utcnow() - timedelta(days=30)
        },
        {
            "user_id": users[4].id,
            "subscription_id": subscriptions[2].id,
            "amount": Decimal("1999.99"),
            "currency": "USD",
            "status": PaymentStatus.SUCCEEDED,
            "provider": PaymentProvider.STRIPE,
            "provider_transaction_id": "pi_3Xyz789Stripe",
            "payment_method": "card",
            "description": "Enterprise Plan - Yearly",
            "paid_at": datetime.utcnow() - timedelta(days=60)
        },
        {
            "user_id": users[1].id,
            "amount": Decimal("100.00"),
            "currency": "USD",
            "status": PaymentStatus.SUCCEEDED,
            "provider": PaymentProvider.STRIPE,
            "provider_transaction_id": "pi_credits123",
            "payment_method": "card",
            "description": "Credit Purchase - 1000 credits",
            "paid_at": datetime.utcnow() - timedelta(days=5)
        }
    ]

    created_payments = []

    for payment_data in payments_data:
        payment = Payment(**payment_data)
        db.add(payment)
        created_payments.append(payment)

    await db.commit()

    for payment in created_payments:
        await db.refresh(payment)

    print(f"✅ Created {len(created_payments)} payment records")
    return created_payments


async def seed_credit_transactions(db: AsyncSession, users: list, subscriptions: list, payments: list):
    """Create sample credit transactions"""
    print("\n🪙 Creating credit transactions...")

    transactions_data = [
        # John's transactions
        {
            "user_id": users[1].id,
            "amount": 5000,
            "transaction_type": "subscription",
            "description": "Pro plan monthly credits",
            "balance_after": 5000
        },
        {
            "user_id": users[1].id,
            "amount": -100,
            "transaction_type": "usage",
            "description": "API usage deduction",
            "balance_after": 4900
        },
        {
            "user_id": users[1].id,
            "amount": 1000,
            "transaction_type": "purchase",
            "description": "Credit purchase",
            "payment_id": payments[3].id,
            "balance_after": 5900
        },
        # Jane's transactions
        {
            "user_id": users[2].id,
            "amount": 1000,
            "transaction_type": "subscription",
            "description": "Basic plan monthly credits",
            "balance_after": 1000
        },
        # Alice's transactions
        {
            "user_id": users[4].id,
            "amount": 50000,
            "transaction_type": "subscription",
            "description": "Enterprise plan monthly credits",
            "balance_after": 50000
        },
        # Bob's bonus
        {
            "user_id": users[3].id,
            "amount": 100,
            "transaction_type": "bonus",
            "description": "Welcome bonus",
            "balance_after": 100
        }
    ]

    created_transactions = []

    for trans_data in transactions_data:
        transaction = CreditTransaction(**trans_data)
        db.add(transaction)
        created_transactions.append(transaction)

    await db.commit()

    print(f"✅ Created {len(created_transactions)} credit transactions")
    return created_transactions


async def main():
    """Main seed function"""
    print("=" * 80)
    print("🌱 SEEDING DATABASE")
    print("=" * 80)

    async with engine.begin() as conn:
        # Create database session
        async_session = AsyncSession(conn, expire_on_commit=False)

        try:
            # Clear existing data
            await clear_database(async_session)

            # Seed data
            users = await seed_users(async_session)
            organizations = await seed_organizations(async_session, users)
            api_keys = await seed_api_keys(async_session, users, organizations)
            webhooks = await seed_webhooks(async_session, users, organizations)
            subscriptions = await seed_subscriptions(async_session, users)
            payments = await seed_payments(async_session, users, subscriptions)
            credit_transactions = await seed_credit_transactions(async_session, users, subscriptions, payments)

            print("\n" + "=" * 80)
            print("✅ DATABASE SEEDING COMPLETE")
            print("=" * 80)

            print("\n📊 Summary:")
            print(f"   Users: {len(users)}")
            print(f"   Organizations: {len(organizations)}")
            print(f"   API Keys: {len(api_keys)}")
            print(f"   Webhooks: {len(webhooks)}")
            print(f"   Subscriptions: {len(subscriptions)}")
            print(f"   Payments: {len(payments)}")
            print(f"   Credit Transactions: {len(credit_transactions)}")

            print("\n🔐 Test Credentials:")
            print("   Super Admin:")
            print("      Email: admin@example.com")
            print("      Password: Admin123!@#")
            print()
            print("   Regular Users:")
            print("      Email: john@acme.com / jane@startup.io / bob@freelance.dev")
            print("      Password: User123!@#")
            print()
            print("   Admin:")
            print("      Email: alice@enterprise.com")
            print("      Password: User123!@#")

        except Exception as e:
            print(f"\n❌ Error during seeding: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())
