# API Documentation

## 📚 Overview

This document provides comprehensive information about the **Enterprise API Management Platform** RESTful API. The API is built with FastAPI and provides complete functionality for user management, authentication, API key management, webhooks, subscriptions, and more.

## 🚀 Quick Start

### Accessing the Documentation

Once the server is running, you can access the interactive API documentation at:

- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON**: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

### Starting the Server

```bash
# Development
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🔐 Authentication

The API supports two authentication methods:

### 1. JWT Bearer Token

Used for user-based authentication (recommended for web/mobile apps).

**How to authenticate:**

1. Register a new account or login:
   ```bash
   POST /api/v1/auth/register
   POST /api/v1/auth/login
   ```

2. Use the returned `access_token` in subsequent requests:
   ```bash
   Authorization: Bearer <access_token>
   ```

3. Refresh tokens before expiry:
   ```bash
   POST /api/v1/auth/refresh
   ```

**Token Expiration:**
- Access Token: 30 minutes
- Refresh Token: 7 days

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 2. API Key

Used for programmatic access without user login (recommended for server-to-server).

**How to use:**

1. Create an API key (requires authentication):
   ```bash
   POST /api/v1/api-keys/
   ```

2. Include the API key in requests:
   ```bash
   X-API-Key: <your_api_key>
   ```

**Example:**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "X-API-Key: apk_1234567890abcdef"
```

## 📖 API Endpoints

### System Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/health` | Health check and service status | No |
| GET | `/` | API information and available endpoints | No |

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/auth/register` | Register new user account | No |
| POST | `/api/v1/auth/login` | Login with email/password | No |
| POST | `/api/v1/auth/logout` | Logout and blacklist token | Yes |
| POST | `/api/v1/auth/refresh` | Refresh access token | No (refresh token) |
| GET | `/api/v1/auth/me` | Get current user profile | Yes |
| POST | `/api/v1/auth/2fa/enable` | Enable two-factor authentication | Yes |
| POST | `/api/v1/auth/2fa/verify` | Verify and activate 2FA | Yes |
| POST | `/api/v1/auth/2fa/login` | Complete 2FA login | No |
| POST | `/api/v1/auth/2fa/disable` | Disable 2FA | Yes |
| POST | `/api/v1/auth/password/reset-request` | Request password reset email | No |
| POST | `/api/v1/auth/password/reset` | Reset password with token | No |
| POST | `/api/v1/auth/password/change` | Change password | Yes |
| POST | `/api/v1/auth/email/verify` | Verify email address | No |

### User Endpoints

| Method | Endpoint | Description | Auth Required | Admin Only |
|--------|----------|-------------|---------------|------------|
| GET | `/api/v1/users/me` | Get current user profile | Yes | No |
| PUT | `/api/v1/users/me` | Update current user profile | Yes | No |
| DELETE | `/api/v1/users/me` | Delete current user account | Yes | No |
| GET | `/api/v1/users/me/stats` | Get current user statistics | Yes | No |
| GET | `/api/v1/users` | List all users (paginated) | Yes | Yes |
| GET | `/api/v1/users/{user_id}` | Get user by ID | Yes | Yes |
| PUT | `/api/v1/users/{user_id}/suspend` | Suspend user account | Yes | Yes |
| PUT | `/api/v1/users/{user_id}/activate` | Activate suspended user | Yes | Yes |
| POST | `/api/v1/users/{user_id}/credits` | Add credits to user | Yes | Yes |
| GET | `/api/v1/users/stats/overview` | Get user statistics overview | Yes | Yes |

### API Key Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/api-keys/` | Create new API key | Yes |
| GET | `/api/v1/api-keys/` | List user's API keys | Yes |
| GET | `/api/v1/api-keys/{key_id}` | Get API key details | Yes |
| PUT | `/api/v1/api-keys/{key_id}` | Update API key | Yes |
| DELETE | `/api/v1/api-keys/{key_id}` | Delete API key | Yes |
| POST | `/api/v1/api-keys/{key_id}/rotate` | Rotate API key | Yes |
| PUT | `/api/v1/api-keys/{key_id}/activate` | Activate API key | Yes |
| PUT | `/api/v1/api-keys/{key_id}/deactivate` | Deactivate API key | Yes |

### Webhook Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/v1/webhooks/` | Create webhook | Yes |
| GET | `/api/v1/webhooks/` | List user's webhooks | Yes |
| GET | `/api/v1/webhooks/{webhook_id}` | Get webhook details | Yes |
| PUT | `/api/v1/webhooks/{webhook_id}` | Update webhook | Yes |
| DELETE | `/api/v1/webhooks/{webhook_id}` | Delete webhook | Yes |
| POST | `/api/v1/webhooks/{webhook_id}/test` | Test webhook delivery | Yes |
| GET | `/api/v1/webhooks/{webhook_id}/deliveries` | Get delivery logs | Yes |

### Subscription Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/subscriptions/plans` | List available plans | No |
| GET | `/api/v1/subscriptions/me` | Get current subscription | Yes |
| POST | `/api/v1/subscriptions/subscribe` | Subscribe to plan | Yes |
| POST | `/api/v1/subscriptions/upgrade` | Upgrade subscription | Yes |
| POST | `/api/v1/subscriptions/cancel` | Cancel subscription | Yes |
| POST | `/api/v1/subscriptions/credits/purchase` | Purchase credits | Yes |
| GET | `/api/v1/subscriptions/invoices` | List invoices | Yes |
| GET | `/api/v1/subscriptions/payment-methods` | List payment methods | Yes |
| POST | `/api/v1/subscriptions/payment-methods` | Add payment method | Yes |

### Admin Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/admin/dashboard` | Get dashboard metrics | Yes (Admin) |
| GET | `/api/v1/admin/analytics` | Get system analytics | Yes (Admin) |
| GET | `/api/v1/admin/audit-logs` | Get audit logs | Yes (Admin) |
| GET | `/api/v1/admin/activity-logs` | Get activity logs | Yes (Admin) |

## 🔄 Common Request Patterns

### Pagination

Most list endpoints support pagination with the following query parameters:

```
?page=1&limit=20
```

**Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (1-100, default: 20)

**Response:**
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "limit": 20,
  "pages": 8
}
```

### Filtering

Many endpoints support filtering:

```
?search=john&status=active&role=user
```

### Sorting

List endpoints support sorting:

```
?sort_by=created_at&sort_order=desc
```

## 📝 Example Workflows

### 1. User Registration and Authentication

```bash
# 1. Register
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "username": "johndoe",
    "password": "SecureP@ss123",
    "full_name": "John Doe"
  }'

# Response:
# {
#   "access_token": "eyJhbGci...",
#   "refresh_token": "eyJhbGci...",
#   "token_type": "bearer",
#   "user": {...}
# }

# 2. Use the access token
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer eyJhbGci..."
```

### 2. Creating and Using API Keys

```bash
# 1. Create API key (requires authentication)
curl -X POST "http://localhost:8000/api/v1/api-keys/" \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production API Key",
    "scopes": ["read", "write"],
    "expires_at": "2025-12-31T23:59:59Z"
  }'

# Response:
# {
#   "id": 1,
#   "key": "apk_1234567890abcdef",
#   "name": "Production API Key",
#   ...
# }

# 2. Use API key
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "X-API-Key: apk_1234567890abcdef"
```

### 3. Setting Up Webhooks

```bash
# Create webhook
curl -X POST "http://localhost:8000/api/v1/webhooks/" \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/webhook",
    "events": ["user.created", "user.updated"],
    "secret": "webhook_secret_123"
  }'

# Test webhook
curl -X POST "http://localhost:8000/api/v1/webhooks/1/test" \
  -H "Authorization: Bearer eyJhbGci..."
```

### 4. Subscribing to a Plan

```bash
# View available plans
curl -X GET "http://localhost:8000/api/v1/subscriptions/plans"

# Subscribe to plan
curl -X POST "http://localhost:8000/api/v1/subscriptions/subscribe" \
  -H "Authorization: Bearer eyJhbGci..." \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "pro",
    "payment_method": "stripe",
    "payment_token": "tok_123..."
  }'
```

## ⚠️ Error Handling

### Standard Error Response Format

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "field": "field_name"
}
```

### HTTP Status Codes

| Code | Description | Example |
|------|-------------|---------|
| 200 | Success | Request completed successfully |
| 201 | Created | Resource created successfully |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Validation Error | Request validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error occurred |

### Validation Errors (422)

```json
{
  "detail": "Validation error",
  "errors": [
    {
      "field": "email",
      "message": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

## 🚦 Rate Limiting

Default rate limits (configurable per user/API key):

- **Per Minute**: 60 requests
- **Per Hour**: 1,000 requests
- **Per Day**: 10,000 requests

### Rate Limit Headers

All responses include rate limit information:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1642598400
```

### Rate Limit Exceeded Response

```json
{
  "detail": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

## 🔒 Security Best Practices

1. **Always use HTTPS in production**
2. **Never expose API keys in client-side code**
3. **Rotate API keys regularly**
4. **Enable 2FA for admin accounts**
5. **Use IP whitelisting for API keys when possible**
6. **Implement proper CORS policies**
7. **Monitor audit logs regularly**
8. **Keep refresh tokens secure**
9. **Set appropriate token expiration times**
10. **Validate webhook signatures**

## 📊 Webhook Events

Available webhook events:

### User Events
- `user.created` - New user registered
- `user.updated` - User profile updated
- `user.deleted` - User account deleted
- `user.suspended` - User account suspended
- `user.activated` - User account activated

### Subscription Events
- `subscription.created` - New subscription created
- `subscription.updated` - Subscription plan changed
- `subscription.cancelled` - Subscription cancelled
- `subscription.expired` - Subscription expired

### Payment Events
- `payment.successful` - Payment completed successfully
- `payment.failed` - Payment failed
- `payment.refunded` - Payment refunded

### API Key Events
- `apikey.created` - New API key created
- `apikey.rotated` - API key rotated
- `apikey.deleted` - API key deleted

## 🧪 Testing the API

### Using Swagger UI

1. Navigate to [http://localhost:8000/docs](http://localhost:8000/docs)
2. Click on any endpoint to expand it
3. Click "Try it out"
4. Fill in the parameters
5. Click "Execute"
6. View the response

### Using cURL

See examples in the "Example Workflows" section above.

### Using Postman

1. Import the OpenAPI spec: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)
2. Set up authentication in the collection settings
3. Start making requests

## 📮 Support

For API support, please contact:

- **Email**: support@api-management-platform.com
- **Documentation**: [https://docs.api-management-platform.com](https://docs.api-management-platform.com)
- **Status Page**: [http://localhost:8000/health](http://localhost:8000/health)

## 📄 License

This API is proprietary software. Unauthorized use is prohibited.

---

**Version**: 2.0.0
**Last Updated**: 2025-11-15
**Environment**: Development
