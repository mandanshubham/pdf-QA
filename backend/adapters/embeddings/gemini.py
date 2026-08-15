"""
backend/adapters/embeddings/gemini.py

Google Gemini embedding adapter.
Model: models/text-embedding-004 (768-dim, free tier)
Required env var: GOOGLE_API_KEY
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import EmbeddingSettings


class GeminiEmbeddingAdapter(BaseEmbeddingAdapter):
    """Embedding adapter for Google Gemini text-embedding-004."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self._settings = settings
        self._embedder: Embeddings | None = None

    @property
    def provider(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_embedder(self) -> Embeddings:
        if self._embedder is None:
            self._embedder = GoogleGenerativeAIEmbeddings(
                model=self._settings.model,
            )
        return self._embedder
