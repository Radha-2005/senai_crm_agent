"""
tests/test_agent.py - Tests for the triage agent ReAct loop.
Tests all 6 evaluation scenarios in dry-run mode.
"""
import pytest
import pytest_asyncio
from backend.agent.triage_agent import TriageAgent
from backend.agent.dry_run import DRY_RUN_SCENARIOS, run_dry_run


@pytest.mark.anyio
class TestTriageAgentScenarios:
    """Test the 6 core evaluation scenarios."""

    async def _run_scenario(self, subject, body, sender_email, contact_name=None, contact_company=None):
        """Helper to run a single dry-run scenario."""
        agent = TriageAgent(max_steps=8)
        return await agent.run(
            email_id="test_scenario",
            subject=subject,
            body=body,
            sender_email=sender_email,
            contact_name=contact_name,
            contact_company=contact_company,
            dry_run=True,
        )

    async def test_scenario_gdpr_request(self):
        """Scenario 1: GDPR data portability request → Legal-Flag."""
        result = await self._run_scenario(
            subject="GDPR Right to Data Portability Request",
            body="I am formally requesting my right to data portability under GDPR Article 20. Please provide all my personal data within 30 days.",
            sender_email="marcus@example.com",
            contact_name="Marcus Weber",
        )
        assert result["decision"] == "Legal-Flag", f"Expected Legal-Flag, got {result['decision']}"
        assert result["classification"] == "legal_gdpr"

    async def test_scenario_ransomware_threat(self):
        """Scenario 2: Ransomware threat → Legal-Flag."""
        result = await self._run_scenario(
            subject="Security Breach - Pay Ransom",
            body="We have compromised your systems. Pay 5 BTC ransom in cryptocurrency within 48 hours or we publish your customer data. Ransomware deployed.",
            sender_email="hacker@darknet.invalid",
        )
        assert result["decision"] == "Legal-Flag", f"Expected Legal-Flag, got {result['decision']}"
        assert result["classification"] in ("security_threat", "legal_threat")

    async def test_scenario_karen_refund_risk(self):
        """Scenario 3: High-risk refund complaint → Escalate."""
        result = await self._run_scenario(
            subject="Final Warning - Refund or I Go Public",
            body="This is my final warning. I am furious and appalled by your terrible service. Give me a full refund now or I will take legal action and post my experience everywhere.",
            sender_email="karen@example.com",
            contact_name="Karen Smith",
            contact_company="Smith Enterprises",
        )
        assert result["decision"] == "Escalate", f"Expected Escalate, got {result['decision']}"

    async def test_scenario_chatbot_misinformation(self):
        """Scenario 4: Chatbot gave wrong refund advice → Escalate."""
        result = await self._run_scenario(
            subject="Your Chatbot Gave Me Wrong Information About Refunds",
            body="Your chatbot told me I was eligible for a 60-day refund. Now your team says it's only 14 days. Your AI chatbot gave me wrong information. I want the refund your chatbot promised.",
            sender_email="confused_user@example.com",
            contact_name="John Doe",
        )
        assert result["decision"] == "Escalate", f"Expected Escalate, got {result['decision']}"

    async def test_scenario_sla_legal_threat(self):
        """Scenario 5: SLA breach with legal action threat → Legal-Flag."""
        result = await self._run_scenario(
            subject="SLA Breach - Legal Action Initiated",
            body="You have breached our SLA agreement by 6 hours. My attorney has been notified and we are pursuing legal action. We demand SLA credits and compensation for the sla breach.",
            sender_email="bob@enterprise.com",
            contact_name="Bob Jones",
            contact_company="Enterprise Corp",
        )
        assert result["decision"] == "Legal-Flag", f"Expected Legal-Flag, got {result['decision']}"

    async def test_scenario_alice_pricing_upgrade(self):
        """Scenario 6: Pricing inquiry for upgrade → Auto-Reply."""
        result = await self._run_scenario(
            subject="Upgrade to Enterprise - Pricing for 10 Additional Seats",
            body="Hi, I would like to upgrade our subscription to the Enterprise plan and add 10 more seats mid-cycle. Can you provide pricing information and calculate the pro-rata cost?",
            sender_email="alice@nonprofit.org",
            contact_name="Alice Chen",
        )
        assert result["decision"] == "Auto-Reply", f"Expected Auto-Reply, got {result['decision']}"


@pytest.mark.anyio
class TestAgentReasoningLoop:
    """Test the ReAct reasoning loop mechanics."""

    async def test_step_limit_respected(self):
        """Agent should not exceed max_steps."""
        agent = TriageAgent(max_steps=3)
        result = await agent.run(
            email_id="step_test",
            subject="Complex issue requiring many steps",
            body="I have a GDPR request, also want a refund, also SLA breach, also legal action.",
            sender_email="complex@example.com",
            dry_run=True,
        )
        # Steps should be bounded by max_steps + classification + decision steps
        assert len(result["steps"]) <= 10  # Allow for classification steps

    async def test_decision_always_returned(self):
        """Agent should always return a valid decision."""
        agent = TriageAgent()
        result = await agent.run(
            email_id="always_decide",
            subject="Random email",
            body="Some random content that doesn't clearly match any category.",
            sender_email="random@example.com",
            dry_run=True,
        )
        valid_decisions = {"Auto-Reply", "Escalate", "Legal-Flag", "Human-Review", "Ignore"}
        assert result["decision"] in valid_decisions

    async def test_classification_included(self):
        """Result should always include classification and sentiment."""
        agent = TriageAgent()
        result = await agent.run(
            email_id="class_test",
            subject="Test",
            body="Test email",
            sender_email="test@example.com",
            dry_run=True,
        )
        assert "classification" in result
        assert "sentiment" in result
        assert "confidence" in result
        assert "steps" in result

    async def test_dry_run_no_db_required(self):
        """Dry-run should work without a database connection."""
        agent = TriageAgent()
        # No db parameter — should work fine in dry-run
        result = await agent.run(
            email_id="no_db_test",
            subject="GDPR Request",
            body="Please provide my data under GDPR Article 20 data portability.",
            sender_email="gdpr@example.com",
            dry_run=True,
        )
        assert result["decision"] is not None


@pytest.mark.anyio
async def test_full_dry_run_suite():
    """Run the complete 6-scenario dry-run evaluation suite."""
    results = await run_dry_run()
    
    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    
    # All 6 scenarios should pass
    failures = [r for r in results if not r["passed"]]
    failure_details = [
        f"{r['scenario_id']}: expected={r['expected_decision']}, got={r['actual_decision']}"
        for r in failures
    ]
    
    assert passed == total, f"Dry-run failures: {failure_details}"
