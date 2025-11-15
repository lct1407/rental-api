/**
 * API Configuration
 */

export const API_CONFIG = {
  BASE_URL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  API_VERSION: import.meta.env.VITE_API_VERSION || 'v1',
  TIMEOUT: 30000, // 30 seconds
}

export const API_ENDPOINTS = {
  // Auth
  AUTH: {
    REGISTER: '/api/v1/auth/register',
    LOGIN: '/api/v1/auth/login',
    LOGOUT: '/api/v1/auth/logout',
    REFRESH: '/api/v1/auth/refresh',
    ME: '/api/v1/auth/me',
    CHANGE_PASSWORD: '/api/v1/auth/password/change',
    RESET_PASSWORD_REQUEST: '/api/v1/auth/password/reset-request',
    RESET_PASSWORD: '/api/v1/auth/password/reset',
    VERIFY_EMAIL: '/api/v1/auth/email/verify',
    ENABLE_2FA: '/api/v1/auth/2fa/enable',
    VERIFY_2FA: '/api/v1/auth/2fa/verify',
    DISABLE_2FA: '/api/v1/auth/2fa/disable',
    LOGIN_2FA: '/api/v1/auth/2fa/login',
  },
  // Users
  USERS: {
    ME: '/api/v1/users/me',
    UPDATE_ME: '/api/v1/users/me',
    DELETE_ME: '/api/v1/users/me',
    STATS: '/api/v1/users/me/stats',
    LIST: '/api/v1/users',
    BY_ID: (id: string | number) => `/api/v1/users/${id}`,
    SUSPEND: (id: string | number) => `/api/v1/users/${id}/suspend`,
    ACTIVATE: (id: string | number) => `/api/v1/users/${id}/activate`,
    ADD_CREDITS: (id: string | number) => `/api/v1/users/${id}/credits`,
    OVERVIEW: '/api/v1/users/stats/overview',
  },
  // API Keys
  API_KEYS: {
    LIST: '/api/v1/api-keys/',
    CREATE: '/api/v1/api-keys/',
    BY_ID: (id: string | number) => `/api/v1/api-keys/${id}`,
    UPDATE: (id: string | number) => `/api/v1/api-keys/${id}`,
    DELETE: (id: string | number) => `/api/v1/api-keys/${id}`,
    ROTATE: (id: string | number) => `/api/v1/api-keys/${id}/rotate`,
    ACTIVATE: (id: string | number) => `/api/v1/api-keys/${id}/activate`,
    DEACTIVATE: (id: string | number) => `/api/v1/api-keys/${id}/deactivate`,
  },
  // Webhooks
  WEBHOOKS: {
    LIST: '/api/v1/webhooks/',
    CREATE: '/api/v1/webhooks/',
    BY_ID: (id: string | number) => `/api/v1/webhooks/${id}`,
    UPDATE: (id: string | number) => `/api/v1/webhooks/${id}`,
    DELETE: (id: string | number) => `/api/v1/webhooks/${id}`,
    TEST: (id: string | number) => `/api/v1/webhooks/${id}/test`,
    DELIVERIES: (id: string | number) => `/api/v1/webhooks/${id}/deliveries`,
  },
  // Subscriptions
  SUBSCRIPTIONS: {
    PLANS: '/api/v1/subscriptions/plans',
    ME: '/api/v1/subscriptions/me',
    SUBSCRIBE: '/api/v1/subscriptions/subscribe',
    UPGRADE: '/api/v1/subscriptions/upgrade',
    CANCEL: '/api/v1/subscriptions/cancel',
    PURCHASE_CREDITS: '/api/v1/subscriptions/credits/purchase',
    INVOICES: '/api/v1/subscriptions/invoices',
    PAYMENT_METHODS: '/api/v1/subscriptions/payment-methods',
  },
  // Admin
  ADMIN: {
    DASHBOARD: '/api/v1/admin/dashboard',
    ANALYTICS: '/api/v1/admin/analytics',
    AUDIT_LOGS: '/api/v1/admin/audit-logs',
    ACTIVITY_LOGS: '/api/v1/admin/activity-logs',
  },
  // System
  HEALTH: '/health',
  ROOT: '/',
}
