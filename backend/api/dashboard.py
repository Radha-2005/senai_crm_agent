"""
api/dashboard.py - Dashboard summary endpoint for the frontend.
Uses explicit SQL joins to avoid lazy-loading issues with async SQLAlchemy.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from backend.db.session import get_db
from backend.db.models import Email, Thread, Contact

router = APIRouter(prefix="/api/v1", tags=["dashboard"])


@router.get(
    "/dashboard/inbox",
    summary="Get inbox items for the dashboard",
)
async def get_inbox(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get recent email threads for the inbox view with eager-loaded relationships."""
    # Eager-load contact and emails to avoid lazy-load errors in async context
    result = await db.execute(
        select(Thread)
        .options(
            selectinload(Thread.contact),
            selectinload(Thread.emails),
        )
        .order_by(desc(Thread.priority_score), desc(Thread.updated_at))
        .limit(limit)
    )
    threads = result.scalars().all()

    inbox_items = []
    for thread in threads:
        contact = thread.contact
        emails = thread.emails or []
        # Sort emails by ingested_at to get the most recent
        sorted_emails = sorted(emails, key=lambda e: e.ingested_at)
        latest_email = sorted_emails[-1] if sorted_emails else None
        
        inbox_items.append({
            "thread_id": thread.id,
            "subject": thread.subject or "(no subject)",
            "contact_name": contact.name if contact else "Unknown",
            "contact_email": contact.email if contact else "",
            "status": thread.status,
            "priority_score": thread.priority_score,
            "last_decision": thread.last_agent_decision,
            "sentiment_trend": thread.sentiment_trend,
            "email_count": len(emails),
            "latest_sentiment": latest_email.sentiment if latest_email else None,
            "latest_classification": latest_email.classification if latest_email else None,
            "updated_at": thread.updated_at.isoformat(),
        })

    return {
        "total": len(inbox_items),
        "threads": inbox_items,
    }


@router.get(
    "/dashboard/summary",
    summary="Quick summary metrics",
)
async def get_summary(db: AsyncSession = Depends(get_db)) -> dict:
    """Quick summary metrics for the dashboard header."""
    total_result = await db.execute(select(func.count(Email.id)))
    total = total_result.scalar() or 0

    unprocessed_result = await db.execute(
        select(func.count(Email.id)).where(Email.status.in_(["pending", "processing"]))
    )
    unprocessed = unprocessed_result.scalar() or 0

    escalated_result = await db.execute(
        select(func.count(Thread.id)).where(Thread.status == "escalated")
    )
    escalated = escalated_result.scalar() or 0

    legal_result = await db.execute(
        select(func.count(Thread.id)).where(Thread.status == "legal_flagged")
    )
    legal_flagged = legal_result.scalar() or 0

    return {
        "total_emails": total,
        "unprocessed": unprocessed,
        "escalated": escalated,
        "legal_flagged": legal_flagged,
    }
