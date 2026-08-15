"""
backend/config/settings.py

Pydantic-based settings model for PDF-QA.

Load order (later overrides earlier):
  1. config.yaml  — human-readable defaults
  2. .env file    — secrets and local overrides
  3. Environment variables — CI / deployment overrides

Environment variable format:  PDF_QA__<SECTION>__<KEY>
Example:                      PDF_QA__LLM__PROVIDER=openai
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ── Locate project root (two levels up from this file) ───────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_YAML = _PROJECT_ROOT / "config.yaml"


# ── Sub-models ────────────────────────────────────────────────────────────────

class LLMModels(BaseModel):
    gemini: str = "gemini-flash-latest"      # updated: works with this API key
    openai: str = "gpt-4o-mini"
    anthropic: str = "claude-3-haiku-20240307"
    ollama: str = "llama3.2"
    vertexai: str = "gemini-3.7-flash"


class LLMSettings(BaseModel):
    provider: Literal["gemini", "openai", "anthropic", "ollama", "vertexai"] = "gemini"
    models: LLMModels = Field(default_factory=LLMModels)
    model: str = ""
    temperature: float = 0.2
    max_tokens: int = 2048

    @model_validator(mode="after")
    def resolve_model(self) -> "LLMSettings":
        """Fill `model` from the provider-specific default if left empty."""
        if not self.model:
            self.model = getattr(self.models, self.provider)
        return self


class EmbeddingModels(BaseModel):
    gemini: str = "models/text-embedding-004"
    openai: str = "text-embedding-3-small"
    huggingface: str = "sentence-transformers/all-MiniLM-L6-v2"
    ollama: str = "nomic-embed-text"
    vertexai: str = "text-embedding-004"  # Vertex AI model name (no models/ prefix)


class EmbeddingSettings(BaseModel):
    provider: Literal["gemini", "openai", "huggingface", "ollama", "vertexai"] = "gemini"
    models: EmbeddingModels = Field(default_factory=EmbeddingModels)
    model: str = ""

    @model_validator(mode="after")
    def resolve_model(self) -> "EmbeddingSettings":
        if not self.model:
            self.model = getattr(self.models, self.provider, self.models.gemini)
        return self


class RetrievalSettings(BaseModel):
    top_k: int = 5
    score_threshold: float = 0.3


class ChunkingSettings(BaseModel):
    chunk_size: int = 1000
    chunk_overlap: int = 200


class VectorStoreSettings(BaseModel):
    persist_directory: str = ".chroma_db"
    collection_name: str = "pdf_qa_docs"


class APISettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_allow_all: bool = True


# ── Root settings ─────────────────────────────────────────────────────────────

class Settings(BaseSettings):
    """
    Master settings object for the PDF-QA application.

    Usage:
        from backend.config.settings import get_settings
        cfg = get_settings()
        print(cfg.llm.provider)
    """

    model_config = SettingsConfigDict(
        env_prefix="PDF_QA__",
        env_nested_delimiter="__",
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    llm: LLMSettings = Field(default_factory=LLMSettings)
    embeddings: EmbeddingSettings = Field(default_factory=EmbeddingSettings)
    retrieval: RetrievalSettings = Field(default_factory=RetrievalSettings)
    chunking: ChunkingSettings = Field(default_factory=ChunkingSettings)
    vector_store: VectorStoreSettings = Field(default_factory=VectorStoreSettings)
    api: APISettings = Field(default_factory=APISettings)

    @classmethod
    def from_yaml_and_env(cls) -> "Settings":
        """
        Load settings by merging config.yaml → .env → environment variables.
        config.yaml values become Pydantic defaults; env vars override them.
        """
        # Load .env into os.environ FIRST so that raw keys like GOOGLE_API_KEY
        # are available to os.getenv() calls everywhere (e.g. in factories).
        from dotenv import load_dotenv
        load_dotenv(_PROJECT_ROOT / ".env", override=False)

        yaml_data: dict = {}
        if _CONFIG_YAML.exists():
            with open(_CONFIG_YAML, encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f) or {}

        # Inject YAML values as environment variable defaults so that
        # Pydantic-settings' env-var layer can still override them.
        for section, values in yaml_data.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    env_key = f"PDF_QA__{section}__{key}".upper()
                    if env_key not in os.environ and value is not None:
                        # Nested dicts (e.g. models) need JSON serialisation
                        if isinstance(value, dict):
                            import json
                            os.environ[env_key] = json.dumps(value)
                        else:
                            os.environ[env_key] = str(value)

        return cls()


# ── Singleton accessor ────────────────────────────────────────────────────────

_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the cached Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings.from_yaml_and_env()
    return _settings
