/**
 * Webhook Service
 *
 * Handles all webhook-related operations
 */
import apiClient from './api'
import type { Webhook, PaginatedResponse } from '../types'

export interface CreateWebhookData {
  name: string
  url: string
  events: string[]
  description?: string
  secret?: string
  headers?: Record<string, string>
  retry_config?: {
    max_retries: number
    retry_delay: number
  }
}

export interface UpdateWebhookData {
  name?: string
  url?: string
  events?: string[]
  description?: string
  is_active?: boolean
  headers?: Record<string, string>
  retry_config?: {
    max_retries: number
    retry_delay: number
  }
}

export interface WebhookDelivery {
  id: number
  webhook_id: number
  event_type: string
  payload: Record<string, any>
  response_status?: number
  response_body?: string
  delivered_at?: string
  failed_at?: string
  retry_count: number
  next_retry_at?: string
  created_at: string
}

class WebhookService {
  /**
   * List user's webhooks
   */
  async listWebhooks(params?: {
    page?: number
    limit?: number
    is_active?: boolean
    event_type?: string
  }): Promise<PaginatedResponse<Webhook>> {
    const response = await apiClient.get<PaginatedResponse<Webhook>>('/webhooks', { params })
    return response.data
  }

  /**
   * Get webhook by ID
   */
  async getWebhookById(webhookId: number): Promise<Webhook> {
    const response = await apiClient.get<Webhook>(`/webhooks/${webhookId}`)
    return response.data
  }

  /**
   * Create new webhook
   */
  async createWebhook(data: CreateWebhookData): Promise<Webhook> {
    const response = await apiClient.post<Webhook>('/webhooks', data)
    return response.data
  }

  /**
   * Update webhook
   */
  async updateWebhook(webhookId: number, data: UpdateWebhookData): Promise<Webhook> {
    const response = await apiClient.put<Webhook>(`/webhooks/${webhookId}`, data)
    return response.data
  }

  /**
   * Delete webhook
   */
  async deleteWebhook(webhookId: number): Promise<void> {
    await apiClient.delete(`/webhooks/${webhookId}`)
  }

  /**
   * Toggle webhook active status
   */
  async toggleWebhook(webhookId: number, isActive: boolean): Promise<Webhook> {
    const response = await apiClient.put<Webhook>(`/webhooks/${webhookId}`, {
      is_active: isActive
    })
    return response.data
  }

  /**
   * Test webhook by sending a test event
   */
  async testWebhook(webhookId: number): Promise<{
    success: boolean
    status_code?: number
    response_time?: number
    error?: string
  }> {
    const response = await apiClient.post(`/webhooks/${webhookId}/test`)
    return response.data
  }

  /**
   * Get webhook delivery history
   */
  async getDeliveries(webhookId: number, params?: {
    page?: number
    limit?: number
    status?: 'success' | 'failed' | 'pending'
    start_date?: string
    end_date?: string
  }): Promise<PaginatedResponse<WebhookDelivery>> {
    const response = await apiClient.get<PaginatedResponse<WebhookDelivery>>(
      `/webhooks/${webhookId}/deliveries`,
      { params }
    )
    return response.data
  }

  /**
   * Retry failed webhook delivery
   */
  async retryDelivery(webhookId: number, deliveryId: number): Promise<WebhookDelivery> {
    const response = await apiClient.post<WebhookDelivery>(
      `/webhooks/${webhookId}/deliveries/${deliveryId}/retry`
    )
    return response.data
  }

  /**
   * Get webhook statistics
   */
  async getWebhookStats(webhookId: number, params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    total_deliveries: number
    successful_deliveries: number
    failed_deliveries: number
    avg_response_time: number
    success_rate: number
    deliveries_by_day: Array<{ date: string; success: number; failed: number }>
  }> {
    const response = await apiClient.get(`/webhooks/${webhookId}/stats`, { params })
    return response.data
  }

  /**
   * Get available webhook events
   */
  async getAvailableEvents(): Promise<Array<{
    event: string
    description: string
    payload_example: Record<string, any>
  }>> {
    const response = await apiClient.get('/webhooks/events')
    return response.data
  }

  /**
   * Regenerate webhook secret
   */
  async regenerateSecret(webhookId: number): Promise<{
    secret: string
  }> {
    const response = await apiClient.post(`/webhooks/${webhookId}/regenerate-secret`)
    return response.data
  }
}

export default new WebhookService()
