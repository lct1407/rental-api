# RentAPI - Enterprise SaaS API Platform

A complete enterprise-grade API management platform with credit-based subscriptions, user management, analytics, and real-time monitoring. Built with FastAPI backend and React TypeScript frontend.

## 🚀 Features

### Backend (FastAPI)
- **JWT Authentication** with 2FA support
- **Role-Based Access Control** (User, Admin, Super Admin)
- **72+ RESTful API Endpoints**
- **PostgreSQL Database** with Alembic migrations
- **Celery Background Tasks** for async operations
- **WebSocket Support** for real-time updates
- **Comprehensive API Documentation** (Swagger UI)
- **Rate Limiting & Credit System**
- **Webhook Management**
- **Payment Integration Ready**

### Frontend (React + TypeScript)
- **Modern UI** with Tailwind CSS & shadcn/ui
- **Real-time Dashboards** for users and admins
- **API Key Management**
- **Usage Analytics & Charts**
- **Subscription Management**
- **Dark Mode Support**
- **Responsive Design** (mobile-first)
- **WebSocket Integration** for live updates

---

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** and npm ([Download](https://nodejs.org/))
- **PostgreSQL 14+** ([Download](https://www.postgresql.org/download/))
- **Redis** (optional, for Celery tasks) ([Download](https://redis.io/download))
- **Git** ([Download](https://git-scm.com/downloads))

---

## 🛠️ Installation Guide

### Part 1: Backend Setup (FastAPI)

#### Step 1: Clone the Repository
```bash
git clone https://github.com/lct1407/APIs-for-rent.git
cd APIs-for-rent
```

#### Step 2: Create Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

#### Step 3: Install Python Dependencies
```bash
pip install -r requirements.txt
```

This will install all required packages including:
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL drivers
- Celery
- And more...

#### Step 4: Set Up PostgreSQL Database

**Option A: Using PostgreSQL Command Line**
```bash
# Connect to PostgreSQL
psql -U postgres

# Create database
CREATE DATABASE apis_for_rent;

# Create user (optional)
CREATE USER rentapi_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE apis_for_rent TO rentapi_user;

# Exit psql
\q
```

**Option B: Using pgAdmin or other GUI tools**
- Create a new database named `apis_for_rent`

#### Step 5: Configure Environment Variables

Create a `.env` file in the project root directory:

```bash
# Copy the example file
cp .env.example .env

# Or create manually
touch .env
```

Edit the `.env` file with your configuration:

```env
# Database Configuration
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/apis_for_rent

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Email Configuration (for 2FA and notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM=your-email@gmail.com

# Redis (for Celery - optional)
REDIS_URL=redis://localhost:6379/0

# CORS (Frontend URL)
CORS_ORIGINS=["http://localhost:5173"]

# Admin User (created during seed)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=Admin123!@#
```

**Important:** Replace placeholder values with your actual credentials.

#### Step 6: Run Database Migrations

```bash
# Initialize Alembic (if not already done)
alembic upgrade head
```

This creates all necessary database tables and relationships.

#### Step 7: Seed the Database with Initial Data

```bash
# Run the seed script
python -m app.scripts.seed_data
```

This creates:
- Admin user (admin@example.com)
- Demo user accounts (john@acme.com, jane@startup.io)
- Sample API keys
- Sample subscriptions
- Demo data for testing

You should see output like:
```
✓ Database seeded successfully!
✓ Created 15 users
✓ Created 25 API keys
✓ Created 15 subscriptions
...
```

#### Step 8: Start the Backend Server

```bash
# Start with Uvicorn (development mode with auto-reload)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Backend is now running!** 🎉

- **API Base URL:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

#### Step 9 (Optional): Start Celery Worker

For background tasks (email sending, data processing):

**Terminal 2:**
```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info
```

**Terminal 3 (Optional):** For scheduled tasks:
```bash
# Activate virtual environment
source venv/bin/activate

# Start Celery beat scheduler
celery -A app.core.celery_app beat --loglevel=info
```

---

### Part 2: Frontend Setup (React + TypeScript)

#### Step 1: Navigate to Frontend Directory
```bash
# Open a new terminal window
cd APIs-for-rent/client
```

#### Step 2: Install Node Dependencies
```bash
npm install
```

This installs all required packages:
- React 19
- TypeScript
- Vite
- Tailwind CSS
- Axios
- Recharts
- And more...

Installation may take 2-3 minutes.

#### Step 3: Configure Frontend Environment

The `.env` file should already exist in `client/` directory with:

```env
VITE_API_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/api/v1/ws
```

If not, create it:
```bash
# Copy example
cp .env.example .env
```

#### Step 4: Start the Frontend Development Server

```bash
npm run dev
```

You should see:
```
  VITE v7.1.7  ready in 1234 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: use --host to expose
  ➜  press h + enter to show help
```

**Frontend is now running!** 🎉

- **Application URL:** http://localhost:5173

---

## 🧪 Testing the Application

### Step 1: Open Your Browser

Navigate to: **http://localhost:5173**

You should see the landing page.

### Step 2: Login with Demo Credentials

Click "Sign In" and use one of these accounts:

**Admin Account:**
- Email: `admin@example.com`
- Password: `Admin123!@#`

**Regular User Accounts:**
- Email: `john@acme.com` | Password: `User123!@#`
- Email: `jane@startup.io` | Password: `User123!@#`

### Step 3: Explore the Application

#### As a Regular User:
1. **Dashboard** - View your API usage statistics and charts
2. **Profile** - Update your profile information
3. **API Keys** - Manage your API keys (when you create them)
4. **Billing** - View subscription and payment info

#### As an Admin:
1. **Admin Dashboard** - Platform-wide statistics and metrics
2. **User Management** - View, search, and manage all users
3. **User Details** - Click on any user to see detailed information
4. **Analytics** - View top users and platform health

### Step 4: Test the API Directly

You can also test the backend API using the interactive documentation:

Open: **http://localhost:8000/docs**

Try these endpoints:
1. `/health` - Check if API is running
2. `/api/v1/auth/login` - Login endpoint
3. `/api/v1/users/me` - Get current user (requires authentication)

---

## 📁 Project Structure

```
APIs-for-rent/
├── app/                          # Backend (FastAPI)
│   ├── api/                      # API endpoints
│   │   ├── v1/
│   │   │   ├── auth.py          # Authentication endpoints
│   │   │   ├── users.py         # User management
│   │   │   ├── api_keys.py      # API key management
│   │   │   ├── webhooks.py      # Webhook management
│   │   │   ├── subscriptions.py # Billing & subscriptions
│   │   │   └── analytics.py     # Analytics endpoints
│   ├── core/                     # Core configuration
│   │   ├── config.py            # App settings
│   │   ├── security.py          # Security utilities
│   │   └── celery_app.py        # Celery configuration
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business logic
│   ├── scripts/                  # Utility scripts
│   │   └── seed_data.py         # Database seeding
│   └── main.py                   # FastAPI application
│
├── client/                       # Frontend (React)
│   ├── src/
│   │   ├── components/
│   │   │   ├── ui/              # Reusable UI components
│   │   │   └── layout/          # Layout components
│   │   ├── pages/
│   │   │   ├── public/          # Public pages
│   │   │   ├── user/            # User pages
│   │   │   └── admin/           # Admin pages
│   │   ├── services/            # API service layer
│   │   │   ├── api.ts           # Axios client
│   │   │   ├── authService.ts   # Auth API calls
│   │   │   ├── userService.ts   # User API calls
│   │   │   ├── apiKeyService.ts
│   │   │   ├── webhookService.ts
│   │   │   ├── subscriptionService.ts
│   │   │   └── analyticsService.ts
│   │   ├── contexts/            # React contexts
│   │   │   ├── AuthContext.tsx  # Authentication state
│   │   │   └── ThemeContext.tsx # Dark mode
│   │   ├── types/               # TypeScript types
│   │   └── App.tsx              # Main app component
│   ├── .env                      # Environment variables
│   └── package.json
│
├── alembic/                      # Database migrations
├── .env                          # Backend environment variables
├── requirements.txt              # Python dependencies
├── README.md                     # This file
└── STARTUP_GUIDE.md             # Detailed startup guide
```

---

## 🔧 Available Commands

### Backend Commands
```bash
# Start development server
uvicorn app.main:app --reload --port 8000

# Run database migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Seed database
python -m app.scripts.seed_data

# Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Start Celery beat
celery -A app.core.celery_app beat --loglevel=info

# Run tests (when implemented)
pytest
```

### Frontend Commands
```bash
# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Run linter
npm run lint

# Type check
npx tsc --noEmit
```

---

## 🌐 API Endpoints Overview

The backend provides 72+ endpoints organized by feature:

### Authentication (`/api/v1/auth/`)
- `POST /login` - User login
- `POST /register` - User registration
- `POST /refresh` - Refresh access token
- `POST /logout` - User logout
- `POST /2fa/enable` - Enable 2FA
- `POST /forgot-password` - Password reset

### Users (`/api/v1/users/`)
- `GET /me` - Get current user
- `PUT /me` - Update profile
- `GET /` - List users (admin)
- `GET /{id}` - Get user by ID (admin)
- `PUT /{id}/suspend` - Suspend user (admin)
- `PUT /{id}/activate` - Activate user (admin)

### API Keys (`/api/v1/api-keys/`)
- `GET /` - List API keys
- `POST /` - Create new API key
- `GET /{id}` - Get API key details
- `PUT /{id}/rotate` - Rotate API key
- `DELETE /{id}` - Revoke API key
- `GET /{id}/stats` - Get usage statistics

### Webhooks (`/api/v1/webhooks/`)
- `GET /` - List webhooks
- `POST /` - Create webhook
- `PUT /{id}` - Update webhook
- `DELETE /{id}` - Delete webhook
- `POST /{id}/test` - Test webhook
- `GET /{id}/deliveries` - Get delivery history

### Subscriptions (`/api/v1/subscriptions/`)
- `GET /plans` - List available plans
- `GET /me` - Get current subscription
- `POST /` - Create subscription
- `PUT /{id}` - Update subscription
- `POST /{id}/cancel` - Cancel subscription

### Analytics (`/api/v1/analytics/`)
- `GET /dashboard` - User dashboard stats
- `GET /api-calls` - API call analytics
- `GET /admin/dashboard` - Admin dashboard (admin)
- `GET /admin/revenue` - Revenue analytics (admin)

**Full API documentation:** http://localhost:8000/docs

---

## 🔐 Security Features

- **JWT Authentication** with access & refresh tokens
- **Password Hashing** using bcrypt
- **Two-Factor Authentication** (2FA) support
- **Role-Based Access Control** (RBAC)
- **API Rate Limiting** per user/key
- **CORS Protection** configured
- **SQL Injection Prevention** via SQLAlchemy ORM
- **XSS Protection** via input validation

---

## 📊 Tech Stack

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| FastAPI | 0.115.x | Web framework |
| SQLAlchemy | 2.0.x | ORM |
| PostgreSQL | 14+ | Database |
| Alembic | 1.13.x | Migrations |
| Celery | 5.4.x | Background tasks |
| Redis | 7.x | Cache & queue |
| Pydantic | 2.x | Validation |

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.1.1 | UI framework |
| TypeScript | 5.9.3 | Type safety |
| Vite | 7.1.7 | Build tool |
| Tailwind CSS | 3.4.18 | Styling |
| Axios | 1.7.0 | HTTP client |
| Recharts | 3.3.0 | Charts |
| React Router | 7.9.5 | Routing |

---

## 🐛 Troubleshooting

### Backend Issues

**Database connection error:**
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list  # macOS

# Check database exists
psql -U postgres -c "\l"
```

**Port 8000 already in use:**
```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>
```

**Migration errors:**
```bash
# Check migration status
alembic current

# Reset database (WARNING: Deletes all data)
alembic downgrade base
alembic upgrade head
python -m app.scripts.seed_data
```

### Frontend Issues

**Dependencies installation fails:**
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**API connection error:**
- Ensure backend is running on http://localhost:8000
- Check `.env` has correct `VITE_API_URL`
- Check backend CORS settings in `.env`

**TypeScript errors:**
```bash
# Check for type errors
npx tsc --noEmit

# Clear Vite cache
rm -rf node_modules/.vite
npm run dev
```

---

## 🚀 Production Deployment

### Backend (FastAPI)

```bash
# Install production server
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# Or use Docker
docker build -t rentapi-backend .
docker run -p 8000:8000 rentapi-backend
```

### Frontend (React)

```bash
# Build production bundle
npm run build

# Output is in client/dist/
# Deploy to:
# - Vercel
# - Netlify
# - AWS S3 + CloudFront
# - Nginx
```

---

## 📝 Demo Credentials

### Admin Account
- **Email:** admin@example.com
- **Password:** Admin123!@#
- **Role:** Super Admin
- **Access:** All features including user management

### User Accounts
- **Email:** john@acme.com | **Password:** User123!@#
- **Email:** jane@startup.io | **Password:** User123!@#
- **Role:** Regular User
- **Access:** Dashboard, profile, API keys, billing

---

## 🎯 Current Implementation Status

### ✅ Completed
- FastAPI backend with 72+ endpoints
- PostgreSQL database with migrations
- JWT authentication with 2FA support
- Role-based access control
- React frontend with TypeScript
- User & Admin dashboards with real data
- API service layer (5 services)
- Celery background tasks
- WebSocket support
- Database seeding script
- Comprehensive documentation

### 🚧 Ready for Implementation
- Additional UI pages (API Keys, Webhooks, Billing)
- WebSocket real-time updates in UI
- Payment gateway integration (Stripe/PayPal)
- Email notification system
- Advanced analytics charts
- Unit & integration tests
- Docker Compose setup

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License.

---

## 💬 Support

For issues and questions:
- **GitHub Issues:** [Create an issue](https://github.com/lct1407/APIs-for-rent/issues)
- **API Documentation:** http://localhost:8000/docs
- **Startup Guide:** See `STARTUP_GUIDE.md` for detailed setup

---

## 🎉 Quick Start Summary

```bash
# Backend (Terminal 1)
cd APIs-for-rent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
# Create .env file with your database config
alembic upgrade head
python -m app.scripts.seed_data
uvicorn app.main:app --reload --port 8000

# Frontend (Terminal 2)
cd APIs-for-rent/client
npm install
npm run dev

# Open http://localhost:5173
# Login: admin@example.com / Admin123!@#
```

---

**Built with ❤️ using FastAPI, React, TypeScript, and PostgreSQL**

Last Updated: 2025-11-15
