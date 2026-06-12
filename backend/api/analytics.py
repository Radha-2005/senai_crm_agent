"""
api/analytics.py - Analytics and reporting API endpoints.
"""
from datetime import datetime, timedelta
from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case

from backend.db.session import get_db
from backend.db.models import Email, Thread, ProcessingJob
from backend.schemas.analytics import DashboardStats, ClassificationStats, SentimentStats

router = APIRouter(prefix="/api/v1", tags=["analytics"])


@router.get(
    "/analytics/dashboard",
    response_model=DashboardStats,
    summary="Dashboard statistics",
)
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)) -> DashboardStats:
    """Get aggregated statistics for the dashboard."""
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

    # Total emails
    total_result = await db.execute(select(func.count(Email.id)))
    total_emails = total_result.scalar() or 0

    # Processed today
    today_result = await db.execute(
        select(func.count(Email.id)).where(Email.ingested_at >= today)
    )
    processed_today = today_result.scalar() or 0

    # Status counts
    pending_result = await db.execute(
        select(func.count(Email.id)).where(Email.status == "pending")
    )
    pending = pending_result.scalar() or 0

    # Decision counts
    decision_result = await db.execute(
        select(Email.agent_decision, func.count(Email.id))
        .where(Email.agent_decision.isnot(None))
        .group_by(Email.agent_decision)
    )
    decision_counts = dict(decision_result.fetchall())

    escalated = decision_counts.get("Escalate", 0)
    legal_flagged = decision_counts.get("Legal-Flag", 0)
    auto_replied = decision_counts.get("Auto-Reply", 0)

    # Classification breakdown
    class_result = await db.execute(
        select(Email.classification, func.count(Email.id))
        .where(Email.classification.isnot(None))
        .group_by(Email.classification)
    )
    class_rows = class_result.fetchall()
    class_total = sum(r[1] for r in class_rows) or 1
    
    classification_breakdown = [
        ClassificationStats(
            label=row[0],
            count=row[1],
            percentage=round(row[1] / class_total * 100, 1),
        )
        for row in sorted(class_rows, key=lambda r: r[1], reverse=True)
    ]

    # Sentiment breakdown
    sentiment_result = await db.execute(
        select(Email.sentiment, func.count(Email.id))
        .where(Email.sentiment.isnot(None))
        .group_by(Email.sentiment)
    )
    sentiment_breakdown = [
        SentimentStats(label=row[0], count=row[1])
        for row in sentiment_result.fetchall()
    ]

    return DashboardStats(
        total_emails=total_emails,
        processed_today=processed_today,
        pending=pending,
        escalated=escalated,
        legal_flagged=legal_flagged,
        auto_replied=auto_replied,
        avg_processing_time_sec=None,  # Would calculate from job timestamps in production
        classification_breakdown=classification_breakdown,
        sentiment_breakdown=sentiment_breakdown,
        decision_breakdown=decision_counts,
    )
