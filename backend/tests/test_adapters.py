"""
backend/tests/test_adapters.py

Phase 2 smoke tests — verify adapter structure and factory wiring.

These tests do NOT make real API calls (no network, no API keys needed).
They test:
  - Factory raises a clear error for missing API keys
  - Factory raises ValueError for unknown providers
  - Each adapter has the correct provider name and model
  - Each adapter exposes the required interface (chat, stream, simple_chat, info)
"""

import os
import pytest
from unittest.mock import patch

from backend.config.settings import Settings, LLMSettings, EmbeddingSettings


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_settings(llm_provider: str, emb_provider: str = "gemini") -> Settings:
    """Build a minimal Settings object for a given provider."""
    cfg = Settings.from_yaml_and_env()
    cfg.llm.provider = llm_provider  # type: ignore[assignment]
    cfg.llm.model = cfg.llm.models.__dict__.get(llm_provider, "test-model")
    cfg.embeddings.provider = emb_provider  # type: ignore[assignment]
    cfg.embeddings.model = cfg.embeddings.models.__dict__.get(emb_provider, "test-embed")
    return cfg


# ── LLM Factory tests ─────────────────────────────────────────────────────────

def test_factory_raises_for_unknown_provider():
    """LLMAdapterFactory should raise ValueError for unrecognised providers."""
    from backend.adapters.llm.factory import LLMAdapterFactory
    cfg = make_settings("gemini")
    cfg.llm.provider = "unknown_provider"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Unknown LLM provider"):
        LLMAdapterFactory.create(cfg)


def test_factory_raises_for_missing_gemini_key():
    """Factory raises EnvironmentError when GOOGLE_API_KEY is absent."""
    from backend.adapters.llm.factory import LLMAdapterFactory
    cfg = make_settings("gemini")
    with patch.dict(os.environ, {}, clear=True):
        # Remove the key if present
        os.environ.pop("GOOGLE_API_KEY", None)
        with pytest.raises(EnvironmentError, match="GOOGLE_API_KEY"):
            LLMAdapterFactory.create(cfg)


def test_gemini_adapter_properties():
    """GeminiAdapter returns correct provider name and model."""
    from backend.adapters.llm.gemini import GeminiAdapter
    settings = LLMSettings(provider="gemini", model="gemini-1.5-flash")
    adapter = GeminiAdapter(settings)
    assert adapter.provider == "gemini"
    assert adapter.model_name == "gemini-1.5-flash"


def test_openai_adapter_properties():
    """OpenAIAdapter returns correct provider name and model."""
    from backend.adapters.llm.openai import OpenAIAdapter
    settings = LLMSettings(provider="openai", model="gpt-4o-mini")
    adapter = OpenAIAdapter(settings)
    assert adapter.provider == "openai"
    assert adapter.model_name == "gpt-4o-mini"


def test_anthropic_adapter_properties():
    """AnthropicAdapter returns correct provider name and model."""
    from backend.adapters.llm.anthropic import AnthropicAdapter
    settings = LLMSettings(provider="anthropic", model="claude-3-haiku-20240307")
    adapter = AnthropicAdapter(settings)
    assert adapter.provider == "anthropic"
    assert adapter.model_name == "claude-3-haiku-20240307"


def test_ollama_adapter_properties():
    """OllamaAdapter returns correct provider name and model."""
    from backend.adapters.llm.ollama import OllamaAdapter
    settings = LLMSettings(provider="ollama", model="llama3.2")
    adapter = OllamaAdapter(settings)
    assert adapter.provider == "ollama"
    assert adapter.model_name == "llama3.2"


def test_adapter_has_required_interface():
    """All adapters must expose chat, stream, simple_chat, simple_stream, info."""
    from backend.adapters.llm.gemini import GeminiAdapter
    settings = LLMSettings(provider="gemini", model="gemini-1.5-flash")
    adapter = GeminiAdapter(settings)
    assert callable(getattr(adapter, "chat", None))
    assert callable(getattr(adapter, "stream", None))
    assert callable(getattr(adapter, "simple_chat", None))
    assert callable(getattr(adapter, "simple_stream", None))
    assert callable(getattr(adapter, "info", None))


def test_adapter_info_dict():
    """adapter.info() returns a dict with 'provider' and 'model' keys."""
    from backend.adapters.llm.gemini import GeminiAdapter
    settings = LLMSettings(provider="gemini", model="gemini-1.5-flash")
    adapter = GeminiAdapter(settings)
    info = adapter.info()
    assert info["provider"] == "gemini"
    assert info["model"] == "gemini-1.5-flash"


# ── Embedding Factory tests ───────────────────────────────────────────────────

def test_embedding_factory_raises_for_unknown_provider():
    """EmbeddingAdapterFactory raises ValueError for unknown provider."""
    from backend.adapters.embeddings.factory import EmbeddingAdapterFactory
    cfg = make_settings("gemini", emb_provider="gemini")
    cfg.embeddings.provider = "unknown"  # type: ignore[assignment]
    with pytest.raises(ValueError, match="Unknown embedding provider"):
        EmbeddingAdapterFactory.create(cfg)


def test_gemini_embedding_adapter_properties():
    """GeminiEmbeddingAdapter returns correct provider and model."""
    from backend.adapters.embeddings.gemini import GeminiEmbeddingAdapter
    settings = EmbeddingSettings(provider="gemini", model="models/text-embedding-004")
    adapter = GeminiEmbeddingAdapter(settings)
    assert adapter.provider == "gemini"
    assert adapter.model_name == "models/text-embedding-004"


def test_embedding_adapter_has_required_interface():
    """Embedding adapters must expose embed_documents, embed_query, info."""
    from backend.adapters.embeddings.gemini import GeminiEmbeddingAdapter
    settings = EmbeddingSettings(provider="gemini", model="models/text-embedding-004")
    adapter = GeminiEmbeddingAdapter(settings)
    assert callable(getattr(adapter, "embed_documents", None))
    assert callable(getattr(adapter, "embed_query", None))
    assert callable(getattr(adapter, "info", None))
