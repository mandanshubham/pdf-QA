# Architecture

## What this system does

PDF-QA lets you upload one or more PDF documents and ask questions about them in natural language. The system finds the most relevant passages from the PDFs and uses an LLM to compose a grounded answer — meaning it only answers from what is actually in your documents, with citations to the exact page and file.

---

## High-Level Data Flow

```
User Question
     │
     ▼
┌─────────────────┐
│   API Layer     │  POST /api/chat
│   (FastAPI)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  RAG Query      │  1. Embed the question
│  Service        │  2. Search vector store (top-K chunks)
│                 │  3. Build context prompt
│                 │  4. Call LLM → stream answer
└────────┬────────┘
         │
         ▼
┌─────────────────┐        ┌─────────────────┐
│  ChromaDB       │        │  LLM Adapter    │
│  Vector Store   │        │  (Gemini /      │
│  (local disk)   │        │   OpenAI /      │
└─────────────────┘        │   Anthropic)    │
                           └─────────────────┘
```

---

## Ingestion Flow (Upload a PDF)

```
PDF File(s)
     │
     ▼
┌─────────────────┐
│  API Layer      │  POST /api/documents/upload
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│  PDF Ingestion Service                       │
│                                             │
│  1. Parse PDF  ──► PyMuPDF (fitz)           │
│     Extract text page by page               │
│                                             │
│  2. Chunk text ──► LangChain TextSplitter   │
│     chunk_size=1000, overlap=200            │
│                                             │
│  3. Embed      ──► Embedding Adapter        │
│     Each chunk → float vector (768-dim)     │
│                                             │
│  4. Store      ──► ChromaDB                 │
│     Vector + metadata (file, page, chunk#) │
└─────────────────────────────────────────────┘
```

---

## Component Map

```
pdf-QA/
│
├── config.yaml              Master config — provider, model, chunking, retrieval
│
├── backend/
│   │
│   ├── config/
│   │   └── settings.py      Pydantic Settings model — loads config.yaml + .env
│   │
│   ├── adapters/
│   │   ├── llm/             One class per LLM provider (Gemini, OpenAI, Anthropic, Ollama)
│   │   │   └── factory.py   Reads config → returns the right adapter
│   │   └── embeddings/      Same pattern for embedding models
│   │
│   ├── services/
│   │   ├── ingestion.py     PDF → chunks → embeddings → ChromaDB
│   │   └── query.py         Question → vector search → LLM → streamed answer
│   │
│   ├── api/
│   │   ├── documents.py     Routes: upload, list, delete documents
│   │   └── chat.py          Routes: ask question, stream response
│   │
│   ├── models/              Pydantic schemas for API request/response bodies
│   ├── storage/
│   │   └── vector_store.py  ChromaDB wrapper (add, search, delete)
│   │
│   └── main.py              FastAPI app — mounts all routers, CORS, startup
│
├── frontend/                Next.js app (Phase 5)
│
└── scripts/
    ├── test_llm.py          CLI: smoke-test the active LLM adapter
    ├── ingest_pdf.py        CLI: ingest a PDF file into ChromaDB
    └── ask.py               CLI: ask a question, print answer + citations
```

---

## Design Patterns Used

### Adapter / Strategy Pattern
Every LLM and embedding provider implements the same abstract interface. The rest of the code never imports `GeminiAdapter` directly — it always goes through `LLMAdapterFactory`. Swapping providers is a one-line config change.

```
BaseLLMAdapter (abstract)
    ├── GeminiAdapter
    ├── OpenAIAdapter
    ├── AnthropicAdapter
    └── OllamaAdapter

LLMAdapterFactory.create(settings) → BaseLLMAdapter
```

### Singleton Settings
`get_settings()` loads and validates config exactly once at startup. Every service, adapter, and router imports `get_settings()` rather than reading files themselves.

### RAG Pipeline (Retrieval-Augmented Generation)
The core agentic pattern: the system *retrieves* relevant information before *generating* an answer. This grounds the LLM in real document content and prevents hallucination.

### Streaming (SSE)
The query pipeline supports Server-Sent Events so the UI can show tokens appearing word-by-word, instead of waiting for the full response.

---

## Tech Stack Summary

| Layer | Technology | Version |
|---|---|---|
| Backend framework | FastAPI | 0.111+ |
| Server | Uvicorn | 0.30+ |
| Config / Validation | Pydantic v2 + pydantic-settings | 2.7+ |
| RAG framework | LangChain | 0.2+ |
| LLM providers | langchain-google-genai / openai / anthropic | latest |
| PDF parsing | PyMuPDF (fitz) | 1.24+ |
| Vector store | ChromaDB | 0.5+ |
| Streaming | sse-starlette | 2.1+ |
| Frontend | Next.js (React) | Phase 5 |
| Testing | Pytest | 8.2+ |
| Python | CPython | 3.11+ |
