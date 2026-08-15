"""
backend/adapters/embeddings/base.py

Abstract base class for all embedding adapters.

Embeddings convert text → float vectors. These vectors are stored in
ChromaDB and used to find the most semantically similar chunks to a query.

Every embedding adapter must implement `get_embedder()` which returns a
LangChain Embeddings object. The base class wraps it with a friendly interface.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from langchain_core.embeddings import Embeddings


class BaseEmbeddingAdapter(ABC):
    """Unified interface for all embedding providers."""

    @abstractmethod
    def get_embedder(self) -> Embeddings:
        """Return the underlying LangChain Embeddings instance."""

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g. 'gemini', 'openai')."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the active embedding model identifier."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of document texts into float vectors.
        Used during PDF ingestion to embed chunks before storing in ChromaDB.
        """
        return self.get_embedder().embed_documents(texts)

    def embed_query(self, text: str) -> list[float]:
        """
        Embed a single query string into a float vector.
        Used during RAG retrieval to embed the user's question.
        """
        return self.get_embedder().embed_query(text)

    def info(self) -> dict[str, Any]:
        """Return provider and model info (used by /api/health)."""
        return {
            "provider": self.provider,
            "model": self.model_name,
        }
