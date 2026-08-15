"""
backend/adapters/embeddings/vertexai.py

Google Vertex AI embedding adapter.
Model: text-embedding-004 (768-dim)

Required env vars:
    GOOGLE_API_KEY        — your Vertex AI API key
    GOOGLE_CLOUD_PROJECT  — your GCP project number or ID
"""

from __future__ import annotations

import os

from langchain_core.embeddings import Embeddings

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import EmbeddingSettings


class VertexAIEmbeddingAdapter(BaseEmbeddingAdapter):
    """Embedding adapter for Google Vertex AI text-embedding-004."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self._settings = settings
        self._embedder: Embeddings | None = None

    @property
    def provider(self) -> str:
        return "vertexai"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_embedder(self) -> Embeddings:
        if self._embedder is None:
            from langchain_google_vertexai import VertexAIEmbeddings
            project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
            self._embedder = VertexAIEmbeddings(
                model_name=self._settings.model,
                project=project,
            )
        return self._embedder
