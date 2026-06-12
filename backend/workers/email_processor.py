"""
workers/email_processor.py - Background email processing worker.
Runs classification, agent triage, and updates email/thread status.
"""
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.session import AsyncSessionLocal
from backend.db.models import Email, Thread, ProcessingJob, AuditLog, JobStatus, EmailStatus, ThreadStatus
from backend.services.classification_service import classify_email, detect_sentiment_deterioration
from backend.agent.triage_agent import TriageAgent

logger = logging.getLogger(__name__)

# Thread status mapping from agent decision
DECISION_TO_THREAD_STATUS = {
    "Auto-Reply": ThreadStatus.AUTO_REPLIED.value,
    "Escalate": ThreadStatus.ESCALATED.value,
    "Legal-Flag": ThreadStatus.LEGAL_FLAGGED.value,
    "Human-Review": ThreadStatus.HUMAN_REVIEW.value,
    "Ignore": ThreadStatus.CLOSED.value,
}


async def process_email(email_id: str, job_id: int) -> None:
    """
    Background task: Process a single email through the full pipeline.
    
    Pipeline:
    1. Load email from database
    2. Multi-layer classification
    3. Sentiment analysis + trend detection
    4. Run triage agent (ReAct loop)
    5. Generate draft reply
    6. Update email, thread, and job records
    7. Write audit log
    """
    # Use a fresh DB session for background task (isolated from request session)
    async with AsyncSessionLocal() as db:
        try:
            # --- Update job status to RUNNING ---
            job_result = await db.execute(
                select(ProcessingJob).where(ProcessingJob.id == job_id)
            )
            job = job_result.scalar_one_or_none()
            if job:
                job.status = JobStatus.RUNNING.value
                job.started_at = datetime.utcnow()
                await db.commit()

            # --- Load email ---
            email_result = await db.execute(
                select(Email).where(Email.id == email_id)
            )
            email = email_result.scalar_one_or_none()
            if not email:
                logger.error(f"Email {email_id} not found for processing")
                return

            email.status = EmailStatus.PROCESSING.value
            await db.commit()

            # --- Load contact for context ---
            contact = email.contact
            contact_name = contact.name if contact else None
            contact_company = contact.company if contact else None

            # --- Load thread history for sentiment trend ---
            thread_emails = []
            if email.thread_id:
                thread_result = await db.execute(
                    select(Email)
                    .where(Email.thread_id == email.thread_id)
                    .where(Email.id != email_id)
                    .order_by(Email.received_at)
                )
                thread_emails = thread_result.scalars().all()

            # --- Multi-layer classification ---
            classification, confidence, sentiment, _ = classify_email(
                email.subject or "",
                email.body or "",
            )

            # --- Sentiment trend detection ---
            historical_sentiments = [e.sentiment for e in thread_emails if e.sentiment]
            historical_sentiments.append(sentiment)
            is_deteriorating = detect_sentiment_deterioration(historical_sentiments)

            # --- Run triage agent ---
            agent = TriageAgent(max_steps=8)
            agent_result = await agent.run(
                email_id=email_id,
                subject=email.subject or "",
                body=email.body or "",
                sender_email=email.sender_email or "",
                thread_id=email.thread_id,
                contact_name=contact_name,
                contact_company=contact_company,
                db=db,
                dry_run=False,
            )

            decision = agent_result["decision"]
            draft_reply = agent_result.get("draft_reply")
            steps = agent_result.get("steps", [])

            # --- Update email record ---
            email.classification = classification
            email.confidence = confidence
            email.sentiment = sentiment
            email.agent_decision = decision
            email.agent_steps = steps
            email.draft_reply = draft_reply
            email.status = EmailStatus.PROCESSED.value

            # --- Update thread record ---
            if email.thread_id:
                thread_result = await db.execute(
                    select(Thread).where(Thread.id == email.thread_id)
                )
                thread = thread_result.scalar_one_or_none()
                if thread:
                    thread.last_agent_decision = decision
                    thread.sentiment_trend = "deteriorating" if is_deteriorating else sentiment
                    thread.status = DECISION_TO_THREAD_STATUS.get(decision, ThreadStatus.OPEN.value)
                    # Priority score: higher for critical/escalated emails
                    priority_map = {
                        "Legal-Flag": 1.0,
                        "Escalate": 0.8,
                        "Human-Review": 0.6,
                        "Auto-Reply": 0.3,
                        "Ignore": 0.0,
                    }
                    thread.priority_score = priority_map.get(decision, 0.5)
                    thread.updated_at = datetime.utcnow()

            # --- Update job record ---
            if job:
                job.status = JobStatus.COMPLETED.value
                job.completed_at = datetime.utcnow()

            # --- Write audit log ---
            audit = AuditLog(
                email_id=email_id,
                thread_id=email.thread_id,
                action=f"agent_triage:{decision}",
                actor="agent",
                details={
                    "classification": classification,
                    "confidence": confidence,
                    "sentiment": sentiment,
                    "decision": decision,
                    "steps_count": len(steps),
                    "is_deteriorating": is_deteriorating,
                },
            )
            db.add(audit)
            await db.commit()

            logger.info(
                f"Email {email_id} processed: "
                f"class={classification}, sentiment={sentiment}, decision={decision}"
            )

        except Exception as e:
            logger.error(f"Error processing email {email_id}: {e}", exc_info=True)
            # Mark job as failed
            try:
                async with AsyncSessionLocal() as error_db:
                    job_result = await error_db.execute(
                        select(ProcessingJob).where(ProcessingJob.id == job_id)
                    )
                    job = job_result.scalar_one_or_none()
                    if job:
                        job.status = JobStatus.FAILED.value
                        job.error_message = str(e)
                        job.completed_at = datetime.utcnow()
                    
                    email_result = await error_db.execute(
                        select(Email).where(Email.id == email_id)
                    )
                    email = email_result.scalar_one_or_none()
                    if email:
                        email.status = EmailStatus.FAILED.value
                    
                    await error_db.commit()
            except Exception as inner_e:
                logger.error(f"Failed to update error status: {inner_e}")
