#!/usr/bin/env python
"""
scripts/replay_dataset.py - Replay the email dataset through the ingestion API.
Loads emails from dataset/email-data-advanced.json and POSTs them to the ingest endpoint.
Handles the actual dataset format with fields: message_id, sender, subject, body, timestamp, thread_id.

Usage:
    python scripts/replay_dataset.py [--limit N] [--url http://localhost:8000] [--delay 0.5]
"""
import asyncio
import json
import sys
import argparse
import logging
from pathlib import Path

try:
    import httpx
except ImportError:
    print("httpx not installed. Run: pip install httpx")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

DATASET_PATH = Path(__file__).parent.parent / "dataset" / "email-data-advanced.json"


def load_dataset(path: Path) -> list:
    """Load and validate the email dataset."""
    if not path.exists():
        logger.error(f"Dataset not found: {path}")
        logger.info("Looking for dataset in other locations...")
        # Try current directory
        alt_path = Path("email-data-advanced.json")
        if alt_path.exists():
            path = alt_path
        else:
            logger.error(f"Dataset not found. Expected at: {DATASET_PATH}")
            sys.exit(1)
    
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Handle both list and dict format
    if isinstance(data, dict):
        emails = data.get("emails", data.get("data", []))
    elif isinstance(data, list):
        emails = data
    else:
        logger.error("Unexpected dataset format")
        sys.exit(1)
    
    return emails


def normalize_email(email: dict, index: int) -> dict:
    """
    Normalize an email record from the dataset format to the ingestion API schema.
    
    Dataset format uses:  message_id, sender, subject, body, timestamp, thread_id
    API format requires:  id, sender_email, subject, body, received_at, thread_id
    """
    # Handle both dataset format (message_id/sender) and API format (id/sender_email)
    email_id = (
        email.get("message_id") or 
        email.get("id") or 
        f"msg_{index:04d}"
    )
    sender_email = (
        email.get("sender") or 
        email.get("sender_email") or 
        f"unknown_{index}@example.com"
    )
    received_at = (
        email.get("timestamp") or 
        email.get("received_at") or 
        email.get("date")
    )
    
    return {
        "id": email_id,
        "thread_id": email.get("thread_id"),
        "subject": email.get("subject", ""),
        "body": email.get("body") or email.get("content") or "",
        "sender_email": sender_email,
        "sender_name": email.get("sender_name") or email.get("name"),
        "company": email.get("company"),
        "received_at": received_at,
        "tags": email.get("tags", []),
        "ltv": float(email.get("ltv", 0.0)),
        "tier": email.get("tier", "standard"),
    }


async def replay(base_url: str, limit: int = None, delay: float = 0.3):
    """Send all emails from the dataset to the ingest endpoint."""
    emails = load_dataset(DATASET_PATH)
    
    if limit:
        emails = emails[:limit]
    
    logger.info(f"🚀 Replaying {len(emails)} emails to {base_url}/api/v1/ingest")
    logger.info(f"   Delay between emails: {delay}s")

    success = 0
    failed = 0
    skipped = 0
    results = []

    async with httpx.AsyncClient(timeout=60) as client:
        for i, raw_email in enumerate(emails):
            payload = normalize_email(raw_email, i + 1)
            
            try:
                resp = await client.post(
                    f"{base_url}/api/v1/ingest",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                
                if resp.status_code == 202:
                    success += 1
                    data = resp.json()
                    emoji = "✅"
                    msg = f"accepted → job_id={data.get('job_id', 'N/A')}"
                elif resp.status_code == 409:
                    skipped += 1
                    emoji = "⏭️ "
                    msg = "skipped (duplicate/blocklist)"
                else:
                    failed += 1
                    emoji = "❌"
                    msg = f"FAILED HTTP {resp.status_code}: {resp.text[:80]}"
                
                logger.info(f"{emoji} [{i+1:2d}/{len(emails)}] {payload['id']:15s} | {payload['sender_email'][:35]:35s} | {msg}")
                results.append({"id": payload["id"], "status": resp.status_code})
                    
            except Exception as e:
                failed += 1
                logger.error(f"❌ [{i+1}/{len(emails)}] Error sending {payload['id']}: {e}")
                results.append({"id": payload["id"], "status": "error"})
            
            # Configurable delay to avoid overwhelming the server
            await asyncio.sleep(delay)

    logger.info(f"\n{'='*60}")
    logger.info(f"📊 Replay complete:")
    logger.info(f"   ✅ Accepted: {success}")
    logger.info(f"   ⏭️  Skipped (duplicate/blocklist): {skipped}")
    logger.info(f"   ❌ Failed: {failed}")
    logger.info(f"{'='*60}")
    logger.info(f"🌐 View results at: http://localhost:5173")
    logger.info(f"📖 API docs at: {base_url}/api/docs")
    
    return results


def main():
    parser = argparse.ArgumentParser(
        description="Replay email dataset through SenAI ingest API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/replay_dataset.py
  python scripts/replay_dataset.py --limit 10
  python scripts/replay_dataset.py --delay 1.0
  python scripts/replay_dataset.py --url http://localhost:8000 --limit 5
        """,
    )
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL of the API (default: http://localhost:8000)")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of emails to replay")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay in seconds between emails (default: 0.3)")
    args = parser.parse_args()
    
    asyncio.run(replay(args.url, args.limit, args.delay))


if __name__ == "__main__":
    main()
