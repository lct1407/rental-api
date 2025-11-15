"""
Subscription and Payment models with incremental bigint ID
Supports both Stripe and PayPal
"""
from sqlalchemy import Column, String, Integer, JSON, Boolean, DateTime, ForeignKey, BigInteger, Numeric, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from decimal import Decimal


class SubscriptionPlan(str, enum.Enum):
    """Subscription plan tiers"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status"""
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    TRIALING = "trialing"


class PaymentProvider(str, enum.Enum):
    """Payment provider"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    MANUAL = "manual"


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELED = "canceled"
    REFUNDED = "refunded"


class Subscription(Base):
    """Subscription model"""

    __tablename__ = "subscriptions"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True)

    # Plan Details
    plan = Column(Enum(SubscriptionPlan), nullable=False)
    status = Column(Enum(SubscriptionStatus), default=SubscriptionStatus.ACTIVE, nullable=False)

    # Billing
    billing_cycle = Column(String(50), default="monthly", nullable=False)  # monthly, yearly
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Provider
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_subscription_id = Column(String(255), unique=True, index=True)
    provider_customer_id = Column(String(255))

    # Dates
    trial_start = Column(DateTime(timezone=True))
    trial_end = Column(DateTime(timezone=True))
    current_period_start = Column(DateTime(timezone=True))
    current_period_end = Column(DateTime(timezone=True))
    canceled_at = Column(DateTime(timezone=True))
    ended_at = Column(DateTime(timezone=True))

    # Features & Limits
    features = Column(JSON, default=[], nullable=False)
    limits = Column(JSON, default={}, nullable=False)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", back_populates="subscriptions")
    organization = relationship("Organization", back_populates="subscriptions")
    payments = relationship(
        "Payment",
        back_populates="subscription",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self):
        return f"<Subscription(id={self.id}, plan={self.plan}, status={self.status})>"


class Payment(Base):
    """Payment transaction model"""

    __tablename__ = "payments"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(BigInteger, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)

    # Payment Details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)

    # Provider
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_payment_id = Column(String(255), unique=True, index=True)
    provider_customer_id = Column(String(255))

    # Payment Method
    payment_method_type = Column(String(50))  # card, paypal, etc
    payment_method_last4 = Column(String(4))
    payment_method_brand = Column(String(50))

    # Transaction Details
    description = Column(Text)
    receipt_url = Column(String(500))
    invoice_url = Column(String(500))

    # Timestamps
    paid_at = Column(DateTime(timezone=True))
    refunded_at = Column(DateTime(timezone=True))
    failed_at = Column(DateTime(timezone=True))

    # Error
    failure_code = Column(String(100))
    failure_message = Column(Text)

    # Credits
    credits_purchased = Column(Integer, default=0, nullable=False)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount}, status={self.status}, provider={self.provider})>"


class Invoice(Base):
    """Invoice model"""

    __tablename__ = "invoices"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(BigInteger, ForeignKey("subscriptions.id", ondelete="SET NULL"), nullable=True)
    payment_id = Column(BigInteger, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)

    # Invoice Details
    invoice_number = Column(String(100), unique=True, index=True, nullable=False)
    amount_due = Column(Numeric(10, 2), nullable=False)
    amount_paid = Column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Status
    status = Column(String(50), default="draft", nullable=False)  # draft, open, paid, void, uncollectible
    paid = Column(Boolean, default=False, nullable=False)

    # Provider
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_invoice_id = Column(String(255), unique=True, index=True)

    # Dates
    invoice_date = Column(DateTime(timezone=True), nullable=False)
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))

    # URLs
    invoice_pdf = Column(String(500))
    hosted_invoice_url = Column(String(500))

    # Line Items
    line_items = Column(JSON, default=[], nullable=False)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<Invoice(id={self.id}, number={self.invoice_number}, status={self.status})>"


class CreditTransaction(Base):
    """Credit transaction history"""

    __tablename__ = "credit_transactions"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(BigInteger, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)

    # Transaction Details
    amount = Column(Integer, nullable=False)  # Can be positive (purchase) or negative (usage)
    balance_after = Column(Integer, nullable=False)
    transaction_type = Column(String(50), nullable=False)  # purchase, usage, refund, bonus, expiration
    description = Column(Text)

    # Metadata
    user_metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<CreditTransaction(id={self.id}, user_id={self.user_id}, amount={self.amount})>"
