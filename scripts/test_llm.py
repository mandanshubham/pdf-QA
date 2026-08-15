"""
scripts/test_llm.py

Phase 2 CLI smoke test — verify the active LLM adapter works end-to-end.

Usage:
    python scripts/test_llm.py

    # Test a specific provider without editing config.yaml:
    PDF_QA__LLM__PROVIDER=openai python scripts/test_llm.py

What it does:
  1. Loads config
  2. Creates the LLM adapter via factory
  3. Sends a simple test prompt
  4. Prints the response
  5. Reports pass / fail
"""

import sys
import os
import time

# Ensure the project root is on the path when running as a script
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from backend.adapters.llm.factory import LLMAdapterFactory


def main() -> None:
    print("\n" + "=" * 60)
    print("  PDF-QA - LLM Adapter Smoke Test")
    print("=" * 60)

    # ── Load config ───────────────────────────────────────────────────────────
    cfg = get_settings()
    print(f"\nProvider : {cfg.llm.provider}")
    print(f"Model    : {cfg.llm.model}")

    # ── Create adapter ────────────────────────────────────────────────────────
    print("\nCreating adapter...", end=" ")
    try:
        adapter = LLMAdapterFactory.create(cfg)
        print("OK")
    except EnvironmentError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    # ── Send test prompt ──────────────────────────────────────────────────────
    prompt = "Say exactly: 'PDF-QA LLM adapter is working.' and nothing else."
    print(f"\nPrompt   : {prompt!r}")
    print("Response : ", end="", flush=True)

    try:
        start = time.perf_counter()
        response = adapter.simple_chat(prompt)
        elapsed = time.perf_counter() - start
        print(response)
        print(f"\nLatency  : {elapsed:.2f}s")
    except Exception as e:
        print(f"\nERROR calling LLM: {e}")
        sys.exit(1)

    # ── Stream test ───────────────────────────────────────────────────────────
    print("\nStream test (first 5 tokens): ", end="", flush=True)
    try:
        count = 0
        for token in adapter.simple_stream("Count from 1 to 5, just the numbers."):
            print(token, end="", flush=True)
            count += 1
            if count >= 20:   # safety limit
                break
        print()
    except Exception as e:
        print(f"\nStream ERROR: {e}")
        sys.exit(1)

    print("\n>> LLM adapter working correctly.\n")


if __name__ == "__main__":
    main()
