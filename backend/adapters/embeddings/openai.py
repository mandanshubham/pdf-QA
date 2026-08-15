"""
backend/adapters/embeddings/openai.py

OpenAI embedding adapter.
Model: text-embedding-3-small (1536-dim)
Required env var: OPENAI_API_KEY
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import EmbeddingSettings


class OpenAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """Embedding adapter for OpenAI text-embedding-3-small / large."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self._settings = settings
        self._embedder: Embeddings | None = None

    @property
    def provider(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_embedder(self) -> Embeddings:
        if self._embedder is None:
            self._embedder = OpenAIEmbeddings(model=self._settings.model)
        return self._embedder
