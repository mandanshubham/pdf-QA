"""
scripts/ask.py

Phase 4 CLI smoke test — ask a question against indexed PDFs.

Usage:
    # Interactive mode (asks for a question):
    python scripts/ask.py

    # Direct question:
    python scripts/ask.py "What is the main topic of the document?"

    # Stream tokens as they arrive:
    python scripts/ask.py --stream "Summarise the key points"

What it does:
  1. Loads config + builds LLM, embedding adapter, vector store
  2. Runs the RAG query pipeline
  3. Prints the grounded answer with source citations
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.config import get_settings
from backend.adapters.embeddings.factory import EmbeddingAdapterFactory
from backend.adapters.llm.factory import LLMAdapterFactory
from backend.services.query import RAGQueryService
from backend.storage.vector_store import VectorStore


def main() -> None:
    # ── Parse args ────────────────────────────────────────────────────────────
    args = sys.argv[1:]
    stream_mode = "--stream" in args
    if stream_mode:
        args = [a for a in args if a != "--stream"]

    if args:
        question = " ".join(args)
    else:
        print("\nPDF-QA — Ask a question about your documents")
        print("=" * 50)
        question = input("Question: ").strip()
        if not question:
            print("No question provided. Exiting.")
            sys.exit(0)

    # ── Build services ────────────────────────────────────────────────────────
    cfg = get_settings()
    embedder = EmbeddingAdapterFactory.create(cfg)
    llm = LLMAdapterFactory.create(cfg)
    store = VectorStore(cfg.vector_store, embedder)
    service = RAGQueryService(store, llm, cfg.retrieval)

    # Check docs are available
    docs = store.list_documents()
    if not docs:
        print("\nNo documents indexed yet.")
        print("Run: python scripts/ingest_pdf.py <your.pdf>")
        sys.exit(1)

    print(f"\nSearching across {len(docs)} document(s): {[d.filename for d in docs]}")
    print(f"Config: top_k={cfg.retrieval.top_k}, threshold={cfg.retrieval.score_threshold}")
    print()

    if stream_mode:
        # ── Streaming mode ────────────────────────────────────────────────────
        print(f"Question: {question}\n")
        print("Answer (streaming): ", end="", flush=True)
        start = time.perf_counter()
        sources = []

        for chunk in service.stream_query(question):
            if chunk.type == "token" and chunk.content:
                print(chunk.content, end="", flush=True)
            elif chunk.type == "sources":
                sources = chunk.sources or []
            elif chunk.type == "done":
                break
            elif chunk.type == "error":
                print(f"\nERROR: {chunk.error}")
                sys.exit(1)

        elapsed = time.perf_counter() - start
        print(f"\n\nLatency: {elapsed:.2f}s")

    else:
        # ── Standard mode ─────────────────────────────────────────────────────
        print(f"Question: {question}\n")
        print("Thinking...", flush=True)
        start = time.perf_counter()
        response = service.query(question)
        elapsed = time.perf_counter() - start

        print(f"\nAnswer ({elapsed:.2f}s):")
        print("-" * 50)
        print(response.answer)
        sources = response.sources

    # ── Sources ───────────────────────────────────────────────────────────────
    if sources:
        print("\nSources:")
        for i, src in enumerate(sources, 1):
            print(f"  [{i}] {src.filename} — Page {src.page} (score: {src.score:.3f})")
            print(f"       {src.snippet[:100]}...")
    else:
        print("\n(No source citations — check that documents are indexed)")


if __name__ == "__main__":
    main()
