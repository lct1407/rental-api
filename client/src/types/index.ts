// ==================== Enums ====================
export type UserRole = 'admin' | 'user'

export type SubscriptionPlan = 'free' | 'starter' | 'pro' | 'enterprise'

export type UserStatus = 'active' | 'suspended' | 'inactive'

// ==================== Auth Types ====================
export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserResponse
}

export interface TempTokenResponse {
  requires_2fa: boolean
  temp_token: string
  message: string
}

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name?: string
}

export interface PasswordChangeData {
  current_password: string
  new_password: string
}

// ==================== User Types ====================
export interface User {
  id: number
  email: string
  username: string
  full_name?: string
  phone_number?: string
  company_name?: string
  bio?: string
  role: UserRole
  status: UserStatus
  email_verified: boolean
  two_factor_enabled: boolean
  credits: number
  last_login_at?: string
  avatar_url?: string
  created_at: string
  updated_at: string
}

export interface UserResponse {
  id: number
  email: string
  username: string
  full_name?: string
  phone_number?: string
  company_name?: string
  bio?: string
  role: UserRole
  status: UserStatus
  email_verified: boolean
  two_factor_enabled: boolean
  credits: number
  last_login_at?: string
  avatar_url?: string
  created_at: string
  updated_at: string
}

export interface UserProfileResponse extends UserResponse {
  api_rate_limit: number
  storage_limit: number
  max_api_keys: number
  max_webhooks: number
  login_count: number
  metadata?: Record<string, unknown>
}

export interface UserUpdate {
  full_name?: string
  phone_number?: string
  company_name?: string
  bio?: string
  avatar_url?: string
  preferences?: Record<string, unknown>
  notification_settings?: Record<string, unknown>
}

// ==================== API Key Types ====================
export interface ApiKey {
  id: number
  user_id: number
  name: string
  key: string
  scopes: string[]
  is_active: boolean
  expires_at?: string
  last_used_at?: string
  created_at: string
  updated_at: string
}

export interface ApiKeyCreate {
  name: string
  scopes?: string[]
  expires_at?: string
}

export interface ApiKeyUpdate {
  name?: string
  scopes?: string[]
  is_active?: boolean
}

export interface ApiKeyWithSecret extends ApiKey {
  secret: string
}

// ==================== Subscription Types ====================
export interface Subscription {
  id: number
  user_id: number
  plan_id: string
  status: 'active' | 'cancelled' | 'expired' | 'past_due'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  stripe_subscription_id?: string
  created_at: string
  updated_at: string
}

export interface SubscriptionPlanInfo {
  id: string
  name: string
  description: string
  price: number
  currency: string
  interval: 'month' | 'year'
  features: string[]
  credits: number
  api_rate_limit: number
  storage_limit: number
  max_api_keys: number
  max_webhooks: number
}

// ==================== Webhook Types ====================
export interface Webhook {
  id: number
  user_id: number
  url: string
  events: string[]
  secret: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface WebhookCreate {
  url: string
  events: string[]
  secret?: string
}

export interface WebhookUpdate {
  url?: string
  events?: string[]
  is_active?: boolean
}

// ==================== Legacy/UI Types ====================
export interface ApiCall {
  id: string
  userId: string
  endpoint: string
  method: string
  status: number
  responseTime: number
  timestamp: string
  credits: number
}

export interface KPIData {
  totalUsers: number
  totalApiCalls: number
  errorRate: number
  revenue: number
  trend?: 'up' | 'down' | 'neutral'
  change?: number
}

export interface ChartData {
  name: string
  value: number
  [key: string]: string | number
}

export interface Invoice {
  id: string
  date: string
  amount: number
  status: 'paid' | 'pending' | 'failed'
  invoiceNumber: string
  downloadUrl?: string
}

export interface PaymentMethod {
  id: string
  type: 'card'
  last4: string
  brand: string
  expiryMonth: number
  expiryYear: number
  isDefault: boolean
}

export interface PlanFeature {
  name: string
  included: boolean
}

export interface PricingPlan {
  id: SubscriptionPlan
  name: string
  price: number
  billingCycle: 'month' | 'year'
  credits: number
  features: PlanFeature[]
  popular?: boolean
}

export interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  read: boolean
  timestamp: string
}

// ==================== API Response Types ====================
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface SuccessResponse {
  message: string
  data?: unknown
}

export interface ErrorResponse {
  detail: string
  error_code?: string
  field?: string
  errors?: Array<{
    field: string
    message: string
    type: string
  }>
}

export interface MessageResponse {
  message: string
}

// ==================== Admin Types ====================
export interface AdminDashboardStats {
  total_users: number
  active_users: number
  total_revenue: number
  total_api_calls: number
  avg_response_time: number
  error_rate: number
}

export interface AuditLog {
  id: number
  user_id?: number
  action: string
  resource_type: string
  resource_id?: string
  details: Record<string, unknown>
  ip_address?: string
  user_agent?: string
  created_at: string
}
