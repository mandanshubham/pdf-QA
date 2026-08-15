"""
backend/api/documents.py

Document management routes:
  POST   /api/documents/upload       — ingest one or more PDFs
  GET    /api/documents              — list all indexed documents
  GET    /api/documents/{doc_id}     — get a single document's info
  DELETE /api/documents/{doc_id}     — remove a document + its vectors
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse

from backend.adapters.embeddings.factory import EmbeddingAdapterFactory
from backend.config import get_settings
from backend.models.documents import (
    DeleteResponse,
    DocumentInfo,
    DocumentListResponse,
    UploadResponse,
)
from backend.services.ingestion import PDFIngestionService
from backend.storage.vector_store import VectorStore

router = APIRouter(prefix="/api/documents", tags=["documents"])


def _get_vector_store() -> VectorStore:
    """Dependency: build VectorStore from current settings."""
    cfg = get_settings()
    embedder = EmbeddingAdapterFactory.create(cfg)
    return VectorStore(cfg.vector_store, embedder)


def _get_ingestion_service(store: VectorStore | None = None) -> PDFIngestionService:
    """Dependency: build PDFIngestionService from current settings."""
    cfg = get_settings()
    if store is None:
        store = _get_vector_store()
    return PDFIngestionService(store, cfg.chunking)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post(
    "/upload",
    response_model=list[UploadResponse],
    summary="Upload and index one or more PDF files",
)
async def upload_documents(
    files: list[UploadFile] = File(..., description="One or more PDF files to ingest"),
) -> list[UploadResponse]:
    """
    Accepts multipart PDF uploads, ingests each one through the RAG pipeline,
    and returns metadata for each indexed document.

    Steps per file:
      1. Save to a temp file
      2. Parse PDF → chunks
      3. Embed chunks → ChromaDB
      4. Return doc_id + chunk count
    """
    cfg = get_settings()
    store = _get_vector_store()
    service = PDFIngestionService(store, cfg.chunking)
    responses: list[UploadResponse] = []

    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' is not a PDF file. Only .pdf files are accepted.",
            )

        # Write to a temp file (FastAPI UploadFile is a stream)
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        try:
            doc_record = service.ingest(tmp_path, file.filename)
            responses.append(
                UploadResponse(
                    message=f"'{file.filename}' ingested successfully.",
                    doc_id=doc_record.doc_id,
                    filename=doc_record.filename,
                    chunk_count=doc_record.chunk_count,
                )
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
        finally:
            tmp_path.unlink(missing_ok=True)  # always clean up the temp file

    return responses


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all indexed documents",
)
def list_documents() -> DocumentListResponse:
    """Return a list of all documents currently indexed in the vector store."""
    store = _get_vector_store()
    records = store.list_documents()
    return DocumentListResponse(
        total=len(records),
        documents=[
            DocumentInfo(
                doc_id=r.doc_id,
                filename=r.filename,
                chunk_count=r.chunk_count,
                upload_timestamp=r.upload_timestamp,  # type: ignore[arg-type]
                file_size_bytes=r.file_size_bytes,
            )
            for r in records
        ],
    )


@router.get(
    "/{doc_id}",
    response_model=DocumentInfo,
    summary="Get a single document's info",
)
def get_document(doc_id: str) -> DocumentInfo:
    """Return metadata for a specific indexed document."""
    store = _get_vector_store()
    record = store.get_document(doc_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")
    return DocumentInfo(
        doc_id=record.doc_id,
        filename=record.filename,
        chunk_count=record.chunk_count,
        upload_timestamp=record.upload_timestamp,  # type: ignore[arg-type]
        file_size_bytes=record.file_size_bytes,
    )


@router.delete(
    "/{doc_id}",
    response_model=DeleteResponse,
    summary="Delete a document and all its vectors",
)
def delete_document(doc_id: str) -> DeleteResponse:
    """
    Remove a document from the vector store entirely.
    Deletes all associated chunks from ChromaDB and the document registry.
    """
    store = _get_vector_store()
    if not store.get_document(doc_id):
        raise HTTPException(status_code=404, detail=f"Document '{doc_id}' not found.")

    chunks_deleted = store.delete_document(doc_id)
    return DeleteResponse(
        message=f"Document '{doc_id}' deleted successfully.",
        doc_id=doc_id,
        chunks_deleted=chunks_deleted,
    )
