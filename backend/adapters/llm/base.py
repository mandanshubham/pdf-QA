"""
backend/adapters/llm/base.py

Abstract base class for all LLM adapters.

Every provider adapter (Gemini, OpenAI, Anthropic, Ollama) must subclass
BaseLLMAdapter and implement `get_llm()`. The base class provides the
unified `chat()` and `stream()` interface used everywhere else in the app.

Design pattern: Adapter / Strategy
- Consumers call BaseLLMAdapter.chat() — they never know which provider
- LLMAdapterFactory decides which concrete class to instantiate
- Swapping providers = one line change in config.yaml
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage


class BaseLLMAdapter(ABC):
    """
    Unified interface for all LLM providers.

    Subclasses must implement `get_llm()` to return a LangChain
    BaseChatModel. All chat and streaming logic is handled here.
    """

    # ── Abstract contract ─────────────────────────────────────────────────────

    @abstractmethod
    def get_llm(self) -> BaseChatModel:
        """Return the configured LangChain chat model instance."""

    @property
    @abstractmethod
    def provider(self) -> str:
        """Return the provider name (e.g. 'gemini', 'openai')."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the active model identifier string."""

    # ── Concrete methods (use get_llm() internally) ───────────────────────────

    @staticmethod
    def _extract_text(content: Any) -> str:
        """
        Normalise LLM response content to a plain string.

        Newer Gemini models return content as a list of typed blocks:
            [{'type': 'text', 'text': '...', 'extras': {...}}]
        Older models return a plain string.
        This method handles both formats.
        """
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif isinstance(block, str):
                    parts.append(block)
            return "".join(parts)
        return str(content)

    def chat(self, messages: list[BaseMessage]) -> str:
        """
        Send a list of messages to the LLM and return the full text response.

        Args:
            messages: List of LangChain BaseMessage objects
                      (HumanMessage, SystemMessage, AIMessage, etc.)

        Returns:
            The assistant's response as a plain string.
        """
        llm = self.get_llm()
        response = llm.invoke(messages)
        return self._extract_text(response.content)

    def stream(self, messages: list[BaseMessage]) -> Iterator[str]:
        """
        Stream tokens from the LLM one chunk at a time.

        Args:
            messages: List of LangChain BaseMessage objects.

        Yields:
            Text chunks (tokens) as they arrive from the provider.
        """
        llm = self.get_llm()
        for chunk in llm.stream(messages):
            if chunk.content:
                yield self._extract_text(chunk.content)

    def simple_chat(self, user_message: str, system_prompt: str = "") -> str:
        """
        Convenience wrapper: send a plain string message and get a response.

        Args:
            user_message: The user's input text.
            system_prompt: Optional system instruction.

        Returns:
            The assistant's response as a plain string.
        """
        messages: list[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))
        return self.chat(messages)

    def simple_stream(self, user_message: str, system_prompt: str = "") -> Iterator[str]:
        """
        Convenience wrapper: stream a response to a plain string message.
        """
        messages: list[BaseMessage] = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=user_message))
        yield from self.stream(messages)

    def info(self) -> dict[str, Any]:
        """Return provider and model info as a dict (used by /api/health)."""
        return {
            "provider": self.provider,
            "model": self.model_name,
        }
