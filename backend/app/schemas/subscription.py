"""
Subscription and Payment Pydantic schemas
Supporting both Stripe and PayPal
"""
from pydantic import Field, field_validator
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal

from app.schemas.common import BaseSchema, TimestampSchema
from app.models import (
    SubscriptionPlan,
    SubscriptionStatus,
    PaymentProvider,
    PaymentStatus
)


# Subscription Plans

class SubscriptionPlanInfo(BaseSchema):
    """Schema for subscription plan information"""
    plan: SubscriptionPlan
    name: str
    description: str
    price_monthly: Decimal
    price_yearly: Decimal
    features: List[str]
    limits: Dict[str, int]
    popular: bool = False


class SubscriptionCreate(BaseSchema):
    """Schema for creating a subscription"""
    plan: SubscriptionPlan
    billing_cycle: str = Field(default="monthly", pattern="^(monthly|yearly)$")
    payment_provider: PaymentProvider
    payment_method_id: Optional[str] = None  # Stripe payment method or PayPal token
    organization_id: Optional[int] = None


class SubscriptionUpdate(BaseSchema):
    """Schema for updating a subscription"""
    plan: Optional[SubscriptionPlan] = None
    billing_cycle: Optional[str] = Field(None, pattern="^(monthly|yearly)$")


class SubscriptionResponse(TimestampSchema):
    """Schema for subscription response"""
    id: int
    user_id: int
    organization_id: Optional[int] = None
    plan: SubscriptionPlan
    status: SubscriptionStatus
    billing_cycle: str
    price: Decimal
    currency: str
    provider: PaymentProvider
    current_period_start: Optional[datetime] = None
    current_period_end: Optional[datetime] = None
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    canceled_at: Optional[datetime] = None
    features: List[str]
    limits: Dict[str, int]


class SubscriptionCancelRequest(BaseSchema):
    """Schema for canceling a subscription"""
    reason: Optional[str] = Field(None, max_length=500)
    cancel_at_period_end: bool = True  # If False, cancel immediately


# Payments

class PaymentCreate(BaseSchema):
    """Schema for creating a payment (one-time or credit purchase)"""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", max_length=3)
    payment_provider: PaymentProvider
    payment_method_id: Optional[str] = None  # Stripe payment method or PayPal order ID
    description: Optional[str] = Field(None, max_length=500)
    credits_to_purchase: Optional[int] = Field(None, gt=0)  # For credit purchases


class PaymentResponse(TimestampSchema):
    """Schema for payment response"""
    id: int
    user_id: int
    subscription_id: Optional[int] = None
    amount: Decimal
    currency: str
    status: PaymentStatus
    provider: PaymentProvider
    payment_method_type: Optional[str] = None
    payment_method_last4: Optional[str] = None
    description: Optional[str] = None
    receipt_url: Optional[str] = None
    invoice_url: Optional[str] = None
    paid_at: Optional[datetime] = None
    credits_purchased: int


class PaymentListResponse(PaymentResponse):
    """Schema for payment in list"""
    pass


class PaymentMethodCreate(BaseSchema):
    """Schema for adding a payment method"""
    provider: PaymentProvider
    payment_method_id: str  # Stripe payment method ID or PayPal billing agreement
    set_as_default: bool = False


class PaymentMethodResponse(BaseSchema):
    """Schema for payment method response"""
    id: str
    provider: PaymentProvider
    type: str  # card, paypal, bank_account
    last4: Optional[str] = None
    brand: Optional[str] = None  # visa, mastercard, etc.
    exp_month: Optional[int] = None
    exp_year: Optional[int] = None
    is_default: bool
    created_at: datetime


# Invoices

class InvoiceResponse(TimestampSchema):
    """Schema for invoice response"""
    id: int
    user_id: int
    subscription_id: Optional[int] = None
    payment_id: Optional[int] = None
    invoice_number: str
    amount_due: Decimal
    amount_paid: Decimal
    currency: str
    status: str
    paid: bool
    provider: PaymentProvider
    invoice_date: datetime
    due_date: Optional[datetime] = None
    paid_at: Optional[datetime] = None
    invoice_pdf: Optional[str] = None
    hosted_invoice_url: Optional[str] = None
    line_items: List[Dict]


class InvoiceListResponse(BaseSchema):
    """Schema for invoice in list"""
    id: int
    invoice_number: str
    amount_due: Decimal
    currency: str
    status: str
    paid: bool
    invoice_date: datetime
    due_date: Optional[datetime] = None
    invoice_pdf: Optional[str] = None


# Credits

class CreditPurchaseRequest(BaseSchema):
    """Schema for purchasing credits"""
    credits: int = Field(..., gt=0, le=1000000)
    payment_provider: PaymentProvider
    payment_method_id: Optional[str] = None

    @field_validator('credits')
    @classmethod
    def validate_credits(cls, v: int) -> int:
        """Validate credit amount (must be in increments of 100)"""
        if v % 100 != 0:
            raise ValueError('Credits must be purchased in increments of 100')
        return v


class CreditPurchaseResponse(BaseSchema):
    """Schema for credit purchase response"""
    credits_purchased: int
    amount_paid: Decimal
    currency: str
    new_balance: int
    payment_id: int
    receipt_url: Optional[str] = None


class CreditTransactionResponse(TimestampSchema):
    """Schema for credit transaction response"""
    id: int
    user_id: int
    amount: int  # Positive for purchase, negative for usage
    balance_after: int
    transaction_type: str
    description: Optional[str] = None
    payment_id: Optional[int] = None


class CreditBalance(BaseSchema):
    """Schema for credit balance response"""
    user_id: int
    current_balance: int
    total_purchased: int
    total_used: int
    total_bonus: int
    last_purchase: Optional[datetime] = None
    recent_transactions: List[CreditTransactionResponse]


# Billing

class BillingInfo(BaseSchema):
    """Schema for billing information"""
    email: Optional[str] = None
    name: Optional[str] = None
    address: Optional[Dict] = None
    tax_id: Optional[str] = None


class BillingInfoUpdate(BillingInfo):
    """Schema for updating billing information"""
    pass


# Webhook Payloads (for Stripe/PayPal webhooks)

class StripeWebhookPayload(BaseSchema):
    """Schema for Stripe webhook payload"""
    type: str
    data: Dict


class PayPalWebhookPayload(BaseSchema):
    """Schema for PayPal webhook payload"""
    event_type: str
    resource: Dict


# Usage-based Billing

class UsageReport(BaseSchema):
    """Schema for usage report"""
    user_id: int
    period_start: datetime
    period_end: datetime
    total_api_calls: int
    total_credits_used: int
    api_calls_by_endpoint: Dict[str, int]
    credits_breakdown: Dict[str, int]
    estimated_cost: Decimal
