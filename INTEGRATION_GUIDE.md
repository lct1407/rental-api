# Frontend-Backend Integration Guide

## Overview

This guide explains how the Frontend (React/TypeScript) and Backend (FastAPI/Python) are integrated in the RentAPI platform.

## Architecture

```
┌─────────────────┐         HTTP/REST         ┌─────────────────┐
│                 │ ───────────────────────> │                 │
│   React Client  │                          │  FastAPI Backend│
│   (Port 5173)   │ <─────────────────────── │  (Port 8000)    │
│                 │     JSON Responses        │                 │
└─────────────────┘                          └─────────────────┘
```

## Setup Instructions

### 1. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment (if not exists)
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# (Optional) Seed database with test data
python scripts/seed_data.py

# Start the backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at: `http://localhost:8000`
API Documentation: `http://localhost:8000/docs`

### 2. Frontend Setup

```bash
# Navigate to frontend directory
cd client

# Install dependencies
npm install

# The .env file is already configured to point to localhost:8000
# If needed, update VITE_API_URL in client/.env

# Start the development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Integration Components

### 1. API Configuration (`client/src/config/api.ts`)

Defines all API endpoints and configuration:
- Base URL: `http://localhost:8000`
- API endpoints for Auth, Users, API Keys, Webhooks, Subscriptions, Admin

### 2. API Service Layer (`client/src/services/`)

#### Main API Service (`api.ts`)
- Handles HTTP requests (GET, POST, PUT, PATCH, DELETE)
- Manages JWT tokens (access & refresh)
- Automatic token refresh on 401 errors
- Error handling with custom `ApiError` class

#### Auth Service (`auth.service.ts`)
- User registration
- User login (with 2FA support)
- Logout
- Password management
- Email verification
- 2FA management

#### User Service (`user.service.ts`)
- Get current user profile
- Update user profile
- User statistics
- Admin user management

### 3. Type Definitions (`client/src/types/index.ts`)

TypeScript interfaces that match backend Pydantic schemas:
- `User`, `UserResponse`, `UserProfileResponse`
- `TokenResponse`, `TempTokenResponse`
- `LoginCredentials`, `RegisterData`
- `ApiKey`, `Webhook`, `Subscription`
- `PaginatedResponse`, `ErrorResponse`

### 4. Authentication Context (`client/src/contexts/AuthContext.tsx`)

React Context that manages authentication state:
- User state management
- Login/Register/Logout functions
- Token persistence
- Automatic user profile fetching on app load
- Support for 2FA flow

### 5. Updated Pages

#### Login Page (`client/src/pages/public/LoginPage.tsx`)
- Removed mock role selection
- Integrated with real API
- Error handling and display
- Loading states
- Automatic role-based navigation

#### Register Page (`client/src/pages/public/RegisterPage.tsx`)
- Added username field (required by backend)
- Updated password requirements (including special characters)
- Full name is now optional
- Error handling and display
- Loading states

## Authentication Flow

### Registration Flow
```
1. User fills registration form (username, email, password, full_name*)
2. Frontend validates password strength
3. POST /api/v1/auth/register
4. Backend creates user and returns tokens + user data
5. Frontend stores tokens in localStorage
6. User is redirected to dashboard
```

### Login Flow
```
1. User enters email and password
2. POST /api/v1/auth/login
3. Backend validates credentials
4. If 2FA enabled: Return temp_token, show 2FA page
5. If 2FA disabled: Return access_token + refresh_token + user data
6. Frontend stores tokens in localStorage
7. User is redirected based on role (admin → /admin, user → /dashboard)
```

### Token Refresh Flow
```
1. API request fails with 401 Unauthorized
2. API service automatically attempts token refresh
3. POST /api/v1/auth/refresh with refresh_token
4. Backend validates refresh token
5. Returns new access_token and refresh_token
6. Frontend stores new tokens
7. Original request is retried with new token
8. If refresh fails, user is logged out and redirected to /login
```

## API Request Examples

### Making Authenticated Requests

```typescript
import { userService } from '../services/user.service'

// Get current user profile
try {
  const user = await userService.getCurrentUser()
  console.log(user)
} catch (error) {
  console.error('Failed to fetch user:', error)
}
```

### Error Handling

```typescript
import { ApiError } from '../services/api'

try {
  await authService.login({ email, password })
} catch (error) {
  if (error instanceof ApiError) {
    console.error('API Error:', error.detail)
    console.error('Status:', error.status)
    console.error('Error Code:', error.errorCode)
  }
}
```

## Environment Variables

### Backend (`.env`)
```env
# Database
DATABASE_URL=postgresql://user:password@localhost/dbname

# JWT Settings
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Frontend (`.env`)
```env
VITE_API_URL=http://localhost:8000
VITE_API_VERSION=v1
VITE_APP_NAME="RentAPI - API Services Platform"
VITE_APP_ENV=development
```

## Testing the Integration

### 1. Test User Registration

```bash
# Using the frontend
1. Navigate to http://localhost:5173/register
2. Fill in:
   - Username: testuser
   - Email: test@example.com
   - Password: Test123!@#
   - Accept terms
3. Click "Create Account"
4. Should redirect to /dashboard

# Using curl
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "username": "testuser",
    "password": "Test123!@#",
    "full_name": "Test User"
  }'
```

### 2. Test User Login

```bash
# Using the frontend
1. Navigate to http://localhost:5173/login
2. Enter email and password
3. Click "Sign In"
4. Should redirect based on role

# Using curl
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test123!@#"
  }'
```

### 3. Test Authenticated Request

```bash
# Get current user profile
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Common Issues and Solutions

### Issue: CORS Error
**Solution**: Ensure backend `.env` has correct `ALLOWED_ORIGINS`:
```env
ALLOWED_ORIGINS=http://localhost:5173
```

### Issue: 401 Unauthorized on all requests
**Solution**:
1. Check if tokens are stored in localStorage
2. Verify token is not expired
3. Check backend SECRET_KEY matches

### Issue: Frontend can't connect to backend
**Solution**:
1. Verify backend is running on port 8000
2. Check `VITE_API_URL` in `client/.env`
3. Ensure no firewall blocking

### Issue: User type errors in components
**Solution**: Update components to use new User type fields:
- `id` is now `number` (was `string`)
- Use `username` instead of `name`
- Use `full_name` for display name
- Use `created_at` instead of `registrationDate`
- Use `avatar_url` instead of `avatar`

## Data Model Mapping

### Backend → Frontend

| Backend Field | Frontend Field | Type |
|--------------|----------------|------|
| `id` | `id` | `number` |
| `email` | `email` | `string` |
| `username` | `username` | `string` |
| `full_name` | `full_name` | `string?` |
| `role` | `role` | `'admin' \| 'user'` |
| `status` | `status` | `'active' \| 'suspended' \| 'inactive'` |
| `credits` | `credits` | `number` |
| `created_at` | `created_at` | `string` (ISO date) |
| `avatar_url` | `avatar_url` | `string?` |
| `email_verified` | `email_verified` | `boolean` |
| `two_factor_enabled` | `two_factor_enabled` | `boolean` |

## Next Steps

### TODO: Components to Update
The following components may need updates to use the new User type structure:
1. `UserProfile.tsx` - Update to use new user fields
2. `UserManagement.tsx` - Update to use new user fields and API
3. `AdminDashboard.tsx` - Update to use admin API endpoints
4. `UserDashboard.tsx` - Update to use user stats API

### TODO: Additional Services to Create
1. `apiKey.service.ts` - For API key management
2. `webhook.service.ts` - For webhook management
3. `subscription.service.ts` - For subscription management
4. `admin.service.ts` - For admin operations

### TODO: Features to Implement
1. 2FA verification page
2. Password reset flow
3. Email verification flow
4. Real-time notifications with WebSockets
5. File upload for avatar

## API Documentation

Full API documentation is available at `http://localhost:8000/docs` (Swagger UI)

Key endpoints:
- **Auth**: `/api/v1/auth/*`
- **Users**: `/api/v1/users/*`
- **API Keys**: `/api/v1/api-keys/*`
- **Webhooks**: `/api/v1/webhooks/*`
- **Subscriptions**: `/api/v1/subscriptions/*`
- **Admin**: `/api/v1/admin/*`

## Support

For issues or questions:
1. Check the API documentation at `/docs`
2. Review backend logs for errors
3. Check browser console for frontend errors
4. Verify environment variables are correct

---

**Last Updated**: 2025-11-15
**Version**: 1.0.0
