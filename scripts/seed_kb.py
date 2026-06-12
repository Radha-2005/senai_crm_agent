#!/usr/bin/env python
"""
scripts/seed_kb.py - Standalone script to seed the knowledge base.
Run this once after setting up the project to index policy documents.

Usage:
    python scripts/seed_kb.py
"""
import asyncio
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    from backend.rag.kb_seed import seed_knowledge_base
    from backend.rag.rag_service import get_kb_stats

    logger.info("Starting knowledge base seeding...")
    count = await seed_knowledge_base()
    
    if count > 0:
        stats = get_kb_stats()
        logger.info(f"✓ Knowledge base seeded successfully!")
        logger.info(f"  Total chunks indexed: {stats['document_count']}")
        logger.info(f"  Collection: {stats['collection_name']}")
    else:
        logger.error("✗ Knowledge base seeding failed or no documents found")
        logger.info("  Make sure knowledge_base/*.md files exist")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
