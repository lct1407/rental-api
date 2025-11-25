"""
Custom middleware for the application
Includes rate limiting, logging, and request tracking
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import uuid
from typing import Callable
import structlog

from app.core.cache import RedisCache
from app.config import settings


logger = structlog.get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis
    Implements token bucket algorithm
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/health/ready", "/metrics"]:
            return await call_next(request)

        # Get client identifier
        client_id = self._get_client_id(request)

        # Check rate limit
        try:
            await self._check_rate_limit(client_id, request.url.path)
        except HTTPException as e:
            return Response(
                content=str(e.detail),
                status_code=e.status_code,
                headers={"X-RateLimit-Exceeded": "true"}
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = await self._get_remaining(client_id)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _get_client_id(self, request: Request) -> str:
        """Get client identifier (API key, user ID, or IP)"""
        # Try API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"api_key:{api_key}"

        # Try authenticated user
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"

        # Fall back to IP
        client_ip = request.client.host
        return f"ip:{client_ip}"

    async def _check_rate_limit(self, client_id: str, path: str):
        """Check if client has exceeded rate limit"""
        # Different limits for different paths
        if path.startswith("/api/v1/admin"):
            limit = settings.RATE_LIMIT_PER_MINUTE * 2  # Higher limit for admin
        else:
            limit = settings.RATE_LIMIT_PER_MINUTE

        # Check Redis - use raw integer storage for atomic increment
        key = f"rate_limit:{client_id}:minute"

        try:
            redis = await RedisCache.get_redis()

            # Use INCR which atomically increments and returns the new value
            # If key doesn't exist, it's set to 0 before incrementing
            current = await redis.incr(key)

            # Set expiration on first request (when current == 1)
            if current == 1:
                await redis.expire(key, 60)

            if current > limit:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Please try again later."
                )
        except HTTPException:
            raise
        except Exception as e:
            # If Redis is unavailable, log and allow the request (fail open)
            logger.warning(f"Rate limiting unavailable (Redis error): {e}")

    async def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client"""
        key = f"rate_limit:{client_id}:minute"
        try:
            redis = await RedisCache.get_redis()
            current = await redis.get(key)
            if current is None:
                return settings.RATE_LIMIT_PER_MINUTE
            return max(0, settings.RATE_LIMIT_PER_MINUTE - int(current))
        except Exception:
            # If Redis is unavailable, return full limit
            return settings.RATE_LIMIT_PER_MINUTE


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Logging middleware to log all requests and responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id

        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            "request_started",
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host,
        )

        # Process request
        try:
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                "request_completed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration=f"{duration:.3f}s",
            )

            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                duration=f"{duration:.3f}s",
            )

            raise


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """
    Additional CORS security checks
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        origin = request.headers.get("origin")

        # Check if origin is allowed
        if origin and origin not in settings.ALLOWED_ORIGINS:
            logger.warning(
                "cors_violation",
                origin=origin,
                path=request.url.path,
                client_ip=request.client.host,
            )

        return await call_next(request)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add security headers to all responses
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        return response


class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    IP whitelist middleware for API keys
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get API key from header
        api_key = request.headers.get("X-API-Key")

        if api_key:
            # Check IP whitelist
            from app.services.api_key_service import ApiKeyService
            from app.database import get_db

            # This is a simplified version - in production, cache this
            # api_key_record = await ApiKeyService.get_by_key(api_key)

            # if api_key_record and api_key_record.ip_whitelist:
            #     client_ip = request.client.host
            #     if client_ip not in api_key_record.ip_whitelist:
            #         raise HTTPException(
            #             status_code=status.HTTP_403_FORBIDDEN,
            #             detail="IP address not whitelisted for this API key"
            #         )

            pass  # Implement IP whitelist check

        return await call_next(request)


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Limit request body size to prevent memory exhaustion
    """

    MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10MB

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_length = request.headers.get("content-length")

        if content_length and int(content_length) > self.MAX_REQUEST_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Request body too large. Maximum size is {self.MAX_REQUEST_SIZE / 1024 / 1024}MB"
            )

        return await call_next(request)
