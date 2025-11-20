"""
Common Pydantic schemas and base classes
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Any, List, Dict, Generic, TypeVar
from datetime import datetime

# Type variable for generic pagination
T = TypeVar('T')


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        str_strip_whitespace=True,
        use_enum_values=True
    )


class TimestampSchema(BaseSchema):
    """Schema with timestamp fields"""
    created_at: datetime
    updated_at: datetime


class PaginationParams(BaseModel):
    """Pagination query parameters"""
    skip: int = Field(default=0, ge=0, description="Number of records to skip")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum number of records to return")


class PaginatedResponse(BaseSchema, Generic[T]):
    """Paginated response wrapper"""
    items: List[T]
    total: int
    skip: int
    limit: int
    has_more: bool

    @classmethod
    def create(cls, items: List[T], total: int, skip: int, limit: int):
        """Create paginated response"""
        return cls(
            items=items,
            total=total,
            skip=skip,
            limit=limit,
            has_more=(skip + len(items)) < total
        )


class SuccessResponse(BaseSchema):
    """Generic success response"""
    success: bool = True
    message: str
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseSchema):
    """Error response"""
    success: bool = False
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class MessageResponse(BaseSchema):
    """Simple message response"""
    message: str


class HealthResponse(BaseSchema):
    """Health check response"""
    status: str
    timestamp: datetime
    version: str
    database: Optional[str] = None
    redis: Optional[str] = None
