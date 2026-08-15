# PDF-QA Build Tracker

## Phase 1 — Scaffold & Config System ✅
- [x] Create directory structure
- [x] `pyproject.toml` with all dependencies
- [x] `config.yaml` master config
- [x] `.env.example` with all API key slots
- [x] `backend/config/settings.py` — Pydantic Settings model
- [x] `backend/__init__.py` and `backend/config/__init__.py`
- [x] `backend/__main__.py` — prints resolved config (verify step)
- [x] `README.md`
- [x] **Verify**: `python -m backend.config` prints validated config — 6/6 tests PASSED

## Phase 2 — LLM Adapter Layer ✅
- [x] `backend/adapters/llm/base.py` — BaseLLMAdapter + `_extract_text()` for new response format
- [x] `backend/adapters/llm/gemini.py` / `openai.py` / `anthropic.py` / `ollama.py` / `vertexai.py`
- [x] `backend/adapters/llm/factory.py`
- [x] `backend/adapters/embeddings/` — BaseEmbeddingAdapter + 5 concrete adapters + factory
- [x] `backend/main.py` — FastAPI app + CORS
- [x] `backend/api/health.py` — `GET /api/health`
- [x] `scripts/test_llm.py` — CLI smoke test
- [x] **Verify**: 17/17 tests PASSED | `GET /api/health` → `{status:ok, provider:gemini, model:gemini-flash-latest}`

## Phase 3 — PDF Ingestion Pipeline ✅
- [x] `backend/storage/vector_store.py` — ChromaDB wrapper + JSON doc registry
- [x] `backend/services/ingestion.py` — PDFIngestionService (parse→chunk→embed→store)
- [x] `backend/models/documents.py` — Pydantic schemas
- [x] `backend/api/documents.py` — upload / list / get / delete routes
- [x] `backend/main.py` — documents router registered
- [x] `scripts/ingest_pdf.py` — CLI smoke test
- [x] **Verify**: 9/9 tests PASSED | live ingest: 1 chunk, score=0.858, registry OK

## Phase 4 — RAG Query Pipeline ✅
- [x] `backend/models/chat.py` — ChatRequest, ChatResponse, SourceCitation, StreamChunk
- [x] `backend/services/query.py` — RAGQueryService (retrieve → prompt → LLM → citations)
- [x] `backend/api/chat.py` — POST /api/chat + POST /api/chat/stream (SSE)
- [x] `backend/main.py` — chat router registered
- [x] `scripts/ask.py` — CLI: standard + --stream modes
- [x] **Verify**: 8/8 tests PASSED | live RAG: score=0.865, grounded answer with citations

## Phase 5 — Next.js Frontend ✅
- [x] Initialize Next.js app in `frontend/`
- [x] PDF upload component (drag-and-drop)
- [x] Document library sidebar
- [x] Chat interface with SSE streaming
- [x] Source citation cards
- [x] LLM provider selector (Skipped / Config-driven for now)
- [x] **Verify**: full browser end-to-end flow

## Phase 6 — Agentic Enhancements ✅
- [x] `PDFSearchTool` — LangChain tool
- [x] ReAct Agent setup
- [x] Conversation memory
- [x] **Verify**: multi-hop CLI query across multiple PDFs