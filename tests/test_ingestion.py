"""
tests/test_ingestion.py - Tests for email ingestion pipeline.
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas.email import EmailIngestPayload
from backend.services.ingestion_service import ingest_email
from backend.services.heuristic_service import clean_html, is_blocklisted


class TestHeuristicService:
    """Test the heuristic helper functions."""

    def test_clean_html_basic(self):
        """Test HTML cleaning."""
        html = "<p>Hello <b>World</b>&amp;!</p>"
        result = clean_html(html)
        assert "<p>" not in result
        assert "&amp;" not in result
        assert "Hello" in result
        assert "World" in result

    def test_clean_html_entities(self):
        """Test HTML entity unescaping."""
        html = "&lt;script&gt;alert(&quot;xss&quot;)&lt;/script&gt;"
        result = clean_html(html)
        assert "&lt;" not in result
        assert "&quot;" not in result

    def test_blocklist_noreply(self):
        """Test that noreply addresses are blocklisted."""
        assert is_blocklisted("noreply@example.com") is True
        assert is_blocklisted("no-reply@service.com") is True
        assert is_blocklisted("donotreply@company.org") is True

    def test_blocklist_regular_email(self):
        """Test that regular emails pass the blocklist check."""
        assert is_blocklisted("customer@example.com") is False
        assert is_blocklisted("support@company.co.uk") is False

    def test_blocklist_bounce(self):
        """Test that bounce addresses are blocklisted."""
        assert is_blocklisted("mailer-daemon@sendgrid.com") is True


@pytest.mark.anyio
class TestIngestionPipeline:
    """Test the email ingestion pipeline."""

    async def test_basic_ingestion(self, db: AsyncSession):
        """Test basic email ingestion creates contact, thread, and email."""
        payload = EmailIngestPayload(
            id="ingest_test_001",
            subject="Test email ingestion",
            body="This is a test email for ingestion testing.",
            sender_email="ingest_test@example.com",
            sender_name="Ingest Test User",
        )
        
        email, job = await ingest_email(db, payload)
        await db.commit()
        
        assert email.id == "ingest_test_001"
        assert email.thread_id is not None
        assert email.contact_id is not None
        assert job.id is not None
        assert job.status == "queued"

    async def test_idempotency(self, db: AsyncSession):
        """Test that ingesting the same email twice raises ValueError."""
        payload = EmailIngestPayload(
            id="ingest_dup_001",
            subject="Duplicate test",
            body="This email should not be ingested twice.",
            sender_email="dup_test@example.com",
        )
        
        # First ingestion
        email, job = await ingest_email(db, payload)
        await db.commit()
        
        # Second ingestion — should raise ValueError
        with pytest.raises(ValueError, match="already exists"):
            await ingest_email(db, payload)

    async def test_blocklisted_sender(self, db: AsyncSession):
        """Test that blocklisted senders are rejected."""
        payload = EmailIngestPayload(
            id="blocklist_test_001",
            subject="Auto-notification",
            body="This is an automated message.",
            sender_email="noreply@automated.com",
        )
        
        with pytest.raises(ValueError, match="blocklist"):
            await ingest_email(db, payload)

    async def test_html_cleaning_in_ingestion(self, db: AsyncSession):
        """Test that HTML in email body is cleaned during ingestion."""
        payload = EmailIngestPayload(
            id="html_clean_001",
            subject="HTML email",
            body="<p>Hello <b>World</b>&amp;!</p><script>alert('xss')</script>",
            sender_email="html_test@example.com",
        )
        
        email, _ = await ingest_email(db, payload)
        await db.commit()
        
        # Body should be clean text
        assert "<p>" not in email.body
        assert "<script>" not in email.body
        assert "Hello" in email.body

    async def test_thread_reuse(self, db: AsyncSession):
        """Test that emails with same thread_id reuse existing thread."""
        thread_id = "thread_reuse_001"
        
        payload1 = EmailIngestPayload(
            id="thread_reuse_email_01",
            thread_id=thread_id,
            subject="Thread test 1",
            body="First email in thread",
            sender_email="thread_test@example.com",
        )
        payload2 = EmailIngestPayload(
            id="thread_reuse_email_02",
            thread_id=thread_id,
            subject="Thread test 2",
            body="Second email in thread",
            sender_email="thread_test@example.com",
        )
        
        email1, _ = await ingest_email(db, payload1)
        email2, _ = await ingest_email(db, payload2)
        await db.commit()
        
        # Both emails should be in the same thread
        assert email1.thread_id == thread_id
        assert email2.thread_id == thread_id
