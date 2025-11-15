"""
Main FastAPI Application - Enterprise SaaS API Platform
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.database import engine, get_db
from app.core.middleware import (
    RateLimitMiddleware,
    LoggingMiddleware as RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
    CreditAndRateLimitHeadersMiddleware
)
from app.core.cache import RedisCache
from app.core.openapi_config import (
    get_openapi_tags,
    get_openapi_metadata,
    customize_openapi_schema
)

# Import API routers
from app.api.v1 import auth, users, api_keys, webhooks, subscriptions, admin, websocket
from app.api.v1 import credits, admin_credits


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info("=" * 80)
    logger.info(f"Starting {settings.APP_NAME}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")
    logger.info("=" * 80)

    # Initialize Redis connection
    try:
        await RedisCache.ping()
        logger.info("✓ Redis connection established")
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")

    # Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
        logger.info("✓ Database connection established")
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")

    logger.info(f"Server running at: http://0.0.0.0:{settings.PORT}")
    logger.info("API Documentation: http://0.0.0.0:{}/docs".format(settings.PORT))

    yield

    # Shutdown
    logger.info("Shutting down application...")

    # Close Redis connections
    try:
        await RedisCache.close()
        logger.info("✓ Redis connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing Redis: {e}")

    # Close database connections
    try:
        await engine.dispose()
        logger.info("✓ Database connections closed")
    except Exception as e:
        logger.error(f"✗ Error closing database: {e}")

    logger.info("Application shutdown complete")


# Get enhanced OpenAPI metadata
openapi_metadata = get_openapi_metadata()

# Create FastAPI app with enhanced OpenAPI configuration
app = FastAPI(
    title=openapi_metadata["title"],
    description=openapi_metadata["description"],
    version=openapi_metadata["version"],
    contact=openapi_metadata["contact"],
    license_info=openapi_metadata["license_info"],
    terms_of_service=openapi_metadata["termsOfService"],
    openapi_tags=get_openapi_tags(),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG
)


# Customize OpenAPI schema
def custom_openapi():
    """
    Generate and cache custom OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = app.openapi()
    app.openapi_schema = customize_openapi_schema(openapi_schema)
    return app.openapi_schema


# Override the default OpenAPI schema generator
app.openapi = custom_openapi


# ============================================================================
# Middleware Configuration
# ============================================================================

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"]
)

# GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Custom middleware (order matters - last added is executed first)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CreditAndRateLimitHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors
    """
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(x) for x in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle database errors
    """
    logger.error(f"Database error: {exc}")

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error occurred",
            "error": str(exc) if settings.DEBUG else "Internal server error"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Handle all other exceptions
    """
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An unexpected error occurred"
        }
    )


# ============================================================================
# API Routes
# ============================================================================

# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check():
    """
    Health check endpoint

    Returns the health status of the application.
    """
    # Check database
    db_healthy = True
    try:
        async with engine.begin() as conn:
            await conn.execute("SELECT 1")
    except Exception:
        db_healthy = False

    # Check Redis
    redis_healthy = True
    try:
        await RedisCache.ping()
    except Exception:
        redis_healthy = False

    # Determine overall status
    overall_healthy = db_healthy and redis_healthy

    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "services": {
            "database": "up" if db_healthy else "down",
            "redis": "up" if redis_healthy else "down"
        }
    }


# Root endpoint
@app.get("/", tags=["System"])
async def root():
    """
    Root endpoint

    Returns API information.
    """
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "documentation": "/docs",
        "api_version": "v1",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "api_keys": "/api/v1/api-keys",
            "webhooks": "/api/v1/webhooks",
            "subscriptions": "/api/v1/subscriptions",
            "credits": "/api/v1/credits",
            "admin": "/api/v1/admin",
            "admin_credits": "/api/v1/admin/credits",
            "websocket": "/api/v1/ws"
        }
    }


# Register API v1 routes
api_v1_prefix = "/api/v1"

app.include_router(auth.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(api_keys.router, prefix=api_v1_prefix)
app.include_router(webhooks.router, prefix=api_v1_prefix)
app.include_router(subscriptions.router, prefix=api_v1_prefix)
app.include_router(credits.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)
app.include_router(admin_credits.router, prefix=api_v1_prefix)
app.include_router(websocket.router, prefix=api_v1_prefix)


# ============================================================================
# Startup Message
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
