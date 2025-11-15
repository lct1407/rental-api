"""
OpenAPI Configuration and Customization
Comprehensive Swagger documentation setup for the API Management Platform
"""
from typing import Dict, Any
from app.config import settings


def get_openapi_tags() -> list[Dict[str, Any]]:
    """
    Define OpenAPI tags with descriptions for better organization
    """
    return [
        {
            "name": "System",
            "description": "System health checks and API information endpoints"
        },
        {
            "name": "Authentication",
            "description": """
            User authentication and authorization endpoints including:
            - User registration and login
            - Two-factor authentication (TOTP)
            - Password management (reset, change)
            - Token management (refresh, logout)
            - Email verification
            """
        },
        {
            "name": "Users",
            "description": """
            User profile management endpoints:
            - View and update user profiles
            - User statistics and usage metrics
            - Account deletion (soft delete)
            - Admin user management (list, suspend, activate)
            - Credit management
            """
        },
        {
            "name": "API Keys",
            "description": """
            API key management for programmatic access:
            - Create and manage API keys
            - Key rotation and expiration
            - Scope-based permissions
            - IP whitelisting
            - Usage tracking per key
            - Key activation/deactivation
            """
        },
        {
            "name": "Webhooks",
            "description": """
            Webhook management for real-time event notifications:
            - Create and configure webhooks
            - Event type subscriptions
            - Delivery retry logic
            - Webhook security (signatures)
            - Delivery logs and monitoring
            - Test webhook endpoints
            """
        },
        {
            "name": "Subscriptions",
            "description": """
            Subscription and billing management:
            - View available subscription plans
            - Subscribe/upgrade/downgrade plans
            - Payment processing (Stripe & PayPal)
            - Credit purchases and management
            - Billing history
            - Invoice generation
            - Payment method management
            """
        },
        {
            "name": "Admin",
            "description": """
            Administrative endpoints (admin role required):
            - System analytics and metrics
            - User management (all users)
            - Subscription management
            - API key oversight
            - Webhook monitoring
            - Activity logs and audit trails
            - System configuration
            """
        },
        {
            "name": "WebSocket",
            "description": """
            Real-time WebSocket connections:
            - Live notifications
            - Real-time analytics updates
            - System event streams
            """
        }
    ]


def get_openapi_metadata() -> Dict[str, Any]:
    """
    Get comprehensive OpenAPI metadata including contact, license, and external docs
    """
    return {
        "title": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": """
# 🚀 Enterprise API Management Platform

A comprehensive, production-ready API management solution with advanced features for modern SaaS applications.

## 🎯 Key Features

### Authentication & Security
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Two-Factor Authentication (2FA)**: TOTP-based 2FA for enhanced security
- **Role-Based Access Control (RBAC)**: Granular permission system
- **Password Security**: Bcrypt hashing with strength requirements
- **Token Blacklisting**: Secure logout and token revocation
- **IP Whitelisting**: Restrict API key access by IP address

### API Key Management
- **Multiple API Keys**: Create unlimited API keys per user
- **Scope-Based Permissions**: Fine-grained access control
- **Key Rotation**: Built-in key expiration and rotation
- **Usage Tracking**: Monitor API calls per key
- **Rate Limiting**: Per-key and per-user rate limits

### Webhooks & Events
- **Real-time Notifications**: Instant event delivery
- **Automatic Retries**: Configurable retry logic with exponential backoff
- **Event Filtering**: Subscribe to specific event types
- **Secure Delivery**: HMAC signature verification
- **Delivery Logs**: Complete webhook delivery history

### Billing & Subscriptions
- **Multi-Gateway Support**: Stripe and PayPal integration
- **Flexible Plans**: Free, Basic, Pro, and Enterprise tiers
- **Credit System**: Pay-as-you-go credit-based billing
- **Automated Invoicing**: PDF invoice generation
- **Payment History**: Complete transaction records

### Analytics & Monitoring
- **Real-time Metrics**: Live usage statistics
- **Historical Data**: TimescaleDB for time-series analytics
- **User Analytics**: Per-user usage tracking
- **System Monitoring**: Health checks and performance metrics
- **Audit Logs**: Complete activity trail

### Performance & Scalability
- **Redis Caching**: Fast response times with intelligent caching
- **Rate Limiting**: Protect against abuse
- **Async Processing**: Celery for background tasks
- **Database Optimization**: Connection pooling and query optimization
- **Compression**: GZip compression for responses

### Developer Experience
- **OpenAPI/Swagger**: Auto-generated interactive API documentation
- **ReDoc**: Alternative documentation interface
- **WebSocket Support**: Real-time bidirectional communication
- **Comprehensive Error Messages**: Detailed validation errors
- **Pagination**: Standardized pagination across all list endpoints

## 🏗️ Architecture

- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL with TimescaleDB extension
- **Cache**: Redis
- **Message Queue**: RabbitMQ + Celery
- **Payment**: Stripe & PayPal
- **Storage**: AWS S3 / MinIO compatible
- **Monitoring**: Prometheus + Grafana ready

## 📚 API Versioning

Current version: **v1**

All endpoints are prefixed with `/api/v1/`

## 🔐 Authentication

Most endpoints require authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your_access_token>
```

### Getting Started

1. **Register** a new account: `POST /api/v1/auth/register`
2. **Login** to get tokens: `POST /api/v1/auth/login`
3. **Use** the access token in subsequent requests
4. **Refresh** tokens before expiry: `POST /api/v1/auth/refresh`

## 📊 Rate Limits

Default rate limits (configurable per API key):
- **Per Minute**: 60 requests
- **Per Hour**: 1,000 requests
- **Per Day**: 10,000 requests

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Total requests allowed
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Time when limit resets

## 🎫 Support

- **Documentation**: [API Docs](/docs)
- **Alternative Docs**: [ReDoc](/redoc)
- **Status Page**: [Health Check](/health)

## 📝 License

This API is proprietary software. Unauthorized use is prohibited.

---

**Environment**: {environment}
**Version**: {version}
**Powered by**: FastAPI
        """.format(environment=settings.ENVIRONMENT, version=settings.APP_VERSION),
        "contact": {
            "name": "API Support Team",
            "url": "https://api-management-platform.com/support",
            "email": "support@api-management-platform.com"
        },
        "license_info": {
            "name": "Proprietary License",
            "url": "https://api-management-platform.com/license"
        },
        "termsOfService": "https://api-management-platform.com/terms",
    }


def get_openapi_security_schemes() -> Dict[str, Any]:
    """
    Define security schemes for OpenAPI documentation
    """
    return {
        "Bearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": """
            JWT Authentication

            To authenticate:
            1. Login via `/api/v1/auth/login` to get an access token
            2. Include the token in the Authorization header: `Bearer <token>`
            3. Refresh the token using `/api/v1/auth/refresh` before it expires

            Access tokens expire in 30 minutes.
            Refresh tokens expire in 7 days.
            """
        },
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": """
            API Key Authentication

            For programmatic access without user login:
            1. Create an API key via `/api/v1/api-keys/`
            2. Include the key in requests: `X-API-Key: <your_api_key>`

            API keys can have custom scopes and IP restrictions.
            """
        }
    }


def get_openapi_servers() -> list[Dict[str, Any]]:
    """
    Define available API servers/environments
    """
    servers = []

    if settings.ENVIRONMENT == "production":
        servers.append({
            "url": "https://api.example.com",
            "description": "Production server"
        })
    elif settings.ENVIRONMENT == "staging":
        servers.append({
            "url": "https://staging-api.example.com",
            "description": "Staging server"
        })
    else:
        servers.append({
            "url": f"http://localhost:{settings.PORT}",
            "description": "Development server"
        })

    return servers


def get_openapi_external_docs() -> Dict[str, str]:
    """
    Link to external documentation
    """
    return {
        "description": "Complete API Documentation & Guides",
        "url": "https://docs.api-management-platform.com"
    }


def customize_openapi_schema(openapi_schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Customize the generated OpenAPI schema with additional metadata
    """
    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = get_openapi_security_schemes()

    # Add servers
    openapi_schema["servers"] = get_openapi_servers()

    # Add external documentation
    openapi_schema["externalDocs"] = get_openapi_external_docs()

    # Add security requirement globally (can be overridden per endpoint)
    # openapi_schema["security"] = [{"Bearer": []}, {"ApiKeyAuth": []}]

    # Enhance schema descriptions
    if "components" in openapi_schema and "schemas" in openapi_schema["components"]:
        schemas = openapi_schema["components"]["schemas"]

        # Add examples to common error responses
        if "HTTPValidationError" in schemas:
            schemas["HTTPValidationError"]["example"] = {
                "detail": [
                    {
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address",
                        "type": "value_error.email"
                    }
                ]
            }

    return openapi_schema


# Response examples for common scenarios
RESPONSE_EXAMPLES = {
    "success_200": {
        "description": "Successful Response",
        "content": {
            "application/json": {
                "example": {"message": "Operation completed successfully"}
            }
        }
    },
    "created_201": {
        "description": "Resource Created",
        "content": {
            "application/json": {
                "example": {
                    "id": 1,
                    "message": "Resource created successfully",
                    "created_at": "2025-01-15T10:30:00Z"
                }
            }
        }
    },
    "unauthorized_401": {
        "description": "Authentication Required",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Not authenticated. Please provide a valid access token."
                }
            }
        }
    },
    "forbidden_403": {
        "description": "Insufficient Permissions",
        "content": {
            "application/json": {
                "example": {
                    "detail": "You don't have permission to perform this action"
                }
            }
        }
    },
    "not_found_404": {
        "description": "Resource Not Found",
        "content": {
            "application/json": {
                "example": {
                    "detail": "The requested resource was not found"
                }
            }
        }
    },
    "validation_422": {
        "description": "Validation Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Validation error",
                    "errors": [
                        {
                            "field": "email",
                            "message": "value is not a valid email address",
                            "type": "value_error.email"
                        }
                    ]
                }
            }
        }
    },
    "rate_limit_429": {
        "description": "Rate Limit Exceeded",
        "content": {
            "application/json": {
                "example": {
                    "detail": "Rate limit exceeded. Please try again later.",
                    "retry_after": 60
                }
            }
        }
    },
    "server_error_500": {
        "description": "Internal Server Error",
        "content": {
            "application/json": {
                "example": {
                    "detail": "An unexpected error occurred. Please contact support if this persists."
                }
            }
        }
    }
}
