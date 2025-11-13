import { useMemo } from 'react'
import MainLayout from '../../components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { Activity, CreditCard, TrendingUp, Calendar, Copy, ArrowUpRight } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { mockApiCalls, pricingPlans } from '../../data/mockData'
import { formatNumber, formatDate } from '../../lib/utils'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Link } from 'react-router-dom'

export default function UserDashboard() {
  const { user } = useAuth()
  
  const userApiCalls = useMemo(() => 
    mockApiCalls.filter(call => call.userId === user?.id),
    [user?.id]
  )
  
  const currentPlan = useMemo(() => 
    pricingPlans.find(p => p.id === user?.plan),
    [user?.plan]
  )

  // Mock usage data for the chart
  const usageData = useMemo(() => [
    { day: 'Mon', calls: 120 },
    { day: 'Tue', calls: 180 },
    { day: 'Wed', calls: 150 },
    { day: 'Thu', calls: 220 },
    { day: 'Fri', calls: 190 },
    { day: 'Sat', calls: 90 },
    { day: 'Sun', calls: 70 },
  ], [])

  const totalCallsThisMonth = useMemo(() => 
    usageData.reduce((sum, day) => sum + day.calls, 0),
    [usageData]
  )
  
  const creditsUsed = useMemo(() => 
    userApiCalls.reduce((sum, call) => sum + call.credits, 0),
    [userApiCalls]
  )
  
  const usagePercentage = currentPlan ? (creditsUsed / currentPlan.credits) * 100 : 0

  const copyApiKey = () => {
    if (user?.apiKey) {
      navigator.clipboard.writeText(user.apiKey)
    }
  }

  return (
    <MainLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Welcome back, {user?.name}!</h1>
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
              <div className="text-2xl font-bold">{formatNumber(totalCallsThisMonth)}</div>
              <p className="text-xs text-muted-foreground flex items-center mt-1">
                <TrendingUp className="h-3 w-3 text-green-500 mr-1" />
                <span className="text-green-500">+12%</span> from last week
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
                {user?.nextRenewalDate ? new Date(user.nextRenewalDate).getDate() : '-'}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                {user?.nextRenewalDate ? formatDate(user.nextRenewalDate) : 'No active subscription'}
              </p>
            </CardContent>
          </Card>
        </div>

        {/* API Key Card */}
        <Card>
          <CardHeader>
            <CardTitle>Your API Key</CardTitle>
            <CardDescription>Use this key to authenticate your API requests</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-2">
              <code className="flex-1 p-3 bg-muted rounded-md text-sm font-mono">
                {user?.apiKey}
              </code>
              <Button variant="outline" size="icon" onClick={copyApiKey}>
                <Copy className="h-4 w-4" />
              </Button>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Keep your API key secure. Do not share it publicly.
            </p>
          </CardContent>
        </Card>

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
            <CardTitle>Recent API Calls</CardTitle>
            <CardDescription>Your latest API requests</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Timestamp</TableHead>
                  <TableHead>Endpoint</TableHead>
                  <TableHead>Method</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Response Time</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {userApiCalls.slice(0, 5).map((call) => (
                  <TableRow key={call.id}>
                    <TableCell className="text-xs text-muted-foreground">
                      {new Date(call.timestamp).toLocaleString()}
                    </TableCell>
                    <TableCell className="font-mono text-xs">{call.endpoint}</TableCell>
                    <TableCell>
                      <Badge variant="outline" className="text-xs">
                        {call.method}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <Badge variant={call.status === 200 ? 'success' : 'destructive'}>
                        {call.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-muted-foreground">{call.responseTime}ms</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>

            {userApiCalls.length === 0 && (
              <div className="text-center py-12">
                <p className="text-muted-foreground">No API calls yet</p>
                <Button variant="outline" className="mt-4">
                  View Documentation
                </Button>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </MainLayout>
  )
}
