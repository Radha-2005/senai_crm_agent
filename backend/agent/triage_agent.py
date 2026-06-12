"""
agent/triage_agent.py - Autonomous ReAct (Reason + Act) triage agent.
Analyzes emails and decides on routing: Auto-Reply, Escalate, Legal-Flag, Human-Review.

The agent uses a step-limited loop:
  1. THINK: Analyze email context and decide next action
  2. ACT: Execute tool
  3. OBSERVE: Process tool result
  4. Repeat until decision is reached or max steps hit
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.agent.tools import execute_tool, TOOL_REGISTRY
from backend.llm.reply_generator import generate_reply
from backend.llm.classifier import classify_with_llm
from backend.services.classification_service import classify_email
from backend.db.models import AgentDecision

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Decision routing constants
# ---------------------------------------------------------------------------

AUTO_REPLY = AgentDecision.AUTO_REPLY.value      # "Auto-Reply"
ESCALATE = AgentDecision.ESCALATE.value           # "Escalate"
LEGAL_FLAG = AgentDecision.LEGAL_FLAG.value       # "Legal-Flag"
HUMAN_REVIEW = AgentDecision.HUMAN_REVIEW.value   # "Human-Review"
IGNORE = AgentDecision.IGNORE.value               # "Ignore"


# ---------------------------------------------------------------------------
# Rule-based decision matrix (applied before LLM reasoning)
# ---------------------------------------------------------------------------

def _determine_initial_decision(
    classification: str,
    sentiment: str,
    confidence: float,
    subject: str,
    body: str,
) -> Optional[str]:
    """
    Apply rule-based decision routing based on classification and sentiment.
    Returns a decision or None (meaning LLM should reason further).
    
    Routing priority (highest to lowest):
    1. GDPR / Legal documents → Legal-Flag (always)
    2. Security threats (ransomware, data breach) → Legal-Flag
    3. Formal legal threats with attorney/lawsuit → Legal-Flag
    4. AI/Chatbot misinformation → Escalate (liability issue)
    5. Critical sentiment (extreme anger) → Escalate
    6. Refund + negative → Escalate
    7. Pricing inquiry + neutral/positive → Auto-Reply
    8. Spam → Ignore
    """
    text = f"{subject} {body}".lower()

    # --- TIER 1: Always Legal-Flag ---
    if classification == "legal_gdpr":
        return LEGAL_FLAG
    
    if classification == "security_threat":
        return LEGAL_FLAG  # Security threats → legal + security team

    # Formal legal threats: must include attorney/lawyer/lawsuit/cease AND desist
    # NOT just a customer saying 'I'll take legal action' in anger
    formal_legal_indicators = [
        "cease and desist",
        "my attorney",
        "our attorney",
        "my lawyer",
        "our lawyer",
        "my legal team",
        "our legal team",
        "legal team is involved",
        "formal correspondence",
        "pending legal",
        "file a lawsuit",
        "initiate legal proceedings",
        "breach of contract",
        "class action",
    ]
    # SLA breach with formal legal involvement
    sla_legal_indicators = [
        "sla breach",
        "service level",
    ]
    
    has_formal_legal = any(kw in text for kw in formal_legal_indicators)
    has_sla_legal = classification == "legal_threat" or (
        any(kw in text for kw in sla_legal_indicators) and has_formal_legal
    )
    
    if has_formal_legal or has_sla_legal:
        return LEGAL_FLAG

    # --- TIER 2: Always Escalate ---
    # AI/Chatbot misinformation
    if classification == "ai_misinformation" or any(
        kw in text for kw in ["chatbot told me", "your ai told", "bot said", "chatbot gave", "chatbot said"]
    ):
        return ESCALATE

    # Critical sentiment (extreme anger, threatening public reviews)
    if sentiment == "critical":
        return ESCALATE

    # --- TIER 3: Context-based routing ---
    if classification == "refund_request" and sentiment in ("negative", "critical"):
        return ESCALATE

    if classification in ("pricing_inquiry",) and sentiment in ("positive", "neutral"):
        return AUTO_REPLY

    if classification == "technical_support" and sentiment == "negative":
        return ESCALATE

    if classification == "spam":
        return IGNORE

    # Low confidence → human review
    if confidence < 0.5:
        return HUMAN_REVIEW

    return None  # Let reasoning loop continue


# ---------------------------------------------------------------------------
# ReAct Agent
# ---------------------------------------------------------------------------

class TriageAgent:
    """
    Autonomous ReAct triage agent for customer email processing.
    
    Implements a structured reasoning loop:
    - Think about what information is needed
    - Act by calling tools
    - Observe results
    - Make final decision
    """

    def __init__(self, max_steps: int = None):
        self.max_steps = max_steps or settings.AGENT_MAX_STEPS

    async def run(
        self,
        email_id: str,
        subject: str,
        body: str,
        sender_email: str,
        thread_id: Optional[str] = None,
        contact_name: Optional[str] = None,
        contact_company: Optional[str] = None,
        db: Optional[AsyncSession] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """
        Run the full triage pipeline for a given email.
        
        Returns:
            Dict containing:
                - decision: Final routing decision
                - steps: List of reasoning steps taken
                - draft_reply: Generated draft reply (if applicable)
                - classification: Email classification label
                - sentiment: Sentiment label
                - confidence: Classification confidence
        """
        steps = []
        step_count = 0

        # ---------------------------------------------------------------
        # Step 0: Multi-layer classification
        # ---------------------------------------------------------------
        classification, confidence, sentiment, _ = classify_email(subject, body)
        
        # Use LLM for low-confidence cases
        if confidence < 0.6 and settings.llm_api_key:
            llm_label, llm_confidence = await classify_with_llm(
                subject, body, fallback_label=classification
            )
            if llm_confidence > confidence:
                classification = llm_label
                confidence = llm_confidence

        steps.append({
            "step": 0,
            "type": "classify",
            "thought": f"Classified as '{classification}' (confidence={confidence:.2f}), sentiment='{sentiment}'",
            "result": {
                "classification": classification,
                "confidence": confidence,
                "sentiment": sentiment,
            },
        })

        # ---------------------------------------------------------------
        # Step 1: Rule-based pre-decision
        # ---------------------------------------------------------------
        initial_decision = _determine_initial_decision(
            classification, sentiment, confidence, subject, body
        )
        if initial_decision:
            steps.append({
                "step": 1,
                "type": "decide",
                "thought": f"Rule-based routing: classification='{classification}', sentiment='{sentiment}' → {initial_decision}",
                "result": {"decision": initial_decision},
            })
            # Even with rule-based decision, gather policy context and draft reply
            decision = initial_decision
        else:
            decision = None

        # ---------------------------------------------------------------
        # ReAct reasoning loop
        # ---------------------------------------------------------------
        policy_context = None
        
        while step_count < self.max_steps:
            step_count += 1

            # ---------- THINK ----------
            next_action = self._think(
                step_count=step_count,
                classification=classification,
                sentiment=sentiment,
                confidence=confidence,
                subject=subject,
                body=body,
                decision=decision,
                steps=steps,
                contact_company=contact_company,
                thread_id=thread_id,
            )

            if next_action is None:
                # Agent has enough information to decide
                break

            tool_name, tool_args = next_action
            
            # ---------- ACT ----------
            thought = f"Step {step_count}: Calling tool '{tool_name}' with args: {tool_args}"
            logger.debug(thought)

            if dry_run:
                # In dry-run mode, simulate tool execution
                tool_result = {"dry_run": True, "tool": tool_name, "args": tool_args}
            else:
                tool_result = await execute_tool(tool_name, tool_args, db=db)

            # ---------- OBSERVE ----------
            steps.append({
                "step": step_count,
                "type": "react",
                "tool": tool_name,
                "args": tool_args,
                "thought": thought,
                "result": tool_result,
            })

            # Extract policy context from search results
            if tool_name == "search_policy" and tool_result.get("found"):
                policy_context = tool_result.get("context")

            # Check if we have reached a decision from tool results
            if not decision and tool_result.get("error"):
                decision = HUMAN_REVIEW
                break

        # ---------------------------------------------------------------
        # Final decision (if not already determined by rules)
        # ---------------------------------------------------------------
        if not decision:
            decision = self._make_final_decision(
                classification, sentiment, confidence, steps
            )

        steps.append({
            "step": step_count + 1,
            "type": "final_decision",
            "thought": f"Final routing decision: {decision}",
            "result": {"decision": decision},
        })

        # ---------------------------------------------------------------
        # Generate draft reply (for Auto-Reply and Escalate decisions)
        # ---------------------------------------------------------------
        draft_reply = None
        if decision in (AUTO_REPLY, ESCALATE, HUMAN_REVIEW) and not dry_run:
            draft_reply = await generate_reply(
                subject=subject,
                body=body,
                contact_name=contact_name,
                classification=classification,
                policy_context=policy_context,
                tone="empathetic" if sentiment in ("negative", "critical") else "professional",
            )

        logger.info(
            f"Triage complete for email {email_id}: "
            f"decision={decision}, classification={classification}, "
            f"sentiment={sentiment}, steps={len(steps)}"
        )

        return {
            "email_id": email_id,
            "decision": decision,
            "classification": classification,
            "confidence": confidence,
            "sentiment": sentiment,
            "steps": steps,
            "draft_reply": draft_reply,
            "processed_at": datetime.utcnow().isoformat(),
        }

    def _think(
        self,
        step_count: int,
        classification: str,
        sentiment: str,
        confidence: float,
        subject: str,
        body: str,
        decision: Optional[str],
        steps: List[dict],
        contact_company: Optional[str],
        thread_id: Optional[str],
    ) -> Optional[Tuple[str, Dict]]:
        """
        Determine the next tool to call based on current context.
        Returns (tool_name, tool_args) or None to stop the loop.
        """
        executed_tools = {s.get("tool") for s in steps if s.get("type") == "react"}

        # Step 1: Always search policy for high-stakes classifications
        if "search_policy" not in executed_tools:
            if classification in ("legal_gdpr", "refund_request", "pricing_inquiry",
                                  "legal_threat", "ai_misinformation", "security_threat"):
                # Map classification to policy query
                policy_queries = {
                    "legal_gdpr": "GDPR data subject rights data portability request",
                    "refund_request": "refund policy eligibility time limit",
                    "pricing_inquiry": "pricing upgrade pro-rata seat pricing",
                    "legal_threat": "SLA service level agreement credits breach",
                    "ai_misinformation": "chatbot AI response liability refund policy",
                    "security_threat": "security incident response ransomware policy",
                }
                query = policy_queries.get(classification, f"{classification} policy")
                return "search_policy", {"query": query, "n_results": 3}

        # Step 2: For high-value customers, scrape company reputation
        if "scrape_company_reputation" not in executed_tools:
            if (
                classification in ("refund_request", "complaint", "legal_threat")
                and sentiment in ("negative", "critical")
                and contact_company
                and str(contact_company) != "None"
            ):
                return "scrape_company_reputation", {"company_name": str(contact_company)}

        # Step 3: For legal/security cases, create internal ticket
        if "create_internal_ticket" not in executed_tools:
            if decision in (LEGAL_FLAG, ESCALATE):
                priority_map = {
                    LEGAL_FLAG: "critical",
                    ESCALATE: "high",
                }
                return "create_internal_ticket", {
                    "title": f"{decision}: {subject[:80]}",
                    "description": f"Automated triage: {classification} | Sentiment: {sentiment}",
                    "priority": priority_map.get(decision, "medium"),
                    "assignee": "legal" if decision == LEGAL_FLAG else "support-lead",
                }

        # Step 4: For legal flags, formally flag in system
        if "flag_for_legal" not in executed_tools:
            if decision == LEGAL_FLAG:
                return "flag_for_legal", {
                    "email_id": "current_email",  # Will be replaced in executor
                    "reason": f"{classification}: {sentiment} sentiment detected",
                }

        # Stop — we have enough context
        return None

    def _make_final_decision(
        self,
        classification: str,
        sentiment: str,
        confidence: float,
        steps: List[dict],
    ) -> str:
        """Make final decision based on all gathered context."""
        # Check if ticket was created
        ticket_created = any(
            s.get("tool") == "create_internal_ticket"
            for s in steps
        )

        if classification in ("legal_gdpr", "security_threat", "legal_threat"):
            return LEGAL_FLAG

        if classification in ("ai_misinformation", "complaint") and sentiment in ("negative", "critical"):
            return ESCALATE

        if classification in ("refund_request",) and sentiment in ("negative", "critical"):
            return ESCALATE

        if classification in ("pricing_inquiry", "general_inquiry"):
            return AUTO_REPLY

        if confidence < 0.5:
            return HUMAN_REVIEW

        return ESCALATE  # Default to escalate for uncertain cases
