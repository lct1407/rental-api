"""
Schemas module - Export all Pydantic schemas
"""

# Common
from app.schemas.common import (
    BaseSchema,
    TimestampSchema,
    PaginationParams,
    PaginatedResponse,
    SuccessResponse,
    ErrorResponse,
    MessageResponse,
    HealthResponse
)

# User
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserProfileResponse,
    PasswordChange,
    UserAdminUpdate,
    UserListResponse,
    UserSuspend
)

# Auth
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TempTokenResponse,
    RefreshTokenRequest,
    TwoFactorEnable,
    TwoFactorEnableResponse,
    TwoFactorVerify,
    TwoFactorDisable,
    PasswordResetRequest,
    PasswordReset,
    LogoutRequest
)

# API Key
from app.schemas.api_key import (
    ApiKeyCreate,
    ApiKeyUpdate,
    ApiKeyResponse,
    ApiKeyWithSecret,
    ApiKeyListResponse,
    ApiKeyUsageStats,
    ApiKeyRotateResponse
)

# Webhook
from app.schemas.webhook import (
    WebhookCreate,
    WebhookUpdate,
    WebhookResponse,
    WebhookListResponse,
    WebhookTest,
    WebhookDeliveryResponse,
    WebhookDeliveryListResponse,
    WebhookDeliveryDetailResponse,
    WebhookStats
)

# Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationDetailResponse,
    OrganizationMemberResponse,
    OrganizationInviteCreate,
    OrganizationInviteResponse,
    OrganizationInviteAccept,
    OrganizationMemberUpdate,
    OrganizationStats
)

# Subscription & Payment
from app.schemas.subscription import (
    SubscriptionPlanInfo,
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionResponse,
    SubscriptionCancelRequest,
    PaymentCreate,
    PaymentResponse,
    PaymentListResponse,
    PaymentMethodCreate,
    PaymentMethodResponse,
    InvoiceResponse,
    InvoiceListResponse,
    CreditPurchaseRequest,
    CreditPurchaseResponse,
    CreditTransactionResponse,
    CreditBalance,
    BillingInfo,
    BillingInfoUpdate,
    StripeWebhookPayload,
    PayPalWebhookPayload,
    UsageReport
)

# Analytics
from app.schemas.analytics import (
    DateRangeFilter,
    UsageStatsSummary,
    UsageStatsTimeSeries,
    UsageStatsResponse,
    RealTimeMetrics,
    EndpointStats,
    GeographicStats,
    ApiKeyAnalytics,
    UserActivityLog,
    SystemMetrics,
    AnalyticsExportRequest,
    AnalyticsExportResponse
)

# Admin
from app.schemas.admin import (
    AdminDashboardStats,
    RecentActivity,
    SystemHealth,
    UserManagementFilter,
    BroadcastMessage,
    MaintenanceMode,
    SystemConfig,
    AuditLogFilter,
    AuditLogResponse,
    SecurityEventResponse,
    BatchUserAction,
    SystemReport,
    CacheStats,
    DatabaseStats,
    FeatureFlag
)

__all__ = [
    # Common
    "BaseSchema",
    "TimestampSchema",
    "PaginationParams",
    "PaginatedResponse",
    "SuccessResponse",
    "ErrorResponse",
    "MessageResponse",
    "HealthResponse",

    # User
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserProfileResponse",
    "PasswordChange",
    "UserAdminUpdate",
    "UserListResponse",
    "UserSuspend",

    # Auth
    "UserRegister",
    "UserLogin",
    "TokenResponse",
    "TempTokenResponse",
    "RefreshTokenRequest",
    "TwoFactorEnable",
    "TwoFactorEnableResponse",
    "TwoFactorVerify",
    "TwoFactorDisable",
    "PasswordResetRequest",
    "PasswordReset",
    "EmailVerify",
    "LogoutRequest",

    # API Key
    "ApiKeyCreate",
    "ApiKeyUpdate",
    "ApiKeyResponse",
    "ApiKeyWithSecret",
    "ApiKeyListResponse",
    "ApiKeyUsageStats",
    "ApiKeyRotateResponse",

    # Webhook
    "WebhookCreate",
    "WebhookUpdate",
    "WebhookResponse",
    "WebhookListResponse",
    "WebhookTest",
    "WebhookDeliveryResponse",
    "WebhookDeliveryListResponse",
    "WebhookDeliveryDetailResponse",
    "WebhookStats",

    # Organization
    "OrganizationCreate",
    "OrganizationUpdate",
    "OrganizationResponse",
    "OrganizationDetailResponse",
    "OrganizationMemberResponse",
    "OrganizationInviteCreate",
    "OrganizationInviteResponse",
    "OrganizationInviteAccept",
    "OrganizationMemberUpdate",
    "OrganizationStats",

    # Subscription & Payment
    "SubscriptionPlanInfo",
    "SubscriptionCreate",
    "SubscriptionUpdate",
    "SubscriptionResponse",
    "SubscriptionCancelRequest",
    "PaymentCreate",
    "PaymentResponse",
    "PaymentListResponse",
    "PaymentMethodCreate",
    "PaymentMethodResponse",
    "InvoiceResponse",
    "InvoiceListResponse",
    "CreditPurchaseRequest",
    "CreditPurchaseResponse",
    "CreditTransactionResponse",
    "CreditBalance",
    "BillingInfo",
    "BillingInfoUpdate",
    "StripeWebhookPayload",
    "PayPalWebhookPayload",
    "UsageReport",

    # Analytics
    "DateRangeFilter",
    "UsageStatsSummary",
    "UsageStatsTimeSeries",
    "UsageStatsResponse",
    "RealTimeMetrics",
    "EndpointStats",
    "GeographicStats",
    "ApiKeyAnalytics",
    "UserActivityLog",
    "SystemMetrics",
    "AnalyticsExportRequest",
    "AnalyticsExportResponse",

    # Admin
    "AdminDashboardStats",
    "RecentActivity",
    "SystemHealth",
    "UserManagementFilter",
    "BroadcastMessage",
    "MaintenanceMode",
    "SystemConfig",
    "AuditLogFilter",
    "AuditLogResponse",
    "SecurityEventResponse",
    "BatchUserAction",
    "SystemReport",
    "CacheStats",
    "DatabaseStats",
    "FeatureFlag",
]
