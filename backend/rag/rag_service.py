"""
rag/rag_service.py - Retrieval-Augmented Generation service.
Uses ChromaDB for vector storage and SentenceTransformers for embeddings.
Provides policy retrieval for the agent's decision-making context.
"""
import logging
import re
from typing import List, Optional, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)

# Lazy initialization to avoid heavy imports at startup
_chroma_client = None
_collection = None
_embedder = None

COLLECTION_NAME = "senai_knowledge_base"
STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "for",
    "of", "and", "or", "but", "not", "with", "this", "that", "are",
    "was", "be", "have", "do", "can", "how", "what", "when", "where",
    "who", "why", "my", "i", "me", "we", "you", "he", "she", "they"
}


def _get_embedder():
    """Lazy load sentence transformer model."""
    global _embedder
    if _embedder is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("SentenceTransformer model loaded")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformer: {e}")
            _embedder = None
    return _embedder


def _get_collection():
    """Lazy load ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        try:
            import chromadb
            from backend.config import settings
            _chroma_client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            _collection = _chroma_client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info(f"ChromaDB collection loaded: {_collection.count()} documents")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            _collection = None
    return _collection


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """
    Split text into overlapping chunks for indexing.
    
    Args:
        text: Input text to chunk
        chunk_size: Target chunk size in characters
        overlap: Overlap between consecutive chunks
    
    Returns:
        List of text chunks
    """
    if not text or not text.strip():
        return []
    if len(text) <= chunk_size:
        return [text.strip()]
    
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        # Extend to nearest sentence boundary if possible
        if end < len(text):
            last_period = text.rfind(".", start, end)
            if last_period > start + chunk_size // 2:
                end = last_period + 1
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # CRITICAL: always advance forward; never let start go backwards
        next_start = end - overlap
        if next_start <= start:
            next_start = end   # no overlap if it would cause regression
        if next_start >= len(text):
            break
        start = next_start
    
    return [c for c in chunks if len(c) > 20]  # Filter trivially short chunks


def _keyword_fallback_search(
    query: str,
    documents: List[str],
    metadatas: List[dict],
    ids: List[str],
    n_results: int = 3,
) -> List[Dict[str, Any]]:
    """
    Keyword-based fallback search when embeddings are unavailable.
    Uses partial word matching with stop-word filtering.
    """
    # Extract meaningful query terms
    query_terms = [
        word.lower().strip(".,!?")
        for word in query.split()
        if word.lower() not in STOP_WORDS and len(word) > 2
    ]
    
    scored = []
    for i, doc in enumerate(documents):
        doc_lower = doc.lower()
        score = 0
        for term in query_terms:
            # Partial/stem matching: "refund" matches "refunds", "refunded"
            if re.search(r'\b' + re.escape(term), doc_lower):
                score += 2  # Exact word match
            elif term in doc_lower:
                score += 1  # Substring match
        if score > 0:
            scored.append({
                "id": ids[i],
                "document": doc,
                "metadata": metadatas[i] if i < len(metadatas) else {},
                "score": score,
            })
    
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:n_results]


async def add_documents(
    documents: List[str],
    metadatas: List[dict],
    ids: List[str],
) -> bool:
    """
    Add documents to the ChromaDB knowledge base.
    
    Returns:
        True on success, False on failure
    """
    collection = _get_collection()
    embedder = _get_embedder()
    
    if not collection:
        logger.error("ChromaDB collection unavailable, cannot add documents")
        return False

    try:
        if embedder:
            embeddings = embedder.encode(documents, show_progress_bar=False).tolist()
            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids,
            )
        else:
            # Add without custom embeddings (ChromaDB uses its default)
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids,
            )
        logger.info(f"Added {len(documents)} documents to knowledge base")
        return True
    except Exception as e:
        logger.error(f"Failed to add documents: {e}")
        return False


async def search_knowledge_base(
    query: str,
    n_results: int = 3,
    filter_metadata: Optional[dict] = None,
) -> List[Dict[str, Any]]:
    """
    Search the knowledge base for relevant policy documents.
    
    Args:
        query: Search query string
        n_results: Number of results to return
        filter_metadata: Optional ChromaDB metadata filter
    
    Returns:
        List of result dicts with 'document', 'metadata', 'id', 'score'
    """
    collection = _get_collection()
    
    if not collection or collection.count() == 0:
        logger.warning("Knowledge base is empty or unavailable")
        return []

    embedder = _get_embedder()

    try:
        if embedder:
            query_embedding = embedder.encode([query], show_progress_bar=False).tolist()
            results = collection.query(
                query_embeddings=query_embedding,
                n_results=min(n_results, collection.count()),
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )
        else:
            # Text-based query fallback
            results = collection.query(
                query_texts=[query],
                n_results=min(n_results, collection.count()),
                where=filter_metadata,
                include=["documents", "metadatas", "distances"],
            )

        if not results or not results.get("documents"):
            return []

        output = []
        docs = results["documents"][0]
        metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
        ids = results["ids"][0] if results.get("ids") else [""] * len(docs)
        distances = results["distances"][0] if results.get("distances") else [0.0] * len(docs)

        for i, doc in enumerate(docs):
            similarity = 1.0 - (distances[i] if distances[i] else 0.0)
            output.append({
                "id": ids[i],
                "document": doc,
                "metadata": metas[i] if metas else {},
                "score": round(similarity, 4),
            })

        # Apply keyword fallback if all scores are very low
        if output and all(r["score"] < 0.3 for r in output):
            logger.info("Low similarity scores, applying keyword fallback")
            all_results = collection.get(include=["documents", "metadatas"])
            fallback = _keyword_fallback_search(
                query,
                all_results["documents"],
                all_results["metadatas"],
                all_results["ids"],
                n_results,
            )
            if fallback:
                return fallback

        return output

    except Exception as e:
        logger.error(f"Knowledge base search failed: {e}")
        # Try keyword fallback
        try:
            all_results = collection.get(include=["documents", "metadatas"])
            return _keyword_fallback_search(
                query,
                all_results["documents"],
                all_results["metadatas"],
                all_results["ids"],
                n_results,
            )
        except Exception:
            return []


def get_kb_stats() -> Dict[str, Any]:
    """Return knowledge base statistics."""
    collection = _get_collection()
    if not collection:
        return {"status": "unavailable", "document_count": 0}
    return {
        "status": "ok",
        "document_count": collection.count(),
        "collection_name": COLLECTION_NAME,
    }
