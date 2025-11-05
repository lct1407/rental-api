import { Link, useLocation } from 'react-router-dom'
import { cn } from '../../lib/utils'
import {
  LayoutDashboard,
  Users,
  CreditCard,
  Settings,
  Key,
  BarChart3,
  Mail,
  MessageSquare,
  Calendar,
  KanbanSquare,
  FileText,
  User,
  HelpCircle,
  BookOpen,
  DollarSign,
  FileCode,
  Map,
  PieChart,
  ChevronDown,
  ChevronRight,
} from 'lucide-react'
import { useState } from 'react'

interface SidebarProps {
  isAdmin?: boolean
}

interface MenuItem {
  to?: string
  label: string
  icon: any
  badge?: string
  children?: MenuItem[]
}

export default function Sidebar({ isAdmin = false }: SidebarProps) {
  const location = useLocation()
  const [openMenus, setOpenMenus] = useState<string[]>(['Dashboard'])

  const toggleMenu = (label: string) => {
    setOpenMenus(prev =>
      prev.includes(label)
        ? prev.filter(item => item !== label)
        : [...prev, label]
    )
  }

  const adminMenus: MenuItem[] = [
    {
      label: 'Dashboard',
      icon: LayoutDashboard,
      children: [
        { to: '/admin', label: 'Analytics', icon: BarChart3 },
        { to: '/admin/ecommerce', label: 'eCommerce', icon: DollarSign },
      ],
    },
    {
      label: 'Apps',
      icon: LayoutDashboard,
      children: [
        { to: '/admin/email', label: 'Email', icon: Mail },
        { to: '/admin/chat', label: 'Chat', icon: MessageSquare, badge: '3' },
        { to: '/admin/calendar', label: 'Calendar', icon: Calendar },
        { to: '/admin/kanban', label: 'Kanban', icon: KanbanSquare },
      ],
    },
    {
      label: 'Users',
      icon: Users,
      children: [
        { to: '/admin/users', label: 'List', icon: Users },
        { to: '/admin/users/view', label: 'View', icon: User },
      ],
    },
    {
      label: 'Pages',
      icon: FileText,
      children: [
        { to: '/profile', label: 'Profile', icon: User },
        { to: '/faq', label: 'FAQ', icon: HelpCircle },
        { to: '/knowledge-base', label: 'Knowledge Base', icon: BookOpen },
        { to: '/account-settings', label: 'Account Settings', icon: Settings },
      ],
    },
    {
      label: 'Charts',
      icon: PieChart,
      children: [
        { to: '/admin/charts/apex', label: 'Apex Charts', icon: BarChart3 },
        { to: '/admin/charts/chartjs', label: 'ChartJS', icon: PieChart },
      ],
    },
  ]

  const userMenus: MenuItem[] = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/profile', label: 'Profile', icon: Settings },
    { to: '/api-keys', label: 'API Keys', icon: Key },
    { to: '/billing', label: 'Billing', icon: CreditCard },
    { to: '/docs', label: 'Documentation', icon: BookOpen },
  ]

  const menus = isAdmin ? adminMenus : userMenus

  const renderMenuItem = (item: MenuItem, depth = 0) => {
    const Icon = item.icon
    const hasChildren = item.children && item.children.length > 0
    const isOpen = openMenus.includes(item.label)
    const isActive = item.to && location.pathname === item.to

    if (hasChildren) {
      return (
        <div key={item.label} className="space-y-1">
          <button
            onClick={() => toggleMenu(item.label)}
            className={cn(
              'w-full group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors',
              'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
            )}
          >
            <div className="flex items-center">
              <Icon className="mr-3 h-5 w-5 flex-shrink-0" />
              <span>{item.label}</span>
            </div>
            {isOpen ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          {isOpen && (
            <div className="ml-4 space-y-1 border-l-2 border-border pl-2">
              {item.children.map(child => renderMenuItem(child, depth + 1))}
            </div>
          )}
        </div>
      )
    }

    return (
      <Link
        key={item.to}
        to={item.to || '#'}
        className={cn(
          'group flex items-center justify-between px-3 py-2 text-sm font-medium rounded-lg transition-colors',
          isActive
            ? 'bg-primary text-primary-foreground shadow-sm'
            : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
        )}
      >
        <div className="flex items-center">
          <Icon
            className={cn(
              'mr-3 h-5 w-5 flex-shrink-0',
              isActive ? 'text-primary-foreground' : ''
            )}
          />
          <span>{item.label}</span>
        </div>
        {item.badge && (
          <span className="ml-auto inline-flex items-center justify-center px-2 py-0.5 text-xs font-bold leading-none text-white bg-destructive rounded-full">
            {item.badge}
          </span>
        )}
      </Link>
    )
  }

  return (
    <aside className="hidden md:flex md:w-64 md:flex-col border-r bg-card">
      <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
        <nav className="mt-5 flex-1 px-3 space-y-2">
          {menus.map(item => renderMenuItem(item))}
        </nav>

        {/* Footer */}
        <div className="px-3 py-4 border-t mt-auto">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-primary/10">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-semibold text-sm">
                {isAdmin ? 'A' : 'U'}
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">
                {isAdmin ? 'Admin' : 'User'} Mode
              </p>
              <p className="text-xs text-muted-foreground truncate">
                {isAdmin ? 'Full Access' : 'Standard Access'}
              </p>
            </div>
          </div>
        </div>
      </div>
    </aside>
  )
}
