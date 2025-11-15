/**
 * Authentication Service
 *
 * Handles all authentication-related API calls
 */
import apiClient from './api'
import type { User } from '../types'

export interface LoginCredentials {
  email: string
  password: string
}

export interface RegisterData {
  email: string
  username: string
  password: string
  full_name: string
  phone_number?: string
  company_name?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in?: number
  user: User
}

export interface TwoFactorLoginResponse {
  requires_2fa: boolean
  temp_token?: string
  message?: string
  access_token?: string
  refresh_token?: string
  user?: User
}

export interface TwoFactorSetup {
  secret: string
  qr_code: string
  backup_codes: string[]
  message: string
}

class AuthService {
  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/register', data)
    return response.data
  }

  /**
   * Login user
   */
  async login(credentials: LoginCredentials): Promise<TwoFactorLoginResponse> {
    const response = await apiClient.post<TwoFactorLoginResponse>('/auth/login', credentials)
    return response.data
  }

  /**
   * Complete 2FA login
   */
  async verify2FALogin(tempToken: string, code: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/2fa/login', {
      temp_token: tempToken,
      code
    })
    return response.data
  }

  /**
   * Logout user
   */
  async logout(): Promise<void> {
    try {
      await apiClient.post('/auth/logout')
    } catch (error) {
      // Ignore logout errors
      console.error('Logout error:', error)
    } finally {
      // Always clear local storage
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken
    })
    return response.data
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get<User>('/auth/me')
    return response.data
  }

  /**
   * Enable 2FA
   */
  async enable2FA(password: string): Promise<TwoFactorSetup> {
    const response = await apiClient.post<TwoFactorSetup>('/auth/2fa/enable', {
      password
    })
    return response.data
  }

  /**
   * Verify and activate 2FA
   */
  async verify2FA(code: string): Promise<void> {
    await apiClient.post('/auth/2fa/verify', { code })
  }

  /**
   * Disable 2FA
   */
  async disable2FA(password: string, code: string): Promise<void> {
    await apiClient.post('/auth/2fa/disable', {
      password,
      code
    })
  }

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<{ message: string }> {
    const response = await apiClient.post<{ message: string }>('/auth/password/reset-request', {
      email
    })
    return response.data
  }

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/password/reset', {
      token,
      new_password: newPassword
    })
  }

  /**
   * Change password (authenticated)
   */
  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiClient.post('/auth/password/change', {
      current_password: currentPassword,
      new_password: newPassword
    })
  }

  /**
   * Verify email address
   */
  async verifyEmail(token: string): Promise<void> {
    await apiClient.post('/auth/email/verify', { token })
  }

  /**
   * Save authentication data to local storage
   */
  saveAuthData(authResponse: AuthResponse): void {
    localStorage.setItem('access_token', authResponse.access_token)
    localStorage.setItem('refresh_token', authResponse.refresh_token)
    localStorage.setItem('user', JSON.stringify(authResponse.user))
  }

  /**
   * Clear authentication data from local storage
   */
  clearAuthData(): void {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token')
  }

  /**
   * Get stored user
   */
  getStoredUser(): User | null {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  }
}

export default new AuthService()
