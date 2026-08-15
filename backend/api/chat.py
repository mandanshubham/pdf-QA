"""
backend/api/chat.py

Chat routes — the user-facing question-answering endpoints.

  POST /api/chat          — standard request/response
  POST /api/chat/stream   — streaming via Server-Sent Events (SSE)

SSE format (one JSON object per line, prefixed with "data: "):
  data: {"type":"token","content":"Paris"}
  data: {"type":"token","content":" is"}
  data: {"type":"sources","sources":[...]}
  data: {"type":"done"}

Why SSE instead of WebSockets?
  - Simpler: one-directional (server → client)
  - Works over plain HTTP (no upgrade needed)
  - Natively supported by browsers via EventSource API
  - Trivial to consume in Next.js with fetch + ReadableStream
"""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from backend.adapters.embeddings.factory import EmbeddingAdapterFactory
from backend.adapters.llm.factory import LLMAdapterFactory
from backend.config import get_settings
from backend.models.chat import ChatRequest, ChatResponse, StreamChunk
from backend.services.query import RAGQueryService
from backend.storage.vector_store import VectorStore

router = APIRouter(prefix="/api/chat", tags=["chat"])


def _get_query_service() -> RAGQueryService:
    """Build the RAGQueryService from current settings."""
    cfg = get_settings()
    embedder = EmbeddingAdapterFactory.create(cfg)
    llm = LLMAdapterFactory.create(cfg)
    store = VectorStore(cfg.vector_store, embedder)
    return RAGQueryService(store, llm, cfg.retrieval)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask a question grounded in your uploaded PDFs",
)
def chat(request: ChatRequest) -> ChatResponse:
    """
    Standard (non-streaming) RAG query.

    Steps:
      1. Embed the question
      2. Retrieve top-K similar chunks from ChromaDB
      3. Build a grounded prompt
      4. Call the LLM
      5. Return answer + source citations
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    service = _get_query_service()
    return service.query(
        question=request.question,
        top_k=request.top_k,
        doc_ids=request.doc_ids,
    )


@router.post(
    "/stream",
    summary="Stream an answer token-by-token via Server-Sent Events",
    response_class=StreamingResponse,
)
def chat_stream(request: ChatRequest) -> StreamingResponse:
    """
    Streaming RAG query via SSE.

    The response is a text/event-stream with one JSON event per line.
    Each event has a "type" field:
      - "token"   → content = the next token to display
      - "sources" → sources = list of citations (emitted after full answer)
      - "done"    → stream is complete
      - "error"   → something went wrong
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    service = _get_query_service()

    def event_generator():
        try:
            for chunk in service.stream_query(
                question=request.question,
                top_k=request.top_k,
                doc_ids=request.doc_ids,
            ):
                payload = chunk.model_dump_json()
                yield f"data: {payload}\n\n"
        except Exception as e:
            error_chunk = StreamChunk(type="error", error=str(e))
            yield f"data: {error_chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # disable nginx buffering
        },
    )
