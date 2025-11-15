"""
Advanced Credit Management Models
Supports monthly grants, purchased credits with expiration, and comprehensive tracking
"""
from sqlalchemy import Column, String, Integer, JSON, Boolean, DateTime, ForeignKey, BigInteger, Numeric, Enum, Text
from sqlalchemy.orm import relationship
from app.database import Base
import enum
from datetime import datetime, timedelta


class CreditType(str, enum.Enum):
    """Credit type enumeration"""
    MONTHLY_GRANT = "monthly_grant"      # Free credits from subscription
    PURCHASED = "purchased"               # Bought credits
    BONUS = "bonus"                       # Admin granted bonus
    REFUND = "refund"                    # Refunded credits
    PROMOTIONAL = "promotional"          # Promotional credits


class CreditTransactionType(str, enum.Enum):
    """Credit transaction type enumeration"""
    CREDIT = "credit"                    # Adding credits
    DEBIT = "debit"                      # Using credits
    EXPIRE = "expire"                    # Credits expired
    ROLLOVER = "rollover"                # Credits rolled over
    ADMIN_ADJUSTMENT = "admin_adjustment"  # Admin manual adjustment


class CreditWallet(Base):
    """Main credit wallet for each user"""
    __tablename__ = "credit_wallets"

    # Foreign Keys
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)

    # Current balance
    total_balance = Column(Integer, default=0, nullable=False)
    monthly_balance = Column(Integer, default=0, nullable=False)      # From subscription
    purchased_balance = Column(Integer, default=0, nullable=False)    # Purchased credits
    bonus_balance = Column(Integer, default=0, nullable=False)        # Admin/promotional credits

    # Usage tracking
    total_consumed = Column(Integer, default=0, nullable=False)
    monthly_consumed = Column(Integer, default=0, nullable=False)
    lifetime_consumed = Column(Integer, default=0, nullable=False)

    # Metadata
    last_monthly_reset = Column(DateTime(timezone=True))
    next_monthly_reset = Column(DateTime(timezone=True))
    last_consumption = Column(DateTime(timezone=True))

    # Alert thresholds
    low_balance_threshold = Column(Integer, default=100, nullable=False)
    alert_sent = Column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="credit_wallet")
    credit_ledgers = relationship("CreditLedger", back_populates="wallet", cascade="all, delete-orphan", lazy="selectin")
    credit_packages = relationship("CreditPackage", back_populates="wallet", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self):
        return f"<CreditWallet(id={self.id}, user_id={self.user_id}, total_balance={self.total_balance})>"


class CreditLedger(Base):
    """Detailed credit transaction history with full audit trail"""
    __tablename__ = "credit_ledgers"

    # Foreign Keys
    wallet_id = Column(BigInteger, ForeignKey("credit_wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Transaction details
    transaction_type = Column(Enum(CreditTransactionType), nullable=False, index=True)
    credit_type = Column(Enum(CreditType), nullable=True)
    amount = Column(Integer, nullable=False)  # Positive for credit, negative for debit
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    # Source information
    source_id = Column(String(255), index=True)  # API call ID, purchase ID, etc.
    source_type = Column(String(100))  # api_call, purchase, admin_grant, etc.

    # Feature consumption details
    feature_id = Column(BigInteger, ForeignKey("feature_definitions.id", ondelete="SET NULL"), nullable=True)
    feature_name = Column(String(255))

    # Admin actions
    admin_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    admin_notes = Column(Text)

    # Metadata
    description = Column(Text, nullable=False)
    metadata = Column(JSON, default={}, nullable=False)
    expires_at = Column(DateTime(timezone=True))

    # IP tracking for security
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(String(500))

    # Relationships
    wallet = relationship("CreditWallet", back_populates="credit_ledgers")
    feature = relationship("FeatureDefinition", back_populates="credit_ledgers")
    admin = relationship("User", foreign_keys=[admin_id])

    def __repr__(self):
        return f"<CreditLedger(id={self.id}, type={self.transaction_type}, amount={self.amount})>"


class CreditPackage(Base):
    """Individual credit packages with expiration and priority"""
    __tablename__ = "credit_packages"

    # Foreign Keys
    wallet_id = Column(BigInteger, ForeignKey("credit_wallets.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Package details
    credit_type = Column(Enum(CreditType), nullable=False)
    original_amount = Column(Integer, nullable=False)
    remaining_amount = Column(Integer, nullable=False)
    consumed_amount = Column(Integer, default=0, nullable=False)

    # Expiration
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    is_expired = Column(Boolean, default=False, nullable=False, index=True)
    expired_at = Column(DateTime(timezone=True))

    # Purchase information (if applicable)
    payment_id = Column(BigInteger, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    purchase_price = Column(Numeric(10, 2))
    currency = Column(String(3), default="USD")

    # Usage priority (lower number = higher priority)
    # Priority 1: Monthly grants (use first)
    # Priority 2: Expiring soon
    # Priority 3: Purchased (FIFO)
    # Priority 4: Bonus/Promotional
    priority = Column(Integer, default=100, nullable=False, index=True)

    # Admin grant information
    granted_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    grant_reason = Column(Text)

    # Metadata
    notes = Column(Text)
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    wallet = relationship("CreditWallet", back_populates="credit_packages")
    payment = relationship("Payment")
    granted_by = relationship("User", foreign_keys=[granted_by_id])

    def __repr__(self):
        return f"<CreditPackage(id={self.id}, type={self.credit_type}, remaining={self.remaining_amount})>"


class FeatureDefinition(Base):
    """Define credit cost and rate limits for each feature"""
    __tablename__ = "feature_definitions"

    # Feature identification
    feature_key = Column(String(100), unique=True, index=True, nullable=False)
    feature_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)  # api_call, webhook, analytics, export, etc.

    # Credit cost
    credit_cost = Column(Integer, default=1, nullable=False)

    # Admin and role exemptions
    admin_exempt = Column(Boolean, default=False, nullable=False)
    super_admin_exempt = Column(Boolean, default=True, nullable=False)

    # Rate limiting specific to this feature
    rpm_limit = Column(Integer)  # Requests per minute
    rph_limit = Column(Integer)  # Requests per hour
    rpd_limit = Column(Integer)  # Requests per day
    rpm_limit_monthly = Column(Integer)  # Requests per month

    # Cost modifiers based on parameters
    cost_modifiers = Column(JSON, default={}, nullable=False)
    # Example: {
    #   "response_size": {"per_kb": 0.1},
    #   "complexity": {"high": 2, "medium": 1.5, "low": 1},
    #   "premium_feature": {"enabled": 5}
    # }

    # Subscription plan specific limits
    plan_overrides = Column(JSON, default={}, nullable=False)
    # Example: {
    #   "free": {"credit_cost": 2, "rpm_limit": 10},
    #   "pro": {"credit_cost": 1, "rpm_limit": 100},
    #   "enterprise": {"credit_cost": 0, "rpm_limit": 1000}
    # }

    # Active status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_billable = Column(Boolean, default=True, nullable=False)

    # Display information
    description = Column(Text)
    display_order = Column(Integer, default=100)
    icon = Column(String(100))
    color = Column(String(20))

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    credit_ledgers = relationship("CreditLedger", back_populates="feature")

    def __repr__(self):
        return f"<FeatureDefinition(id={self.id}, key={self.feature_key}, cost={self.credit_cost})>"


class CreditPricing(Base):
    """Dynamic credit pricing tiers for purchase"""
    __tablename__ = "credit_pricing"

    # Package details
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(255), nullable=False)
    credits = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)

    # Discount
    discount_percentage = Column(Numeric(5, 2), default=0, nullable=False)
    original_price = Column(Numeric(10, 2))

    # Validity
    valid_days = Column(Integer, default=365, nullable=False)  # How long credits are valid

    # Display
    is_featured = Column(Boolean, default=False, nullable=False)
    is_popular = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=100, nullable=False)
    badge_text = Column(String(50))  # "Best Value", "Popular", etc.

    # Payment provider integration
    stripe_price_id = Column(String(255), unique=True)
    paypal_plan_id = Column(String(255), unique=True)

    # Active status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Limits
    min_purchase_count = Column(Integer, default=1)
    max_purchase_count = Column(Integer)

    # Metadata
    description = Column(Text)
    features = Column(JSON, default=[], nullable=False)  # List of features/benefits
    metadata = Column(JSON, default={}, nullable=False)

    def __repr__(self):
        return f"<CreditPricing(id={self.id}, name={self.name}, credits={self.credits}, price={self.price})>"


class RateLimitRule(Base):
    """Custom rate limit rules for specific users or API keys"""
    __tablename__ = "rate_limit_rules"

    # Target
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    api_key_id = Column(BigInteger, ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(BigInteger, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True, index=True)

    # Rule details
    rule_name = Column(String(255), nullable=False)
    rule_type = Column(String(50), nullable=False)  # user, api_key, organization, global

    # Limits
    rpm_limit = Column(Integer)  # Requests per minute
    rph_limit = Column(Integer)  # Requests per hour
    rpd_limit = Column(Integer)  # Requests per day
    rpm_limit_monthly = Column(Integer)  # Requests per month

    # Burst allowance
    burst_limit = Column(Integer)  # Allow burst up to this many requests
    burst_window_seconds = Column(Integer, default=1)

    # Feature specific
    feature_key = Column(String(100), index=True)  # If null, applies to all features

    # Active status
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Validity period
    valid_from = Column(DateTime(timezone=True))
    valid_until = Column(DateTime(timezone=True))

    # Priority (lower number = higher priority)
    priority = Column(Integer, default=100, nullable=False)

    # Created by admin
    created_by_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason = Column(Text)

    # Metadata
    metadata = Column(JSON, default={}, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    created_by = relationship("User", foreign_keys=[created_by_id])

    def __repr__(self):
        return f"<RateLimitRule(id={self.id}, type={self.rule_type}, name={self.rule_name})>"
