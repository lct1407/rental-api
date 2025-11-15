/**
 * Subscription Service
 *
 * Handles all subscription and billing-related operations
 */
import apiClient from './api'
import type { Subscription, Payment, PaginatedResponse } from '../types'

export interface SubscriptionPlan {
  id: string
  name: 'free' | 'basic' | 'pro' | 'enterprise'
  display_name: string
  description: string
  price: number
  billing_period: 'monthly' | 'yearly'
  credits_per_month: number
  max_api_keys: number
  rate_limit: number
  features: string[]
  is_popular?: boolean
}

export interface CreateSubscriptionData {
  plan_id: string
  billing_period: 'monthly' | 'yearly'
  payment_method_id?: string
}

export interface UpdatePaymentMethodData {
  payment_method_id: string
  set_as_default?: boolean
}

export interface PaymentMethod {
  id: string
  type: 'card' | 'bank_account' | 'paypal'
  last4?: string
  brand?: string
  exp_month?: number
  exp_year?: number
  is_default: boolean
  created_at: string
}

export interface Invoice {
  id: string
  subscription_id: number
  amount: number
  currency: string
  status: 'paid' | 'pending' | 'failed' | 'refunded'
  invoice_number: string
  invoice_date: string
  due_date: string
  paid_at?: string
  invoice_url?: string
  items: Array<{
    description: string
    quantity: number
    unit_price: number
    total: number
  }>
  created_at: string
}

class SubscriptionService {
  /**
   * Get available subscription plans
   */
  async getPlans(billingPeriod?: 'monthly' | 'yearly'): Promise<SubscriptionPlan[]> {
    const response = await apiClient.get<SubscriptionPlan[]>('/subscriptions/plans', {
      params: { billing_period: billingPeriod }
    })
    return response.data
  }

  /**
   * Get current user's subscription
   */
  async getCurrentSubscription(): Promise<Subscription> {
    const response = await apiClient.get<Subscription>('/subscriptions/me')
    return response.data
  }

  /**
   * Create new subscription
   */
  async createSubscription(data: CreateSubscriptionData): Promise<Subscription> {
    const response = await apiClient.post<Subscription>('/subscriptions', data)
    return response.data
  }

  /**
   * Update subscription plan
   */
  async updateSubscription(
    subscriptionId: number,
    data: {
      plan_id?: string
      billing_period?: 'monthly' | 'yearly'
    }
  ): Promise<Subscription> {
    const response = await apiClient.put<Subscription>(
      `/subscriptions/${subscriptionId}`,
      data
    )
    return response.data
  }

  /**
   * Cancel subscription
   */
  async cancelSubscription(
    subscriptionId: number,
    immediately: boolean = false
  ): Promise<Subscription> {
    const response = await apiClient.post<Subscription>(
      `/subscriptions/${subscriptionId}/cancel`,
      null,
      { params: { immediately } }
    )
    return response.data
  }

  /**
   * Reactivate cancelled subscription
   */
  async reactivateSubscription(subscriptionId: number): Promise<Subscription> {
    const response = await apiClient.post<Subscription>(
      `/subscriptions/${subscriptionId}/reactivate`
    )
    return response.data
  }

  /**
   * Get subscription usage statistics
   */
  async getUsageStats(subscriptionId: number): Promise<{
    current_period_start: string
    current_period_end: string
    credits_used: number
    credits_remaining: number
    credits_total: number
    api_calls_count: number
    usage_percentage: number
  }> {
    const response = await apiClient.get(`/subscriptions/${subscriptionId}/usage`)
    return response.data
  }

  // Payment Methods

  /**
   * List payment methods
   */
  async getPaymentMethods(): Promise<PaymentMethod[]> {
    const response = await apiClient.get<PaymentMethod[]>('/billing/payment-methods')
    return response.data
  }

  /**
   * Add payment method
   */
  async addPaymentMethod(data: UpdatePaymentMethodData): Promise<PaymentMethod> {
    const response = await apiClient.post<PaymentMethod>('/billing/payment-methods', data)
    return response.data
  }

  /**
   * Delete payment method
   */
  async deletePaymentMethod(paymentMethodId: string): Promise<void> {
    await apiClient.delete(`/billing/payment-methods/${paymentMethodId}`)
  }

  /**
   * Set default payment method
   */
  async setDefaultPaymentMethod(paymentMethodId: string): Promise<PaymentMethod> {
    const response = await apiClient.put<PaymentMethod>(
      `/billing/payment-methods/${paymentMethodId}/default`
    )
    return response.data
  }

  // Payments & Invoices

  /**
   * Get payment history
   */
  async getPayments(params?: {
    page?: number
    limit?: number
    status?: 'completed' | 'pending' | 'failed' | 'refunded'
    start_date?: string
    end_date?: string
  }): Promise<PaginatedResponse<Payment>> {
    const response = await apiClient.get<PaginatedResponse<Payment>>('/billing/payments', {
      params
    })
    return response.data
  }

  /**
   * Get payment by ID
   */
  async getPaymentById(paymentId: number): Promise<Payment> {
    const response = await apiClient.get<Payment>(`/billing/payments/${paymentId}`)
    return response.data
  }

  /**
   * Get invoices
   */
  async getInvoices(params?: {
    page?: number
    limit?: number
    status?: 'paid' | 'pending' | 'failed' | 'refunded'
  }): Promise<PaginatedResponse<Invoice>> {
    const response = await apiClient.get<PaginatedResponse<Invoice>>('/billing/invoices', {
      params
    })
    return response.data
  }

  /**
   * Download invoice PDF
   */
  async downloadInvoice(invoiceId: string): Promise<Blob> {
    const response = await apiClient.get(`/billing/invoices/${invoiceId}/download`, {
      responseType: 'blob'
    })
    return response.data
  }

  // Credits

  /**
   * Purchase additional credits
   */
  async purchaseCredits(amount: number, paymentMethodId?: string): Promise<Payment> {
    const response = await apiClient.post<Payment>('/billing/credits/purchase', {
      amount,
      payment_method_id: paymentMethodId
    })
    return response.data
  }

  /**
   * Get credit balance
   */
  async getCreditBalance(): Promise<{
    current_balance: number
    monthly_allocation: number
    purchased_credits: number
    expires_at?: string
  }> {
    const response = await apiClient.get('/billing/credits/balance')
    return response.data
  }

  /**
   * Get credit usage history
   */
  async getCreditHistory(params?: {
    page?: number
    limit?: number
    start_date?: string
    end_date?: string
  }): Promise<PaginatedResponse<{
    id: number
    type: 'allocation' | 'purchase' | 'usage' | 'refund'
    amount: number
    balance_after: number
    description: string
    created_at: string
  }>> {
    const response = await apiClient.get('/billing/credits/history', { params })
    return response.data
  }
}

export default new subscriptionService()
