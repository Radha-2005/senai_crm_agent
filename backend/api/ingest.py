"""
api/ingest.py - Email ingestion API endpoint.
Accepts email payloads and queues them for background processing.
"""
import logging
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.schemas.email import EmailIngestPayload, EmailIngestResponse
from backend.services.ingestion_service import ingest_email
from backend.workers.email_processor import process_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["ingestion"])


@router.post(
    "/ingest",
    response_model=EmailIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Ingest a new email",
    description="Accepts an email payload, stores it, and queues background triage processing.",
)
async def ingest_email_endpoint(
    payload: EmailIngestPayload,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
) -> EmailIngestResponse:
    """
    Ingest endpoint:
    1. Validates and deduplicates the email
    2. Resolves/creates contact and thread
    3. Creates processing job
    4. Queues background triage
    """
    try:
        email, job = await ingest_email(db, payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Ingestion failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Ingestion failed due to internal error",
        )

    # Queue background processing
    background_tasks.add_task(process_email, email.id, job.id)

    return EmailIngestResponse(
        message="Email accepted for processing",
        email_id=email.id,
        job_id=job.id,
    )
