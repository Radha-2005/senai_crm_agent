"""
services/ingestion_service.py - Email ingestion pipeline.
Handles deduplication, contact resolution, thread management, and job creation.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import Email, Contact, Thread, ProcessingJob, EmailStatus, JobStatus
from backend.schemas.email import EmailIngestPayload
from backend.services.heuristic_service import clean_html, is_blocklisted

logger = logging.getLogger(__name__)


def _parse_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse an ISO datetime string to a timezone-naive UTC datetime."""
    if not dt_str:
        return None
    try:
        # Handle 'Z' suffix
        dt_str = dt_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(dt_str)
        # Convert to UTC and strip timezone info for DB storage
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt
    except (ValueError, AttributeError):
        logger.warning(f"Could not parse datetime: {dt_str}")
        return None


async def _get_or_create_contact(
    db: AsyncSession,
    payload: EmailIngestPayload,
) -> Contact:
    """Find existing contact by email or create a new one."""
    result = await db.execute(
        select(Contact).where(Contact.email == payload.sender_email)
    )
    contact = result.scalar_one_or_none()

    if contact:
        # Update mutable fields if provided
        if payload.sender_name and not contact.name:
            contact.name = payload.sender_name
        if payload.company and not contact.company:
            contact.company = payload.company
        contact.updated_at = datetime.utcnow()
        return contact

    # Create new contact
    contact_id = f"contact_{uuid.uuid4().hex[:12]}"
    contact = Contact(
        id=contact_id,
        email=payload.sender_email,
        name=payload.sender_name,
        company=payload.company,
        tier=payload.tier or "standard",
        ltv=payload.ltv or 0.0,
        tags=payload.tags or [],
    )
    db.add(contact)
    await db.flush()  # Get ID without full commit
    return contact


async def _get_or_create_thread(
    db: AsyncSession,
    payload: EmailIngestPayload,
    contact_id: str,
) -> Thread:
    """Find existing thread by thread_id or create a new one."""
    if payload.thread_id:
        result = await db.execute(
            select(Thread).where(Thread.id == payload.thread_id)
        )
        thread = result.scalar_one_or_none()
        if thread:
            thread.updated_at = datetime.utcnow()
            return thread

    # Create new thread
    thread_id = payload.thread_id or f"thread_{uuid.uuid4().hex[:12]}"
    thread = Thread(
        id=thread_id,
        contact_id=contact_id,
        subject=payload.subject,
        status="open",
    )
    db.add(thread)
    await db.flush()
    return thread


async def ingest_email(
    db: AsyncSession,
    payload: EmailIngestPayload,
) -> tuple[Email, ProcessingJob]:
    """
    Main ingestion pipeline:
    1. Check for duplicates
    2. Blocklist check
    3. Clean HTML body
    4. Resolve/create contact
    5. Resolve/create thread
    6. Create email record
    7. Create processing job
    
    Returns the (Email, ProcessingJob) tuple.
    Raises ValueError for duplicate or blocked emails.
    """
    # 1. Deduplication check
    existing = await db.execute(
        select(Email).where(Email.id == payload.id)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"Email {payload.id} already exists (idempotency guard)")

    # 2. Blocklist check
    if is_blocklisted(payload.sender_email):
        raise ValueError(f"Sender {payload.sender_email} is on the blocklist")

    # 3. Clean HTML
    clean_body = clean_html(payload.body or "")
    received_dt = _parse_datetime(payload.received_at)

    # 4. Contact resolution
    contact = await _get_or_create_contact(db, payload)

    # 5. Thread resolution
    thread = await _get_or_create_thread(db, payload, contact.id)

    # 6. Create email
    email = Email(
        id=payload.id,
        thread_id=thread.id,
        contact_id=contact.id,
        subject=payload.subject,
        body=clean_body,
        sender_email=payload.sender_email,
        received_at=received_dt,
        status=EmailStatus.PENDING.value,
        raw_payload=payload.model_dump(),
    )
    db.add(email)
    await db.flush()

    # 7. Create processing job
    job = ProcessingJob(
        email_id=email.id,
        status=JobStatus.QUEUED.value,
    )
    db.add(job)
    await db.flush()

    logger.info(f"Ingested email {email.id} -> thread {thread.id}, job queued")
    return email, job
