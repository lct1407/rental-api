import { useState, useEffect } from 'react'
import MainLayout from '../../components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Activity, CreditCard, TrendingUp, Calendar, Copy, ArrowUpRight, Loader2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { formatNumber, formatDate } from '../../lib/utils'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Link } from 'react-router-dom'
import analyticsService from '../../services/analyticsService'
import apiKeyService from '../../services/apiKeyService'
import subscriptionService from '../../services/subscriptionService'
import type { DashboardStats, ApiCallAnalytics } from '../../services/analyticsService'
import type { ApiKey } from '../../types'

export default function UserDashboard() {
  const { user } = useAuth()
  const [loading, setLoading] = useState(true)
  const [dashboardStats, setDashboardStats] = useState<DashboardStats | null>(null)
  const [analytics, setAnalytics] = useState<ApiCallAnalytics | null>(null)
  const [apiKeys, setApiKeys] = useState<ApiKey[]>([])
  const [subscription, setSubscription] = useState<any>(null)

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true)
        const [stats, analyticsData, keysData, subData] = await Promise.all([
          analyticsService.getDashboardStats(),
          analyticsService.getApiCallAnalytics({ start_date: getSevenDaysAgo() }),
          apiKeyService.listKeys({ limit: 1 }),
          subscriptionService.getCurrentSubscription().catch(() => null),
        ])
        setDashboardStats(stats)
        setAnalytics(analyticsData)
        setApiKeys(keysData.items)
        setSubscription(subData)
      } catch (error) {
        console.error('Failed to fetch dashboard data:', error)
      } finally {
        setLoading(false)
      }
    }

    if (user) {
      fetchDashboardData()
    }
  }, [user])

  const getSevenDaysAgo = () => {
    const date = new Date()
    date.setDate(date.getDate() - 7)
    return date.toISOString()
  }

  const copyApiKey = (key: string) => {
    navigator.clipboard.writeText(key)
  }

  // Transform analytics data for chart
  const usageData = analytics?.calls_by_day.map(day => ({
    day: new Date(day.date).toLocaleDateString('en-US', { weekday: 'short' }),
    calls: day.total,
  })) || []

  const usagePercentage = dashboardStats
    ? ((dashboardStats.credits_used_this_month / (user?.credits || 1)) * 100)
    : 0

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <Loader2 className="h-8 w-8 animate-spin text-primary" />
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, {user?.full_name || user?.username}!</h1>
          <p className="text-muted-foreground">
            Here's what's happening with your API usage
          </p>
        </div>

        {/* Overview Cards */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Current Plan</CardTitle>
              <CreditCard className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {user?.plan.charAt(0).toUpperCase()}{user?.plan.slice(1)}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {currentPlan?.credits.toLocaleString()} calls/month
              </p>
              <Link to="/profile">
                <Button variant="link" className="px-0 mt-2">
                  Upgrade plan
                  <ArrowUpRight className="ml-1 h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">API Calls</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(dashboardStats?.api_calls_this_month || 0)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <span className="text-muted-foreground">{formatNumber(dashboardStats?.api_calls_today || 0)} today</span>
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Credits Remaining</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formatNumber(user?.credits || 0)}</div>
              <div className="mt-2">
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary h-2 rounded-full transition-all"
                    style={{ width: `${Math.min(100 - usagePercentage, 100)}%` }}
                  />
                </div>
                <p className="text-xs text-muted-foreground mt-1">
                  {usagePercentage.toFixed(1)}% used this month
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Next Renewal</CardTitle>
              <Calendar className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {subscription?.current_period_end ? new Date(subscription.current_period_end).getDate() : '-'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {subscription?.current_period_end ? formatDate(subscription.current_period_end) : 'No active subscription'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* API Key Card */}
        {apiKeys.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Your API Key</CardTitle>
              <CardDescription>Use this key to authenticate your API requests</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
                <code className="flex-1 p-3 bg-muted rounded-md text-sm font-mono">
                  {apiKeys[0].key_prefix}••••{apiKeys[0].last_four}
                </code>
                <Button variant="outline" size="icon" onClick={() => copyApiKey(`${apiKeys[0].key_prefix}${apiKeys[0].last_four}`)}>
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Keep your API key secure. Do not share it publicly.
              </p>
              <Link to="/api-keys">
                <Button variant="link" className="px-0 mt-2">
                  Manage API Keys
                  <ArrowUpRight className="ml-1 h-3 w-3" />
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Usage Chart */}
        <Card>
          <CardHeader>
            <CardTitle>API Usage This Week</CardTitle>
            <CardDescription>Daily API call statistics</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={usageData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="day" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="calls" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Recent API Calls */}
        <Card>
          <CardHeader>
            <CardTitle>API Call Statistics</CardTitle>
            <CardDescription>Overview of your API usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <div className="text-sm text-muted-foreground">Total Calls</div>
                <div className="text-2xl font-bold">{formatNumber(analytics?.total_calls || 0)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Successful</div>
                <div className="text-2xl font-bold text-green-500">{formatNumber(analytics?.successful_calls || 0)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Failed</div>
                <div className="text-2xl font-bold text-red-500">{formatNumber(analytics?.failed_calls || 0)}</div>
              </div>
              <div>
                <div className="text-sm text-muted-foreground">Avg Response</div>
                <div className="text-2xl font-bold">{analytics?.avg_response_time || 0}ms</div>
              </div>
            </div>

            {analytics && analytics.calls_by_endpoint && analytics.calls_by_endpoint.length > 0 && (
              <div className="mt-6">
                <h4 className="text-sm font-medium mb-3">Top Endpoints</h4>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Endpoint</TableHead>
                      <TableHead>Calls</TableHead>
                      <TableHead>Avg Response</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {analytics.calls_by_endpoint.slice(0, 5).map((endpoint, idx) => (
                      <TableRow key={idx}>
                        <TableCell className="font-mono text-xs">{endpoint.endpoint}</TableCell>
                        <TableCell>{formatNumber(endpoint.count)}</TableCell>
                        <TableCell className="text-muted-foreground">{endpoint.avg_response_time}ms</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
