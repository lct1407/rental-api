/**
 * Analytics Service
 *
 * Handles all analytics and statistics-related operations
 */
import apiClient from './api'

export interface DashboardStats {
  total_api_calls: number
  api_calls_today: number
  api_calls_this_month: number
  credits_used_today: number
  credits_used_this_month: number
  credits_remaining: number
  active_api_keys: number
  active_webhooks: number
  avg_response_time: number
  success_rate: number
}

export interface ApiCallAnalytics {
  total_calls: number
  successful_calls: number
  failed_calls: number
  avg_response_time: number
  calls_by_day: Array<{
    date: string
    total: number
    success: number
    failed: number
  }>
  calls_by_endpoint: Array<{
    endpoint: string
    count: number
    avg_response_time: number
  }>
  calls_by_status: Array<{
    status_code: number
    count: number
    percentage: number
  }>
}

export interface UsageMetrics {
  period: string
  api_calls: number
  credits_used: number
  data_transferred: number
  unique_endpoints: number
  avg_daily_calls: number
}

export interface PerformanceMetrics {
  avg_response_time: number
  min_response_time: number
  max_response_time: number
  p50_response_time: number
  p95_response_time: number
  p99_response_time: number
  response_times_by_hour: Array<{
    hour: number
    avg_time: number
  }>
}

export interface AdminDashboardStats {
  total_users: number
  active_users: number
  new_users_today: number
  new_users_this_month: number
  total_revenue: number
  revenue_today: number
  revenue_this_month: number
  total_api_calls: number
  api_calls_today: number
  total_subscriptions: number
  active_subscriptions: number
  user_growth: Array<{
    date: string
    new_users: number
    total_users: number
  }>
  revenue_by_plan: Array<{
    plan: string
    revenue: number
    users: number
  }>
}

class AnalyticsService {
  // User Analytics

  /**
   * Get user dashboard statistics
   */
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await apiClient.get<DashboardStats>('/analytics/dashboard')
    return response.data
  }

  /**
   * Get API call analytics
   */
  async getApiCallAnalytics(params?: {
    start_date?: string
    end_date?: string
    api_key_id?: number
  }): Promise<ApiCallAnalytics> {
    const response = await apiClient.get<ApiCallAnalytics>('/analytics/api-calls', { params })
    return response.data
  }

  /**
   * Get usage metrics
   */
  async getUsageMetrics(params?: {
    period?: 'day' | 'week' | 'month' | 'year'
    start_date?: string
    end_date?: string
  }): Promise<UsageMetrics[]> {
    const response = await apiClient.get<UsageMetrics[]>('/analytics/usage', { params })
    return response.data
  }

  /**
   * Get performance metrics
   */
  async getPerformanceMetrics(params?: {
    start_date?: string
    end_date?: string
  }): Promise<PerformanceMetrics> {
    const response = await apiClient.get<PerformanceMetrics>('/analytics/performance', {
      params
    })
    return response.data
  }

  /**
   * Get endpoint usage breakdown
   */
  async getEndpointUsage(params?: {
    start_date?: string
    end_date?: string
    limit?: number
  }): Promise<Array<{
    endpoint: string
    method: string
    total_calls: number
    success_rate: number
    avg_response_time: number
    credits_used: number
  }>> {
    const response = await apiClient.get('/analytics/endpoints', { params })
    return response.data
  }

  /**
   * Get geographic distribution of API calls
   */
  async getGeographicDistribution(params?: {
    start_date?: string
    end_date?: string
  }): Promise<Array<{
    country: string
    country_code: string
    calls: number
    percentage: number
  }>> {
    const response = await apiClient.get('/analytics/geographic', { params })
    return response.data
  }

  /**
   * Export analytics data
   */
  async exportAnalytics(params: {
    format: 'csv' | 'json' | 'xlsx'
    start_date?: string
    end_date?: string
    include?: string[]
  }): Promise<Blob> {
    const response = await apiClient.get('/analytics/export', {
      params,
      responseType: 'blob'
    })
    return response.data
  }

  // Admin Analytics

  /**
   * Get admin dashboard statistics (admin only)
   */
  async getAdminDashboardStats(): Promise<AdminDashboardStats> {
    const response = await apiClient.get<AdminDashboardStats>('/analytics/admin/dashboard')
    return response.data
  }

  /**
   * Get platform-wide API call statistics (admin only)
   */
  async getPlatformApiStats(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    total_calls: number
    successful_calls: number
    failed_calls: number
    avg_response_time: number
    calls_by_day: Array<{
      date: string
      total: number
      success: number
      failed: number
    }>
    top_users: Array<{
      user_id: number
      user_email: string
      total_calls: number
    }>
  }> {
    const response = await apiClient.get('/analytics/admin/api-calls', { params })
    return response.data
  }

  /**
   * Get revenue analytics (admin only)
   */
  async getRevenueAnalytics(params?: {
    start_date?: string
    end_date?: string
    group_by?: 'day' | 'week' | 'month'
  }): Promise<{
    total_revenue: number
    revenue_by_period: Array<{
      period: string
      revenue: number
      transactions: number
    }>
    revenue_by_plan: Array<{
      plan: string
      revenue: number
      users: number
    }>
    mrr: number
    arr: number
  }> {
    const response = await apiClient.get('/analytics/admin/revenue', { params })
    return response.data
  }

  /**
   * Get user growth analytics (admin only)
   */
  async getUserGrowthAnalytics(params?: {
    start_date?: string
    end_date?: string
  }): Promise<{
    total_users: number
    growth_rate: number
    new_users_by_day: Array<{
      date: string
      new_users: number
      total_users: number
    }>
    user_retention: Array<{
      cohort: string
      retention_rate: number
    }>
    churn_rate: number
  }> {
    const response = await apiClient.get('/analytics/admin/user-growth', { params })
    return response.data
  }

  /**
   * Get system health metrics (admin only)
   */
  async getSystemHealth(): Promise<{
    api_uptime: number
    avg_response_time: number
    error_rate: number
    active_connections: number
    queue_size: number
    database_health: 'healthy' | 'degraded' | 'unhealthy'
    cache_hit_rate: number
  }> {
    const response = await apiClient.get('/analytics/admin/system-health')
    return response.data
  }
}

export default new AnalyticsService()
