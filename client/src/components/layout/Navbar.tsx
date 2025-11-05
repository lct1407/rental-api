import { Link } from 'react-router-dom'
import { Moon, Sun, Bell, User, LogOut, Settings } from 'lucide-react'
import { useTheme } from '../../contexts/ThemeContext'
import { useAuth } from '../../contexts/AuthContext'
import { Button } from '../ui/button'
import { Dropdown, DropdownItem, DropdownSeparator } from '../ui/dropdown'

export default function Navbar() {
  const { theme, toggleTheme } = useTheme()
  const { user, logout, isAuthenticated } = useAuth()

  return (
    <nav className="sticky top-0 z-50 w-full border-b bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/60">
      <div className="container mx-auto flex h-16 items-center px-4 lg:px-8 max-w-[1800px]">
        {/* Logo */}
        <Link to="/" className="flex items-center space-x-3 mr-6">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-lg">
            <span className="text-white font-bold text-sm">AR</span>
          </div>
          <span className="font-bold text-xl hidden sm:inline-block bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
            RentAPI
          </span>
        </Link>

        {/* Spacer */}
        <div className="flex-1" />

        {/* Right side */}
        <div className="flex items-center space-x-2">
          {/* Theme toggle */}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleTheme}
            className="rounded-lg hover:bg-accent"
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
              <Dropdown
                align="right"
                trigger={
                  <Button variant="ghost" size="icon" className="relative rounded-lg hover:bg-accent">
                    <Bell className="h-5 w-5" />
                    <span className="absolute -top-1 -right-1 h-5 w-5 flex items-center justify-center rounded-full bg-destructive text-[10px] text-white font-bold">
                      3
                    </span>
                  </Button>
                }
              >
                <div className="w-80 max-h-96 overflow-y-auto">
                  <div className="p-4 border-b">
                    <h3 className="font-semibold">Notifications</h3>
                    <p className="text-xs text-muted-foreground mt-1">You have 3 unread messages</p>
                  </div>
                  <div className="p-2 space-y-1">
                    <button className="w-full p-3 text-left hover:bg-accent rounded-md transition-colors">
                      <p className="text-sm font-medium">New user registered</p>
                      <p className="text-xs text-muted-foreground mt-1">John Doe just signed up for Pro plan</p>
                      <p className="text-xs text-muted-foreground mt-1">2 hours ago</p>
                    </button>
                    <button className="w-full p-3 text-left hover:bg-accent rounded-md transition-colors">
                      <p className="text-sm font-medium">API limit warning</p>
                      <p className="text-xs text-muted-foreground mt-1">User approaching API call limit</p>
                      <p className="text-xs text-muted-foreground mt-1">5 hours ago</p>
                    </button>
                    <button className="w-full p-3 text-left hover:bg-accent rounded-md transition-colors">
                      <p className="text-sm font-medium">Payment received</p>
                      <p className="text-xs text-muted-foreground mt-1">$49.99 received from subscription</p>
                      <p className="text-xs text-muted-foreground mt-1">1 day ago</p>
                    </button>
                  </div>
                  <div className="p-3 border-t">
                    <button className="text-sm text-primary hover:underline">View all notifications</button>
                  </div>
                </div>
              </Dropdown>

              {/* User menu */}
              <Dropdown
                align="right"
                trigger={
                  <button className="flex items-center gap-2 px-2 py-1.5 rounded-lg hover:bg-accent transition-colors">
                    <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center text-white font-semibold text-sm">
                      {user?.name.split(' ').map(n => n[0]).join('').toUpperCase()}
                    </div>
                    <div className="hidden md:block text-left">
                      <p className="text-sm font-medium">{user?.name}</p>
                      <p className="text-xs text-muted-foreground capitalize">{user?.role}</p>
                    </div>
                  </button>
                }
              >
                <div className="py-2 min-w-[200px]">
                  <div className="px-4 py-3 border-b">
                    <p className="text-sm font-medium">{user?.name}</p>
                    <p className="text-xs text-muted-foreground">{user?.email}</p>
                  </div>
                  <div className="py-1">
                    <Link to={user?.role === 'admin' ? '/admin' : '/dashboard'}>
                      <DropdownItem icon={<User className="h-4 w-4" />}>
                        My Dashboard
                      </DropdownItem>
                    </Link>
                    {user?.role === 'user' && (
                      <Link to="/profile">
                        <DropdownItem icon={<Settings className="h-4 w-4" />}>
                          Profile Settings
                        </DropdownItem>
                      </Link>
                    )}
                    <DropdownSeparator />
                    <DropdownItem
                      icon={<LogOut className="h-4 w-4" />}
                      onClick={logout}
                      destructive
                    >
                      Logout
                    </DropdownItem>
                  </div>
                </div>
              </Dropdown>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login">
                <Button variant="ghost">Login</Button>
              </Link>
              <Link to="/register">
                <Button>Get Started</Button>
              </Link>
            </div>
          )}
        </div>
      </div>
    </nav>
  )
}
