export type UserRole = 'user' | 'admin' | 'super_admin'

export type SubscriptionPlan = 'free' | 'basic' | 'pro' | 'enterprise'

export type UserStatus = 'active' | 'inactive' | 'suspended' | 'deleted'

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  phone_number?: string
  company_name?: string
  bio?: string
  avatar_url?: string
  role: UserRole
  status: UserStatus
  plan: SubscriptionPlan
  email_verified: boolean
  email_verified_at?: string
  two_factor_enabled: boolean
  credits: number
  max_api_keys: number
  api_rate_limit: number
  last_login_at?: string
  last_login_ip?: string
  login_count: number
  timezone?: string
  language?: string
  created_at: string
  updated_at: string
}

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

// API Keys
export interface ApiKey {
  id: number
  name: string
  description?: string
  key_prefix: string
  last_four: string
  scopes: string[]
  ip_whitelist?: string[]
  allowed_origins?: string[]
  rate_limit_per_hour: number
  rate_limit_per_day: number
  usage_count: number
  last_used_at?: string
  last_used_ip?: string
  is_active: boolean
  expires_at?: string
  created_at: string
  updated_at: string
}

export interface ApiKeyWithSecret extends ApiKey {
  key: string // Full key only returned once on creation
}

// Webhooks
export interface Webhook {
  id: number
  name: string
  url: string
  events: string[]
  description?: string
  secret: string
  is_active: boolean
  delivery_count: number
  failed_count: number
  last_delivery_at?: string
  created_at: string
  updated_at: string
}

export interface WebhookDelivery {
  id: number
  webhook_id: number
  event_type: string
  payload: any
  status: 'pending' | 'success' | 'failed'
  response_status_code?: number
  response_body?: string
  error_message?: string
  retry_count: number
  next_retry_at?: string
  delivered_at?: string
  created_at: string
}

// Subscriptions
export interface Subscription {
  id: number
  user_id: number
  plan: SubscriptionPlan
  status: 'active' | 'cancelled' | 'past_due' | 'trialing'
  billing_cycle: 'monthly' | 'yearly'
  current_period_start: string
  current_period_end: string
  cancel_at_period_end: boolean
  cancelled_at?: string
  auto_renew: boolean
  created_at: string
  updated_at: string
}

export interface Payment {
  id: number
  amount: number
  currency: string
  status: 'pending' | 'completed' | 'failed' | 'refunded'
  provider: 'stripe' | 'paypal'
  provider_transaction_id?: string
  payment_method?: string
  description?: string
  paid_at?: string
  created_at: string
}

// Analytics
export interface UsageStats {
  total_calls: number
  successful_calls: number
  failed_calls: number
  total_credits_used: number
  avg_response_time: number
  p95_response_time: number
  p99_response_time: number
  period_start: string
  period_end: string
}

export interface RealTimeMetrics {
  current_rps: number
  avg_response_time_5min: number
  error_rate_5min: number
  active_api_keys: number
  credits_remaining: number
  timestamp: string
}

// Pagination
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  limit: number
  pages: number
}
