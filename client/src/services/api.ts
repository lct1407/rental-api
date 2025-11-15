/**
 * API Service - Handles all HTTP requests to the backend
 */

import { API_CONFIG } from '../config/api'
import type { ErrorResponse } from '../types'

/**
 * Custom API Error class
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string,
    public errorCode?: string,
    public field?: string,
    public errors?: Array<{ field: string; message: string; type: string }>
  ) {
    super(detail)
    this.name = 'ApiError'
  }
}

/**
 * Token management
 */
class TokenManager {
  private readonly ACCESS_TOKEN_KEY = 'access_token'
  private readonly REFRESH_TOKEN_KEY = 'refresh_token'

  getAccessToken(): string | null {
    return localStorage.getItem(this.ACCESS_TOKEN_KEY)
  }

  getRefreshToken(): string | null {
    return localStorage.getItem(this.REFRESH_TOKEN_KEY)
  }

  setTokens(accessToken: string, refreshToken: string): void {
    localStorage.setItem(this.ACCESS_TOKEN_KEY, accessToken)
    localStorage.setItem(this.REFRESH_TOKEN_KEY, refreshToken)
  }

  clearTokens(): void {
    localStorage.removeItem(this.ACCESS_TOKEN_KEY)
    localStorage.removeItem(this.REFRESH_TOKEN_KEY)
  }
}

const tokenManager = new TokenManager()

/**
 * Build full URL from endpoint
 */
function buildUrl(endpoint: string): string {
  const baseUrl = API_CONFIG.BASE_URL.replace(/\/$/, '')
  const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`
  return `${baseUrl}${path}`
}

/**
 * Build request headers
 */
function buildHeaders(includeAuth = true, customHeaders: HeadersInit = {}): HeadersInit {
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...customHeaders,
  }

  if (includeAuth) {
    const token = tokenManager.getAccessToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  return headers
}

/**
 * Handle API response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  const contentType = response.headers.get('content-type')
  const isJson = contentType?.includes('application/json')

  if (!response.ok) {
    if (isJson) {
      const error: ErrorResponse = await response.json()
      throw new ApiError(
        response.status,
        error.detail || 'An error occurred',
        error.error_code,
        error.field,
        error.errors
      )
    } else {
      throw new ApiError(response.status, `HTTP Error ${response.status}: ${response.statusText}`)
    }
  }

  if (isJson) {
    return response.json()
  }

  return response.text() as T
}

/**
 * Make HTTP request
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  includeAuth = true
): Promise<T> {
  const url = buildUrl(endpoint)
  const headers = buildHeaders(includeAuth, options.headers)

  const config: RequestInit = {
    ...options,
    headers,
  }

  try {
    const response = await fetch(url, config)
    return handleResponse<T>(response)
  } catch (error) {
    if (error instanceof ApiError) {
      // If unauthorized, try to refresh token
      if (error.status === 401 && includeAuth) {
        try {
          await refreshAccessToken()
          // Retry the original request
          const retryResponse = await fetch(url, {
            ...config,
            headers: buildHeaders(true, options.headers),
          })
          return handleResponse<T>(retryResponse)
        } catch (refreshError) {
          // Refresh failed, logout user
          tokenManager.clearTokens()
          window.location.href = '/login'
          throw refreshError
        }
      }
      throw error
    }

    // Network or other errors
    throw new ApiError(0, error instanceof Error ? error.message : 'Network error occurred')
  }
}

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken(): Promise<void> {
  const refreshToken = tokenManager.getRefreshToken()
  if (!refreshToken) {
    throw new ApiError(401, 'No refresh token available')
  }

  const response = await fetch(buildUrl('/api/v1/auth/refresh'), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!response.ok) {
    throw new ApiError(response.status, 'Failed to refresh token')
  }

  const data = await response.json()
  tokenManager.setTokens(data.access_token, data.refresh_token)
}

/**
 * API Service exports
 */
export const apiService = {
  /**
   * GET request
   */
  async get<T>(endpoint: string, includeAuth = true): Promise<T> {
    return request<T>(endpoint, { method: 'GET' }, includeAuth)
  },

  /**
   * POST request
   */
  async post<T>(endpoint: string, data?: unknown, includeAuth = true): Promise<T> {
    return request<T>(
      endpoint,
      {
        method: 'POST',
        body: data ? JSON.stringify(data) : undefined,
      },
      includeAuth
    )
  },

  /**
   * PUT request
   */
  async put<T>(endpoint: string, data?: unknown, includeAuth = true): Promise<T> {
    return request<T>(
      endpoint,
      {
        method: 'PUT',
        body: data ? JSON.stringify(data) : undefined,
      },
      includeAuth
    )
  },

  /**
   * PATCH request
   */
  async patch<T>(endpoint: string, data?: unknown, includeAuth = true): Promise<T> {
    return request<T>(
      endpoint,
      {
        method: 'PATCH',
        body: data ? JSON.stringify(data) : undefined,
      },
      includeAuth
    )
  },

  /**
   * DELETE request
   */
  async delete<T>(endpoint: string, includeAuth = true): Promise<T> {
    return request<T>(endpoint, { method: 'DELETE' }, includeAuth)
  },

  /**
   * Set authentication tokens
   */
  setTokens(accessToken: string, refreshToken: string): void {
    tokenManager.setTokens(accessToken, refreshToken)
  },

  /**
   * Clear authentication tokens
   */
  clearTokens(): void {
    tokenManager.clearTokens()
  },

  /**
   * Get access token
   */
  getAccessToken(): string | null {
    return tokenManager.getAccessToken()
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return !!tokenManager.getAccessToken()
  },
}
