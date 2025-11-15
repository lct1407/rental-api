/**
 * User Service
 *
 * Handles all user-related API calls
 */
import apiClient from './api'
import type { User, PaginatedResponse } from '../types'

export interface UserUpdate {
  full_name?: string
  phone_number?: string
  company_name?: string
  bio?: string
  avatar_url?: string
  timezone?: string
  language?: string
}

export interface UserStats {
  credits: number
  api_keys_count: number
  subscription_plan: string
  member_since: string
  last_login: string
  total_logins: number
  email_verified: boolean
  two_factor_enabled: boolean
}

class UserService {
  /**
   * Get current user profile
   */
  async getProfile(): Promise<User> {
    const response = await apiClient.get<User>('/users/me')
    return response.data
  }

  /**
   * Update current user profile
   */
  async updateProfile(data: UserUpdate): Promise<User> {
    const response = await apiClient.put<User>('/users/me', data)
    return response.data
  }

  /**
   * Get user statistics
   */
  async getStats(): Promise<UserStats> {
    const response = await apiClient.get<UserStats>('/users/me/stats')
    return response.data
  }

  /**
   * Delete current user account
   */
  async deleteAccount(): Promise<void> {
    await apiClient.delete('/users/me')
  }

  // Admin endpoints

  /**
   * List all users (admin only)
   */
  async listUsers(params?: {
    page?: number
    limit?: number
    search?: string
    role?: string
    status?: string
    sort_by?: string
    sort_order?: 'asc' | 'desc'
  }): Promise<PaginatedResponse<User>> {
    const response = await apiClient.get<PaginatedResponse<User>>('/users', { params })
    return response.data
  }

  /**
   * Get user by ID (admin only)
   */
  async getUserById(userId: number): Promise<User> {
    const response = await apiClient.get<User>(`/users/${userId}`)
    return response.data
  }

  /**
   * Suspend user (admin only)
   */
  async suspendUser(userId: number, reason: string, durationDays?: number): Promise<User> {
    const response = await apiClient.put<User>(
      `/users/${userId}/suspend`,
      null,
      { params: { reason, duration_days: durationDays } }
    )
    return response.data
  }

  /**
   * Activate user (admin only)
   */
  async activateUser(userId: number): Promise<User> {
    const response = await apiClient.put<User>(`/users/${userId}/activate`)
    return response.data
  }

  /**
   * Add credits to user (admin only)
   */
  async addCredits(userId: number, credits: number): Promise<User> {
    const response = await apiClient.post<User>(
      `/users/${userId}/credits`,
      null,
      { params: { credits } }
    )
    return response.data
  }

  /**
   * Get users overview stats (admin only)
   */
  async getUsersOverview(): Promise<{
    total: number
    active: number
    suspended: number
    inactive: number
    new_today: number
  }> {
    const response = await apiClient.get('/users/stats/overview')
    return response.data
  }
}

export default new UserService()
