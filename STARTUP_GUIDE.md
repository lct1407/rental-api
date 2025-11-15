# Startup Guide - Enterprise SaaS API Platform

## Prerequisites

- Python 3.11+ installed
- Node.js 18+ and npm installed
- PostgreSQL database running
- Redis server running (for Celery tasks)

## Backend Setup

### 1. Navigate to Backend Directory
```bash
cd APIs-for-rent
```

### 2. Create and Activate Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/apis_for_rent

# Security
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email (for 2FA and notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=["http://localhost:5173"]

# Admin
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=Admin123!@#
```

### 5. Initialize Database
```bash
# Run migrations
alembic upgrade head

# Seed initial data (creates admin user and demo data)
python -m app.scripts.seed_data
```

### 6. Start the Backend Server
```bash
# Option 1: Using Uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Using the run script
python run.py
```

The backend API will be available at: **http://localhost:8000**
API Documentation: **http://localhost:8000/docs**

### 7. Start Celery Worker (Optional - for background tasks)
In a new terminal:
```bash
source venv/bin/activate
celery -A app.core.celery_app worker --loglevel=info
```

### 8. Start Celery Beat (Optional - for scheduled tasks)
In another terminal:
```bash
source venv/bin/activate
celery -A app.core.celery_app beat --loglevel=info
```

## Frontend Setup

### 1. Navigate to Frontend Directory
```bash
cd APIs-for-rent/client
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Configure Environment Variables
The `.env` file should already exist with:
```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/ws
```

### 4. Start the Frontend Development Server
```bash
npm run dev
```

The frontend will be available at: **http://localhost:5173**

## Testing the Application

### 1. Access the Frontend
Open your browser and navigate to: **http://localhost:5173**

### 2. Login with Demo Credentials

**Admin Account:**
- Email: `admin@example.com`
- Password: `Admin123!@#`

**Regular User Accounts:**
- Email: `john@acme.com` | Password: `User123!@#`
- Email: `jane@startup.io` | Password: `User123!@#`

### 3. Test Key Features

#### As Regular User:
1. **Dashboard**: View API usage statistics, charts, and metrics
2. **Profile**: Update user profile information
3. **API Keys**: Create, view, and manage API keys (when implemented)
4. **Billing**: View subscription plan and payment history (when implemented)

#### As Admin:
1. **Admin Dashboard**: View platform-wide statistics, user growth, revenue
2. **User Management**: List, search, filter, and manage users
3. **User Details**: View individual user details, suspend/activate accounts
4. **Analytics**: View platform metrics and top users

### 4. API Testing

#### Test Backend API Directly:
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"Admin123!@#"}'

# Get current user (replace TOKEN with access_token from login)
curl http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer TOKEN"
```

## Troubleshooting

### Backend Issues

**Database Connection Error:**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check database exists
psql -U postgres -c "\l"
```

**Migration Issues:**
```bash
# Reset migrations (CAUTION: Drops all data)
alembic downgrade base
alembic upgrade head
```

**Port Already in Use:**
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>
```

### Frontend Issues

**Module Not Found:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**TypeScript Errors:**
```bash
# Check for type errors
npx tsc --noEmit

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

**API Connection Error:**
- Ensure backend is running on port 8000
- Check CORS settings in backend `.env`
- Verify `VITE_API_URL` in frontend `.env`

## Production Deployment

### Backend (FastAPI)
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

### Frontend (React)
```bash
# Build production bundle
npm run build

# Preview production build
npm run preview

# Serve with nginx or any static file server
# Build output is in client/dist/
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    Client (React)                       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Dashboard │ │  Auth    │ │ Profile  │ │  Admin   │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┴────────────┴────────────┘         │
│                      │ HTTP/WebSocket                   │
└──────────────────────┼──────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────┐
│                      ▼                                   │
│              FastAPI Backend                             │
│  ┌──────────────────────────────────────────────┐      │
│  │          API Routes (72+ endpoints)          │      │
│  ├──────────┬──────────┬──────────┬─────────────┤      │
│  │  Auth    │  Users   │ API Keys │  Webhooks   │      │
│  │  RBAC    │Analytics │  Billing │Subscriptions│      │
│  └──────────┴──────────┴──────────┴─────────────┘      │
│       │                                                  │
│  ┌────▼─────────┐  ┌──────────┐  ┌──────────┐         │
│  │  PostgreSQL  │  │  Redis   │  │  Celery  │         │
│  │   Database   │  │  Cache   │  │  Worker  │         │
│  └──────────────┘  └──────────┘  └──────────┘         │
└─────────────────────────────────────────────────────────┘
```

## Current Implementation Status

### ✅ Completed Features

**Backend:**
- JWT authentication with 2FA support
- Role-based access control (User, Admin, Super Admin)
- 72+ RESTful API endpoints
- Database models with relationships
- Celery background tasks
- WebSocket support
- Comprehensive API documentation
- Seed data script

**Frontend:**
- Authentication (login, register, logout)
- User dashboard with real-time stats
- Admin dashboard with platform metrics
- API services layer (5 services created)
- TypeScript types matching backend
- Error handling and loading states
- Responsive design

### 🚧 Features Ready for Implementation

- API Key management UI
- Webhook management UI
- Billing and subscription UI
- User settings page
- Real-time WebSocket updates
- Toast notifications
- Advanced analytics charts

## Next Steps

1. **Test the complete authentication flow**
2. **Verify dashboard data loading from backend**
3. **Implement remaining UI pages** (API Keys, Webhooks, Billing)
4. **Add WebSocket real-time updates**
5. **Implement toast notifications for user feedback**
6. **Add comprehensive error boundaries**
7. **Implement unit and integration tests**

## Support

For issues or questions:
- Check backend logs in terminal running uvicorn
- Check frontend console in browser DevTools
- Review API documentation at http://localhost:8000/docs
- Check network requests in browser DevTools

---

**Last Updated:** 2025-11-15
**Version:** Phase 2 - Frontend-Backend Integration Complete
