"""
agent/tools.py - Agent tool definitions for the ReAct loop.
Each tool is an async function that the agent can call during triage.
"""
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.db.models import Email, Thread, Contact
from backend.rag.rag_service import search_knowledge_base
from backend.web_intelligence.reputation_service import get_company_reputation

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool registry — maps tool_name -> (function, description, parameters_schema)
# ---------------------------------------------------------------------------

TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {}


def register_tool(name: str, description: str, parameters: dict):
    """Decorator to register an agent tool."""
    def decorator(func):
        TOOL_REGISTRY[name] = {
            "function": func,
            "description": description,
            "parameters": parameters,
        }
        return func
    return decorator


# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------

@register_tool(
    name="search_policy",
    description="Search company policy documents in the knowledge base",
    parameters={
        "query": {"type": "string", "description": "Policy search query"},
        "n_results": {"type": "integer", "description": "Number of results", "default": 3},
    },
)
async def search_policy(query: str, n_results: int = 3, **kwargs) -> Dict[str, Any]:
    """Search policy documents via RAG."""
    results = await search_knowledge_base(query, n_results=n_results)
    if not results:
        return {"found": False, "context": "No relevant policy found for this query."}
    
    combined = "\n\n---\n\n".join(
        f"[{r['metadata'].get('source', 'Policy')}]\n{r['document']}"
        for r in results
    )
    return {
        "found": True,
        "context": combined,
        "sources": [r["metadata"].get("source") for r in results],
    }


@register_tool(
    name="get_customer_profile",
    description="Retrieve customer profile and history from CRM",
    parameters={
        "email": {"type": "string", "description": "Customer email address"},
    },
)
async def get_customer_profile(
    email: str,
    db: Optional[AsyncSession] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Fetch customer profile and basic stats from database."""
    if not db:
        return {"found": False, "message": "No database connection"}

    result = await db.execute(
        select(Contact).where(Contact.email == email)
    )
    contact = result.scalar_one_or_none()
    if not contact:
        return {"found": False, "email": email, "message": "Customer not found in CRM"}

    # Count emails
    email_count_result = await db.execute(
        select(Email).where(Email.contact_id == contact.id)
    )
    emails = email_count_result.scalars().all()

    return {
        "found": True,
        "id": contact.id,
        "name": contact.name,
        "email": contact.email,
        "company": contact.company or "Unknown",
        "tier": contact.tier,
        "ltv": contact.ltv,
        "tags": contact.tags or [],
        "email_count": len(emails),
        "customer_since": contact.created_at.isoformat() if contact.created_at else None,
    }


@register_tool(
    name="get_thread_history",
    description="Get full email thread history for context",
    parameters={
        "thread_id": {"type": "string", "description": "Thread ID to retrieve"},
    },
)
async def get_thread_history(
    thread_id: str,
    db: Optional[AsyncSession] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Fetch all emails in a thread."""
    if not db:
        return {"found": False, "message": "No database connection"}

    result = await db.execute(
        select(Thread).where(Thread.id == thread_id)
    )
    thread = result.scalar_one_or_none()
    if not thread:
        return {"found": False, "thread_id": thread_id}

    email_result = await db.execute(
        select(Email)
        .where(Email.thread_id == thread_id)
        .order_by(Email.received_at)
    )
    emails = email_result.scalars().all()

    return {
        "found": True,
        "thread_id": thread_id,
        "status": thread.status,
        "email_count": len(emails),
        "emails": [
            {
                "id": e.id,
                "subject": e.subject,
                "body": (e.body or "")[:300],  # Truncate for context
                "sentiment": e.sentiment,
                "classification": e.classification,
                "received_at": e.received_at.isoformat() if e.received_at else None,
            }
            for e in emails
        ],
    }


@register_tool(
    name="scrape_company_reputation",
    description="Scrape public web to assess company reputation and recent news",
    parameters={
        "company_name": {"type": "string", "description": "Company name to research"},
    },
)
async def scrape_company_reputation(
    company_name: str,
    **kwargs,
) -> Dict[str, Any]:
    """Check company reputation via web intelligence."""
    return await get_company_reputation(company_name)


@register_tool(
    name="create_internal_ticket",
    description="Create an internal ticket for escalation or follow-up",
    parameters={
        "title": {"type": "string", "description": "Ticket title"},
        "description": {"type": "string", "description": "Ticket description"},
        "priority": {"type": "string", "description": "Priority: low, medium, high, critical"},
        "assignee": {"type": "string", "description": "Team or person to assign to"},
    },
)
async def create_internal_ticket(
    title: str,
    description: str,
    priority: str = "medium",
    assignee: str = "support",
    **kwargs,
) -> Dict[str, Any]:
    """Simulate creating an internal support/escalation ticket."""
    import uuid
    ticket_id = f"TICKET-{uuid.uuid4().hex[:6].upper()}"
    logger.info(f"Created internal ticket {ticket_id}: {title} (priority={priority}, assignee={assignee})")
    return {
        "success": True,
        "ticket_id": ticket_id,
        "title": title,
        "priority": priority,
        "assignee": assignee,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
    }


@register_tool(
    name="flag_for_legal",
    description="Flag an email thread for legal team review",
    parameters={
        "email_id": {"type": "string", "description": "Email ID to flag"},
        "reason": {"type": "string", "description": "Reason for legal flag"},
    },
)
async def flag_for_legal(
    email_id: str,
    reason: str,
    db: Optional[AsyncSession] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Flag an email for the legal team."""
    logger.info(f"Legal flag raised for email {email_id}: {reason}")
    # In production, this would update the email record and notify legal team
    return {
        "success": True,
        "email_id": email_id,
        "flagged": True,
        "reason": reason,
        "legal_team_notified": True,
        "timestamp": datetime.utcnow().isoformat(),
    }


@register_tool(
    name="send_auto_reply",
    description="Send an automated reply to the customer",
    parameters={
        "email_id": {"type": "string", "description": "Email ID to reply to"},
        "reply_content": {"type": "string", "description": "Reply body text"},
    },
)
async def send_auto_reply(
    email_id: str,
    reply_content: str,
    **kwargs,
) -> Dict[str, Any]:
    """Simulate sending an automated reply."""
    logger.info(f"Auto-reply sent for email {email_id}: {reply_content[:100]}...")
    return {
        "success": True,
        "email_id": email_id,
        "reply_sent": True,
        "preview": reply_content[:200],
        "timestamp": datetime.utcnow().isoformat(),
    }


async def execute_tool(
    tool_name: str,
    tool_args: Dict[str, Any],
    db: Optional[AsyncSession] = None,
) -> Dict[str, Any]:
    """
    Execute a registered tool by name with given arguments.
    Injects db session for tools that need database access.
    """
    if tool_name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {tool_name}"}

    tool_func = TOOL_REGISTRY[tool_name]["function"]
    try:
        result = await tool_func(**tool_args, db=db)
        return result
    except Exception as e:
        logger.error(f"Tool {tool_name} failed: {e}")
        return {"error": str(e), "tool": tool_name}
