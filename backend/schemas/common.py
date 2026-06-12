"""
schemas/common.py - Shared Pydantic base models and utility schemas.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class BaseResponse(BaseModel):
    """Standard API response wrapper."""
    model_config = ConfigDict(from_attributes=True)


class HealthResponse(BaseResponse):
    status: str = "ok"
    version: str
    environment: str
    timestamp: datetime


class ErrorResponse(BaseResponse):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


class PaginationMeta(BaseResponse):
    total: int
    page: int
    per_page: int
    pages: int
