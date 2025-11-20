/**
 * API Client Configuration
 *
 * Axios-based HTTP client for communicating with FastAPI backend
 */
import axios from 'axios'
import type { AxiosError, AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios'

// API Base URL - can be configured via environment variable
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds
})

// Request interceptor - Add auth token to requests
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get access token from localStorage
    const token = localStorage.getItem('access_token')

    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor - Handle errors and token refresh
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    // If 401 and not already retried, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        const refreshToken = localStorage.getItem('refresh_token')

        if (refreshToken) {
          // Try to refresh the access token
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken
          })

          const { access_token } = response.data

          // Store new access token
          localStorage.setItem('access_token', access_token)

          // Retry the original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }

          return apiClient(originalRequest)
        }
      } catch (refreshError) {
        // Refresh failed - redirect to login
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

/**
 * API Error type for consistent error handling
 */
export interface ApiError {
  message: string
  status?: number
  errors?: Array<{
    field: string
    message: string
  }>
}

/**
 * Extract error message from API response
 */
export const getErrorMessage = (error: unknown): string => {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{
      detail?: string | { msg: string }[]
      message?: string
      errors?: Array<{ field: string; message: string }>
    }>

    if (axiosError.response?.data) {
      const data = axiosError.response.data

      // Handle FastAPI validation errors
      if (Array.isArray(data.detail)) {
        return data.detail.map((err) => err.msg).join(', ')
      }

      // Handle string detail
      if (typeof data.detail === 'string') {
        return data.detail
      }

      // Handle custom error format
      if (data.message) {
        return data.message
      }

      // Handle field errors
      if (data.errors && data.errors.length > 0) {
        return data.errors.map((err) => `${err.field}: ${err.message}`).join(', ')
      }
    }

    return axiosError.message
  }

  if (error instanceof Error) {
    return error.message
  }

  return 'An unknown error occurred'
}

export default apiClient
