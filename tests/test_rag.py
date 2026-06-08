"""Tests for the RAG layer: chunking, ingestion, and retrieval."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from copilot.rag import chunk_document, ingest_references, retrieve, COLLECTION_NAME


SAMPLE_PRD = """# PRD: Automated Credit Limit Enforcement

## Summary

Build an automated credit limit enforcement system that prevents clients from exceeding their approved credit thresholds.

## Background & Context

Currently, credit limit checks are manual. Account managers verify limits in a spreadsheet before confirming shipments. This creates bottlenecks during peak season.

## Objective & Key Results

**Objective:** Reduce financial risk from credit overruns while maintaining booking speed.

**Key Results:**
- KR1: Zero credit limit breaches per quarter
- KR2: Credit check response time < 2 seconds
- KR3: Finance team time on credit monitoring reduced by 80%

## Solution

Real-time credit check at booking time with automated holds and override workflow.
"""

SAMPLE_TICKET = """## User Story: Implement credit check API endpoint

**As a** booking system
**I want to** validate available credit before confirming a booking
**So that** we prevent credit limit breaches automatically

### Acceptance Criteria
- API responds in < 200ms
- Returns green/yellow/red status
- Logs every check for audit trail
"""


class TestChunkDocument:
    """Tests for chunk_document function."""

    def test_small_document_single_chunk(self):
        text = "This is a short document."
        chunks = chunk_document(text)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_splits_on_paragraph_boundaries(self):
        paragraphs = [f"Paragraph {i} with enough content." for i in range(20)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_document(text, chunk_size=200, overlap=10)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_produces_multiple_chunks_for_large_docs(self):
        text = "\n\n".join([f"Section {i}: " + "x" * 100 for i in range(10)])
        chunks = chunk_document(text, chunk_size=300, overlap=10)
        assert len(chunks) > 1, "Large document should be split into multiple chunks"

    def test_overlap_creates_shared_content(self):
        paragraphs = [f"Word{i} " * 30 for i in range(10)]
        text = "\n\n".join(paragraphs)
        chunks = chunk_document(text, chunk_size=200, overlap=20)
        if len(chunks) >= 2:
            last_words_first = chunks[0].split()[-5:]
            found_overlap = any(w in chunks[1] for w in last_words_first)
            assert found_overlap, "Expected overlap between consecutive chunks"

    def test_empty_document(self):
        chunks = chunk_document("")
        assert len(chunks) == 0 or (len(chunks) == 1 and chunks[0] == "")

    def test_prd_chunking(self):
        chunks = chunk_document(SAMPLE_PRD)
        assert len(chunks) >= 1
        assert any("credit" in c.lower() for c in chunks)


class TestIngestionAndRetrieval:
    """Integration tests using a temporary directory structure."""

    @pytest.fixture(autouse=True)
    def setup_temp_dirs(self, tmp_path):
        """Create temp reference dirs and redirect rag.py to use them."""
        self.ref_docs = tmp_path / "reference_docs"
        self.ref_tickets = tmp_path / "reference_tickets"
        self.chroma_dir = tmp_path / ".chroma"
        self.ref_docs.mkdir()
        self.ref_tickets.mkdir()

        (self.ref_docs / "credit-prd.md").write_text(SAMPLE_PRD, encoding="utf-8")
        (self.ref_tickets / "credit-ticket.md").write_text(
            SAMPLE_TICKET, encoding="utf-8"
        )

        self.patches = [
            patch("copilot.rag.REFERENCE_DIRS", {
                "prd": self.ref_docs,
                "ticket": self.ref_tickets,
            }),
            patch("copilot.rag.CHROMA_DIR", self.chroma_dir),
        ]
        for p in self.patches:
            p.start()

        yield

        for p in self.patches:
            p.stop()

    def test_ingest_counts(self):
        counts = ingest_references()
        assert counts["prd"] > 0
        assert counts["ticket"] > 0
        assert sum(counts.values()) > 0

    def test_ingest_raises_on_empty_dirs(self, tmp_path):
        empty_docs = tmp_path / "empty_docs"
        empty_tickets = tmp_path / "empty_tickets"
        empty_docs.mkdir()
        empty_tickets.mkdir()
        with patch("copilot.rag.REFERENCE_DIRS", {
            "prd": empty_docs, "ticket": empty_tickets,
        }):
            with pytest.raises(FileNotFoundError):
                ingest_references()

    def test_retrieve_returns_relevant_chunks(self):
        ingest_references()
        result = retrieve("credit limit enforcement")
        assert len(result) > 0
        assert "credit" in result.lower()

    def test_retrieve_with_doc_type_filter(self):
        ingest_references()
        prd_result = retrieve("credit", doc_type="prd")
        ticket_result = retrieve("credit", doc_type="ticket")
        assert len(prd_result) > 0
        assert len(ticket_result) > 0

    def test_retrieve_empty_collection(self, tmp_path):
        fresh_chroma = tmp_path / ".chroma_empty"
        with patch("copilot.rag.CHROMA_DIR", fresh_chroma):
            result = retrieve("anything")
            assert result == ""

    def test_retrieve_n_results(self):
        ingest_references()
        result_1 = retrieve("credit", n_results=1)
        result_3 = retrieve("credit", n_results=3)
        assert len(result_1) <= len(result_3)

    def test_reingest_clears_old_data(self):
        counts_1 = ingest_references()
        counts_2 = ingest_references()
        assert counts_1 == counts_2
