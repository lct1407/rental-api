"""
Credit management schemas
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.credit import CreditType, CreditTransactionType


# ==================== Credit Balance Schemas ====================

class CreditPackageResponse(BaseModel):
    """Credit package response"""
    id: int
    credit_type: CreditType
    original_amount: int
    remaining_amount: int
    consumed_amount: int
    expires_at: datetime
    is_expired: bool
    days_until_expiry: Optional[int] = None
    priority: int
    purchase_price: Optional[Decimal] = None
    currency: Optional[str] = None
    granted_by_name: Optional[str] = None
    grant_reason: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CreditBalanceResponse(BaseModel):
    """Detailed credit balance response"""
    total_balance: int
    monthly_balance: int
    purchased_balance: int
    bonus_balance: int
    monthly_consumed: int
    total_consumed: int
    lifetime_consumed: int
    next_monthly_reset: Optional[datetime] = None
    last_consumption: Optional[datetime] = None
    expiring_soon: int = 0
    expiring_soon_amount: int = 0
    low_balance_warning: bool = False
    packages: List[CreditPackageResponse] = []

    class Config:
        from_attributes = True


# ==================== Credit Transaction Schemas ====================

class CreditLedgerResponse(BaseModel):
    """Credit ledger/transaction response"""
    id: int
    transaction_type: CreditTransactionType
    credit_type: Optional[CreditType] = None
    amount: int
    balance_before: int
    balance_after: int
    description: str
    feature_name: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None
    admin_notes: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    ip_address: Optional[str] = None

    class Config:
        from_attributes = True


class CreditActivityResponse(BaseModel):
    """Credit activity with pagination"""
    total: int
    page: int
    page_size: int
    total_pages: int
    transactions: List[CreditLedgerResponse]


# ==================== Credit Purchase Schemas ====================

class CreditPurchaseRequest(BaseModel):
    """Credit purchase request"""
    pricing_id: int = Field(..., description="ID of the credit pricing package")
    quantity: int = Field(1, ge=1, le=100, description="Number of packages to purchase")
    payment_method: str = Field("stripe", description="Payment method: stripe or paypal")
    success_url: Optional[str] = Field(None, description="URL to redirect after successful payment")
    cancel_url: Optional[str] = Field(None, description="URL to redirect after cancelled payment")


class CreditPurchaseResponse(BaseModel):
    """Credit purchase response"""
    checkout_url: str
    session_id: str
    amount: int
    credits: int
    price: Decimal
    currency: str
    expires_in_days: int


class CreditPricingResponse(BaseModel):
    """Credit pricing package response"""
    id: int
    name: str
    display_name: str
    credits: int
    price: Decimal
    currency: str
    discount_percentage: Decimal
    original_price: Optional[Decimal] = None
    price_per_credit: Decimal
    validity_days: int
    is_featured: bool
    is_popular: bool
    badge_text: Optional[str] = None
    description: Optional[str] = None
    features: List[str] = []

    class Config:
        from_attributes = True


# ==================== Feature Definition Schemas ====================

class FeatureCostResponse(BaseModel):
    """Feature cost response"""
    id: int
    feature_key: str
    feature_name: str
    category: str
    credit_cost: int
    admin_exempt: bool
    super_admin_exempt: bool
    rpm_limit: Optional[int] = None
    rph_limit: Optional[int] = None
    rpd_limit: Optional[int] = None
    rpm_limit_monthly: Optional[int] = None
    cost_modifiers: Dict[str, Any] = {}
    plan_overrides: Dict[str, Any] = {}
    description: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True


class FeatureDefinitionCreate(BaseModel):
    """Create feature definition"""
    feature_key: str = Field(..., min_length=1, max_length=100)
    feature_name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    credit_cost: int = Field(1, ge=0)
    admin_exempt: bool = False
    super_admin_exempt: bool = True
    rpm_limit: Optional[int] = Field(None, ge=0)
    rph_limit: Optional[int] = Field(None, ge=0)
    rpd_limit: Optional[int] = Field(None, ge=0)
    rpm_limit_monthly: Optional[int] = Field(None, ge=0)
    cost_modifiers: Dict[str, Any] = {}
    plan_overrides: Dict[str, Any] = {}
    description: Optional[str] = None
    is_active: bool = True


class FeatureDefinitionUpdate(BaseModel):
    """Update feature definition"""
    feature_name: Optional[str] = Field(None, min_length=1, max_length=255)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    credit_cost: Optional[int] = Field(None, ge=0)
    admin_exempt: Optional[bool] = None
    super_admin_exempt: Optional[bool] = None
    rpm_limit: Optional[int] = Field(None, ge=0)
    rph_limit: Optional[int] = Field(None, ge=0)
    rpd_limit: Optional[int] = Field(None, ge=0)
    rpm_limit_monthly: Optional[int] = Field(None, ge=0)
    cost_modifiers: Optional[Dict[str, Any]] = None
    plan_overrides: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== Admin Credit Management Schemas ====================

class AdminGrantCreditsRequest(BaseModel):
    """Admin grant credits request"""
    user_id: int = Field(..., description="User ID to grant credits to")
    amount: int = Field(..., ge=1, description="Amount of credits to grant")
    credit_type: CreditType = Field(CreditType.BONUS, description="Type of credits to grant")
    expires_in_days: int = Field(365, ge=1, le=3650, description="Number of days until credits expire")
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for granting credits")
    notes: Optional[str] = Field(None, max_length=5000, description="Additional notes")


class AdminAdjustCreditsRequest(BaseModel):
    """Admin adjust credits request (can add or remove)"""
    user_id: int = Field(..., description="User ID to adjust credits for")
    adjustment: int = Field(..., description="Amount to adjust (positive to add, negative to remove)")
    reason: str = Field(..., min_length=1, max_length=1000, description="Reason for adjustment")
    notes: Optional[str] = Field(None, max_length=5000, description="Additional notes")


class AdminCreditAdjustmentResponse(BaseModel):
    """Admin credit adjustment response"""
    success: bool
    user_id: int
    adjustment: int
    new_balance: int
    action: str
    reason: str
    package_id: Optional[int] = None
    transaction_id: int


# ==================== Credit Usage Report Schemas ====================

class CreditUsageByFeature(BaseModel):
    """Credit usage breakdown by feature"""
    feature_key: str
    feature_name: str
    credits_consumed: int
    request_count: int
    percentage_of_total: float


class CreditUsageByDay(BaseModel):
    """Credit usage by day"""
    date: str
    credits_consumed: int
    request_count: int


class CreditUsageReport(BaseModel):
    """Comprehensive credit usage report"""
    period_start: datetime
    period_end: datetime
    total_credits_consumed: int
    total_requests: int
    average_cost_per_request: float
    by_feature: List[CreditUsageByFeature]
    by_day: List[CreditUsageByDay]
    top_consuming_features: List[CreditUsageByFeature]


class AdminCreditOverview(BaseModel):
    """Admin overview of system-wide credits"""
    total_credits_in_system: int
    monthly_balance_total: int
    purchased_balance_total: int
    bonus_balance_total: int
    active_wallets: int
    monthly_consumption: int
    monthly_revenue: Decimal
    average_consumption_per_user: float
    top_consumers: List[Dict[str, Any]]


# ==================== Rate Limiting Schemas ====================

class RateLimitStatus(BaseModel):
    """Rate limit status for a specific period"""
    current: int
    limit: int
    remaining: int
    exceeded: bool
    reset_at: Optional[datetime] = None


class RateLimitResponse(BaseModel):
    """Complete rate limit status"""
    rpm: RateLimitStatus
    rph: RateLimitStatus
    rpd: RateLimitStatus
    monthly: RateLimitStatus


class RateLimitRuleCreate(BaseModel):
    """Create rate limit rule"""
    rule_name: str = Field(..., min_length=1, max_length=255)
    rule_type: str = Field(..., description="user, api_key, organization, or global")
    user_id: Optional[int] = None
    api_key_id: Optional[int] = None
    organization_id: Optional[int] = None
    feature_key: Optional[str] = None
    rpm_limit: Optional[int] = Field(None, ge=0)
    rph_limit: Optional[int] = Field(None, ge=0)
    rpd_limit: Optional[int] = Field(None, ge=0)
    rpm_limit_monthly: Optional[int] = Field(None, ge=0)
    burst_limit: Optional[int] = Field(None, ge=0)
    burst_window_seconds: int = Field(1, ge=1, le=60)
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    priority: int = Field(100, ge=0, le=1000)
    reason: Optional[str] = None
    is_active: bool = True

    @field_validator('rule_type')
    def validate_rule_type(cls, v):
        if v not in ['user', 'api_key', 'organization', 'global']:
            raise ValueError('rule_type must be one of: user, api_key, organization, global')
        return v


class RateLimitRuleResponse(BaseModel):
    """Rate limit rule response"""
    id: int
    rule_name: str
    rule_type: str
    user_id: Optional[int] = None
    api_key_id: Optional[int] = None
    organization_id: Optional[int] = None
    feature_key: Optional[str] = None
    rpm_limit: Optional[int] = None
    rph_limit: Optional[int] = None
    rpd_limit: Optional[int] = None
    rpm_limit_monthly: Optional[int] = None
    burst_limit: Optional[int] = None
    burst_window_seconds: int
    is_active: bool
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    priority: int
    created_by_name: Optional[str] = None
    reason: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== Credit Consumption Simulation ====================

class CreditConsumptionSimulation(BaseModel):
    """Simulate credit consumption"""
    feature_key: str
    metadata: Optional[Dict[str, Any]] = None


class CreditConsumptionResponse(BaseModel):
    """Credit consumption response"""
    can_consume: bool
    required_credits: int
    available_credits: int
    remaining_after: Optional[int] = None
    warnings: List[str] = []


# ==================== Utility Schemas ====================

class BulkCreditGrantRequest(BaseModel):
    """Bulk grant credits to multiple users"""
    user_ids: List[int] = Field(..., min_items=1, max_items=1000)
    amount: int = Field(..., ge=1)
    credit_type: CreditType = Field(CreditType.BONUS)
    expires_in_days: int = Field(365, ge=1, le=3650)
    reason: str = Field(..., min_length=1, max_length=1000)


class BulkCreditGrantResponse(BaseModel):
    """Bulk credit grant response"""
    total_users: int
    successful: int
    failed: int
    results: List[Dict[str, Any]]
