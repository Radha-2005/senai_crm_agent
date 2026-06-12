"""
api/status.py - Status and health check endpoints.
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from backend.config import settings
from backend.db.session import get_db
from backend.rag.rag_service import get_kb_stats
from backend.schemas.common import HealthResponse

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check endpoint",
)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Returns application health status including DB connectivity."""
    # Test DB connection
    try:
        await db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    kb_stats = get_kb_stats()

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=settings.APP_VERSION,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.utcnow(),
    )


@router.get(
    "/status",
    summary="System status with component details",
)
async def system_status(db: AsyncSession = Depends(get_db)) -> dict:
    """Detailed system status including all component health."""
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"

    kb_stats = get_kb_stats()

    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": db_status,
            "knowledge_base": kb_stats,
            "llm_provider": "groq" if settings.GROQ_API_KEY else "openai" if settings.OPENAI_API_KEY else "none",
            "llm_model": settings.llm_model,
        },
    }
