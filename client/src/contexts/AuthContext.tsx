import React, { createContext, useContext, useState, useEffect } from 'react'
import type { User, RegisterData, TempTokenResponse } from '../types'
import { authService } from '../services/auth.service'
import { userService } from '../services/user.service'
import { apiService } from '../services/api'

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<void | TempTokenResponse>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  verify2FA: (tempToken: string, code: string) => Promise<void>
  refreshUser: () => Promise<void>
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)

  // Initialize - check if user is authenticated and fetch user data
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        if (apiService.isAuthenticated()) {
          // Fetch current user profile
          const userData = await userService.getCurrentUser()
          setUser(userData)
        }
      } catch (error) {
        console.error('Failed to initialize auth:', error)
        // Clear invalid tokens
        apiService.clearTokens()
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const login = async (email: string, password: string): Promise<void | TempTokenResponse> => {
    try {
      const response = await authService.login({ email, password })

      // Check if 2FA is required
      if ('requires_2fa' in response && response.requires_2fa) {
        return response as TempTokenResponse
      }

      // Login successful, set user
      setUser(response.user)
    } catch (error) {
      console.error('Login error:', error)
      throw error
    }
  }

  const verify2FA = async (tempToken: string, code: string): Promise<void> => {
    try {
      const response = await authService.verify2FA(tempToken, code)
      setUser(response.user)
    } catch (error) {
      console.error('2FA verification error:', error)
      throw error
    }
  }

  const register = async (data: RegisterData): Promise<void> => {
    try {
      const response = await authService.register(data)
      setUser(response.user)
    } catch (error) {
      console.error('Registration error:', error)
      throw error
    }
  }

  const logout = async (): Promise<void> => {
    try {
      await authService.logout()
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      setUser(null)
    }
  }

  const refreshUser = async (): Promise<void> => {
    try {
      const userData = await userService.getCurrentUser()
      setUser(userData)
    } catch (error) {
      console.error('Failed to refresh user:', error)
      throw error
    }
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login,
        register,
        logout,
        verify2FA,
        refreshUser,
        isAuthenticated: !!user,
        isAdmin: user?.role === 'admin',
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
