"""
backend/storage/vector_store.py

ChromaDB wrapper — the only file in the project that imports chromadb directly.

Responsibilities:
  - Initialise and persist the ChromaDB collection
  - Add document chunks (text + embedding + metadata)
  - Similarity search: embed a query → find top-K nearest chunks
  - Delete all chunks belonging to a document
  - List all unique documents (tracked via a sidecar JSON registry)

Design note: we store document-level metadata (filename, chunk_count, etc.)
in a small JSON registry file alongside ChromaDB. This avoids having to scan
all vectors to reconstruct document info, and keeps the document management
layer clean and fast.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import VectorStoreSettings


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class DocumentChunk:
    """A single text chunk ready to be stored in ChromaDB."""
    chunk_id: str           # unique id for this chunk
    doc_id: str             # parent document id (shared by all chunks in a PDF)
    text: str               # the chunk text
    metadata: dict[str, Any]  # page, chunk_index, filename, upload_timestamp


@dataclass
class SearchResult:
    """A single retrieved chunk from a similarity search."""
    chunk_id: str
    doc_id: str
    text: str
    score: float            # similarity score (higher = more relevant)
    metadata: dict[str, Any]


@dataclass
class DocRecord:
    """Document-level record stored in the JSON registry."""
    doc_id: str
    filename: str
    chunk_count: int
    upload_timestamp: str   # ISO 8601
    file_size_bytes: int


# ── VectorStore ───────────────────────────────────────────────────────────────

class VectorStore:
    """
    Thin wrapper around ChromaDB providing a clean interface for
    the ingestion and query services.

    Usage:
        store = VectorStore(settings.vector_store, embedding_adapter)
        store.add_chunks(chunks)
        results = store.search("what is the capital of France?", top_k=5)
    """

    _REGISTRY_FILENAME = "document_registry.json"

    def __init__(
        self,
        settings: VectorStoreSettings,
        embedding_adapter: BaseEmbeddingAdapter,
    ) -> None:
        self._settings = settings
        self._embedding_adapter = embedding_adapter

        # Ensure the persist directory exists
        persist_path = Path(settings.persist_directory).resolve()
        persist_path.mkdir(parents=True, exist_ok=True)

        # Initialise ChromaDB with persistent storage
        self._client = chromadb.PersistentClient(
            path=str(persist_path),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Get or create the collection (no built-in embedding function —
        # we embed manually via our adapter before inserting)
        self._collection = self._client.get_or_create_collection(
            name=settings.collection_name,
            metadata={"hnsw:space": "cosine"},  # cosine similarity
        )

        # Path to the document registry JSON
        self._registry_path = persist_path / self._REGISTRY_FILENAME

    # ── Registry helpers ──────────────────────────────────────────────────────

    def _load_registry(self) -> dict[str, dict]:
        if self._registry_path.exists():
            return json.loads(self._registry_path.read_text(encoding="utf-8"))
        return {}

    def _save_registry(self, registry: dict[str, dict]) -> None:
        self._registry_path.write_text(
            json.dumps(registry, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def add_chunks(self, chunks: list[DocumentChunk], doc_record: DocRecord) -> None:
        """
        Embed and store a list of chunks in ChromaDB, then register the document.

        Args:
            chunks: List of DocumentChunk objects from the ingestion service.
            doc_record: Document-level metadata to store in the registry.
        """
        if not chunks:
            return

        texts = [c.text for c in chunks]

        # Embed all chunks in one batch call (efficient)
        embeddings = self._embedding_adapter.embed_documents(texts)

        self._collection.add(
            ids=[c.chunk_id for c in chunks],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c.metadata for c in chunks],
        )

        # Register the document
        registry = self._load_registry()
        registry[doc_record.doc_id] = {
            "doc_id": doc_record.doc_id,
            "filename": doc_record.filename,
            "chunk_count": doc_record.chunk_count,
            "upload_timestamp": doc_record.upload_timestamp,
            "file_size_bytes": doc_record.file_size_bytes,
        }
        self._save_registry(registry)

    def search(
        self,
        query: str,
        top_k: int = 5,
        score_threshold: float = 0.0,
        doc_ids: list[str] | None = None,
    ) -> list[SearchResult]:
        """
        Embed a query and return the top-K most similar chunks.

        Args:
            query: The user's question as a plain string.
            top_k: Maximum number of results to return.
            score_threshold: Minimum similarity score (0.0 = no filter).
            doc_ids: Optional list of doc_ids to restrict search to.

        Returns:
            List of SearchResult ordered by relevance (highest score first).
        """
        query_embedding = self._embedding_adapter.embed_query(query)

        where_filter = None
        if doc_ids:
            where_filter = {"doc_id": {"$in": doc_ids}}

        results = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self._collection.count() or 1),
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )

        search_results: list[SearchResult] = []
        if not results["ids"] or not results["ids"][0]:
            return search_results

        for chunk_id, text, metadata, distance in zip(
            results["ids"][0],
            results["documents"][0],  # type: ignore[index]
            results["metadatas"][0],  # type: ignore[index]
            results["distances"][0],  # type: ignore[index]
        ):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity score: 1 - (distance / 2)
            score = 1.0 - (distance / 2.0)
            if score >= score_threshold:
                search_results.append(
                    SearchResult(
                        chunk_id=chunk_id,
                        doc_id=metadata.get("doc_id", ""),
                        text=text,
                        score=round(score, 4),
                        metadata=metadata,
                    )
                )

        return search_results

    def delete_document(self, doc_id: str) -> int:
        """
        Delete all chunks belonging to a document from ChromaDB and the registry.

        Args:
            doc_id: The document ID to delete.

        Returns:
            Number of chunks deleted.
        """
        # Find all chunk IDs belonging to this doc
        results = self._collection.get(
            where={"doc_id": {"$eq": doc_id}},
            include=[],
        )
        chunk_ids = results["ids"]

        if chunk_ids:
            self._collection.delete(ids=chunk_ids)

        # Remove from registry
        registry = self._load_registry()
        registry.pop(doc_id, None)
        self._save_registry(registry)

        return len(chunk_ids)

    def list_documents(self) -> list[DocRecord]:
        """Return all registered documents from the registry."""
        registry = self._load_registry()
        return [DocRecord(**rec) for rec in registry.values()]

    def get_document(self, doc_id: str) -> DocRecord | None:
        """Return a single document's record, or None if not found."""
        registry = self._load_registry()
        rec = registry.get(doc_id)
        return DocRecord(**rec) if rec else None

    def chunk_count(self) -> int:
        """Total number of chunks stored across all documents."""
        return self._collection.count()
