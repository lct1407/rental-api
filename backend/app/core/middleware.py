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

        # Check Redis
        key = f"rate_limit:{client_id}:minute"
        current = await RedisCache.get(key)

        if current is None:
            # First request
            await RedisCache.set(key, 1, expire=60)
            return

        if int(current) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )

        # Increment counter
        await RedisCache.incr(key)

    async def _get_remaining(self, client_id: str) -> int:
        """Get remaining requests for client"""
        key = f"rate_limit:{client_id}:minute"
        current = await RedisCache.get(key)
        if current is None:
            return settings.RATE_LIMIT_PER_MINUTE
        return max(0, settings.RATE_LIMIT_PER_MINUTE - int(current))


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


class CreditAndRateLimitHeadersMiddleware(BaseHTTPMiddleware):
    """
    Add credit balance and rate limit information to response headers
    Provides real-time credit and rate limit status to clients
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip for health checks and docs
        if request.url.path in ["/health", "/health/ready", "/metrics", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)

        # Track request start time
        start_time = time.time()

        # Get user info from request state (set by auth dependency)
        user_id = getattr(request.state, "user_id", None)
        api_key_id = getattr(request.state, "api_key_id", None)

        # Process request
        response = await call_next(request)

        # Add timing header
        duration_ms = (time.time() - start_time) * 1000
        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"

        # Add credit and rate limit headers if user is authenticated
        if user_id:
            try:
                # Get credit balance from cache first
                credit_balance = await RedisCache.get(f"credit_balance:{user_id}")

                if credit_balance is None:
                    # Fetch from database and cache
                    from app.services.credit_service import CreditService
                    from app.database import get_db_session

                    async with get_db_session() as db:
                        balance_data = await CreditService.get_credit_balance(
                            db, user_id, include_packages=False
                        )

                        credit_balance = balance_data.get("total_balance", 0)
                        monthly_balance = balance_data.get("monthly_balance", 0)
                        purchased_balance = balance_data.get("purchased_balance", 0)
                        next_reset = balance_data.get("next_monthly_reset", "")

                        # Cache for 5 minutes
                        await RedisCache.set(f"credit_balance:{user_id}", credit_balance, expire=300)
                        await RedisCache.set(f"credit_monthly:{user_id}", monthly_balance, expire=300)
                        await RedisCache.set(f"credit_purchased:{user_id}", purchased_balance, expire=300)
                        await RedisCache.set(f"credit_reset:{user_id}", next_reset, expire=300)
                else:
                    monthly_balance = await RedisCache.get(f"credit_monthly:{user_id}") or 0
                    purchased_balance = await RedisCache.get(f"credit_purchased:{user_id}") or 0
                    next_reset = await RedisCache.get(f"credit_reset:{user_id}") or ""

                # Add credit headers
                response.headers["X-Credits-Remaining"] = str(credit_balance)
                response.headers["X-Credits-Monthly"] = str(monthly_balance)
                response.headers["X-Credits-Purchased"] = str(purchased_balance)
                response.headers["X-Credits-Reset"] = str(next_reset)

                # Get rate limit status from cache
                from app.services.rate_limiter import RateLimiter

                # Get current usage
                rpm_current = await RateLimiter._get_usage(user_id, "minute")
                rph_current = await RateLimiter._get_usage(user_id, "hour")
                rpd_current = await RateLimiter._get_usage(user_id, "day")
                rpm_current_month = await RateLimiter._get_usage(user_id, "month")

                # Get limits (these would be cached per user plan)
                limits_key = f"user_limits:{user_id}"
                cached_limits = await RedisCache.get(limits_key)

                if cached_limits:
                    import json
                    limits = json.loads(cached_limits)
                else:
                    # Fetch limits from database
                    from app.database import get_db_session

                    async with get_db_session() as db:
                        limits_dict = await RateLimiter._get_user_limits(db, user_id)

                        # Cache limits for 1 hour
                        await RedisCache.set(
                            limits_key,
                            json.dumps(limits_dict),
                            expire=3600
                        )
                        limits = limits_dict

                # Add rate limit headers
                rpm_limit = limits.get("rpm", 60)
                rph_limit = limits.get("rph", 1000)
                rpd_limit = limits.get("rpd", 10000)
                monthly_limit = limits.get("monthly", 300000)

                response.headers["X-RateLimit-Limit-RPM"] = str(rpm_limit)
                response.headers["X-RateLimit-Remaining-RPM"] = str(max(0, rpm_limit - rpm_current))
                response.headers["X-RateLimit-Limit-RPH"] = str(rph_limit)
                response.headers["X-RateLimit-Remaining-RPH"] = str(max(0, rph_limit - rph_current))
                response.headers["X-RateLimit-Limit-Daily"] = str(rpd_limit)
                response.headers["X-RateLimit-Remaining-Daily"] = str(max(0, rpd_limit - rpd_current))
                response.headers["X-RateLimit-Limit-Monthly"] = str(monthly_limit)
                response.headers["X-RateLimit-Remaining-Monthly"] = str(max(0, monthly_limit - rpm_current_month))

                # Add warnings if approaching limits
                if int(credit_balance) < 100:
                    response.headers["X-Credits-Warning"] = "Low credit balance"

                rpm_remaining = rpm_limit - rpm_current
                if rpm_remaining < rpm_limit * 0.1:  # Less than 10% remaining
                    response.headers["X-RateLimit-Warning"] = "Approaching rate limit"

            except Exception as e:
                # Log error but don't fail the request
                logger.error(
                    "failed_to_add_credit_headers",
                    user_id=user_id,
                    error=str(e)
                )

        return response
