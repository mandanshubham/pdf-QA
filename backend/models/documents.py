"""
backend/models/documents.py

Pydantic schemas for the document management API (Phase 3).
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class DocumentInfo(BaseModel):
    """Metadata for a single indexed PDF document."""
    doc_id: str
    filename: str
    chunk_count: int
    upload_timestamp: datetime
    file_size_bytes: int


class UploadResponse(BaseModel):
    """Response returned after successfully ingesting a PDF."""
    message: str
    doc_id: str
    filename: str
    chunk_count: int


class DocumentListResponse(BaseModel):
    """Response for GET /api/documents."""
    total: int
    documents: list[DocumentInfo]


class DeleteResponse(BaseModel):
    """Response returned after deleting a document."""
    message: str
    doc_id: str
    chunks_deleted: int
