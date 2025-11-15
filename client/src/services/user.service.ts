/**
 * User Service
 */

import { apiService } from './api'
import { API_ENDPOINTS } from '../config/api'
import type {
  UserResponse,
  UserProfileResponse,
  UserUpdate,
  PaginatedResponse,
  MessageResponse,
} from '../types'

export const userService = {
  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<UserProfileResponse> {
    return apiService.get<UserProfileResponse>(API_ENDPOINTS.USERS.ME)
  },

  /**
   * Update current user profile
   */
  async updateCurrentUser(data: UserUpdate): Promise<UserResponse> {
    return apiService.put<UserResponse>(API_ENDPOINTS.USERS.UPDATE_ME, data)
  },

  /**
   * Delete current user account
   */
  async deleteCurrentUser(): Promise<MessageResponse> {
    return apiService.delete<MessageResponse>(API_ENDPOINTS.USERS.DELETE_ME)
  },

  /**
   * Get current user statistics
   */
  async getCurrentUserStats(): Promise<{
    total_api_calls: number
    total_credits_used: number
    total_api_keys: number
    total_webhooks: number
  }> {
    return apiService.get(API_ENDPOINTS.USERS.STATS)
  },

  /**
   * Get all users (admin only)
   */
  async getAllUsers(params?: {
    page?: number
    limit?: number
    search?: string
    status?: string
    role?: string
  }): Promise<PaginatedResponse<UserResponse>> {
    const queryParams = new URLSearchParams()
    if (params?.page) queryParams.append('page', params.page.toString())
    if (params?.limit) queryParams.append('limit', params.limit.toString())
    if (params?.search) queryParams.append('search', params.search)
    if (params?.status) queryParams.append('status', params.status)
    if (params?.role) queryParams.append('role', params.role)

    const endpoint = `${API_ENDPOINTS.USERS.LIST}?${queryParams.toString()}`
    return apiService.get<PaginatedResponse<UserResponse>>(endpoint)
  },

  /**
   * Get user by ID (admin only)
   */
  async getUserById(userId: number | string): Promise<UserResponse> {
    return apiService.get<UserResponse>(API_ENDPOINTS.USERS.BY_ID(userId))
  },

  /**
   * Suspend user (admin only)
   */
  async suspendUser(userId: number | string, reason: string, durationDays?: number): Promise<MessageResponse> {
    return apiService.put<MessageResponse>(API_ENDPOINTS.USERS.SUSPEND(userId), {
      reason,
      duration_days: durationDays,
    })
  },

  /**
   * Activate user (admin only)
   */
  async activateUser(userId: number | string): Promise<MessageResponse> {
    return apiService.put<MessageResponse>(API_ENDPOINTS.USERS.ACTIVATE(userId), {})
  },

  /**
   * Add credits to user (admin only)
   */
  async addCredits(userId: number | string, credits: number, reason?: string): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(API_ENDPOINTS.USERS.ADD_CREDITS(userId), {
      credits,
      reason,
    })
  },

  /**
   * Get user statistics overview (admin only)
   */
  async getUserStatsOverview(): Promise<{
    total_users: number
    active_users: number
    suspended_users: number
    total_credits_distributed: number
  }> {
    return apiService.get(API_ENDPOINTS.USERS.OVERVIEW)
  },
}
