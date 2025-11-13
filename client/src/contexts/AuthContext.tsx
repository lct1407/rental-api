import React, { createContext, useContext, useState, useEffect } from 'react'
import type { User, UserRole } from '../types'
import { generateApiKey } from '../lib/utils'

interface AuthContextType {
  user: User | null
  login: (email: string, password: string, role: UserRole) => Promise<void>
  register: (name: string, email: string, password: string) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
  isAdmin: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(() => {
    const stored = localStorage.getItem('user')
    return stored ? JSON.parse(stored) : null
  })

  useEffect(() => {
    if (user) {
      localStorage.setItem('user', JSON.stringify(user))
    } else {
      localStorage.removeItem('user')
    }
  }, [user])

  const login = async (email: string, _password: string, role: UserRole) => {
    // Mock login - in production, this would call an API
    const mockUser: User = {
      id: '1',
      name: role === 'admin' ? 'Admin User' : 'John Doe',
      email,
      role,
      plan: 'pro',
      credits: 10000,
      apiKey: generateApiKey(),
      status: 'active',
      registrationDate: new Date().toISOString(),
      nextRenewalDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      billingCycle: 'monthly',
    }
    setUser(mockUser)
  }

  const register = async (name: string, email: string, _password: string) => {
    // Mock registration - in production, this would call an API
    const newUser: User = {
      id: Math.random().toString(36).substring(2, 11),
      name,
      email,
      role: 'user',
      plan: 'free',
      credits: 1000,
      apiKey: generateApiKey(),
      status: 'active',
      registrationDate: new Date().toISOString(),
      billingCycle: 'monthly',
    }
    setUser(newUser)
  }

  const logout = () => {
    setUser(null)
  }

  return (
    <AuthContext.Provider
      value={{
        user,
        login,
        register,
        logout,
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
