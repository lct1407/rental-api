import { useParams, Link } from 'react-router-dom'
import MainLayout from '../../components/layout/MainLayout'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card'
import { Input } from '../../components/ui/input'
import { Button } from '../../components/ui/button'
import { Badge } from '../../components/ui/badge'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '../../components/ui/table'
import { ArrowLeft, Copy, RefreshCw, Save, Ban, Trash2 } from 'lucide-react'
import { mockUsers, mockApiCalls } from '../../data/mockData'
import { formatDate, formatNumber } from '../../lib/utils'
import { useState } from 'react'

export default function UserDetail() {
  const { id } = useParams()
  const user = mockUsers.find(u => u.id === id)
  const userApiCalls = mockApiCalls.filter(call => call.userId === id)

  const [credits, setCredits] = useState(user?.credits || 0)
  const [status, setStatus] = useState(user?.status || 'active')

  if (!user) {
    return (
      <MainLayout isAdmin>
        <div className="text-center py-12">
          <h2 className="text-2xl font-bold">User not found</h2>
          <Link to="/admin/users">
            <Button className="mt-4" variant="outline">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Users
            </Button>
          </Link>
        </div>
      </MainLayout>
    )
  }

  const copyApiKey = () => {
    navigator.clipboard.writeText(user.apiKey)
  }

  return (
    <MainLayout isAdmin>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link to="/admin/users">
              <Button variant="ghost" size="icon">
                <ArrowLeft className="h-4 w-4" />
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{user.name}</h1>
              <p className="text-muted-foreground">{user.email}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="destructive">
              <Ban className="mr-2 h-4 w-4" />
              Suspend Account
            </Button>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Personal Information */}
          <Card>
            <CardHeader>
              <CardTitle>Personal Information</CardTitle>
              <CardDescription>User account details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Full Name</label>
                <Input defaultValue={user.name} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Email</label>
                <Input defaultValue={user.email} type="email" />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Phone</label>
                <Input defaultValue={user.phone || 'Not provided'} />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Registration Date</label>
                <Input value={formatDate(user.registrationDate)} disabled />
              </div>
            </CardContent>
          </Card>

          {/* API Credentials */}
          <Card>
            <CardHeader>
              <CardTitle>API Credentials</CardTitle>
              <CardDescription>API key and usage information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">API Key</label>
                <div className="flex gap-2">
                  <Input value={user.apiKey} disabled className="font-mono text-xs" />
                  <Button variant="outline" size="icon" onClick={copyApiKey}>
                    <Copy className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="icon">
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Total API Calls</label>
                <Input value={formatNumber(userApiCalls.length)} disabled />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Success Rate</label>
                <Input
                  value={`${((userApiCalls.filter(c => c.status === 200).length / userApiCalls.length) * 100).toFixed(1)}%`}
                  disabled
                />
              </div>
            </CardContent>
          </Card>

          {/* Credits Management */}
          <Card>
            <CardHeader>
              <CardTitle>Credits Management</CardTitle>
              <CardDescription>Manage user credit balance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Current Balance</label>
                <Input
                  type="number"
                  value={credits}
                  onChange={(e) => setCredits(Number(e.target.value))}
                />
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Add/Deduct Credits</label>
                <div className="flex gap-2">
                  <Input type="number" placeholder="Amount" />
                  <Button variant="outline">Apply</Button>
                </div>
              </div>
              <div className="p-4 bg-muted rounded-md">
                <p className="text-sm text-muted-foreground">
                  Credit usage this month: {formatNumber(userApiCalls.reduce((sum, call) => sum + call.credits, 0))}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Subscription Details */}
          <Card>
            <CardHeader>
              <CardTitle>Subscription Details</CardTitle>
              <CardDescription>Plan and billing information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium">Current Plan</label>
                <div>
                  <Badge variant="default" className="text-sm">
                    {user.plan.charAt(0).toUpperCase() + user.plan.slice(1)}
                  </Badge>
                </div>
              </div>
              <div className="space-y-2">
                <label className="text-sm font-medium">Billing Cycle</label>
                <Input value={user.billingCycle || 'N/A'} disabled />
              </div>
              {user.nextRenewalDate && (
                <div className="space-y-2">
                  <label className="text-sm font-medium">Next Renewal</label>
                  <Input value={formatDate(user.nextRenewalDate)} disabled />
                </div>
              )}
              <div className="space-y-2">
                <label className="text-sm font-medium">Account Status</label>
                <select
                  value={status}
                  onChange={(e) => setStatus(e.target.value as any)}
                  className="w-full px-3 py-2 rounded-md border border-input bg-background"
                >
                  <option value="active">Active</option>
                  <option value="suspended">Suspended</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Recent API Activity */}
        <Card>
          <CardHeader>
            <CardTitle>Recent API Activity</CardTitle>
            <CardDescription>Latest API calls from this user</CardDescription>
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
                  <TableHead>Credits</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {userApiCalls.slice(0, 10).map((call) => (
                  <TableRow key={call.id}>
                    <TableCell className="text-muted-foreground text-xs">
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
                    <TableCell>{call.credits}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex justify-between">
          <Button variant="destructive" className="gap-2">
            <Trash2 className="h-4 w-4" />
            Delete User
          </Button>
          <Button className="gap-2">
            <Save className="h-4 w-4" />
            Save Changes
          </Button>
        </div>
      </div>
    </MainLayout>
  )
}
