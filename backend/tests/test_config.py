"""
backend/tests/test_config.py

Phase 1 smoke test — verifies the config system loads correctly.
Run: pytest backend/tests/test_config.py -v
"""

import pytest
from backend.config.settings import Settings, get_settings


def test_settings_loads():
    """Settings object can be instantiated without errors."""
    cfg = Settings.from_yaml_and_env()
    assert cfg is not None


def test_llm_provider_is_valid():
    """LLM provider is one of the allowed values."""
    cfg = get_settings()
    assert cfg.llm.provider in ("gemini", "openai", "anthropic", "ollama")


def test_llm_model_auto_resolved():
    """If config.yaml model is empty, the provider default is filled in."""
    cfg = get_settings()
    assert cfg.llm.model, "llm.model must be non-empty after resolution"


def test_embedding_model_auto_resolved():
    """Embedding model is resolved from provider default if not set."""
    cfg = get_settings()
    assert cfg.embeddings.model, "embeddings.model must be non-empty after resolution"


def test_chunking_values_are_positive():
    """Chunk size and overlap must be positive integers."""
    cfg = get_settings()
    assert cfg.chunking.chunk_size > 0
    assert cfg.chunking.chunk_overlap >= 0
    assert cfg.chunking.chunk_overlap < cfg.chunking.chunk_size


def test_retrieval_values_in_range():
    """top_k must be positive, score_threshold must be 0–1."""
    cfg = get_settings()
    assert cfg.retrieval.top_k > 0
    assert 0.0 <= cfg.retrieval.score_threshold <= 1.0
