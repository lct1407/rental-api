/**
 * API Key Service
 *
 * Handles all API key-related operations
 */
import apiClient from './api'
import type { ApiKey, PaginatedResponse } from '../types'

export interface CreateApiKeyData {
  name: string
  description?: string
  permissions?: string[]
  rate_limit?: number
  expires_at?: string
}

export interface ApiKeyStats {
  total_keys: number
  active_keys: number
  expired_keys: number
  total_requests_today: number
  total_requests_month: number
}

class ApiKeyService {
  /**
   * List user's API keys
   */
  async listKeys(params?: {
    page?: number
    limit?: number
    status?: 'active' | 'expired' | 'revoked'
  }): Promise<PaginatedResponse<ApiKey>> {
    const response = await apiClient.get<PaginatedResponse<ApiKey>>('/api-keys', { params })
    return response.data
  }

  /**
   * Get API key by ID
   */
  async getKeyById(keyId: number): Promise<ApiKey> {
    const response = await apiClient.get<ApiKey>(`/api-keys/${keyId}`)
    return response.data
  }

  /**
   * Create new API key
   */
  async createKey(data: CreateApiKeyData): Promise<ApiKey> {
    const response = await apiClient.post<ApiKey>('/api-keys', data)
    return response.data
  }

  /**
   * Rotate API key (generate new key value)
   */
  async rotateKey(keyId: number): Promise<ApiKey> {
    const response = await apiClient.put<ApiKey>(`/api-keys/${keyId}/rotate`)
    return response.data
  }

  /**
   * Revoke API key
   */
  async revokeKey(keyId: number): Promise<void> {
    await apiClient.delete(`/api-keys/${keyId}`)
  }

  /**
   * Get API key usage statistics
   */
  async getKeyStats(keyId: number, params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    total_requests: number
    successful_requests: number
    failed_requests: number
    avg_response_time: number
    requests_by_day: Array<{ date: string; count: number }>
  }> {
    const response = await apiClient.get(`/api-keys/${keyId}/stats`, { params })
    return response.data
  }

  /**
   * Get user's API key statistics overview
   */
  async getStats(): Promise<ApiKeyStats> {
    const response = await apiClient.get<ApiKeyStats>('/api-keys/stats/overview')
    return response.data
  }

  /**
   * Test API key validity
   */
  async testKey(apiKey: string): Promise<{
    valid: boolean
    key_id?: number
    rate_limit_remaining?: number
  }> {
    const response = await apiClient.post('/api-keys/test', { api_key: apiKey })
    return response.data
  }
}

export default new ApiKeyService()
