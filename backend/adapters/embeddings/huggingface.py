"""
backend/adapters/embeddings/huggingface.py

HuggingFace local embedding adapter — no API key, runs on CPU.
Model: sentence-transformers/all-MiniLM-L6-v2 (384-dim)

First run downloads the model (~90MB). Subsequent runs use the local cache.
Good fallback option when you want zero API cost and latency doesn't matter.
"""

from __future__ import annotations

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.embeddings import Embeddings

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import EmbeddingSettings


class HuggingFaceEmbeddingAdapter(BaseEmbeddingAdapter):
    """Embedding adapter using HuggingFace sentence-transformers (local CPU)."""

    def __init__(self, settings: EmbeddingSettings) -> None:
        self._settings = settings
        self._embedder: Embeddings | None = None

    @property
    def provider(self) -> str:
        return "huggingface"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_embedder(self) -> Embeddings:
        if self._embedder is None:
            self._embedder = HuggingFaceEmbeddings(
                model_name=self._settings.model,
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
        return self._embedder
