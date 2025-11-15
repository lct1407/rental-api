/**
 * Authentication Service
 */

import { apiService } from './api'
import { API_ENDPOINTS } from '../config/api'
import type {
  TokenResponse,
  TempTokenResponse,
  LoginCredentials,
  RegisterData,
  UserResponse,
  PasswordChangeData,
  MessageResponse,
} from '../types'

export const authService = {
  /**
   * Register a new user
   */
  async register(data: RegisterData): Promise<TokenResponse> {
    const response = await apiService.post<TokenResponse>(API_ENDPOINTS.AUTH.REGISTER, data, false)

    // Store tokens
    apiService.setTokens(response.access_token, response.refresh_token)

    return response
  },

  /**
   * Login with email and password
   */
  async login(credentials: LoginCredentials): Promise<TokenResponse | TempTokenResponse> {
    const response = await apiService.post<TokenResponse | TempTokenResponse>(
      API_ENDPOINTS.AUTH.LOGIN,
      credentials,
      false
    )

    // Check if 2FA is required
    if ('requires_2fa' in response && response.requires_2fa) {
      return response as TempTokenResponse
    }

    // Store tokens
    const tokenResponse = response as TokenResponse
    apiService.setTokens(tokenResponse.access_token, tokenResponse.refresh_token)

    return tokenResponse
  },

  /**
   * Verify 2FA code and complete login
   */
  async verify2FA(tempToken: string, code: string): Promise<TokenResponse> {
    const response = await apiService.post<TokenResponse>(
      API_ENDPOINTS.AUTH.LOGIN_2FA,
      { temp_token: tempToken, code },
      false
    )

    // Store tokens
    apiService.setTokens(response.access_token, response.refresh_token)

    return response
  },

  /**
   * Logout
   */
  async logout(): Promise<void> {
    try {
      await apiService.post(API_ENDPOINTS.AUTH.LOGOUT, {})
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      // Clear tokens regardless of API response
      apiService.clearTokens()
    }
  },

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<UserResponse> {
    return apiService.get<UserResponse>(API_ENDPOINTS.AUTH.ME)
  },

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<TokenResponse> {
    const response = await apiService.post<TokenResponse>(
      API_ENDPOINTS.AUTH.REFRESH,
      { refresh_token: refreshToken },
      false
    )

    // Store new tokens
    apiService.setTokens(response.access_token, response.refresh_token)

    return response
  },

  /**
   * Change password
   */
  async changePassword(data: PasswordChangeData): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(API_ENDPOINTS.AUTH.CHANGE_PASSWORD, data)
  },

  /**
   * Request password reset
   */
  async requestPasswordReset(email: string): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(
      API_ENDPOINTS.AUTH.RESET_PASSWORD_REQUEST,
      { email },
      false
    )
  },

  /**
   * Reset password with token
   */
  async resetPassword(token: string, newPassword: string, confirmPassword: string): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(
      API_ENDPOINTS.AUTH.RESET_PASSWORD,
      { token, new_password: newPassword, confirm_password: confirmPassword },
      false
    )
  },

  /**
   * Verify email
   */
  async verifyEmail(token: string): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(
      API_ENDPOINTS.AUTH.VERIFY_EMAIL,
      { token },
      false
    )
  },

  /**
   * Enable 2FA
   */
  async enable2FA(password: string): Promise<{
    secret: string
    qr_code: string
    backup_codes: string[]
    message: string
  }> {
    return apiService.post(API_ENDPOINTS.AUTH.ENABLE_2FA, { password })
  },

  /**
   * Verify and activate 2FA
   */
  async verify2FASetup(code: string): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(API_ENDPOINTS.AUTH.VERIFY_2FA, { code })
  },

  /**
   * Disable 2FA
   */
  async disable2FA(password: string, code: string): Promise<MessageResponse> {
    return apiService.post<MessageResponse>(API_ENDPOINTS.AUTH.DISABLE_2FA, {
      password,
      code,
    })
  },
}
