"""
db/models.py - SQLAlchemy ORM models for the SenAI CRM platform.
Defines all database tables and relationships.
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean,
    DateTime, ForeignKey, Enum as SAEnum, JSON
)
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class EmailStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    HUMAN_REVIEW = "human_review"


class ThreadStatus(str, enum.Enum):
    OPEN = "open"
    ESCALATED = "escalated"
    LEGAL_FLAGGED = "legal_flagged"
    AUTO_REPLIED = "auto_replied"
    CLOSED = "closed"
    HUMAN_REVIEW = "human_review"


class AgentDecision(str, enum.Enum):
    AUTO_REPLY = "Auto-Reply"
    ESCALATE = "Escalate"
    LEGAL_FLAG = "Legal-Flag"
    HUMAN_REVIEW = "Human-Review"
    IGNORE = "Ignore"


class SentimentLabel(str, enum.Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"
    CRITICAL = "critical"


class JobStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# ---------------------------------------------------------------------------
# Contact / Customer model
# ---------------------------------------------------------------------------

class Contact(Base):
    """Represents a customer or external party."""
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[Optional[str]] = mapped_column(String(255))
    company: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    tier: Mapped[str] = mapped_column(String(20), default="standard")  # standard, premium, enterprise
    ltv: Mapped[float] = mapped_column(Float, default=0.0)  # lifetime value USD
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    threads: Mapped[List["Thread"]] = relationship("Thread", back_populates="contact", lazy="selectin")
    emails: Mapped[List["Email"]] = relationship("Email", back_populates="contact", lazy="selectin")


# ---------------------------------------------------------------------------
# Thread model
# ---------------------------------------------------------------------------

class Thread(Base):
    """A conversation thread grouping multiple emails from the same contact/topic."""
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("contacts.id"), index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        SAEnum(ThreadStatus, values_callable=lambda x: [e.value for e in x]),
        default=ThreadStatus.OPEN.value
    )
    last_agent_decision: Mapped[Optional[str]] = mapped_column(String(50))
    sentiment_trend: Mapped[Optional[str]] = mapped_column(String(20))
    priority_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="threads")
    emails: Mapped[List["Email"]] = relationship("Email", back_populates="thread", lazy="selectin", order_by="Email.received_at")


# ---------------------------------------------------------------------------
# Email model
# ---------------------------------------------------------------------------

class Email(Base):
    """Individual email message in the system."""
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("threads.id"), index=True)
    contact_id: Mapped[Optional[str]] = mapped_column(String(50), ForeignKey("contacts.id"), index=True)
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    body: Mapped[Optional[str]] = mapped_column(Text)
    sender_email: Mapped[Optional[str]] = mapped_column(String(255))
    received_at: Mapped[Optional[datetime]] = mapped_column(DateTime, index=True)
    status: Mapped[str] = mapped_column(
        SAEnum(EmailStatus, values_callable=lambda x: [e.value for e in x]),
        default=EmailStatus.PENDING.value
    )
    # Classification results
    classification: Mapped[Optional[str]] = mapped_column(String(100))
    sentiment: Mapped[Optional[str]] = mapped_column(String(20))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    # Agent output
    agent_decision: Mapped[Optional[str]] = mapped_column(String(50))
    agent_steps: Mapped[Optional[dict]] = mapped_column(JSON)
    draft_reply: Mapped[Optional[str]] = mapped_column(Text)
    draft_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    # Raw data
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSON)
    ingested_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    thread: Mapped[Optional["Thread"]] = relationship("Thread", back_populates="emails")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="emails")
    processing_jobs: Mapped[List["ProcessingJob"]] = relationship("ProcessingJob", back_populates="email")


# ---------------------------------------------------------------------------
# ProcessingJob model
# ---------------------------------------------------------------------------

class ProcessingJob(Base):
    """Tracks background processing tasks for emails."""
    __tablename__ = "processing_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[str] = mapped_column(String(50), ForeignKey("emails.id"), index=True)
    status: Mapped[str] = mapped_column(
        SAEnum(JobStatus, values_callable=lambda x: [e.value for e in x]),
        default=JobStatus.QUEUED.value
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    email: Mapped["Email"] = relationship("Email", back_populates="processing_jobs")


# ---------------------------------------------------------------------------
# AuditLog model
# ---------------------------------------------------------------------------

class AuditLog(Base):
    """Immutable audit trail for all agent actions and decisions."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    thread_id: Mapped[Optional[str]] = mapped_column(String(50), index=True)
    action: Mapped[str] = mapped_column(String(100))
    actor: Mapped[str] = mapped_column(String(100))  # "agent", "human", "system"
    details: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
