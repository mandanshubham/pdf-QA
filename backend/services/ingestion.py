"""
backend/services/ingestion.py

PDF Ingestion Service — orchestrates the full ingest pipeline:

    PDF file → [PyMuPDF] → raw text per page
             → [TextSplitter] → overlapping chunks
             → [EmbeddingAdapter] → float vectors
             → [VectorStore] → stored in ChromaDB

This service is called by the API layer (POST /api/documents/upload)
and by the CLI script (scripts/ingest_pdf.py).

What you learn here:
  - How to extract structured text from PDFs page by page
  - Chunking strategy: why overlap matters for context preservation
  - The concept of "document" vs "chunk" in a RAG system
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pymupdf as fitz  # PyMuPDF (fitz is the legacy alias, pymupdf is current)
from langchain_text_splitters import RecursiveCharacterTextSplitter

from backend.config.settings import ChunkingSettings
from backend.storage.vector_store import DocRecord, DocumentChunk, VectorStore


class PDFIngestionService:
    """
    Ingests one PDF file into the vector store.

    Pipeline:
      1. parse_pdf()   — extract text from each page using PyMuPDF
      2. chunk_text()  — split into overlapping chunks
      3. build_chunks() — attach metadata to each chunk
      4. store.add_chunks() — embed + upsert to ChromaDB

    Usage:
        service = PDFIngestionService(vector_store, chunking_settings)
        doc_record = service.ingest(pdf_path, original_filename)
    """

    def __init__(
        self,
        vector_store: VectorStore,
        chunking_settings: ChunkingSettings,
    ) -> None:
        self._store = vector_store
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunking_settings.chunk_size,
            chunk_overlap=chunking_settings.chunk_overlap,
            length_function=len,
            # Split on: paragraphs → sentences → words → characters
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def ingest(self, pdf_path: Path, original_filename: str) -> DocRecord:
        """
        Run the full ingestion pipeline for one PDF file.

        Args:
            pdf_path: Path to the PDF file on disk.
            original_filename: The original upload filename (shown to users).

        Returns:
            DocRecord with metadata about the ingested document.
        """
        doc_id = str(uuid.uuid4())
        upload_timestamp = datetime.now(timezone.utc).isoformat()
        file_size = pdf_path.stat().st_size

        # Step 1: Extract text from each page
        pages = self._parse_pdf(pdf_path)
        if not pages:
            raise ValueError(f"No extractable text found in '{original_filename}'.")

        # Step 2 & 3: Split and build DocumentChunk objects
        chunks = self._build_chunks(pages, doc_id, original_filename, upload_timestamp)
        if not chunks:
            raise ValueError(f"PDF '{original_filename}' produced no chunks after splitting.")

        # Step 4: Embed and store (the VectorStore handles the embedding call)
        doc_record = DocRecord(
            doc_id=doc_id,
            filename=original_filename,
            chunk_count=len(chunks),
            upload_timestamp=upload_timestamp,
            file_size_bytes=file_size,
        )
        self._store.add_chunks(chunks, doc_record)

        return doc_record

    # ── Private helpers ───────────────────────────────────────────────────────

    def _parse_pdf(self, pdf_path: Path) -> list[dict]:
        """
        Extract text from every page of the PDF using PyMuPDF.

        Returns:
            List of dicts: [{"page": 1, "text": "..."}, ...]
            Pages with no text are skipped.
        """
        pages = []
        with fitz.open(str(pdf_path)) as doc:
            for page_num, page in enumerate(doc, start=1):
                text = page.get_text("text").strip()
                if text:
                    pages.append({"page": page_num, "text": text})
        return pages

    def _build_chunks(
        self,
        pages: list[dict],
        doc_id: str,
        filename: str,
        upload_timestamp: str,
    ) -> list[DocumentChunk]:
        """
        Split each page's text into overlapping chunks, attaching rich metadata.

        Metadata stored per chunk:
          - doc_id       → used to filter/delete by document
          - filename     → shown to users as citation source
          - page         → shown to users as citation page number
          - chunk_index  → position within the document
          - upload_timestamp → for auditing

        Returns:
            Flat list of DocumentChunk objects ready for embedding.
        """
        all_chunks: list[DocumentChunk] = []
        global_chunk_index = 0

        for page_info in pages:
            page_num = page_info["page"]
            page_text = page_info["text"]

            # Split this page's text into chunks
            page_chunks = self._splitter.split_text(page_text)

            for local_idx, chunk_text in enumerate(page_chunks):
                chunk_text = chunk_text.strip()
                if not chunk_text:
                    continue

                all_chunks.append(
                    DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        doc_id=doc_id,
                        text=chunk_text,
                        metadata={
                            "doc_id": doc_id,
                            "filename": filename,
                            "page": page_num,
                            "chunk_index": global_chunk_index,
                            "local_chunk_index": local_idx,
                            "upload_timestamp": upload_timestamp,
                        },
                    )
                )
                global_chunk_index += 1

        return all_chunks

    def get_stats(self, pdf_path: Path) -> dict:
        """
        Return basic stats about a PDF without ingesting it.
        Useful for previewing before upload.
        """
        pages = self._parse_pdf(pdf_path)
        total_chars = sum(len(p["text"]) for p in pages)
        return {
            "pages": len(pages),
            "total_characters": total_chars,
            "estimated_chunks": total_chars // (self._splitter._chunk_size // 2),
        }
