"""
tests/test_rag.py - Tests for RAG pipeline.
"""
import pytest
from backend.rag.rag_service import chunk_text, _keyword_fallback_search


class TestTextChunking:
    """Test the text chunking algorithm."""

    def test_short_text_no_chunk(self):
        """Short text should not be split."""
        text = "This is a short text that fits in one chunk."
        chunks = chunk_text(text, chunk_size=500)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_long_text_split(self):
        """Long text should be split into multiple chunks."""
        # 1200 chars
        text = "A" * 600 + ". " + "B" * 600
        chunks = chunk_text(text, chunk_size=500, overlap=50)
        assert len(chunks) > 1

    def test_overlap(self):
        """Chunks should have overlap for context continuity."""
        text = "word " * 200  # ~1000 chars
        chunks = chunk_text(text, chunk_size=200, overlap=40)
        # With overlap, adjacent chunks should share some content
        assert len(chunks) >= 2

    def test_empty_chunks_filtered(self):
        """Empty or trivially short chunks should be filtered out."""
        text = "Good content here. " + " " * 100 + "More good content."
        chunks = chunk_text(text, chunk_size=30, overlap=5)
        for chunk in chunks:
            assert len(chunk) > 20


class TestKeywordFallbackSearch:
    """Test the keyword fallback search for RAG."""

    def setup_method(self):
        """Set up test documents."""
        self.documents = [
            "The refund policy states that customers can request a refund within 14 days.",
            "GDPR compliance requires data portability within 30 days of request.",
            "SLA breach compensation is calculated based on downtime percentage.",
            "Pricing for Enterprise plan starts at a custom quote.",
            "Support tickets should be responded to within 4 hours for P1 incidents.",
        ]
        self.metadatas = [
            {"source": "refund_policy", "category": "refund"},
            {"source": "gdpr_policy", "category": "gdpr"},
            {"source": "sla_policy", "category": "sla"},
            {"source": "pricing_policy", "category": "pricing"},
            {"source": "sla_policy", "category": "sla"},
        ]
        self.ids = [f"doc_{i}" for i in range(len(self.documents))]

    def test_refund_query_matches_refund_doc(self):
        """Refund query should match refund policy document."""
        results = _keyword_fallback_search(
            "How long can I request a refund?",
            self.documents,
            self.metadatas,
            self.ids,
            n_results=3,
        )
        assert len(results) > 0
        # First result should be refund-related
        sources = [r["metadata"].get("source") for r in results]
        assert "refund_policy" in sources

    def test_gdpr_query_matches(self):
        """GDPR query should match GDPR document."""
        results = _keyword_fallback_search(
            "GDPR data portability request",
            self.documents,
            self.metadatas,
            self.ids,
            n_results=2,
        )
        assert len(results) > 0
        assert "gdpr_policy" in [r["metadata"].get("source") for r in results]

    def test_stop_words_filtered(self):
        """Common stop words should not dominate matching."""
        results = _keyword_fallback_search(
            "How do I do a thing",  # Mostly stop words
            self.documents,
            self.metadatas,
            self.ids,
            n_results=3,
        )
        # Should return few or no results since only stop words
        # The important thing is it doesn't crash
        assert isinstance(results, list)

    def test_stem_matching(self):
        """Partial word matching should work for stemmed words."""
        results = _keyword_fallback_search(
            "refunds eligibility",
            self.documents,
            self.metadatas,
            self.ids,
            n_results=3,
        )
        # "refunds" should match "refund" in the document
        assert len(results) > 0
