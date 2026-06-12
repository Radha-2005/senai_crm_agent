"""
agent/dry_run.py - Dry-run simulation for the triage agent.
Allows testing agent reasoning without actual database operations.
"""
import asyncio
import logging
from typing import Dict, Any

from backend.agent.triage_agent import TriageAgent

logger = logging.getLogger(__name__)

# Test scenario emails for dry-run validation
DRY_RUN_SCENARIOS = [
    {
        "id": "test_gdpr_01",
        "subject": "GDPR Right to Data Portability Request",
        "body": "I am formally requesting my right to data portability under GDPR Article 20. Please provide all my personal data in a machine-readable format within 30 days.",
        "sender_email": "marcus@example.com",
        "contact_name": "Marcus Weber",
        "expected_decision": "Legal-Flag",
    },
    {
        "id": "test_ransom_01",
        "subject": "Urgent: Security Breach Notification",
        "body": "We have compromised your systems. Pay 5 BTC in cryptocurrency within 48 hours or we will publish your customer data. This is a ransomware attack.",
        "sender_email": "hacker@darkweb.invalid",
        "contact_name": None,
        "expected_decision": "Legal-Flag",
    },
    {
        "id": "test_refund_01",
        "subject": "Final Warning - Refund Required",
        "body": "This is my final warning. I am extremely frustrated with your terrible service. I want a full refund immediately or I will take legal action and share my experience publicly.",
        "sender_email": "karen@example.com",
        "contact_name": "Karen Smith",
        "expected_decision": "Escalate",
    },
    {
        "id": "test_chatbot_01",
        "subject": "Your Chatbot Gave Wrong Refund Information",
        "body": "Your chatbot told me I could get a full refund within 60 days. Now your support says it's only 14 days. I want the refund your AI promised me.",
        "sender_email": "user@example.com",
        "contact_name": "John Doe",
        "expected_decision": "Escalate",
    },
    {
        "id": "test_sla_01",
        "subject": "SLA Breach - Legal Action Pending",
        "body": "You have breached our SLA by 4 hours. My attorney has been notified. We are claiming SLA credits and reserve the right to pursue legal remedies.",
        "sender_email": "bob@enterprise.com",
        "contact_name": "Bob Jones",
        "expected_decision": "Legal-Flag",
    },
    {
        "id": "test_pricing_01",
        "subject": "Upgrade to Enterprise - 10 Additional Seats",
        "body": "Hi, I'd like to upgrade my subscription to Enterprise plan and add 10 seats mid-cycle. Can you provide pricing for pro-rata billing?",
        "sender_email": "alice@nonprofit.org",
        "contact_name": "Alice Chen",
        "expected_decision": "Auto-Reply",
    },
]


async def run_dry_run(scenario_id: str = None) -> list[Dict[str, Any]]:
    """
    Run dry-run simulations on predefined test scenarios.
    
    Args:
        scenario_id: Run only a specific scenario (or all if None)
    
    Returns:
        List of results with pass/fail status
    """
    agent = TriageAgent(max_steps=5)
    scenarios = DRY_RUN_SCENARIOS
    
    if scenario_id:
        scenarios = [s for s in scenarios if s["id"] == scenario_id]

    results = []
    for scenario in scenarios:
        logger.info(f"Running dry-run scenario: {scenario['id']}")
        
        result = await agent.run(
            email_id=scenario["id"],
            subject=scenario["subject"],
            body=scenario["body"],
            sender_email=scenario["sender_email"],
            contact_name=scenario.get("contact_name"),
            dry_run=True,
        )
        
        decision = result["decision"]
        expected = scenario["expected_decision"]
        passed = decision == expected
        
        results.append({
            "scenario_id": scenario["id"],
            "subject": scenario["subject"],
            "expected_decision": expected,
            "actual_decision": decision,
            "classification": result["classification"],
            "sentiment": result["sentiment"],
            "confidence": result["confidence"],
            "step_count": len(result["steps"]),
            "passed": passed,
        })
        
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(
            f"{status} | {scenario['id']}: expected={expected}, got={decision} "
            f"(class={result['classification']}, sentiment={result['sentiment']})"
        )

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    logger.info(f"\nDry-run complete: {passed}/{total} passed")
    
    return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_dry_run())
