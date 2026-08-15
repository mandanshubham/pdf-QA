# Feature Tracker

Live status of every feature across all build phases.

---

## Phase 1 — Scaffold & Config System ✅ COMPLETE

**Goal**: A clean project structure with a validated, layered config system.

| Feature | Status | File(s) |
|---|---|---|
| Repo directory structure | ✅ Done | `backend/`, `docs/`, `scripts/`, `frontend/` |
| Dependency manifest | ✅ Done | `pyproject.toml` |
| Master config file | ✅ Done | `config.yaml` |
| API key template | ✅ Done | `.env.example` |
| Pydantic Settings model | ✅ Done | `backend/config/settings.py` |
| Config layering (yaml → env → vars) | ✅ Done | `settings.py::from_yaml_and_env()` |
| Auto-resolve provider model names | ✅ Done | `@model_validator` in `LLMSettings` |
| Config verify script | ✅ Done | `python -m backend.config` |
| Smoke tests | ✅ Done | `backend/tests/test_config.py` — 6/6 pass |

**Verify command**: `python -m backend.config`

---

## Phase 2 — LLM Adapter Layer ✅ COMPLETE

**Goal**: A unified interface that plugs in any cloud LLM with zero code changes.

| Feature | Status | File(s) |
|---|---|---|
| `BaseLLMAdapter` abstract class | ✅ Done | `backend/adapters/llm/base.py` |
| `GeminiAdapter` | ✅ Done | `backend/adapters/llm/gemini.py` |
| `OpenAIAdapter` | ✅ Done | `backend/adapters/llm/openai.py` |
| `AnthropicAdapter` | ✅ Done | `backend/adapters/llm/anthropic.py` |
| `OllamaAdapter` | ✅ Done | `backend/adapters/llm/ollama.py` |
| `LLMAdapterFactory` | ✅ Done | `backend/adapters/llm/factory.py` |
| `BaseEmbeddingAdapter` | ✅ Done | `backend/adapters/embeddings/base.py` |
| Embedding adapters (Gemini, OpenAI, HF, Ollama) | ✅ Done | `backend/adapters/embeddings/` |
| `EmbeddingAdapterFactory` | ✅ Done | `backend/adapters/embeddings/factory.py` |
| FastAPI app entry point | ✅ Done | `backend/main.py` |
| `GET /api/health` endpoint | ✅ Done | `backend/api/health.py` |
| CLI smoke test script | ✅ Done | `scripts/test_llm.py` |
| Smoke tests | ✅ Done | `backend/tests/test_adapters.py` — 11/11 pass |

**Verify command**: `python scripts/test_llm.py` + `curl http://localhost:8000/api/health`


---

## Phase 3 — PDF Ingestion Pipeline ✅ COMPLETE

**Goal**: Upload PDFs → parse → chunk → embed → store in ChromaDB.

| Feature | Status | File(s) |
|---|---|---|
| ChromaDB wrapper | ✅ Done | `backend/storage/vector_store.py` |
| PDF ingestion service | ✅ Done | `backend/services/ingestion.py` |
| PyMuPDF text extraction | ✅ Done | `services/ingestion.py::_parse_pdf()` |
| Fixed-size text chunking with overlap | ✅ Done | `RecursiveCharacterTextSplitter` |
| Chunk metadata (file, page, index) | ✅ Done | `services/ingestion.py::_build_chunks()` |
| Document registry (JSON sidecar) | ✅ Done | `storage/vector_store.py` |
| `POST /api/documents/upload` | ✅ Done | `backend/api/documents.py` |
| `GET /api/documents` | ✅ Done | `backend/api/documents.py` |
| `GET /api/documents/{doc_id}` | ✅ Done | `backend/api/documents.py` |
| `DELETE /api/documents/{doc_id}` | ✅ Done | `backend/api/documents.py` |
| CLI ingest script | ✅ Done | `scripts/ingest_pdf.py` |
| Smoke tests | ✅ Done | `backend/tests/test_ingestion.py` |

**Verify command**: `python scripts/ingest_pdf.py`


---

## Phase 4 — RAG Query Pipeline 🔲 NOT STARTED

**Goal**: Question → retrieve chunks → LLM answer with citations.

| Feature | Status | File(s) |
|---|---|---|
| RAG query service | 🔲 | `backend/services/query.py` |
| Question embedding | 🔲 | `services/query.py` |
| Similarity search (top-K) | 🔲 | `services/query.py` |
| Context prompt builder | 🔲 | `services/query.py` |
| LLM call + answer | 🔲 | `services/query.py` |
| Source attribution (file + page) | 🔲 | `services/query.py` |
| `POST /api/chat` (standard) | 🔲 | `backend/api/chat.py` |
| `POST /api/chat/stream` (SSE) | 🔲 | `backend/api/chat.py` |
| Request/response Pydantic models | 🔲 | `backend/models/chat.py` |
| CLI ask script | 🔲 | `scripts/ask.py` |
| Smoke tests | 🔲 | `backend/tests/test_query.py` |

**Verify command**: `python scripts/ask.py "What is this document about?"`

---

## Phase 5 — Next.js Frontend 🔲 NOT STARTED

**Goal**: A polished browser UI for uploading PDFs and chatting with them.

| Feature | Status | File(s) |
|---|---|---|
| Next.js project init | 🔲 | `frontend/` |
| Drag-and-drop PDF upload | 🔲 | `frontend/src/components/UploadZone.tsx` |
| Upload progress indicator | 🔲 | `frontend/src/components/UploadZone.tsx` |
| Document library sidebar | 🔲 | `frontend/src/components/DocumentList.tsx` |
| Delete document from library | 🔲 | `frontend/src/components/DocumentList.tsx` |
| Chat message interface | 🔲 | `frontend/src/components/ChatWindow.tsx` |
| Streaming SSE integration | 🔲 | `frontend/src/lib/api.ts` |
| Source citation cards | 🔲 | `frontend/src/components/CitationCard.tsx` |
| LLM provider / model selector | 🔲 | `frontend/src/components/ProviderSelector.tsx` |
| Dark mode design | 🔲 | `frontend/src/app/globals.css` |

**Verify**: Full browser end-to-end — upload PDF → ask question → streamed answer with citations

---

## Phase 6 — Agentic Enhancements 🔲 NOT STARTED

**Goal**: Upgrade from RAG to a reasoning agent that can plan and use tools.

| Feature | Status | File(s) |
|---|---|---|
| `PDFSearchTool` LangChain tool | 🔲 | `backend/agent/tools.py` |
| ReAct agent setup | 🔲 | `backend/agent/agent.py` |
| Agent decides when to search | 🔲 | `backend/agent/agent.py` |
| Conversation memory | 🔲 | `backend/agent/memory.py` |
| Multi-hop reasoning | 🔲 | `backend/agent/agent.py` |
| `POST /api/agent/chat` route | 🔲 | `backend/api/agent.py` |
| CLI agent script | 🔲 | `scripts/agent.py` |

**Verify**: CLI multi-hop query across 2 PDFs answered correctly

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Complete and verified |
| 🔄 | In progress |
| 🔲 | Not started |
| ❌ | Blocked / needs rework |
