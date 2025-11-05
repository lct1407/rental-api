export type UserRole = 'admin' | 'user'

export type SubscriptionPlan = 'free' | 'starter' | 'pro' | 'enterprise'

export type UserStatus = 'active' | 'suspended' | 'inactive'

export interface User {
  id: string
  name: string
  email: string
  role: UserRole
  plan: SubscriptionPlan
  credits: number
  apiKey: string
  status: UserStatus
  avatar?: string
  phone?: string
  registrationDate: string
  nextRenewalDate?: string
  billingCycle?: 'monthly' | 'annual'
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
