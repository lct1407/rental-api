# RentAPI - Enterprise SaaS API Platform (Backend)

> Complete FastAPI backend with authentication, billing, webhooks, real-time updates, and background tasks

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7+-red.svg)](https://redis.io/)

## 🚀 Features

### Core Features
- ✅ **Incremental bigint IDs** (NOT UUID) for all database models
- ✅ **JWT Authentication** with access + refresh tokens
- ✅ **Two-Factor Authentication** (TOTP) with QR code generation
- ✅ **Role-Based Access Control** (RBAC) with 30+ permissions
- ✅ **Redis Caching** with custom decorators
- ✅ **Rate Limiting** (per-user and per-API-key with token bucket algorithm)
- ✅ **API Key Management** with scopes, IP whitelist, and rotation
- ✅ **Webhook System** with retry logic and exponential backoff
- ✅ **Dual Payment Processing** - Stripe AND PayPal in parallel
- ✅ **Multi-tenancy** with Organizations
- ✅ **Real-time Analytics** with usage tracking
- ✅ **WebSocket Support** for real-time updates
- ✅ **Background Tasks** with Celery for async processing
- ✅ **Audit Logging** and security events
- ✅ **Email Notifications** with templates

### API Endpoints
- **Auth** (14 endpoints): Register, login, 2FA, password management, email verification
- **Users** (9 endpoints): Profile, admin management, suspension/activation
- **API Keys** (8 endpoints): CRUD, rotation, usage tracking
- **Webhooks** (11 endpoints): CRUD, delivery tracking, testing, retry
- **Subscriptions** (15 endpoints): Plans, billing, payments, invoices, credits
- **Admin** (15+ endpoints): Dashboard, analytics, system management, monitoring
- **WebSocket** (3 endpoints): Real-time updates, analytics streaming, organization chat

## 📋 Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- (Optional) Celery worker for background tasks

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/lct1407/rental-api.git
cd rental-api/backend
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and configure:

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/rentapi

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Payment Providers
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
PAYPAL_CLIENT_ID=your_paypal_client_id
PAYPAL_CLIENT_SECRET=your_paypal_secret

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Celery
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
```

### 5. Initialize Database

```bash
# Run migrations
alembic upgrade head

# Seed sample data (optional, for development)
python scripts/seed_data.py
```

## 🚀 Running the Application

### Development Mode

```bash
# Start FastAPI server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### With Background Tasks

```bash
# Terminal 1: Start FastAPI
uvicorn app.main:app --reload

# Terminal 2: Start Celery worker
celery -A app.core.celery_app worker --loglevel=info

# Terminal 3: Start Celery beat (periodic tasks)
celery -A app.core.celery_app beat --loglevel=info
```

### Access Points

- **API Documentation**: http://localhost:8000/docs
- **Alternative Docs**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## 📖 API Documentation

### Authentication

#### Register
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "johndoe",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### Use Access Token
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### API Keys

#### Create API Key
```bash
curl -X POST http://localhost:8000/api/v1/api-keys \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Key",
    "description": "Main production API key",
    "scopes": ["read:*", "write:*"],
    "rate_limit_per_hour": 10000
  }'
```

#### Use API Key
```bash
curl -X GET http://localhost:8000/api/v1/users/me \
  -H "X-API-Key: sk_abc123..."
```

### WebSocket

#### Connect to Real-time Updates
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/realtime?token=YOUR_JWT_TOKEN');

ws.onopen = () => {
  // Subscribe to events
  ws.send(JSON.stringify({
    action: 'subscribe',
    events: ['api_call', 'payment', 'webhook_delivery']
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

## 🗃️ Database Schema

### Key Tables
- **users** - User accounts with roles, 2FA, credits
- **organizations** - Multi-tenant organizations
- **organization_members** - Organization membership
- **api_keys** - API keys with scopes and rate limits
- **webhooks** - Webhook configurations
- **webhook_deliveries** - Delivery tracking with retry
- **subscriptions** - Subscription plans
- **payments** - Payment records (Stripe + PayPal)
- **invoices** - Billing invoices
- **credit_transactions** - Credit balance tracking
- **api_usage_logs** - API call analytics
- **audit_logs** - Audit trail
- **security_events** - Security monitoring

All tables use **incremental bigint IDs** (NOT UUID).

## 🔐 Security Features

### Authentication & Authorization
- JWT tokens with blacklisting
- Refresh token rotation
- TOTP 2FA with backup codes
- Password hashing with bcrypt
- Role-based access control (RBAC)

### API Security
- Rate limiting (Redis-backed)
- IP whitelisting for API keys
- CORS protection
- Security headers (HSTS, CSP, etc.)
- Input validation with Pydantic
- SQL injection protection

### Audit & Monitoring
- Complete audit logging
- Security event tracking
- Failed login detection
- Account lockout after failed attempts

## 📊 Background Tasks (Celery)

### Periodic Tasks
- **Every 5 minutes**: Retry failed webhooks
- **Every hour**: Aggregate analytics
- **Daily**: Check expiring subscriptions, renew subscriptions, generate reports
- **Weekly**: Clean up old logs
- **Monthly**: Check inactive API keys

### Task Queues
- `webhooks` - Webhook delivery
- `emails` - Email notifications
- `analytics` - Analytics processing
- `subscriptions` - Subscription management
- `maintenance` - System maintenance

## 🧪 Testing

### Test Credentials (from seed data)

**Super Admin:**
- Email: `admin@example.com`
- Password: `Admin123!@#`

**Regular Users:**
- Email: `john@acme.com`, `jane@startup.io`, `bob@freelance.dev`
- Password: `User123!@#`

**Admin:**
- Email: `alice@enterprise.com`
- Password: `User123!@#`

### Running Tests

```bash
# Install test dependencies
pip install -r requirements-dev.txt

# Run tests
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## 📦 Project Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── dependencies.py       # Common dependencies
│   │   └── v1/
│   │       ├── auth.py           # Auth endpoints
│   │       ├── users.py          # User endpoints
│   │       ├── api_keys.py       # API key endpoints
│   │       ├── webhooks.py       # Webhook endpoints
│   │       ├── subscriptions.py  # Billing endpoints
│   │       ├── admin.py          # Admin endpoints
│   │       └── websocket.py      # WebSocket endpoints
│   ├── core/
│   │   ├── security.py           # JWT, 2FA, hashing
│   │   ├── permissions.py        # RBAC system
│   │   ├── cache.py              # Redis caching
│   │   ├── middleware.py         # Rate limiting, logging
│   │   ├── celery_app.py         # Celery configuration
│   │   └── websocket.py          # WebSocket manager
│   ├── models/                   # SQLAlchemy models
│   ├── schemas/                  # Pydantic schemas
│   ├── services/                 # Business logic
│   ├── tasks/                    # Celery tasks
│   ├── config.py                 # Configuration
│   ├── database.py               # Database setup
│   └── main.py                   # FastAPI app
├── migrations/                   # Alembic migrations
├── scripts/
│   └── seed_data.py              # Database seeding
├── tests/                        # Test suite
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `REDIS_URL` | Redis connection string | Required |
| `SECRET_KEY` | JWT secret key | Required |
| `ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry | 30 |
| `ALLOWED_ORIGINS` | CORS allowed origins | * |
| `STRIPE_SECRET_KEY` | Stripe API key | Optional |
| `PAYPAL_CLIENT_ID` | PayPal client ID | Optional |
| `MAIL_SERVER` | SMTP server | Optional |

## 📈 Performance

### Optimizations
- Redis caching with TTL
- Database query optimization with indexes
- Connection pooling
- Async I/O with asyncpg
- Code splitting for webhooks, emails
- Rate limiting to prevent abuse

### Monitoring
- Request logging middleware
- Response time tracking
- Error rate monitoring
- System health checks
- Database connection pool stats

## 🚢 Deployment

### Production Checklist
- [ ] Change `SECRET_KEY` to strong random value
- [ ] Set `DEBUG=False`
- [ ] Configure production `DATABASE_URL`
- [ ] Set up Redis cluster
- [ ] Configure proper `ALLOWED_ORIGINS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure payment provider keys
- [ ] Set up email SMTP
- [ ] Run database migrations
- [ ] Set up Celery workers
- [ ] Configure monitoring (Sentry, etc.)
- [ ] Set up backups
- [ ] Configure logging

### Docker (Optional)

```bash
# Build image
docker build -t rentapi-backend .

# Run container
docker run -p 8000:8000 --env-file .env rentapi-backend
```

## 📝 API Rate Limits

### Default Limits
- **Free Tier**: 100 requests/hour, 1,000/day
- **Basic**: 1,000 requests/hour, 10,000/day
- **Pro**: 10,000 requests/hour, 100,000/day
- **Enterprise**: 50,000 requests/hour, 500,000/day

Rate limits are enforced per API key and tracked in Redis.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Write/update tests
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

- **Documentation**: http://localhost:8000/docs
- **Issues**: https://github.com/lct1407/rental-api/issues

## 🎯 Roadmap

- [ ] GraphQL API support
- [ ] Additional payment providers
- [ ] Advanced analytics dashboard
- [ ] API versioning
- [ ] Rate limit customization per endpoint
- [ ] API marketplace features
- [ ] Developer portal
- [ ] SDK generation

---

**Built with FastAPI, PostgreSQL, Redis, and Celery**
