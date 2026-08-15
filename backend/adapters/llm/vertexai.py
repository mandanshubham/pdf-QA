"""
backend/adapters/llm/vertexai.py

Google Vertex AI adapter using langchain-google-vertexai.

This is the adapter to use when you have a Google Cloud / Vertex AI API key
(format: AQ.xxx...) rather than a Google AI Studio key (format: AIza...).

Required env vars:
    GOOGLE_API_KEY        — your Vertex AI API key  (AQ.xxx...)
    GOOGLE_CLOUD_PROJECT  — your GCP project number or ID

Or configure via config.yaml:
    llm:
      provider: "vertexai"
"""

from __future__ import annotations

import os

from langchain_core.language_models import BaseChatModel

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import LLMSettings


class VertexAIAdapter(BaseLLMAdapter):
    """LLM adapter for Google Vertex AI via langchain-google-vertexai."""

    def __init__(self, settings: LLMSettings) -> None:
        self._settings = settings
        self._llm: BaseChatModel | None = None

    @property
    def provider(self) -> str:
        return "vertexai"

    @property
    def model_name(self) -> str:
        return self._settings.model

    def get_llm(self) -> BaseChatModel:
        if self._llm is None:
            from langchain_google_vertexai import ChatVertexAI
            project = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT_ID")
            api_key = os.getenv("GOOGLE_API_KEY")

            self._llm = ChatVertexAI(
                model=self._settings.model,
                temperature=self._settings.temperature,
                max_output_tokens=self._settings.max_tokens,
                project=project,
                api_key=api_key,
                location="us-central1",
            )
        return self._llm
