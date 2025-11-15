# Requirements Organization

Python dependencies organized from base to advanced requirements.

## Structure

```
requirements/
├── base.txt              # Core dependencies (required)
├── advanced.txt          # Advanced features (optional)
├── requirements.txt      # Legacy all-in-one (deprecated)
├── requirements-dev.txt  # Development and testing tools
└── README.md            # This file
```

## Installation

### Option 1: Base Only (Minimal)

For basic API functionality:

```bash
pip install -r requirements/base.txt
```

**Includes:**
- FastAPI framework
- Database (SQLAlchemy, Alembic, AsyncPG)
- Authentication (JWT, bcrypt)
- Validation (Pydantic)
- HTTP client (httpx)

### Option 2: Base + Advanced (Full Production)

For all features:

```bash
pip install -r requirements/base.txt
pip install -r requirements/advanced.txt
```

**Advanced features include:**
- Redis caching and rate limiting
- Two-factor authentication (2FA)
- Background tasks (Celery)
- Email sending
- Payment processing (Stripe, PayPal)
- Cloud storage (AWS S3)
- WebSocket support
- Monitoring and tracing
- PDF generation and reporting

### Option 3: Development

Base + Advanced + Dev tools:

```bash
pip install -r requirements/base.txt
pip install -r requirements/advanced.txt
pip install -r requirements/requirements-dev.txt
```

## Advanced Features by Category

The `advanced.txt` file is organized with clear section comments:

1. **REDIS** - Caching and rate limiting
2. **AUTHENTICATION** - 2FA and phone validation
3. **BACKGROUND TASKS** - Celery workers
4. **EMAIL** - Email sending and templates
5. **PAYMENTS** - Stripe and PayPal integration
6. **STORAGE** - AWS S3 cloud storage
7. **WEBSOCKET** - Real-time communication
8. **MONITORING** - Prometheus, logging, tracing
9. **REPORTING** - PDF generation, data processing
10. **UTILITIES** - Additional production tools

## Usage Examples

**Local Development (minimal):**
```bash
pip install -r requirements/base.txt
pip install -r requirements/requirements-dev.txt
```

**API Server (without background tasks):**
```bash
pip install -r requirements/base.txt
# Then selectively install from advanced.txt (copy needed lines)
```

**Full Production:**
```bash
pip install -r requirements/base.txt
pip install -r requirements/advanced.txt
```

## Docker Optimization

```dockerfile
# Stage 1: Base
FROM python:3.11-slim as base
COPY requirements/base.txt .
RUN pip install -r base.txt

# Stage 2: Production
FROM base as production
COPY requirements/advanced.txt .
RUN pip install -r advanced.txt
```

## Selective Installation

You can install only specific features from `advanced.txt` by copying relevant sections:

```bash
# Install base
pip install -r requirements/base.txt

# Install only Redis (copy from advanced.txt REDIS section)
pip install redis==5.0.1 aioredis==2.0.1 limits==3.7.0 slowapi==0.1.9

# Install only Payments (copy from advanced.txt PAYMENTS section)
pip install stripe==7.12.0 paypalrestsdk==1.13.1
```

## Migration from Legacy

Old `requirements.txt` is deprecated:

```bash
# Old (deprecated)
pip install -r requirements/requirements.txt

# New (recommended)
pip install -r requirements/base.txt
pip install -r requirements/advanced.txt
```

## Security & Updates

Run security audits:

```bash
pip install safety
safety check -r requirements/base.txt
safety check -r requirements/advanced.txt
```

## Version Pinning

All dependencies are pinned to specific versions for reproducible builds.
