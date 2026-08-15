"""
backend/adapters/llm/ollama.py

Ollama adapter for local LLM inference — no API key required.

Requirements:
  1. Install Ollama: https://ollama.com/download
  2. Start the server: ollama serve
  3. Pull a model:    ollama pull llama3.2

Set in config.yaml:
  llm:
    provider: "ollama"
    models:
      ollama: "llama3.2"   # or any model you have pulled
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_ollama import ChatOllama

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import LLMSettings


class OllamaAdapter(BaseLLMAdapter):
    """LLM adapter for Ollama local inference via langchain-ollama."""

    def __init__(self, settings: LLMSettings, base_url: str = "http://localhost:11434") -> None:
        self._settings = settings
        self._base_url = base_url
        self._llm: BaseChatModel | None = None

    @property
    def provider(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = ChatOllama(
                model=self._settings.model,
                temperature=self._settings.temperature,
                base_url=self._base_url,
            )
        return self._llm
