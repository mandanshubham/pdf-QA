"""
backend/adapters/llm/anthropic.py

Anthropic (Claude) adapter using langchain-anthropic.

Required env var: ANTHROPIC_API_KEY
Note: Anthropic does not provide an embeddings API.
      Keep embeddings.provider as "gemini" or "openai" when using Anthropic LLM.
"""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import LLMSettings


class AnthropicAdapter(BaseLLMAdapter):
    """LLM adapter for Anthropic (Claude) via langchain-anthropic."""

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        self._llm: BaseChatModel | None = None

    @property
    def provider(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = ChatAnthropic(
                model=self._settings.model,
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
            )
        return self._llm
