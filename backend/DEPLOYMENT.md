# RentAPI Deployment Guide

Complete guide for deploying the RentAPI backend to production.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Database Setup](#database-setup)
- [Redis Setup](#redis-setup)
- [Application Deployment](#application-deployment)
- [Celery Workers](#celery-workers)
- [Nginx Configuration](#nginx-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Monitoring](#monitoring)
- [Backup Strategy](#backup-strategy)

---

## Prerequisites

### Server Requirements
- Ubuntu 22.04 LTS (recommended)
- 2+ CPU cores
- 4GB+ RAM
- 20GB+ storage
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx 1.18+

### Domain Setup
- Domain name configured (e.g., api.yourdomain.com)
- DNS A record pointing to server IP

---

## Environment Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Python and build tools
sudo apt install -y python3.11 python3.11-venv python3-pip build-essential

# PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Redis
sudo apt install -y redis-server

# Nginx
sudo apt install -y nginx

# Supervisor (for process management)
sudo apt install -y supervisor

# Other tools
sudo apt install -y git curl wget
```

### 3. Create Application User

```bash
sudo useradd -m -s /bin/bash rentapi
sudo su - rentapi
```

### 4. Clone Repository

```bash
cd /home/rentapi
git clone https://github.com/lct1407/rental-api.git
cd rental-api/backend
```

### 5. Setup Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

---

## Database Setup

### 1. Create PostgreSQL Database

```bash
sudo -u postgres psql

-- In PostgreSQL prompt:
CREATE DATABASE rentapi;
CREATE USER rentapi_user WITH PASSWORD 'STRONG_PASSWORD_HERE';
ALTER ROLE rentapi_user SET client_encoding TO 'utf8';
ALTER ROLE rentapi_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE rentapi_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE rentapi TO rentapi_user;

-- PostgreSQL 15+ requires additional grant
\c rentapi
GRANT ALL ON SCHEMA public TO rentapi_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO rentapi_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO rentapi_user;

\q
```

### 2. Configure PostgreSQL for Production

Edit `/etc/postgresql/15/main/postgresql.conf`:

```conf
# Connection Settings
max_connections = 100
shared_buffers = 256MB

# Write Ahead Log
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query Tuning
effective_cache_size = 1GB
random_page_cost = 1.1

# Logging
logging_collector = on
log_directory = 'log'
log_filename = 'postgresql-%Y-%m-%d_%H%M%S.log'
log_rotation_age = 1d
log_rotation_size = 100MB
```

Restart PostgreSQL:
```bash
sudo systemctl restart postgresql
```

### 3. Run Database Migrations

```bash
cd /home/rentapi/rental-api/backend
source venv/bin/activate
alembic upgrade head
```

---

## Redis Setup

### 1. Configure Redis

Edit `/etc/redis/redis.conf`:

```conf
# Bind to localhost only (if on same server)
bind 127.0.0.1

# Set password
requirepass YOUR_REDIS_PASSWORD

# Persistence
save 900 1
save 300 10
save 60 10000

# Memory
maxmemory 256mb
maxmemory-policy allkeys-lru

# Security
protected-mode yes
```

### 2. Restart Redis

```bash
sudo systemctl restart redis
sudo systemctl enable redis
```

### 3. Test Redis Connection

```bash
redis-cli
AUTH YOUR_REDIS_PASSWORD
PING
# Should return PONG
```

---

## Application Deployment

### 1. Create Production Environment File

```bash
cd /home/rentapi/rental-api/backend
nano .env.production
```

```env
# Application
APP_NAME=RentAPI
ENVIRONMENT=production
DEBUG=False
PORT=8000

# Security
SECRET_KEY=GENERATE_STRONG_SECRET_KEY_HERE_AT_LEAST_32_CHARS
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Database
DATABASE_URL=postgresql+asyncpg://rentapi_user:STRONG_PASSWORD_HERE@localhost:5432/rentapi

# Redis
REDIS_URL=redis://:YOUR_REDIS_PASSWORD@localhost:6379/0
REDIS_PASSWORD=YOUR_REDIS_PASSWORD
REDIS_DB=0

# CORS
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Payment Providers
STRIPE_SECRET_KEY=sk_live_YOUR_STRIPE_SECRET_KEY
STRIPE_PUBLISHABLE_KEY=pk_live_YOUR_STRIPE_PUBLISHABLE_KEY
PAYPAL_CLIENT_ID=YOUR_PAYPAL_CLIENT_ID
PAYPAL_CLIENT_SECRET=YOUR_PAYPAL_SECRET
PAYPAL_MODE=live

# Email
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@yourdomain.com
MAIL_FROM_NAME=RentAPI

# Celery
CELERY_BROKER_URL=redis://:YOUR_REDIS_PASSWORD@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:YOUR_REDIS_PASSWORD@localhost:6379/2
```

### 2. Secure Environment File

```bash
chmod 600 .env.production
```

### 3. Create Systemd Service for FastAPI

```bash
sudo nano /etc/systemd/system/rentapi.service
```

```ini
[Unit]
Description=RentAPI FastAPI Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=rentapi
Group=rentapi
WorkingDirectory=/home/rentapi/rental-api/backend
Environment="PATH=/home/rentapi/rental-api/backend/venv/bin"
EnvironmentFile=/home/rentapi/rental-api/backend/.env.production
ExecStart=/home/rentapi/rental-api/backend/venv/bin/uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --workers 4 \
    --loop uvloop \
    --log-level info \
    --access-log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 4. Start and Enable Service

```bash
sudo systemctl daemon-reload
sudo systemctl start rentapi
sudo systemctl enable rentapi
sudo systemctl status rentapi
```

---

## Celery Workers

### 1. Create Celery Worker Service

```bash
sudo nano /etc/systemd/system/rentapi-celery.service
```

```ini
[Unit]
Description=RentAPI Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=rentapi
Group=rentapi
WorkingDirectory=/home/rentapi/rental-api/backend
Environment="PATH=/home/rentapi/rental-api/backend/venv/bin"
EnvironmentFile=/home/rentapi/rental-api/backend/.env.production
ExecStart=/home/rentapi/rental-api/backend/venv/bin/celery -A app.core.celery_app worker \
    --loglevel=info \
    --concurrency=4 \
    --pidfile=/var/run/celery/worker.pid \
    --logfile=/var/log/celery/worker.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 2. Create Celery Beat Service (Periodic Tasks)

```bash
sudo nano /etc/systemd/system/rentapi-celery-beat.service
```

```ini
[Unit]
Description=RentAPI Celery Beat
After=network.target redis.service

[Service]
Type=simple
User=rentapi
Group=rentapi
WorkingDirectory=/home/rentapi/rental-api/backend
Environment="PATH=/home/rentapi/rental-api/backend/venv/bin"
EnvironmentFile=/home/rentapi/rental-api/backend/.env.production
ExecStart=/home/rentapi/rental-api/backend/venv/bin/celery -A app.core.celery_app beat \
    --loglevel=info \
    --pidfile=/var/run/celery/beat.pid \
    --logfile=/var/log/celery/beat.log
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 3. Create Log Directories

```bash
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown rentapi:rentapi /var/log/celery /var/run/celery
```

### 4. Start Celery Services

```bash
sudo systemctl daemon-reload
sudo systemctl start rentapi-celery
sudo systemctl start rentapi-celery-beat
sudo systemctl enable rentapi-celery
sudo systemctl enable rentapi-celery-beat
```

---

## Nginx Configuration

### 1. Create Nginx Site Configuration

```bash
sudo nano /etc/nginx/sites-available/rentapi
```

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

upstream rentapi_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    listen [::]:80;
    server_name api.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name api.yourdomain.com;

    # SSL Configuration (will be set up with certbot)
    ssl_certificate /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/rentapi-access.log;
    error_log /var/log/nginx/rentapi-error.log;

    # Max upload size
    client_max_body_size 10M;

    # API endpoints
    location / {
        # Rate limiting
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://rentapi_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # WebSocket support
    location /api/v1/ws {
        proxy_pass http://rentapi_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket timeouts
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;
    }

    # Health check (don't rate limit)
    location /health {
        proxy_pass http://rentapi_backend;
        access_log off;
    }
}
```

### 2. Enable Site and Test Configuration

```bash
sudo ln -s /etc/nginx/sites-available/rentapi /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/TLS Setup

### 1. Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 2. Obtain SSL Certificate

```bash
sudo certbot --nginx -d api.yourdomain.com
```

Follow the prompts. Certbot will automatically configure SSL in Nginx.

### 3. Auto-Renewal

Certbot automatically sets up renewal. Test it:

```bash
sudo certbot renew --dry-run
```

---

## Monitoring

### 1. Application Logs

```bash
# FastAPI logs
sudo journalctl -u rentapi -f

# Celery worker logs
sudo tail -f /var/log/celery/worker.log

# Celery beat logs
sudo tail -f /var/log/celery/beat.log

# Nginx access logs
sudo tail -f /var/log/nginx/rentapi-access.log

# Nginx error logs
sudo tail -f /var/log/nginx/rentapi-error.log
```

### 2. System Monitoring

Install monitoring tools:

```bash
sudo apt install -y htop iotop nethogs
```

### 3. Application Monitoring (Optional)

Set up Sentry for error tracking:

```bash
pip install sentry-sdk[fastapi]
```

Add to `app/main.py`:

```python
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration

sentry_sdk.init(
    dsn="YOUR_SENTRY_DSN",
    integrations=[FastApiIntegration()],
    environment="production"
)
```

---

## Backup Strategy

### 1. Database Backup Script

```bash
sudo nano /usr/local/bin/backup-rentapi-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/var/backups/rentapi"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Backup database
pg_dump -U rentapi_user -h localhost rentapi | gzip > $BACKUP_DIR/rentapi_db_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "rentapi_db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/rentapi_db_$DATE.sql.gz"
```

```bash
sudo chmod +x /usr/local/bin/backup-rentapi-db.sh
```

### 2. Schedule Daily Backups

```bash
sudo crontab -e
```

Add:
```
0 2 * * * /usr/local/bin/backup-rentapi-db.sh
```

### 3. Application Files Backup

```bash
# Backup application files
sudo tar -czf /var/backups/rentapi/app_$(date +%Y%m%d).tar.gz \
    /home/rentapi/rental-api/backend \
    --exclude=venv \
    --exclude=__pycache__
```

---

## Security Checklist

- [ ] Change all default passwords
- [ ] Use strong SECRET_KEY (32+ characters)
- [ ] Enable firewall (ufw)
- [ ] Configure PostgreSQL to accept only local connections
- [ ] Set up Redis password
- [ ] Use HTTPS only (SSL certificate)
- [ ] Set DEBUG=False
- [ ] Configure proper CORS origins
- [ ] Enable rate limiting
- [ ] Set up fail2ban for brute force protection
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Set up database backups
- [ ] Use environment variables for secrets
- [ ] Enable audit logging

---

## Firewall Configuration

```bash
# Enable UFW
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status
```

---

## Performance Tuning

### 1. Uvicorn Workers

Adjust workers in systemd service based on CPU cores:
```
--workers $(nproc)
```

### 2. PostgreSQL Connection Pool

In `.env.production`:
```env
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/db?pool_size=20&max_overflow=0
```

### 3. Redis Configuration

Adjust `maxmemory` based on available RAM in `/etc/redis/redis.conf`.

---

## Troubleshooting

### Service Not Starting

```bash
# Check service status
sudo systemctl status rentapi

# Check logs
sudo journalctl -u rentapi -n 100 --no-pager
```

### Database Connection Issues

```bash
# Test database connection
psql -U rentapi_user -h localhost -d rentapi
```

### Redis Connection Issues

```bash
# Test Redis
redis-cli -a YOUR_REDIS_PASSWORD PING
```

### High Memory Usage

```bash
# Check memory usage
htop

# Restart services
sudo systemctl restart rentapi
sudo systemctl restart rentapi-celery
```

---

## Updating Application

```bash
# As rentapi user
cd /home/rentapi/rental-api
git pull origin main

# Activate venv
source backend/venv/bin/activate

# Install updated dependencies
pip install -r backend/requirements.txt

# Run migrations
cd backend
alembic upgrade head

# Restart services
sudo systemctl restart rentapi
sudo systemctl restart rentapi-celery
sudo systemctl restart rentapi-celery-beat
```

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/lct1407/rental-api/issues
- Documentation: https://api.yourdomain.com/docs

---

**Last Updated**: 2025-11-15
