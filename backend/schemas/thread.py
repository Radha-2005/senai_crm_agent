"""
schemas/thread.py - Pydantic schemas for Thread model.
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List
from backend.schemas.email import EmailResponse, ContactResponse


class ThreadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contact_id: Optional[str]
    subject: Optional[str]
    status: str
    last_agent_decision: Optional[str]
    sentiment_trend: Optional[str]
    priority_score: float
    created_at: datetime
    updated_at: datetime
    emails: List[EmailResponse] = []
    contact: Optional[ContactResponse] = None


class ThreadListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    contact_id: Optional[str]
    subject: Optional[str]
    status: str
    last_agent_decision: Optional[str]
    sentiment_trend: Optional[str]
    priority_score: float
    created_at: datetime
    updated_at: datetime
    email_count: int = 0
