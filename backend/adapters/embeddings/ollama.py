"""
backend/adapters/embeddings/ollama.py

Ollama local embedding adapter — no API key required.
Model: nomic-embed-text (768-dim)
Requires: ollama serve && ollama pull nomic-embed-text
"""

from __future__ import annotations

from langchain_core.embeddings import Embeddings
from langchain_ollama import OllamaEmbeddings

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import EmbeddingSettings


class OllamaEmbeddingAdapter(BaseEmbeddingAdapter):
    """Embedding adapter for Ollama local inference."""

    def __init__(self, settings: EmbeddingSettings, base_url: str = "http://localhost:11434") -> None:
        self._settings = settings
        self._base_url = base_url
        self._embedder: Embeddings | None = None

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_embedder(self) -> Embeddings:
        if self._embedder is None:
            self._embedder = OllamaEmbeddings(
                model=self._settings.model,
                base_url=self._base_url,
            )
        return self._embedder
