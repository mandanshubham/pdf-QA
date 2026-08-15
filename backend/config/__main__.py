"""
backend/config/__main__.py

Phase 1 verification script.
Run:  python -m backend.config
# -*- coding: utf-8 -*-

Prints the fully resolved, validated configuration so you can confirm
that config.yaml + .env values are loading correctly.
"""

import json
from backend.config.settings import get_settings


def _redact(value: str) -> str:
    """Show only the first 4 chars of secrets."""
    if not value or len(value) < 8:
        return "*** (not set)"
    return value[:4] + "****"


def main() -> None:
    import sys
    # Ensure UTF-8 output on Windows terminals
    if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    cfg = get_settings()

    print("\n" + "=" * 60)
    print("  PDF-QA · Resolved Configuration")
    print("=" * 60)

    print("\n[LLM]")
    print(f"   Provider  : {cfg.llm.provider}")
    print(f"   Model     : {cfg.llm.model}")
    print(f"   Temp      : {cfg.llm.temperature}")
    print(f"   Max tokens: {cfg.llm.max_tokens}")

    print("\n[Embeddings]")
    print(f"   Provider  : {cfg.embeddings.provider}")
    print(f"   Model     : {cfg.embeddings.model}")

    print("\n[Retrieval]")
    print(f"   Top-K     : {cfg.retrieval.top_k}")
    print(f"   Threshold : {cfg.retrieval.score_threshold}")

    print("\n[Chunking]")
    print(f"   Size      : {cfg.chunking.chunk_size} chars")
    print(f"   Overlap   : {cfg.chunking.chunk_overlap} chars")

    print("\n[Vector Store]")
    print(f"   Directory : {cfg.vector_store.persist_directory}")
    print(f"   Collection: {cfg.vector_store.collection_name}")

    print("\n[API Server]")
    print(f"   Host      : {cfg.api.host}")
    print(f"   Port      : {cfg.api.port}")
    print(f"   CORS all  : {cfg.api.cors_allow_all}")

    # Check which API keys are present (without printing them)
    import os
    print("\n[API Keys] (redacted)")
    print(f"   GOOGLE_API_KEY    : {_redact(os.getenv('GOOGLE_API_KEY', ''))}")
    print(f"   OPENAI_API_KEY    : {_redact(os.getenv('OPENAI_API_KEY', ''))}")
    print(f"   ANTHROPIC_API_KEY : {_redact(os.getenv('ANTHROPIC_API_KEY', ''))}")

    print("\n>> Config loaded successfully!\n")


if __name__ == "__main__":
    main()
