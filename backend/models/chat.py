"""
backend/models/chat.py

Pydantic schemas for the chat / RAG query API (Phase 4).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for POST /api/chat."""
    question: str = Field(..., min_length=1, description="The user's question")
    session_id: str | None = Field(None, description="Optional session ID for future memory support")
    doc_ids: list[str] | None = Field(None, description="Restrict search to these document IDs")
    top_k: int | None = Field(None, ge=1, le=20, description="Override config top_k for this request")


class SourceCitation(BaseModel):
    """A single document chunk cited in an answer."""
    filename: str
    page: int
    score: float = Field(description="Similarity score (0–1, higher = more relevant)")
    snippet: str = Field(description="First 200 characters of the matched chunk")
    doc_id: str


class ChatResponse(BaseModel):
    """Response body for POST /api/chat."""
    question: str
    answer: str
    sources: list[SourceCitation]
    chunks_searched: int = Field(description="Number of chunks retrieved from the vector store")


class StreamChunk(BaseModel):
    """A single SSE event payload for POST /api/chat/stream."""
    type: str             # "token" | "sources" | "done" | "error"
    content: str | None = None          # used for type="token"
    sources: list[SourceCitation] | None = None   # used for type="sources"
    error: str | None = None            # used for type="error"
