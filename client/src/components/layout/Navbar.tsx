import { Link } from 'react-router-dom'
import { Moon, Sun, Bell, User, LogOut } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { useState } from 'react'

export default function Navbar() {
  const { theme, toggleTheme } = useTheme()
  const { user, logout, isAuthenticated } = useAuth()
  const [showUserMenu, setShowUserMenu] = useState(false)

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center px-4">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-2">
          <div className="h-8 w-8 rounded-lg bg-primary flex items-center justify-center">
            <span className="text-white font-bold">API</span>
          </div>
          <span className="font-bold text-xl hidden sm:inline-block">RentAPI</span>
        </Link>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right side */}
        <div className="flex items-center space-x-4">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="rounded-full"
          >
            {theme === 'light' ? (
              <Moon className="h-5 w-5" />
            ) : (
              <Sun className="h-5 w-5" />
            )}
          </Button>

          {isAuthenticated ? (
            <>
              {/* Notifications */}
              <Button variant="ghost" size="icon" className="relative rounded-full">
                <Bell className="h-5 w-5" />
                <Badge className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center p-0 text-xs" variant="destructive">
                  3
                </Badge>
              </Button>

              {/* User menu */}
              <div className="relative">
                <Button
                  variant="ghost"
                  size="icon"
                  className="rounded-full"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                >
                  <User className="h-5 w-5" />
                </Button>

                {showUserMenu && (
                  <>
                    <div
                      className="fixed inset-0 z-40"
                      onClick={() => setShowUserMenu(false)}
                    />
                    <div className="absolute right-0 mt-2 w-48 rounded-md shadow-lg bg-popover border z-50">
                      <div className="py-1">
                        <div className="px-4 py-2 text-sm text-muted-foreground border-b">
                          <div className="font-medium text-foreground">{user?.name}</div>
                          <div className="text-xs">{user?.email}</div>
                        </div>
                        <Link
                          to={user?.role === 'admin' ? '/admin' : '/dashboard'}
                          className="block px-4 py-2 text-sm hover:bg-accent"
                          onClick={() => setShowUserMenu(false)}
                        >
                          Dashboard
                        </Link>
                        {user?.role === 'user' && (
                          <Link
                            to="/profile"
                            className="block px-4 py-2 text-sm hover:bg-accent"
                            onClick={() => setShowUserMenu(false)}
                          >
                            Profile
                          </Link>
                        )}
                        <button
                          className="flex w-full items-center px-4 py-2 text-sm hover:bg-accent text-destructive"
                          onClick={() => {
                            logout()
                            setShowUserMenu(false)
                          }}
                        >
                          <LogOut className="mr-2 h-4 w-4" />
                          Logout
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </>
          ) : (
            <>
              <Link to="/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link to="/register">
                <Button>Get Started</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
