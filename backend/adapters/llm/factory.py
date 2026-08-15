"""
backend/adapters/llm/factory.py

LLMAdapterFactory — reads config and returns the correct adapter.

This is the ONLY place in the codebase that imports concrete adapter classes.
All other code receives a BaseLLMAdapter and never knows the actual provider.

Usage:
    from backend.adapters.llm.factory import LLMAdapterFactory
    from backend.config import get_settings

    adapter = LLMAdapterFactory.create(get_settings())
    response = adapter.simple_chat("Hello!")
"""

from __future__ import annotations

import os

from backend.adapters.llm.base import BaseLLMAdapter
from backend.config.settings import Settings


class LLMAdapterFactory:
    """
    Creates and returns the appropriate LLM adapter based on settings.

    Pattern: Factory Method
    - Centralises provider selection logic
    - New providers = add one case here, nothing else changes
    """

    @staticmethod
    def create(settings: Settings) -> BaseLLMAdapter:
        """
        Instantiate and return the configured LLM adapter.

        Args:
            settings: The resolved Settings object from get_settings().

        Returns:
            A concrete BaseLLMAdapter for the configured provider.

        Raises:
            ValueError: If the provider name is not recognised.
            EnvironmentError: If a required API key is missing.
        """
        provider = settings.llm.provider

        if provider == "gemini":
            LLMAdapterFactory._require_env("GOOGLE_API_KEY", "Gemini")
            from backend.adapters.llm.gemini import GeminiAdapter
            return GeminiAdapter(settings.llm)

        if provider == "openai":
            LLMAdapterFactory._require_env("OPENAI_API_KEY", "OpenAI")
            from backend.adapters.llm.openai import OpenAIAdapter
            return OpenAIAdapter(settings.llm)

        if provider == "anthropic":
            LLMAdapterFactory._require_env("ANTHROPIC_API_KEY", "Anthropic")
            from backend.adapters.llm.anthropic import AnthropicAdapter
            return AnthropicAdapter(settings.llm)

        if provider == "ollama":
            from backend.adapters.llm.ollama import OllamaAdapter
            ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
            return OllamaAdapter(settings.llm, base_url=ollama_url)

        if provider == "vertexai":
            LLMAdapterFactory._require_env("GOOGLE_API_KEY", "Vertex AI")
            from backend.adapters.llm.vertexai import VertexAIAdapter
            return VertexAIAdapter(settings.llm)

        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Valid options: gemini, openai, anthropic, ollama"
        )

    @staticmethod
    def _require_env(var: str, provider: str) -> None:
        """Raise a clear error if a required API key is missing."""
        if not os.getenv(var):
            raise EnvironmentError(
                f"{provider} requires the {var} environment variable. "
                f"Add it to your .env file: {var}=your_key_here"
            )
