"""
Custom exceptions for the application
"""
from fastapi import HTTPException, status


class AppException(HTTPException):
    """Base exception for application errors"""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: str = "INTERNAL_ERROR",
        headers: dict = None
    ):
        super().__init__(
            status_code=status_code,
            detail={
                "message": message,
                "error_code": error_code
            },
            headers=headers
        )
        self.message = message
        self.error_code = error_code


class InsufficientCreditsError(AppException):
    """Raised when user doesn't have enough credits"""

    def __init__(self, message: str = "Insufficient credits"):
        super().__init__(
            message=message,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            error_code="INSUFFICIENT_CREDITS"
        )


class RateLimitExceededError(AppException):
    """Raised when rate limit is exceeded"""

    def __init__(self, message: str = "Rate limit exceeded", headers: dict = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            error_code="RATE_LIMIT_EXCEEDED",
            headers=headers
        )


class ResourceNotFoundError(AppException):
    """Raised when a resource is not found"""

    def __init__(self, message: str = "Resource not found"):
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="RESOURCE_NOT_FOUND"
        )


class UnauthorizedError(AppException):
    """Raised when user is not authorized"""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="UNAUTHORIZED"
        )


class ForbiddenError(AppException):
    """Raised when user doesn't have permission"""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="FORBIDDEN"
        )


class ValidationError(AppException):
    """Raised when validation fails"""

    def __init__(self, message: str = "Validation error"):
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_code="VALIDATION_ERROR"
        )


class ConflictError(AppException):
    """Raised when there's a conflict"""

    def __init__(self, message: str = "Conflict"):
        super().__init__(
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            error_code="CONFLICT"
        )
