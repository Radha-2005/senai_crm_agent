"""
tests/test_api.py - Integration tests for the FastAPI API endpoints.
"""
import pytest
import pytest_asyncio
import asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession


@pytest_asyncio.fixture
async def client(test_engine):
    """Create test HTTP client with ASGI transport."""
    from backend.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


@pytest.mark.anyio
class TestHealthEndpoints:
    """Test health and status endpoints."""

    async def test_health_check(self, client: AsyncClient):
        """Health endpoint should return 200."""
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "version" in data

    async def test_system_status(self, client: AsyncClient):
        """System status should include all components."""
        resp = await client.get("/api/v1/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "components" in data
        assert "database" in data["components"]

    async def test_root_endpoint(self, client: AsyncClient):
        """Root endpoint should return app info."""
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert "app" in data


@pytest.mark.anyio
class TestIngestionAPI:
    """Test email ingestion endpoint."""

    async def test_ingest_email(self, client: AsyncClient):
        """Successfully ingest an email."""
        payload = {
            "id": "api_test_001",
            "subject": "API Test Email",
            "body": "This is a test email via the API.",
            "sender_email": "api_test@example.com",
            "sender_name": "API Test User",
        }
        resp = await client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 202
        data = resp.json()
        assert data["email_id"] == "api_test_001"
        assert "job_id" in data

    async def test_ingest_duplicate(self, client: AsyncClient):
        """Duplicate email should return 409."""
        payload = {
            "id": "api_dup_001",
            "subject": "Dup Test",
            "body": "Test body for duplicate check.",
            "sender_email": "dup_api@example.com",
        }
        # First ingestion
        resp = await client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 202
        
        # Second ingestion — should fail
        resp = await client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 409

    async def test_ingest_blocklisted(self, client: AsyncClient):
        """Blocklisted sender should return 409."""
        payload = {
            "id": "blocklist_api_001",
            "subject": "Auto notification",
            "body": "Automated message",
            "sender_email": "noreply@automated.com",
        }
        resp = await client.post("/api/v1/ingest", json=payload)
        assert resp.status_code == 409


@pytest.mark.anyio
class TestThreadsAPI:
    """Test thread and email management endpoints."""

    async def test_list_threads_empty(self, client: AsyncClient):
        """List threads should return array."""
        resp = await client.get("/api/v1/threads")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_thread_not_found(self, client: AsyncClient):
        """Non-existent thread should return 404."""
        resp = await client.get("/api/v1/threads/nonexistent_thread")
        assert resp.status_code == 404

    async def test_email_not_found(self, client: AsyncClient):
        """Non-existent email should return 404."""
        resp = await client.get("/api/v1/emails/nonexistent_email")
        assert resp.status_code == 404

    async def test_ingest_then_get_email(self, client: AsyncClient):
        """Ingest email and retrieve it via API."""
        # Ingest
        payload = {
            "id": "get_test_001",
            "subject": "Get Test Email",
            "body": "Testing email retrieval via API.",
            "sender_email": "get_test@example.com",
        }
        ingest_resp = await client.post("/api/v1/ingest", json=payload)
        assert ingest_resp.status_code == 202
        
        # Wait for ingestion to complete
        await asyncio.sleep(0.2)
        
        # Get the email
        resp = await client.get(f"/api/v1/emails/get_test_001")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "get_test_001"

    async def test_edit_draft(self, client: AsyncClient):
        """Test editing a draft reply."""
        # First ingest
        payload = {
            "id": "draft_test_001",
            "subject": "Draft edit test",
            "body": "Please help me with a refund request.",
            "sender_email": "draft_test@example.com",
        }
        await client.post("/api/v1/ingest", json=payload)
        await asyncio.sleep(0.2)
        
        # Edit draft
        resp = await client.patch(
            "/api/v1/emails/draft_test_001/draft",
            json={"draft_reply": "Thank you for contacting us. We are reviewing your request."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reviewing your request" in data["draft_reply"]

    async def test_approve_draft(self, client: AsyncClient):
        """Test approving a draft reply."""
        # Ingest
        payload = {
            "id": "approve_test_001",
            "subject": "Approve draft test",
            "body": "I want to approve this email.",
            "sender_email": "approve_test@example.com",
        }
        await client.post("/api/v1/ingest", json=payload)
        await asyncio.sleep(0.2)
        
        resp = await client.post(
            "/api/v1/emails/approve_test_001/approve",
            json={"approved": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["draft_approved"] is True


@pytest.mark.anyio
class TestContactsAPI:
    """Test contact management endpoints."""

    async def test_list_contacts(self, client: AsyncClient):
        """List contacts should return array."""
        resp = await client.get("/api/v1/contacts")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_contact_not_found(self, client: AsyncClient):
        """Non-existent contact should return 404."""
        resp = await client.get("/api/v1/contacts/nonexistent_contact")
        assert resp.status_code == 404


@pytest.mark.anyio
class TestAnalyticsAPI:
    """Test analytics endpoints."""

    async def test_dashboard_stats(self, client: AsyncClient):
        """Dashboard stats should return valid structure."""
        resp = await client.get("/api/v1/analytics/dashboard")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_emails" in data
        assert "pending" in data
        assert "escalated" in data

    async def test_dashboard_inbox(self, client: AsyncClient):
        """Inbox endpoint should return threads list."""
        resp = await client.get("/api/v1/dashboard/inbox")
        assert resp.status_code == 200
        data = resp.json()
        assert "threads" in data
        assert "total" in data

    async def test_dashboard_summary(self, client: AsyncClient):
        """Summary endpoint should return key metrics."""
        resp = await client.get("/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_emails" in data
        assert "escalated" in data
