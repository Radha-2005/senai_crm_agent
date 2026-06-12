"""
tests/test_db_and_schemas.py - Tests for database models and Pydantic schemas.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.db.models import Contact, Thread, Email, ProcessingJob, EmailStatus, JobStatus


class TestPydanticSchemas:
    """Test Pydantic schema validation."""

    def test_email_ingest_payload_validation(self):
        """Test EmailIngestPayload schema validation."""
        from backend.schemas.email import EmailIngestPayload
        
        payload = EmailIngestPayload(
            id="test_001",
            subject="Test subject",
            body="Test body",
            sender_email="test@example.com",
            sender_name="Test User",
        )
        assert payload.id == "test_001"
        assert payload.sender_email == "test@example.com"
        assert payload.tier == "standard"
        assert payload.ltv == 0.0

    def test_contact_response_schema(self):
        """Test ContactResponse schema from_attributes."""
        from backend.schemas.email import ContactResponse
        
        # Simulate a contact model
        contact = Contact(
            id="c_001",
            email="user@example.com",
            name="Test User",
            tier="premium",
            ltv=5000.0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        response = ContactResponse.model_validate(contact)
        assert response.id == "c_001"
        assert response.email == "user@example.com"

    def test_dashboard_stats_schema(self):
        """Test DashboardStats schema."""
        from backend.schemas.analytics import DashboardStats, ClassificationStats
        
        stats = DashboardStats(
            total_emails=100,
            processed_today=10,
            pending=5,
            escalated=3,
            legal_flagged=1,
            auto_replied=6,
            avg_processing_time_sec=2.5,
            classification_breakdown=[
                ClassificationStats(label="refund_request", count=10, percentage=10.0)
            ],
            sentiment_breakdown=[],
            decision_breakdown={"Escalate": 3},
        )
        assert stats.total_emails == 100


@pytest.mark.anyio
class TestDatabaseModels:
    """Test SQLAlchemy model CRUD operations."""

    async def test_create_contact(self, db: AsyncSession):
        """Test creating a contact record."""
        contact = Contact(
            id="c_schema_001",
            email="schema_test@example.com",
            name="Schema Test User",
            tier="enterprise",
            ltv=10000.0,
        )
        db.add(contact)
        await db.commit()
        
        result = await db.execute(
            select(Contact).where(Contact.id == "c_schema_001")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.email == "schema_test@example.com"
        assert found.tier == "enterprise"

    async def test_create_thread_and_email(self, db: AsyncSession):
        """Test creating a thread with a linked email."""
        # Create contact first
        contact = Contact(
            id="c_schema_002",
            email="thread_test@example.com",
        )
        db.add(contact)
        await db.flush()
        
        # Create thread
        thread = Thread(
            id="t_schema_001",
            contact_id=contact.id,
            subject="Test Thread",
        )
        db.add(thread)
        await db.flush()
        
        # Create email
        email = Email(
            id="e_schema_001",
            thread_id=thread.id,
            contact_id=contact.id,
            subject="Test Thread",
            body="This is a test email body",
            sender_email=contact.email,
            status=EmailStatus.PENDING.value,
        )
        db.add(email)
        await db.commit()
        
        result = await db.execute(
            select(Email).where(Email.id == "e_schema_001")
        )
        found = result.scalar_one_or_none()
        assert found is not None
        assert found.thread_id == "t_schema_001"
        assert found.status == EmailStatus.PENDING.value
