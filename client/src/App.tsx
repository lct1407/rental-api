import { lazy, Suspense, memo } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import { ThemeProvider } from './contexts/ThemeContext'

// Lazy load all page components
const LandingPage = lazy(() => import('./pages/public/LandingPage'))
const LoginPage = lazy(() => import('./pages/public/LoginPage'))
const RegisterPage = lazy(() => import('./pages/public/RegisterPage'))

const AdminDashboard = lazy(() => import('./pages/admin/AdminDashboard'))
const UserManagement = lazy(() => import('./pages/admin/UserManagement'))
const UserDetail = lazy(() => import('./pages/admin/UserDetail'))

const UserDashboard = lazy(() => import('./pages/user/UserDashboard'))
const UserProfile = lazy(() => import('./pages/user/UserProfile'))

// Loading fallback component
const LoadingFallback = memo(function LoadingFallback() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 dark:border-gray-100"></div>
    </div>
  )
})

const ProtectedRoute = memo(function ProtectedRoute({ children, requireAdmin = false }: { children: React.ReactNode; requireAdmin?: boolean }) {
  const { isAuthenticated, isAdmin } = useAuth()

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (requireAdmin && !isAdmin) {
    return <Navigate to="/dashboard" replace />
  }

  return <>{children}</>
})

function AppRoutes() {
  const { isAuthenticated, isAdmin } = useAuth()

  return (
    <Suspense fallback={<LoadingFallback />}>
      <Routes>
        {/* Public routes */}
        <Route path="/" element={<LandingPage />} />
        <Route
          path="/login"
          element={isAuthenticated ? <Navigate to={isAdmin ? "/admin" : "/dashboard"} replace /> : <LoginPage />}
        />
        <Route
          path="/register"
          element={isAuthenticated ? <Navigate to="/dashboard" replace /> : <RegisterPage />}
        />

        {/* Admin routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute requireAdmin>
              <AdminDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users"
          element={
            <ProtectedRoute requireAdmin>
              <UserManagement />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/users/:id"
          element={
            <ProtectedRoute requireAdmin>
              <UserDetail />
            </ProtectedRoute>
          }
        />

        {/* User routes */}
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <UserDashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <UserProfile />
            </ProtectedRoute>
          }
        />

        {/* Catch all */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  )
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  )
}

export default App
