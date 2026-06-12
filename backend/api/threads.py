"""
api/threads.py - Thread management API endpoints.
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from backend.db.session import get_db
from backend.db.models import Thread, Email
from backend.schemas.thread import ThreadResponse, ThreadListResponse
from backend.schemas.email import EmailResponse, DraftEditRequest, DraftApproveRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1", tags=["threads"])


@router.get(
    "/threads",
    response_model=List[ThreadListResponse],
    summary="List all threads",
)
async def list_threads(
    status_filter: Optional[str] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> List[ThreadListResponse]:
    """List all threads with optional status filter and pagination."""
    query = select(Thread).order_by(desc(Thread.priority_score), desc(Thread.updated_at))
    
    if status_filter:
        query = query.where(Thread.status == status_filter)
    
    # Apply pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    threads = result.scalars().all()
    
    response = []
    for thread in threads:
        response.append(ThreadListResponse(
            id=thread.id,
            contact_id=thread.contact_id,
            subject=thread.subject,
            status=thread.status,
            last_agent_decision=thread.last_agent_decision,
            sentiment_trend=thread.sentiment_trend,
            priority_score=thread.priority_score,
            created_at=thread.created_at,
            updated_at=thread.updated_at,
            email_count=len(thread.emails) if thread.emails else 0,
        ))
    
    return response


@router.get(
    "/threads/{thread_id}",
    response_model=ThreadResponse,
    summary="Get thread details",
)
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
) -> ThreadResponse:
    """Get a single thread with all associated emails and contact info."""
    result = await db.execute(
        select(Thread).where(Thread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Thread {thread_id} not found",
        )
    
    return ThreadResponse.model_validate(thread)


@router.get(
    "/emails/{email_id}",
    response_model=EmailResponse,
    summary="Get email details",
)
async def get_email(
    email_id: str,
    db: AsyncSession = Depends(get_db),
) -> EmailResponse:
    """Get a single email with full classification and agent results."""
    result = await db.execute(
        select(Email).where(Email.id == email_id)
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email {email_id} not found",
        )
    
    return EmailResponse.model_validate(email)


@router.patch(
    "/emails/{email_id}/draft",
    response_model=EmailResponse,
    summary="Edit draft reply",
)
async def edit_draft(
    email_id: str,
    body: DraftEditRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailResponse:
    """Human operator edits the agent-generated draft reply."""
    result = await db.execute(
        select(Email).where(Email.id == email_id)
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email {email_id} not found",
        )
    
    email.draft_reply = body.draft_reply
    await db.commit()
    
    return EmailResponse.model_validate(email)


@router.post(
    "/emails/{email_id}/approve",
    response_model=EmailResponse,
    summary="Approve draft reply",
)
async def approve_draft(
    email_id: str,
    body: DraftApproveRequest,
    db: AsyncSession = Depends(get_db),
) -> EmailResponse:
    """Human operator approves the draft reply for sending."""
    result = await db.execute(
        select(Email).where(Email.id == email_id)
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email {email_id} not found",
        )
    
    email.draft_approved = body.approved
    await db.commit()
    
    return EmailResponse.model_validate(email)
