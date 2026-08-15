"""
backend/tests/test_query.py

Phase 4 smoke tests — verify RAG query service behaviour.

All LLM and embedding calls are mocked — no network or API keys needed.
Tests cover:
  - Basic query returns ChatResponse with answer and sources
  - No documents returns a helpful "no documents" message
  - Source deduplication (same filename+page only cited once)
  - Streaming query yields token, sources, done events in correct order
  - Context formatting includes filename, page and score
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from backend.config.settings import RetrievalSettings
from backend.models.chat import ChatResponse, StreamChunk
from backend.storage.vector_store import SearchResult


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def retrieval_settings():
    return RetrievalSettings(top_k=3, score_threshold=0.0)


@pytest.fixture
def mock_store():
    """A mock VectorStore that returns pre-canned SearchResults."""
    store = MagicMock()
    store.search.return_value = [
        SearchResult(
            chunk_id=str(uuid.uuid4()),
            doc_id="doc-1",
            text="Retrieval-Augmented Generation (RAG) combines vector search with LLM generation.",
            score=0.91,
            metadata={"filename": "ml_paper.pdf", "page": 3, "doc_id": "doc-1"},
        ),
        SearchResult(
            chunk_id=str(uuid.uuid4()),
            doc_id="doc-1",
            text="ChromaDB stores embeddings and enables fast similarity search.",
            score=0.85,
            metadata={"filename": "ml_paper.pdf", "page": 5, "doc_id": "doc-1"},
        ),
    ]
    return store


@pytest.fixture
def mock_llm():
    """A mock LLMAdapter that returns a canned answer."""
    llm = MagicMock()
    llm.chat.return_value = "RAG stands for Retrieval-Augmented Generation."
    llm.stream.return_value = iter(["RAG ", "stands ", "for ", "RAG."])
    return llm


@pytest.fixture
def query_service(mock_store, mock_llm, retrieval_settings):
    from backend.services.query import RAGQueryService
    return RAGQueryService(mock_store, mock_llm, retrieval_settings)


# ── Query tests ───────────────────────────────────────────────────────────────

def test_query_returns_chat_response(query_service):
    """query() returns a ChatResponse with answer and sources."""
    response = query_service.query("What is RAG?")
    assert isinstance(response, ChatResponse)
    assert response.answer == "RAG stands for Retrieval-Augmented Generation."
    assert response.question == "What is RAG?"
    assert response.chunks_searched == 2


def test_query_returns_sources(query_service):
    """query() includes source citations with filename and page."""
    response = query_service.query("What is RAG?")
    assert len(response.sources) == 2
    assert response.sources[0].filename == "ml_paper.pdf"
    assert response.sources[0].page == 3
    assert 0.0 <= response.sources[0].score <= 1.0


def test_query_source_deduplication(mock_store, mock_llm, retrieval_settings):
    """Sources with the same (filename, page) are deduplicated."""
    from backend.services.query import RAGQueryService

    # Two chunks from the same page
    mock_store.search.return_value = [
        SearchResult(
            chunk_id=str(uuid.uuid4()),
            doc_id="doc-1",
            text="First chunk from page 3.",
            score=0.90,
            metadata={"filename": "paper.pdf", "page": 3, "doc_id": "doc-1"},
        ),
        SearchResult(
            chunk_id=str(uuid.uuid4()),
            doc_id="doc-1",
            text="Second chunk also from page 3.",
            score=0.88,
            metadata={"filename": "paper.pdf", "page": 3, "doc_id": "doc-1"},
        ),
    ]
    service = RAGQueryService(mock_store, mock_llm, retrieval_settings)
    response = service.query("tell me about page 3")
    # Should only have one citation for page 3
    assert len(response.sources) == 1


def test_query_no_documents(mock_store, mock_llm, retrieval_settings):
    """When no chunks are found, query() returns a helpful message."""
    from backend.services.query import RAGQueryService
    mock_store.search.return_value = []
    service = RAGQueryService(mock_store, mock_llm, retrieval_settings)
    response = service.query("anything")
    assert "couldn't find" in response.answer.lower()
    assert response.sources == []
    assert response.chunks_searched == 0
    # LLM should NOT be called when there are no results
    mock_llm.chat.assert_not_called()


def test_query_passes_doc_ids_filter(query_service, mock_store):
    """query() passes doc_ids filter through to the vector store."""
    query_service.query("question", doc_ids=["doc-abc"])
    call_kwargs = mock_store.search.call_args.kwargs
    assert call_kwargs.get("doc_ids") == ["doc-abc"]


# ── Streaming tests ───────────────────────────────────────────────────────────

def test_stream_query_yields_correct_events(query_service):
    """stream_query() emits token → sources → done in order."""
    events = list(query_service.stream_query("What is RAG?"))

    types = [e.type for e in events]
    assert "token" in types
    assert "sources" in types
    assert "done" in types

    # done must be last
    assert types[-1] == "done"
    # sources must come before done
    sources_idx = types.index("sources")
    done_idx = types.index("done")
    assert sources_idx < done_idx


def test_stream_query_no_documents_yields_message(mock_store, mock_llm, retrieval_settings):
    """When no chunks found, stream_query still yields token + sources + done."""
    from backend.services.query import RAGQueryService
    mock_store.search.return_value = []
    service = RAGQueryService(mock_store, mock_llm, retrieval_settings)

    events = list(service.stream_query("anything"))
    types = [e.type for e in events]
    assert "token" in types
    assert "sources" in types
    assert "done" in types

    token_events = [e for e in events if e.type == "token"]
    assert any("couldn't find" in (e.content or "").lower() for e in token_events)


# ── Context formatting tests ──────────────────────────────────────────────────

def test_format_context_includes_metadata():
    """_format_context() includes filename, page, and score in each block."""
    from backend.services.query import RAGQueryService
    results = [
        SearchResult(
            chunk_id="c1",
            doc_id="d1",
            text="Some text about AI.",
            score=0.88,
            metadata={"filename": "paper.pdf", "page": 2, "doc_id": "d1"},
        )
    ]
    context = RAGQueryService._format_context(results)
    assert "paper.pdf" in context
    assert "Page 2" in context
    assert "0.88" in context
    assert "Some text about AI." in context
