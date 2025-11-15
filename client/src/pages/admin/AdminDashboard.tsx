import { useState, useEffect } from 'react'
import MainLayout from '../../components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Users, Activity, AlertCircle, DollarSign, TrendingUp, TrendingDown, Loader2 } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { formatCurrency, formatNumber } from '../../lib/utils'
import analyticsService from '../../services/analyticsService'
import userService from '../../services/userService'
import type { AdminDashboardStats } from '../../services/analyticsService'

export default function AdminDashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState<AdminDashboardStats | null>(null)
  const [apiStats, setApiStats] = useState<any>(null)

  useEffect(() => {
    const fetchAdminData = async () => {
      try {
        setLoading(true)
        const [dashboardStats, platformStats] = await Promise.all([
          analyticsService.getAdminDashboardStats(),
          analyticsService.getPlatformApiStats(),
        ])
        setStats(dashboardStats)
        setApiStats(platformStats)
      } catch (error) {
        console.error('Failed to fetch admin dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchAdminData()
  }, [])

  if (loading) {
    return (
      <MainLayout isAdmin>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </MainLayout>
    )
  }

  const statusData = [
    { name: 'Active', value: stats?.active_users || 0, color: '#3b82f6' },
    { name: 'New Today', value: stats?.new_users_today || 0, color: '#10b981' },
  ]

  // Transform user growth data for chart
  const chartData = stats?.user_growth.slice(-30).map(item => ({
    name: new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    users: item.new_users,
  })) || []

  return (
    <MainLayout isAdmin>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your API platform performance
          </p>
        </div>

        {/* KPI Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Users</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(stats?.total_users || 0)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">+{stats?.new_users_today || 0}</span> today
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Calls</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(apiStats?.total_calls || 0)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <span className="text-muted-foreground">
                  {formatNumber(apiStats?.successful_calls || 0)} successful
                </span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Response Time</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{apiStats?.avg_response_time || 0}ms</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <span className="text-muted-foreground">
                  Platform average
                </span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Revenue (MRR)</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(stats?.revenue_this_month || 0)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <span className="text-muted-foreground">
                  {formatCurrency(stats?.revenue_today || 0)} today
                </span>
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid gap-4 md:grid-cols-7">
          {/* API Calls Over Time */}
          <Card className="md:col-span-4">
            <CardHeader>
              <CardTitle>New Users Over Time</CardTitle>
              <CardDescription>Daily user registration statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="users" stroke="#3b82f6" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* User Status Distribution */}
          <Card className="md:col-span-3">
            <CardHeader>
              <CardTitle>User Status</CardTitle>
              <CardDescription>Distribution of user account statuses</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={statusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name}: ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {statusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Top Users */}
        <Card>
          <CardHeader>
            <CardTitle>Top API Users</CardTitle>
            <CardDescription>Users with the most API calls</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {apiStats?.top_users?.slice(0, 5).map((user: any, idx: number) => (
                <div key={idx} className="flex items-center justify-between border-b pb-3">
                  <div className="space-y-1">
                    <p className="text-sm font-medium">
                      {user.user_email}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      User ID: {user.user_id}
                    </p>
                  </div>
                  <div className="flex items-center gap-4">
                    <span className="text-sm font-medium">
                      {formatNumber(user.total_calls)} calls
                    </span>
                  </div>
                </div>
              ))}
              {(!apiStats?.top_users || apiStats.top_users.length === 0) && (
                <div className="text-center py-8 text-muted-foreground">
                  No API activity yet
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
