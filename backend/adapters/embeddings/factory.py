"""
backend/adapters/embeddings/factory.py

EmbeddingAdapterFactory — same pattern as LLMAdapterFactory.

Usage:
    from backend.adapters.embeddings.factory import EmbeddingAdapterFactory
    from backend.config import get_settings

    embedder = EmbeddingAdapterFactory.create(get_settings())
    vectors = embedder.embed_documents(["Hello world", "Another chunk"])
"""

from __future__ import annotations

import os

from backend.adapters.embeddings.base import BaseEmbeddingAdapter
from backend.config.settings import Settings


class EmbeddingAdapterFactory:
    """Creates and returns the appropriate embedding adapter from config."""

    @staticmethod
    def create(settings: Settings) -> BaseEmbeddingAdapter:
        """
        Instantiate and return the configured embedding adapter.

        Args:
            settings: Resolved Settings object.

        Returns:
            A concrete BaseEmbeddingAdapter.

        Raises:
            ValueError: If provider name is not recognised.
            EnvironmentError: If a required API key is missing.
        """
        provider = settings.embeddings.provider

        if provider == "gemini":
            EmbeddingAdapterFactory._require_env("GOOGLE_API_KEY", "Gemini embeddings")
            from backend.adapters.embeddings.gemini import GeminiEmbeddingAdapter
            return GeminiEmbeddingAdapter(settings.embeddings)

        if provider == "openai":
            EmbeddingAdapterFactory._require_env("OPENAI_API_KEY", "OpenAI embeddings")
            from backend.adapters.embeddings.openai import OpenAIEmbeddingAdapter
            return OpenAIEmbeddingAdapter(settings.embeddings)

        if provider == "huggingface":
            from backend.adapters.embeddings.huggingface import HuggingFaceEmbeddingAdapter
            return HuggingFaceEmbeddingAdapter(settings.embeddings)

        if provider == "ollama":
            from backend.adapters.embeddings.ollama import OllamaEmbeddingAdapter
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaEmbeddingAdapter(settings.embeddings, base_url=ollama_url)

        raise ValueError(
            f"Unknown embedding provider: '{provider}'. "
            f"Valid options: gemini, openai, huggingface, ollama"
        )

    @staticmethod
    def _require_env(var: str, provider: str) -> None:
        if not os.getenv(var):
            raise EnvironmentError(
                f"{provider} requires the {var} environment variable. "
                f"Add it to your .env file: {var}=your_key_here"
            )
