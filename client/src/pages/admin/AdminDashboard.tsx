import { useMemo } from 'react'
import MainLayout from '../../components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Users, Activity, AlertCircle, DollarSign, TrendingUp, TrendingDown } from 'lucide-react'
import { mockKPIData, mockChartData, mockUsers, mockApiCalls } from '../../data/mockData'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { formatCurrency, formatNumber } from '../../lib/utils'

export default function AdminDashboard() {
  const kpi = mockKPIData[0]

  // Memoize expensive computations
  const statusData = useMemo(() => [
    { name: 'Active', value: mockUsers.filter(u => u.status === 'active').length, color: '#3b82f6' },
    { name: 'Suspended', value: mockUsers.filter(u => u.status === 'suspended').length, color: '#ef4444' },
    { name: 'Inactive', value: mockUsers.filter(u => u.status === 'inactive').length, color: '#6b7280' },
  ], [])

  const recentActivity = useMemo(() => mockApiCalls.slice(0, 5), [])

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
              <div className="text-2xl font-bold">{formatNumber(kpi.totalUsers)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">+{kpi.change}%</span> from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Calls</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(kpi.totalApiCalls)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">+18.2%</span> from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Error Rate</CardTitle>
              <AlertCircle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpi.errorRate}%</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingDown className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">-0.5%</span> from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Revenue (MRR)</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatCurrency(kpi.revenue)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">+{kpi.change}%</span> from last month
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts */}
        <div className="grid gap-4 md:grid-cols-7">
          {/* API Calls Over Time */}
          <Card className="md:col-span-4">
            <CardHeader>
              <CardTitle>API Calls Over Time</CardTitle>
              <CardDescription>Monthly API call statistics</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={mockChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Line type="monotone" dataKey="calls" stroke="#3b82f6" strokeWidth={2} />
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

        {/* Recent Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent API Activity</CardTitle>
            <CardDescription>Latest API calls across all users</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {recentActivity.map((call) => {
                const user = mockUsers.find(u => u.id === call.userId)
                return (
                  <div key={call.id} className="flex items-center justify-between border-b pb-3">
                    <div className="space-y-1">
                      <p className="text-sm font-medium">
                        {call.method} {call.endpoint}
                      </p>
                      <p className="text-xs text-muted-foreground">
                        {user?.name} • {new Date(call.timestamp).toLocaleString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className={`text-xs px-2 py-1 rounded ${
                        call.status === 200 ? 'bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300' :
                        'bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300'
                      }`}>
                        {call.status}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {call.responseTime}ms
                      </span>
                    </div>
                  </div>
                )
              })}
            </div>
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
