"""
api/rag.py - Knowledge base RAG API endpoints.
Provides search and management of the policy knowledge base.
"""
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from backend.rag.rag_service import search_knowledge_base, get_kb_stats
from backend.rag.kb_seed import seed_knowledge_base

router = APIRouter(prefix="/api/v1", tags=["knowledge-base"])


class SearchRequest(BaseModel):
    query: str
    n_results: int = 3


class SearchResult(BaseModel):
    id: str
    document: str
    metadata: dict
    score: float


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int


@router.post(
    "/rag/search",
    response_model=SearchResponse,
    summary="Search knowledge base",
)
async def search_kb(body: SearchRequest) -> SearchResponse:
    """Search the policy knowledge base using semantic similarity."""
    results = await search_knowledge_base(body.query, n_results=body.n_results)
    return SearchResponse(
        query=body.query,
        results=[SearchResult(**r) for r in results],
        total=len(results),
    )


@router.get(
    "/rag/stats",
    summary="Knowledge base statistics",
)
async def kb_stats() -> dict:
    """Get knowledge base document count and status."""
    return get_kb_stats()


@router.post(
    "/rag/seed",
    summary="Re-seed knowledge base from markdown files",
    status_code=status.HTTP_202_ACCEPTED,
)
async def reseed_kb() -> dict:
    """Re-index all markdown policy documents into the knowledge base."""
    count = await seed_knowledge_base()
    return {
        "message": f"Knowledge base seeded with {count} chunks",
        "chunks_indexed": count,
    }
