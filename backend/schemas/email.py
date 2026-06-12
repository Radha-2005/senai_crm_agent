"""
schemas/email.py - Pydantic schemas for Email and Contact models.
"""
from pydantic import BaseModel, EmailStr, ConfigDict, Field
from datetime import datetime
from typing import Optional, List, Any, Dict
from backend.db.models import EmailStatus, AgentDecision, SentimentLabel


class ContactBase(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    phone: Optional[str] = None
    tier: str = "standard"
    ltv: float = 0.0
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None


class ContactCreate(ContactBase):
    id: Optional[str] = None


class ContactResponse(ContactBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        """Override to handle None tags from DB."""
        if hasattr(obj, '__dict__') and getattr(obj, 'tags', None) is None:
            obj.tags = []
        return super().model_validate(obj, *args, **kwargs)


class EmailIngestPayload(BaseModel):
    """Schema for incoming email ingestion requests."""
    id: str
    thread_id: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    sender_email: str
    sender_name: Optional[str] = None
    company: Optional[str] = None
    received_at: Optional[str] = None  # ISO string
    tags: Optional[List[str]] = Field(default_factory=list)
    ltv: Optional[float] = 0.0
    tier: Optional[str] = "standard"


class EmailIngestResponse(BaseModel):
    message: str
    email_id: str
    job_id: int


class EmailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    thread_id: Optional[str]
    contact_id: Optional[str]
    subject: Optional[str]
    body: Optional[str]
    sender_email: Optional[str]
    received_at: Optional[datetime]
    status: str
    classification: Optional[str]
    sentiment: Optional[str]
    confidence: Optional[float]
    agent_decision: Optional[str]
    agent_steps: Optional[List[Dict[str, Any]]]
    draft_reply: Optional[str]
    draft_approved: bool
    ingested_at: datetime


class DraftEditRequest(BaseModel):
    draft_reply: str


class DraftApproveRequest(BaseModel):
    approved: bool = True
