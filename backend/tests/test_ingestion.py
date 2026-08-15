"""
backend/tests/test_ingestion.py

Phase 3 smoke tests — verify ingestion pipeline and vector store.

No real API calls: embedding calls are mocked with fixed-size random vectors
so tests run offline and fast.
"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from backend.config.settings import ChunkingSettings, VectorStoreSettings
from backend.storage.vector_store import DocRecord, DocumentChunk, VectorStore


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_embedder():
    """A mock embedding adapter that returns fixed-size random vectors."""
    embedder = MagicMock()
    embedder.embed_documents.side_effect = lambda texts: [
        [0.1] * 768 for _ in texts
    ]
    embedder.embed_query.return_value = [0.1] * 768
    return embedder


@pytest.fixture
def temp_store(mock_embedder, tmp_path):
    """A VectorStore backed by a temporary directory."""
    settings = VectorStoreSettings(
        persist_directory=str(tmp_path / "chroma"),
        collection_name="test_collection",
    )
    return VectorStore(settings, mock_embedder)


@pytest.fixture
def sample_chunks():
    """A small list of DocumentChunk objects for testing."""
    doc_id = str(uuid.uuid4())
    return [
        DocumentChunk(
            chunk_id=str(uuid.uuid4()),
            doc_id=doc_id,
            text=f"This is chunk number {i} about artificial intelligence.",
            metadata={
                "doc_id": doc_id,
                "filename": "test.pdf",
                "page": 1,
                "chunk_index": i,
                "local_chunk_index": i,
                "upload_timestamp": "2024-01-01T00:00:00+00:00",
            },
        )
        for i in range(5)
    ]


@pytest.fixture
def sample_doc_record(sample_chunks):
    return DocRecord(
        doc_id=sample_chunks[0].doc_id,
        filename="test.pdf",
        chunk_count=len(sample_chunks),
        upload_timestamp="2024-01-01T00:00:00+00:00",
        file_size_bytes=12345,
    )


# ── VectorStore tests ─────────────────────────────────────────────────────────

def test_vector_store_initialises(temp_store):
    """VectorStore can be created and reports zero chunks initially."""
    assert temp_store.chunk_count() == 0


def test_add_chunks_and_count(temp_store, sample_chunks, sample_doc_record):
    """After adding chunks, chunk_count reflects the correct number."""
    temp_store.add_chunks(sample_chunks, sample_doc_record)
    assert temp_store.chunk_count() == len(sample_chunks)


def test_list_documents_after_add(temp_store, sample_chunks, sample_doc_record):
    """list_documents() returns the registered document after ingestion."""
    temp_store.add_chunks(sample_chunks, sample_doc_record)
    docs = temp_store.list_documents()
    assert len(docs) == 1
    assert docs[0].doc_id == sample_doc_record.doc_id
    assert docs[0].filename == "test.pdf"


def test_get_document(temp_store, sample_chunks, sample_doc_record):
    """get_document() returns the correct record by doc_id."""
    temp_store.add_chunks(sample_chunks, sample_doc_record)
    record = temp_store.get_document(sample_doc_record.doc_id)
    assert record is not None
    assert record.chunk_count == 5


def test_get_document_not_found(temp_store):
    """get_document() returns None for an unknown doc_id."""
    assert temp_store.get_document("nonexistent-id") is None


def test_search_returns_results(temp_store, sample_chunks, sample_doc_record):
    """search() returns results after chunks have been added."""
    temp_store.add_chunks(sample_chunks, sample_doc_record)
    results = temp_store.search("artificial intelligence", top_k=3)
    assert len(results) > 0
    assert all(hasattr(r, "score") for r in results)
    assert all(hasattr(r, "text") for r in results)


def test_delete_document(temp_store, sample_chunks, sample_doc_record):
    """delete_document() removes chunks and the registry entry."""
    temp_store.add_chunks(sample_chunks, sample_doc_record)
    assert temp_store.chunk_count() == 5

    chunks_deleted = temp_store.delete_document(sample_doc_record.doc_id)
    assert chunks_deleted == 5
    assert temp_store.chunk_count() == 0
    assert temp_store.get_document(sample_doc_record.doc_id) is None


# ── Ingestion service tests ────────────────────────────────────────────────────

def test_ingestion_service_with_real_pdf(temp_store):
    """PDFIngestionService can ingest a programmatically generated PDF."""
    import fitz
    from backend.services.ingestion import PDFIngestionService

    chunking = ChunkingSettings(chunk_size=200, chunk_overlap=20)
    service = PDFIngestionService(temp_store, chunking)

    # Create a minimal test PDF in memory
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text(
            (72, 100),
            "This is a test document about machine learning and AI. " * 10,
        )
        doc.save(str(tmp_path))
        doc.close()

        record = service.ingest(tmp_path, "test.pdf")
        assert record.chunk_count > 0
        assert record.filename == "test.pdf"
        assert len(record.doc_id) == 36  # UUID format
        assert temp_store.chunk_count() == record.chunk_count
    finally:
        tmp_path.unlink(missing_ok=True)


def test_ingestion_rejects_empty_pdf(temp_store):
    """Ingesting a PDF with no text raises ValueError."""
    import fitz
    from backend.services.ingestion import PDFIngestionService

    chunking = ChunkingSettings(chunk_size=200, chunk_overlap=20)
    service = PDFIngestionService(temp_store, chunking)

    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        # Create a blank PDF (no text)
        doc = fitz.open()
        doc.new_page()
        doc.save(str(tmp_path))
        doc.close()

        with pytest.raises(ValueError, match="No extractable text"):
            service.ingest(tmp_path, "blank.pdf")
    finally:
        tmp_path.unlink(missing_ok=True)
