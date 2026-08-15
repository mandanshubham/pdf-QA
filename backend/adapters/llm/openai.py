"""
backend/adapters/llm/openai.py

OpenAI adapter using langchain-openai.

Required env var: OPENAI_API_KEY
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import LLMSettings


class OpenAIAdapter(BaseLLMAdapter):
    """LLM adapter for OpenAI (GPT) via langchain-openai."""

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        self._llm: BaseChatModel | None = None

    @property
    def provider(self) -> str:
        return "openai"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_llm(self) -> BaseChatModel:
        if self._llm is None:
            self._llm = ChatOpenAI(
                model=self._settings.model,
                temperature=self._settings.temperature,
                max_tokens=self._settings.max_tokens,
            )
        return self._llm
