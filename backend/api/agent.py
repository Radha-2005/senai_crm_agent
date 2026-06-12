"""
api/agent.py - Agent triage API endpoints.
Allows triggering agent dry-runs and viewing triage results.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional

from backend.db.session import get_db
from backend.db.models import Email
from backend.agent.triage_agent import TriageAgent
from backend.agent.dry_run import run_dry_run

router = APIRouter(prefix="/api/v1", tags=["agent"])


class TriageRequest(BaseModel):
    email_id: str
    dry_run: bool = False


class ManualTriageRequest(BaseModel):
    subject: str
    body: str
    sender_email: str
    contact_name: Optional[str] = None
    dry_run: bool = True


@router.post(
    "/agent/triage",
    summary="Trigger agent triage for an email",
)
async def trigger_triage(
    body: TriageRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Manually trigger agent triage for a specific email ID."""
    result = await db.execute(
        select(Email).where(Email.id == body.email_id)
    )
    email = result.scalar_one_or_none()
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Email {body.email_id} not found",
        )

    agent = TriageAgent()
    triage_result = await agent.run(
        email_id=email.id,
        subject=email.subject or "",
        body=email.body or "",
        sender_email=email.sender_email or "",
        thread_id=email.thread_id,
        db=db,
        dry_run=body.dry_run,
    )
    
    return triage_result


@router.post(
    "/agent/triage/manual",
    summary="Manually triage an email payload (without DB storage)",
)
async def manual_triage(
    body: ManualTriageRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Run agent triage on a raw email payload (for testing/debugging)."""
    agent = TriageAgent()
    return await agent.run(
        email_id="manual_triage",
        subject=body.subject,
        body=body.body,
        sender_email=body.sender_email,
        contact_name=body.contact_name,
        db=db,
        dry_run=body.dry_run,
    )


@router.get(
    "/agent/dry-run",
    summary="Run all dry-run evaluation scenarios",
)
async def dry_run_all() -> dict:
    """Execute all 6 predefined evaluation scenarios in dry-run mode."""
    results = await run_dry_run()
    passed = sum(1 for r in results if r["passed"])
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results,
    }
