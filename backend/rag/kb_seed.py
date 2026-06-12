"""
rag/kb_seed.py - Knowledge base seeding module.
Loads markdown policy documents and indexes them into ChromaDB.
"""
import logging
import uuid
from pathlib import Path
from typing import List, Tuple

from backend.rag.rag_service import add_documents, chunk_text

logger = logging.getLogger(__name__)

# Path to knowledge base markdown files
KB_DIR = Path(__file__).parent.parent.parent / "knowledge_base"


def load_markdown_files(kb_dir: Path) -> List[Tuple[str, str, str]]:
    """
    Load all markdown files from the knowledge base directory.
    
    Returns:
        List of (filename_stem, content, category) tuples
    """
    if not kb_dir.exists():
        logger.error(f"Knowledge base directory not found: {kb_dir}")
        return []

    results = []
    for md_file in kb_dir.glob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8")
            # Infer category from filename
            stem = md_file.stem.lower()
            if "gdpr" in stem or "privacy" in stem:
                category = "gdpr_privacy"
            elif "refund" in stem:
                category = "refund"
            elif "sla" in stem or "service" in stem:
                category = "sla"
            elif "security" in stem:
                category = "security"
            elif "pricing" in stem or "billing" in stem:
                category = "pricing"
            else:
                category = "general"
            results.append((md_file.stem, content, category))
            logger.info(f"Loaded KB file: {md_file.name} ({len(content)} chars)")
        except Exception as e:
            logger.error(f"Failed to load {md_file}: {e}")

    return results


async def seed_knowledge_base(kb_dir: Path = KB_DIR) -> int:
    """
    Seed the ChromaDB knowledge base from markdown files.
    
    Returns:
        Number of chunks indexed
    """
    docs = load_markdown_files(kb_dir)
    if not docs:
        logger.warning("No knowledge base documents found to seed")
        return 0

    all_documents = []
    all_metadatas = []
    all_ids = []

    for filename, content, category in docs:
        chunks = chunk_text(content, chunk_size=500, overlap=50)
        for i, chunk in enumerate(chunks):
            chunk_id = f"{filename}_chunk_{i}_{uuid.uuid4().hex[:8]}"
            all_documents.append(chunk)
            all_metadatas.append({
                "source": filename,
                "category": category,
                "chunk_index": i,
            })
            all_ids.append(chunk_id)

    success = await add_documents(all_documents, all_metadatas, all_ids)
    if success:
        logger.info(f"Seeded {len(all_documents)} chunks from {len(docs)} documents")
        return len(all_documents)
    else:
        logger.error("Knowledge base seeding failed")
        return 0
