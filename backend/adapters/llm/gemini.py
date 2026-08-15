"""
backend/adapters/llm/gemini.py

Google Gemini adapter using langchain-google-genai.

Required env var: GOOGLE_API_KEY
Free tier: gemini-1.5-flash has a generous free quota at aistudio.google.com
"""

from __future__ import annotations

from langchain_core.language_models import BaseChatModel
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import LLMSettings


class GeminiAdapter(BaseLLMAdapter):
    """LLM adapter for Google Gemini via langchain-google-genai."""

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        self._llm: BaseChatModel | None = None  # lazy-initialised

    # ── Abstract implementations ──────────────────────────────────────────────

    @property
    def provider(self) -> str:
        return "gemini"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_llm(self) -> BaseChatModel:
        """Lazy-init so the API key error is raised at first use, not import."""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(
                model=self._settings.model,
                temperature=self._settings.temperature,
                max_output_tokens=self._settings.max_tokens,
            )
        return self._llm
