import React, { createContext, useContext, useState, useEffect } from 'react'
import type { User } from '../types'
import authService, { type RegisterData, type LoginCredentials } from '../services/authService'
import { getErrorMessage } from '../services/api'

interface AuthContextType {
  user: User | null
  login: (email: string, password: string) => Promise<void>
  register: (data: Omit<RegisterData, 'username'> & { name: string }) => Promise<void>
  logout: () => Promise<void>
  isAuthenticated: boolean
  isAdmin: boolean
  loading: boolean
  error: string | null
  clearError: () => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    return authService.getStoredUser()
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load user on mount if token exists
  useEffect(() => {
    const loadUser = async () => {
      if (authService.isAuthenticated() && !user) {
        try {
          const currentUser = await authService.getCurrentUser()
          setUser(currentUser)
          localStorage.setItem('user', JSON.stringify(currentUser))
        } catch (err) {
          console.error('Failed to load user:', err)
          authService.clearAuthData()
        }
      }
    }

    loadUser()
  }, [])

  const login = async (email: string, password: string) => {
    setLoading(true)
    setError(null)

    try {
      const credentials: LoginCredentials = { email, password }
      const response = await authService.login(credentials)

      // Check if 2FA is required
      if (response.requires_2fa && response.temp_token) {
        // Store temp token for 2FA verification
        // In a real app, you'd navigate to a 2FA page here
        // For now, we'll throw an error indicating 2FA is required
        throw new Error('Two-factor authentication required. Please implement 2FA flow.')
      }

      // No 2FA required - save auth data
      if (response.access_token && response.refresh_token && response.user) {
        authService.saveAuthData({
          access_token: response.access_token,
          refresh_token: response.refresh_token,
          token_type: 'bearer',
          user: response.user
        })

        setUser(response.user)
      }
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const register = async (data: Omit<RegisterData, 'username'> & { name: string }) => {
    setLoading(true)
    setError(null)

    try {
      // Generate username from name (lowercase, no spaces)
      const username = data.name.toLowerCase().replace(/\s+/g, '')

      const registerData: RegisterData = {
        email: data.email,
        username,
        password: data.password,
        full_name: data.name,
        company_name: data.company_name,
        phone_number: data.phone_number
      }

      const response = await authService.register(registerData)

      // Save auth data and user
      authService.saveAuthData(response)
      setUser(response.user)
    } catch (err) {
      const errorMessage = getErrorMessage(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    setLoading(true)
    setError(null)

    try {
      await authService.logout()
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      setUser(null)
      authService.clearAuthData()
      setLoading(false)
    }
  }

  const clearError = () => {
    setError(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin' || user?.role === 'super_admin',
        loading,
        error,
        clearError
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
